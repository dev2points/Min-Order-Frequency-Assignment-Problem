from multiprocessing import process
import os
import sys
import psutil
import gurobipy as gp
import time
from gurobipy import Model, GRB


def get_file_names(dataset_folder):
    base = os.path.basename(dataset_folder)
    if base.lower().startswith(("graph", "tud")):
        return {
            "domain": os.path.join(dataset_folder, "dom.txt"),
            "var": os.path.join(dataset_folder, "var.txt"),
            "ctr": os.path.join(dataset_folder, "ctr.txt")
        }
    elif base.lower().startswith("scen"):
        return {
            "domain": os.path.join(dataset_folder, "DOM.TXT"),
            "var": os.path.join(dataset_folder, "VAR.TXT"),
            "ctr": os.path.join(dataset_folder, "CTR.TXT")
        }
    else:
        raise ValueError("Not a valid dataset: " + dataset_folder)


def read_domain(file):
    domain = []
    with open(file) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            values = list(map(int, parts[2:]))
            domain.append(values)
    return domain


def read_var(file, domain):
    var = {}
    with open(file) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            idx = int(parts[0])
            if len(parts) >= 4:
                var[idx] = [int(parts[-2])]
            else:
                var[idx] = domain[int(parts[1])]
    return var

def delete_invalid_labels(var, ctr_file):
    # Read constraints and remove invalid labels from domain
    constraint = {}
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == '\x00':
                continue
            parts = line.strip().split()
            if not parts:
                continue
            u, v = int(parts[0]), int(parts[1])
            distance = int(parts[4])
            constraint[(u, v)] = (parts[3], distance)
    while True:
            changed = False
            for (u, v), (op, distance) in constraint.items():
                if op == '=':
                    new_var_u = [label for label in var[u] if any(abs(label - label_v) == distance for label_v in var[v])]
                    new_var_v = [label for label in var[v] if any(abs(label - label_u) == distance for label_u in new_var_u)]
                elif op == '>':
                    new_var_u = [label for label in var[u] if any(abs(label - label_v) > distance for label_v in var[v])]
                    new_var_v = [label for label in var[v] if any(abs(label - label_u) > distance for label_u in new_var_u)]
                else:
                    continue

                if len(new_var_u) != len(var[u]) or len(new_var_v) != len(var[v]):
                    changed = True
                    var[u] = new_var_u
                    var[v] = new_var_v
            for i,vals in var.items():
                if len(vals) == 0:
                    print("Warning: variable", i, "has no valid labels after preprocessing.")
                    return False
            if not changed:
                break
    return True


def build_gurobi_model(var, ctr_file):
    model = Model("MOFAP")
    model.Params.OutputFlag = 0


    # binary variable 
    x = {}
    for i, vals in var.items():
        for v in vals:
            x[(i, v)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{v}")

    # label variable 
    label_set = sorted({v for vals in var.values() for v in vals})
    y = {}
    for lb in label_set:
        y[lb] = model.addVar(vtype=GRB.BINARY, name=f"y_{lb}")

    model.update()

    #exactly one
    for i, vals in var.items():
        model.addConstr(sum(x[(i, v)] for v in vals) == 1)

    # Link binary variables to label usage
    for (i, v), xv in x.items():
        model.addConstr(xv <= y[v])

    # distance constraints
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == '\x00':
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            vals_i = var[i]
            vals_j = var[j]

            if '>' in parts:
                distance = int(parts[4])
                for vi in vals_i:
                    not_valid_vj = [vj for vj in vals_j if abs(vi - vj) <= distance]
                    if len(not_valid_vj) == len(vals_j):
                        model.addConstr(x[(i, vi)] == 0)
                    else:
                        for vj in not_valid_vj:
                            model.addConstr(x[(i, vi)] + x[(j, vj)] <= 1)
                        

            elif '=' in parts:
                target = int(parts[4])
                for vi in vals_i:
                    if not any(abs(vi - vj) == target for vj in vals_j):
                        model.addConstr(x[(i, vi)] == 0)
                    else:
                        model.addConstr(x[(i, vi)] <= sum(x[(j, vj)] for vj in vals_j if abs(vi - vj) == target))

    # Minimize number of labels used
    model.setObjective(sum(y[v] for v in label_set), GRB.MINIMIZE)

    return model, x, y
def mycallback(model, where):
    if where == GRB.Callback.MIPSOL:

        vals = model.cbGetSolution(model._vars)

        sol_dict = {var: val for var, val in zip(model._vars, vals)}

        solution = extract_solution_from_dict(model._map, sol_dict)


        print(solution)
        print("\nNumber of labels used:", len(set(solution.values())))

        # if verify_solution(solution, model._domain, model._ctr_file) :
        #     print("Solution is CORRECT!")
        # else:
        #     print("Solution is INCORRECT!")
        print(f"Total time used: {time.perf_counter() - model._time:.2f} sec")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.2f} MB")
        print("================================")

def extract_solution_from_dict(var_map, sol_dict):
    solution = {}

    for var, val in sol_dict.items():
        if val > 0.5:
            i, v = var_map[var]
            solution[i] = v

    return solution

def extract_solution(x):
    solution = {}
    for (i, v), var in x.items():
        if var.X > 0.5:
            solution[i] = v
    return solution
def verify_solution(solution, var, ctr_file):

    # Check each variable has 1 value and in domain
    for i, allowed_vals in var.items():
        if i not in solution:
            print(f"Variable {i} missing in solution")
            return False

        if solution[i] not in allowed_vals:
            print(f"Variable {i} has value {solution[i]} not in domain {allowed_vals}")
            return False

    # Check distance constraints
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == '\x00':
                continue
            parts = line.strip().split()
            if not parts:
                continue

            i, j = int(parts[0]), int(parts[1])
            vi = solution[i]
            vj = solution[j]

            if '>' in parts:
                distance = int(parts[4])
                if abs(vi - vj) <= distance:
                    print(f"Constraint violated: |{vi}-{vj}| <= {distance}")
                    return False

            elif '=' in parts:
                target = int(parts[4])
                if abs(vi - vj) != target:
                    print(f"Constraint violated: |{vi}-{vj}| != {target}")
                    return False

    return True



def main():
    start_time = time.perf_counter()

    if len(sys.argv) < 2:
        print("Use: python main.py <dataset_folder>")
        return

    dataset_folder = os.path.join("dataset", sys.argv[1])

    files = get_file_names(dataset_folder)

    domain = read_domain(files["domain"])
    var = read_var(files["var"], domain)
    if(not delete_invalid_labels(var, files["ctr"])):
        print("Cannot find solution!")
        print(f"Total time used: {time.perf_counter() - start_time:.2f} sec")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.2f} MB")
        return

    print("Building Gurobi model...")
    model, x, y = build_gurobi_model(var, files["ctr"])
    model.update()
    model._vars = list(x.values())
    model._map = {var: (i, v) for (i, v), var in x.items()}
    model._domain = var
    model._ctr_file = files["ctr"]
    model._time = start_time


    print(f"Build time used: {time.perf_counter() - start_time:.2f} sec")
    

    print("Solving...")
    model.optimize(mycallback)

    if model.status != GRB.OPTIMAL:
        print("No solution found.")
        print(f"Total time used: {time.perf_counter() - start_time:.2f} sec")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.2f} MB")
        return
    


if __name__ == "__main__":
    main()

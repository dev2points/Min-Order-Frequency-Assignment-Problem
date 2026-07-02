import os
import sys
import time

import psutil
from ortools.sat.python import cp_model


def find_dataset_folder(dataset_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "dataset", dataset_name),
        os.path.join(script_dir, "..", "Gurobi", "dataset", dataset_name),
        os.path.join(script_dir, "..", "SAT", "pairwise", "dataset", dataset_name),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return os.path.normpath(path)
    raise ValueError("Cannot find dataset: " + dataset_name)


def get_file_names(dataset_folder):
    base = os.path.basename(dataset_folder)
    if base.lower().startswith(("graph", "tud")):
        return {
            "domain": os.path.join(dataset_folder, "dom.txt"),
            "var": os.path.join(dataset_folder, "var.txt"),
            "ctr": os.path.join(dataset_folder, "ctr.txt"),
        }
    if base.lower().startswith("scen"):
        return {
            "domain": os.path.join(dataset_folder, "DOM.TXT"),
            "var": os.path.join(dataset_folder, "VAR.TXT"),
            "ctr": os.path.join(dataset_folder, "CTR.TXT"),
        }
    raise ValueError("Not a valid dataset: " + dataset_folder)


def read_domain(file_path):
    domain = []
    with open(file_path) as file:
        for line in file:
            parts = line.strip().split()
            if parts:
                domain.append(list(map(int, parts[2:])))
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
                domain_idx = int(parts[1])
                if int(parts[-2]) not in domain[domain_idx]:
                    print(f"Warning: variable {idx} has assigned label {parts[-2]} that is not in the domain {domain_idx}.")
                    return None
                else:
                    var[idx] = [int(parts[-2])]
            else:
                var[idx] = domain[int(parts[1])]
    return var # domain subset for each variable


def delete_invalid_labels(var, ctr_file):
    constraints = {}
    with open(ctr_file) as file:
        for line in file:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue
            u, v = int(parts[0]), int(parts[1])
            constraints[(u, v)] = (parts[3], int(parts[4]))

    while True:
        changed = False
        for (u, v), (op, distance) in constraints.items():
            if op == "=":
                new_var_u = [
                    label
                    for label in var[u]
                    if any(abs(label - label_v) == distance for label_v in var[v])
                ]
                new_var_v = [
                    label
                    for label in var[v]
                    if any(abs(label - label_u) == distance for label_u in new_var_u)
                ]
            elif op == ">":
                new_var_u = [
                    label
                    for label in var[u]
                    if any(abs(label - label_v) > distance for label_v in var[v])
                ]
                new_var_v = [
                    label
                    for label in var[v]
                    if any(abs(label - label_u) > distance for label_u in new_var_u)
                ]
            else:
                continue

            if len(new_var_u) != len(var[u]) or len(new_var_v) != len(var[v]):
                changed = True
                var[u] = new_var_u
                var[v] = new_var_v

        for i, vals in var.items():
            if not vals:
                print("Warning: variable", i, "has no valid labels after preprocessing.")
                return False
        if not changed:
            return True


def build_cpsat_model(var, ctr_file):
    model = cp_model.CpModel()

    x = {}
    for i, vals in var.items():
        for value in vals:
            x[(i, value)] = model.NewBoolVar(f"x_{i}_{value}")

    label_set = sorted({value for vals in var.values() for value in vals})
    y = {value: model.NewBoolVar(f"y_{value}") for value in label_set}

    for i, vals in var.items():
        model.AddExactlyOne(x[(i, value)] for value in vals)

    for (i, value), x_var in x.items():
        model.Add(x_var <= y[value])

    with open(ctr_file) as file:
        for line in file:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue

            i, j = int(parts[0]), int(parts[1])
            vals_i = var[i]
            vals_j = var[j]

            if ">" in parts:
                distance = int(parts[4])
                for vi in vals_i:
                    forbidden = [vj for vj in vals_j if abs(vi - vj) <= distance]
                    if len(forbidden) == len(vals_j):
                        model.Add(x[(i, vi)] == 0)
                    else:
                        for vj in forbidden:
                            model.Add(x[(i, vi)] + x[(j, vj)] <= 1)
            elif "=" in parts:
                target = int(parts[4])
                for vi in vals_i:
                    allowed = [vj for vj in vals_j if abs(vi - vj) == target]
                    if not allowed:
                        model.Add(x[(i, vi)] == 0)
                    else:
                        model.Add(x[(i, vi)] <= sum(x[(j, vj)] for vj in allowed))

    model.Minimize(sum(y[value] for value in label_set))
    return model, x, y


def extract_solution(solver, x):
    assignment = {}
    for (i, value), x_var in x.items():
        if solver.BooleanValue(x_var):
            assignment[i] = value
    return assignment


def verify_solution(solution, var, ctr_file):
    for i, vals in var.items():
        if i not in solution:
            print(f"Variable {i} missing in solution")
            return False
        if solution[i] not in vals:
            print(f"Variable {i} has value {solution[i]} not in domain")
            return False

    with open(ctr_file) as file:
        for line in file:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            distance = int(parts[4])
            diff = abs(solution[i] - solution[j])
            if ">" in parts and diff <= distance:
                print(f"Constraint violated: |{solution[i]}-{solution[j]}| <= {distance}")
                return False
            if "=" in parts and diff != distance:
                print(f"Constraint violated: |{solution[i]}-{solution[j]}| != {distance}")
                return False
    return True


class IncumbentPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, x, start_time):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._x = x
        self._start_time = start_time

    def on_solution_callback(self):
        assignment = {}
        for (i, value), x_var in self._x.items():
            if self.BooleanValue(x_var):
                assignment[i] = value
        print("Number of labels used:", len(set(assignment.values())))
        print(f"Time taken: {time.perf_counter() - self._start_time:.5f}s")


def solve_with_callback(solver, model, callback):
    if hasattr(solver, "SolveWithSolutionCallback"):
        return solver.SolveWithSolutionCallback(model, callback)
    return solver.Solve(model, callback)


def run(preprocess):
    start_time = time.perf_counter()
    if len(sys.argv) < 2:
        print("Use: python main.py <dataset_folder> [time_limit_seconds]")
        return

    dataset_name = sys.argv[1]
    time_limit = float(sys.argv[2]) if len(sys.argv) >= 3 else None

    dataset_folder = find_dataset_folder(dataset_name)
    files = get_file_names(dataset_folder)

    domain = read_domain(files["domain"])
    var = read_var(files["var"], domain)
    if var is None:
        print("Cannot find solution!")
        print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return
    
    if preprocess and not delete_invalid_labels(var, files["ctr"]):
        print("Cannot find solution!")
        print(f"Total time: {time.perf_counter() - start_time:.5f}s")
        print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / 1024**2:.5f} MB")
        return

    print("Dataset:", dataset_name)
    print("Preprocessing:", "on" if preprocess else "off")
    print(f"Building CP-SAT model for {len(var)} variables...")
    model, x, y = build_cpsat_model(var, files["ctr"])
    print("Number of assignment variables:", len(x))
    print("Number of label variables:", len(y))
    print(f"Build time: {time.perf_counter() - start_time:.5f}s")

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = os.cpu_count() or 1
    solver.parameters.log_search_progress = False
    if time_limit is not None:
        solver.parameters.max_time_in_seconds = time_limit

    print("Solving with OR-Tools CP-SAT...")
    callback = IncumbentPrinter(x, start_time)
    status = solve_with_callback(solver, model, callback)
    status_name = solver.StatusName(status)
    print("Status:", status_name)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("No solution found.")
        print(f"Objective bound: {solver.BestObjectiveBound()}")
        print(f"Total time: {time.perf_counter() - start_time:.5f}s")
        print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / 1024**2:.5f} MB")
        return

    assignment = extract_solution(solver, x)
    print("Solution:")
    print(dict(sorted(assignment.items())))
    print("Number of labels used:", len(set(assignment.values())))
    print("Objective value:", solver.ObjectiveValue())
    print("Best objective bound:", solver.BestObjectiveBound())
    print("Solution is CORRECT!" if verify_solution(assignment, var, files["ctr"]) else "Solution is INCORRECT!")
    print(f"Total time: {time.perf_counter() - start_time:.5f}s")
    print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / 1024**2:.5f} MB")
import os
import psutil
import sys
import time
from pysat.solvers import Solver
from pysat.card import CardEnc, ITotalizer
from pysat.formula import CNF
from pysat import card

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
                domain_idx = int(parts[1])
                if int(parts[-2]) not in domain[domain_idx]:
                    print(f"Warning: variable {idx} has assigned label {parts[-2]} that is not in the domain {domain_idx}.")
                    return None
                else:
                    var[idx] = [int(parts[-2])]
            else:
                var[idx] = domain[int(parts[1])]
    return var # domain subset for each variable


def create_var_map(var):
    var_map = {}
    counter = 0
    for i, vals in var.items():
        for v in vals:
            counter += 1
            var_map[(i, v)] = counter
    print("Number of assignment variables: ", counter)
    return counter, var_map # dict mapping (i, v) to variable number


def build_constraints(solver, var, var_map, ctr_file, type_card, distance_mode, distance_card):
    top_id = max(var_map.values())

    # Exactly One
    for i, vals in var.items():
        if distance_mode == 'pairwise':
            solver.add_clause([var_map[(i, v)] for v in vals])
            for j in range(len(vals)):
                for k in range(j + 1, len(vals)):
                    solver.add_clause([-var_map[(i, vals[j])], -var_map[(i, vals[k])]])
        elif distance_mode == 'card':
            enc = CardEnc.equals(
                [var_map[(i, v)] for v in vals],
                bound=1,
                top_id=top_id,
                encoding=type_card,
            )
            for clause in enc.clauses:
                solver.add_clause(clause)
            top_id = enc.nv
    exo_clauses = solver.nof_clauses()
    print("Number of clauses for exactly one constraints: ", exo_clauses)
    # Distance constraints
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == '\x00':
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            vals_i = var.get(i, [])
            vals_j = var.get(j, [])
            if '>' in parts:
                distance = int(parts[4])
                if distance_mode == 'pairwise':
                    for vi in vals_i:
                        for vj in vals_j:
                            if abs(vi - vj) <= distance:
                                solver.add_clause([-var_map[(i, vi)], -var_map[(j, vj)]])
                elif distance_mode == 'card':
                    for vi in vals_i:
                        forbidden = [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) <= distance]
                        if forbidden:
                            enc = CardEnc.atmost(
                                [var_map[(i, vi)]] + forbidden,
                                bound=1,
                                top_id=top_id,
                                encoding=distance_card,
                            )
                            for clause in enc.clauses:
                                solver.add_clause(clause)
                            top_id = enc.nv
                            
            elif '=' in parts:
                target = int(parts[4])
                for vi in vals_i:
                    solver.add_clause([-var_map[(i, vi)]] + [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) == target])
    print("Number of clauses for distance constraints: ", solver.nof_clauses() - exo_clauses)
    
    return top_id
    
    
                            
def create_label_var_map(labels, start_index):
    label_var_map = {}
    current = start_index
    for lb in labels:
        label_var_map[lb] = current
        current += 1
    print("Number of label variables: ", len(label_var_map))
    return label_var_map
    
# ánh xạ biến active -> biến xác nhận label được sử dụng    
def build_label_constraints(solver, var_map, label_var_map):
    last_clause_count = solver.nof_clauses()
    for (i, v), varnum in var_map.items():
        lb_varnum = label_var_map[v]
        solver.add_clause([-varnum, lb_varnum])
    print("Number of clauses for label constraints: ", solver.nof_clauses() - last_clause_count)

def amk_nsc(solver, lits, K):
    if isinstance(lits, dict):
        lits = list(lits.values())

    n = len(lits)
    top = solver.nof_vars()

    # r[i][j] với i = 1..n, j = 1..K
    r = [[0] * (K + 1) for _ in range(n + 1)]

    for i in range(1, K):
        for j in range(1, i + 1):
            top += 1
            r[i][j] = top
    for i in range(K, n + 1):
        for j in range(1, K + 1):
            top += 1
            r[i][j] = top
    print("Number of new variables for cardinality constraints: ", top - solver.nof_vars())
    last_clause_count = solver.nof_clauses()
    # (1)  ¬x_i ∨ r(i,1)
    for i in range(1, n + 1):
        solver.add_clause([-lits[i - 1], r[i][1]])

    # (2)  ¬r(i-1,j) ∨ r(i,j)
    for i in range(2, n + 1):
        for j in range(1, min(i - 1, K) + 1):
            solver.add_clause([-r[i - 1][j], r[i][j]])

    # (3)  ¬x_i ∨ ¬r(i-1,j-1) ∨ r(i,j)
    for i in range(2, n + 1):
        for j in range(2, min(i, K) + 1):
            solver.add_clause([-lits[i - 1], -r[i - 1][j - 1], r[i][j]])

    # (5)  x_i ∨ ¬r(i,i)
    for i in range(1, K + 1):
        solver.add_clause([lits[i - 1], -r[i][i]])

    # (6)  r(i-1,j-1) ∨ ¬r(i,j)
    for i in range(2, n + 1):
        for j in range(2, min(i, K) + 1):
            solver.add_clause([r[i - 1][j - 1], -r[i][j]])

    # (7)  x_i ∨ r(i-1,j-1) ∨ ¬r(i,j)
    for i in range(2, n + 1):
        for j in range(1, min(i - 1, K) + 1):
            solver.add_clause([lits[i - 1], r[i - 1][j], -r[i][j]])

    # (8)  ¬x_i ∨ ¬r(i-1,K)
    for i in range(K + 1, n + 1):
        solver.add_clause([-lits[i - 1], -r[i - 1][K]])

    # rhs[j-1] ⇔ sum(lits) ≤ j
    rhs = [r[n][j] for j in range(1, K + 1)]
    
    print("Number of clauses for cardinality constraints: ", solver.nof_clauses() - last_clause_count)
    return rhs


def amk_tot(solver, lits, K):
    if isinstance(lits, dict):
        lits = list(lits.values())

    top = solver.nof_vars()
    tot = ITotalizer(lits=lits, ubound=K, top_id=top)

    last_clause_count = solver.nof_clauses()
    for clause in tot.cnf.clauses:
        solver.add_clause(clause)
    print("Number of clauses for cardinality constraints: ", solver.nof_clauses() - last_clause_count)

    return tot.rhs


def add_limit_label_constraints(solver, lits, K, strategy='nsc'):
    if strategy == 'nsc':
        return amk_nsc(solver, lits, K)
    if strategy == 'tot':
        return amk_tot(solver, lits, K)
    raise ValueError("strategy must be either 'nsc' or 'tot'")




def solve_and_print(solver, var_map, rhs, num_labels, type):
    if type != 'incremental' and type != 'assumptions' and type != 'first':
        raise ValueError("Type must be either 'incremental', 'assumptions', or 'first'")
    if type == 'incremental':
        solver.add_clause([-rhs[num_labels - 1]])
    status = None
    if type == 'assumptions':
        status = solver.solve(assumptions = [-rhs[num_labels - 1]]) 
    else :
        status = solver.solve()
    if status:
        model = solver.get_model()
        assignment = {}
        for (i, v), varnum in var_map.items():
            if model[varnum-1] > 0:
                if i in assignment:
                    raise ValueError(f"Warning: variable {i} assigned multiple values.")
                assignment[i] = v
        print("Solution:")
        print(assignment)
        return assignment
    else:
        print("Cannot find solution.")
        return None

def verify_solution_simple(assignment, var, ctr_file):
    if assignment is None:
        return False
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == '\x00':
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            if i not in assignment or j not in assignment:
                return False
            vi = assignment[i]
            vj = assignment[j]
            if(vi not in var[i]) or (vj not in var[j]):
                return False
            if '>' in parts:
                distance = int(parts[4])
                if abs(vi - vj) <= distance:
                    return False
            elif '=' in parts:
                value = int(parts[4])
                if abs(vi - vj) != value:
                    return False
    return True

def main():
    start_time = time.perf_counter()
    solvers = ["glucose4", "cadical195"]
    strategies = ["nsc", "tot"]
    sat_types = ["incremental", "assumptions"]
    if len(sys.argv) < 5:
        print("Use: python main.py <dataset_folder> <strategy> <sat_type> <solver> [type_card] [distance_mode] [distance_card]")
        print("  strategy: 'nsc' (default DSE+INCSC) or 'tot' (DSE+INC)")
        print("  sat_type: 'incremental' or 'assumptions'")
        print("  solver: 'glucose4' or 'cadical195'")
        print("  type_card: exactly-one encoding id, used when distance_mode='card'; default is 1")
        print("  distance_mode: 'pairwise' (default) or 'card'")
        print("  distance_card: cardinality encoding for distance constraints; defaults to type_card")
        return
    if sys.argv[2] not in strategies:
        print("Invalid strategy. Use 'nsc' or 'tot'.")
        return
    if sys.argv[3] not in sat_types:
        print("Invalid sat_type. Use 'incremental' or 'assumptions'.")
        return
    if sys.argv[4] not in solvers:
        print("Invalid solver. Use 'glucose4' or 'cadical195'.")
        return

    dataset_folder = os.path.join("dataset", sys.argv[1])

    try:
        files = get_file_names(dataset_folder)
    except ValueError as e:
        print(e)
        return
    objective_strategy = sys.argv[2].lower()
    sat_type = sys.argv[3]
    solver_name = sys.argv[4]
    type_card = int(sys.argv[5]) if len(sys.argv) >= 6 else 1
    distance_mode = sys.argv[6].lower() if len(sys.argv) >= 7 else 'pairwise'
    if distance_mode not in ('pairwise', 'card'):
        print("Invalid distance_mode. Use 'pairwise' or 'card'.")
        return
    distance_card = int(sys.argv[7]) if len(sys.argv) >= 8 else type_card
    print("Exactly-one cardinality encoding: ", type_card)
    print("Distance constraint mode: ", distance_mode)
    print("Distance cardinality encoding: ", distance_card)
    print("Objective strategy: ", objective_strategy)
    print("SAT type: ", sat_type)
    print("Solver: ", solver_name)
    domain = read_domain(files["domain"])
    var = read_var(files["var"], domain)
    if var is None:
        print("Cannot find solution!")
        print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return

    solver = Solver(name=solver_name)
    last_var_num, var_map = create_var_map(var)

    
    
    # solver = Cadical195()
    top_id = build_constraints(solver, var, var_map, files["ctr"], type_card, distance_mode, distance_card)
    print("---------------------------------------------------")
    print("Solve first problem:")
    assignment = solve_and_print(solver, var_map, None, None, 'first')
    if assignment is None:
        print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds ")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return
    
    num_lables = len(set(assignment.values()))
    print("Number of lables used: ", num_lables)
    # if verify_solution_simple(assignment, var, files["ctr"]):
    #     print("Correct solution!")
        
        
    # else:   
    #     print("Incorrect solution!")
    #     return
    print(f"Total time: {time.perf_counter() - start_time:.5f} seconds")
    process = psutil.Process(os.getpid())
    print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
    print("--------------------------------------------------")

    lable_var_map = create_label_var_map(domain[0], top_id + 1)
    build_label_constraints(solver, var_map, lable_var_map)


    x_vars = add_limit_label_constraints(solver, lable_var_map, num_lables - 1, objective_strategy)
    
    print("Initial variable count: ", solver.nof_vars())
    print("Initial clause count: ", solver.nof_clauses())
    if objective_strategy == 'nsc':
        print("--------------------------------------------------")
        print(f"\nTrying with at most {num_lables - 1} labels...")

        assignment = solve_and_print(solver, var_map, None, None, 'first')
        if assignment is None:
            print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds ")
            process = psutil.Process(os.getpid())
            print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
            return
        
        num_lables = len(set(assignment.values()))
        print("Number of lables used: ", num_lables)
        print(f"Total time: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")

    

    while num_lables > 1:
        
        print("--------------------------------------------------")
        print(f"\nTrying with at most {num_lables - 1} labels...")
        assignment = solve_and_print(solver, var_map, x_vars, num_lables, sat_type)
        if assignment is None:
            print("No more solutions found.")
            print("Optimal number of labels used: ", num_lables)
            print(f"Total time: {time.perf_counter() - start_time:.5f} seconds")
            process = psutil.Process(os.getpid())
            print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
            
            break
        # if verify_solution_simple(assignment, var, files["ctr"]):
        #     print("Correct solution!")
        # else:
        #     print("Incorrect solution!")
        #     break
        new_num_lables = len(set(assignment.values()))
        print("Number of lables used: ", new_num_lables)
        num_lables = new_num_lables

        print(f"Total time: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")

    solver.delete()

if __name__ == "__main__":
    main()

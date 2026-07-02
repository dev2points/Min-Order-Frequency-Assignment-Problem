import os
import sys
import time
import psutil
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from pysat.card import CardEnc


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


def delete_invalid_labels(var, ctr_file):
    constraint = {}
    with open(ctr_file) as f:
        for line in f:
            if line.strip() == "\x00":
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
            if op == "=":
                new_var_u = [label for label in var[u] if any(abs(label - label_v) == distance for label_v in var[v])]
                new_var_v = [label for label in var[v] if any(abs(label - label_u) == distance for label_u in new_var_u)]
            elif op == ">":
                new_var_u = [label for label in var[u] if any(abs(label - label_v) > distance for label_v in var[v])]
                new_var_v = [label for label in var[v] if any(abs(label - label_u) > distance for label_u in new_var_u)]
            else:
                continue

            if len(new_var_u) != len(var[u]) or len(new_var_v) != len(var[v]):
                changed = True
                var[u] = new_var_u
                var[v] = new_var_v

        for i, vals in var.items():
            if len(vals) == 0:
                print(f"Warning: variable {i} has no valid labels after preprocessing.")
                return False
        if not changed:
            break
    return True


def create_var_map(var):
    var_map = {}
    counter = 1
    for i, vals in var.items():
        for v in vals:
            var_map[(i, v)] = counter
            counter += 1
    return counter, var_map


def add_exactly_one(wcnf, lits, top_id, mode, encoding=None):
    if mode == "manual":
        wcnf.append(list(lits))
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                wcnf.append([-lits[i], -lits[j]])
        return top_id

    if mode == "card":
        enc = CardEnc.equals(list(lits), bound=1, top_id=top_id, encoding=encoding)
        for clause in enc.clauses:
            wcnf.append(clause)
        return enc.nv

    raise ValueError(f"Unsupported exactly-one mode: {mode}")


def add_atmost_one(wcnf, lits, top_id, mode, encoding=None):
    if len(lits) <= 1:
        return top_id

    if mode == "manual":
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                wcnf.append([-lits[i], -lits[j]])
        return top_id

    if mode == "card":
        enc = CardEnc.atmost(list(lits), bound=1, top_id=top_id, encoding=encoding)
        for clause in enc.clauses:
            wcnf.append(clause)
        return enc.nv

    raise ValueError(f"Unsupported at-most-one mode: {mode}")


def create_order_var_map(var, var_map, last_var_num, wcnf):
    counter = last_var_num + 1
    order_var_map = {}

    for u, labels in var.items():
        for i in labels:
            order_var_map[(u, i)] = counter
            counter += 1

    for u, labels in var.items():
        if len(labels) <= 0:
            print("Warning: variable", u, "has no valid labels.")
            return

        last_i = labels[-1]
        wcnf.append([-var_map[(u, last_i)], order_var_map[(u, last_i)]])
        wcnf.append([-order_var_map[(u, last_i)], var_map[(u, last_i)]])

        for idx in range(1, len(labels)):
            wcnf.append([-order_var_map[(u, labels[idx])], order_var_map[(u, labels[idx - 1])]])
        wcnf.append([order_var_map[(u, labels[0])]])

        for idx in range(len(labels) - 1):
            wcnf.append([-var_map[(u, labels[idx])], order_var_map[(u, labels[idx])]])
            wcnf.append([-var_map[(u, labels[idx])], -order_var_map[(u, labels[idx + 1])]])
            wcnf.append(
                [-order_var_map[(u, labels[idx])], order_var_map[(u, labels[idx + 1])], var_map[(u, labels[idx])]]
            )

    return counter - 1, order_var_map


def build_constraints_POSE(wcnf, var, var_map, last_var_num, ctr_file):
    counter, order_var_map = create_order_var_map(var, var_map, last_var_num, wcnf)

    with open(ctr_file) as f:
        for line in f:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue

            u, v = int(parts[0]), int(parts[1])
            vals_u = var.get(u, [])
            vals_v = var.get(v, [])
            distance = int(parts[4])

            if "=" in parts:
                for iu in vals_u:
                    wcnf.append([-var_map[(u, iu)]] + [var_map[(v, jv)] for jv in vals_v if abs(iu - jv) == distance])
            elif ">" in parts:
                for iu in vals_u:
                    if iu - distance <= vals_v[0]:
                        for jv in vals_v:
                            if jv - iu > distance:
                                wcnf.append([-var_map[(u, iu)], order_var_map[(v, jv)]])
                                break
                    elif iu + distance >= vals_v[-1]:
                        t_limit = iu - distance
                        for t in vals_v:
                            if t >= t_limit:
                                wcnf.append([-var_map[(u, iu)], -order_var_map[(v, t)]])
                                break
                    else:
                        limit_low = iu - distance
                        limit_high = iu + distance
                        clause = [-var_map[(u, iu)]]
                        for t in vals_v:
                            if t >= limit_low:
                                clause.append(-order_var_map[(v, t)])
                                break
                        for t in vals_v:
                            if t > limit_high:
                                clause.append(order_var_map[(v, t)])
                                break
                        if len(clause) > 1:
                            wcnf.append(clause)
    return counter


def build_constraints_DSE(wcnf, var, var_map, ctr_file, _type_card):
    top_id = max(var_map.values())

    for i, vals in var.items():
        top_id = add_exactly_one(wcnf, [var_map[(i, v)] for v in vals], top_id, mode="manual")

    with open(ctr_file) as f:
        for line in f:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            vals_i = var.get(i, [])
            vals_j = var.get(j, [])

            if ">" in parts:
                distance = int(parts[4])
                for vi in vals_i:
                    for vj in vals_j:
                        if abs(vi - vj) <= distance:
                            wcnf.append([-var_map[(i, vi)], -var_map[(j, vj)]])
            elif "=" in parts:
                target = int(parts[4])
                for vi in vals_i:
                    wcnf.append([-var_map[(i, vi)]] + [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) == target])

    return top_id


def build_constraints_CARD(wcnf, var, var_map, ctr_file, exact_encoding, amo_encoding):
    top_id = max(var_map.values())

    for i, vals in var.items():
        top_id = add_exactly_one(
            wcnf,
            [var_map[(i, v)] for v in vals],
            top_id,
            mode="card",
            encoding=exact_encoding,
        )

    with open(ctr_file) as f:
        for line in f:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue
            i, j = int(parts[0]), int(parts[1])
            vals_i = var.get(i, [])
            vals_j = var.get(j, [])

            if ">" in parts:
                distance = int(parts[4])
                for vi in vals_i:
                    forbidden = [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) <= distance]
                    if forbidden:
                        top_id = add_atmost_one(
                            wcnf,
                            [var_map[(i, vi)]] + forbidden,
                            top_id,
                            mode="card",
                            encoding=amo_encoding,
                        )
            elif "=" in parts:
                target = int(parts[4])
                for vi in vals_i:
                    wcnf.append([-var_map[(i, vi)]] + [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) == target])

    return top_id


def create_label_var_map(labels, start_index):
    label_var_map = {}
    current = start_index
    for lb in labels:
        label_var_map[lb] = current
        current += 1
    return label_var_map


def build_maxsat_label_constraints(wcnf, var_map, label_var_map):
    for (i, v), varnum in var_map.items():
        lb_varnum = label_var_map[v]
        wcnf.append([-varnum, lb_varnum])

    for v, lb_varnum in label_var_map.items():
        wcnf.append([-lb_varnum], weight=1)


def main():
    start_time = time.perf_counter()

    helpers = (
        "Usage: python3 main.py <dataset_folder> <encoding_method> [<encoding_1>] [<encoding_2>]\n"
        "  encoding_method: 'POSE', 'DSE', or 'CARD'\n"
        "  DSE: optional third argument is accepted for backward compatibility but ignored.\n"
        "  CARD: encoding_1 controls exactly-one, encoding_2 controls AMO for distance constraints.\n"
        "        If encoding_2 is omitted, it defaults to encoding_1.\n"
    )

    if len(sys.argv) < 3:
        print(helpers)
        return

    encoding_method = sys.argv[2].upper()
    if encoding_method not in ["POSE", "DSE", "CARD"]:
        print(f"Error: invalid encoding method.\n{helpers}")
        return

    dse_compat_encoding = 1
    exact_encoding = 1
    amo_encoding = 1

    if encoding_method == "DSE" and len(sys.argv) >= 4:
        try:
            dse_compat_encoding = int(sys.argv[3])
        except ValueError:
            print("Error: DSE compatibility encoding must be an integer.")
            return

    if encoding_method == "CARD":
        try:
            exact_encoding = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
            amo_encoding = int(sys.argv[4]) if len(sys.argv) >= 5 else exact_encoding
        except ValueError:
            print("Error: CARD encodings must be integers.")
            return

    dataset_folder = os.path.join("dataset", sys.argv[1])

    try:
        files = get_file_names(dataset_folder)
    except ValueError as e:
        print(e)
        return

    domain = read_domain(files["domain"])
    var = read_var(files["var"], domain)
    if var is None:
        print("Cannot find solution!")
        print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return
    if not delete_invalid_labels(var, files["ctr"]):
        print("No solution found in the preprocessing step!")
        return

    last_var_num, var_map = create_var_map(var)
    wcnf = WCNF()

    if encoding_method == "POSE":
        print("--- POSE ---")
        top_var_num = build_constraints_POSE(wcnf, var, var_map, last_var_num, files["ctr"])
    elif encoding_method == "DSE":
        print(f"--- DSE [compat arg: {dse_compat_encoding}] ---")
        top_var_num = build_constraints_DSE(wcnf, var, var_map, files["ctr"], dse_compat_encoding)
    else:
        print(f"--- CARD [Exactly-One: {exact_encoding}, AMO: {amo_encoding}] ---")
        top_var_num = build_constraints_CARD(wcnf, var, var_map, files["ctr"], exact_encoding, amo_encoding)

    label_var_map = create_label_var_map(domain[0], top_var_num + 1)
    build_maxsat_label_constraints(wcnf, var_map, label_var_map)

    print(" solving MaxSAT (RC2)...")

    with RC2(wcnf) as rc2:
        model = rc2.compute()

        if model:
            assignment = {}
            for (i, v), varnum in var_map.items():
                if varnum in model:
                    if i in assignment:
                        raise ValueError(f"Warning: variable {i} assigned multiple values.")
                    assignment[i] = v

            num_labels = len(set(assignment.values()))
            print("\n--------------------------------------------------")
            print("Found solution!")
            print(f"Number of labels used: {num_labels}")
        else:
            print("No solution found.")

    end_time = time.perf_counter()
    print("--------------------------------------------------")
    print(f"Time taken: {end_time - start_time:.5f} seconds")
    process = psutil.Process(os.getpid())
    print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")


if __name__ == "__main__":
    main()
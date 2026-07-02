#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
import time
from typing import Dict, Optional, Tuple

from pysat.card import CardEnc
from pysat.formula import WCNF


def build_paths(dataset: str, encoding: str, exact_encoding: Optional[int], amo_encoding: Optional[int]) -> Tuple[str, str, str]:
    if encoding == "POSE":
        group = "POSE"
        filename = f"{dataset}_POSE.wcnf"
    elif encoding == "DSE":
        group = "DSE"
        filename = f"{dataset}_DSE.wcnf"
    else:
        if exact_encoding is None:
            raise ValueError("exact encoding is required for CARD")
        if amo_encoding is None:
            amo_encoding = exact_encoding
        group = f"CARD_{exact_encoding}_{amo_encoding}"
        filename = f"{dataset}_CARD_{exact_encoding}_{amo_encoding}.wcnf"

    wcnf_dir = os.path.join("wcnf", "processing", group)
    decode_dir = os.path.join("results", "processing", "decode", group)
    return os.path.join(wcnf_dir, filename), decode_dir, group


def get_file_names(dataset_folder: str) -> Dict[str, str]:
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


def read_domain(file_path: str) -> list:
    domain = []
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            values = list(map(int, parts[2:]))
            domain.append(values)
    return domain


def read_var(file_path: str, domain: list) -> Dict[int, list]:
    var = {}
    with open(file_path, encoding="utf-8", errors="ignore") as f:
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
    return var



def delete_invalid_labels(var: Dict[int, list], ctr_file: str) -> bool:
    constraints = {}
    with open(ctr_file, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip() == "\x00":
                continue
            parts = line.strip().split()
            if not parts:
                continue
            u, v = int(parts[0]), int(parts[1])
            distance = int(parts[4])
            constraints[(u, v)] = (parts[3], distance)

    while True:
        changed = False
        for (u, v), (op, distance) in constraints.items():
            if op == "=":
                new_u = [lb for lb in var[u] if any(abs(lb - lb_v) == distance for lb_v in var[v])]
                new_v = [lb for lb in var[v] if any(abs(lb - lb_u) == distance for lb_u in new_u)]
            elif op == ">":
                new_u = [lb for lb in var[u] if any(abs(lb - lb_v) > distance for lb_v in var[v])]
                new_v = [lb for lb in var[v] if any(abs(lb - lb_u) > distance for lb_u in new_u)]
            else:
                continue

            if len(new_u) != len(var[u]) or len(new_v) != len(var[v]):
                var[u] = new_u
                var[v] = new_v
                changed = True

        for _, vals in var.items():
            if len(vals) == 0:
                return False
        if not changed:
            break

    return True


def create_var_map(var: Dict[int, list]) -> Tuple[int, Dict[Tuple[int, int], int]]:
    var_map = {}
    counter = 1
    for i, vals in var.items():
        for v in vals:
            var_map[(i, v)] = counter
            counter += 1
    return counter, var_map


def add_exactly_one(wcnf: WCNF, lits: list, top_id: int, mode: str, encoding: Optional[int], stats: dict) -> int:
    if mode == "manual":
        wcnf.append(list(lits))
        stats["card_clauses"] += 1
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                wcnf.append([-lits[i], -lits[j]])
                stats["card_clauses"] += 1
        return top_id

    enc = CardEnc.equals(list(lits), bound=1, top_id=top_id, encoding=encoding)
    for clause in enc.clauses:
        wcnf.append(clause)
    stats["card_clauses"] += len(enc.clauses)
    return enc.nv


def add_atmost_one(wcnf: WCNF, lits: list, top_id: int, mode: str, encoding: Optional[int], stats: dict) -> int:
    if len(lits) <= 1:
        return top_id

    if mode == "manual":
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                wcnf.append([-lits[i], -lits[j]])
                stats["card_clauses"] += 1
        return top_id

    enc = CardEnc.atmost(list(lits), bound=1, top_id=top_id, encoding=encoding)
    for clause in enc.clauses:
        wcnf.append(clause)
    stats["card_clauses"] += len(enc.clauses)
    return enc.nv


def create_order_var_map(
    var: Dict[int, list],
    var_map: Dict[Tuple[int, int], int],
    last_var_num: int,
    wcnf: WCNF,
    stats: dict,
) -> Tuple[int, Dict[Tuple[int, int], int]]:
    counter = last_var_num + 1
    order_var_map = {}

    for u, labels in var.items():
        for i in labels:
            order_var_map[(u, i)] = counter
            counter += 1

    stats["order_vars"] = len(order_var_map)

    for u, labels in var.items():
        if not labels:
            return counter - 1, order_var_map

        last_i = labels[-1]
        wcnf.append([-var_map[(u, last_i)], order_var_map[(u, last_i)]])
        wcnf.append([-order_var_map[(u, last_i)], var_map[(u, last_i)]])
        stats["order_clauses"] += 2

        for idx in range(1, len(labels)):
            wcnf.append([-order_var_map[(u, labels[idx])], order_var_map[(u, labels[idx - 1])]])
            stats["order_clauses"] += 1

        wcnf.append([order_var_map[(u, labels[0])]])
        stats["order_clauses"] += 1

        for idx in range(len(labels) - 1):
            wcnf.append([-var_map[(u, labels[idx])], order_var_map[(u, labels[idx])]])
            wcnf.append([-var_map[(u, labels[idx])], -order_var_map[(u, labels[idx + 1])]])
            wcnf.append([-order_var_map[(u, labels[idx])], order_var_map[(u, labels[idx + 1])], var_map[(u, labels[idx])]])
            stats["order_clauses"] += 3

    return counter - 1, order_var_map


def build_constraints_pose(
    wcnf: WCNF,
    var: Dict[int, list],
    var_map: Dict[Tuple[int, int], int],
    last_var_num: int,
    ctr_file: str,
    stats: dict,
) -> int:
    counter, order_var_map = create_order_var_map(var, var_map, last_var_num, wcnf, stats)

    with open(ctr_file, encoding="utf-8", errors="ignore") as f:
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
                    stats["distance_clauses"] += 1
            elif ">" in parts:
                for iu in vals_u:
                    if vals_v and iu - distance <= vals_v[0]:
                        for jv in vals_v:
                            if jv - iu > distance:
                                wcnf.append([-var_map[(u, iu)], order_var_map[(v, jv)]])
                                stats["distance_clauses"] += 1
                                break
                    elif vals_v and iu + distance >= vals_v[-1]:
                        threshold = iu - distance
                        for t in vals_v:
                            if t >= threshold:
                                wcnf.append([-var_map[(u, iu)], -order_var_map[(v, t)]])
                                stats["distance_clauses"] += 1
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
                            stats["distance_clauses"] += 1

    return counter


def build_constraints_dse(
    wcnf: WCNF,
    var: Dict[int, list],
    var_map: Dict[Tuple[int, int], int],
    ctr_file: str,
    _compat_card: Optional[int],
    stats: dict,
) -> int:
    top_id = max(var_map.values())

    for i, vals in var.items():
        top_id = add_exactly_one(wcnf, [var_map[(i, v)] for v in vals], top_id, "manual", None, stats)

    with open(ctr_file, encoding="utf-8", errors="ignore") as f:
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
                            stats["distance_clauses"] += 1
            elif "=" in parts:
                target = int(parts[4])
                for vi in vals_i:
                    wcnf.append([-var_map[(i, vi)]] + [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) == target])
                    stats["distance_clauses"] += 1

    stats["card_aux_vars"] = top_id - max(var_map.values())
    return top_id


def build_constraints_card(
    wcnf: WCNF,
    var: Dict[int, list],
    var_map: Dict[Tuple[int, int], int],
    ctr_file: str,
    exact_encoding: int,
    amo_encoding: int,
    stats: dict,
) -> int:
    top_id = max(var_map.values())

    for i, vals in var.items():
        top_id = add_exactly_one(
            wcnf,
            [var_map[(i, v)] for v in vals],
            top_id,
            "card",
            exact_encoding,
            stats,
        )

    with open(ctr_file, encoding="utf-8", errors="ignore") as f:
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
                            "card",
                            amo_encoding,
                            stats,
                        )
            elif "=" in parts:
                target = int(parts[4])
                for vi in vals_i:
                    wcnf.append([-var_map[(i, vi)]] + [var_map[(j, vj)] for vj in vals_j if abs(vi - vj) == target])
                    stats["distance_clauses"] += 1

    stats["card_aux_vars"] = top_id - max(var_map.values())
    return top_id


def create_label_var_map(labels: list, start_index: int) -> Dict[int, int]:
    label_var_map = {}
    current = start_index
    for lb in labels:
        label_var_map[lb] = current
        current += 1
    return label_var_map


def build_maxsat_label_constraints(
    wcnf: WCNF,
    var_map: Dict[Tuple[int, int], int],
    label_var_map: Dict[int, int],
    stats: dict,
) -> None:
    for (_, v), varnum in var_map.items():
        lb_varnum = label_var_map[v]
        wcnf.append([-varnum, lb_varnum])
        stats["label_link_clauses"] += 1

    for _, lb_varnum in label_var_map.items():
        wcnf.append([-lb_varnum], weight=1)

    stats["label_vars"] = len(label_var_map)
    stats["soft_clauses"] = len(label_var_map)


def add_wcnf_header_comments(outfile: str, dataset: str, encoding: str, stats: dict, wcnf: WCNF) -> None:
    with open(outfile, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    comments = [
        f"c Dataset: {dataset}",
        f"c Encoding: {encoding}",
        f"c DecisionVars: {stats['decision_vars']}",
        f"c OrderVars: {stats['order_vars']}",
        f"c CardinalityAuxVars: {stats['card_aux_vars']}",
        f"c LabelVars: {stats['label_vars']}",
        f"c TotalVars: {wcnf.nv}",
        f"c OrderClauses: {stats['order_clauses']}",
        f"c CardinalityClauses: {stats['card_clauses']}",
        f"c DistanceClauses: {stats['distance_clauses']}",
        f"c LabelLinkClauses: {stats['label_link_clauses']}",
        f"c SoftClauses: {stats['soft_clauses']}",
        f"c HardClauses: {len(wcnf.hard)}",
        f"c TotalClauses: {len(wcnf.hard) + len(wcnf.soft)}",
        "",
    ]

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(comments))
        f.write(content)


def generate_wcnf(
    dataset: str,
    encoding: str,
    exact_encoding: Optional[int],
    amo_encoding: Optional[int],
    outfile: str,
) -> Tuple[bool, Dict[Tuple[int, int], int], Dict[int, list]]:
    dataset_folder = os.path.join("dataset", dataset)
    files = get_file_names(dataset_folder)
    domain = read_domain(files["domain"])
    var = read_var(files["var"], domain)
    if var is None:
        return False, {}, {}

    if not delete_invalid_labels(var, files["ctr"]):
        print("[SKIP] No solution found in preprocessing step")
        return False, {}, {}

    last_var_num, var_map = create_var_map(var)
    wcnf = WCNF()
    stats = {
        "decision_vars": len(var_map),
        "order_vars": 0,
        "card_aux_vars": 0,
        "label_vars": 0,
        "order_clauses": 0,
        "card_clauses": 0,
        "distance_clauses": 0,
        "label_link_clauses": 0,
        "soft_clauses": 0,
    }

    if encoding == "POSE":
        top_var_num = build_constraints_pose(wcnf, var, var_map, last_var_num, files["ctr"], stats)
        encoding_name = "POSE"
    elif encoding == "DSE":
        top_var_num = build_constraints_dse(wcnf, var, var_map, files["ctr"], exact_encoding, stats)
        encoding_name = "DSE"
    else:
        if exact_encoding is None:
            raise ValueError("CARD requires at least one encoding id")
        if amo_encoding is None:
            amo_encoding = exact_encoding
        top_var_num = build_constraints_card(wcnf, var, var_map, files["ctr"], exact_encoding, amo_encoding, stats)
        encoding_name = f"CARD_{exact_encoding}_{amo_encoding}"

    label_var_map = create_label_var_map(domain[0], top_var_num + 1)
    build_maxsat_label_constraints(wcnf, var_map, label_var_map, stats)

    wcnf.to_file(outfile)
    add_wcnf_header_comments(outfile, dataset, encoding_name, stats, wcnf)
    return True, var_map, var


def run_solver(wcnf_file: str) -> subprocess.CompletedProcess:
    cmd = ["./EvalMaxSAT_bin", wcnf_file]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def parse_solver_output(text: str) -> Tuple[Optional[str], Optional[int], str]:
    status = None
    objective = None
    bit_chunks = []
    collecting_bits = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("s "):
            status = line[2:].strip()
            collecting_bits = False
            continue

        if line.startswith("o "):
            token = line[2:].strip().split()[0]
            try:
                objective = int(token)
            except ValueError:
                pass
            collecting_bits = False
            continue

        if line.startswith("v "):
            bit_chunks.append(re.sub(r"\s+", "", line[2:]))
            collecting_bits = True
            continue

        if collecting_bits and re.fullmatch(r"[01]+", line):
            bit_chunks.append(line)
            continue

        collecting_bits = False

    return status, objective, "".join(bit_chunks)


def decode_solution(bitstring: str, var_map: Dict[Tuple[int, int], int], var_domains: Dict[int, list]) -> Tuple[Dict[int, int], bool]:
    inv_map = {varnum: key for key, varnum in var_map.items()}
    solution: Dict[int, int] = {}

    for varnum in range(1, len(var_map) + 1):
        if varnum > len(bitstring):
            break
        if bitstring[varnum - 1] != "1":
            continue
        i, label = inv_map[varnum]
        solution[i] = label

    feasible_assignment = len(solution) == len(var_domains)
    return solution, feasible_assignment


def write_decode_file(
    path: str,
    dataset: str,
    encoding: str,
    status: Optional[str],
    objective: Optional[int],
    solution: Dict[int, int],
    feasible_assignment: bool,
) -> None:
    used_labels = sorted(set(solution.values()))
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"dataset={dataset}\n")
        f.write(f"encoding={encoding}\n")
        f.write(f"solver_status={status}\n")
        f.write(f"objective={objective}\n")
        f.write(f"assigned_vars={len(solution)}\n")
        f.write(f"assignment_complete={feasible_assignment}\n")
        f.write(f"num_labels_used={len(used_labels)}\n")
        f.write("labels_used=" + ",".join(str(x) for x in used_labels) + "\n")

        for var_id in sorted(solution):
            f.write(f"x[{var_id}]={solution[var_id]}\n")


def finish(return_code: int, start_time: float) -> int:
    print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds")
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate WCNF, solve with EvalMaxSAT_bin, and decode a feasible assignment."
    )
    parser.add_argument("dataset", help="Dataset name, e.g. scen04")
    parser.add_argument("encoding", choices=["POSE", "DSE", "CARD"], help="Encoding type")
    parser.add_argument("exact_encoding", nargs="?", type=int, default=None, help="Encoding for exactly-one (CARD) or compatibility arg (DSE)")
    parser.add_argument("amo_encoding", nargs="?", type=int, default=None, help="Encoding for AMO distance constraints (CARD)")
    args = parser.parse_args()

    dataset = args.dataset
    encoding = args.encoding
    exact_encoding = args.exact_encoding
    amo_encoding = args.amo_encoding
    start_time = time.perf_counter()

    if encoding == "CARD" and exact_encoding is None:
        print("[ERROR] CARD requires at least one encoding id (example: 1 or 1 1)")
        return finish(2, start_time)

    if encoding != "CARD":
        amo_encoding = None

    wcnf_file, decode_dir, group = build_paths(dataset, encoding, exact_encoding, amo_encoding)
    os.makedirs(os.path.dirname(wcnf_file), exist_ok=True)
    os.makedirs(decode_dir, exist_ok=True)
    if os.path.exists(wcnf_file):
        os.remove(wcnf_file)

    display_encoding = encoding
    if encoding == "CARD":
        display_encoding = f"CARD,{exact_encoding},{amo_encoding if amo_encoding is not None else exact_encoding}"
    elif encoding == "DSE" and exact_encoding is not None:
        display_encoding = f"DSE,{exact_encoding}"

    print(f"[INFO] Generating WCNF for {dataset} ({display_encoding})")
    try:
        generated, var_map, var_domains = generate_wcnf(dataset, encoding, exact_encoding, amo_encoding, wcnf_file)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return finish(2, start_time)
    except Exception as exc:
        print(f"[ERROR] Generation failed: {exc}")
        return finish(1, start_time)

    if not generated or not os.path.exists(wcnf_file):
        print(f"[SKIP] No WCNF generated for {dataset} ({group}); preprocessing found no feasible solution")
        return finish(0, start_time)

    print(f"[INFO] Solving {wcnf_file}")
    solve = run_solver(wcnf_file)
    if solve.stdout:
        print(solve.stdout, end="")
    if solve.stderr:
        print(solve.stderr, end="", file=sys.stderr)

    status, objective, bitstring = parse_solver_output(solve.stdout)

    solution, complete = decode_solution(bitstring, var_map, var_domains)
    decode_file = os.path.join(decode_dir, f"{dataset}.decoded.txt")
    decode_encoding = "DSE" if encoding == "DSE" else ("POSE" if encoding == "POSE" else f"CARD_{exact_encoding}_{amo_encoding if amo_encoding is not None else exact_encoding}")
    write_decode_file(decode_file, dataset, decode_encoding, status, objective, solution, complete)

    used_labels = len(set(solution.values()))
    print("[INFO] Decode summary")
    print(f"[INFO] status={status}, objective={objective}, assigned_vars={len(solution)}, complete={complete}, labels_used={used_labels}")
    print(f"[INFO] Decoded assignment file: {decode_file}")

    return finish(0, start_time)


if __name__ == "__main__":
    raise SystemExit(main())

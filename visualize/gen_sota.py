from __future__ import annotations
from pathlib import Path
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR if (BASE_DIR / "result_file").exists() else BASE_DIR.parent
CSV_PATH = PROJECT_DIR / "result_file" / "preprocess.csv"

# Explicit BKS values provided by the user/reference.
BKS_OVERRIDES = {
    "C01": 16,
    "C02": 14,
    "C03": 14,
    "C04": 46,
    "C11": 22,
    "G01": 18,
    "G02": 14,
    "G08": 18,
    "G09": 18,
    "G14": 8,
}


def _load_normalized_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load CSV into long format with columns: Bench, Metric, solver columns."""
    # Most result CSVs include a first metadata row ("UNKNOWN").
    df = pd.read_csv(csv_path, skiprows=1)

    # New format (final_preprocess/final_no_preprocess): Bench, unnamed metric col, solver ids.
    if "Bench" in df.columns:
        cols = list(df.columns)
        if len(cols) >= 2:
            cols[1] = "Metric"
            df.columns = cols
        df["Bench"] = df["Bench"].astype(str).str.strip()
        df["Metric"] = df["Metric"].astype(str).str.strip()
        return df

    # Legacy wide format (preprocess/nopreprocess): Problem + repeated Value/Time/Status blocks.
    if "Problem" in df.columns:
        solver_blocks = [
            ("POSE_INCSC", "", "", ""),
            ("POSE_INC", ".1", ".1", ".1"),
            ("DSE", ".2", ".2", ".2"),
            ("GUR", ".3", ".3", ".3"),
            ("CPX_MP", ".4", ".4", ".4"),
            ("CPX_CP", ".5", ".5", ".5"),
        ]

        rows: list[dict[str, object]] = []
        for _, row in df.iterrows():
            bench = str(row.get("Problem", "")).strip()
            if not bench:
                continue

            for metric_label, base_col in [
                ("Solution", "Value"),
                ("Total time", "Time"),
                ("Status", "Status"),
            ]:
                rec: dict[str, object] = {"Bench": bench, "Metric": metric_label}
                for solver_id, v_sfx, t_sfx, st_sfx in solver_blocks:
                    suffix = {"Value": v_sfx, "Time": t_sfx, "Status": st_sfx}[base_col]
                    col_name = f"{base_col}{suffix}"
                    rec[solver_id] = row.get(col_name, None)
                rows.append(rec)

        return pd.DataFrame(rows)

    raise ValueError(
        f"Unsupported CSV format in {csv_path}. Expected columns containing 'Bench' or 'Problem'."
    )


def generate_super_master_table(csv_path: Path) -> str:
    df = _load_normalized_dataframe(csv_path)

    # Danh sách solver theo thứ tự hiển thị trong bảng.
    solvers = ["POSE_INCSC", "POSE_INC", "DSE", "GUR", "CPX_CP", "CPX_MP"]
    records = []
    # Aggregate runtime per solver (sum of available numeric times across instances).
    solver_total_times = {s_id: 0.0 for s_id in solvers}
    # Count status occurrences per solver for summary rows.
    solver_status_counts = {s_id: {"OPT": 0, "INF": 0, "TO": 0} for s_id in solvers}
    benches = df["Bench"].unique()

    for bench in benches:
        row_data = {"Bench": bench}
        all_times = []

        for s_id in solvers:
            sub = df[df["Bench"] == bench]
            sol_val = sub[sub["Metric"] == "Solution"][s_id].values
            time_val = sub[sub["Metric"] == "Total time"][s_id].values
            stat_val = sub[sub["Metric"] == "Status"][s_id].values

            # Status chuẩn hóa
            raw_st = str(stat_val[0]).strip().upper() if len(stat_val) > 0 else ""
            if raw_st in ["TO", "TIMEOUT", "TL"]:
                st = "TO"
            elif raw_st in ["MO", "OOM"]:
                st = "MO"
            elif raw_st in ["INF", "INFEASIBLE", "UNSAT"]:
                st = "INF"
            elif raw_st in ["OPT", "OPTIMAL"]:
                st = "OPT"
            else:
                st = "-"
            if st in solver_status_counts[s_id]:
                solver_status_counts[s_id][st] += 1

            # Solution
            s = "-"
            if len(sol_val) > 0 and pd.notna(sol_val[0]):
                try:
                    val = str(sol_val[0]).strip()
                    if val not in ["", "-", "nan"]:
                        s = str(int(float(val)))
                except:
                    s = "-"

            # Time
            t = None
            if len(time_val) > 0:
                try:
                    raw_t = str(time_val[0]).strip()
                    if raw_t not in ["", "-", "nan"]:
                        t = float(raw_t)
                except:
                    t = None

            row_data[f"{s_id}_S"] = s
            row_data[f"{s_id}_T"] = t
            row_data[f"{s_id}_St"] = st
            if t is not None:
                all_times.append(t)
                solver_total_times[s_id] += t

        # Best known solution: use explicit override first, then fallback to min valid objective.
        numeric_solutions = []
        for s_id in solvers:
            sval = row_data[f"{s_id}_S"]
            if sval != "-":
                try:
                    numeric_solutions.append(float(sval))
                except Exception:
                    pass
        row_data["BKS"] = _resolve_bks(row_data["Bench"], numeric_solutions)

        # Tìm min time để bold
        min_time = min(all_times) if all_times else None
        row_data["min_time"] = min_time
        records.append(row_data)

    # --- Xây dựng LaTeX ---
    lines = [
        "\\begin{table*}[htbp]",
        "\\centering",
        "\\caption{Comprehensive Comparison between Proposed POSE+INCSC and Exact Methods}",
        "\\label{tab:super_master}",
        "\\setlength{\\tabcolsep}{2.5pt}",
        "\\renewcommand{\\arraystretch}{1.05}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{@{}l c ccc ccc ccc ccc ccc ccc ccc@{}}",
        "\\toprule",
        "\\textbf{Inst.} & \\textbf{BKS \\cite{Gomez2023MO}} & \\multicolumn{3}{c}{\\textbf{POSE+INCSC}} & \\multicolumn{3}{c}{\\textbf{POSE+INC}} & \\multicolumn{3}{c}{\\textbf{DSE+INCSC}} & \\multicolumn{3}{c}{\\textbf{GUROBI}} & \\multicolumn{3}{c}{\\textbf{CPLEX-CP}} & \\multicolumn{3}{c}{\\textbf{CPLEX-MIP}} " + r"\\",
        "\\cmidrule(lr){3-5} \\cmidrule(lr){6-8} \\cmidrule(lr){9-11} \\cmidrule(lr){12-14} \\cmidrule(lr){15-17} \\cmidrule(lr){18-20}",
        " &  & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status} " + r"\\",
        "\\midrule",
    ]

    for r in records:
        bench_label = _format_bench_label(r["Bench"])
        row_str = f"{bench_label} & {r['BKS']}"
        for s_id in solvers:
            s_val = r[f"{s_id}_S"]
            t_val = r[f"{s_id}_T"]
            st_val = r[f"{s_id}_St"]

            if t_val is None:
                # Keep explicit status in the Status column; use '-' only when time is truly missing.
                t_str = "-"
            else:
                formatted = f"{t_val:.2f}"
                # Do not bold timeout rows; TO is already highlighted by status.
                if st_val != "TO" and r["min_time"] is not None and t_val <= r["min_time"]:
                    t_str = f"\\textbf{{{formatted}}}"
                else:
                    t_str = formatted

            row_str += f" & {s_val} & {t_str} & {st_val}"
        lines.append(row_str + " \\\\")

    # Final aggregate row: cumulative runtime of each solver over all instances.
    total_row = "\\midrule\n\\textbf{Total Time} & -"
    min_total_time = min(solver_total_times.values()) if solver_total_times else None
    for s_id in solvers:
        total_val = solver_total_times[s_id]
        total_fmt = f"{total_val:.2f}"
        if min_total_time is not None and abs(total_val - min_total_time) <= 1e-9:
            total_fmt = f"\\textbf{{{total_fmt}}}"
        total_row += f" & - & {total_fmt} & -"
    lines.append(total_row + " \\\\")

    # Status count summary rows (#OPT, #INF, #TO) in each solver Status sub-column.
    for status_key in ["OPT", "INF", "TO"]:
        summary_row = f"\\#{status_key} & -"
        for s_id in solvers:
            summary_row += f" & - & - & {solver_status_counts[s_id][status_key]}"
        lines.append(summary_row + " \\\\")

    lines.extend([
        "\\bottomrule",
        "\\multicolumn{20}{l}{\\footnotesize \\textbf{BKS}: Best Known Solution (including non-optimality solution)\\cite{Gomez2023MO}.} " + r"\\",
        "\\multicolumn{20}{l}{\\footnotesize All values in \\textbf{Time} columns and the \\textbf{Total Time} row are reported in seconds (s).} " + r"\\",
        "\\multicolumn{20}{l}{\\footnotesize \\textbf{OPT}: Optimal, \\textbf{INF}: Infeasible, \\textbf{TO}: Timeout (600s).} " + r"\\",
        "\\multicolumn{20}{l}{\\footnotesize Bold time values indicate the fastest method with minimum solution value.}",
        "\\end{tabular}%",
        "}",
        "\\end{table*}",
    ])
    return "\n".join(lines)


def _format_bench_label(name: str) -> str:
    """Abbreviate bench labels for compact table display."""
    raw = str(name).strip()

    # scen01 -> C01, graph03 -> G03 (same normalization used by BKS mapping)
    key = _canonical_bench_key(raw)
    if re.fullmatch(r"[CG]\d{2}", key):
        return key

    m = re.match(r"^TUD(\d+)\.(\d+)$", raw, flags=re.IGNORECASE)
    if not m:
        return raw
    family = m.group(1)
    suffix = m.group(2)
    # Keep the leading family digit: TUD900.1 -> T9.1, TUD200.5 -> T2.5.
    return f"T{family[0]}.{suffix}"


def _canonical_bench_key(name: str) -> str:
    """Normalize bench labels so overrides match both legacy and short names."""
    raw = str(name).strip()
    low = raw.lower()

    m = re.match(r"^scen(\d+)$", low)
    if m:
        return f"C{int(m.group(1)):02d}"

    m = re.match(r"^graph(\d+)$", low)
    if m:
        return f"G{int(m.group(1)):02d}"

    m = re.match(r"^([cg])(\d+)$", raw, flags=re.IGNORECASE)
    if m:
        return f"{m.group(1).upper()}{int(m.group(2)):02d}"

    return raw


def _resolve_bks(bench_name: str, numeric_solutions: list[float]) -> str:
    key = _canonical_bench_key(bench_name)
    if key in BKS_OVERRIDES:
        return str(int(BKS_OVERRIDES[key]))
    return str(int(min(numeric_solutions))) if numeric_solutions else "-"


if __name__ == "__main__":
    print(generate_super_master_table(CSV_PATH))
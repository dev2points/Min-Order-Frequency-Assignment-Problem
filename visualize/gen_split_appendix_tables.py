from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import re


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
COMPARISON_CSV = PROJECT_DIR / "stats_csv" / "generated_comparison" / "preprocess_new.csv"
OUTPUT_DIR = BASE_DIR / "tables"


@dataclass(frozen=True)
class MethodSpec:
    label: str
    source_label: str


SAT_CORE_METHODS = [
    MethodSpec("POSE+INCSC", "POSE+INCSC"),
    MethodSpec("POSE+INC", "POSE+INC"),
    MethodSpec("POSE+MaxSAT-RC2", "MaxSAT RC2 POSE"),
    MethodSpec("POSE+EvalMaxSAT", "evalmaxsat POSE"),
    MethodSpec("DSE+INCSC", "DSE+INCSC"),
    MethodSpec("CARD-Seq+INCSC", "Card seqcounter+INCSC"),
    MethodSpec("CARD-Totalizer+INCSC", "Card totalizer+INCSC"),
    MethodSpec("CARD-CardNet+INCSC", "Card cardnetwrk+INCSC"),
]


SOLVER_METHODS = [
    MethodSpec("POSE+INCSC", "POSE+INCSC"),
    MethodSpec("Gurobi", "Gurobi"),
    MethodSpec("CPLEX/MIP", "CPLEX/MIP"),
    MethodSpec("CPLEX/CP", "CPLEX/CP"),
    MethodSpec("CP-SAT", "CP-SAT"),
]


def format_instance(name: str) -> str:
    raw = str(name).strip()
    lower = raw.lower()
    match = re.fullmatch(r"scen(\d+)", lower)
    if match:
        return f"C{int(match.group(1)):02d}"
    match = re.fullmatch(r"graph(\d+)", lower)
    if match:
        return f"G{int(match.group(1)):02d}"
    match = re.fullmatch(r"tud(\d+)\.(\d+)", lower)
    if match:
        return f"T{match.group(1)[0]}.{match.group(2)}"
    return raw


def normalize_status(value: str) -> str:
    raw = str(value).strip().upper()
    if raw in {"OPT", "OPTIMAL"}:
        return "OPT"
    if raw in {"INF", "INFEASIBLE", "UNSAT"}:
        return "INF"
    if raw in {"TO", "TIMEOUT", "TL"}:
        return "TO"
    if raw in {"MO", "OOM"}:
        return "MO"
    return "-" if raw in {"", "-", "NAN"} else raw


def format_solution(value: str) -> str:
    raw = str(value).strip()
    if raw in {"", "-", "nan", "None"}:
        return "-"
    try:
        return str(int(float(raw)))
    except ValueError:
        return raw


def parse_time(value: str) -> float | None:
    raw = str(value).strip()
    if raw in {"", "-", "nan", "None"}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def format_time(value: float | None, bold: bool = False) -> str:
    if value is None:
        return "-"
    if abs(value - round(value)) <= 1e-9:
        formatted = f"{int(round(value))}"
    elif 0 < abs(value) < 0.01:
        formatted = f"{value:.4f}".rstrip("0").rstrip(".")
    else:
        formatted = f"{value:.2f}"
    return f"\\textbf{{{formatted}}}" if bold else formatted


def method_positions(header_row: list[str]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, label in enumerate(header_row):
        cleaned = label.strip()
        if cleaned:
            positions[cleaned] = index
    return positions


def read_records(csv_path: Path, methods: list[MethodSpec]) -> list[dict[object, object]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        raise ValueError(f"CSV has fewer than two header rows: {csv_path}")

    positions = method_positions(rows[0])
    records: list[dict[object, object]] = []

    for raw_row in rows[2:]:
        if not raw_row or not raw_row[0].strip():
            continue
        record: dict[object, object] = {"instance": raw_row[0].strip()}
        for method in methods:
            if method.source_label not in positions:
                raise KeyError(f"Missing method '{method.source_label}' in {csv_path}")
            start = positions[method.source_label]
            value = raw_row[start] if start < len(raw_row) else "-"
            time = raw_row[start + 1] if start + 1 < len(raw_row) else "-"
            status = raw_row[start + 2] if start + 2 < len(raw_row) else "-"
            record[(method.label, "value")] = format_solution(value)
            record[(method.label, "time")] = parse_time(time)
            record[(method.label, "status")] = normalize_status(status)
        records.append(record)

    return records


def build_table(
    records: list[dict[object, object]],
    methods: list[MethodSpec],
    caption: str,
    label: str,
    tabcolsep: str,
    include_bks: bool = False,
) -> str:
    status_counts = {method.label: {"OPT": 0, "INF": 0, "TO": 0} for method in methods}
    total_times = {method.label: 0.0 for method in methods}
    column_spec = "@{}l "
    if include_bks:
        column_spec += "c "
    column_spec += " ".join(["ccc"] * len(methods)) + "@{}"
    total_columns = 1 + (1 if include_bks else 0) + 3 * len(methods)

    lines = [
        "\\begin{table*}[!htbp]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\scriptsize",
        f"\\setlength{{\\tabcolsep}}{{{tabcolsep}}}",
        "\\renewcommand{\\arraystretch}{1.05}",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{column_spec}}}",
        "\\toprule",
    ]

    header = "\\textbf{Inst.}"
    if include_bks:
        header += " & \\textbf{BKS}"
    for method in methods:
        header += f" & \\multicolumn{{3}}{{c}}{{\\textbf{{{method.label}}}}}"
    lines.append(header + " \\\\")

    cmidrules = []
    for method_index in range(len(methods)):
        start = 2 + (1 if include_bks else 0) + 3 * method_index
        cmidrules.append(f"\\cmidrule(lr){{{start}-{start + 2}}}")
    lines.append(" ".join(cmidrules))

    subheader = ""
    if include_bks:
        subheader += " & "
    for _ in methods:
        subheader += " & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status}"
    lines.append(subheader + " \\\\")
    lines.append("\\midrule")

    for record in records:
        times = [
            record[(method.label, "time")]
            for method in methods
            if record[(method.label, "time")] is not None
        ]
        min_time = min(times) if times else None
        row = format_instance(str(record["instance"]))
        if include_bks:
            pose_status = str(record.get(("POSE+INCSC", "status"), "-"))
            pose_value = str(record.get(("POSE+INCSC", "value"), "-"))
            bks_value = pose_value if pose_status == "OPT" and pose_value != "-" else "-"
            row += f" & {bks_value}"
        for method in methods:
            value = str(record[(method.label, "value")])
            time = record[(method.label, "time")]
            status = str(record[(method.label, "status")])
            if status in status_counts[method.label]:
                status_counts[method.label][status] += 1
            if time is not None:
                total_times[method.label] += float(time)
            bold_time = (
                time is not None
                and min_time is not None
                and abs(float(time) - min_time) <= 1e-9
                and status != "TO"
            )
            row += f" & {value} & {format_time(time, bold_time)} & {status}"
        lines.append(row + " \\\\")

    min_total = min(total_times.values()) if total_times else None
    total_row = "\\midrule\n\\textbf{Total Time}"
    if include_bks:
        total_row += " & -"
    for method in methods:
        total = total_times[method.label]
        total_row += f" & - & {format_time(total, min_total is not None and abs(total - min_total) <= 1e-9)} & -"
    lines.append(total_row + " \\\\")

    for status in ["OPT", "INF", "TO"]:
        row = f"\\#{status}"
        if include_bks:
            row += " & -"
        for method in methods:
            row += f" & - & - & {status_counts[method.label][status]}"
        lines.append(row + " \\\\")

    note_lines = []
    if include_bks:
        note_lines.append(
            f"\\multicolumn{{{total_columns}}}{{l}}{{\\footnotesize \\textbf{{BKS}}: Best Known Solution value reported in~\\cite{{Gomez2023MO}}.}} \\\\"
        )
    note_lines.extend(
        [
            f"\\multicolumn{{{total_columns}}}{{l}}{{\\footnotesize \\textbf{{OPT}}: optimal, \\textbf{{INF}}: infeasible, \\textbf{{TO}}: timeout under the 600-second limit.}} \\\\",
            f"\\multicolumn{{{total_columns}}}{{l}}{{\\footnotesize Time values are reported in seconds. Bold values indicate the fastest non-timeout method for each instance.}}",
        ]
    )
    lines.extend(
        [
            "\\bottomrule",
            *note_lines,
            "\\end{tabular}%",
            "}",
            "\\end{table*}",
        ]
    )
    return "\n".join(lines)


def write_table(
    methods: list[MethodSpec],
    output_name: str,
    caption: str,
    label: str,
    tabcolsep: str,
    include_bks: bool = False,
) -> None:
    records = read_records(COMPARISON_CSV, methods)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_name
    output_path.write_text(
        build_table(records, methods, caption, label, tabcolsep, include_bks=include_bks),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


def main() -> None:
    write_table(
        SAT_CORE_METHODS,
        "appendix_sat_core_preprocess.tex",
        "Detailed comparison of the main SAT configurations and the additional EvalMaxSAT reference with domain preprocessing.",
        "tab:appendix_sat_core_preprocess",
        "3.0pt",
    )
    write_table(
        SOLVER_METHODS,
        "appendix_solver_baselines_preprocess.tex",
        "Detailed comparison of POSE+INCSC and exact solver baselines with domain preprocessing.",
        "tab:appendix_solver_baselines_preprocess",
        "4.0pt",
        include_bks=True,
    )


if __name__ == "__main__":
    main()

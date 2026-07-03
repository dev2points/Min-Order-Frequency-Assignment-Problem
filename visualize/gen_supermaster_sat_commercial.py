from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import re


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
COMPARISON_DIR = PROJECT_DIR / "stats_csv" / "generated_comparison"
OUTPUT_DIR = BASE_DIR / "tables"


@dataclass(frozen=True)
class MethodSpec:
    label: str
    source_label: str


METHODS = [
    MethodSpec("POSE+INC", "POSE+INC"),
    MethodSpec("POSE+INCSC", "POSE+INCSC"),
    MethodSpec("POSE+MaxSAT-RC2", "MaxSAT RC2 POSE"),
    MethodSpec("DSE+INC", "DSE+INC (current)"),
    MethodSpec("DSE+INCSC", "DSE+INCSC"),
    MethodSpec("DSE+MaxSAT-RC2", "MaxSAT RC2 DSE"),
    MethodSpec("CARD-Seq+INC", "Card seqcounter+INC"),
    MethodSpec("CARD-Seq+INCSC", "Card seqcounter+INCSC"),
    MethodSpec("CARD-Seq+MaxSAT-RC2", "MaxSAT RC2 Card seqcounter"),
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
    precision = 4 if 0 < abs(value) < 0.01 else 2
    formatted = f"{value:.{precision}f}".rstrip("0").rstrip(".")
    return f"\\textbf{{{formatted}}}" if bold else formatted


def method_positions(header_row: list[str]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for index, label in enumerate(header_row):
        cleaned = label.strip()
        if cleaned:
            positions[cleaned] = index
    return positions


def read_matrix(csv_path: Path) -> list[dict[str, object]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 2:
        raise ValueError(f"CSV has fewer than two header rows: {csv_path}")

    positions = method_positions(rows[0])
    records: list[dict[str, object]] = []

    for raw_row in rows[2:]:
        if not raw_row or not raw_row[0].strip():
            continue
        instance = raw_row[0].strip()
        record: dict[str, object] = {"instance": instance}

        for method in METHODS:
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


def build_table(records: list[dict[str, object]], caption: str, label: str) -> str:
    status_counts = {method.label: {"OPT": 0, "INF": 0, "TO": 0} for method in METHODS}
    total_times = {method.label: 0.0 for method in METHODS}

    column_spec = "@{}l " + " ".join(["ccc"] * len(METHODS)) + "@{}"
    total_columns = 1 + 3 * len(METHODS)

    lines = [
        "\\begin{table*}[!htbp]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\setlength{\\tabcolsep}{2.2pt}",
        "\\renewcommand{\\arraystretch}{1.05}",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{column_spec}}}",
        "\\toprule",
    ]

    header = "\\textbf{Inst.}"
    for method in METHODS:
        header += f" & \\multicolumn{{3}}{{c}}{{\\textbf{{{method.label}}}}}"
    lines.append(header + " \\\\")

    cmidrules = []
    for method_index in range(len(METHODS)):
        start = 2 + 3 * method_index
        end = start + 2
        cmidrules.append(f"\\cmidrule(lr){{{start}-{end}}}")
    lines.append(" ".join(cmidrules))

    subheader = ""
    for _ in METHODS:
        subheader += " & \\textbf{Sol.} & \\textbf{Time} & \\textbf{Status}"
    lines.append(subheader + " \\\\")
    lines.append("\\midrule")

    for record in records:
        times = [
            record[(method.label, "time")]
            for method in METHODS
            if record[(method.label, "time")] is not None
        ]
        min_time = min(times) if times else None

        row = format_instance(str(record["instance"]))
        for method in METHODS:
            value = str(record[(method.label, "value")])
            time = record[(method.label, "time")]
            status = str(record[(method.label, "status")])

            if status in status_counts[method.label]:
                status_counts[method.label][status] += 1
            if time is not None:
                total_times[method.label] += time

            bold_time = (
                time is not None
                and min_time is not None
                and abs(time - min_time) <= 1e-9
                and status != "TO"
            )
            row += f" & {value} & {format_time(time, bold_time)} & {status}"
        lines.append(row + " \\\\")

    min_total = min(total_times.values()) if total_times else None
    total_row = "\\midrule\n\\textbf{Total Time}"
    for method in METHODS:
        total = total_times[method.label]
        total_row += f" & - & {format_time(total, min_total is not None and abs(total - min_total) <= 1e-9)} & -"
    lines.append(total_row + " \\\\")

    for status in ["OPT", "INF", "TO"]:
        row = f"\\#{status}"
        for method in METHODS:
            row += f" & - & - & {status_counts[method.label][status]}"
        lines.append(row + " \\\\")

    lines.extend(
        [
            "\\bottomrule",
            f"\\multicolumn{{{total_columns}}}{{l}}{{\\footnotesize \\textbf{{OPT}}: optimal, \\textbf{{INF}}: infeasible, \\textbf{{TO}}: timeout under the 600-second limit.}} \\\\",
            f"\\multicolumn{{{total_columns}}}{{l}}{{\\footnotesize Time values are reported in seconds. Bold values indicate the fastest non-timeout method for each instance.}}",
            "\\end{tabular}%",
            "}",
            "\\end{table*}",
        ]
    )
    return "\n".join(lines)


def write_table(input_csv: Path, output_tex: Path, caption: str, label: str) -> None:
    records = read_matrix(input_csv)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(build_table(records, caption, label), encoding="utf-8")
    print(f"Wrote {output_tex}")


def main() -> None:
    write_table(
        COMPARISON_DIR / "preprocess_new.csv",
        OUTPUT_DIR / "supermaster_sat_commercial_preprocess.tex",
        "Comprehensive comparison of SAT configurations and commercial solvers with domain preprocessing.",
        "tab:supermaster_sat_commercial_preprocess",
    )
    write_table(
        COMPARISON_DIR / "nopreprocess_new.csv",
        OUTPUT_DIR / "supermaster_sat_commercial_nopreprocess.tex",
        "Comprehensive comparison of SAT configurations and commercial solvers without domain preprocessing.",
        "tab:supermaster_sat_commercial_nopreprocess",
    )


if __name__ == "__main__":
    main()

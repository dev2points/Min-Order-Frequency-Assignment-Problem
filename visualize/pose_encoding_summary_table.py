"""Generate a certification-status table for SAT encodings."""

from __future__ import annotations

import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"
OUTPUT_DIR = BASE_DIR / "tables"

POSE_METHOD = "POSE+INCSC"
METHODS = [
    ("POSE+INCSC", "POSE+INCSC"),
    ("DSE+INCSC", "DSE+INCSC"),
    ("CARD-Seq+INCSC", "Card seqcounter+INCSC"),
]


def normalize_status(value: str) -> str:
    status = value.strip().upper()
    if status in {"OPT", "OPTIMAL"}:
        return "OPT"
    if status in {"INF", "INFEASIBLE", "UNSAT", "UNSATISFIABLE"}:
        return "INF"
    if status in {"TO", "TIMEOUT", "MO", "OOM", "OUT_OF_MEMORY"}:
        return "TO"
    return "OTHER"


def read_results(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    top_headers = rows[0]
    sub_headers = rows[1]
    groups: list[str] = []
    current_group = ""
    for header in top_headers:
        if header:
            current_group = header
        groups.append(current_group)

    column_map: dict[tuple[str, str], int] = {}
    for index, (group, metric) in enumerate(zip(groups, sub_headers)):
        column_map[(group, metric)] = index

    results: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows[2:]:
        if not row or row[0] == "Total time":
            continue
        instance = row[0]
        results[instance] = {}
        for method_label, csv_group in METHODS:
            results[instance][method_label] = {
                "value": row[column_map[(csv_group, "Value")]].strip(),
                "status": normalize_status(row[column_map[(csv_group, "Status")]]),
            }

    return results


def build_summary(results: dict[str, dict[str, dict[str, str]]]) -> list[dict[str, str]]:
    summary_rows: list[dict[str, str]] = []
    for method, _ in METHODS:
        counts = {"OPT": 0, "INF": 0, "TO": 0, "OTHER": 0}
        for instance, by_method in results.items():
            item = by_method[method]
            counts[item["status"]] = counts.get(item["status"], 0) + 1

        certified = counts["OPT"] + counts["INF"]
        total = certified + counts["TO"] + counts["OTHER"]
        summary_rows.append(
            {
                "Method": method,
                "OPT": str(counts["OPT"]),
                "INF": str(counts["INF"]),
                "TO": str(counts["TO"]),
                "Certified (OPT+INF)": f"{certified}/{total}",
            }
        )

    return summary_rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_latex(rows: list[dict[str, str]], path: Path) -> None:
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{Number of benchmark instances certified by each SAT encoding after preprocessing.}",
        r"\label{tab:pose_encoding_certification}",
        r"\small",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Method & OPT & INF & TO & Certified \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['Method']} & {row['OPT']} & {row['INF']} & {row['TO']} & "
            f"{row['Certified (OPT+INF)']} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[header] for header in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results = read_results(CSV_PATH)
    rows = build_summary(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows, OUTPUT_DIR / "pose_encoding_certification.csv")
    write_latex(rows, OUTPUT_DIR / "pose_encoding_certification.tex")
    write_markdown(rows, OUTPUT_DIR / "pose_encoding_certification.md")

    print(f"Wrote {OUTPUT_DIR / 'pose_encoding_certification.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'pose_encoding_certification.tex'}")
    print(f"Wrote {OUTPUT_DIR / 'pose_encoding_certification.md'}")


if __name__ == "__main__":
    main()

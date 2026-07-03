import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "stats_csv" / "generated_comparison" / "hard_encoding_stats.csv"
DEFAULT_OUTDIR = ROOT / "visualize" / "tables"


def read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def encoding_name(row):
    if row["encoding"] != "CARD":
        return row["encoding"]
    exact = row.get("exact_encoding", "")
    distance = row.get("distance_encoding", "")
    return f"CARD {exact}:{distance}"


def to_int(value):
    if value in (None, ""):
        return 0
    return int(float(value))


def summarize(rows):
    groups = {}
    for row in rows:
        name = encoding_name(row)
        group = groups.setdefault(
            name,
            {
                "encoding": name,
                "ok": 0,
                "preprocess_infeasible": 0,
                "other_status": 0,
                "sum_vars": 0,
                "sum_clauses": 0,
                "max_vars": 0,
                "max_clauses": 0,
            },
        )
        status = row["status"]
        if status == "ok":
            group["ok"] += 1
            vars_ = to_int(row["num_vars"])
            clauses = to_int(row["num_clauses"])
            group["sum_vars"] += vars_
            group["sum_clauses"] += clauses
            group["max_vars"] = max(group["max_vars"], vars_)
            group["max_clauses"] = max(group["max_clauses"], clauses)
        elif status == "preprocess_infeasible":
            group["preprocess_infeasible"] += 1
        else:
            group["other_status"] += 1

    summary = []
    for group in groups.values():
        ok = group["ok"]
        summary.append(
            {
                "encoding": group["encoding"],
                "ok": ok,
                "preprocess_infeasible": group["preprocess_infeasible"],
                "other_status": group["other_status"],
                "avg_vars": round(group["sum_vars"] / ok, 2) if ok else 0,
                "avg_clauses": round(group["sum_clauses"] / ok, 2) if ok else 0,
                "max_vars": group["max_vars"],
                "max_clauses": group["max_clauses"],
                "sum_vars": group["sum_vars"],
                "sum_clauses": group["sum_clauses"],
            }
        )
    return sorted(summary, key=lambda row: row["encoding"])


def pivot_instances(rows):
    table = {}
    for row in rows:
        dataset = row["dataset"]
        enc = encoding_name(row)
        item = table.setdefault(dataset, {"dataset": dataset})
        if row["status"] == "ok":
            item[f"{enc}_vars"] = to_int(row["num_vars"])
            item[f"{enc}_clauses"] = to_int(row["num_clauses"])
        else:
            item[f"{enc}_vars"] = row["status"]
            item[f"{enc}_clauses"] = row["status"]

    encodings = sorted({encoding_name(row) for row in rows})
    fieldnames = ["dataset"]
    for enc in encodings:
        fieldnames.extend([f"{enc}_vars", f"{enc}_clauses"])
    return [table[key] for key in sorted(table)], fieldnames


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows, fieldnames):
    def fmt(value):
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)

    lines = []
    lines.append("| " + " | ".join(fieldnames) + " |")
    lines.append("| " + " | ".join(["---"] * len(fieldnames)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(field, "")) for field in fieldnames) + " |")
    return "\n".join(lines) + "\n"


def write_markdown(path, title, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# {title}\n\n")
        fh.write(markdown_table(rows, fieldnames))


def parse_args():
    parser = argparse.ArgumentParser(description="Create readable tables from hard-encoding CNF statistics.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    outdir = Path(args.outdir)
    rows = read_rows(input_path)

    summary = summarize(rows)
    summary_fields = [
        "encoding",
        "ok",
        "preprocess_infeasible",
        "other_status",
        "avg_vars",
        "avg_clauses",
        "max_vars",
        "max_clauses",
        "sum_vars",
        "sum_clauses",
    ]
    write_csv(outdir / "hard_encoding_summary.csv", summary, summary_fields)
    write_markdown(outdir / "hard_encoding_summary.md", "Hard Encoding Summary", summary, summary_fields)

    pivot_rows, pivot_fields = pivot_instances(rows)
    write_csv(outdir / "hard_encoding_by_instance.csv", pivot_rows, pivot_fields)
    write_markdown(outdir / "hard_encoding_by_instance.md", "Hard Encoding By Instance", pivot_rows, pivot_fields)

    print(markdown_table(summary, summary_fields))
    print(f"Wrote tables to {outdir}")


if __name__ == "__main__":
    main()

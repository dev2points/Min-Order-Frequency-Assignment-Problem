import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "visualize" / "tables" / "hard_encoding_by_instance.csv"
DEFAULT_OUTDIR = ROOT / "visualize" / "tables"


ENC_CARD = "CARD 1:1"
ENC_DSE = "DSE"
ENC_POSE = "POSE"
STATUS_INFEASIBLE = "preprocess_infeasible"


def read_rows(path):
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_int(value):
    if value in (None, "", STATUS_INFEASIBLE):
        return None
    return int(float(value))


def fmt_num(value):
    if value is None:
        return "--"
    return f"{value:,}"


def fmt_pct(value, base):
    if value is None or base in (None, 0):
        return "--"
    return f"{100.0 * value / base:.0f}"


def normalize_dataset_name(name):
    mapping = {
        "scen01": "C01",
        "scen02": "C02",
        "scen03": "C03",
        "scen04": "C04",
        "scen05": "C05",
        "scen06": "C06",
        "scen07": "C07",
        "scen08": "C08",
        "scen09": "C09",
        "scen10": "C10",
        "scen11": "C11",
        "graph01": "G01",
        "graph02": "G02",
        "graph03": "G03",
        "graph04": "G04",
        "graph05": "G05",
        "graph06": "G06",
        "graph07": "G07",
        "graph08": "G08",
        "graph09": "G09",
        "graph10": "G10",
        "graph11": "G11",
        "graph12": "G12",
        "graph13": "G13",
        "graph14": "G14",
        "TUD200.1": "T2.1",
        "TUD200.2": "T2.2",
        "TUD200.3": "T2.3",
        "TUD200.4": "T2.4",
        "TUD200.5": "T2.5",
        "TUD916.1": "T9.1",
        "TUD916.2": "T9.2",
        "TUD916.3": "T9.3",
        "TUD916.4": "T9.4",
        "TUD916.5": "T9.5",
    }
    return mapping.get(name, name)


def instance_sort_key(instance):
    if instance.startswith("C"):
        return (0, int(instance[1:]))
    if instance.startswith("G"):
        return (1, int(instance[1:]))
    if instance.startswith("T2."):
        return (2, int(instance.split(".")[1]))
    if instance.startswith("T9."):
        return (3, int(instance.split(".")[1]))
    return (9, instance)


def build_rows(rows):
    out = []
    for row in rows:
        instance = normalize_dataset_name(row["dataset"])
        dse_vars = parse_int(row.get(f"{ENC_DSE}_vars"))
        pose_vars = parse_int(row.get(f"{ENC_POSE}_vars"))
        card_vars = parse_int(row.get(f"{ENC_CARD}_vars"))
        dse_clauses = parse_int(row.get(f"{ENC_DSE}_clauses"))
        pose_clauses = parse_int(row.get(f"{ENC_POSE}_clauses"))
        card_clauses = parse_int(row.get(f"{ENC_CARD}_clauses"))
        if all(value is None for value in (dse_vars, pose_vars, card_vars, dse_clauses, pose_clauses, card_clauses)):
            continue
        out.append(
            {
                "Instance": instance,
                "DSE Vars": fmt_num(dse_vars),
                "POSE Vars": fmt_num(pose_vars),
                "POSE/DSE Vars (%)": fmt_pct(pose_vars, dse_vars),
                "CARD Vars": fmt_num(card_vars),
                "CARD/DSE Vars (%)": fmt_pct(card_vars, dse_vars),
                "DSE Clauses": fmt_num(dse_clauses),
                "POSE Clauses": fmt_num(pose_clauses),
                "POSE/DSE Clauses (%)": fmt_pct(pose_clauses, dse_clauses),
                "CARD Clauses": fmt_num(card_clauses),
                "CARD/DSE Clauses (%)": fmt_pct(card_clauses, dse_clauses),
            }
        )
    return sorted(out, key=lambda item: instance_sort_key(item["Instance"]))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, rows, fields):
    lines = []
    lines.append("| " + " | ".join(fields) + " |")
    lines.append("| " + " | ".join(["---"] * len(fields)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row[field] for field in fields) + " |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def latex_escape(value):
    return value.replace("%", r"\%")


def write_latex(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table}[!htbp]",
        r"\centering",
        r"\caption{Number of variables and clauses in the SAT encodings of the assignment, exact-distance, and interference constraints for instances not eliminated by preprocessing.}",
        r"\label{tab:hard_encoding_full}",
        r"\tiny",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\renewcommand{\arraystretch}{1.0}",
        r"\begin{tabular}{@{}lrrrrrrrrrr@{}}",
        r"\toprule",
        r"\multirow{2}{*}{\textbf{Inst.}} & \multicolumn{5}{c}{\textbf{Variables}} & \multicolumn{5}{c}{\textbf{Clauses}} \\",
        r"\cmidrule(lr){2-6}\cmidrule(lr){7-11}",
        r"& \textbf{DSE} & \textbf{POSE} & \textbf{P/D} & \textbf{CARD} & \textbf{C/D} & \textbf{DSE} & \textbf{POSE} & \textbf{P/D} & \textbf{CARD} & \textbf{C/D} \\",
        r"\midrule",
    ]
    for row in rows:
        values = [
            row["Instance"],
            row["DSE Vars"],
            row["POSE Vars"],
            row["POSE/DSE Vars (%)"],
            row["CARD Vars"],
            row["CARD/DSE Vars (%)"],
            row["DSE Clauses"],
            row["POSE Clauses"],
            row["POSE/DSE Clauses (%)"],
            row["CARD Clauses"],
            row["CARD/DSE Clauses (%)"],
        ]
        lines.append(" & ".join(latex_escape(value) for value in values) + r" \\")
    lines.extend(
        [
            r"\midrule",
            r"\multicolumn{11}{@{}l}{\footnotesize P/D and C/D are percentages relative to DSE.} \\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate full hard-encoding comparison tables.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    return parser.parse_args()


def main():
    args = parse_args()
    rows = build_rows(read_rows(Path(args.input)))
    fields = list(rows[0].keys()) if rows else []
    outdir = Path(args.outdir)
    write_csv(outdir / "hard_encoding_full_table.csv", rows, fields)
    write_markdown(outdir / "hard_encoding_full_table.md", rows, fields)
    write_latex(outdir / "hard_encoding_full_table.tex", rows)
    print(f"Wrote full hard-encoding tables to {outdir}")


if __name__ == "__main__":
    main()

"""Plot the effect of domain preprocessing on solving time."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from plot_style import METHOD_COLORS, STATUS_MARKERS


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR.parent
DEFAULT_STATS_DIR = SOURCE_DIR / "stats_csv" / "generated_comparison"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "figures"

TIMEOUT_SECONDS = 600.0
MIN_PLOT_TIME = 0.001
EXPECTED_INSTANCES = 35

METHOD_HEADER_MAP = {
    "POSE+INCSC": "POSE+INCSC",
    "POSE+INC": "POSE+INC",
    "DSE+INCSC": "DSE+INCSC",
    "Card seqcounter+INCSC": "CARD-Seq+INCSC",
    "MaxSAT RC2 POSE": "POSE+MaxSAT-RC2",
    "Gurobi": "Gurobi",
    "CPLEX/CP": "CPLEX-CP",
    "CPLEX/MIP": "CPLEX-MIP",
    "CP-SAT": "CP-SAT",
}

SAT_METHODS = [
    "POSE+INCSC",
    "POSE+INC",
    "DSE+INCSC",
    "CARD-Seq+INCSC",
    "POSE+MaxSAT-RC2",
]

BASELINE_METHODS = [
    "Gurobi",
    "CPLEX-CP",
    "CPLEX-MIP",
    "CP-SAT",
]

STATUS_ALIASES = {
    "OPT": "OPT",
    "OPTIMAL": "OPT",
    "INF": "INF",
    "INFEASIBLE": "INF",
    "UNSAT": "INF",
    "UNSATISFIABLE": "INF",
    "TO": "TO",
    "TIMEOUT": "TO",
    "MO": "TO",
    "OUT_OF_MEMORY": "TO",
    "OOM": "TO",
}


def _canon(value: object) -> str:
    return " ".join(str(value).strip().lower().split())


CANON_HEADER_MAP = {_canon(header): method for header, method in METHOD_HEADER_MAP.items()}


def _normalize_status(value: object) -> str:
    raw = str(value).strip().upper() if not pd.isna(value) else ""
    return STATUS_ALIASES.get(raw, "UNKNOWN")


def _normalize_time(value: object, status: str) -> float | None:
    if status == "TO":
        return TIMEOUT_SECONDS
    if pd.isna(value):
        return None
    raw = str(value).strip()
    if raw in {"", "-"}:
        return None
    try:
        return max(float(raw), MIN_PLOT_TIME)
    except ValueError:
        return None


def _flatten_comparison_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1])
    flattened = pd.DataFrame({"Instance": raw.iloc[:, 0].astype(str).str.strip()})

    current_group = ""
    groups: list[str] = []
    for top_header, _ in raw.columns:
        header = str(top_header).strip()
        if header and not header.startswith("Unnamed:"):
            current_group = header
        groups.append(current_group)

    metric_names = {
        "value": "Value",
        "time": "Time",
        "status": "Status",
    }
    for column_index in range(1, raw.shape[1]):
        method = CANON_HEADER_MAP.get(_canon(groups[column_index]))
        metric = metric_names.get(str(raw.columns[column_index][1]).strip().lower())
        if method is None or metric is None:
            continue
        flattened[f"{method}__{metric}"] = raw.iloc[:, column_index]

    flattened = flattened.loc[:, ~flattened.columns.duplicated()]
    is_summary_row = flattened["Instance"].str.casefold().eq("total time")
    return flattened.loc[~is_summary_row].copy()


def _combined_status(status_pre: str, status_no_pre: str) -> str:
    statuses = {status_pre, status_no_pre}
    if "INF" in statuses:
        return "INF"
    if "TO" in statuses:
        return "TO"
    if statuses == {"OPT"}:
        return "OPT"
    return "UNKNOWN"


def build_comparison(preprocess_csv: Path, nopreprocess_csv: Path) -> pd.DataFrame:
    pre = _flatten_comparison_csv(preprocess_csv).set_index("Instance")
    no_pre = _flatten_comparison_csv(nopreprocess_csv).set_index("Instance")
    instances = sorted(set(pre.index) & set(no_pre.index))

    rows: list[dict[str, object]] = []
    for method in SAT_METHODS + BASELINE_METHODS:
        for instance in instances:
            status_pre = _normalize_status(pre.at[instance, f"{method}__Status"])
            status_no_pre = _normalize_status(no_pre.at[instance, f"{method}__Status"])
            time_pre = _normalize_time(pre.at[instance, f"{method}__Time"], status_pre)
            time_no_pre = _normalize_time(no_pre.at[instance, f"{method}__Time"], status_no_pre)
            status = _combined_status(status_pre, status_no_pre)

            if time_pre is None or time_no_pre is None or status == "UNKNOWN":
                continue
            rows.append(
                {
                    "Instance": instance,
                    "Method": method,
                    "Time_Pre": time_pre,
                    "Time_No_Pre": time_no_pre,
                    "Status": status,
                }
            )

    comparison = pd.DataFrame(rows)
    _validate_comparison(comparison)
    return comparison


def _validate_comparison(comparison: pd.DataFrame) -> None:
    problems = []
    for method in SAT_METHODS + BASELINE_METHODS:
        method_rows = comparison[comparison["Method"] == method]
        count = method_rows["Instance"].nunique()
        if count != EXPECTED_INSTANCES:
            problems.append(f"{method}: {count}/{EXPECTED_INSTANCES} paired instances")
    if problems:
        raise ValueError("Incomplete preprocessing comparison:\n" + "\n".join(problems))


def _plot_methods(ax: plt.Axes, comparison: pd.DataFrame, methods: list[str]) -> None:
    for method in methods:
        method_rows = comparison[comparison["Method"] == method]
        for status in ("OPT", "INF", "TO"):
            status_rows = method_rows[method_rows["Status"] == status]
            if status_rows.empty:
                continue
            ax.scatter(
                status_rows["Time_No_Pre"],
                status_rows["Time_Pre"],
                color=METHOD_COLORS[method],
                marker=STATUS_MARKERS[status],
                s=28,
                edgecolors="black",
                linewidths=0.4,
                alpha=0.82,
                zorder=3,
            )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Time without preprocessing (s)", fontweight="bold")
    ax.set_ylabel("Time with preprocessing (s)", fontweight="bold")
    ax.grid(True, which="both", linestyle="--", linewidth=0.45, alpha=0.3)

    method_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markersize=5.5,
            markerfacecolor=METHOD_COLORS[method],
            markeredgecolor="black",
            markeredgewidth=0.4,
            label=method,
        )
        for method in methods
    ]
    method_legend = ax.legend(
        handles=method_handles,
        loc="upper left",
        ncol=2,
        fontsize=5.8,
        columnspacing=0.8,
        handletextpad=0.35,
        borderpad=0.35,
        frameon=True,
        edgecolor="0.4",
    )
    ax.add_artist(method_legend)


def plot_runtime_scatter(comparison: pd.DataFrame, output_dir: Path) -> None:
    all_times = pd.concat([comparison["Time_Pre"], comparison["Time_No_Pre"]])
    lower = max(MIN_PLOT_TIME, all_times.min() * 0.7)
    upper = max(TIMEOUT_SECONDS, all_times.max()) * 1.3

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 8,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
        }
    )
    fig, ax = plt.subplots(figsize=(3.5, 3.5))

    _plot_methods(ax, comparison, SAT_METHODS + BASELINE_METHODS)
    ax.plot([lower, upper], [lower, upper], color="black", linestyle="--", linewidth=0.9, zorder=2)
    ax.set_xlim(lower, upper)
    ax.set_ylim(lower, upper)
    ax.set_aspect("equal", adjustable="box")

    status_handles = [
        Line2D(
            [0],
            [0],
            marker=STATUS_MARKERS[status],
            linestyle="None",
            markersize=5.5,
            markerfacecolor="white",
            markeredgecolor="black",
            label=label,
        )
        for status, label in (("OPT", "OPT"), ("INF", "INF"), ("TO", "TO in either run"))
    ]
    status_handles.append(Line2D([0], [0], color="black", linestyle="--", label=r"$y=x$"))
    ax.legend(
        handles=status_handles,
        loc="lower right",
        ncol=2,
        fontsize=5.8,
        columnspacing=0.8,
        handletextpad=0.35,
        borderpad=0.35,
        frameon=True,
        edgecolor="0.4",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_dir / "iv_b_runtime_scatter_by_solver.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "iv_b_runtime_scatter_by_solver.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "iv_b_runtime_scatter_by_solver.eps", format="eps", dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocess-csv",
        type=Path,
        default=DEFAULT_STATS_DIR / "preprocess_new.csv",
    )
    parser.add_argument(
        "--nopreprocess-csv",
        type=Path,
        default=DEFAULT_STATS_DIR / "nopreprocess_new.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparison = build_comparison(args.preprocess_csv.resolve(), args.nopreprocess_csv.resolve())
    plot_runtime_scatter(comparison, args.output_dir.resolve())
    print(
        f"Plotted {len(comparison)} paired rows for "
        f"{comparison['Method'].nunique()} methods in {args.output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()

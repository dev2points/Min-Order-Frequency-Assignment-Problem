"""Scatter plots comparing POSE against DSE and CARD-Seq under INCSC."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR.parent
DEFAULT_STATS_DIR = SOURCE_DIR / "stats_csv" / "generated_comparison"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "figures"

TIMEOUT_SECONDS = 600.0
MIN_PLOT_TIME = 0.001

METHOD_HEADER_MAP = {
    "POSE+INCSC": "POSE+INCSC",
    "DSE+INCSC": "DSE+INCSC",
    "Card seqcounter+INCSC": "CARD-Seq+INCSC",
}

BASELINE_METHODS = ["DSE+INCSC", "CARD-Seq+INCSC"]
BASELINE_COLORS = {
    "DSE+INCSC": "forestgreen",
    "CARD-Seq+INCSC": "darkorange",
}

TIMEOUT_STATUS = {"TO", "TIMEOUT", "TL", "MO", "OOM"}
INF_STATUS = {"INF", "INFEASIBLE", "UNSAT"}
OPT_STATUS = {"OPT", "OPTIMAL"}

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


def build_pair_data(preprocess_csv: Path) -> pd.DataFrame:
    flat = _flatten_comparison_csv(preprocess_csv)
    rows: list[dict[str, object]] = []

    for _, row in flat.iterrows():
        pose_status = _normalize_status(row["POSE+INCSC__Status"])
        pose_time = _normalize_time(row["POSE+INCSC__Time"], pose_status)
        if pose_time is None or pose_status == "UNKNOWN":
            continue

        for baseline in BASELINE_METHODS:
            baseline_status = _normalize_status(row[f"{baseline}__Status"])
            baseline_time = _normalize_time(row[f"{baseline}__Time"], baseline_status)
            if baseline_time is None or baseline_status == "UNKNOWN":
                continue
            rows.append(
                {
                    "Instance": row["Instance"],
                    "Baseline": baseline,
                    "POSE_Time": pose_time,
                    "Baseline_Time": baseline_time,
                    "POSE_Status": pose_status,
                    "Baseline_Status": baseline_status,
                    "Group": _classify_group(pose_status, baseline_status),
                }
            )

    return pd.DataFrame(rows)


def _classify_group(pose_status: str, baseline_status: str) -> str:
    if pose_status in INF_STATUS and baseline_status in INF_STATUS:
        return "INF"
    if pose_status in OPT_STATUS and baseline_status in OPT_STATUS:
        return "OPT_BOTH"
    if pose_status in OPT_STATUS and baseline_status in TIMEOUT_STATUS:
        return "OPT_BASELINE_TO"
    if pose_status in TIMEOUT_STATUS or baseline_status in TIMEOUT_STATUS:
        return "TO"
    return "OTHER"


def plot_pair_scatter(pair_data: pd.DataFrame, output_dir: Path) -> None:
    all_times = pd.concat([pair_data["POSE_Time"], pair_data["Baseline_Time"]])
    lower = max(MIN_PLOT_TIME, all_times.min() * 0.7)
    upper = max(TIMEOUT_SECONDS, all_times.max()) * 1.3

    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.size"] = 10
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharex=True, sharey=True)

    group_styles = {
        "INF": dict(marker="^", s=45, alpha=0.8),
        "OPT_BOTH": dict(marker="o", s=45, alpha=0.8),
        "OPT_BASELINE_TO": dict(marker="*", s=120, alpha=0.9),
        "TO": dict(marker="X", s=55, alpha=0.75),
    }
    group_labels = {
        "INF": "INF Instances",
        "OPT_BOTH": "OPT (Both Solved)",
        "OPT_BASELINE_TO": "OPT (Baseline Timeout)",
        "TO": "TO in either method",
    }

    for ax, baseline in zip(axes, BASELINE_METHODS):
        subset = pair_data[pair_data["Baseline"] == baseline]
        for group, style in group_styles.items():
            status_rows = subset[subset["Group"] == group]
            if status_rows.empty:
                continue
            ax.scatter(
                status_rows["Baseline_Time"],
                status_rows["POSE_Time"],
                label=f"{group_labels[group]} ({len(status_rows)})",
                color=BASELINE_COLORS[baseline],
                edgecolors="black",
                linewidths=0.5,
                zorder=3,
                **style,
            )

        ax.plot([lower, upper], [lower, upper], "k--", alpha=0.6, label=r"Equal Time ($y=x$)", zorder=2)
        ax.axvline(x=TIMEOUT_SECONDS, color="gray", linestyle=":", alpha=0.8)
        ax.axhline(y=TIMEOUT_SECONDS, color="gray", linestyle=":", alpha=0.8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim((0.005, 1200))
        ax.set_ylim((0.005, 1200))
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.set_xlabel(f"{baseline} time (s)", fontweight="bold")
        ax.set_title(f"POSE+INCSC vs {baseline}", fontweight="bold", fontsize=10)
        ax.text(
            650,
            0.01,
            "Timeout limit (600s)",
            rotation=90,
            va="bottom",
            ha="left",
            color="gray",
            fontsize=8,
        )
        legend_handles = [
            Line2D(
                [0],
                [0],
                marker=group_styles[group]["marker"],
                linestyle="None",
                markersize=7 if group != "OPT_BASELINE_TO" else 10,
                markerfacecolor=BASELINE_COLORS[baseline],
                markeredgecolor="black",
                markeredgewidth=0.5,
                label=group_labels[group],
            )
            for group in ("INF", "OPT_BOTH", "OPT_BASELINE_TO")
        ]
        legend_handles.append(Line2D([0], [0], color="black", linestyle="--", alpha=0.6, label=r"Equal Time ($y=x$)"))
        ax.legend(
            handles=legend_handles,
            loc="upper left",
            bbox_to_anchor=(0.02, 0.96),
            fontsize=8.0,
            frameon=True,
            edgecolor="black",
        )

    axes[0].set_ylabel("POSE+INCSC time (s)", fontweight="bold")

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_dir / "pose_encoding_pair_scatter.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "pose_encoding_pair_scatter.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "pose_encoding_pair_scatter.eps", format="eps", dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preprocess-csv",
        type=Path,
        default=DEFAULT_STATS_DIR / "preprocess_new.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pair_data = build_pair_data(args.preprocess_csv.resolve())
    plot_pair_scatter(pair_data, args.output_dir.resolve())
    print(
        f"Plotted {len(pair_data)} paired rows for {pair_data['Baseline'].nunique()} baselines "
        f"in {args.output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()

"""Two-panel lollipop ratio plot for POSE objective-function strategies."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 10

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"

METHOD_MAP = {
    "POSE+INCSC": "POSE_INCSC",
    "POSE+INC": "POSE_INC",
    "MaxSAT RC2 POSE": "POSE_MAXSAT_RC2",
}

COLORS = {
    "POSE_INCSC": "steelblue",
    "POSE_INC": "slateblue",
    "POSE_MAXSAT_RC2": "crimson",
    "EQUAL": "dimgray",
}

INSTANCE_NAME_MAP = {
    "scen01": "C01", "scen02": "C02", "scen03": "C03", "scen04": "C04", "scen05": "C05",
    "scen06": "C06", "scen07": "C07", "scen08": "C08", "scen09": "C09", "scen10": "C10", "scen11": "C11",
    "graph01": "G01", "graph02": "G02", "graph03": "G03", "graph04": "G04", "graph05": "G05",
    "graph06": "G06", "graph07": "G07", "graph08": "G08", "graph09": "G09", "graph10": "G10",
    "graph11": "G11", "graph12": "G12", "graph13": "G13", "graph14": "G14",
    "TUD200.1": "T2.1", "TUD200.2": "T2.2", "TUD200.3": "T2.3", "TUD200.4": "T2.4", "TUD200.5": "T2.5",
    "TUD916.1": "T9.1", "TUD916.2": "T9.2", "TUD916.3": "T9.3", "TUD916.4": "T9.4", "TUD916.5": "T9.5",
}


def to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def flatten_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1])
    out = pd.DataFrame()
    out["Bench"] = raw.iloc[:, 0].astype(str).str.strip()

    current_group = ""
    groups: list[str] = []
    for top_header, _ in raw.columns:
        header = str(top_header).strip()
        if header and not header.startswith("Unnamed:"):
            current_group = header
        groups.append(current_group)

    for col_idx in range(1, raw.shape[1]):
        method = METHOD_MAP.get(groups[col_idx])
        metric = str(raw.columns[col_idx][1]).strip()
        metric_name = {"Value": "Value", "Time": "Total time", "Status": "Status"}.get(metric)
        if method is None or metric_name is None:
            continue
        out[f"{method}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def build_ratio_data(df: pd.DataFrame, numerator: str) -> tuple[list[str], list[float], list[str]]:
    instances: list[str] = []
    ratios: list[float] = []
    labels: list[str] = []

    for _, row in df.iterrows():
        bench = row.get("Bench")
        bench_display = INSTANCE_NAME_MAP.get(str(bench), str(bench))

        value_base = str(row.get("POSE_INCSC__Value", "")).strip()
        value_num = str(row.get(f"{numerator}__Value", "")).strip()
        status_base = str(row.get("POSE_INCSC__Status", "")).strip().upper()
        status_num = str(row.get(f"{numerator}__Status", "")).strip().upper()
        if status_base != "OPT" or status_num != "OPT":
            continue
        if value_base in {"", "-"} or value_base != value_num:
            continue

        time_base = to_num(row.get("POSE_INCSC__Total time"))
        time_num = to_num(row.get(f"{numerator}__Total time"))
        if time_base is None or time_num is None or time_base == 0:
            continue

        ratio = time_num / time_base
        instances.append(bench_display)
        ratios.append(ratio)

        if ratio > 1.0001:
            labels.append("POSE_INCSC")
        elif ratio < 0.9999:
            labels.append(numerator)
        else:
            labels.append("EQUAL")

    return instances, ratios, labels


def draw_panel(
    ax: plt.Axes,
    instances: list[str],
    ratios: list[float],
    labels: list[str],
    numerator: str,
    numerator_label: str,
    ylabel: str,
) -> None:
    x = np.arange(len(instances))
    ratios_arr = np.array(ratios)
    labels_arr = np.array(labels)

    ax.axhline(1, color="black", linewidth=0.9, linestyle="--", zorder=1)

    incsc_idx = np.where(labels_arr == "POSE_INCSC")[0]
    num_idx = np.where(labels_arr == numerator)[0]
    equal_idx = np.where(labels_arr == "EQUAL")[0]

    if incsc_idx.size:
        ax.vlines(x[incsc_idx], ymin=1, ymax=ratios_arr[incsc_idx], color=COLORS["POSE_INCSC"], alpha=0.98, linewidth=1.7, zorder=2)
        ax.scatter(x[incsc_idx], ratios_arr[incsc_idx], marker="o", facecolor=COLORS["POSE_INCSC"], edgecolor="black", s=25, linewidth=0.6, zorder=3)
    if num_idx.size:
        ax.vlines(x[num_idx], ymin=1, ymax=ratios_arr[num_idx], color=COLORS[numerator], alpha=0.98, linewidth=1.7, zorder=2)
        ax.scatter(x[num_idx], ratios_arr[num_idx], marker="^", facecolor=COLORS[numerator], edgecolor="black", s=27, linewidth=0.6, zorder=3)
    if equal_idx.size:
        ax.scatter(x[equal_idx], ratios_arr[equal_idx], marker="s", facecolor=COLORS["EQUAL"], edgecolor="black", s=22, linewidth=0.6, zorder=3)

    ax.set_ylabel(ylabel, fontweight="bold", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.tick_params(axis="y", labelsize=9)

    legend_handles = [
        Line2D([0], [0], color=COLORS["POSE_INCSC"], marker="o", markerfacecolor=COLORS["POSE_INCSC"], markeredgecolor="black", markeredgewidth=0.6, linestyle="-", label="POSE+INCSC faster"),
        Line2D([0], [0], color=COLORS[numerator], marker="^", markerfacecolor=COLORS[numerator], markeredgecolor="black", markeredgewidth=0.6, linestyle="-", label=f"{numerator_label} faster"),
    ]
    if equal_idx.size:
        legend_handles.append(Line2D([0], [0], color=COLORS["EQUAL"], marker="s", markerfacecolor=COLORS["EQUAL"], markeredgecolor="black", markeredgewidth=0.6, linestyle="None", label="Equal"))

    ax.legend(handles=legend_handles, loc="upper right", frameon=True, fontsize=7.5, borderpad=0.25, handlelength=1.3, labelspacing=0.2)


def safe_save(out_path: Path, fmt: str, **kwargs: object) -> None:
    try:
        plt.savefig(out_path, format=fmt, **kwargs)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
        plt.savefig(fallback, format=fmt, **kwargs)
        print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")


def main() -> None:
    df = flatten_csv(CSV_PATH)
    inc_instances, inc_ratios, inc_labels = build_ratio_data(df, "POSE_INC")
    maxsat_instances, maxsat_ratios, maxsat_labels = build_ratio_data(df, "POSE_MAXSAT_RC2")

    if inc_instances != maxsat_instances:
        print("[WARNING] Panel instance lists differ; x-axis labels use the first panel.")

    fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.2), sharex=True)
    draw_panel(axes[0], inc_instances, inc_ratios, inc_labels, "POSE_INC", "POSE+INC", "Time POSE+INC / Time POSE+INCSC")
    draw_panel(axes[1], maxsat_instances, maxsat_ratios, maxsat_labels, "POSE_MAXSAT_RC2", "POSE+MaxSAT-RC2", "Time POSE+MaxSAT-RC2 / Time POSE+INCSC")

    tick_step = 1
    tick_idx = np.arange(0, len(inc_instances), tick_step)
    axes[1].set_xticks(tick_idx)
    axes[1].set_xticklabels([inc_instances[i] for i in tick_idx], rotation=75, ha="right")
    axes[1].tick_params(axis="x", pad=2, labelsize=8)
    axes[1].set_xlabel("Instances (Same Solution Value)", fontweight="bold")

    plt.tight_layout(pad=0.55)
    fig.subplots_adjust(bottom=0.21, hspace=0.18)

    fig_dir = BASE_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    safe_save(fig_dir / "objective_speedup_lollipop_combined.png", "png", dpi=600, bbox_inches="tight")
    safe_save(fig_dir / "objective_speedup_lollipop_combined.pdf", "pdf", bbox_inches="tight", pad_inches=0.01)
    safe_save(fig_dir / "objective_speedup_lollipop_combined.eps", "eps", bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    print(f"Plotted {len(inc_instances)} INC rows and {len(maxsat_instances)} MaxSAT rows")


if __name__ == "__main__":
    main()

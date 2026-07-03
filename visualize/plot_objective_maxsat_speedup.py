"""Lollipop ratio plot comparing POSE+INCSC and POSE+MaxSAT-RC2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 12

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"

METHOD_MAP = {
    "POSE+INCSC": "POSE_INCSC",
    "MaxSAT RC2 POSE": "POSE_MAXSAT_RC2",
}

METHOD_COLORS = {
    "POSE_INCSC": "steelblue",
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


def _to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _flatten_raw_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1])
    out = pd.DataFrame()
    out["Bench"] = raw.iloc[:, 0].astype(str).str.strip()

    top_headers = [str(raw.columns[i][0]).strip() for i in range(raw.shape[1])]
    normalized_top = []
    current_group = ""
    for header in top_headers:
        if header == "" or header.startswith("Unnamed:"):
            normalized_top.append(current_group)
        else:
            current_group = header
            normalized_top.append(header)

    for col_idx in range(1, raw.shape[1]):
        group = normalized_top[col_idx]
        metric = str(raw.columns[col_idx][1]).strip()
        method = METHOD_MAP.get(group)
        if method is None:
            continue

        metric_name = {"Value": "Value", "Time": "Total time", "Status": "Status"}.get(metric)
        if metric_name is None:
            continue
        out[f"{method}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def build_ratio_data(df: pd.DataFrame) -> tuple[list[str], list[float], list[str]]:
    instances: list[str] = []
    ratios: list[float] = []
    labels: list[str] = []

    for _, row in df.iterrows():
        bench = row.get("Bench")
        bench_display = INSTANCE_NAME_MAP.get(str(bench), str(bench))

        value_incsc = str(row.get("POSE_INCSC__Value", "")).strip()
        value_maxsat = str(row.get("POSE_MAXSAT_RC2__Value", "")).strip()
        if value_incsc != value_maxsat:
            continue

        time_incsc = _to_num(row.get("POSE_INCSC__Total time"))
        time_maxsat = _to_num(row.get("POSE_MAXSAT_RC2__Total time"))
        if time_incsc is None or time_maxsat is None or time_incsc == 0:
            continue

        ratio = time_maxsat / time_incsc
        instances.append(bench_display)
        ratios.append(ratio)

        if ratio > 1.0001:
            labels.append("POSE_INCSC")
        elif ratio < 0.9999:
            labels.append("POSE_MAXSAT_RC2")
        else:
            labels.append("EQUAL")

    return instances, ratios, labels


def plot_ratio(instances: list[str], ratios: list[float], labels: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    x = np.arange(len(instances))
    ratios_arr = np.array(ratios)
    labels_arr = np.array(labels)

    ax.axhline(1, color="black", linewidth=0.9, linestyle="--", zorder=1)

    incsc_idx = np.where(labels_arr == "POSE_INCSC")[0]
    maxsat_idx = np.where(labels_arr == "POSE_MAXSAT_RC2")[0]
    equal_idx = np.where(labels_arr == "EQUAL")[0]

    if incsc_idx.size:
        ax.vlines(
            x[incsc_idx],
            ymin=1,
            ymax=ratios_arr[incsc_idx],
            color=METHOD_COLORS["POSE_INCSC"],
            alpha=0.98,
            linewidth=1.9,
            linestyle="-",
            zorder=2,
        )
        ax.scatter(
            x[incsc_idx],
            ratios_arr[incsc_idx],
            marker="o",
            facecolor=METHOD_COLORS["POSE_INCSC"],
            edgecolor="black",
            s=30,
            linewidth=0.65,
            zorder=3,
        )
    if maxsat_idx.size:
        ax.vlines(
            x[maxsat_idx],
            ymin=1,
            ymax=ratios_arr[maxsat_idx],
            color=METHOD_COLORS["POSE_MAXSAT_RC2"],
            alpha=0.98,
            linewidth=1.9,
            linestyle="-",
            zorder=2,
        )
        ax.scatter(
            x[maxsat_idx],
            ratios_arr[maxsat_idx],
            marker="^",
            facecolor=METHOD_COLORS["POSE_MAXSAT_RC2"],
            edgecolor="black",
            s=32,
            linewidth=0.65,
            zorder=3,
        )
    if equal_idx.size:
        ax.scatter(
            x[equal_idx],
            ratios_arr[equal_idx],
            marker="s",
            facecolor=METHOD_COLORS["EQUAL"],
            edgecolor="black",
            s=24,
            linewidth=0.6,
            zorder=3,
        )

    tick_step = 1 if len(instances) <= 20 else 2
    tick_idx = np.arange(0, len(instances), tick_step)
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([instances[i] for i in tick_idx], rotation=55, ha="right")
    ax.tick_params(axis="x", pad=2, labelsize=10)
    ax.tick_params(axis="y", labelsize=10)

    ax.set_ylabel("Time ratio (MaxSAT-RC2 / INCSC)", fontweight="bold", fontsize=10)
    ax.set_xlabel("Instances (Same Solution Value)", fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=METHOD_COLORS["POSE_INCSC"],
            marker="o",
            markerfacecolor=METHOD_COLORS["POSE_INCSC"],
            markeredgecolor="black",
            markeredgewidth=0.65,
            linestyle="-",
            label="POSE+INCSC faster",
        ),
        Line2D(
            [0],
            [0],
            color=METHOD_COLORS["POSE_MAXSAT_RC2"],
            marker="^",
            markerfacecolor=METHOD_COLORS["POSE_MAXSAT_RC2"],
            markeredgecolor="black",
            markeredgewidth=0.65,
            linestyle="-",
            label="POSE+MaxSAT-RC2 faster",
        ),
    ]
    if equal_idx.size:
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=METHOD_COLORS["EQUAL"],
                marker="s",
                markerfacecolor=METHOD_COLORS["EQUAL"],
                markeredgecolor="black",
                markeredgewidth=0.6,
                linestyle="None",
                label="Equal",
            )
        )

    ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=True,
        fontsize=9,
        ncol=1,
        borderpad=0.3,
        handlelength=1.4,
        labelspacing=0.25,
    )

    ax.margins(x=0.02)
    plt.tight_layout(pad=0.55)
    fig.subplots_adjust(bottom=0.30, top=0.83)

    fig_dir = BASE_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    def safe_save(out_path: Path, fmt: str, **kwargs: object) -> None:
        try:
            plt.savefig(out_path, format=fmt, **kwargs)
        except PermissionError:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
            plt.savefig(fallback, format=fmt, **kwargs)
            print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")

    safe_save(fig_dir / "maxsat_speedup_lollipop_1col.png", "png", dpi=600, bbox_inches="tight")
    safe_save(fig_dir / "maxsat_speedup_lollipop_1col.pdf", "pdf", bbox_inches="tight", pad_inches=0.01)
    safe_save(fig_dir / "maxsat_speedup_lollipop_1col.eps", "eps", bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)


def main() -> None:
    flat_df = _flatten_raw_csv(CSV_PATH)
    instances, ratios, labels = build_ratio_data(flat_df)
    plot_ratio(instances, ratios, labels)
    print(f"Plotted {len(instances)} same-value instances")


if __name__ == "__main__":
    main()

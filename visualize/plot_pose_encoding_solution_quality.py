"""Runtime plot for hard instances under SAT encodings."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 7
plt.rcParams["axes.titlesize"] = 8
plt.rcParams["axes.labelsize"] = 7.5
plt.rcParams["xtick.labelsize"] = 6.3
plt.rcParams["ytick.labelsize"] = 6.8
plt.rcParams["legend.fontsize"] = 6
plt.rcParams["hatch.linewidth"] = 0.25

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"

SOLVER_MAP = {
    "POSE+INCSC": "POSE+INCSC",
    "DSE+INCSC": "DSE+INCSC",
    "Card seqcounter+INCSC": "CARD-Seq+INCSC",
}

SOLVER_COLORS = {
    "POSE+INCSC": "steelblue",
    "DSE+INCSC": "forestgreen",
    "CARD-Seq+INCSC": "darkorange",
}


def _canon_header(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


CANON_SOLVER_MAP = {_canon_header(key): value for key, value in SOLVER_MAP.items()}


def _to_sol(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    if text in {"", "-", "TO", "TIMEOUT", "OOM", "MO", "N/A"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_time(value: object, status: str) -> float | None:
    if pd.isna(value):
        return None
    if _is_timeout(status):
        return 600.0
    text = str(value).strip()
    if text in {"", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _status(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


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

    metric_alias = {
        "value": "Solution",
        "solution": "Solution",
        "obj": "Solution",
        "time": "Time",
        "status": "Status",
    }

    for col_idx in range(1, raw.shape[1]):
        group = normalized_top[col_idx]
        metric = str(raw.columns[col_idx][1]).strip().lower()
        solver = CANON_SOLVER_MAP.get(_canon_header(group))
        if solver is None:
            continue

        metric_name = metric_alias.get(metric)
        if metric_name is None:
            continue

        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    out = out.loc[:, ~out.columns.duplicated()]
    return out[~out["Bench"].str.casefold().eq("total time")].copy()


def _format_instance_name(name: str) -> str:
    text = str(name).strip()
    match = re.fullmatch(r"(?i)scen(\d+)", text)
    if match:
        return f"C{int(match.group(1)):02d}"
    match = re.fullmatch(r"(?i)graph(\d+)", text)
    if match:
        return f"G{int(match.group(1)):02d}"
    match = re.fullmatch(r"(?i)tud(\d+)\.(\d+)", text)
    if match:
        return f"T{str(int(match.group(1)))[0]}.{int(match.group(2))}"
    return text


def _is_opt(status: str) -> bool:
    return status in {"OPT", "OPTIMAL"}


def _is_timeout(status: str) -> bool:
    return status in {"TO", "TIMEOUT", "OOM", "MO"}


def main() -> None:
    print("--- READING CSV FILE ---")
    flat_df = _flatten_raw_csv(CSV_PATH)
    print("Parsed columns:", list(flat_df.columns))

    instances = []
    solver_times = {solver: [] for solver in SOLVER_MAP.values()}
    solver_opt_flags = {solver: [] for solver in SOLVER_MAP.values()}

    for _, row in flat_df.iterrows():
        bench = row.get("Bench")
        pose_solution = _to_sol(row.get("POSE+INCSC__Solution"))
        pose_status = _status(row.get("POSE+INCSC__Status"))

        if pose_solution is None or not _is_opt(pose_status):
            continue

        has_baseline_timeout = any(
            _is_timeout(_status(row.get(f"{solver}__Status")))
            for solver in ("DSE+INCSC", "CARD-Seq+INCSC")
        )
        if not has_baseline_timeout:
            continue

        instances.append(_format_instance_name(bench))

        for solver in SOLVER_MAP.values():
            status = _status(row.get(f"{solver}__Status"))
            time_value = _to_time(row.get(f"{solver}__Time"), status)
            solver_times[solver].append(time_value if time_value is not None else 0)
            solver_opt_flags[solver].append(_is_opt(status))

    print(f"-> Selected {len(instances)} instances for plotting: {instances}")

    if len(instances) == 0:
        print("\n[WARNING] No data found for plotting. Please verify CSV content.")
        return

    x = list(range(len(instances)))
    width = 0.19
    fig, ax = plt.subplots(figsize=(4.2, 2.9))

    offsets = {
        "POSE+INCSC": -width,
        "DSE+INCSC": 0,
        "CARD-Seq+INCSC": width,
    }
    rects_by_solver = {}
    for solver in SOLVER_MAP.values():
        rects_by_solver[solver] = ax.bar(
            [idx + offsets[solver] for idx in x],
            solver_times[solver],
            width,
            label=solver,
            color=SOLVER_COLORS[solver],
            edgecolor="black",
            linewidth=0.3,
            zorder=3,
        )

    def annotate_timeout(rects, solver):
        for idx, rect in enumerate(rects):
            if solver_times[solver][idx] >= 600.0 and not solver_opt_flags[solver][idx]:
                ax.text(
                    rect.get_x() + rect.get_width() / 2,
                    rect.get_height() * 0.6,
                    "TO",
                    ha="center",
                    va="bottom",
                    color="0.2",
                    fontweight="bold",
                    rotation=90,
                    fontsize=5.6,
                )

    def annotate_opt(rects, values, flags):
        for idx, rect in enumerate(rects):
            if idx < len(flags) and flags[idx] and values[idx] > 0:
                y = rect.get_height() * 1.12
                ax.scatter(
                    rect.get_x() + rect.get_width() / 2,
                    y,
                    marker="*",
                    s=6,
                    c="black",
                    zorder=6,
                    clip_on=False,
                )

    for solver in ("DSE+INCSC", "CARD-Seq+INCSC"):
        annotate_timeout(rects_by_solver[solver], solver)
    for solver in SOLVER_MAP.values():
        annotate_opt(rects_by_solver[solver], solver_times[solver], solver_opt_flags[solver])

    ax.set_yscale("log")
    ax.set_ylim((0.05, 1200))
    ax.set_ylabel("Solving Time (s)", fontweight="bold")
    ax.set_xlabel("Hard Instances", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(instances, rotation=30, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)

    legend_handles = [
        Patch(facecolor=SOLVER_COLORS[solver], edgecolor="black", linewidth=0.3, label=solver)
        for solver in SOLVER_MAP.values()
    ]
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="*",
            color="black",
            markerfacecolor="black",
            linestyle="None",
            markersize=3.5,
            label="Optimal",
        )
    )

    ax.legend(
        handles=legend_handles,
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="0.35",
        framealpha=0.95,
        ncol=1,
        borderpad=0.35,
        handlelength=1.8,
        handleheight=1.0,
        handletextpad=0.8,
        labelspacing=0.35,
    )

    ax.margins(x=0.05)
    plt.tight_layout(pad=0.25)

    fig_dir = BASE_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    def safe_save(out_path: Path, fmt: str) -> None:
        try:
            plt.savefig(out_path, format=fmt, dpi=300)
        except PermissionError:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
            plt.savefig(fallback, format=fmt, dpi=300)
            print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")

    safe_save(fig_dir / "pose_encoding_runtime_bar.pdf", "pdf")
    safe_save(fig_dir / "pose_encoding_runtime_bar.png", "png")
    safe_save(fig_dir / "pose_encoding_runtime_bar.eps", "eps")

    if "agg" not in plt.get_backend().lower():
        plt.show()


if __name__ == "__main__":
    main()

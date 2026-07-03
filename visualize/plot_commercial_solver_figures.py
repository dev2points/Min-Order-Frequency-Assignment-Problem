"""Generate commercial-solver comparison figures with CP-SAT included."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from plot_style import METHOD_COLORS


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"
FIG_DIR = BASE_DIR / "figures"
TIMEOUT_VALUE = 600.0

SOLVER_MAP = {
    "POSE+INCSC": "POSE+INCSC",
    "Gurobi": "Gurobi",
    "CPLEX/CP": "CPLEX-CP",
    "CPLEX/MIP": "CPLEX-MIP",
    "CP-SAT": "CP-SAT",
}

SOLVERS = ["POSE+INCSC", "Gurobi", "CPLEX-CP", "CPLEX-MIP", "CP-SAT"]


def _to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text in {"", "-", "TO", "TIMEOUT", "OOM", "N/A"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _flatten_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1])
    out = pd.DataFrame()
    out["Bench"] = raw.iloc[:, 0].astype(str).str.strip()

    current_group = ""
    normalized_groups: list[str] = []
    for top_header, _ in raw.columns:
        header = str(top_header).strip()
        if header and not header.startswith("Unnamed:"):
            current_group = header
        normalized_groups.append(current_group)

    metric_alias = {
        "Value": "Solution",
        "Time": "Total time",
        "Status": "Status",
    }
    for col_idx in range(1, raw.shape[1]):
        solver = SOLVER_MAP.get(normalized_groups[col_idx])
        metric = metric_alias.get(str(raw.columns[col_idx][1]).strip())
        if solver is None or metric is None:
            continue
        out[f"{solver}__{metric}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def _format_instance_name(name: object) -> str:
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


def _safe_save(out_path: Path, fmt: str, **kwargs: object) -> None:
    try:
        plt.savefig(out_path, format=fmt, **kwargs)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
        plt.savefig(fallback, format=fmt, **kwargs)
        print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")


def _prepare_cactus(times: list[float]) -> tuple[np.ndarray, np.ndarray]:
    if not times:
        return np.array([]), np.array([])
    sorted_times = np.sort(np.array(times))
    solved_times = sorted_times[sorted_times < TIMEOUT_VALUE]
    return np.arange(1, len(solved_times) + 1), solved_times


def plot_cactus(df: pd.DataFrame) -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
    })

    solver_times: dict[str, list[float]] = {solver: [] for solver in SOLVERS}
    for _, row in df.iterrows():
        for solver in SOLVERS:
            time_value = _to_num(row.get(f"{solver}__Total time"))
            if time_value is not None:
                solver_times[solver].append(time_value)

    fig, ax = plt.subplots(figsize=(8, 6))
    styles = {
        "POSE+INCSC": dict(linewidth=2.5, linestyle="-", marker="o", markersize=5, zorder=6),
        "Gurobi": dict(linewidth=2.0, linestyle="--", marker="s", markersize=5),
        "CPLEX-CP": dict(linewidth=2.0, linestyle="-.", marker="^", markersize=5),
        "CPLEX-MIP": dict(linewidth=2.0, linestyle=":", marker="d", markersize=5),
        "CP-SAT": dict(linewidth=2.0, linestyle=(0, (3, 1, 1, 1)), marker="x", markersize=5),
    }

    for solver in SOLVERS:
        x_axis, y_axis = _prepare_cactus(solver_times[solver])
        ax.plot(
            x_axis,
            y_axis,
            label=solver,
            color=METHOD_COLORS[solver],
            **styles[solver],
        )

    ax.set_yscale("log")
    ax.set_ylim((0.005, 1200))
    ax.set_xlim((0, 36))
    ax.set_xlabel("Number of Solved Instances (OPT/INF before timeout)", fontweight="bold")
    ax.set_ylabel("Time (s)", fontweight="bold")
    ax.axhline(y=TIMEOUT_VALUE, color="gray", linestyle="-", alpha=0.5)
    ax.text(1, TIMEOUT_VALUE + 50, f"Timeout limit ({int(TIMEOUT_VALUE)}s)", color="gray", fontsize=10, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.4)
    ax.legend(loc="lower right", frameon=True, edgecolor="black")

    plt.tight_layout()
    _safe_save(FIG_DIR / "sota_cactus_plot.pdf", "pdf", dpi=300)
    _safe_save(FIG_DIR / "sota_cactus_plot.png", "png", dpi=300)
    _safe_save(FIG_DIR / "sota_cactus_plot.eps", "eps", dpi=300)
    plt.close(fig)


def plot_solution_quality(df: pd.DataFrame) -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 7,
        "axes.titlesize": 8,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.3,
        "ytick.labelsize": 6.8,
        "legend.fontsize": 6,
        "hatch.linewidth": 0.25,
    })

    instances: list[str] = []
    solutions: dict[str, list[float]] = {solver: [] for solver in SOLVERS}
    optimal_flags: dict[str, list[bool]] = {solver: [] for solver in SOLVERS}

    for _, row in df.iterrows():
        pose_solution = _to_num(row.get("POSE+INCSC__Solution"))
        if pose_solution is None:
            continue

        row_solutions = {
            solver: _to_num(row.get(f"{solver}__Solution"))
            for solver in SOLVERS
        }
        if all(row_solutions[solver] == pose_solution for solver in SOLVERS[1:]):
            continue

        instances.append(_format_instance_name(row.get("Bench")))
        feasible_values = [value for value in row_solutions.values() if value is not None]
        best = min(feasible_values) if feasible_values else None

        for solver in SOLVERS:
            value = row_solutions[solver]
            solutions[solver].append(value if value is not None else 0.0)
            optimal_flags[solver].append(best is not None and value is not None and abs(value - best) <= 1e-9)

    print(f"Selected {len(instances)} solution-quality instances: {instances}")
    if not instances:
        return

    x = np.arange(len(instances))
    width = 0.15
    offsets = {
        "POSE+INCSC": -2 * width,
        "Gurobi": -1 * width,
        "CPLEX-CP": 0,
        "CPLEX-MIP": 1 * width,
        "CP-SAT": 2 * width,
    }

    fig, ax = plt.subplots(figsize=(4.2, 2.9))
    bars = {}
    for solver in SOLVERS:
        bars[solver] = ax.bar(
            x + offsets[solver],
            solutions[solver],
            width,
            label=solver,
            color=METHOD_COLORS[solver],
            edgecolor="black",
            linewidth=0.3,
            zorder=3,
        )

    ax.set_ylabel("Solution Value (No. of Frequencies)", fontweight="bold")
    ax.set_xlabel("Instances (Different Solution Value)", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(instances, rotation=30, ha="right")

    for solver in SOLVERS[1:]:
        for idx, rect in enumerate(bars[solver]):
            if solutions[solver][idx] == 0:
                ax.text(
                    rect.get_x() + rect.get_width() / 2,
                    0.9,
                    "N/A",
                    ha="center",
                    va="bottom",
                    color="0.2",
                    fontweight="bold",
                    rotation=90,
                    fontsize=5.6,
                )

    for solver in SOLVERS:
        for idx, rect in enumerate(bars[solver]):
            if optimal_flags[solver][idx] and solutions[solver][idx] > 0:
                y_pos = rect.get_height() + max(0.7, rect.get_height() * 0.025)
                ax.scatter(
                    rect.get_x() + rect.get_width() / 2,
                    y_pos,
                    marker="*",
                    s=6,
                    c="black",
                    zorder=6,
                    clip_on=False,
                )

    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    legend_handles = [
        Patch(facecolor=METHOD_COLORS[solver], edgecolor="black", linewidth=0.3, label=solver)
        for solver in SOLVERS
    ]
    legend_handles.append(
        Line2D([0], [0], marker="*", color="black", markerfacecolor="black", linestyle="None", markersize=3.5, label="Optimal")
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
    _safe_save(FIG_DIR / "solution_quality_bar.pdf", "pdf", dpi=300)
    _safe_save(FIG_DIR / "solution_quality_bar.png", "png", dpi=300)
    _safe_save(FIG_DIR / "solution_quality_bar.eps", "eps", dpi=300)
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = _flatten_csv(CSV_PATH)
    plot_cactus(df)
    plot_solution_quality(df)


if __name__ == "__main__":
    main()

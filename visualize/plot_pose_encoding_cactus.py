"""Cactus plot for POSE, DSE, and CARD-Seq SAT encodings."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 12

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "stats_csv" / "generated_comparison" / "preprocess_new.csv"
TIMEOUT_VALUE = 600.0

SOLVER_MAP = {
    "POSE+INCSC": "POSE+INCSC",
    "DSE+INCSC": "DSE+INCSC",
    "Card seqcounter+INCSC": "CARD-Seq+INCSC",
}

SOLVER_STYLES = {
    "POSE+INCSC": dict(color="steelblue", linewidth=2.5, marker="o", markersize=5, linestyle="-", zorder=5),
    "DSE+INCSC": dict(color="forestgreen", linewidth=2, marker="s", markersize=5, linestyle="--"),
    "CARD-Seq+INCSC": dict(color="darkorange", linewidth=2, marker="d", markersize=5, linestyle=":"),
}


def _to_num(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    if text in {"", "-"}:
        return None
    if text in {"TO", "TIMEOUT", "OOM", "MO"}:
        return TIMEOUT_VALUE
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
        solver = SOLVER_MAP.get(group)
        if solver is None:
            continue

        metric_name = {"Time": "Total time", "Status": "Status"}.get(metric)
        if metric_name is None:
            continue

        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    out = out.loc[:, ~out.columns.duplicated()]
    return out[~out["Bench"].str.casefold().eq("total time")].copy()


def _prepare_cactus(times: list[float]) -> tuple[np.ndarray, np.ndarray]:
    sorted_times = np.sort(np.array(times, dtype=float))
    solved = sorted_times[sorted_times < TIMEOUT_VALUE]
    x_axis = np.arange(1, len(solved) + 1)
    return x_axis, solved


def main() -> None:
    flat_df = _flatten_raw_csv(CSV_PATH)

    solver_times = {solver: [] for solver in SOLVER_MAP.values()}
    for _, row in flat_df.iterrows():
        for solver in solver_times:
            time_value = _to_num(row.get(f"{solver}__Total time"))
            if time_value is not None:
                solver_times[solver].append(time_value)

    fig, ax = plt.subplots(figsize=(8, 6))
    for solver, times in solver_times.items():
        x_axis, y_axis = _prepare_cactus(times)
        ax.plot(x_axis, y_axis, label=solver, **SOLVER_STYLES[solver])

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
    fig_dir = BASE_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_dir / "pose_encoding_cactus_plot.pdf", format="pdf", dpi=300)
    plt.savefig(fig_dir / "pose_encoding_cactus_plot.png", format="png", dpi=300)
    plt.savefig(fig_dir / "pose_encoding_cactus_plot.eps", format="eps", dpi=300)

    if "agg" not in plt.get_backend().lower():
        plt.show()


if __name__ == "__main__":
    main()

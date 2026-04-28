import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib.lines import Line2D
from matplotlib.legend import Legend

if not hasattr(Legend, "_ncol"):
    Legend._ncol = property(lambda self: getattr(self, "_ncols", 1))

if not hasattr(Legend, "legendHandles"):
    Legend.legendHandles = property(lambda self: getattr(self, "legend_handles", []))

# IEEE-like font setup
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 11

BASE_DIR = Path(__file__).resolve().parent
CSV_WITH_PRE = BASE_DIR / "result_file" / "preprocess.csv"
CSV_WITHOUT_PRE = BASE_DIR / "result_file" / "nopreprocess.csv"

SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE+INCSC",
    "PSE tot assumptions": "POSE+INC",
    "pairwise nsc assumptions": "DSE+INCSC",
    "Gurobi": "Gurobi",
    "CPLEX/CP": "CPLEX-CP",
    "CPLEX/MIP": "CPLEX-MIP",
}

SOLVER_ORDER = ["POSE+INCSC", "POSE+INC", "DSE+INCSC", "Gurobi", "CPLEX-CP", "CPLEX-MIP"]

# Keep colors consistent with previous figures for commercial solvers.
SOLVER_COLORS = {
    "POSE+INCSC": "steelblue",
    "POSE+INC": "slateblue",
    "DSE+INCSC": "teal",
    "Gurobi": "forestgreen",
    "CPLEX-CP": "#FF00FF",
    "CPLEX-MIP": "darkorange",
}

TIMEOUT_STATUS = {"TO", "TIMEOUT", "OOM"}
TIMEOUT_VALUE = 600.0
PREPROCESS_CAPTION = "Impact of Pre-processing on 35 Benchmark Instances"

INF_STATUS = {"INF", "INFEASIBLE", "UNSAT"}
OPT_STATUS = {"OPT", "OPTIMAL"}
STATUS_MARKERS = {"INF": "^"}


def _canon(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


_CANON_MAP = {_canon(k): v for k, v in SOLVER_MAP.items()}


def _to_num_time(v, status=""):
    if pd.isna(v):
        return None
    t = str(v).strip()
    st = str(status).strip().upper()
    if t in {"", "-"}:
        return None
    if st in TIMEOUT_STATUS:
        return TIMEOUT_VALUE
    try:
        return float(t)
    except ValueError:
        return TIMEOUT_VALUE if t.upper() in TIMEOUT_STATUS else None


def _normalize_status(v) -> str:
    s = str(v).strip().upper() if not pd.isna(v) else ""
    if s in INF_STATUS:
        return "INF"
    if s in OPT_STATUS:
        return "OPT"
    return "TO"


def _has_value(v) -> bool:
    if pd.isna(v):
        return False
    s = str(v).strip()
    return s not in {"", "-", "nan", "None"}


def _normalize_status_detail(status, solution) -> str:
    base = _normalize_status(status)
    if base != "TO":
        return base
    return "TO_WITH_RESULT" if _has_value(solution) else "TO_NO_RESULT"


def _flatten_raw_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, header=[0, 1])
    out = pd.DataFrame()
    out["Bench"] = raw.iloc[:, 0].astype(str).str.strip()

    top_headers = [str(raw.columns[i][0]).strip() for i in range(raw.shape[1])]
    normalized_top = []
    current_group = ""
    for h in top_headers:
        if h == "" or h.startswith("Unnamed:"):
            normalized_top.append(current_group)
        else:
            current_group = h
            normalized_top.append(h)

    metric_alias = {"value": "Solution", "time": "Total time", "status": "Status"}

    for col_idx in range(1, raw.shape[1]):
        group = normalized_top[col_idx]
        metric = str(raw.columns[col_idx][1]).strip().lower()
        solver = _CANON_MAP.get(_canon(group))
        metric_name = metric_alias.get(metric)
        if solver is None or metric_name is None:
            continue
        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def _build_compare_df(pre_path: Path, no_path: Path) -> pd.DataFrame:
    pre = _flatten_raw_csv(pre_path).rename(columns={"Bench": "Instance"})
    no = _flatten_raw_csv(no_path).rename(columns={"Bench": "Instance"})

    rows = []
    instances = sorted(set(pre["Instance"].tolist()) & set(no["Instance"].tolist()))
    for ins in instances:
        r_pre = pre[pre["Instance"] == ins].iloc[0]
        r_no = no[no["Instance"] == ins].iloc[0]
        for solver in SOLVER_ORDER:
            sol_pre = r_pre.get(f"{solver}__Solution", "")
            sol_no = r_no.get(f"{solver}__Solution", "")
            st_pre = r_pre.get(f"{solver}__Status", "")
            st_no = r_no.get(f"{solver}__Status", "")
            t_pre = _to_num_time(r_pre.get(f"{solver}__Total time"), st_pre)
            t_no = _to_num_time(r_no.get(f"{solver}__Total time"), st_no)
            if t_pre is None or t_no is None:
                continue
            rows.append(
                {
                    "Instance": ins,
                    "Solver": solver,
                    "Solution_Pre": sol_pre,
                    "Solution_No_Pre": sol_no,
                    "Time_Pre": t_pre,
                    "Time_No_Pre": t_no,
                    "Status_Pre": _normalize_status_detail(st_pre, sol_pre),
                    "Status_No_Pre": _normalize_status_detail(st_no, sol_no),
                }
            )

    return pd.DataFrame(rows)


def plot_time_tradeoff_by_solver(comp_df: pd.DataFrame):
    agg = (
        comp_df.groupby("Solver", as_index=False)[["Time_Pre", "Time_No_Pre"]]
        .median()
        .set_index("Solver")
        .reindex(SOLVER_ORDER)
        .dropna(how="all")
        .reset_index()
    )

    x = np.arange(len(agg))
    width = 0.38
    fig, ax = plt.subplots(figsize=(9.5, 5.2))

    for i, row in agg.iterrows():
        c = SOLVER_COLORS[row["Solver"]]
        ax.bar(x[i] - width / 2, row["Time_No_Pre"], width, color="white", edgecolor=c, hatch="//", linewidth=1.4)
        ax.bar(x[i] + width / 2, row["Time_Pre"], width, color=c, edgecolor="black", linewidth=0.9)

    ax.set_yscale("log")
    ax.set_ylabel("Median solving time (s)", fontweight="bold")
    ax.set_xlabel("Method", fontweight="bold")
    # ax.set_title("Pre-processing vs. No Pre-processing (per method)", fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(agg["Solver"], rotation=15)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    # Compact condition legend
    from matplotlib.patches import Patch

    cond_handles = [
        Patch(facecolor="white", edgecolor="black", hatch="//", label="No pre-processing"),
        Patch(facecolor="black", edgecolor="black", label="With pre-processing"),
    ]
    ax.legend(handles=cond_handles, loc="upper left", frameon=True, edgecolor="black")

    plt.tight_layout()
    out_dir = BASE_DIR / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "iv_b_time_tradeoff_by_solver.pdf", format="pdf", dpi=300)


def plot_runtime_scatter_by_solver(comp_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7.2, 6.6))

    min_v = min(comp_df["Time_No_Pre"].min(), comp_df["Time_Pre"].min())
    max_v = max(comp_df["Time_No_Pre"].max(), comp_df["Time_Pre"].max())
    lo = max(1e-3, min_v * 0.7)
    hi = max_v * 1.3

    for solver in SOLVER_ORDER:
        sub_solver = comp_df[comp_df["Solver"] == solver]
        if sub_solver.empty:
            continue

        inf = sub_solver[sub_solver["Status_Pre"] == "INF"]
        if not inf.empty:
            ax.scatter(
                inf["Time_No_Pre"],
                inf["Time_Pre"],
                s=52,
                marker=STATUS_MARKERS["INF"],
                color=SOLVER_COLORS[solver],
                edgecolor="black",
                alpha=0.85,
            )

        feasible = sub_solver[sub_solver["Status_Pre"] != "INF"]
        if not feasible.empty:
            ax.scatter(
                feasible["Time_No_Pre"],
                feasible["Time_Pre"],
                s=52,
                marker="o",
                color=SOLVER_COLORS[solver],
                edgecolor="black",
                alpha=0.85,
            )

    ax.plot([lo, hi], [lo, hi], "k--", alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Time without pre-processing (s)", fontweight="bold")
    ax.set_ylabel("Time with pre-processing (s)", fontweight="bold")
    # ax.set_title(PREPROCESS_CAPTION, fontweight="bold", pad=12)
    ax.grid(True, which="both", linestyle="--", alpha=0.35)

    # Split legend: colors for solvers, markers for status (on pre-processing side)
    solver_handles = [
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               markerfacecolor=SOLVER_COLORS[s], markeredgecolor="black", label=s)
        for s in SOLVER_ORDER if not comp_df[comp_df["Solver"] == s].empty
    ]
    status_handles = [
        Line2D([0], [0], marker=STATUS_MARKERS["INF"], linestyle="None", markersize=8,
               markerfacecolor="white", markeredgecolor="black", label="Infeasible (INF)"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=8,
               markerfacecolor="white", markeredgecolor="black", label="Feasible"),
    ]
    diag_handle = Line2D([0], [0], linestyle="--", color="black", label="y = x")

    leg1 = ax.legend(handles=solver_handles, loc="upper left", frameon=True, edgecolor="black", ncol=2)
    ax.add_artist(leg1)
    ax.legend(handles=status_handles + [diag_handle], loc="lower right", frameon=True, edgecolor="black")

    plt.tight_layout()
    out_dir = BASE_DIR / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "iv_b_runtime_scatter_by_solver.pdf", format="pdf", dpi=300)


if __name__ == "__main__":
    print("--- LOADING preprocess vs nopreprocess CSVs ---")
    comp = _build_compare_df(CSV_WITH_PRE, CSV_WITHOUT_PRE)
    if comp.empty:
        print("[WARNING] No comparable rows found. Please verify CSV headers.")
    else:
        print(f"Loaded {len(comp)} rows ({comp['Instance'].nunique()} instances).")
        plot_time_tradeoff_by_solver(comp)
        plot_runtime_scatter_by_solver(comp)
        print("Saved IV-B figures in figures/.")

    if "agg" not in plt.get_backend().lower():
        plt.show()


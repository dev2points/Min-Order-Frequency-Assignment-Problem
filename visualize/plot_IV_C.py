import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Cài đặt font chuẩn IEEE (Times New Roman / Serif)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 12

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "result_file" / "preprocess.csv"

SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE_INCSC",
    "pairwise nsc assumptions": "DSE",
}

TIMEOUT_STATUS = {"TO", "TIMEOUT", "TL", "MO", "OOM"}
INF_STATUS = {"INF", "INFEASIBLE", "UNSAT"}
OPT_STATUS = {"OPT", "OPTIMAL"}


def _to_num(v):
    if pd.isna(v):
        return None
    t = str(v).strip()
    if t in {"", "-"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _st(v):
    if pd.isna(v):
        return ""
    return str(v).strip().upper()


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

    for col_idx in range(1, raw.shape[1]):
        group = normalized_top[col_idx]
        metric = str(raw.columns[col_idx][1]).strip()

        solver = SOLVER_MAP.get(group)
        if solver is None:
            continue

        metric_name = {"Value": "Solution", "Time": "Total time", "Status": "Status"}.get(metric)
        if metric_name is None:
            continue

        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def _build_groups(df: pd.DataFrame):
    inf_points = []
    opt_solved_points = []
    opt_timeout_points = []

    for _, row in df.iterrows():
        pose_time = _to_num(row.get("POSE_INCSC__Total time"))
        dse_time = _to_num(row.get("DSE__Total time"))
        pose_status = _st(row.get("POSE_INCSC__Status"))
        dse_status = _st(row.get("DSE__Status"))

        if pose_time is None or dse_time is None:
            continue

        # Định dạng điểm: [Thời gian DSE, Thời gian POSE]
        point = [dse_time, pose_time]

        if pose_status in INF_STATUS and dse_status in INF_STATUS:
            inf_points.append(point)
        elif pose_status in OPT_STATUS and dse_status in OPT_STATUS:
            opt_solved_points.append(point)
        elif pose_status in OPT_STATUS and dse_status in TIMEOUT_STATUS:
            opt_timeout_points.append(point)

    def as_array(points):
        if not points:
            return np.empty((0, 2), dtype=float)
        return np.array(points, dtype=float)

    return as_array(inf_points), as_array(opt_solved_points), as_array(opt_timeout_points)


flat_df = _flatten_raw_csv(CSV_PATH)
inf_data, opt_solved_data, opt_timeout_data = _build_groups(flat_df)

# Khởi tạo đồ thị
fig, ax = plt.subplots(figsize=(7, 6))

# Vẽ đường chéo y = x (Đường ranh giới tốc độ)
x_vals = [0.005, 1000]
ax.plot(x_vals, x_vals, 'k--', alpha=0.6, label='Equal Time ($y=x$)')

# Vẽ vạch Timeout 600s
ax.axvline(x=600, color='gray', linestyle=':', alpha=0.8)
ax.axhline(y=600, color='gray', linestyle=':', alpha=0.8)

# Scatter plot cho từng nhóm
if len(inf_data) > 0:
    ax.scatter(inf_data[:, 0], inf_data[:, 1],
               color='forestgreen', marker='^', s=60, alpha=0.8,
               label=f'INF Instances ({len(inf_data)})', edgecolors='k')

if len(opt_solved_data) > 0:
    ax.scatter(opt_solved_data[:, 0], opt_solved_data[:, 1],
               color='royalblue', marker='o', s=60, alpha=0.8,
               label=f'OPT (Both Solved) ({len(opt_solved_data)})', edgecolors='k')

if len(opt_timeout_data) > 0:
    ax.scatter(opt_timeout_data[:, 0], opt_timeout_data[:, 1],
               color='crimson', marker='*', s=150, alpha=0.9,
               label=f'OPT (DSE Timeout) ({len(opt_timeout_data)})', edgecolors='k')

# Cài đặt thang đo Logarit
ax.set_xscale('log')
ax.set_yscale('log')

# Giới hạn trục (để đồ thị có không gian thở)
ax.set_xlim((0.005, 1200))
ax.set_ylim((0.005, 1200))

# Nhãn và tiêu đề
ax.set_xlabel('Time of DSE+INCSC (s)', fontweight='bold')
ax.set_ylabel('Time of POSE+INCSC (s)', fontweight='bold')
# ax.set_title('Time Comparison: POSE+INCSC vs. DSE+INCSC', fontweight='bold', pad=15)

# Tùy chỉnh Legend
# ax.legend(loc='upper left', frameon=True, edgecolor='black')
ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.88), frameon=True, edgecolor='black')
# Thêm text chú thích Timeout
ax.text(650, 0.01, 'Timeout limit (600s)', rotation=90, va='bottom', ha='left', color='gray', fontsize=10)

# Kẻ lưới mờ cho dễ nhìn
ax.grid(True, which="both", ls="-", alpha=0.2)

# Lưu ảnh chất lượng cao để chèn vào LaTeX
plt.tight_layout()
plt.savefig('figures\\pose_vs_dse_scatter.pdf', format='pdf', dpi=300)
plt.savefig('figures\\pose_vs_dse_scatter.png', format='png', dpi=300)

if "agg" not in plt.get_backend().lower():
    plt.show()

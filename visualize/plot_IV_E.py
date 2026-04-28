import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Cài đặt font chuẩn IEEE (Times New Roman / Serif)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 12

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "result_file" / "preprocess.csv"

# ==========================================================
# CHÚ Ý: ĐẢM BẢO TÊN TRONG DICT NÀY KHỚP CHÍNH XÁC VỚI FILE CSV
# ==========================================================
SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE+INCSC",
    "Gurobi": "Gurobi",
    "CPLEX/CP": "CPLEX-CP",
    "CPLEX/MIP": "CPLEX-MIP",
}

TIMEOUT_VALUE = 600.0


def _to_num(v):
    if pd.isna(v): return None
    t = str(v).strip()
    if t in {"", "-", "TO", "TIMEOUT", "OOM"}:
        # Nếu gặp chữ Timeout, gán luôn bằng 600 để vẽ Cactus
        if t in {"TO", "TIMEOUT", "OOM"}: return TIMEOUT_VALUE
        return None
    try:
        return float(t)
    except ValueError:
        return None


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
        if solver is None: continue

        metric_name = {"Time": "Total time", "Status": "Status"}.get(metric)
        if metric_name is None: continue

        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


# 1. Đọc và làm sạch dữ liệu
flat_df = _flatten_raw_csv(CSV_PATH)

solver_times = {
    "POSE+INCSC": [],
    "Gurobi": [],
    "CPLEX-CP": [],
    "CPLEX-MIP": []
}

for _, row in flat_df.iterrows():
    for solver in solver_times.keys():
        t = _to_num(row.get(f"{solver}__Total time"))
        if t is not None:
            solver_times[solver].append(t)


# 2. Hàm chuẩn bị dữ liệu cho Cactus Plot
def prep_cactus(data_list):
    if not data_list: return [], []
    sorted_data = np.sort(np.array(data_list))
    solved = sorted_data[sorted_data < TIMEOUT_VALUE]
    x_axis = np.arange(1, len(solved) + 1)
    return x_axis, solved


x_prop, y_prop = prep_cactus(solver_times["POSE+INCSC"])
x_gur, y_gur = prep_cactus(solver_times["Gurobi"])
x_cp, y_cp = prep_cactus(solver_times["CPLEX-CP"])
x_mip, y_mip = prep_cactus(solver_times["CPLEX-MIP"])

# 3. Vẽ đồ thị
fig, ax = plt.subplots(figsize=(8, 6))

# ax.plot(x_prop, y_prop, label='POSE+INCSC', color='steelblue', linewidth=2.5, marker='o', markersize=5, zorder=5)
# ax.plot(x_gur, y_gur, label='Gurobi', color='forestgreen', linewidth=2, linestyle='--', marker='s', markersize=5)
# ax.plot(x_cp, y_cp, label='CPLEX-CP', color='royalblue', linewidth=2, linestyle='-.', marker='^', markersize=5)
# ax.plot(x_mip, y_mip, label='CPLEX-MIP', color='darkorange', linewidth=2, linestyle=':', marker='d', markersize=5)

ax.plot(x_prop, y_prop, label='POSE+INCSC', color='steelblue', linewidth=2.5, marker='o', markersize=5, zorder=5)
ax.plot(x_gur, y_gur, label='Gurobi', color='forestgreen', linewidth=2, linestyle='--', marker='s', markersize=5)
ax.plot(x_cp, y_cp, label='CPLEX-CP', color='#FF00FF', linewidth=2, linestyle='-.', marker='^', markersize=5)
ax.plot(x_mip, y_mip, label='CPLEX-MIP', color='darkorange', linewidth=2, linestyle=':', marker='d', markersize=5)

ax.set_yscale('log')
ax.set_ylim((0.005, 1200))  # Nới lên 1200 một chút để cái chữ Timeout không bị dính sát lề trên
ax.set_xlim((0, 36))

# TÙY CHỈNH TIÊU ĐỀ VÀ NHÃN TRỤC CHÍNH XÁC TỪNG CHỮ
ax.set_xlabel('Number of Solved Instances (OPT/INF before timeout)', fontweight='bold')
ax.set_ylabel('Time (s)', fontweight='bold')
# ax.set_title('Time comparison between POSE+INCSC and Commercial Solvers', fontweight='bold', pad=15)

# Vẽ vạch Timeout ngang
ax.axhline(y=TIMEOUT_VALUE, color='gray', linestyle='-', alpha=0.5)
ax.text(1, TIMEOUT_VALUE + 50, f'Timeout limit ({int(TIMEOUT_VALUE)}s)', color='gray', fontsize=10, fontweight='bold')

ax.grid(True, which="both", ls="--", alpha=0.4)
ax.legend(loc='lower right', frameon=True, edgecolor='black')

plt.tight_layout()

# 4. Lưu file ảnh chất lượng cao
fig_dir = BASE_DIR / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(fig_dir / 'sota_cactus_plot.pdf', format='pdf', dpi=300)
plt.savefig(fig_dir / 'sota_cactus_plot.png', format='png', dpi=300)

if "agg" not in plt.get_backend().lower():
    plt.show()
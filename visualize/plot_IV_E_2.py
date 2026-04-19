import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib.lines import Line2D
import re
from datetime import datetime

# Compact IEEE 1-column style for dense categorical bars.
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 7
plt.rcParams['axes.titlesize'] = 8
plt.rcParams['axes.labelsize'] = 7.5
plt.rcParams['xtick.labelsize'] = 6.3
plt.rcParams['ytick.labelsize'] = 6.8
plt.rcParams['legend.fontsize'] = 6
plt.rcParams['hatch.linewidth'] = 0.4

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "result_file" / "preprocess.csv"

# ==========================================================
# TRẢ LẠI MAP CHUẨN XÁC 100% CỦA BẠN
# ==========================================================
SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE+INCSC",
    "Gurobi": "Gurobi",
    "CPLEX/CP": "CPLEX-CP",
    "CPLEX/MIP": "CPLEX-MIP",
}


def _canon_header(s: str) -> str:
    # Chuẩn hóa nhẹ để map đúng dù header có khoảng trắng/kiểu chữ khác nhau
    return " ".join(str(s).strip().lower().split())


_CANON_SOLVER_MAP = {_canon_header(k): v for k, v in SOLVER_MAP.items()}


# Hàm parse giá trị Solution
def _to_sol(v):
    if pd.isna(v): return None
    t = str(v).strip().upper()
    if t in {"", "-", "TO", "TIMEOUT", "OOM", "N/A"}:
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

    metric_alias = {
        "value": "Solution",
        "solution": "Solution",
        "obj": "Solution",
    }

    for col_idx in range(1, raw.shape[1]):
        group = normalized_top[col_idx]
        metric = str(raw.columns[col_idx][1]).strip().lower()

        solver = _CANON_SOLVER_MAP.get(_canon_header(group))
        if solver is None:
            continue

        metric_name = metric_alias.get(metric)
        if metric_name is None:
            continue

        out[f"{solver}__{metric_name}"] = raw.iloc[:, col_idx]

    return out.loc[:, ~out.columns.duplicated()]


def _format_instance_name(name: str) -> str:
    s = str(name).strip()
    m = re.fullmatch(r"(?i)scen(\d+)", s)
    if m:
        return f"C{int(m.group(1)):02d}"
    m = re.fullmatch(r"(?i)graph(\d+)", s)
    if m:
        return f"G{int(m.group(1)):02d}"
    m = re.fullmatch(r"(?i)tud(\d+)\.(\d+)", s)
    if m:
        # Keep the same shorthand style used in the notebook: T9.1, T2.5, ...
        return f"T{str(int(m.group(1)))[0]}.{int(m.group(2))}"
    return s


# 1. Đọc dữ liệu
print("--- READING CSV FILE ---")
flat_df = _flatten_raw_csv(CSV_PATH)
print("Parsed columns:", list(flat_df.columns))

instances = []
pose_sols, gur_sols, cp_sols, mip_sols = [], [], [], []
pose_opt_flags, gur_opt_flags, cp_opt_flags, mip_opt_flags = [], [], [], []

# 2. TỰ ĐỘNG LỌC DỮ LIỆU
for _, row in flat_df.iterrows():
    bench = row.get("Bench")

    # GỌI ĐÚNG TÊN CỘT CÓ DẤU CỘNG VÀ GẠCH NGANG THEO MAP CỦA BẠN
    s_pose = _to_sol(row.get("POSE+INCSC__Solution"))
    s_gur = _to_sol(row.get("Gurobi__Solution"))
    s_cp = _to_sol(row.get("CPLEX-CP__Solution"))
    s_mip = _to_sol(row.get("CPLEX-MIP__Solution"))

    # Bỏ qua các bài toán Infeasible (Vô nghiệm từ đầu)
    if s_pose is None:
        continue

    # Kiểm tra xem các solver có ra nghiệm kém hơn không?
    match_gur = (s_gur == s_pose)
    match_cp = (s_cp == s_pose)
    match_mip = (s_mip == s_pose)

    # Nếu tất cả commercial đều bằng POSE thì bỏ qua để biểu đồ gọn hơn
    if match_gur and match_cp and match_mip:
        continue

    # Đưa vào danh sách vẽ
    instances.append(_format_instance_name(bench))
    pose_sols.append(s_pose)
    gur_sols.append(s_gur if s_gur is not None else 0)
    cp_sols.append(s_cp if s_cp is not None else 0)
    mip_sols.append(s_mip if s_mip is not None else 0)

    feasible = [v for v in [s_pose, s_gur, s_cp, s_mip] if v is not None]
    best = min(feasible) if feasible else None
    eps = 1e-9
    pose_opt_flags.append(best is not None and abs(s_pose - best) <= eps)
    gur_opt_flags.append(s_gur is not None and best is not None and abs(s_gur - best) <= eps)
    cp_opt_flags.append(s_cp is not None and best is not None and abs(s_cp - best) <= eps)
    mip_opt_flags.append(s_mip is not None and best is not None and abs(s_mip - best) <= eps)

print(f"-> Selected {len(instances)} instances for plotting: {instances}")

if len(instances) == 0:
    print("\n[WARNING] No data found for plotting. Please verify CSV content.")
else:
    # 3. Vẽ biểu đồ Bar Chart (1 cột IEEE)
    x = np.arange(len(instances))
    width = 0.16

    # Slightly taller than standard to avoid x-label collisions in 1-column format.
    fig, ax = plt.subplots(figsize=(3.45, 2.9))

    # MÀU SẮC ĐỒNG BỘ CACTUS PLOT + HẠT CHÉO ĐỂ IN ĐEN TRẮNG VẪN PHÂN BIỆT ĐƯỢC
    rects1 = ax.bar(x - 1.5 * width, pose_sols, width, label='POSE+INCSC', color='steelblue',
                    edgecolor='black', hatch='', linewidth=0.55, zorder=3)
    rects2 = ax.bar(x - 0.5 * width, gur_sols, width, label='Gurobi', color='forestgreen',
                    edgecolor='black', hatch='///', linewidth=0.55, zorder=3)
    rects3 = ax.bar(x + 0.5 * width, cp_sols, width, label='CPLEX-CP', color='#FF00FF',
                    edgecolor='black', hatch='\\\\\\', linewidth=0.55, zorder=3)
    rects4 = ax.bar(x + 1.5 * width, mip_sols, width, label='CPLEX-MIP', color='darkorange',
                    edgecolor='black', hatch='xxx', linewidth=0.55, zorder=3)

    ax.set_ylabel('Solution Value (No. of Frequencies)', fontweight='bold')
    ax.set_xlabel('Instances (Different Solution Value)', fontweight='bold')
    ax.set_title('Solution comparison between POSE+INCSC and Commercial Solvers', fontweight='bold', fontsize=5.5)
    ax.set_xticks(x)
    ax.set_xticklabels(instances, rotation=30, ha='right')


    # 4. Tự động dán nhãn N/A cho các cột bị gán bằng 0
    def annotate_na(rects, sols):
        for i, rect in enumerate(rects):
            if sols[i] == 0:
                ax.text(rect.get_x() + rect.get_width() / 2, 1.1, 'N/A', ha='center', va='bottom',
                        color='black', fontweight='bold', rotation=90, fontsize=6)

    def annotate_opt(rects, sols, flags):
        for i, rect in enumerate(rects):
            if i < len(flags) and flags[i] and sols[i] > 0:
                y = rect.get_height() + max(0.35, rect.get_height() * 0.015)
                ax.scatter(
                    rect.get_x() + rect.get_width() / 2,
                    y,
                    marker='*',
                    s=10,
                    c='black',
                    zorder=5,
                    clip_on=False,
                )


    annotate_na(rects2, gur_sols)
    annotate_na(rects3, cp_sols)
    annotate_na(rects4, mip_sols)
    annotate_opt(rects1, pose_sols, pose_opt_flags)
    annotate_opt(rects2, gur_sols, gur_opt_flags)
    annotate_opt(rects3, cp_sols, cp_opt_flags)
    annotate_opt(rects4, mip_sols, mip_opt_flags)

    # Kẻ lưới ngang
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)

    # Cấu hình Legend
    opt_handle = Line2D([0], [0], marker='*', color='black', linestyle='None', markersize=4.5,
                        label='Optimal')
    ax.legend(handles=[rects1, rects2, rects3, rects4, opt_handle],
              loc='upper left', frameon=True, edgecolor='black', ncol=1,
              borderpad=0.35, handlelength=1.4, labelspacing=0.35)

    ax.margins(x=0.05)
    plt.tight_layout(pad=0.25)

    # 5. Lưu file
    fig_dir = BASE_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    def _safe_save(fig_obj, out_path: Path, fmt: str):
        try:
            fig_obj.savefig(out_path, format=fmt, dpi=300)
        except PermissionError:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
            fig_obj.savefig(fallback, format=fmt, dpi=300)
            print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")

    _safe_save(plt, fig_dir / 'solution_quality_bar.pdf', 'pdf')
    _safe_save(plt, fig_dir / 'solution_quality_bar.png', 'png')

    if "agg" not in plt.get_backend().lower():
        plt.show()
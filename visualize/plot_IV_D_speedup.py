import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from matplotlib.lines import Line2D
from datetime import datetime

# Đồng bộ cỡ chữ với phần C.
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 12

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "result_file" / "preprocess.csv"

SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE_INCSC",
    "PSE tot assumptions": "POSE_INC", 
}

# Đồng bộ palette với các biểu đồ trước (plot_IV_B.py)
METHOD_COLORS = {
    "POSE_INCSC": "steelblue",
    "POSE_INC": "slateblue",
    "EQUAL": "dimgray",
}

# B/W-safe mode: distinguish methods by marker/linestyle so printed grayscale is still readable.
BW_SAFE = False

INSTANCE_NAME_MAP = {
    "scen01": "C01", "scen02": "C02", "scen03": "C03", "scen04": "C04", "scen05": "C05",
    "scen06": "C06", "scen07": "C07", "scen08": "C08", "scen09": "C09", "scen10": "C10", "scen11": "C11",
    "graph01": "G01", "graph02": "G02", "graph03": "G03", "graph04": "G04", "graph05": "G05",
    "graph06": "G06", "graph07": "G07", "graph08": "G08", "graph09": "G09", "graph10": "G10",
    "graph11": "G11", "graph12": "G12", "graph13": "G13", "graph14": "G14",
    "TUD200.1": "T2.1", "TUD200.2": "T2.2", "TUD200.3": "T2.3", "TUD200.4": "T2.4", "TUD200.5": "T2.5",
    "TUD916.1": "T9.1", "TUD916.2": "T9.2", "TUD916.3": "T9.3", "TUD916.4": "T9.4", "TUD916.5": "T9.5",
}

def _to_num(v):
    if pd.isna(v): return None
    t = str(v).strip()
    if t in {"", "-"}: return None
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

flat_df = _flatten_raw_csv(CSV_PATH)

instances = []
speedups = []
labels = []

# Lọc dữ liệu: Chỉ so sánh thời gian khi cùng solution (Value).
# Coi '-' và '-' là cùng nhau (INF case).
for _, row in flat_df.iterrows():
    bench = row.get("Bench")
    bench_display = INSTANCE_NAME_MAP.get(str(bench), str(bench))
    
    # Lấy solution value
    val_inc = str(row.get("POSE_INC__Value", "")).strip()
    val_incsc = str(row.get("POSE_INCSC__Value", "")).strip()
    
    # Chỉ giữ nếu cùng value (kể cả '-' = '-')
    if val_inc != val_incsc:
        continue
    
    # Lấy thời gian
    t_inc = _to_num(row.get("POSE_INC__Total time"))
    t_incsc = _to_num(row.get("POSE_INCSC__Total time"))

    # Cần có đủ dữ liệu thời gian
    if t_inc is None or t_incsc is None or t_incsc == 0:
        continue

    # Tính speedup (cho phép bằng nhau, khác nhau, hay chênh lệch nhiều)
    speedup = t_inc / t_incsc
    instances.append(bench_display)
    speedups.append(speedup)
    
    if speedup > 1.0001:  # POSE+INCSC nhanh hơn
        labels.append("POSE_INCSC")
    elif speedup < 0.9999:  # POSE+INC nhanh hơn
        labels.append("POSE_INC")
    else:  # Bằng nhau (trong sai số 0.01%)
        labels.append("EQUAL")

# Wider canvas to avoid title/tick overlap with Section C font scale.
fig, ax = plt.subplots(figsize=(7.0, 4.8))

x = np.arange(len(instances))

# Vẽ đường baseline tại mức 1.0 (Không tăng tốc)
ax.axhline(1, color='black', linewidth=0.9, linestyle='--', zorder=1)

# Vẽ dạng Lollipop theo từng nhóm để dễ phân biệt khi in đen trắng
incsc_idx = np.array([i for i, s in enumerate(labels) if s == "POSE_INCSC"], dtype=int)
inc_idx = np.array([i for i, s in enumerate(labels) if s == "POSE_INC"], dtype=int)
equal_idx = np.array([i for i, s in enumerate(labels) if s == "EQUAL"], dtype=int)

if BW_SAFE:
    # POSE+INCSC faster: circle + solid; POSE+INC faster: triangle + dashed
    if incsc_idx.size:
        ax.vlines(x[incsc_idx], ymin=1, ymax=np.array(speedups)[incsc_idx],
                  color='black', alpha=0.9, linewidth=1.6, linestyle='-', zorder=2)
        ax.scatter(x[incsc_idx], np.array(speedups)[incsc_idx],
                   marker='o', facecolor='white', edgecolor='black', s=28, linewidth=0.9, zorder=3)
    if inc_idx.size:
        ax.vlines(x[inc_idx], ymin=1, ymax=np.array(speedups)[inc_idx],
                  color='black', alpha=0.9, linewidth=1.6, linestyle='--', zorder=2)
        ax.scatter(x[inc_idx], np.array(speedups)[inc_idx],
                   marker='^', facecolor='black', edgecolor='black', s=30, linewidth=0.8, zorder=3)
    if equal_idx.size:
        ax.scatter(x[equal_idx], np.array(speedups)[equal_idx],
                   marker='s', facecolor='0.6', edgecolor='black', s=22, linewidth=0.6, zorder=3)
else:
    # Giữ đúng palette cũ, tăng tương phản bằng viền đen + marker shape khác nhau.
    if incsc_idx.size:
        ax.vlines(x[incsc_idx], ymin=1, ymax=np.array(speedups)[incsc_idx],
                  color=METHOD_COLORS['POSE_INCSC'], alpha=0.98, linewidth=1.9, linestyle='-', zorder=2)
        ax.scatter(x[incsc_idx], np.array(speedups)[incsc_idx],
                   marker='o', facecolor=METHOD_COLORS['POSE_INCSC'], edgecolor='black',
                   s=30, linewidth=0.65, zorder=3)
    if inc_idx.size:
        ax.vlines(x[inc_idx], ymin=1, ymax=np.array(speedups)[inc_idx],
                  color=METHOD_COLORS['POSE_INC'], alpha=0.98, linewidth=1.9, linestyle='-', zorder=2)
        ax.scatter(x[inc_idx], np.array(speedups)[inc_idx],
                   marker='^', facecolor=METHOD_COLORS['POSE_INC'], edgecolor='black',
                   s=32, linewidth=0.65, zorder=3)
    if equal_idx.size:
        ax.scatter(x[equal_idx], np.array(speedups)[equal_idx],
                   marker='s', facecolor=METHOD_COLORS['EQUAL'], edgecolor='black',
                   s=24, linewidth=0.6, zorder=3)

# Thin x tick labels when many instances to keep the layout readable.
tick_step = 1 if len(instances) <= 20 else 2
tick_idx = np.arange(0, len(instances), tick_step)
ax.set_xticks(tick_idx)
ax.set_xticklabels([instances[i] for i in tick_idx], rotation=55, ha='right')
ax.tick_params(axis='x', pad=2, labelsize=10)
ax.tick_params(axis='y', labelsize=11)

ax.set_ylabel('Time POSE+INC / Time POSE+INCSC)', fontweight='bold', fontsize=10)
ax.set_xlabel('Instances (Same Solution Value)', fontweight='bold')
ax.set_title('Time Comparison: POSE+INCSC vs. POSE+INC', fontweight='bold', pad=15)

# Thêm vạch lưới ngang cho dễ g\caption{Relative execution time comparison between the proposed POSE+INCSC and baseline POSE+INC on selected computationally demanding instances. Percentages indicate the relative time saved (green, negative) or increased (red, positive) by utilizing the INCSC strategy.}ióng
ax.grid(axis='y', linestyle=':', alpha=0.5)

legend_handles = [
    Line2D([0], [0], color='black' if BW_SAFE else METHOD_COLORS['POSE_INCSC'],
           marker='o', markerfacecolor='white' if BW_SAFE else METHOD_COLORS['POSE_INCSC'],
           markeredgecolor='black', markeredgewidth=0.8 if BW_SAFE else 0.65,
           linestyle='-', label='POSE+INCSC faster'),
    Line2D([0], [0], color='black' if BW_SAFE else METHOD_COLORS['POSE_INC'],
           marker='^', markerfacecolor='black' if BW_SAFE else METHOD_COLORS['POSE_INC'],
           markeredgecolor='black', markeredgewidth=0.8 if BW_SAFE else 0.65,
           linestyle='--' if BW_SAFE else '-', label='POSE+INC faster'),
]
if np.any(np.array(labels) == 'EQUAL'):
    legend_handles.append(
        Line2D([0], [0], color='0.4' if BW_SAFE else METHOD_COLORS['EQUAL'], marker='s',
               markerfacecolor='0.6' if BW_SAFE else METHOD_COLORS['EQUAL'],
               markeredgecolor='black', markeredgewidth=0.6, linestyle='None', label='Equal')
    )

ax.legend(handles=legend_handles, loc='upper right',
          frameon=True, ncol=1, borderpad=0.3, handlelength=1.4,
          labelspacing=0.25)

ax.margins(x=0.02)
plt.tight_layout(pad=0.55)
fig.subplots_adjust(bottom=0.30, top=0.83)

# Lưu file với độ phân giải siêu cao để in ấn không bị vỡ
fig_dir = BASE_DIR / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)

def _safe_save(out_path: Path, fmt: str, **kwargs):
    try:
        plt.savefig(out_path, format=fmt, **kwargs)
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = out_path.with_name(f"{out_path.stem}_{stamp}{out_path.suffix}")
        plt.savefig(fallback, format=fmt, **kwargs)
        print(f"[WARNING] File locked: {out_path.name}. Saved fallback: {fallback.name}")

_safe_save(fig_dir / 'speedup_lollipop_1col.png', 'png', dpi=600, bbox_inches='tight')
_safe_save(fig_dir / 'speedup_lollipop_1col.pdf', 'pdf', bbox_inches='tight', pad_inches=0.01)

if "agg" not in plt.get_backend().lower():
    plt.show()
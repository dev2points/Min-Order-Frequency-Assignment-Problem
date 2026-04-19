import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Cài đặt font chuẩn IEEE
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 16
plt.rcParams['axes.titlesize'] = 24
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 16
plt.rcParams['legend.fontsize'] = 16

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "result_file" / "preprocess.csv"

# ==========================================================
# CHÚ Ý: BẠN CẦN THAY TÊN CỘT GỐC CỦA PHƯƠNG PHÁP POSE+INC Ở ĐÂY
# ==========================================================
SOLVER_MAP = {
    "PSE nsc_asumptions": "POSE_INCSC",
    "PSE tot assumptions": "POSE_INC",  # <--- SỬA CHỖ NÀY !!!
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

TIME_DIFF_ATOL = 1e-6
TIME_DIFF_RTOL = 1e-6


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


# 1. Đọc dữ liệu
flat_df = _flatten_raw_csv(CSV_PATH)

instances = []
inc_times = []
incsc_times = []

# 2. Rút trích và Lọc dữ liệu thông minh
for _, row in flat_df.iterrows():
    bench = row.get("Bench")
    bench_display = INSTANCE_NAME_MAP.get(str(bench), str(bench))
    t_inc = _to_num(row.get("POSE_INC__Total time"))
    t_incsc = _to_num(row.get("POSE_INCSC__Total time"))

    # Bỏ qua nếu thiếu dữ liệu
    if t_inc is None or t_incsc is None:
        continue

    # Chỉ giữ các benchmark có thời gian khác nhau giữa 2 phương pháp.
    # Dùng tolerance để tránh nhiễu do sai số số thực.
    if not np.isclose(t_inc, t_incsc, rtol=TIME_DIFF_RTOL, atol=TIME_DIFF_ATOL):
        instances.append(bench_display)
        inc_times.append(t_inc)
        incsc_times.append(t_incsc)

# 3. Vẽ biểu đồ
x = np.arange(len(instances))
width = 0.35

# Céo dài biểu đồ ra cho đỡ chật (figsize 12x5 thay vì 8x5)
fig, ax = plt.subplots(figsize=(28, 15))

rects1 = ax.bar(x - width / 2, incsc_times, width, label='POSE+INCSC',
                color='steelblue', edgecolor='black')
rects2 = ax.bar(x + width / 2, inc_times, width, label='POSE+INC',
                color='lightcoral', edgecolor='black', hatch='//')


# # MÀU XANH STEELBLUE TRƠN CHO POSE+INCSC
# rects2 = ax.bar(x + width/2, incsc_times, width, label='POSE+INCSC',
#                 color='steelblue', edgecolor='black')
#
# # MÀU ĐỎ NHẠT GẠCH CHÉO CHO POSE+INC
# rects1 = ax.bar(x - width/2, inc_times, width, label='POSE+INC',
#                 color='lightcoral', edgecolor='black', hatch='//')

# Dùng log-scale để nhìn rõ cả cột nhỏ và cột lớn trong cùng một hình.
if instances:
    positive_vals = [v for v in (inc_times + incsc_times) if v > 0]
    y_min = min(positive_vals)
    y_max = max(positive_vals)
    ax.set_yscale('log')
    ax.set_ylim(y_min * 0.75, y_max * 1.75)
    ax.margins(x=0.01, y=0.06)

ax.set_ylabel('Time (s)', fontweight='bold')
ax.set_xlabel('Instances (Different Solving Time)', fontweight='bold')
ax.set_title('Time Comparison: POSE+INCSC vs. POSE+INC', fontweight='bold', pad=20)

# Xoay tên instance 45 độ cho dễ đọc
ax.set_xticks(x)
ax.set_xticklabels(instances, rotation=45, ha='right')
ax.legend(loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.7)

# 4. Tính toán và ghi chú % lên đầu cột
if instances:
    y_top = ax.get_ylim()[1]
    for i in range(len(instances)):
        t_inc = inc_times[i]
        t_incsc = incsc_times[i]
        bar_top = max(t_inc, t_incsc)

        if t_incsc < t_inc and t_inc != 0:
            saved_pct = ((t_inc - t_incsc) / t_inc) * 100
            text = f'-{saved_pct:.1f}%'
            color = 'green'
        elif t_inc != 0:
            inc_pct = ((t_incsc - t_inc) / t_inc) * 100
            text = f'+{inc_pct:.1f}%'
            color = 'red'
        else:
            text = '-'
            color = 'black'
        
        near_top = bar_top > y_top * 0.9
        # So le nhe vi tri nhan de giam de chu khi de ngang.
        x_offset = -6 if i % 2 == 0 else 6
        y_offset = -10 if near_top else (8 if i % 2 == 0 else 16)
        va = 'top' if near_top else 'bottom'

        ax.annotate(
            text,
            xy=(x[i], bar_top),
            xytext=(x_offset, y_offset),
            textcoords='offset points',
            ha='center',
            va=va,
            fontweight='bold',
            color=color,
            fontsize=14,
            rotation=0,
            clip_on=False,
        )

# Căn chỉnh để label X không bị cắt
plt.tight_layout(pad=1.3)
fig.subplots_adjust(top=0.87, bottom=0.26)

# Lưu file
fig_dir = BASE_DIR / "figures"
fig_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(
    fig_dir / 'inc_vs_incsc_bar_log.png',
    format='png',
    dpi=300,
    bbox_inches='tight',
    pad_inches=0.28,
)

if "agg" not in plt.get_backend().lower():
    plt.show()
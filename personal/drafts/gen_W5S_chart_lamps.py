"""
摸魚記 W5S 圖表 B：三市場亮燈對照圖
台灣 6/11 vs 韓國 6/8 vs 韓國 6/23 vs 日本 6/23
四盞燈 × 四個時間點，視覺化亮燈狀態與市場背景
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

CJK_CANDIDATES = [
    '/usr/local/share/fonts/NotoSerifTC.otf',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]
CJK_FONT = next(p for p in CJK_CANDIDATES if os.path.exists(p))
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
matplotlib.rcParams['font.family'] = prop.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

NAVY  = "#1a2744"
GOLD  = "#b8954a"
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"
OFF   = "#3a4a6b"
BLUE  = "#2980b9"

# ── data ──────────────────────────────────────────────────────────────────
# Columns: Taiwan 6/11 | Korea 6/8 | Korea 6/23 | Japan 6/23
# Rows: VIX-type | Foreign selling | Index drawdown -20% | Margin/national team
events = [
    "台灣 6/11\n(底部當天)",
    "韓國 6/8\n(第一波底)",
    "韓國 6/23\n(第二波底)",
    "日本 6/23\n(連累下跌)",
]
lamps = [
    "① VIX型指數",
    "② 外資/匯率訊號",
    "③ 跌幅 -20%",
    "④ 護盤/結構燈",
]

# True = lit (亮), False = dark (暗)
# [VIX, 外資, 跌幅, 維持率]
lamp_states = [
    [True,  True,  False, False],   # Taiwan 6/11: VIXTWN 43.58, 外資-4300億, -7%, 163%
    [True,  True,  False, False],   # Korea 6/8: VKOSPI 91.23, massive selling, -8.2% single day (not -20%)
    [True,  True,  False, False],   # Korea 6/23: VKOSPI 89.41, continued selling, -11.8% from high
    [False, False, False, False],   # Japan 6/23: Nikkei VI 23.93, no data, -3.55%, BOJ gone
]

# Supplementary stats per event
stats = [
    ["VIXTWN 43.58", "賣超 4,300億", "跌幅 -7%", "維持率 163%\n(國安基金可裁量)"],
    ["VKOSPI 91.23\n史上最高", "淨流出 620億美元\n(至5月底)", "單日 -8.2%\n(非 -20%)", "放空禁令\n2025/3已恢復"],
    ["VKOSPI 89.41\n(6/24達94.28)", "持續賣超", "從高點 -11.8%\n(非 -20%)", "放空禁令\n尚未重啟"],
    ["Nikkei VI 23.93\n（正常區間）", "USD/JPY\n未見極端急跌\n(週報太慢用匯率代理)", "跌 -3.55%\n(非恐慌)", "BOJ已退場\n護盤網消失"],
]

result_text = ["V轉創新高\n（2盞就夠）", "隔天暴彈8.18%\n10天後新高", "底部未確認\nU/L型觀察", "不適用\n燈全暗勿接"]
result_col  = [GREEN, GREEN, AMBER, LGREY]

fig, ax = plt.subplots(figsize=(16, 10), facecolor=NAVY)
ax.set_facecolor(NAVY)
ax.set_xlim(-0.5, len(events) - 0.5)
ax.set_ylim(-0.5, len(lamps) + 1.5)
ax.axis('off')

# ── column headers ──
for j, ev in enumerate(events):
    ax.text(j, len(lamps) + 1.1, ev, ha='center', va='center',
            color=WHITE, fontsize=11.5, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.45', facecolor=DGREY, edgecolor=LGREY, alpha=0.9))

# ── row labels ──
for i, lamp in enumerate(lamps):
    row_y = len(lamps) - 1 - i
    ax.text(-0.48, row_y, lamp, ha='left', va='center',
            color=GOLD, fontsize=11, fontweight='bold')

# ── lamp cells ──
for i, lamp in enumerate(lamps):
    row_y = len(lamps) - 1 - i
    for j, ev in enumerate(events):
        lit = lamp_states[j][i]
        col = GREEN if lit else OFF
        edge = WHITE if lit else LGREY
        # glow ring
        if lit:
            ax.scatter([j], [row_y], s=900, color=GREEN, alpha=0.15, zorder=3)
        ax.scatter([j], [row_y], s=320, color=col, zorder=4,
                   edgecolors=edge, linewidths=1.5)
        # stat text below lamp
        ax.text(j, row_y - 0.32, stats[j][i],
                ha='center', va='top', color=WHITE if lit else LGREY,
                fontsize=7.8, linespacing=1.3)

# ── result row ──
for j in range(len(events)):
    ax.text(j, -0.1, result_text[j], ha='center', va='top',
            color=result_col[j], fontsize=9.5, fontweight='bold',
            linespacing=1.4,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=DGREY,
                      edgecolor=result_col[j], alpha=0.85))

# ── horizontal dividers ──
for i in range(len(lamps)):
    y = i + 0.5
    ax.axhline(y, color=DGREY, lw=0.8, alpha=0.5, zorder=1)

# ── lamp count row ──
count_labels = ["2 盞 🟢", "2 盞 🟢", "2 盞 🟡", "0 盞 ⚫"]
count_colors = [GREEN, GREEN, AMBER, LGREY]
for j in range(len(events)):
    lit_count = sum(lamp_states[j])
    ax.text(j, len(lamps) + 0.55, f"亮燈：{lit_count} / 4",
            ha='center', va='center', color=count_colors[j],
            fontsize=10.5, fontweight='bold')

# ── title & footer ──
fig.text(0.5, 0.965,
         '同一張儀表板，三個市場，四個時間點——亮燈數決定倉位大小',
         ha='center', color=GOLD, fontsize=12.5, fontweight='bold')
fig.text(0.5, 0.035,
         '摸魚記 · 2026年6月 · 資料：KRX、TSE、TAIFEX公開數據 · 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=8.5, alpha=0.85)

# ── legend ──
ax.scatter([3.42], [3.7], s=260, color=GREEN, zorder=5,
           edgecolors=WHITE, linewidths=1.3)
ax.text(3.47, 3.7, '亮（條件達標）', color=WHITE, fontsize=8.5, va='center')
ax.scatter([3.42], [3.25], s=260, color=OFF, zorder=5,
           edgecolors=LGREY, linewidths=1.3)
ax.text(3.47, 3.25, '暗（條件未達）', color=LGREY, fontsize=8.5, va='center')

plt.subplots_adjust(top=0.90, bottom=0.10, left=0.12, right=0.97)
out = '/home/user/KIWI/personal/drafts/W5S-chart-lamps.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

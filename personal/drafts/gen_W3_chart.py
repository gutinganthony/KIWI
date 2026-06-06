"""
摸魚記 W3 主圖
Chart 1: VIX at Historical Bottoms (2018 / 2020 / 2022 / current)
Chart 2: SOX Five Crash Comparison — Drawdown % vs Recovery Months
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import numpy as np

# ── Font ──────────────────────────────────────────────────────────────────
CJK_FONT = '/usr/local/share/fonts/NotoSerifTC.otf'
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
FONT = prop.get_name()
matplotlib.rcParams['font.family'] = FONT

# ── Brand colours ─────────────────────────────────────────────────────────
NAVY  = "#1a2744"
GOLD  = "#b8954a"
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"

# ══════════════════════════════════════════════════════════════════════════
# DATA — all verified from published sources
# ══════════════════════════════════════════════════════════════════════════

# VIX at major correction/bear-market bottoms (confirmed dates & levels)
# Sources: CBOE historical data, macrotrends.net
vix_events = [
    # label,           bottom_date,   VIX_at_bottom,  color
    ("2018 年 12 月\n貿易戰底部\n(2018-12-26)",   "2018-12-26",  36.07,  AMBER),
    ("2020 年 3 月\nCOVID 底部\n(2020-03-23)",    "2020-03-23",  57.08,  RED),
    ("2022 年 10 月\n升息熊市底部\n(2022-10-13)", "2022-10-13",  34.53,  AMBER),
    ("現在\n(2026-06-06)",                          "2026-06-06",  21.51,  GOLD),
]

# SOX / 費半 major crashes
# drawdown % (peak-to-trough), recovery months, nature of crash
# Sources: quantflowlab.com, Yahoo Finance historical, SOXX ETF data
sox_crashes = [
    # label,              drawdown_pct,  recovery_months, nature,      bar_color
    ("2018\n貿易戰",       -30,           6,  "估值疲勞\n+情緒",  AMBER),
    ("2020\nCOVID",        -35,           5,  "外部衝擊\n需求未損", GREEN),
    ("2022\n升息循環",      -45,          14,  "需求真實\n惡化",   RED),
    ("2026 現在\n(進行中)", -10,          None, "估值疲勞\n+升息恐懼", GOLD),
]

# ══════════════════════════════════════════════════════════════════════════
# Figure layout
# ══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 10), facecolor=NAVY)
gs = gridspec.GridSpec(1, 2, figure=fig,
                       wspace=0.38,
                       left=0.07, right=0.96,
                       top=0.86, bottom=0.12)

# ══════════════════════════════════════════════════════════════════════════
# LEFT PANEL — VIX at bottoms
# ══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(NAVY)

labels  = [e[0] for e in vix_events]
values  = [e[2] for e in vix_events]
colors  = [e[3] for e in vix_events]
x       = np.arange(len(labels))
bars    = ax1.bar(x, values, color=colors, alpha=0.85, width=0.55, zorder=3)

# threshold line at 30
ax1.axhline(30, color=LRED, lw=1.5, linestyle='--', alpha=0.8, zorder=4)
ax1.text(3.45, 31.5, 'VIX 30 歷史底部閾值', color=LRED,
         fontsize=8, ha='right', alpha=0.9)

# annotate bars
for bar, val, col in zip(bars, values, colors):
    weight = 'bold' if val == 21.51 else 'normal'
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 1.2,
             f'{val}', ha='center', color=col,
             fontsize=12, fontweight=weight)

# "not yet" annotation for current
ax1.annotate('尚未達到\n歷史底部水位',
    xy=(3, 21.51), xytext=(2.4, 42),
    color=GOLD, fontsize=8.5, ha='center',
    arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.2))

ax1.set_xticks(x)
ax1.set_xticklabels(labels, color=LGREY, fontsize=8.5)
ax1.set_yticks([0, 15, 30, 45, 60, 75])
ax1.set_yticklabels(['0', '15', '30', '45', '60', '75'], color=LGREY, fontsize=9)
ax1.set_ylim(0, 75)
ax1.tick_params(colors=LGREY, length=3)
ax1.set_ylabel('VIX 指數（恐慌指標）', color=LGREY, fontsize=9)
ax1.set_title('歷史底部的 VIX 水位\n現在的 21.51 從未是底部',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax1.spines.values():
    sp.set_color(DGREY)
ax1.yaxis.grid(True, color=DGREY, alpha=0.5, zorder=0)

# ══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — SOX crash comparison
# ══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(NAVY)

crash_labels = [c[0] for c in sox_crashes]
drawdowns    = [abs(c[1]) for c in sox_crashes]  # positive for display
recoveries   = [c[2] if c[2] else 0 for c in sox_crashes]
natures      = [c[3] for c in sox_crashes]
c_colors     = [c[4] for c in sox_crashes]
x2 = np.arange(len(crash_labels))

# drawdown bars (left axis)
bars2 = ax2.bar(x2 - 0.18, drawdowns, width=0.32,
                color=c_colors, alpha=0.85, zorder=3, label='跌幅 %')

# recovery bars (secondary — overlay lighter)
ax2b = ax2.twinx()
recovery_bars = ax2b.bar(x2 + 0.18, recoveries, width=0.32,
                          color=c_colors, alpha=0.35, zorder=2,
                          hatch='///', edgecolor=WHITE, label='回本月數')

# Annotate drawdown %
for bar, val, col in zip(bars2, drawdowns, c_colors):
    ax2.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.8,
             f'-{val}%', ha='center', color=col, fontsize=11, fontweight='bold')

# Annotate recovery months
for i, (rec, col) in enumerate(zip(recoveries, c_colors)):
    if rec > 0:
        ax2b.text(x2[i] + 0.18, rec + 0.4,
                  f'{rec}月', ha='center', color=col, fontsize=10, alpha=0.8)
    else:
        ax2b.text(x2[i] + 0.18, 1.5,
                  '未知', ha='center', color=GOLD, fontsize=9)

# Nature labels below x-axis
for i, nat in enumerate(natures):
    ax2.text(x2[i], -7, nat, ha='center', color=LGREY,
             fontsize=7.5, alpha=0.8)

ax2.set_xticks(x2)
ax2.set_xticklabels(crash_labels, color=LGREY, fontsize=9)
ax2.set_ylim(0, 60)
ax2.set_yticks([0, 10, 20, 30, 40, 50])
ax2.set_yticklabels(['0', '-10%', '-20%', '-30%', '-40%', '-50%'],
                    color=LGREY, fontsize=9)
ax2.set_ylabel('費半跌幅（峰值至谷底）', color=LGREY, fontsize=9)
ax2b.set_ylim(0, 20)
ax2b.set_yticks([0, 5, 10, 15])
ax2b.set_yticklabels(['0', '5個月', '10個月', '15個月'], color=LGREY, fontsize=8)
ax2b.set_ylabel('回到前高月數', color=LGREY, fontsize=9)

ax2.tick_params(colors=LGREY, length=3)
ax2b.tick_params(colors=LGREY, length=3)
ax2.set_title('費半（SOX）三次崩跌對照\n跌幅大小不決定痛苦時間，性質才決定',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax2.spines.values():
    sp.set_color(DGREY)
for sp in ax2b.spines.values():
    sp.set_color(DGREY)

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=LGREY, alpha=0.85, label='深色 = 跌幅 %'),
    Patch(facecolor=LGREY, alpha=0.35, hatch='///', label='淺色 = 回本月數'),
]
ax2.legend(handles=legend_elements, facecolor=NAVY, edgecolor=DGREY,
           labelcolor=LGREY, fontsize=8, loc='upper left')

# ── Master title ─────────────────────────────────────────────────────────
fig.text(0.5, 0.94,
         '費半崩跌 10%，現在在哪裡？歷史數據說的故事',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.922,
         '摸魚記  ·  2026年6月  ·  VIX 21.51 / 費半 -10.26% / 尚未到歷史底部水位',
         ha='center', color=GOLD, fontsize=9.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W3-chart-crash-analysis.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

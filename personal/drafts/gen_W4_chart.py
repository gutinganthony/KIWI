"""
摸魚記 W4 圖表
Left panel:  Fed 資產負債表 2008-2026 (approximated from FRED WALCL key milestones)
Right panel: 2024 降息+縮表悖論 — Fed 降 100bps，10年期殖利率反升 100bps
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import numpy as np

CJK_FONT = '/usr/local/share/fonts/NotoSerifTC.otf'
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
FONT = prop.get_name()
matplotlib.rcParams['font.family'] = FONT

NAVY  = "#1a2744"
GOLD  = "#b8954a"
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"
BLUE  = "#2980b9"
TEAL  = "#1abc9c"

fig = plt.figure(figsize=(16, 9), facecolor=NAVY)
gs = gridspec.GridSpec(1, 2, figure=fig,
                       wspace=0.42,
                       left=0.07, right=0.96,
                       top=0.86, bottom=0.16)

# ══════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Fed 資產負債表 2008-2026
# Key milestones from FRED WALCL (Total Assets, Federal Reserve):
#   Jan 2008: ~0.9T (pre-crisis)
#   Dec 2008: ~2.3T (QE1 launch)
#   Jun 2011: ~2.9T (QE2 end)
#   Dec 2012: ~2.9T (QE3 start)
#   Jan 2015: ~4.5T (QE3 end, peak)
#   Sep 2019: ~3.8T (QT reduced it)
#   Mar 2020: ~4.2T (pre-COVID)
#   Jun 2020: ~7.2T (COVID QE surge)
#   Apr 2022: ~8.9T (peak)
#   Jun 2024: ~7.3T (QT ongoing)
#   Jun 2026: ~6.7T (current estimate)
# ══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(NAVY)

# Year fractions (approximate)
years = [2008.0, 2008.9, 2010.5, 2012.0, 2013.0, 2015.0, 2017.5, 2019.75,
         2020.2, 2020.5, 2022.3, 2022.9, 2024.5, 2026.4]
assets = [0.9, 2.3, 2.7, 2.9, 3.6, 4.5, 4.5, 3.8,
          4.2, 7.2, 8.9, 8.8, 7.3, 6.7]

# Interpolate for smooth curve
from scipy.interpolate import make_interp_spline
t_fine = np.linspace(2008.0, 2026.4, 500)
spl = make_interp_spline(years, assets, k=3)
a_fine = spl(t_fine)

# Color segments: QE eras gold/green, QT eras red/teal
ax1.fill_between(t_fine, 0, a_fine, alpha=0.12, color=GOLD)
ax1.plot(t_fine, a_fine, color=GOLD, lw=2.5, zorder=5)

# Key annotations
annotations = [
    (2008.9, 2.3,  "QE1 啟動\n$2.3兆",   'up',   RED),
    (2015.0, 4.5,  "QE 高峰\n$4.5兆",    'up',   GOLD),
    (2020.5, 7.2,  "COVID\nQE 衝頂",     'up',   GREEN),
    (2022.3, 8.9,  "歷史峰值\n$8.9兆",   'up',   LRED),
    (2026.4, 6.7,  "現在\n$6.7兆",       'up',   WHITE),
]

for xp, yp, label, direction, color in annotations:
    offset = 0.35 if direction == 'up' else -0.35
    va = 'bottom' if direction == 'up' else 'top'
    ax1.annotate(label,
                 xy=(xp, yp),
                 xytext=(xp, yp + offset),
                 ha='center', va=va,
                 color=color, fontsize=8, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=color, lw=1.2),
                 zorder=8)

# Warsh arrow — direction indicator at right edge
ax1.annotate('', xy=(2026.8, 5.5), xytext=(2026.8, 6.6),
             arrowprops=dict(arrowstyle='->', color=RED, lw=2.5))
ax1.text(2026.85, 6.05, "Warsh\n方向↓", color=RED, fontsize=8.5,
         fontweight='bold', va='center', ha='left')

# QT shading band 2022-2026
ax1.axvspan(2022.3, 2026.5, alpha=0.06, color=RED, label='縮表期(QT)')

# Era labels at bottom
ax1.text(2009.5, 0.3, "QE1", color=LGREY, fontsize=8, ha='center', alpha=0.8)
ax1.text(2012.5, 0.3, "QE2/3", color=LGREY, fontsize=8, ha='center', alpha=0.8)
ax1.text(2020.9, 0.3, "COVID QE", color=LGREY, fontsize=8, ha='center', alpha=0.8)
ax1.text(2024.3, 0.3, "QT進行中", color=RED, fontsize=8, ha='center', alpha=0.9)

ax1.set_xlim(2007.5, 2027.5)
ax1.set_ylim(0, 11)
ax1.set_xticks([2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024, 2026])
ax1.set_xticklabels(['2008', '10', '12', '14', '16', '18', '20', '22', '24', '26'],
                    color=LGREY, fontsize=9)
ax1.set_yticks([0, 2, 4, 6, 8, 10])
ax1.set_yticklabels(['$0', '$2兆', '$4兆', '$6兆', '$8兆', '$10兆'],
                    color=LGREY, fontsize=9)
ax1.set_ylabel('Fed 總資產（兆美元）', color=LGREY, fontsize=9)
ax1.set_title('Fed 資產負債表 2008–2026\n從 $0.9兆 → $8.9兆 → 現在 $6.7兆，Warsh 要繼續縮',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax1.spines.values():
    sp.set_color(DGREY)
ax1.yaxis.grid(True, color=DGREY, alpha=0.4, zorder=0)
ax1.xaxis.grid(True, color=DGREY, alpha=0.2, zorder=0)

ax1.text(0.5, -0.13,
         '來源：FRED WALCL（Federal Reserve Total Assets）',
         ha='center', transform=ax1.transAxes,
         color=LGREY, fontsize=7.5, alpha=0.8)

# ══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — 2024 降息 vs 10年期殖利率背離
# Fed cut 100bps (Sep-Dec 2024), 10Y yield rose 100bps in same period
# Sept 2024: Fed funds ~5.25-5.5%, 10Y ~3.63% (low)
# Dec 2024: Fed funds ~4.25-4.5% (cut 100bps), 10Y ~4.57% (rose 94bps)
# ══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(NAVY)

months = np.array([0, 1, 2, 3])   # Sep, Oct, Nov, Dec 2024
month_labels = ['2024年\n9月', '10月', '11月', '12月']

# Fed funds effective rate upper bound (%)
fed_rate = np.array([5.50, 5.25, 5.00, 4.50])   # cut 25bp Oct, 25bp Nov, 50bp Dec
# 10-year Treasury yield (%)
yield_10y = np.array([3.63, 4.05, 4.29, 4.57])  # actual approximate monthly closes

# Scale 10Y to show on same axis — offset trick: show both on left axis
# Fed rate on left axis (blue), 10Y on right axis (red)
ax2_r = ax2.twinx()

l1, = ax2.plot(months, fed_rate, color=BLUE, lw=3, marker='o', markersize=8,
               zorder=5, label='聯邦基金利率（短端）↓ 降息100bps')
l2, = ax2_r.plot(months, yield_10y, color=RED, lw=3, marker='s', markersize=8,
                 zorder=5, label='10年期美債殖利率（長端）↑ 上升94bps')

# Shading between start and end
ax2.fill_between(months, fed_rate, fed_rate[0], alpha=0.12, color=BLUE)
ax2_r.fill_between(months, yield_10y, yield_10y[0], alpha=0.12, color=RED)

# Value labels
for i, (m, fr, y) in enumerate(zip(months, fed_rate, yield_10y)):
    ax2.text(m, fr + 0.07, f'{fr:.2f}%', color=BLUE, ha='center',
             fontsize=9, fontweight='bold', zorder=8)
    ax2_r.text(m, y - 0.13, f'{y:.2f}%', color=RED, ha='center',
               fontsize=9, fontweight='bold', zorder=8)

# Arrow annotations for direction
ax2.annotate('Fed 降了\n-100 bps ↓', xy=(3, 4.50), xytext=(2.3, 4.9),
             color=BLUE, fontsize=8.5, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.5))

ax2_r.annotate('長端反升\n+94 bps ↑', xy=(3, 4.57), xytext=(2.1, 4.25),
               color=RED, fontsize=8.5, fontweight='bold',
               arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))

# Dec 18 event marker
ax2_r.axvline(x=3, color=AMBER, lw=1.2, linestyle='--', alpha=0.7)
ax2_r.text(3.05, 4.68, "12/18\n道瓊\n-1100點", color=AMBER, fontsize=7.5,
           va='top', fontweight='bold')

# Divergence box
ax2.text(1.5, 5.5,
         '40年來首次：降息 ≠ 長端利率下降\n1980年代以來，7次降息循環\n首次降息後100天，10年期殖利率\n七次全部下降——2024例外',
         ha='center', va='center', color=WHITE, fontsize=8.5,
         bbox=dict(boxstyle='round,pad=0.5', facecolor=DGREY, edgecolor=GOLD, alpha=0.9))

ax2.set_xlim(-0.4, 3.7)
ax2.set_ylim(3.5, 6.2)
ax2_r.set_ylim(2.8, 5.5)

ax2.set_xticks(months)
ax2.set_xticklabels(month_labels, color=LGREY, fontsize=9)
ax2.set_yticks([4.0, 4.5, 5.0, 5.5])
ax2.set_yticklabels(['4.00%', '4.50%', '5.00%', '5.50%'], color=BLUE, fontsize=9)
ax2.set_ylabel('聯邦基金利率 →', color=BLUE, fontsize=9)

ax2_r.set_yticks([3.5, 4.0, 4.5, 5.0])
ax2_r.set_yticklabels(['3.50%', '4.00%', '4.50%', '5.00%'], color=RED, fontsize=9)
ax2_r.set_ylabel('← 10年期殖利率', color=RED, fontsize=9)

ax2.set_title('2024年降息悖論：Fed 降息，長端殖利率反升\n（Warsh 若加速縮表，可能把這個劇本調高一個八度）',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)

for sp in ax2.spines.values():
    sp.set_color(DGREY)
for sp in ax2_r.spines.values():
    sp.set_color(DGREY)
ax2.yaxis.grid(True, color=DGREY, alpha=0.35, zorder=0)

# Legend
lines = [l1, l2]
labs = [l.get_label() for l in lines]
ax2.legend(lines, labs, facecolor=NAVY, edgecolor=DGREY, labelcolor=LGREY,
           fontsize=8, loc='upper right')

ax2.text(0.5, -0.13,
         '來源：FRED（DFF, DGS10）；Wolf Street "10-Year Treasury Yield Rose 100 Basis Points\nsince September as the Fed Cut 100 Basis Points"',
         ha='center', transform=ax2.transAxes,
         color=LGREY, fontsize=7, alpha=0.8)

# ── Master title
fig.text(0.5, 0.94,
         '華許的兩張牌：那張 6.7 兆的表，和一個 40 年來從沒發生過的悖論',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.923,
         '摸魚記  ·  2026年6月  ·  數據來源：FRED / Wolf Street',
         ha='center', color=GOLD, fontsize=9.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W4-chart-warsh.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

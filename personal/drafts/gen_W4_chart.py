"""
摸魚記 W4 圖表 (v2)
Left panel:  Fed 資產負債表 2008-2026 (FRED WALCL key milestones, linear interp —
             no spline overshoot, peak $8.9T lands exactly on the line)
Right panel: 首次降息後100天，10年期殖利率變動 — 歷次循環 vs 2024
             Source: J.P. Morgan "Why have 10-year U.S. Treasury yields increased
             since the Fed started cutting rates?" (Jan 2025)
             1989: -20.5bp, 1995: -7.4bp, 1998: +20.5bp, 2001: +0.5bp,
             2007: -27.5bp, 2024: ~+94bp
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

fig = plt.figure(figsize=(16, 9), facecolor=NAVY)
gs = gridspec.GridSpec(1, 2, figure=fig,
                       wspace=0.38,
                       left=0.07, right=0.97,
                       top=0.85, bottom=0.16)

# ══════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Fed 資產負債表 2008-2026 (FRED WALCL milestones)
# Linear interpolation: the line passes EXACTLY through every anchor,
# so the $8.9T annotation sits precisely on the curve's true maximum.
# ══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(NAVY)

# (year, trillions) — FRED WALCL milestones
pts = [
    (2008.0,  0.9),   # pre-crisis
    (2008.7,  0.95),  # just before Lehman
    (2008.95, 2.25),  # QE1 emergency expansion
    (2009.5,  2.1),
    (2010.5,  2.3),
    (2011.5,  2.85),  # QE2
    (2012.7,  2.85),
    (2014.0,  4.0),   # QE3
    (2015.0,  4.5),   # QE3 end — plateau
    (2017.7,  4.45),  # plateau end, QT1 starts
    (2019.7,  3.76),  # QT1 trough (Sep 2019)
    (2020.15, 4.2),   # pre-COVID
    (2020.45, 7.1),   # COVID QE explosion (3 months)
    (2021.0,  7.4),
    (2022.27, 8.965), # historical peak (Apr 2022)
    (2023.0,  8.3),
    (2024.0,  7.7),
    (2025.0,  6.9),
    (2025.92, 6.6),   # QT2 ends Dec 1, 2025
    (2026.42, 6.65),  # transition: reinvesting, roughly flat
]
yrs = np.array([p[0] for p in pts])
val = np.array([p[1] for p in pts])

t_fine = np.linspace(yrs[0], yrs[-1], 800)
a_fine = np.interp(t_fine, yrs, val)

ax1.fill_between(t_fine, 0, a_fine, alpha=0.12, color=GOLD)
ax1.plot(t_fine, a_fine, color=GOLD, lw=2.5, zorder=5,
         solid_joinstyle='round')

# Key annotations — each anchored exactly on a data point
annot = [
    (2008.95, 2.25, "QE1 啟動\n$2.3兆",  0.0,  0.9, RED),
    (2015.0,  4.5,  "QE 高原\n$4.5兆",   0.0,  0.9, GOLD),
    (2019.7,  3.76, "QT1 低點\n$3.8兆",  0.0, -1.1, BLUE),
    (2022.27, 8.965,"歷史峰值\n$8.9兆",  0.0,  0.7, LRED),
    (2025.92, 6.6,  "QT 結束\n2025/12", -1.8, -1.6, AMBER),
    (2026.42, 6.65, "現在\n約$6.6兆",   -0.5,  1.3, WHITE),
]
for xp, yp, label, dx, dy, color in annot:
    ax1.annotate(label,
                 xy=(xp, yp),
                 xytext=(xp + dx, yp + dy),
                 ha='center',
                 va='bottom' if dy > 0 else 'top',
                 color=color, fontsize=8.5, fontweight='bold',
                 arrowprops=dict(arrowstyle='->', color=color, lw=1.2),
                 zorder=8)

# COVID QE label (no arrow, alongside steep segment)
ax1.text(2019.6, 6.3, "COVID QE\n3個月+$3兆", color=GREEN, fontsize=8,
         fontweight='bold', ha='right')

# Warsh direction arrow at right edge — restart QT?
ax1.annotate('', xy=(2027.0, 5.4), xytext=(2027.0, 6.5),
             arrowprops=dict(arrowstyle='->', color=RED, lw=2.5,
                             linestyle='--'))
ax1.text(2027.15, 5.95, "Warsh\n重啟\n縮表？", color=RED, fontsize=8.5,
         fontweight='bold', va='center', ha='left')

# QT2 shading band: Jun 2022 – Dec 2025 (runoff ended Dec 1, 2025)
ax1.axvspan(2022.45, 2025.92, alpha=0.06, color=RED)
# Transition band: Dec 2025 – now (reinvesting, neither QT nor QE)
ax1.axvspan(2025.92, 2026.5, alpha=0.08, color=LGREY)
ax1.text(2024.2, 0.35, "QT2\n(2022/6–2025/12)", color=RED, fontsize=7.5,
         ha='center', alpha=0.95, fontweight='bold')
ax1.text(2026.2, 0.55, "過渡期\n不縮不擴", color=WHITE, fontsize=7,
         ha='center', alpha=0.95, fontweight='bold')
ax1.text(2011.5, 0.35, "QE 時代", color=LGREY, fontsize=8.5,
         ha='center', alpha=0.85)

ax1.set_xlim(2007.5, 2028.2)
ax1.set_ylim(0, 10.6)
ax1.set_xticks([2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024, 2026])
ax1.set_xticklabels(['2008', '10', '12', '14', '16', '18', '20', '22', '24', '26'],
                    color=LGREY, fontsize=9)
ax1.set_yticks([0, 2, 4, 6, 8, 10])
ax1.set_yticklabels(['$0', '$2兆', '$4兆', '$6兆', '$8兆', '$10兆'],
                    color=LGREY, fontsize=9)
ax1.set_ylabel('Fed 總資產（兆美元）', color=LGREY, fontsize=9)
ax1.set_title('Fed 資產負債表 2008–2026\n\\$0.9兆 → 峰值 \\$8.9兆 → QT 已於 2025/12 結束，Warsh 會重啟嗎？',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax1.spines.values():
    sp.set_color(DGREY)
ax1.yaxis.grid(True, color=DGREY, alpha=0.4, zorder=0)
ax1.xaxis.grid(True, color=DGREY, alpha=0.2, zorder=0)

ax1.text(0.5, -0.13,
         '來源：FRED WALCL（Federal Reserve Total Assets, 週資料里程碑）',
         ha='center', transform=ax1.transAxes,
         color=LGREY, fontsize=7.5, alpha=0.8)

# ══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — 首次降息後 100 天，10 年期殖利率變動（bp）
# Past cycles: small moves within ±30bp. 2024: +94bp — towering red bar.
# Source: J.P. Morgan Private Bank (Jan 2025), FRED DGS10
# ══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(NAVY)

cycles  = ['1989', '1995', '1998', '2001', '2007', '2024']
chg_bp  = [-20.5,  -7.4,   20.5,   0.5,   -27.5,  94.0]
colors  = [BLUE, BLUE, BLUE, BLUE, BLUE, RED]

x = np.arange(len(cycles))
bars = ax2.bar(x, chg_bp, color=colors, alpha=0.88, width=0.55, zorder=3)

for bar, v in zip(bars, chg_bp):
    if v >= 0:
        ax2.text(bar.get_x() + bar.get_width()/2, v + 2.5,
                 f'+{v:.1f}' if v > 0 else f'{v:.1f}',
                 ha='center', color=WHITE, fontsize=10, fontweight='bold')
    else:
        ax2.text(bar.get_x() + bar.get_width()/2, v - 2.5,
                 f'{v:.1f}', ha='center', va='top',
                 color=WHITE, fontsize=10, fontweight='bold')

ax2.axhline(0, color=WHITE, lw=1.2, alpha=0.8)

# ±30bp historical band
ax2.axhspan(-30, 30, alpha=0.07, color=LGREY, zorder=1)
ax2.text(-0.45, 26, '過去每次都在 ±30bp 內', color=LGREY, fontsize=8,
         ha='left', alpha=0.95)

# 2024 callout
ax2.annotate('Fed 同期降了 100bp\n長端卻大升 94bp\n＝近四十年最大背離',
             xy=(5, 94), xytext=(3.15, 78),
             color=LRED, fontsize=9.5, fontweight='bold', ha='center',
             arrowprops=dict(arrowstyle='->', color=LRED, lw=1.5),
             bbox=dict(boxstyle='round,pad=0.4', facecolor=DGREY,
                       edgecolor=LRED, alpha=0.9))

# Stock market reaction note
ax2.text(2.5, -48,
         '股市怎麼反應？前幾次「軟著陸式降息」（1984/89/95/98），S&P 一年後 100% 上漲、平均 +18.6%\n'
         '但 2024/12/18：Fed 如期降息、卻暗示隔年少降——當天道瓊 -1,100 點、那斯達克 -3.6%\n'
         '市場交易的不是那 1 碼，是「長端殖利率去哪裡」',
         ha='center', va='center', color=WHITE, fontsize=8,
         bbox=dict(boxstyle='round,pad=0.55', facecolor=DGREY,
                   edgecolor=GOLD, alpha=0.9))

ax2.set_xticks(x)
ax2.set_xticklabels(cycles, color=LGREY, fontsize=10)
ax2.set_xlabel('降息循環（首次降息年份）', color=LGREY, fontsize=9)
ax2.set_ylim(-70, 112)
ax2.set_yticks([-30, 0, 30, 60, 90])
ax2.set_yticklabels(['-30', '0', '+30', '+60', '+90'], color=LGREY, fontsize=9)
ax2.set_ylabel('首次降息後約100天，10年期殖利率變動（基點）', color=LGREY, fontsize=9)
ax2.set_title('歷次「首次降息」之後，長端殖利率怎麼走？\n過去都乖乖的——2024 年第一次失控',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax2.spines.values():
    sp.set_color(DGREY)
ax2.yaxis.grid(True, color=DGREY, alpha=0.4, zorder=0)

ax2.text(0.5, -0.13,
         '來源：J.P. Morgan Private Bank（2025/1）；FRED DGS10；CNBC（降息後 S&P 歷史統計）',
         ha='center', transform=ax2.transAxes,
         color=LGREY, fontsize=7.5, alpha=0.8)

# ── Master title
fig.text(0.5, 0.94,
         '華許的兩張牌：那張 6.6 兆的表，和一個四十年沒見過的背離',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.922,
         '摸魚記  ·  2026年6月  ·  數據來源：FRED / J.P. Morgan / CNBC',
         ha='center', color=GOLD, fontsize=9.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W4-chart-warsh.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

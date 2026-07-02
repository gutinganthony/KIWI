"""
摸魚記 W6M 圖 A：崩的是股價，不是記憶體
左：股價跌幅（紅、向左）｜右：實體報價漲幅（綠、向右）
發散條形圖：方向＋顏色雙重編碼極性，文字用白/灰不吃色
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
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"

# 上半：股價（跌，負值）；下半：實體報價（漲，正值）
rows = [
    ("美光（7/1 單日）",          -10.57, "股價"),
    ("華邦電（7/1–7/2 兩天）",    -11.57, "股價"),
    ("南亞科（6/30–7/2 三天）",   -10.15, "股價"),
    ("DDR4 8Gb 合約價（5月下半）", 25.00, "報價"),
    ("DDR4 4Gb 合約價（5月下半）", 20.00, "報價"),
    ("DDR4 16Gb 合約價（5月下半）",19.40, "報價"),
    ("DDR4 16Gb 現貨（7/2 盤中）",  1.17, "報價"),
]

fig, ax = plt.subplots(figsize=(13, 8), facecolor=NAVY)
ax.set_facecolor(NAVY)

y = np.arange(len(rows))[::-1]
vals = [r[1] for r in rows]
cols = [LRED if v < 0 else GREEN for v in vals]

ax.barh(y, vals, height=0.62, color=cols, edgecolor=NAVY, linewidth=2)

# 中線（零軸）
ax.axvline(0, color=LGREY, lw=1.2, alpha=0.8)

for yi, (name, v, kind) in zip(y, rows):
    # 名稱：放在零軸另一側
    if v < 0:
        ax.text(0.6, yi, name, ha='left', va='center', color=WHITE, fontsize=11.5)
        ax.text(v - 0.6, yi, f'{v:+.2f}%', ha='right', va='center',
                color=WHITE, fontsize=12, fontweight='bold')
    else:
        ax.text(-0.6, yi, name, ha='right', va='center', color=WHITE, fontsize=11.5)
        ax.text(v + 0.6, yi, f'{v:+.2f}%', ha='left', va='center',
                color=WHITE, fontsize=12, fontweight='bold')

# 區塊分隔線與標題
ax.axhline(3.5, color=DGREY, lw=1.5, ls=':')
ax.text(-27, 5.9, '股票市場\n（這三天）', ha='center', va='center',
        color=LGREY, fontsize=12, fontweight='bold', linespacing=1.6)
ax.text(27, 1.9, '實體市場\n（同一時間）', ha='center', va='center',
        color=LGREY, fontsize=12, fontweight='bold', linespacing=1.6)

ax.set_xlim(-32, 33)
ax.set_ylim(-0.7, len(rows) - 0.3)
ax.set_yticks([])
ax.set_xticks([-30, -20, -10, 0, 10, 20, 30])
ax.set_xticklabels(['-30%', '-20%', '-10%', '0', '+10%', '+20%', '+30%'],
                   color=LGREY, fontsize=10)
ax.xaxis.grid(True, color=DGREY, alpha=0.35, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(False)

fig.text(0.5, 0.955, '崩的是股價，不是記憶體', ha='center',
         color=GOLD, fontsize=16, fontweight='bold')
fig.text(0.5, 0.905, '股價跳水的同一時間，DRAM 報價還在創新高（TrendForce：6 月合約價屢創新高、3Q26 續漲）',
         ha='center', color=LGREY, fontsize=10.5)
fig.text(0.5, 0.018,
         '摸魚記 · 2026/7/2 · 股價：各交易所收盤；報價：DRAMeXchange/TrendForce（合約價為 5 月下半月均價漲幅、現貨為 7/2 14:40 盤中）· 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=7.6, alpha=0.85)

plt.subplots_adjust(top=0.87, bottom=0.075, left=0.04, right=0.97)
out = '/home/user/KIWI/personal/drafts/W6M-chart-price-vs-physical.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

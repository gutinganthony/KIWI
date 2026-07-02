"""
摸魚記 W6M 圖 B：記憶體版抄底儀表板 · 五盞燈（7/2）
四綠一黃一紅 → 結構完好、籌碼過熱、時鐘剛響
燈內帶字（穩/響/燙），不靠顏色單獨傳達
下半沿用品牌「旋鈕」半圓：指針指「試單」
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Wedge, Circle
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
AMBER = "#e67e22"
OFF   = "#3a4a6b"

fig = plt.figure(figsize=(13, 10.5), facecolor=NAVY)

# ── 上半：五盞燈 ──
ax = fig.add_axes([0.03, 0.42, 0.94, 0.46])
ax.set_facecolor(NAVY)
ax.set_xlim(0, 5)
ax.set_ylim(0, 2.3)
ax.axis('off')

lamps = [
    ("① 合約價方向", GREEN, "穩", "6月屢創新高\n3Q26 續漲預期"),
    ("② HBM 長約",   GREEN, "穩", "美光 2026 售罄\n海力士鎖到 2027"),
    ("③ 供給時鐘",   AMBER, "響", "史上最大擴產已宣布\n產能 2028 後開出"),
    ("④ 需求真偽",   GREEN, "穩", "放緩未實際發生\n缺口看到 2H27"),
    ("⑤ 籌碼溫度",   LRED,  "燙", "美光今年漲逾兩倍\n一天能跌 10.57%"),
]

for j, (name, col, word, stat) in enumerate(lamps):
    cx = j + 0.5
    ax.scatter([cx], [1.52], s=2400, color=col, alpha=0.16, zorder=2)
    ax.scatter([cx], [1.52], s=1000, color=col, zorder=4,
               edgecolors=WHITE, linewidths=2.0)
    ax.text(cx, 1.52, word, ha='center', va='center',
            color=WHITE, fontsize=15, fontweight='bold', zorder=5)
    ax.text(cx, 0.90, name, ha='center', va='center',
            color=GOLD, fontsize=12.5, fontweight='bold')
    ax.text(cx, 0.38, stat, ha='center', va='center',
            color=WHITE, fontsize=9, linespacing=1.5)

ax.text(2.5, 2.16, '記憶體抄底儀表板 · 7/2 → 四穩、一響、一燙', ha='center', va='center',
        color=WHITE, fontsize=13.5, fontweight='bold')

# ── 下半：旋鈕（半圓儀表）──
axg = fig.add_axes([0.20, 0.055, 0.60, 0.32])
axg.set_facecolor(NAVY)
axg.set_xlim(-1.35, 1.35)
axg.set_ylim(-0.18, 1.18)
axg.axis('off')

zones = [
    (135, 180, "#34495e", "報價轉跌\n離場"),
    (90, 135, OFF,        "時鐘走遠\n減碼"),
    (45, 90,  GREEN,      "現在\n試單 1–2 成"),
    (0,  45,  GOLD,       "報價漲+籌碼冷\n加碼"),
]
for a0, a1, c, lab in zones:
    axg.add_patch(Wedge((0, 0), 1.0, a0, a1, width=0.34,
                        facecolor=c, edgecolor=NAVY, lw=2.5, alpha=0.92))
    amid = np.radians((a0 + a1) / 2)
    axg.text(1.18*np.cos(amid), 1.18*np.sin(amid), lab,
             ha='center', va='center', color=WHITE, fontsize=10,
             fontweight='bold', linespacing=1.3)

ang = np.radians(67.5)
axg.annotate('', xy=(0.72*np.cos(ang), 0.72*np.sin(ang)), xytext=(0, 0),
             arrowprops=dict(arrowstyle='-|>', color=WHITE, lw=4.5,
                             mutation_scale=26))
axg.add_patch(Circle((0, 0), 0.07, facecolor=WHITE, edgecolor=GOLD, lw=2, zorder=6))

axg.text(0, -0.14, '離場訊號只有兩個：合約價實際轉跌、或需求放緩被證實。跌幅不是訊號。',
         ha='center', va='center', color=GOLD, fontsize=11, fontweight='bold')

fig.text(0.5, 0.955,
         '結構完好、籌碼過熱、時鐘剛響：可以試單，不是倒車接貨',
         ha='center', color=GOLD, fontsize=14, fontweight='bold')
fig.text(0.5, 0.012,
         '摸魚記 · 2026/7/2 · 報價：DRAMeXchange/TrendForce；擴產：韓國 800 兆韓元計畫（6/29）· 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=7.8, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W6M-chart-memory-lamps.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

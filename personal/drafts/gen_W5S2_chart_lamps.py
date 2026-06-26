"""
摸魚記 W5S2 圖 B：台股抄底儀表板 · 6/26 收盤
四盞燈（2 亮 2 暗）＋ 下方「旋鈕」：亮燈數 → 倉位大小（不是 on/off 按鈕）
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
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"
OFF   = "#3a4a6b"

fig = plt.figure(figsize=(13, 10), facecolor=NAVY)

# ── 上半：四盞燈 ──
ax = fig.add_axes([0.05, 0.42, 0.90, 0.46])
ax.set_facecolor(NAVY)
ax.set_xlim(0, 4)
ax.set_ylim(0, 2.2)
ax.axis('off')

lamps = [
    ("① VIXTWN", True,  "44.27（+9.61%）\n破 40，極端恐慌"),
    ("② 外資賣超", True,  "連四天 >1,700 億\n（歷史級賣法）"),
    ("③ 跌幅 −20%", False, "才 −6.6%\n離 −20% 還很遠"),
    ("④ 融資維持率", False, "174.57%（6/25）\n正常區、沒壓力"),
]

for j, (name, lit, stat) in enumerate(lamps):
    cx = j + 0.5
    col  = GREEN if lit else OFF
    edge = WHITE if lit else LGREY
    if lit:
        ax.scatter([cx], [1.45], s=2600, color=GREEN, alpha=0.16, zorder=2)
    ax.scatter([cx], [1.45], s=1050, color=col, zorder=4,
               edgecolors=edge, linewidths=2.0)
    ax.text(cx, 1.45, "亮" if lit else "暗", ha='center', va='center',
            color=WHITE if lit else LGREY, fontsize=14, fontweight='bold', zorder=5)
    ax.text(cx, 0.82, name, ha='center', va='center',
            color=GOLD if lit else LGREY, fontsize=13, fontweight='bold')
    ax.text(cx, 0.30, stat, ha='center', va='center',
            color=WHITE if lit else LGREY, fontsize=9.5, linespacing=1.4)

ax.text(2.0, 2.08, '台股抄底儀表板 · 6/26 收盤 → 亮兩盞', ha='center', va='center',
        color=WHITE, fontsize=13.5, fontweight='bold')

# ── 下半：旋鈕（半圓儀表）──
axg = fig.add_axes([0.18, 0.06, 0.64, 0.34])
axg.set_facecolor(NAVY)
axg.set_xlim(-1.35, 1.35)
axg.set_ylim(-0.18, 1.18)
axg.axis('off')

# 四個區段：0空手 / 1不動 / 2試單 / 3-4重壓（半圓 180→0 度）
zones = [
    (135, 180, "#34495e", "0 盞\n空手"),
    (90, 135, OFF,        "1 盞\n不動"),
    (45, 90,  GREEN,      "2 盞\n試單 2–3 成"),
    (0,  45,  GOLD,       "3–4 盞\n倒車接貨"),
]
for a0, a1, c, lab in zones:
    axg.add_patch(Wedge((0, 0), 1.0, a0, a1, width=0.34,
                        facecolor=c, edgecolor=NAVY, lw=2.5, alpha=0.92))
    amid = np.radians((a0 + a1) / 2)
    axg.text(1.16*np.cos(amid), 1.16*np.sin(amid), lab,
             ha='center', va='center', color=WHITE, fontsize=10.5,
             fontweight='bold', linespacing=1.3)

# 指針指向「2 盞試單」區中心（67.5 度）
ang = np.radians(67.5)
axg.annotate('', xy=(0.72*np.cos(ang), 0.72*np.sin(ang)), xytext=(0, 0),
             arrowprops=dict(arrowstyle='-|>', color=WHITE, lw=4.5,
                             mutation_scale=26))
axg.add_patch(Circle((0, 0), 0.07, facecolor=WHITE, edgecolor=GOLD, lw=2, zorder=6))

axg.text(0, -0.13, '這是「旋鈕」，不是「開關」：亮燈數 → 倉位大小，不是進場 or 空手',
         ha='center', va='center', color=GOLD, fontsize=11.5, fontweight='bold')

fig.text(0.5, 0.955,
         '亮兩盞 → 可以試單，不是倒車接貨；而這次是「混血刀」，節奏要再放慢',
         ha='center', color=GOLD, fontsize=13.5, fontweight='bold')
fig.text(0.5, 0.012,
         '摸魚記 · 2026/6/26 盤後 · VIXTWN 為 6/26 收盤、融資維持率為 6/25（M平方，6/26 尚未公布）· 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=7.6, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W5S2-chart-lamps.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

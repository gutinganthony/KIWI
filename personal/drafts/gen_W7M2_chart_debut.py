"""
摸魚記 W7M2 圖：掛牌日記分板（JPM Daily Guide 版型）
單欄橫條：SKHY（對發行價）/ SanDisk / 美光 首日表現＋關鍵注記
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG    = "#ffffff"
INK   = "#1a1a1a"
GREY  = "#6b6b6b"
LGRID = "#d9d9d9"
GOLD  = "#b8954a"
RED   = "#b23b32"
GREEN = "#2e7d4f"

fig = plt.figure(figsize=(13, 6.8), facecolor=BG)

fig.text(0.052, 0.925, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.918, "史上最大 ADR 掛牌那天，沒有人被分走",
         color=INK, fontsize=19, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.882, 0.882],
                             transform=fig.transFigure, color=INK, lw=0.8))

ax = fig.add_axes([0.30, 0.20, 0.55, 0.56])
ax.set_facecolor(BG)
ax.set_title("7/10 掛牌日收盤表現", loc='left', color=INK,
             fontsize=12.5, fontproperties=serif_b, pad=24)
ax.text(0, 1.06, "漲跌幅（%）", transform=ax.transAxes, color=GREY, fontsize=9.5)

rows = [
    ("SKHY 對發行價 149\n（收 168.01，盤中高 177）", 12.76),
    ("SanDisk（收 1,915.92）",                            3.10),
    ("美光（收 979.30）",                                 -1.24),
]
y = np.arange(len(rows))[::-1]
vals = [v for _, v in rows]
cols = [GREEN if v >= 0 else RED for v in vals]

ax.barh(y, vals, height=0.5, color=cols, edgecolor=BG, linewidth=1.5)
ax.axvline(0, color=GREY, lw=0.8)

for yi, (name, v) in zip(y, rows):
    ax.text(-0.25 if v >= 0 else 0.25, yi, name,
            ha='right' if v >= 0 else 'left', va='center',
            color=INK, fontsize=10.5, linespacing=1.5)
    ax.text(v + (0.18 if v >= 0 else -0.18), yi, f"{v:+.2f}%",
            ha='left' if v >= 0 else 'right', va='center',
            color=cols[list(y).index(yi)], fontsize=12, fontproperties=serif_b)

ax.set_xlim(-4.2, 15.0)
ax.set_ylim(-0.6, len(rows) - 0.4)
ax.set_yticks([])
ax.set_xticks([-4, 0, 4, 8, 12])
ax.set_xticklabels(['-4', '0', '+4', '+8', '+12'], color=GREY, fontsize=9.5)
ax.xaxis.grid(True, color=LGRID, lw=0.7)
ax.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(GREY)
ax.spines['bottom'].set_linewidth(0.8)
ax.tick_params(colors=GREY, length=3)

ax.text(0.98, 0.05,
        "SKHY 首日成交 1.06 億股；美光掛牌前兩日已自 938 反彈至 991",
        transform=ax.transAxes, ha='right', color=GREY, fontsize=9.5, style='italic', va='bottom')

fig.text(0.052, 0.075,
         "資料來源：Nasdaq／Yahoo Finance（10/07/26 收盤），摸魚記整理。SKHY 最終發行價 149 美元（1.779 億份 ADS，募資約 265 億美元，史上最大 ADR；招股書指標價 158.14 經下修）。\n"
         "漲跌幅以發行價 149 為基準。過往表現並非未來業績的可靠指標。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/W7M2-chart-debut.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

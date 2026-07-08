"""
摸魚記 W7 圖：稀缺租到期（JPM Daily Guide 版型）
左欄：美光 6/30-7/7 收盤 ＋ 7/10 SKHY 掛牌垂直虛線
右欄：兩組溢價的收斂（美光/海力士 35%→20%；台積電 ADR 26%→13.7%）
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
GOLD  = "#b8954a"   # 溢價「之前」
SLATE = "#4a5d7a"   # 溢價「之後」（灰藍，非漲跌語意）
RED   = "#b23b32"

fig = plt.figure(figsize=(13, 7.6), facecolor=BG)

fig.text(0.052, 0.935, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.928, "美光收了十三年的「稀缺租」，這週五到期",
         color=INK, fontsize=19, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.895, 0.895],
                             transform=fig.transFigure, color=INK, lw=0.8))

# ══ 左欄：美光股價 ══
axL = fig.add_axes([0.075, 0.17, 0.40, 0.62])
axL.set_facecolor(BG)
axL.set_title("美光股價：替代品上架前", loc='left', color=INK,
              fontsize=12.5, fontproperties=serif_b, pad=26)
axL.text(0, 1.045, "收盤價（美元）", transform=axL.transAxes, color=GREY, fontsize=9.5)

# x 依交易日等距排：6/30,7/1,7/2,7/6,7/7 → 0..4；7/10 在 x=6（中間隔 7/8,7/9 兩個交易日）
x = [0, 1, 2, 3, 4]
mu = [1154.29, 1032.28, 975.56, 984.75, 938.38]
axL.plot(x, mu, color=RED, lw=2.0, marker='o', markersize=6,
         markerfacecolor=RED, markeredgecolor=BG, markeredgewidth=1.2, zorder=5)

axL.axvline(6, color=INK, lw=1.0, ls=(0, (4, 3)))
axL.text(5.85, 1120, "7/10\nSKHY 掛牌", ha='right', va='top', color=INK,
         fontsize=9.5, linespacing=1.5)

axL.text(0, 1154.29 + 22, "1,154.29", ha='center', color=GREY, fontsize=9.5)
axL.text(4.15, 938.38 - 16, "938.38", ha='left', color=RED,
         fontsize=10.5, fontproperties=serif_b)
axL.text(2.0, 1105, "四個交易日 -18.7%\n距高點約 -22%", ha='center', color=RED,
         fontsize=9.5, linespacing=1.6)

axL.set_xlim(-0.4, 6.6)
axL.set_ylim(880, 1200)
axL.set_xticks([0, 1, 2, 3, 4, 6])
axL.set_xticklabels(['6/30', '7/1', '7/2', '7/6', '7/7', '7/10'],
                    color=GREY, fontsize=9.5)
axL.set_yticks([900, 1000, 1100, 1200])
axL.set_yticklabels(['900', '1,000', '1,100', '1,200'], color=GREY, fontsize=9.5)
axL.yaxis.grid(True, color=LGRID, lw=0.7)
axL.set_axisbelow(True)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axL.spines[s].set_color(GREY)
    axL.spines[s].set_linewidth(0.8)
axL.tick_params(colors=GREY, length=3)

# ══ 右欄：兩組溢價的收斂 ══
axR = fig.add_axes([0.565, 0.17, 0.40, 0.62])
axR.set_facecolor(BG)
axR.set_title("兩種「買不到別的」溢價，都在收斂", loc='left', color=INK,
              fontsize=12.5, fontproperties=serif_b, pad=26)
axR.text(0, 1.045, "溢價（%）", transform=axR.transAxes, color=GREY, fontsize=9.5)

# 分組柱狀：組1 美光 vs 海力士；組2 台積電 ADR vs 2330
groups = [
    ("美光 vs 海力士\n（HSBC）", 35.0, "13 年平均", 20.0, "ADR 掛牌後假設"),
    ("台積電 ADR vs 2330", 26.0, "2025/12", 13.7, "2026/5"),
]
xg = np.array([0, 1.6])
w = 0.42
before = [g[1] for g in groups]
after  = [g[3] for g in groups]

b1 = axR.bar(xg - w/2 - 0.03, before, width=w, color=GOLD, edgecolor=BG, linewidth=1.5)
b2 = axR.bar(xg + w/2 + 0.03, after,  width=w, color=SLATE, edgecolor=BG, linewidth=1.5)

for xi, (name, v1, l1, v2, l2) in zip(xg, groups):
    axR.text(xi - w/2 - 0.03, v1 + 1.0, f"+{v1:g}%", ha='center', color=INK,
             fontsize=10.5, fontproperties=serif_b)
    axR.text(xi - w/2 - 0.03, v1 + 4.6, l1, ha='center', color=GREY, fontsize=8.5)
    axR.text(xi + w/2 + 0.03, v2 + 1.0, f"+{v2:g}%", ha='center', color=INK,
             fontsize=10.5, fontproperties=serif_b)
    axR.text(xi + w/2 + 0.03, v2 + 4.6, l2, ha='center', color=GREY, fontsize=8.5)
    axR.text(xi, -4.5, name, ha='center', va='top', color=INK,
             fontsize=10, linespacing=1.5)

axR.axhline(0, color=GREY, lw=0.8)
axR.set_xlim(-0.75, 2.35)
axR.set_ylim(0, 46)
axR.set_xticks([])
axR.set_yticks([0, 10, 20, 30, 40])
axR.set_yticklabels(['0', '+10', '+20', '+30', '+40'], color=GREY, fontsize=9.5)
axR.yaxis.grid(True, color=LGRID, lw=0.7)
axR.set_axisbelow(True)
for s in ('top', 'right'):
    axR.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axR.spines[s].set_color(GREY)
    axR.spines[s].set_linewidth(0.8)
axR.tick_params(colors=GREY, length=3)

fig.text(0.052, 0.075,
         "資料來源：Nasdaq，HSBC（via CNBC 26/06/26），GuruFocus，SEC F-1/A，摸魚記整理。\n"
         "美光 7/7 收盤 938.38；SKHY 參考價 242,500 韓元／ADR（以 7/3 首爾收盤為基準），暫定 7/10 掛牌，規模約 290 億美元（史上最大 ADR）。\n"
         "反映截至 07/07/26 的最新數據。過往表現並非當前及未來業績的可靠指標。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/W7-chart-scarcity.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

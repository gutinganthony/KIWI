"""
摸魚記 長端與 AI 融資篇 圖：兩股力量把長端推上去，錢在 AI 內部重新排序
上左：十年期殖利率四個時點的階梯（含 8 月寫的 4.75% 分界線）
上右：hyperscaler 發債，實績三根＋預估兩根
下：台股五個交易日的分岔，依「現金流離現在多遠」分色
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LGRID = "#dcdcdc"
GOLD = "#b8954a"; RED = "#b23b32"; SLATE = "#4a5d7a"

FW, FH = 15.6, 11.2
fig = plt.figure(figsize=(FW, FH), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.05, 0.958, "■", color=GOLD, fontsize=17)
fig.text(0.077, 0.950, "錢變貴了，所以錢變挑剔了",
         color=INK, fontsize=28, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.05, 0.96], [0.925, 0.925],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.077, 0.901, "長端衝上十九年新高，而錢已經在 AI 內部重新排序",
         color=GREY, fontsize=15)

# ══════════ 上左：十年期殖利率階梯 ══════════
axL = fig.add_axes([0.05, 0.545, 0.41, 0.305])
axL.set_facecolor(BG)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axL.spines[s].set_color(LGRID)
axL.tick_params(axis='both', length=0, labelsize=12, colors=GREY)

fig.text(0.05, 0.872, "十年期公債殖利率", color=INK,
         fontsize=16, fontproperties=serif_b)

pts = [("9/2", 4.79), ("9/15", 5.041), ("9/25", 5.23), ("9/28", 5.25)]
xs = list(range(len(pts)))
ys = [v for _, v in pts]

axL.step(xs, ys, where='post', color=SLATE, lw=2.6, zorder=3)
axL.plot(xs, ys, 'o', color=SLATE, ms=9, zorder=4)
axL.axhline(4.75, color=GOLD, lw=1.5, ls=(0, (5, 3)), zorder=2)
axL.text(3.42, 4.722, "4.75%　八月那篇寫的分界線", color=GOLD,
         fontsize=11.5, ha='right', va='top')

for i, (lab, v) in enumerate(pts):
    txt = "5.04%" if v == 5.041 else "%.2f%%" % v
    if i == 0:
        axL.text(i + 0.10, v + 0.030, txt, color=INK, fontsize=14,
                 fontproperties=serif_b, ha='left', va='bottom')
    else:
        axL.text(i, v + 0.030, txt, color=INK, fontsize=14,
                 fontproperties=serif_b, ha='center', va='bottom')

axL.set_xticks(xs)
axL.set_xticklabels([l for l, _ in pts])
axL.set_xlim(-0.25, 3.45)
axL.set_ylim(4.66, 5.40)
axL.set_yticks([4.8, 5.0, 5.2])
axL.set_yticklabels(["4.8%", "5.0%", "5.2%"])
axL.grid(axis='y', color=LGRID, lw=0.6, zorder=0)

fig.text(0.05, 0.476, "2007 年以來最高。下次 FOMC（10/27–28）升息機率 72.3%",
         color=INK, fontsize=12.5, fontproperties=serif_b)

# ══════════ 上右：hyperscaler 發債 ══════════
axR = fig.add_axes([0.545, 0.545, 0.415, 0.305])
axR.set_facecolor(BG)
for s in ('top', 'right'):
    axR.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axR.spines[s].set_color(LGRID)
axR.tick_params(axis='both', length=0, labelsize=11.5, colors=GREY)

fig.text(0.545, 0.872, "五大業者發債金額（億美元）", color=INK,
         fontsize=16, fontproperties=serif_b)

bars = [
    ("2020–24\n年均", 280, False),
    ("2025\n全年", 1210, False),
    ("2026\n上半年", 1940, False),
    ("2026 全年\n高盛估", 2500, True),
    ("2027\n高盛估", 4000, True),
]
for i, (lab, v, est) in enumerate(bars):
    axR.bar(i, v, width=0.56, color=GOLD if not est else BG,
            edgecolor=GOLD, lw=1.8, alpha=1.0 if not est else 1.0,
            hatch=None if not est else '///', zorder=3)
    axR.text(i, v + 105, "{:,}".format(v), color=INK, fontsize=13.5,
             fontproperties=serif_b, ha='center')

axR.set_xticks(range(len(bars)))
axR.set_xticklabels([l for l, _, _ in bars], linespacing=1.6)
axR.set_yticks([])
axR.set_ylim(0, 4750)
axR.grid(axis='y', color=LGRID, lw=0.6, zorder=0)
axR.add_patch(mpatches.Rectangle((2.5, 0), 2.45, 4750, facecolor=GREY,
                                 alpha=0.05, zorder=0))
axR.text(3.72, 4580, "斜線為預估", color=GREY, fontsize=11.5, ha='center')

fig.text(0.545, 0.476, "2027 年預估中，超過三分之一的資本支出是借來的",
         color=INK, fontsize=12.5, fontproperties=serif_b)

# ══════════ 下：台股五日分岔 ══════════
fig.text(0.05, 0.436, "同一週，同一條 AI 供應鏈",
         color=INK, fontsize=16, fontproperties=serif_b)
fig.text(0.05, 0.412, "2026/9/18 到 9/24，五個交易日的漲跌幅",
         color=GREY, fontsize=12.5)

axB = fig.add_axes([0.05, 0.135, 0.91, 0.258])
axB.set_facecolor(BG)
axB.axis('off')
axB.set_xlim(-14.0, 31.0)
axB.set_ylim(-0.9, 6.0)

rows = [
    ("創意", 19.2, GOLD),
    ("聯發科", 12.2, GOLD),
    ("加權指數", 1.8, GREY),
    ("台積電", 0.6, GREY),
    ("南亞科", -4.2, SLATE),
    ("華邦電", -4.5, SLATE),
]
NAME_X = -8.6          # 股名右切齊的位置，在最長的負值長條左邊
TOP_Y, STEP, BH = 5.2, 0.95, 0.56


def row_y(i):
    return TOP_Y - i * STEP


axB.plot([0, 0], [-0.55, 5.72], color=INK, lw=1.0, zorder=4)
for v in (-5, 5, 10, 15, 20):
    axB.plot([v, v], [-0.55, 5.72], color=LGRID, lw=0.6, zorder=0)
    axB.text(v, -0.78, "%+d%%" % v, color=GREY, fontsize=11,
             ha='center', va='center')

for i, (name, v, c) in enumerate(rows):
    y = row_y(i)
    axB.add_patch(mpatches.Rectangle((min(0, v), y - BH / 2), abs(v), BH,
                                     facecolor=c, zorder=3))
    axB.text(NAME_X, y, name, color=INK, fontsize=15,
             fontproperties=serif_b, ha='right', va='center')
    off = 0.55 if v > 0 else -0.55
    axB.text(v + off, y, "%+.1f%%" % v, color=c, fontsize=15,
             fontproperties=serif_b,
             ha='left' if v > 0 else 'right', va='center')

# ── 右側分組括號：依現金流離現在多遠 ──
BR_X = 22.8
for lo, hi, c, note in ((0, 1, GOLD, "現金流在兩三個月內"),
                        (4, 5, SLATE, "現金流在 2027 年之後")):
    y_hi, y_lo = row_y(lo), row_y(hi)
    axB.plot([BR_X, BR_X], [y_lo - 0.16, y_hi + 0.16], color=c, lw=1.6,
             zorder=3)
    for yy in (y_lo - 0.16, y_hi + 0.16):
        axB.plot([BR_X, BR_X + 0.45], [yy, yy], color=c, lw=1.6, zorder=3)
    axB.text(BR_X + 1.1, (y_lo + y_hi) / 2, note, color=c, fontsize=13,
             fontproperties=serif_b, ha='left', va='center')

# ══════════ 底部 ══════════
fig.lines.append(plt.Line2D([0.05, 0.96], [0.108, 0.108],
                            transform=fig.transFigure, color=LGRID, lw=0.9))
fig.text(0.05, 0.078, "折現率往上走的時候，遠的那一塊會先被檢查。",
         color=INK, fontsize=17, fontproperties=serif_b)
fig.text(0.05, 0.048,
         "資料來源：殖利率為媒體報導彙整（9/28 各家在 5.21%–5.25% 之間，取報導最多者）；發債 2020–24 與 2025 年為五家美國公司債統計，2026 上半年起為高盛投資等級債口徑與預估；\n"
         "台股為 FinMind 收盤價計算，區間 2026/9/18 至 9/24。長端上升同時受能源與通膨影響，AI 借款為其中一部分而非全部。本圖為摸魚記自行整理，不構成投資建議。",
         color=GREY, fontsize=10, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/COST-chart-two-forces.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print('Done -> ' + out)

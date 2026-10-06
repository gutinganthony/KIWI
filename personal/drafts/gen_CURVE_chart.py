"""
摸魚記 殖利率曲線篇 圖：升息被延期，長端被往上推
上：9/21 → 10/2 兩週殖利率變化（2Y／10Y／30Y），短端與長端分色
左下：非農當天先跌再翻上來（相對前一日收盤的基點變化）
右下：十月與十二月升息機率，升息是延期不是取消
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線）
資料：FinMind GovernmentBondsYield 收盤序列；盤中值與升息機率為媒體報導
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

fig = plt.figure(figsize=(15.6, 11.4), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.05, 0.958, "■", color=GOLD, fontsize=17)
fig.text(0.077, 0.950, "同一份報告，兩個市場讀出相反的事",
         color=INK, fontsize=28, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.05, 0.96], [0.925, 0.925],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.077, 0.901, "升息被延期，長端被往上推", color=GREY, fontsize=15)

# ══════════ 上：兩週殖利率變化 ══════════
fig.text(0.05, 0.858, "兩週內，長端漲的幅度是短端的四倍多", color=INK,
         fontsize=16.5, fontproperties=serif_b)
fig.text(0.05, 0.834, "美國公債殖利率，2026/9/21 至 10/2 收盤變化（基點）",
         color=GREY, fontsize=12.5)

axT = fig.add_axes([0.05, 0.545, 0.91, 0.265])
axT.set_facecolor(BG)
axT.axis('off')
axT.set_xlim(-0.6, 9.0)
axT.set_ylim(-8, 46)

tenors = [("二年期", 7, SLATE, "4.76% → 4.83%"),
          ("十年期", 32, RED, "4.96% → 5.28%"),
          ("三十年期", 34, RED, "5.29% → 5.63%")]
BW = 0.95
for i, (lab, bp, c, path) in enumerate(tenors):
    x = i * 1.75
    axT.add_patch(mpatches.Rectangle((x - BW / 2, 0), BW, bp,
                                     facecolor=c, zorder=3))
    axT.text(x, bp + 1.6, "+%d" % bp, color=c, fontsize=24,
             fontproperties=serif_b, ha='center', va='bottom')
    axT.text(x, -2.6, lab, color=INK, fontsize=14.5,
             fontproperties=serif_b, ha='center', va='top')
    axT.text(x, -6.4, path, color=GREY, fontsize=11.5,
             ha='center', va='top')
axT.plot([-0.6, 4.4], [0, 0], color=INK, lw=1.0, zorder=4)

# 右側說文解字：兩塊
BX = 5.15
axT.text(BX, 41.5, "長天期殖利率＝兩塊加起來", color=INK, fontsize=15,
         fontproperties=serif_b, va='center')
blocks = [
    (SLATE, "第一塊", "未來幾次會議的利率預期",
     "聯準會管得到。升息是延期不是取消，所以這塊沒怎麼動"),
    (RED, "第二塊", "長期通膨預期＋持有長債要求的補償",
     "聯準會下一次會議管不到。油價與發債供給都在推它"),
]
for k, (c, tag, what, note) in enumerate(blocks):
    y = 30.0 - k * 16.5
    axT.add_patch(mpatches.Rectangle((BX, y - 6.6), 0.11, 13.2,
                                     color=c, zorder=3))
    axT.text(BX + 0.32, y + 3.9, tag, color=c, fontsize=14.5,
             fontproperties=serif_b, va='center')
    axT.text(BX + 1.30, y + 3.9, what, color=INK, fontsize=13,
             va='center')
    axT.text(BX + 0.32, y - 2.6, note, color=GREY, fontsize=11.5,
             va='center')

# ══════════ 左下：非農當天的翻轉 ══════════
fig.text(0.05, 0.468, "非農當天：先跌，再翻上來", color=INK,
         fontsize=16.5, fontproperties=serif_b)
fig.text(0.05, 0.444, "相對 10/1 收盤的變化（基點）。九月非農僅增 2.9 萬，預期 8.4 萬",
         color=GREY, fontsize=12)

axL = fig.add_axes([0.05, 0.150, 0.40, 0.255])
axL.set_facecolor(BG)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axL.spines[s].set_color(LGRID)
axL.tick_params(axis='both', length=0, labelsize=12, colors=GREY)

xs = [0, 1, 2]
paths = [("十年期", [0, -6, 4], RED), ("二年期", [0, -6, 5], SLATE)]
axL.axhline(0, color=INK, lw=0.9, zorder=2)
for name, ys, c in paths:
    axL.plot(xs, ys, color=c, lw=2.6, zorder=3, marker='o', ms=9)
axL.text(2.08, 5.3, "二年期 +5", color=SLATE, fontsize=13.5,
         fontproperties=serif_b, va='center')
axL.text(2.08, 3.4, "十年期 +4", color=RED, fontsize=13.5,
         fontproperties=serif_b, va='center')
axL.text(1, -7.2, "兩條都約 −6", color=GREY, fontsize=12.5,
         ha='center', va='top')
axL.set_xticks(xs)
axL.set_xticklabels(["前一日收盤", "公布後盤中", "當日收盤"])
axL.set_xlim(-0.25, 2.75)
axL.set_ylim(-10, 8)
axL.set_yticks([-6, 0, 4])
axL.set_yticklabels(["−6", "0", "+4"])
axL.grid(axis='y', color=LGRID, lw=0.6, zorder=0)

# ══════════ 右下：升息機率 ══════════
fig.text(0.545, 0.468, "升息沒有取消，是延期", color=INK,
         fontsize=16.5, fontproperties=serif_b)
fig.text(0.545, 0.444, "CME FedWatch，各場 FOMC 升息一碼的機率",
         color=GREY, fontsize=12)

axR = fig.add_axes([0.545, 0.150, 0.415, 0.255])
axR.set_facecolor(BG)
axR.axis('off')
axR.set_xlim(-30, 108)
axR.set_ylim(0, 10)

for v in (0, 25, 50, 75, 100):
    axR.plot([v, v], [1.2, 9.3], color=LGRID, lw=0.6, zorder=0)
    axR.text(v, 0.55, "%d%%" % v, color=GREY, fontsize=11,
             ha='center', va='center')

BH = 1.55
# 十月：前後對照
yO = 6.9
axR.text(-3, yO, "十月會議", color=INK, fontsize=14.5,
         fontproperties=serif_b, ha='right', va='center')
axR.add_patch(mpatches.Rectangle((0, yO - BH / 2), 70, BH, facecolor=BG,
                                 edgecolor=GREY, lw=1.4, ls=(0, (4, 3)),
                                 zorder=2))
axR.add_patch(mpatches.Rectangle((0, yO - BH / 2), 20, BH, facecolor=SLATE,
                                 zorder=3))
axR.text(71.5, yO + 0.05, "非農前約七成", color=GREY, fontsize=12,
         va='center')
axR.text(21.5, yO + 0.05, "非農後兩成上下", color=SLATE, fontsize=13,
         fontproperties=serif_b, va='center')

# 十二月
yD = 3.3
axR.text(-3, yD, "十二月會議", color=INK, fontsize=14.5,
         fontproperties=serif_b, ha='right', va='center')
axR.add_patch(mpatches.Rectangle((0, yD - BH / 2), 75, BH, facecolor=RED,
                                 zorder=3))
axR.text(76.5, yD + 0.05, "仍在七成五以上", color=RED, fontsize=13,
         fontproperties=serif_b, va='center')

axR.annotate("", xy=(60, yD + BH / 2 + 0.25), xytext=(45, yO - BH / 2 - 0.25),
             arrowprops=dict(arrowstyle='-|>', color=GOLD, lw=2.0,
                             connectionstyle="arc3,rad=-0.25"))
axR.text(33, 5.1, "往後挪一場", color=GOLD, fontsize=12.5,
         fontproperties=serif_b, ha='right', va='center')

# ══════════ 底部 ══════════
fig.lines.append(plt.Line2D([0.05, 0.96], [0.112, 0.112],
                            transform=fig.transFigure, color=LGRID, lw=0.9))
fig.text(0.05, 0.078, "看到升息機率變了，先看長端有沒有跟著動。",
         color=INK, fontsize=17, fontproperties=serif_b)
fig.text(0.05, 0.048,
         "資料來源：殖利率收盤為 FinMind 美國公債殖利率序列；非農當天盤中低點與升息機率為媒體報導彙整（CME FedWatch，非農後各家 17%–22%）。\n"
         "長天期殖利率的兩塊拆解為概念示意，期限溢價無法直接觀察。本圖為摸魚記自行整理，不構成投資建議。",
         color=GREY, fontsize=10, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/CURVE-chart-two-halves.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print('Done -> ' + out)

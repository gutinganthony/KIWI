"""
摸魚記 退休規劃篇 圖：健康窗口 ＋ 三個口袋 ＋ 四人物對照 ＋ 房租資本化
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線輕格線）
沿用放大字級
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

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LGRID = "#d9d9d9"
GOLD = "#b8954a"; RED = "#b23b32"; GREEN = "#2e7d4f"; SLATE = "#4a5d7a"

fig = plt.figure(figsize=(15.6, 12.8), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.045, 0.966, "■", color=GOLD, fontsize=17)
fig.text(0.071, 0.958, "四個口袋，只有一個歸零",
         color=INK, fontsize=26, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.045, 0.965], [0.942, 0.942],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.071, 0.922, "死前歸零的問題不在歸零，在哪一袋歸零",
         color=GREY, fontsize=14.5)

# ══════════ 全寬：健康窗口時間軸 ══════════
axT = fig.add_axes([0.045, 0.762, 0.920, 0.128])
axT.set_facecolor(BG); axT.axis('off')
axT.set_xlim(0, 112); axT.set_ylim(0, 10)

axT.text(0, 9.5, "一條線：健康平均餘命 71.4 歲，平均壽命 80.77 歲",
         color=INK, fontsize=15.5, fontproperties=serif_b, va='center')

BAR_Y, BAR_H = 4.6, 1.7
axT.add_patch(mpatches.Rectangle((0, BAR_Y), 65, BAR_H,
                                 facecolor=SLATE, alpha=0.20, zorder=2))
axT.add_patch(mpatches.Rectangle((65, BAR_Y), 6.4, BAR_H,
                                 facecolor=GOLD, zorder=3))
axT.add_patch(mpatches.Rectangle((71.4, BAR_Y), 9.37, BAR_H,
                                 facecolor=RED, alpha=0.75, zorder=3))

axT.text(32.5, BAR_Y + BAR_H / 2, "工作與累積期", color=INK,
         fontsize=13, fontproperties=serif_b, va='center', ha='center')
axT.text(68.2, BAR_Y + BAR_H + 1.15, "退休後的健康期", color=GOLD,
         fontsize=12.5, fontproperties=serif_b, va='center', ha='center')
axT.annotate("", xy=(68.2, BAR_Y + BAR_H + 0.15),
             xytext=(68.2, BAR_Y + BAR_H + 0.85),
             arrowprops=dict(arrowstyle='-|>', color=GOLD, lw=1.6))
axT.text(76.1, BAR_Y + BAR_H / 2, "不健康 9.4 年", color='#ffffff',
         fontsize=10, fontproperties=serif_b, va='center', ha='center')

for x, lab in ((0, "0 歲"), (65, "65 退休"), (71.4, "71.4"), (80.77, "80.77")):
    axT.plot([x, x], [BAR_Y - 0.5, BAR_Y], color=GREY, lw=0.9, zorder=4)
    axT.text(x, BAR_Y - 1.25, lab, color=GREY, fontsize=11.5,
             va='center', ha='center')

axT.text(84.0, BAR_Y + BAR_H / 2 + 0.55, "6.4 年", color=GOLD,
         fontsize=25, fontproperties=serif_b, va='center')
axT.text(84.0, BAR_Y + BAR_H / 2 - 0.95, "65 歲退休的人，健康期只剩這麼長",
         color=GREY, fontsize=11, va='center')

axT.text(0, 1.35, "用四十年，換六年。", color=INK,
         fontsize=14, fontproperties=serif_b, va='center')
axT.text(14.5, 1.35, "所以問題不是「夠不夠」，是「什麼時候開始花」。",
         color=GREY, fontsize=12.5, va='center')

# ══════════ 左欄：三個口袋 ══════════
axL = fig.add_axes([0.045, 0.098, 0.305, 0.625])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.72, "每一袋的處理原則", color=INK,
         fontsize=15.5, fontproperties=serif_b, va='center')

pockets = [
    ("④ 體驗", GOLD, 2.55, "這一袋刻意歸零",
     ["按時間桶分配", "而且前重後輕"]),
    ("③ 傳承", SLATE, 1.85, "現在就決定金額與時間",
     ["提前給，不要等死後"]),
    ("② 長照", RED, 1.85, "鎖起來",
     ["保險或自住房", "可換掉資本佔用"]),
    ("① 地板", "#2f3d52", 2.35, "永遠不動",
     ["勞保＋勞退＋年金", "對抗長壽風險"]),
]
top = 9.05
for name, c, h, rule, notes in pockets:
    bot = top - h
    axL.add_patch(mpatches.Rectangle((0, bot + 0.10), 10, h - 0.20,
                                     facecolor=c, alpha=0.10, zorder=0))
    axL.add_patch(mpatches.Rectangle((0, bot + 0.10), 0.18, h - 0.20,
                                     color=c, zorder=3))
    axL.text(0.52, top - 0.52, name, color=c, fontsize=15,
             fontproperties=serif_b, va='center')
    axL.text(3.15, top - 0.52, rule, color=c, fontsize=12,
             fontproperties=serif_b, va='center')
    for j, n in enumerate(notes):
        axL.text(0.52, top - 1.05 - j * 0.42, n, color=INK,
                 fontsize=11.5, va='center')
    top = bot

axL.annotate("", xy=(9.35, 6.75), xytext=(9.35, 8.75),
             arrowprops=dict(arrowstyle='-|>', color=GOLD, lw=2.4))

axL.text(0, 0.42, "先關最容易關的那一袋：長照",
         color=INK, fontsize=12.5, fontproperties=serif_b, va='center')

# ══════════ 右上：四人物對照 ══════════
axR = fig.add_axes([0.395, 0.398, 0.570, 0.325])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 100); axR.set_ylim(0, 10)

axR.text(0, 9.72, "四個人物，對號入座", color=INK,
         fontsize=15.5, fontproperties=serif_b, va='center')
axR.text(100, 9.72, "48 歲、65 歲退休、勞保打八折的壓力情境",
         color=GREY, fontsize=11, va='center', ha='right')

cols = [
    ("A 單身\n有房", 40.5, SLATE), ("B 單身\n無房", 58.5, SLATE),
    ("C 有小孩\n有房", 76.5, SLATE), ("D 有小孩\n無房", 94.5, RED),
]
rows = [
    ("可投資資產", ["1,200 萬", "1,500 萬", "900 萬", "1,000 萬"], False),
    ("月基本開銷", ["4 萬", "6 萬（含租）", "4 萬", "6 萬（含租）"], False),
    ("① 地板", ["240 萬", "926 萬", "240 萬", "926 萬"], False),
    ("② 長照", ["180 萬", "360 萬", "180 萬", "360 萬"], False),
    ("③ 傳承", ["0", "0", "300 萬", "300 萬"], False),
    ("④ 體驗層", ["780 萬", "214 萬", "180 萬", "−586 萬"], True),
    ("前十年每年可花", ["39 萬", "10.7 萬", "9 萬", "算不出來"], True),
]

for lab, x, c in cols:
    axR.text(x, 8.55, lab, color=c, fontsize=12.3, fontproperties=serif_b,
             va='center', ha='center', linespacing=1.5)

axR.plot([0, 100], [7.62, 7.62], color=INK, lw=0.9)

for i, (label, vals, hi) in enumerate(rows):
    y = 7.05 - i * 1.02
    if hi:
        axR.add_patch(mpatches.Rectangle((0, y - 0.44), 100, 0.88,
                                         facecolor=GOLD, alpha=0.10, zorder=0))
    fp = serif_b if hi else None
    axR.text(0, y, label, color=INK, fontsize=12 if hi else 11.5,
             fontproperties=serif_b if hi else sans, va='center')
    for j, (v, (_, x, _)) in enumerate(zip(vals, cols)):
        col = RED if (j == 3 and hi) else INK
        axR.text(x, y, v, color=col, fontsize=12.3 if hi else 11.5,
                 fontproperties=serif_b if hi else sans,
                 va='center', ha='center')

axR.text(0, 0.30, "資產金額為對比用的情境設定，不是統計數據",
         color=GREY, fontsize=10.5, va='center')

# ══════════ 右下：房租的資本化價格 ══════════
axB = fig.add_axes([0.395, 0.098, 0.570, 0.252])
axB.set_facecolor(BG); axB.axis('off')
axB.set_xlim(0, 100); axB.set_ylim(0, 10)

axB.text(0, 9.35, "最反直覺的一格：房租進地板，不進體驗", color=INK,
         fontsize=15.5, fontproperties=serif_b, va='center')
axB.text(0, 7.85, "B 的資產比 A 多 300 萬，體驗層卻少 566 萬。房租是一輩子的支出。",
         color=INK, fontsize=12.3, va='center')

axB.add_patch(mpatches.Rectangle((0, 5.55), 100, 1.55,
                                 facecolor=GOLD, alpha=0.12, zorder=0))
axB.text(1.2, 6.32, "退休後每月房租 × 12 ÷ 3.5%  ＝  你要準備的資本",
         color=INK, fontsize=13.5, fontproperties=serif_b, va='center')

rents = [("月租 1.5 萬", "514 萬", GREY), ("月租 2 萬", "686 萬", GOLD),
         ("月租 2.5 萬", "857 萬", GREY), ("月租 3 萬", "1,029 萬", RED)]
for i, (r, cap, c) in enumerate(rents):
    x = i * 25.2
    axB.text(x, 4.25, r, color=GREY, fontsize=11.5, va='center')
    axB.text(x, 2.75, cap, color=c, fontsize=21,
             fontproperties=serif_b, va='center')

axB.text(0, 0.85, "這才是「買不買房」在退休規劃上的真實價格",
         color=INK, fontsize=12.5, fontproperties=serif_b, va='center')

fig.text(0.045, 0.060,
         "資料來源：內政部（113 年平均壽命 80.77 歲）、衛福部（健康平均餘命 71.4 歲、住宿式機構補助）、勞動部（勞保年金公式、勞退試算）、Morningstar\n"
         "2026 State of Retirement Income、Bill Perkins《Die With Zero》，摸魚記整理。地板提領率採 3.5%；勞退月領含自訂報酬率假設，非官方數字。四個人物的資產與開銷為情境設定，非統計平均。",
         color=GREY, fontsize=9.6, linespacing=1.85, va='top')

out = '/home/user/KIWI/personal/drafts/RETIRE-chart-three-pockets.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print(f'Done -> {out}')

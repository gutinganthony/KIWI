"""
摸魚記 中國記憶體禁令篇 圖：兩種劇本的供需推演 ＋ SanDisk 十二天目標價來回
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線輕格線）
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

fig = plt.figure(figsize=(13.6, 8.4), facecolor=BG)

fig.text(0.046, 0.945, "■", color=GOLD, fontsize=13)
fig.text(0.068, 0.938, "禁或不禁，記憶體都不會變便宜",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.046, 0.968], [0.906, 0.906],
                            transform=fig.transFigure, color=INK, lw=0.8))

# ══════════ 左欄：兩種劇本 ══════════
axL = fig.add_axes([0.046, 0.115, 0.425, 0.775])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.62, "兩種劇本，各自的意思", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

# 中國記憶體份量（上方小卡）
axL.add_patch(mpatches.Rectangle((0, 7.72), 10, 1.42,
                                 facecolor=SLATE, alpha=0.06, zorder=0))
axL.text(0.3, 8.78, "桌上的份量", color=SLATE, fontsize=10,
         fontproperties=serif_b, va='center')
axL.text(0.3, 8.24, "長鑫：全球第四大 DRAM 廠，市佔約 8%（2028 預估 18%）",
         color=INK, fontsize=8.9, va='center')
axL.text(0.3, 7.92, "長江存儲：NAND 全球市佔約 11–13%",
         color=INK, fontsize=8.9, va='center')

scripts = [
    ("劇本一", "禁令實施", RED,
     ["DRAM 少約 8%、NAND 少一成上下的供給來源",
      "2027 年那波供給潮少掉中國那一塊",
      "缺口擴大　→　價格更硬　→　台韓吃到轉單"]),
    ("劇本二", "禁令不實施", SLATE,
     ["中國供給繼續進來，數量上緩解短缺",
      "但它的報價本來就跟三大廠同步",
      "緩解「拿不拿得到」，不緩解「貴不貴」"]),
]

for i, (tag, name, c, points) in enumerate(scripts):
    top = 6.95 - i * 2.66
    axL.add_patch(mpatches.Rectangle((0, top - 2.12), 0.13, 2.12,
                                     color=c, zorder=3))
    axL.text(0.42, top - 0.30, tag, color=c, fontsize=10,
             fontproperties=serif_b, va='center')
    axL.text(1.55, top - 0.30, name, color=INK, fontsize=12.5,
             fontproperties=serif_b, va='center')
    for j, pt in enumerate(points):
        axL.text(0.42, top - 0.92 - j * 0.50, pt, color=INK,
                 fontsize=9, va='center')

axL.add_patch(mpatches.Rectangle((0, 0.42), 10, 1.05,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axL.text(0.3, 1.14, "共同結論", color=GOLD, fontsize=10,
         fontproperties=serif_b, va='center')
axL.text(0.3, 0.68, "「中國記憶體會把價格打下來」，兩個劇本都不成立",
         color=INK, fontsize=10.2, fontproperties=serif_b, va='center')

# ══════════ 右欄：SanDisk 十二天 ══════════
axR = fig.add_axes([0.525, 0.115, 0.443, 0.775])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.62, "十二天，同一批人砍完又升", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')
axR.text(9.95, 9.62, "單位：美元", color=GREY,
         fontsize=8.8, va='center', ha='right')

events = [
    ("8/5", "財報公布", GREEN,
     ["營收 +372%、毛利率 84.6%", "額外 140 億美元回購"], None),
    ("8/6", "四家券商砍目標價", RED,
     ["3,000 → 1,750（-42%）", "2,500 → 2,100　1,620 → 1,400"],
     "理由：NAND 定價趨緩"),
    ("8/17", "投資人日後升目標價", GREEN,
     ["升評並升至 2,250（當日股價 +8.88%）", "另家升至 3,250　2,100 → 2,500"],
     "理由：AI 帶動結構性需求"),
]

for i, (date, title, c, lines, why) in enumerate(events):
    top = 8.72 - i * 2.48
    axR.plot([0.55, 0.55], [top - 2.30, top], color=LGRID, lw=1.4, zorder=1)
    axR.add_patch(mpatches.Circle((0.55, top - 0.30), 0.20,
                                  color=c, zorder=3))
    axR.text(1.20, top - 0.30, date, color=c, fontsize=11,
             fontproperties=serif_b, va='center')
    axR.text(2.35, top - 0.30, title, color=INK, fontsize=11.5,
             fontproperties=serif_b, va='center')
    for j, ln in enumerate(lines):
        axR.text(1.20, top - 0.92 - j * 0.46, ln, color=INK,
                 fontsize=9, va='center')
    if why:
        axR.text(1.20, top - 0.92 - len(lines) * 0.46, why, color=GREY,
                 fontsize=8.6, va='center')

axR.add_patch(mpatches.Rectangle((0, 0.42), 10, 1.05,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axR.text(0.3, 1.14, "中間發生了什麼基本面變化？", color=GOLD, fontsize=10,
         fontproperties=serif_b, va='center')
axR.text(0.3, 0.68, "合約價沒轉跌、需求沒消失。變的是解讀",
         color=INK, fontsize=10.2, fontproperties=serif_b, va='center')

fig.text(0.046, 0.072,
         "資料來源：眾議院中國問題特別委員會信函、券商報告、Tom's Hardware、TrendForce／DRAMeXchange、產業媒體，摸魚記整理。\n"
         "市佔與 2028 年預估各家統計口徑不一；券商目標價為其個別觀點，非投資建議。",
         color=GREY, fontsize=7.5, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/BAN-chart-two-scripts.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

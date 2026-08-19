"""
摸魚記 中國記憶體篇 v2 圖：十二天的兩件事 ＋ 兩種劇本
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

fig = plt.figure(figsize=(13.6, 8.6), facecolor=BG)

fig.text(0.046, 0.948, "■", color=GOLD, fontsize=13)
fig.text(0.068, 0.941, "十二天砍完又升，中間發生了兩件事",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.046, 0.968], [0.912, 0.912],
                            transform=fig.transFigure, color=INK, lw=0.8))

# ══════════ 左欄：時間軸 ══════════
axL = fig.add_axes([0.046, 0.108, 0.455, 0.785])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.66, "時間軸", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')
axL.text(9.95, 9.66, "目標價單位：美元", color=GREY,
         fontsize=8.6, va='center', ha='right')

events = [
    ("8/5", "財報公布", SLATE, False,
     ["營收 +372%、毛利率 84.6%", "但財測的定價展望偏保守"]),
    ("8/6", "四家券商砍目標價", RED, False,
     ["3,000 → 1,750（-42%）", "2,500 → 2,100　1,620 → 1,400"]),
    ("8/13", "投資人日：939 億長約", GREEN, True,
     ["8 個客戶、911 億未認列、地板價結構", "FY28–30 毛利率目標約 80%",
      "產業首例：逾半位元產出以地板價鎖定"]),
    ("8/14–17", "商務部長警告蘋果", GREEN, True,
     ["公開點名不得採購中國記憶體", "但目前沒有法規可以真正阻止"]),
    ("8/17", "券商回頭升目標價", GREEN, False,
     ["升評並升至 2,250（當日 +8.88%）", "另家升至 3,250　2,100 → 2,500"]),
]

for i, (date, title, c, is_key, lines) in enumerate(events):
    top = 8.92 - i * 1.58
    axL.plot([0.52, 0.52], [top - 1.46, top], color=LGRID, lw=1.3, zorder=1)
    r = 0.22 if is_key else 0.16
    axL.add_patch(mpatches.Circle((0.52, top - 0.26), r, color=c, zorder=3))
    axL.text(1.12, top - 0.26, date, color=c, fontsize=10.5,
             fontproperties=serif_b, va='center')
    axL.text(2.55, top - 0.26, title, color=INK,
             fontsize=11.5 if is_key else 10.8,
             fontproperties=serif_b, va='center')
    if is_key:
        axL.text(9.95, top - 0.26, "實質事件", color=GREEN, fontsize=8.8,
                 fontproperties=serif_b, va='center', ha='right')
    for j, ln in enumerate(lines):
        axL.text(1.12, top - 0.74 - j * 0.36, ln, color=INK,
                 fontsize=8.6, va='center')

axL.add_patch(mpatches.Rectangle((0, 0.05), 10, 0.92,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axL.text(0.3, 0.51, "不是情緒來回。合約結構與政策風向，都真的變了",
         color=INK, fontsize=10, fontproperties=serif_b, va='center')

# ══════════ 右欄：兩種劇本 ══════════
axR = fig.add_axes([0.545, 0.108, 0.423, 0.785])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.66, "那禁令呢？兩種劇本", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

axR.add_patch(mpatches.Rectangle((0, 7.98), 10, 1.28,
                                 facecolor=SLATE, alpha=0.06, zorder=0))
axR.text(0.3, 8.90, "桌上的份量", color=SLATE, fontsize=9.6,
         fontproperties=serif_b, va='center')
axR.text(0.3, 8.44, "長鑫：全球第四大 DRAM 廠，市佔約 8%（2028 預估 18%）",
         color=INK, fontsize=8.6, va='center')
axR.text(0.3, 8.14, "長江存儲：NAND 全球市佔約 11–13%",
         color=INK, fontsize=8.6, va='center')

scripts = [
    ("劇本一", "管制真的落地", RED,
     ["DRAM 少約 8%、NAND 少一成上下",
      "2027 那波供給潮少掉中國那塊",
      "缺口擴大 → 價格更硬 → 台韓轉單"]),
    ("劇本二", "停在勸阻，不落地", SLATE,
     ["中國供給續進，數量上緩解短缺",
      "但它的報價本來就跟三大廠同步",
      "緩解「拿不拿得到」，不緩解「貴不貴」"]),
]

for i, (tag, name, c, points) in enumerate(scripts):
    top = 7.28 - i * 2.42
    axR.add_patch(mpatches.Rectangle((0, top - 1.96), 0.13, 1.96,
                                     color=c, zorder=3))
    axR.text(0.42, top - 0.28, tag, color=c, fontsize=9.8,
             fontproperties=serif_b, va='center')
    axR.text(1.50, top - 0.28, name, color=INK, fontsize=11.8,
             fontproperties=serif_b, va='center')
    for j, pt in enumerate(points):
        axR.text(0.42, top - 0.84 - j * 0.46, pt, color=INK,
                 fontsize=8.8, va='center')

axR.add_patch(mpatches.Rectangle((0, 1.62), 10, 0.92,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axR.text(0.3, 2.08, "共同結論：「中國記憶體會把價格打下來」，兩邊都不成立",
         color=INK, fontsize=9.8, fontproperties=serif_b, va='center')

axR.text(0.3, 1.05, "現況：長鑫未列 BIS 實體清單，僅列國防部名單；",
         color=GREY, fontsize=8.4, va='center')
axR.text(0.3, 0.66, "部長的話很重，但那是勸阻，不是禁令",
         color=GREY, fontsize=8.4, va='center')

fig.text(0.046, 0.066,
         "資料來源：SanDisk 2026 投資人日、眾議院中國問題特別委員會信函、券商報告、Tom's Hardware、TrendForce／DRAMeXchange，摸魚記整理。\n"
         "市佔與 2028 年預估各家統計口徑不一；券商目標價為其個別觀點，非投資建議。",
         color=GREY, fontsize=7.5, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/BAN-chart-two-scripts.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

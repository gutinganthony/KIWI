"""
摸魚記 記憶體對帳篇 圖：對帳計分卡 ＋ 日本那條斷掉的鏈 ＋ 三道裂縫與反方證據
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題），沿用放大字級
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

fig = plt.figure(figsize=(15.4, 12.4), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.045, 0.964, "■", color=GOLD, fontsize=17)
fig.text(0.071, 0.956, "不缺貨，跟不漲價，是兩件事",
         color=INK, fontsize=26, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.045, 0.965], [0.939, 0.939],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.071, 0.920,
         "缺貨講拿不拿得到，漲價講貴不貴，股價講的是還能漲幾季。三件事會依序結束。",
         color=GREY, fontsize=14)

# ══════════ 全寬：對帳計分卡 ══════════
axT = fig.add_axes([0.045, 0.806, 0.920, 0.098])
axT.set_facecolor(BG); axT.axis('off')
axT.set_xlim(0, 100); axT.set_ylim(0, 10)

axT.text(0, 9.4, "上一篇的四條，這週開獎", color=INK,
         fontsize=15, fontproperties=serif_b, va='top')

cards = [
    ("升息已被定價", "○", "12-0 全票，3.75–4.00%", GREEN),
    ("點陣圖 4% 出頭不算鷹", "○", "2026、2027 年底皆 4.1%", GREEN),
    ("關鍵是通膨失控與否", "○", "核心 CPI 2.4%，2021/3 來最低", GREEN),
    ("日本套利交易會鬆動", "×", "日圓反貶到 157.23", RED),
]
for i, (claim, mark, note, c) in enumerate(cards):
    x = i * 25.1
    axT.add_patch(mpatches.Rectangle((x, 0.5), 0.16, 5.6, color=c, zorder=3))
    axT.text(x + 0.6, 5.0, claim, color=INK, fontsize=12.2,
             fontproperties=serif_b, va='center')
    axT.text(x + 0.6, 2.6, f"{mark}", color=c, fontsize=18,
             fontproperties=serif_b, va='center')
    axT.text(x + 2.3, 2.6, note, color=GREY, fontsize=10.8, va='center')

# ══════════ 左欄：日本那條斷掉的鏈 ══════════
axL = fig.add_axes([0.045, 0.100, 0.400, 0.680])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.72, "我那條鏈，斷在第二節", color=INK,
         fontsize=15.5, fontproperties=serif_b, va='center')

chain = [
    ("日本升息", True, SLATE, "9/18 升至 1.25%，1995/4 來最高"),
    ("日圓變貴", False, RED, "沒有發生。反貶至 157.23"),
    ("借日圓的成本上升", False, GREY, ""),
    ("套利交易平倉", False, GREY, ""),
    ("全球資產被拋售", False, GREY, ""),
]
for i, (txt, ok, c, note) in enumerate(chain):
    y = 8.40 - i * 1.15
    axL.add_patch(mpatches.Circle((0.32, y), 0.145, color=c, zorder=3))
    axL.text(0.88, y, txt, color=INK if ok or i == 1 else GREY,
             fontsize=13, fontproperties=serif_b if i <= 1 else sans, va='center')
    if note:
        axL.text(0.88, y - 0.50, note, color=c, fontsize=11, va='center')
    if i < len(chain) - 1:
        style = '-|>' if i == 0 else '-|>'
        col = LGRID if i > 0 else LGRID
        axL.annotate("", xy=(0.32, y - 0.97), xytext=(0.32, y - 0.19),
                     arrowprops=dict(arrowstyle=style, color=col, lw=1.5))

axL.plot([0.10, 4.05], [7.60, 6.90], color=RED, lw=2.6, zorder=5)
axL.plot([0.10, 4.05], [6.90, 7.60], color=RED, lw=2.6, zorder=5)

axL.add_patch(mpatches.Rectangle((0, 1.45), 10, 1.70,
                                 facecolor=SLATE, alpha=0.055, zorder=0))
evid = [
    ("7 比 2", "兩位委員反對，被讀成「不會太鷹」"),
    ("−4.9bp", "日本 10 年期反跌至 2.947%"),
    ("+1.38%", "日經 225 收 65,019 點"),
]
for i, (num, desc) in enumerate(evid):
    y = 2.82 - i * 0.48
    axL.text(0.28, y, num, color=SLATE, fontsize=12,
             fontproperties=serif_b, va='center')
    axL.text(2.45, y, desc, color=INK, fontsize=11, va='center')

axL.add_patch(mpatches.Rectangle((0, 0.05), 10, 1.02,
                                 facecolor=GOLD, alpha=0.12, zorder=0))
axL.text(0.28, 0.72, "升息不等於貨幣走強。", color=INK,
         fontsize=12.6, fontproperties=serif_b, va='center')
axL.text(0.28, 0.32, "匯率看的是下一次還會不會升，而票數分歧講的正是下一次。",
         color=GREY, fontsize=11, va='center')

# ══════════ 右欄上：三道裂縫 ══════════
axR = fig.add_axes([0.495, 0.432, 0.470, 0.348])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 100); axR.set_ylim(0, 10)

axR.text(0, 9.72, "記憶體的三道裂縫", color=INK,
         fontsize=15.5, fontproperties=serif_b, va='center')

cracks = [
    ("9/9", "鎧俠", RED,
     ["社長太田裕雄指示業務，不要再向", "資料中心客戶大幅推漲報價"],
     "第一家主動喊煞車的原廠"),
    ("9/19", "宏碁", RED,
     ["陳俊聖：記憶體沒有缺貨、", "大家滿手貨、陸方價錢很殺"],
     "但同場說 4Q PC 仍漲 5–20%"),
    ("9/20", "長鑫", RED,
     ["G5 量產，每片晶圓裸片數 +50%", "（官方未公布良率）"],
     "與「陸方價錢很殺」是同一條線"),
]
for i, (d, who, c, lines, tail) in enumerate(cracks):
    top = 8.55 - i * 2.72
    axR.add_patch(mpatches.Rectangle((0, top - 2.16), 0.16, 2.16,
                                     color=c, zorder=3))
    axR.text(0.7, top - 0.30, d, color=c, fontsize=13,
             fontproperties=serif_b, va='center')
    axR.text(7.6, top - 0.30, who, color=INK, fontsize=13,
             fontproperties=serif_b, va='center')
    for j, ln in enumerate(lines):
        axR.text(14.5, top - 0.18 - j * 0.60, ln, color=INK,
                 fontsize=11.2, va='center')
    axR.text(14.5, top - 1.72, tail, color=GREY, fontsize=10.8, va='center')

axR.text(0, 0.42, "外資對華邦電：9/18 淨買 42,774 張 → 9/21 淨賣 23,212 張",
         color=INK, fontsize=11.8, fontproperties=serif_b, va='center')

# ══════════ 右欄下：反方證據 ══════════
fig.text(0.495, 0.392, "但反方的證據一樣硬", color=INK,
         fontsize=15.5, fontproperties=serif_b)

axB = fig.add_axes([0.495, 0.100, 0.470, 0.272])
axB.set_facecolor(BG); axB.axis('off')
axB.set_xlim(0, 100); axB.set_ylim(0, 10)

counters = [
    ("+259.4%", "韓國 9/1–20 半導體出口年增，佔出口 47.8%，史上最高", GREEN),
    ("+7.05%", "鎧俠喊煞車當天，SK 海力士 ADR 收漲；美光 +2.75%", GREEN),
    ("逾 20%", "UBS 預期第三季記憶體 ASP 再漲，供給吃緊延續至 2027", GREEN),
]
for i, (num, desc, c) in enumerate(counters):
    y = 8.6 - i * 2.35
    axB.add_patch(mpatches.Rectangle((0, y - 0.95), 0.16, 1.90,
                                     color=c, zorder=3))
    axB.text(0.7, y, num, color=c, fontsize=19,
             fontproperties=serif_b, va='center')
    axB.text(17.5, y, desc, color=INK, fontsize=11.2, va='center')

axB.add_patch(mpatches.Rectangle((0, 0.05), 100, 1.15,
                                 facecolor=GOLD, alpha=0.12, zorder=0))
axB.text(0.7, 0.62, "一家原廠喊煞車是個別策略，三家都喊才是循環轉折。目前是一家。",
         color=INK, fontsize=12, fontproperties=serif_b, va='center')

fig.text(0.045, 0.062,
         "資料來源：聯準會（FOMC 聲明與 SEP）、美國勞工統計局、日本銀行、彭博、中央社、韓國關稅廳、台灣證券交易所，摸魚記整理。\n"
         "鎧俠社長發言出自彭博獨家專訪，係媒體專訪非正式財測，且僅涉及 NAND 不涉 DRAM；三星與 SK 海力士截至本稿未跟進。\n"
         "長鑫 G5 良率官方未公布，本圖不列。本圖為摸魚記自行整理，不構成投資建議。",
         color=GREY, fontsize=9.8, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/CRACK-chart-memory.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print(f'Done -> {out}')

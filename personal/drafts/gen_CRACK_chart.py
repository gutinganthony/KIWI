"""
摸魚記 記憶體篇 圖 v3：分層矩陣
骨架已換（v2 的「三件事依序結束」已被推翻）。
主視覺＝五層記憶體 × 兩問（還缺不缺／還在漲嗎），用圓形圖示承載鬆緊，文字只做註腳。
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

FW, FH = 15.5, 9.8
fig = plt.figure(figsize=(FW, FH), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.05, 0.952, "■", color=GOLD, fontsize=17)
fig.text(0.077, 0.944, "「記憶體」不是一個市場",
         color=INK, fontsize=28, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.05, 0.96], [0.918, 0.918],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.077, 0.893, "同一個詞底下，是五個正在分岔的市場", color=GREY, fontsize=15)

# ══════════ 主視覺 ══════════
AX = [0.05, 0.158, 0.910, 0.705]
ax = fig.add_axes(AX)
ax.set_facecolor(BG); ax.axis('off')
X0, X1, Y0, Y1 = 0, 100, 4, 104
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)

# 讓圓形不被座標系拉成橢圓
x_in = AX[2] * FW / (X1 - X0)
y_in = AX[3] * FH / (Y1 - Y0)
ASPECT = x_in / y_in          # 一個 x 單位相當於幾個 y 單位

RX = 1.75                      # 圖示半徑（x 單位）
RY = RX * ASPECT


def icon(cx, cy, state):
    """state: 'tight' 實心／'easing' 下半實心／'loose' 空心"""
    c = {'tight': RED, 'easing': GOLD, 'loose': GREY}[state]
    ring = mpatches.Ellipse((cx, cy), 2 * RX, 2 * RY, facecolor='none',
                            edgecolor=c, lw=2.4, zorder=5)
    ax.add_patch(ring)
    if state == 'tight':
        ax.add_patch(mpatches.Ellipse((cx, cy), 2 * RX, 2 * RY,
                                      facecolor=c, edgecolor='none', zorder=4))
    elif state == 'easing':
        half = mpatches.Rectangle((cx - RX, cy - RY), 2 * RX, RY,
                                  facecolor=c, edgecolor='none', zorder=4)
        ax.add_patch(half)
        half.set_clip_path(ring)


COL_ICON1, COL_TXT1 = 30.0, 34.6
COL_ICON2, COL_TXT2 = 58.0, 62.6
COL_WHO = 84.0

# ── 欄標 ──
ax.text(0, 100, "這一層是什麼", color=GREY, fontsize=13.5, va='center')
ax.text(COL_ICON1 - RX, 100, "還缺不缺", color=INK, fontsize=15,
        fontproperties=serif_b, va='center')
ax.text(COL_ICON2 - RX, 100, "還在漲嗎", color=INK, fontsize=15,
        fontproperties=serif_b, va='center')
ax.text(COL_WHO, 100, "這兩週誰在講", color=INK, fontsize=15,
        fontproperties=serif_b, va='center')
ax.plot([0, 100], [95.5, 95.5], color=INK, lw=0.9, zorder=3)

# ── 兩個群組的底色帶 ──
ax.add_patch(mpatches.Rectangle((0, 52), 100, 42, facecolor=SLATE,
                                alpha=0.055, zorder=0))
ax.add_patch(mpatches.Rectangle((0, 17), 100, 31, facecolor=GREY,
                                alpha=0.045, zorder=0))

ax.text(0.9, 90, "AI 資料中心買的是這三層", color=SLATE, fontsize=14,
        fontproperties=serif_b, va='center')
ax.text(0.9, 44, "這兩層不是", color=GREY, fontsize=14,
        fontproperties=serif_b, va='center')

# ── 五列 ──
#  (層名, 副註, y, 缺貨狀態, 缺貨註, 漲價狀態, 漲價註, 誰在講, 誰的顏色)
rows = [
    ("HBM", "貼在 GPU 旁邊", 82,
     'tight', "2027 年產能已售完", 'tight', "客戶只拿到六到七成",
     "輝達改評 8 層", SLATE),
    ("伺服器 DRAM", "餵 CPU 的主記憶體", 70,
     'tight', "企業級交期逾 40 週", 'tight', "傳 Q4 附約 +40~50%",
     "沒有人說鬆", GREY),
    ("企業級 SSD", "NAND，容量層", 58,
     'easing', "資料中心需求仍旺", 'loose', "合約價走平、現貨弱",
     "鎧俠「漲夠了」", RED),
    ("PC DRAM", "筆電桌機用", 36,
     'easing', "品牌廠庫存在高檔", 'easing', "漲幅收斂，未轉跌",
     "宏碁「不缺了」", RED),
    ("行動 DRAM", "手機用的 LPDDR", 24,
     'easing', "陸廠產能持續投入", 'easing', "季增收斂到 8~13%",
     "長鑫 G5 量產", RED),
]

for name, sub, y, s1, t1, s2, t2, who, wc in rows:
    ax.text(0, y + 1.5, name, color=INK, fontsize=16.5,
            fontproperties=serif_b, va='center')
    ax.text(0, y - 2.6, sub, color=GREY, fontsize=11.5, va='center')
    icon(COL_ICON1, y, s1)
    ax.text(COL_TXT1, y, t1, color=INK, fontsize=12.5, va='center')
    icon(COL_ICON2, y, s2)
    ax.text(COL_TXT2, y, t2, color=INK, fontsize=12.5, va='center')
    ax.text(COL_WHO, y, who, color=wc, fontsize=13.5,
            fontproperties=serif_b, va='center')

# ── 圖示說明 ──
LEG_Y = 9.0
ax.text(0, LEG_Y, "圖示", color=GREY, fontsize=12, va='center')
for i, (st, lab) in enumerate((('tight', "還緊"), ('easing', "收斂中"),
                               ('loose', "已鬆"))):
    cx = COL_ICON1 + i * 13.5
    icon(cx, LEG_Y, st)
    ax.text(cx + 2.9, LEG_Y, lab, color=GREY, fontsize=12, va='center')

# ══════════ 底部 ══════════
fig.lines.append(plt.Line2D([0.05, 0.96], [0.127, 0.127],
                            transform=fig.transFigure, color=LGRID, lw=0.9))
fig.text(0.05, 0.090, "他們三個講的，是三條不同的線。",
         color=INK, fontsize=17, fontproperties=serif_b)
fig.text(0.05, 0.055,
         "資料來源：集邦科技、彭博、中央社、長鑫存儲、韓國關稅廳，摸魚記整理。各層供需為 2026 年 9 月狀態。第四季附約漲幅為媒體引述之業界說法，非原廠公告；\n"
         "長鑫 G5 官方未公布良率。反方觀點：另有報導引 PC 業界稱三大原廠第四季仍將調漲，韓國輸出入銀行預測 DRAM 短缺延續至 2027 下半年。不構成投資建議。",
         color=GREY, fontsize=10, linespacing=1.75, va='top')

out = '/home/user/KIWI/personal/drafts/CRACK-chart-memory.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print('Done -> ' + out)

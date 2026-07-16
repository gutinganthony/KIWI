"""
摸魚記 W6 圖：三週對帳 ＋ 台積電證詞（JPM Daily Guide 版型）
左欄：6/26 → 7/16 四指標對帳（雙點 dumbbell 各自獨立行，避免混軸）
右欄：台積電法說三個證詞數字（stat 大字）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

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
SLATE = "#4a5d7a"

fig = plt.figure(figsize=(13, 7.6), facecolor=BG)

fig.text(0.052, 0.93, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.923, "恐慌喊到最大聲的那週，裁判剛好一個一個進場",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.888, 0.888],
                             transform=fig.transFigure, color=INK, lw=0.8))

# ══ 左欄：三週對帳 ══
axL = fig.add_axes([0.055, 0.14, 0.46, 0.63])
axL.set_facecolor(BG)
axL.set_title("成績單一：三週前說「可以試單」，對帳", loc='left',
              color=INK, fontsize=12.5, fontproperties=serif_b, pad=40)
axL.text(0, 1.055, "6/26（試單日）→ 7/16（今天）", transform=axL.transAxes,
         color=GREY, fontsize=9.5)
axL.set_xlim(0, 10)
axL.set_ylim(0, 4.6)
axL.axis('off')

rows = [
    ("加權指數",   "44,571.76", "45,624.98", "+2.4%，盤中低點未破 6/26", GREEN),
    ("VIXTWN",     "44.27",     "34.74",     "恐慌大退潮",               GREEN),
    ("外資單日賣超", ">1,700 億", "483 億",   "還在賣，力道剩 1/3",       SLATE),
    ("融資維持率", "174.57%",   "182.88%",   "散戶層更穩",               GREEN),
]
for i, (name, v0, v1, note, c) in enumerate(rows):
    y = 4.0 - i * 1.08
    axL.text(0.0, y, name, ha='left', va='center', color=INK,
             fontsize=11.5, fontproperties=serif_b)
    axL.text(3.6, y, v0, ha='right', va='center', color=GREY, fontsize=11)
    axL.annotate('', xy=(4.9, y), xytext=(3.9, y),
                 arrowprops=dict(arrowstyle='->', color=GREY, lw=1.0))
    axL.text(5.1, y, v1, ha='left', va='center', color=c,
             fontsize=12, fontproperties=serif_b)
    axL.text(10.0, y, note, ha='right', va='center', color=GREY, fontsize=9)
    if i < 3:
        axL.plot([0, 10], [y - 0.54, y - 0.54], color=LGRID, lw=0.7)

axL.text(0, -0.06, "判斷驗收：兩盞燈＝可試單 ✓（恐慌燈自己退了，三、四盞的世代大底沒有來）",
         transform=axL.transAxes, color=INK, fontsize=10, fontproperties=serif_b, va='top')

# ══ 右欄：台積電證詞 ══
axR = fig.add_axes([0.575, 0.14, 0.39, 0.63])
axR.set_facecolor(BG)
axR.set_title("成績單二：需求端證人的證詞（7/16 法說）", loc='left',
              color=INK, fontsize=12.5, fontproperties=serif_b, pad=40)
axR.set_xlim(0, 1)
axR.set_ylim(0, 4.6)
axR.axis('off')

stats = [
    ("600–640 億美元", "資本支出上修，理由：客戶需求太過強烈"),
    ("+40% 以上", "全年美元營收成長率，再度上修"),
    ("67.7%", "Q2 毛利率，超出自家指引上緣"),
]
for i, (big, small) in enumerate(stats):
    y = 3.85 - i * 1.3
    axR.text(0.0, y, big, ha='left', va='center', color=GOLD,
             fontsize=21, fontproperties=serif_b)
    axR.text(0.0, y - 0.45, small, ha='left', va='center', color=INK, fontsize=10)
    if i < 2:
        axR.plot([0, 1], [y - 0.72, y - 0.72], color=LGRID, lw=0.7)

axR.text(0, -0.06, "韓國吵「供給過剩」的三天後：\n恐慌是用喊的，證據是用錢投的。",
         transform=axR.transAxes, color=INK, fontsize=10.5,
         fontproperties=serif_b, va='top', linespacing=1.7)

fig.text(0.052, 0.045,
         "資料來源：TWSE／期交所／WantGoo（16/07/26 收盤，融資維持率為 Jake 提供讀數）、台積電法說會（16/07/26）、BLS（美國 6 月 CPI 3.5%）。\n"
         "6/26 基準值出自〈台股抄底儀表板〉當日收盤。過往表現並非未來業績的可靠指標。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/W6-chart-verdict.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

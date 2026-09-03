"""
摸魚記 宏觀對帳篇 圖：貝森特的兩隻手 ＋ 四條判斷對帳 ＋ 台股三日籌碼
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線輕格線）
本張依 Jake 要求整體放大字級約 35%
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

fig = plt.figure(figsize=(15.2, 12.6), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.045, 0.965, "■", color=GOLD, fontsize=17)
fig.text(0.071, 0.957, "貝森特的兩隻手",
         color=INK, fontsize=26, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.045, 0.965], [0.941, 0.941],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.071, 0.921, "他左手買回長債，右手把最大的買家推回家",
         color=GREY, fontsize=14.5)

# ══════════ 全寬水位條 ══════════
axT = fig.add_axes([0.045, 0.812, 0.920, 0.092])
axT.set_facecolor(BG); axT.axis('off')
axT.set_xlim(0, 30); axT.set_ylim(0, 10)

axT.text(0, 9.6, "全球長端正在同步重估", color=INK,
         fontsize=15, fontproperties=serif_b, va='top')

levels = [
    ("日本", "十年期", "3.00%", "1996 年 9 月以來首見", RED),
    ("英國", "三十年期", "5.90%", "1990 年代末以來首見", RED),
    ("美國", "十年期", "4.79%", "已站上 4.75% 門檻", GOLD),
]
for i, (ctry, tenor, num, note, c) in enumerate(levels):
    x = i * 10.1
    axT.add_patch(mpatches.Rectangle((x, 0.2), 0.16, 6.2, color=c, zorder=3))
    axT.text(x + 0.62, 5.4, f"{ctry}｜{tenor}", color=GREY,
             fontsize=12, va='center')
    axT.text(x + 0.62, 2.6, num, color=c, fontsize=26,
             fontproperties=serif_b, va='center')
    axT.text(x + 4.0, 2.6, note, color=INK, fontsize=12, va='center')

# ══════════ 左欄：兩隻手 ＋ 傳導鏈 ＋ 三個證據 ══════════
axL = fig.add_axes([0.045, 0.105, 0.430, 0.677])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

hands = [
    ("對內", "8/19、8/24", SLATE,
     ["買回規模至少加倍（20 億 → 40 億）", "傳出可能動用近 1 兆美元 TGA 帳戶"],
     "目的：壓低美國長天期殖利率"),
    ("對外", "8/14 – 9/1", RED,
     ["稱日本央行「落後曲線」、預期升息", "美日聯合進場干預匯市",
      "直接告訴日本官員需要升息"],
     "目的：讓日圓走強"),
]
top = 9.90
for tag, when, c, lines, goal in hands:
    last = top - 0.75 - (len(lines) - 1) * 0.34
    gy = last - 0.48
    bottom = gy - 0.28
    axL.add_patch(mpatches.Rectangle((0, bottom), 10, top - bottom,
                                     facecolor=c, alpha=0.055, zorder=0))
    axL.add_patch(mpatches.Rectangle((0, bottom), 0.15, top - bottom,
                                     color=c, zorder=3))
    axL.text(0.48, top - 0.30, tag, color=c, fontsize=15,
             fontproperties=serif_b, va='center')
    axL.text(1.85, top - 0.30, when, color=GREY, fontsize=11.5, va='center')
    for j, ln in enumerate(lines):
        axL.text(0.48, top - 0.75 - j * 0.34, ln, color=INK,
                 fontsize=11.5, va='center')
    axL.text(0.48, gy, goal, color=c, fontsize=11.8,
             fontproperties=serif_b, va='center')
    top = bottom - 0.22

axL.text(0, 5.22, "但這兩隻手會在債市撞在一起", color=INK,
         fontsize=15, fontproperties=serif_b, va='center')

chain = [
    ("貝森特施壓", SLATE),
    ("日本央行升息", SLATE),
    ("日本公債殖利率上升", RED),
    ("壽險發現錢放在家裡賺得比較多", RED),
    ("賣掉美債，換回日本公債", RED),
    ("美國長端殖利率上升", RED),
    ("財政部的買回被抵銷", GOLD),
]
for i, (txt, c) in enumerate(chain):
    y = 4.67 - i * 0.45
    axL.add_patch(mpatches.Circle((0.30, y), 0.125, color=c, zorder=3))
    axL.text(0.78, y, txt, color=INK, fontsize=12.5, va='center')
    if i < len(chain) - 1:
        axL.annotate("", xy=(0.30, y - 0.315), xytext=(0.30, y - 0.145),
                     arrowprops=dict(arrowstyle='-|>', color=LGRID, lw=1.5))

axL.add_patch(mpatches.Rectangle((0, 0.35), 10, 1.20,
                                 facecolor=SLATE, alpha=0.05, zorder=0))
evid = [
    ("1.117 兆美元", "日本持有美債，全球最大外國持有者（2026/6）"),
    ("296 億美元", "2026 年第一季淨賣超，2022 年以來最大單季"),
    ("避險後已勝出", "日本長債報酬扣掉避險成本後高於 30 年期美債"),
]
for i, (num, desc) in enumerate(evid):
    y = 1.28 - i * 0.33
    axL.text(0.28, y, num, color=SLATE, fontsize=11.8,
             fontproperties=serif_b, va='center')
    axL.text(2.75, y, desc, color=INK, fontsize=11, va='center')

# ══════════ 右上：四條判斷對帳 ══════════
axR = fig.add_axes([0.525, 0.430, 0.440, 0.352])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.75, "上週寫的四條，九天後對帳", color=INK,
         fontsize=15, fontproperties=serif_b, va='center')

scores = [
    ("4.75% 是戰術轉結構的分界線", "成立", "9/2 收 4.79%", GREEN),
    ("通膨沒降，30Y 往 6% 要當真", "成立", "七月核心 PCE 年增 3.3%", GREEN),
    ("好消息帶著副作用", "判斷失準", "輝達財報後 +8.7%", RED),
    ("買回只是搬動問題", "觀察中", "10Y 破高、30Y 未再創高", GREY),
]
for i, (claim, verdict, note, c) in enumerate(scores):
    y = 8.30 - i * 2.12
    axR.add_patch(mpatches.Rectangle((0, y - 0.80), 0.15, 1.74,
                                     color=c, zorder=3))
    axR.text(0.48, y + 0.50, claim, color=INK, fontsize=12.8,
             fontproperties=serif_b, va='center')
    mark = "○" if c == GREEN else ("×" if c == RED else "△")
    axR.text(0.48, y - 0.20, f"{mark}  {verdict}", color=c, fontsize=13,
             fontproperties=serif_b, va='center')
    axR.text(3.30, y - 0.20, note, color=GREY, fontsize=11.5, va='center')

axR.text(0, 0.25, "分母只有在分子沒動的時候，才決定勝負",
         color=INK, fontsize=12.5, fontproperties=serif_b, va='center')

# ══════════ 右下：台股三日籌碼 ══════════
fig.text(0.525, 0.392, "三大法人買賣超與指數變動", color=INK,
         fontsize=15, fontproperties=serif_b)
fig.text(0.525, 0.370,
         "9/2 賣超是前一日買超的 2.03 倍，跌幅只有前一日漲幅的三分之一",
         color=INK, fontsize=12.3, fontproperties=serif_b)

axB = fig.add_axes([0.525, 0.105, 0.440, 0.230])
axB.set_facecolor(BG)
for s in ('top', 'right', 'left'):
    axB.spines[s].set_visible(False)
axB.spines['bottom'].set_color(LGRID)
axB.tick_params(axis='both', length=0, labelsize=11.5, colors=GREY)

days = ["8/31\nMSCI 生效日", "9/1", "9/2"]
net = [-258.46, 566.37, -1152.44]
idx = ["指數 -202.98", "指數 +820.25", "指數 -274.83"]
cols = [LGRID, GREEN, RED]

bars = axB.bar(range(3), net, width=0.50, color=cols, zorder=3)
axB.axhline(0, color=INK, lw=0.9, zorder=4)
axB.set_xticks(range(3)); axB.set_xticklabels(days)
axB.set_yticks([])
axB.set_ylim(-1720, 1060)
axB.grid(axis='y', color=LGRID, lw=0.6, zorder=0)

for i, (b, v, note) in enumerate(zip(bars, net, idx)):
    up = v > 0
    cx = b.get_x() + b.get_width() / 2
    axB.text(cx, v + (70 if up else -70), f"{v:+,.2f} 億",
             ha='center', va='bottom' if up else 'top',
             color=cols[i] if i else GREY, fontsize=12.5,
             fontproperties=serif_b)
    axB.text(cx, v + (300 if up else -300), note,
             ha='center', va='bottom' if up else 'top',
             color=GREY, fontsize=11)

fig.text(0.045, 0.042,
         "資料來源：美國財政部與 FRED、彭博、Japan Times、美國財政部國際資本流動報告、台灣證交所、MSCI，摸魚記整理。殖利率為 2026/9/2 水位；\n"
         "台股籌碼取自證交所三大法人買賣金額統計表。日本持有美債 1.117 兆美元為 2026 年 6 月數字。本圖為摸魚記自行整理，不構成投資建議。",
         color=GREY, fontsize=10, linespacing=1.9, va='top')

out = '/home/user/KIWI/personal/drafts/BOND-chart-two-hands.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print(f'Done -> {out}')

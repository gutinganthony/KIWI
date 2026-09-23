"""
摸魚記 記憶體對帳篇 圖 v2：極簡版
主視覺只有一個：三條依序結束的橫條。其餘壓到最低。
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LGRID = "#dcdcdc"
GOLD = "#b8954a"; RED = "#b23b32"; GREEN = "#2e7d4f"; SLATE = "#4a5d7a"

fig = plt.figure(figsize=(13.6, 8.8), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.05, 0.945, "■", color=GOLD, fontsize=16)
fig.text(0.078, 0.937, "三件事會依序結束",
         color=INK, fontsize=27, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.05, 0.96], [0.915, 0.915],
                            transform=fig.transFigure, color=INK, lw=1.0))

# ══════════ 主視覺：三條依序結束的橫條 ══════════
axM = fig.add_axes([0.05, 0.455, 0.91, 0.425])
axM.set_facecolor(BG); axM.axis('off')
axM.set_xlim(0, 100); axM.set_ylim(0, 10)

bars = [
    ("① 缺貨", "拿不拿得到", 40, 58, SLATE),
    ("② 漲價", "貴不貴", 58, 80, GOLD),
    ("③ 還能漲幾季", "股價賭的是這個", 80, 100, RED),
]

BAR_H = 1.55
for i, (name, sub, solid, fade, c) in enumerate(bars):
    y = 7.55 - i * 2.35
    axM.add_patch(mpatches.Rectangle((22, y), solid - 22, BAR_H,
                                     facecolor=c, zorder=3))
    cmap = LinearSegmentedColormap.from_list('fade', [c, BG])
    axM.imshow(np.linspace(0, 1, 512).reshape(1, -1),
               extent=[solid, fade, y, y + BAR_H],
               aspect='auto', cmap=cmap, zorder=3, interpolation='bilinear')
    axM.text(0, y + BAR_H / 2 + 0.30, name, color=c, fontsize=17,
             fontproperties=serif_b, va='center')
    axM.text(0, y + BAR_H / 2 - 0.52, sub, color=GREY, fontsize=12, va='center')

axM.annotate("", xy=(100, 1.45), xytext=(22, 1.45),
             arrowprops=dict(arrowstyle='-|>', color=LGRID, lw=1.6))
axM.text(22, 0.62, "越往右，結束得越晚", color=GREY, fontsize=12, va='center')
axM.text(100, 0.62, "多數人把這三件事當成同一件", color=INK, fontsize=12.5,
         fontproperties=serif_b, va='center', ha='right')

# ══════════ 左下：三道裂縫 ══════════
axL = fig.add_axes([0.05, 0.105, 0.42, 0.275])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 100); axL.set_ylim(0, 10)

axL.text(0, 9.5, "這兩週的三道裂縫", color=INK,
         fontsize=14.5, fontproperties=serif_b, va='top')

cracks = [("9/9", "鎧俠", "漲夠了"),
          ("9/19", "宏碁", "不缺了"),
          ("9/20", "長鑫", "我量產了")]
for i, (d, who, what) in enumerate(cracks):
    y = 6.5 - i * 2.35
    axL.add_patch(mpatches.Circle((2.2, y), 0.62, color=RED, zorder=3))
    axL.text(8, y, d, color=GREY, fontsize=13, va='center')
    axL.text(24, y, who, color=INK, fontsize=15,
             fontproperties=serif_b, va='center')
    axL.text(48, y, f"「{what}」", color=RED, fontsize=15,
             fontproperties=serif_b, va='center')
    if i < 2:
        axL.plot([2.2, 2.2], [y - 0.66, y - 1.69], color=LGRID, lw=1.4, zorder=1)

# ══════════ 右下：反方 ══════════
axR = fig.add_axes([0.545, 0.105, 0.415, 0.275])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 100); axR.set_ylim(0, 10)

axR.text(0, 9.5, "但反方一樣硬", color=INK,
         fontsize=14.5, fontproperties=serif_b, va='top')

counters = [("+259.4%", "韓國 9 月半導體出口年增"),
            ("+7.05%", "喊煞車當天，海力士 ADR"),
            ("逾 20%", "UBS 看第三季 ASP 再漲")]
for i, (num, desc) in enumerate(counters):
    y = 6.5 - i * 2.35
    axR.add_patch(mpatches.Rectangle((0, y - 0.95), 0.9, 1.9,
                                     color=GREEN, zorder=3))
    axR.text(4, y, num, color=GREEN, fontsize=20,
             fontproperties=serif_b, va='center')
    axR.text(34, y, desc, color=INK, fontsize=12.5, va='center')

# ══════════ 底線 ══════════
fig.lines.append(plt.Line2D([0.05, 0.96], [0.088, 0.088],
                            transform=fig.transFigure, color=LGRID, lw=0.9))
fig.text(0.05, 0.058, "一家原廠喊煞車是個別策略，三家都喊才是循環轉折。目前是一家。",
         color=INK, fontsize=14, fontproperties=serif_b)
fig.text(0.05, 0.022,
         "資料來源：彭博、中央社、長鑫存儲、韓國關稅廳、UBS，摸魚記整理。鎧俠社長發言僅涉 NAND 不涉 DRAM，三星與 SK 海力士未跟進。不構成投資建議。",
         color=GREY, fontsize=9.5)

out = '/home/user/KIWI/personal/drafts/CRACK-chart-memory.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

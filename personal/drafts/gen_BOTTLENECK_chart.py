"""
摸魚記 瓶頸分層篇 圖：四層瓶頸的壽命 ＋ 記憶體家族站在哪一層
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
fig.text(0.068, 0.938, "瓶頸有四種，壽命完全不同",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.046, 0.968], [0.906, 0.906],
                            transform=fig.transFigure, color=INK, lw=0.8))
fig.text(0.068, 0.884, "黃仁勳說「沒有一個瓶頸會持續超過兩三年」。這句話只對第一層完全成立。",
         color=GREY, fontsize=10)

# ══════════ 左欄：四層瓶頸 ══════════
axL = fig.add_axes([0.046, 0.115, 0.435, 0.735])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.72, "兩三年內能被突破嗎？", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

layers = [
    ("產能瓶頸", "✓ 能", GREEN,
     "錢與時間可解，設備買得到",
     "CoWoS 三年十倍、缺口 20%→10%"),
    ("技術瓶頸", "△ 部分", GOLD,
     "良率與 know-how 要爬學習曲線",
     "HBM 堆疊、混合鍵合、EUV"),
    ("材料瓶頸", "× 難", RED,
     "卡在地理，不受資本開支影響",
     "銦約七成來自中國、鎵與稀土"),
    ("政策瓶頸", "× 不適用", SLATE,
     "不受市場規律，還會反向擴大",
     "FCC 擬禁中國光模組、出口管制"),
]

for i, (name, verdict, c, why, case) in enumerate(layers):
    top = 8.95 - i * 2.22
    axL.add_patch(mpatches.Rectangle((0, top - 1.72), 0.14, 1.72,
                                     color=c, zorder=3))
    axL.text(0.45, top - 0.30, name, color=INK, fontsize=12.5,
             fontproperties=serif_b, va='center')
    axL.text(9.98, top - 0.30, verdict, color=c, fontsize=12.5,
             fontproperties=serif_b, va='center', ha='right')
    axL.text(0.45, top - 0.92, why, color=INK, fontsize=9.4, va='center')
    axL.text(0.45, top - 1.44, case, color=GREY, fontsize=8.8, va='center')
    if i < 3:
        axL.plot([0, 10], [top - 1.96, top - 1.96], color=LGRID, lw=0.7)

# ══════════ 右欄：記憶體家族站在哪一層 ══════════
axR = fig.add_axes([0.535, 0.115, 0.433, 0.735])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.72, "記憶體這一家人，站在哪一層？", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')
axR.text(9.98, 9.72, "越上面，越不容易被錢解決", color=GREY,
         fontsize=9, va='center', ha='right')

tiers = [
    ("技術瓶頸層", "撐最久", GREEN, 8.95, 2.72,
     "HBM 三雄",
     ["市佔：海力士 50–62%、三星 25–40%、美光 10–20%",
      "但整體 DRAM 三星 38% 居首，錯位是最大變數",
      "1 bit HBM 吃掉 DDR5 三倍晶圓；新產能 2027 底才來"]),
    ("排擠型瓶頸層", "現在最甜，但要盯", GOLD, 5.86, 2.72,
     "台廠 DDR4、利基型記憶體、模組廠",
     ["大廠產能全轉 HBM／DDR5，沒人回頭擴舊規格",
      "大摩 DDR4 缺口預估 14% → 19–20%",
      "7 月現貨 DDR4 約 80 美元，反而高於 DDR5 的 49 美元"]),
    ("純產能瓶頸層", "最先鬆", RED, 2.77, 2.50,
     "NAND",
     ["財報 beat：營收 +372%、毛利率 84.6%",
      "但 Jefferies 目標價砍 42% 仍維持 Buy",
      "理由：NAND 定價趨緩。營收在長，價格在鈍"]),
]

for name, tag, c, top, h, member, points in tiers:
    axR.add_patch(mpatches.Rectangle((0, top - h), 10, h,
                                     facecolor=c, alpha=0.055, zorder=0))
    axR.add_patch(mpatches.Rectangle((0, top - h), 0.13, h,
                                     color=c, zorder=3))
    axR.text(0.42, top - 0.34, name, color=c, fontsize=11.4,
             fontproperties=serif_b, va='center')
    axR.text(9.92, top - 0.34, tag, color=c, fontsize=9.6,
             fontproperties=serif_b, va='center', ha='right')
    axR.text(0.42, top - 0.94, member, color=INK, fontsize=10.4,
             fontproperties=serif_b, va='center')
    for j, pt in enumerate(points):
        axR.text(0.42, top - 1.44 - j * 0.42, pt, color=GREY,
                 fontsize=8.5, va='center')


fig.text(0.046, 0.068,
         "資料來源：黃仁勳 Dwarkesh Patel Podcast 專訪（CoWoS 數據為其說法轉述）、TrendForce／DRAMeXchange、Morgan Stanley、"
         "各公司財報與券商報告，摸魚記整理。\n"
         "HBM 與 DRAM 市佔各家統計口徑不一，區間為多方來源綜合。分層為摸魚記自訂框架，非標準產業分類；不構成投資建議。",
         color=GREY, fontsize=7.5, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/BOTTLENECK-chart-four-layers.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

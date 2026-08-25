"""
摸魚記 美債殖利率篇 圖：AI 發債的自我抑制循環 ＋ 關鍵水位與台股台幣連動
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
fig.text(0.068, 0.941, "AI 正在推高自己的資金成本",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.046, 0.968], [0.912, 0.912],
                            transform=fig.transFigure, color=INK, lw=0.8))
fig.text(0.068, 0.888, "產業看證據，估值看利率。這兩件事都對，只是不在同一條跑道上。",
         color=GREY, fontsize=10)

# ══════════ 左欄：自我抑制循環 ══════════
axL = fig.add_axes([0.046, 0.105, 0.455, 0.755])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.58, "一個自我抑制的循環", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

loop = [
    ("AI 資本支出暴增", "2026 年 hyperscaler capex 約 6,970 億美元", SLATE),
    ("自有現金流不夠", "capex 已吃掉近 100% 營運現金流（十年均 40%）", SLATE),
    ("只好大量發債", "2026 年 AI 相關發債近 5,700 億，為前一年兩倍多", RED),
    ("成為投等債最大板塊", "供給壓垮需求，認購倍數下降", RED),
    ("殖利率上升", "30 年期 5.273%，2007 年以來最高", RED),
    ("折現率上升", "遠期獲利現值下降，本益比被壓縮", RED),
    ("高倍數股票受壓", "而 AI 股正是高倍數股票", GOLD),
]

for i, (title, desc, c) in enumerate(loop):
    y = 8.78 - i * 1.14
    axL.add_patch(mpatches.Circle((0.42, y), 0.20, color=c, zorder=3))
    axL.text(0.42, y, str(i + 1), color='#ffffff', fontsize=8.6,
             fontproperties=serif_b, va='center', ha='center')
    axL.text(1.02, y + 0.16, title, color=INK, fontsize=11,
             fontproperties=serif_b, va='center')
    axL.text(1.02, y - 0.32, desc, color=GREY, fontsize=8.4, va='center')
    if i < len(loop) - 1:
        axL.annotate("", xy=(0.42, y - 0.82), xytext=(0.42, y - 0.26),
                     arrowprops=dict(arrowstyle='-|>', color=LGRID, lw=1.3))

axL.add_patch(mpatches.Rectangle((0, 0.10), 10, 0.78,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axL.text(0.3, 0.49, "AI 投資越積極，它自己的估值壓力就越大",
         color=INK, fontsize=10.2, fontproperties=serif_b, va='center')

# ══════════ 右欄：水位 + 台股台幣 ══════════
axR = fig.add_axes([0.545, 0.105, 0.423, 0.755])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.58, "三個要記住的水位", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')
axR.text(9.95, 9.58, "2026/8/21", color=GREY,
         fontsize=8.6, va='center', ha='right')

levels = [
    ("4.74%", "十年期公債", GOLD,
     "4.75% 是「戰術謹慎 → 結構換股」的分界，已站在線上"),
    ("5.273%", "三十年期公債", RED,
     "2007 年以來最高，十九年沒看過的水位"),
    ("6%", "市場心裡的天花板", GREY,
     "有分析師稱這是股市當前最大風險（單一觀點）"),
]

for i, (num, name, c, desc) in enumerate(levels):
    top = 8.86 - i * 1.52
    axR.add_patch(mpatches.Rectangle((0, top - 1.16), 0.13, 1.16,
                                     color=c, zorder=3))
    axR.text(0.45, top - 0.30, num, color=c, fontsize=17,
             fontproperties=serif_b, va='center')
    axR.text(2.75, top - 0.30, name, color=INK, fontsize=10.5,
             fontproperties=serif_b, va='center')
    axR.text(0.45, top - 0.90, desc, color=GREY, fontsize=8.4, va='center')

axR.text(0, 4.18, "財政部出手三次，市場不買帳", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

moves = [
    ("8/19", "宣布買回至少加倍（20 億 → 40 億）", "30Y 5.26% → 5.18%", GREEN),
    ("8/20 早", "長端反轉，吐回全部跌幅", "10Y 回升至 4.7% 以上", RED),
    ("8/20", "說可再超過 40 億，並預告財政整頓計畫", "市場評價：弱化版扭轉操作", GREY),
]
for j, (d, act, react, c) in enumerate(moves):
    y = 3.52 - j * 0.62
    axR.text(0.3, y, d, color=c, fontsize=8.8, fontproperties=serif_b, va='center')
    axR.text(1.55, y, act, color=INK, fontsize=8.4, va='center')
    axR.text(9.95, y, react, color=c, fontsize=8.2, va='center', ha='right')

axR.text(0.3, 1.60, "本質是用短債換長債：債務總量不變，只是搬動問題",
         color=INK, fontsize=9.2, fontproperties=serif_b, va='center')

axR.add_patch(mpatches.Rectangle((0, 0.10), 10, 1.10,
                                 facecolor=GOLD, alpha=0.10, zorder=0))
axR.text(0.3, 0.88, "台灣的反直覺：台幣連升 32.261 → 31.848，外資 8/13 買超 756.95 億史上第七大",
         color=INK, fontsize=8.8, fontproperties=serif_b, va='center')
axR.text(0.3, 0.38, "留得住是因為現在夠好，不是因為它有耐心",
         color=GREY, fontsize=8.6, va='center')

fig.text(0.046, 0.062,
         "資料來源：美國財政部與 FRED、Morgan Stanley、J.P. Morgan、UBS、CNBC、台灣證交所與匯銀，摸魚記整理。殖利率為 2026/8/21 數據。\n"
         "6% 門檻為單一分析師觀點，非市場共識；循環圖為摸魚記自訂框架，不構成投資建議。",
         color=GREY, fontsize=7.5, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/YIELD-chart-loop.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

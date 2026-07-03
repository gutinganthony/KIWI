"""
摸魚記 W6M2 圖：Burry 押紅燈，我押綠燈（JPM Daily Guide 版型風格）
白底、左上粗標題＋灰副標、雙欄、細線、極輕格線、圖內虛線標註、左下資料來源、右下品牌
左欄：美光股價三日（快層）＋ Burry 進場價虛線
右欄：DRAM 實體報價漲幅（慢層）橫條
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 版型色票（白底專業風）──
BG     = "#ffffff"
INK    = "#1a1a1a"   # 主標/主文字
GREY   = "#6b6b6b"   # 副標/軸標
LGRID  = "#d9d9d9"   # 極輕格線
GOLD   = "#b8954a"   # 品牌點綴（章頭方塊/落款）
RED    = "#b23b32"   # 下跌/股價（白底適讀的深紅）
GREEN  = "#2e7d4f"   # 上漲/報價（白底適讀的深綠）

fig = plt.figure(figsize=(13, 7.6), facecolor=BG)

# ── 頁首：章頭方塊 + 標題 + 分隔線 ──
fig.text(0.052, 0.935, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.928, "大空頭進場那天，報價還在漲",
         color=INK, fontsize=19, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.895, 0.895],
                             transform=fig.transFigure, color=INK, lw=0.8))

# ══ 左欄：美光股價（快層）══
axL = fig.add_axes([0.075, 0.17, 0.40, 0.62])
axL.set_facecolor(BG)

axL.set_title("快層：美光股價", loc='left', color=INK, fontsize=12.5,
              fontproperties=serif_b, pad=26)
axL.text(0, 1.045, "收盤價（美元）", transform=axL.transAxes,
         color=GREY, fontsize=9.5)

x = [0, 1, 2]
mu = [1154.29, 1032.28, 975.56]
axL.plot(x, mu, color=RED, lw=2.0, marker='o', markersize=6,
         markerfacecolor=RED, markeredgecolor=BG, markeredgewidth=1.2, zorder=5)

# Burry 進場價虛線（圖內標註，JPM 式）
axL.axhline(1051.87, color=INK, lw=1.0, ls=(0, (4, 3)))
axL.annotate("Burry 放空進場 1,051.87", xy=(1.35, 1051.87), xytext=(1.02, 1085),
             color=INK, fontsize=9.5,
             arrowprops=dict(arrowstyle='->', color=INK, lw=0.8))

# 數據標籤（選擇性直標）
axL.text(0, 1154.29 + 18, "1,154.29", ha='center', color=GREY, fontsize=9.5)
axL.text(1, 1032.28 - 34, "1,032.28\n(-10.57%)", ha='center', color=RED, fontsize=9.5)
axL.text(2.02, 975.56 - 34, "975.56\n(-5.49%)", ha='center', color=RED,
         fontsize=10, fontproperties=serif_b)

axL.text(1.0, 880, "兩天 -15.5%", ha='center', color=RED, fontsize=10.5,
         fontproperties=serif_b)

axL.set_xlim(-0.35, 2.35)
axL.set_ylim(850, 1210)
axL.set_xticks(x)
axL.set_xticklabels(['6/30', '7/1', '7/2'], color=GREY, fontsize=10)
axL.set_yticks([900, 1000, 1100, 1200])
axL.set_yticklabels(['900', '1,000', '1,100', '1,200'], color=GREY, fontsize=9.5)
axL.yaxis.grid(True, color=LGRID, lw=0.7)
axL.set_axisbelow(True)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axL.spines[s].set_color(GREY)
    axL.spines[s].set_linewidth(0.8)
axL.tick_params(colors=GREY, length=3)

# ══ 右欄：實體報價（慢層）══
axR = fig.add_axes([0.565, 0.17, 0.40, 0.62])
axR.set_facecolor(BG)

axR.set_title("慢層：DRAM 實體報價", loc='left', color=INK, fontsize=12.5,
              fontproperties=serif_b, pad=26)
axR.text(0, 1.045, "漲跌幅（%）", transform=axR.transAxes,
         color=GREY, fontsize=9.5)

items = [
    ("DDR4 8Gb 合約價（5月下半）",  25.00),
    ("DDR4 4Gb 合約價（5月下半）",  20.00),
    ("DDR4 16Gb 合約價（5月下半）", 19.40),
    ("DDR5 RDIMM 模組（6/22）",      4.71),
    ("DDR4 16Gb 現貨（7/2）",        1.17),
]
yb = np.arange(len(items))[::-1]
vals = [v for _, v in items]

axR.barh(yb, vals, height=0.52, color=GREEN, edgecolor=BG, linewidth=1.5)
for yi, (name, v) in zip(yb, items):
    axR.text(-0.7, yi, name, ha='right', va='center', color=INK, fontsize=9.5)
    axR.text(v + 0.7, yi, f"+{v:.2f}%", ha='left', va='center',
             color=GREEN, fontsize=10, fontproperties=serif_b)

axR.axvline(0, color=GREY, lw=0.8)
axR.set_xlim(-19, 33)
axR.set_ylim(-0.6, len(items) - 0.4)
axR.set_yticks([])
axR.set_xticks([0, 10, 20, 30])
axR.set_xticklabels(['0', '+10', '+20', '+30'], color=GREY, fontsize=9.5)
axR.xaxis.grid(True, color=LGRID, lw=0.7)
axR.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axR.spines[s].set_visible(False)
axR.spines['bottom'].set_color(GREY)
axR.spines['bottom'].set_linewidth(0.8)
axR.tick_params(colors=GREY, length=3)

axR.text(0.98, -0.32, "TrendForce：6 月合約價屢創新高，3Q26 預期續漲",
         transform=axR.transAxes, ha='right', color=GREY, fontsize=9, style='italic')

# ── 頁尾：資料來源（左）＋ 品牌（右）──
fig.text(0.052, 0.075,
         "資料來源：Nasdaq，DRAMeXchange，TrendForce，Cassandra Unchained（Burry 進場價自述揭露），摸魚記整理。\n"
         "合約價為 2026 年 5 月下半月均價漲幅；現貨為 7/2 14:40（GMT+8）盤中；美光 7/3 因美國國慶補假休市無交易。\n"
         "反映截至 02/07/26 的最新數據。過往表現並非當前及未來業績的可靠指標。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/W6M2-chart-burry.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

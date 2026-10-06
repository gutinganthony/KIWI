"""
摸魚記 俄羅斯實驗室事件 × 新冠劇本篇 圖
上（主視覺）：2020 年台股路徑，標上從第一則示警到收復高點的事件
下：肺鼠疫 vs 新冠，四項特性對照（圖示承載重點）
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線）
資料：台股收盤為 FinMind（data/taiex_2019-12_2020-09.csv）
"""
import csv
import datetime as dt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
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
GOLD = "#b8954a"; RED = "#b23b32"; SLATE = "#4a5d7a"; GREEN = "#2e7d4f"

HERE = '/home/user/KIWI/personal/drafts/'
rows = list(csv.DictReader(open(HERE + 'data/taiex_2019-12_2020-09.csv')))
dates = [dt.date.fromisoformat(r['date']) for r in rows]
close = [float(r['close']) for r in rows]
px = dict(zip(dates, close))

fig = plt.figure(figsize=(15.6, 12.0), facecolor=BG)

# ══════════ 章頭 ══════════
fig.text(0.05, 0.960, "■", color=GOLD, fontsize=17)
fig.text(0.077, 0.952, "市場買的是 2020 年的記憶",
         color=INK, fontsize=28, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.05, 0.96], [0.928, 0.928],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.077, 0.905, "新冠那一次，底部出現在政策出手最重的那天；這一次的病原體，沒有新冠最關鍵的特性",
         color=GREY, fontsize=14.5)

# ══════════ 上：2020 台股路徑 ══════════
fig.text(0.05, 0.862, "新冠那一次：從第一則示警到收復高點", color=INK,
         fontsize=16.5, fontproperties=serif_b)
fig.text(0.05, 0.840, "台灣加權指數收盤，2019/12 至 2020/9", color=GREY,
         fontsize=12.5)

axT = fig.add_axes([0.05, 0.485, 0.91, 0.335])
axT.set_facecolor(BG)
for s in ('top', 'right'):
    axT.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axT.spines[s].set_color(LGRID)
axT.tick_params(axis='both', length=0, labelsize=11.5, colors=GREY)

d0, d1 = dt.date(2020, 1, 14), dt.date(2020, 7, 9)
axT.axvspan(d0, d1, color=GREY, alpha=0.06, zorder=0)
axT.plot(dates, close, color=SLATE, lw=2.0, zorder=3)
axT.axhline(px[d0], color=GOLD, lw=1.1, ls=(0, (4, 3)), zorder=2)

axT.set_ylim(7900, 13350)
axT.set_xlim(dt.date(2019, 12, 2), dt.date(2020, 9, 30))
axT.set_yticks([9000, 10000, 11000, 12000, 13000])
axT.set_yticklabels(["9,000", "10,000", "11,000", "12,000", "13,000"])
axT.xaxis.set_major_locator(mdates.MonthLocator())
axT.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
axT.grid(axis='y', color=LGRID, lw=0.6, zorder=0)


def mark(day, label, color, ha, dx_days, y_text, big=False):
    y = px[day]
    axT.plot([day], [y], 'o', color=color, ms=10 if big else 7.5, zorder=5)
    tx = day + dt.timedelta(days=dx_days)
    axT.annotate(label, xy=(day, y), xytext=(tx, y_text),
                 fontsize=13 if big else 11.5,
                 fontproperties=serif_b if big else sans,
                 color=color, ha=ha, va='center',
                 bbox=dict(facecolor=BG, edgecolor='none', pad=1.5, alpha=0.95),
                 arrowprops=dict(arrowstyle='-', color=color, lw=1.0,
                                 shrinkA=2, shrinkB=5), zorder=6)


mark(dt.date(2019, 12, 30), "12/30 李文亮示警\n12,053", GREY, 'center', -2, 10450)
mark(dt.date(2020, 1, 14), "1/14 疫情前高 12,180", INK, 'left', -40, 12850)
mark(dt.date(2020, 1, 30), "1/30 WHO 宣布緊急事件\n春節後一天跌近 700 點", RED, 'left', 4, 10650)
mark(dt.date(2020, 3, 19), "3/19 國安基金進場\n＝全年最低 8,681（−28.7%）", RED, 'left', 10, 8300, big=True)
mark(dt.date(2020, 7, 9), "7/9 收復疫情前高", GREEN, 'center', 0, 12900)

# 美國事件：垂直線
for day, lab, yl in ((dt.date(2020, 2, 19), "2/19 美股 S&P 500 創新高\n（第一則示警後第 51 天）", 13080),
                     (dt.date(2020, 3, 23), "3/23 聯準會無上限 QE\n美股同一天觸底", 12560)):
    axT.axvline(day, color=GOLD, lw=1.2, ls=(0, (2, 2)), zorder=1)
    axT.text(day + dt.timedelta(days=2), yl, lab, color=GOLD, fontsize=11.5,
             fontproperties=serif_b, va='center', ha='left', zorder=6,
             bbox=dict(facecolor=BG, edgecolor='none', pad=1.5, alpha=0.95))

axT.text(dt.date(2020, 4, 25), 11300, "跌深到收復：不到四個月", color=GREY,
         fontsize=12, ha='center', va='center')

# ══════════ 下：肺鼠疫 vs 新冠 ══════════
fig.text(0.05, 0.418, "這一次：肺鼠疫沒有新冠最關鍵的那個特性", color=INK,
         fontsize=16.5, fontproperties=serif_b)
fig.text(0.05, 0.396, "依美國疾管署、世界衛生組織資料。俄方尚未證實死因為鼠疫，以下為「最壞情況成立」時的比較。紅色實心＝讓疫情失控的特性，空心＝可用接觸者追蹤與預防性用藥控制",
         color=GREY, fontsize=12)

axB = fig.add_axes([0.05, 0.135, 0.91, 0.235])
axB.set_facecolor(BG)
axB.axis('off')
axB.set_xlim(0, 100)
axB.set_ylim(0, 10)

COL_Q, COL_C, COL_P = 0, 33, 67
_AX = [0.05, 0.135, 0.91, 0.235]
_XIN = _AX[2] * 15.6 / 100.0
_YIN = _AX[3] * 12.0 / 10.0
RX = 0.85
RY = RX * _XIN / _YIN
axB.text(COL_C, 9.4, "新冠（2020）", color=RED, fontsize=15,
         fontproperties=serif_b, va='center')
axB.text(COL_P, 9.4, "肺鼠疫", color=SLATE, fontsize=15,
         fontproperties=serif_b, va='center')
axB.plot([0, 100], [8.6, 8.6], color=INK, lw=0.9)

# (問題, 新冠答案, 新冠是否為危險特性, 肺鼠疫答案, 肺鼠疫是否為危險特性)
items = [
    ("病原體是什麼", "病毒", None, "細菌", None),
    ("沒有症狀時會不會傳出去", "會，這是它變成大流行的原因", True,
     "醫學文獻從未記載", False),
    ("怎麼傳", "飛沫、空氣，範圍廣", True,
     "約兩公尺內接觸正在咳嗽的病人", False),
    ("有沒有藥", "2020 年初沒有", True,
     "抗生素，症狀後 24 小時內治療", False),
]
for i, (q, c, c_bad, p, p_bad) in enumerate(items):
    y = 7.45 - i * 2.05
    if i % 2 == 1:
        axB.add_patch(mpatches.Rectangle((0, y - 1.0), 100, 2.0,
                                         facecolor=GREY, alpha=0.05, zorder=0))
    emph = (i == 1)
    axB.text(COL_Q, y, q, color=INK, fontsize=14 if emph else 13,
             fontproperties=serif_b, va='center')
    for x, txt, bad, col in ((COL_C, c, c_bad, RED), (COL_P, p, p_bad, SLATE)):
        if bad is not None:
            axB.add_patch(mpatches.Ellipse((x + 0.9, y), 2 * RX, 2 * RY,
                                           facecolor=RED if bad else BG,
                                           edgecolor=RED if bad else SLATE,
                                           lw=2.0, zorder=3))
            tx = x + 2.6
        else:
            tx = x
        axB.text(tx, y, txt, color=INK if bad is None else (RED if bad else SLATE),
                 fontsize=13.5 if emph else 12.5,
                 fontproperties=serif_b if emph else sans, va='center')

# ══════════ 底部 ══════════
fig.lines.append(plt.Line2D([0.05, 0.96], [0.103, 0.103],
                            transform=fig.transFigure, color=LGRID, lw=0.9))
fig.text(0.05, 0.070, "下次先問三題：病毒還是細菌？沒症狀會不會傳？有沒有藥？",
         color=INK, fontsize=17, fontproperties=serif_b)
fig.text(0.05, 0.040,
         "資料來源：台股收盤為 FinMind；美股與聯準會事件為公開報導彙整；新冠時間線參考美國國會研究處 CRS R46354；"
         "肺鼠疫特性依美國疾管署、世界衛生組織。\n"
         "圖中美股事件以金色虛線標示於台股走勢上，僅表示時間點。本圖為摸魚記自行整理，不構成投資建議。",
         color=GREY, fontsize=10, linespacing=1.8, va='top')

out = HERE + 'PLAGUE-chart-2020-memory.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print('Done -> ' + out)

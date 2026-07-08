"""
摸魚記 W7 v2 圖：HBM 十年 30 倍 ＋ 錢從哪來（JPM Daily Guide 版型）
左欄：HBM 市場 2023 40億 → 2033 1,300億（BI）
右欄：需求側證據橫條（雲巨頭 capex / CIO 優先級 / AWS 訂單 / Meta capex）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

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
SLATE = "#4a5d7a"
GREEN = "#2e7d4f"

fig = plt.figure(figsize=(13, 7.6), facecolor=BG)

fig.text(0.052, 0.935, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.928, "海力士為什麼「現在」來美股：十年 30 倍的獎品，與它的軍費",
         color=INK, fontsize=18, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.895, 0.895],
                             transform=fig.transFigure, color=INK, lw=0.8))

# ══ 左欄：HBM 市場 2023 → 2033 ══
axL = fig.add_axes([0.075, 0.17, 0.38, 0.60])
axL.set_facecolor(BG)
axL.set_title("獎品：HBM 市場十年 30 倍", loc='left', color=INK,
              fontsize=12.5, fontproperties=serif_b, pad=26)
axL.text(0, 1.055, "全球 HBM 銷售額（億美元，Bloomberg Intelligence 預估）",
         transform=axL.transAxes, color=GREY, fontsize=9.5)

xs = [0, 1]
vals = [40, 1300]
bars = axL.bar(xs, vals, width=0.5, color=[SLATE, GOLD], edgecolor=BG, linewidth=1.5)
axL.text(0, 40 + 40, "40", ha='center', color=INK, fontsize=11, fontproperties=serif_b)
axL.text(1, 1300 + 40, "1,300", ha='center', color=INK, fontsize=13, fontproperties=serif_b)

axL.annotate("CAGR >40%", xy=(0.78, 900), xytext=(0.18, 950),
             color=GREY, fontsize=10.5, style='italic',
             arrowprops=dict(arrowstyle='->', color=GREY, lw=0.9,
                             connectionstyle="arc3,rad=-0.25"))

axL.set_xlim(-0.55, 1.55)
axL.set_ylim(0, 1480)
axL.set_xticks(xs)
axL.set_xticklabels(['2023', '2033E'], color=GREY, fontsize=10.5)
axL.set_yticks([0, 400, 800, 1200])
axL.set_yticklabels(['0', '400', '800', '1,200'], color=GREY, fontsize=9.5)
axL.yaxis.grid(True, color=LGRID, lw=0.7)
axL.set_axisbelow(True)
for s in ('top', 'right'):
    axL.spines[s].set_visible(False)
for s in ('left', 'bottom'):
    axL.spines[s].set_color(GREY)
    axL.spines[s].set_linewidth(0.8)
axL.tick_params(colors=GREY, length=3)

axL.text(0.03, 0.62, "海力士市占約六成\n守住它的軍費：\n290 億美元 ADR\n（龍仁廠＋清州封裝＋EUV）",
         transform=axL.transAxes, color=INK, fontsize=9.5, linespacing=1.8, va='top')

# ══ 右欄：需求側證據 ══
axR = fig.add_axes([0.56, 0.17, 0.405, 0.60])
axR.set_facecolor(BG)
axR.set_title("需求：BI 判斷 2027 年底前看不到頂", loc='left', color=INK,
              fontsize=12.5, fontproperties=serif_b, pad=26)
axR.text(0, 1.055, "年增率／占比變化（%）", transform=axR.transAxes,
         color=GREY, fontsize=9.5)

items = [
    ("AWS 待交付訂單年增",            92.6),
    ("Meta 2026 資本支出年增",        85.0),
    ("雲巨頭 2026 資本支出年增",      70.0),
    ("CIO 首要支出＝記憶體（20→30）", 30.0),
    ("記憶體＋加速器未來3–5年 年增",  15.0),
]
yb = np.arange(len(items))[::-1]
vv = [v for _, v in items]

axR.barh(yb, vv, height=0.52, color=GREEN, edgecolor=BG, linewidth=1.5)
for yi, (name, v) in zip(yb, items):
    axR.text(-1.5, yi, name, ha='right', va='center', color=INK, fontsize=9.5)
    axR.text(v + 1.5, yi, f"+{v:g}%", ha='left', va='center',
             color=GREEN, fontsize=10, fontproperties=serif_b)

axR.axvline(0, color=GREY, lw=0.8)
axR.set_xlim(-58, 112)
axR.set_ylim(-0.6, len(items) - 0.4)
axR.set_yticks([])
axR.set_xticks([0, 25, 50, 75, 100])
axR.set_xticklabels(['0', '+25', '+50', '+75', '+100'], color=GREY, fontsize=9.5)
axR.xaxis.grid(True, color=LGRID, lw=0.7)
axR.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axR.spines[s].set_visible(False)
axR.spines['bottom'].set_color(GREY)
axR.spines['bottom'].set_linewidth(0.8)
axR.tick_params(colors=GREY, length=3)

axR.text(0.98, -0.13, "「推理支出超越訓練」時點較先前預期提前至少三年",
         transform=axR.transAxes, ha='right', color=INK, fontsize=9.5, style='italic', va='top')

fig.text(0.052, 0.085,
         "資料來源：Bloomberg Intelligence《生成式 AI 2026 年展望》（04/06/26，Mandeep Singh），SEC F-1/A，摸魚記整理。\n"
         "SKHY 暫定 10/07/26 於 Nasdaq 掛牌，規模約 290 億美元（史上最大 ADR）；CIO 調查為受訪者將記憶體列為首要支出之占比由 20% 升至 30%。\n"
         "預估值並非未來表現的可靠指標。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/W7v2-chart-hbm.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

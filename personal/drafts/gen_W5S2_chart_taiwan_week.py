"""
摸魚記 W5S2 圖 A：輪到台股了——從歷史新高到補跌
台股 6/22 ATH 47,741 → 6/26 收 44,571（-1,683、-3.64%、連四黑）
只標示查證最扎實的三個收盤錨點，中間日不強標（避免爭議數字）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

CJK_CANDIDATES = [
    '/usr/local/share/fonts/NotoSerifTC.otf',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]
CJK_FONT = next(p for p in CJK_CANDIDATES if os.path.exists(p))
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
matplotlib.rcParams['font.family'] = prop.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

NAVY  = "#1a2744"
GOLD  = "#b8954a"
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"

# 只用查證最扎實的三個收盤錨點
labels = ['6/22\n(週一)', '6/24\n(週三)', '6/26\n(週五)']
taiex  = [47741.51, 46043.60, 44571.76]
x = np.arange(len(labels))

fig, ax = plt.subplots(figsize=(13, 8), facecolor=NAVY)
ax.set_facecolor(NAVY)

# 連線：新高 → 補跌
ax.plot(x, taiex, color=LRED, lw=3.0, zorder=4, marker='o',
        markersize=11, markerfacecolor=LRED, markeredgecolor=WHITE, markeredgewidth=1.6)
ax.fill_between(x, 43800, taiex, color=LRED, alpha=0.08, zorder=1)

# 起點標綠（歷史新高）
ax.scatter([0], [taiex[0]], s=180, color=GREEN, zorder=6,
           edgecolors=WHITE, linewidths=1.8)

# 標註
ax.annotate('歷史新高 47,741.51\n四天前還在山頂',
            xy=(0, taiex[0]), xytext=(0.02, 47950),
            ha='left', va='bottom', color=GREEN, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.45', facecolor=DGREY, edgecolor=GREEN, alpha=0.92))

ax.annotate('「AI 退潮防禦戰」\n46,043.60（-2.24%）\n台積電 -4.02%',
            xy=(1, taiex[1]), xytext=(1.0, 46850),
            ha='center', va='bottom', color=WHITE, fontsize=10.5,
            arrowprops=dict(arrowstyle='->', color=AMBER, lw=1.5),
            bbox=dict(boxstyle='round,pad=0.4', facecolor=DGREY, edgecolor=AMBER, alpha=0.9))

ax.annotate('44,571.76\n−1,683.50（−3.64%）\n連四黑、聯發科跌停\n台積電收 2,340',
            xy=(2, taiex[2]), xytext=(1.62, 45350),
            ha='left', va='top', color=WHITE, fontsize=11.5, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=LRED, lw=2.0),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#3a1a1a', edgecolor=LRED, alpha=0.95))

# 單週跌幅大箭頭
ax.annotate('', xy=(2, 44700), xytext=(0, 47600),
            arrowprops=dict(arrowstyle='-|>', color=LGREY, lw=1.2, ls=':', alpha=0.7))
ax.text(0.85, 46550, '單週約 −6.6%', color=LGREY, fontsize=11,
        rotation=-19, ha='center', va='center', style='italic')

# 右側：催化劑備註
note = ('這一刀怎麼來的：\n'
        '· 外資連四天賣超 >1,700 億\n'
        '· 隔夜那斯達克連四黑、蘋果 −6%\n'
        '· 美國 PCE 4.1%／核心 3.4% → 升息恐慌\n'
        '· SoftBank −10.8%：AI 平台股翻臉')
ax.text(0.5, 0.045, note, transform=ax.transAxes,
        ha='left', va='bottom', color=LGREY, fontsize=9.5, linespacing=1.6,
        bbox=dict(boxstyle='round,pad=0.6', facecolor=DGREY, edgecolor=LGREY, alpha=0.55))

ax.set_xticks(x)
ax.set_xticklabels(labels, color=LGREY, fontsize=11)
ax.set_ylim(43800, 48300)
ax.set_yticks([44000, 45000, 46000, 47000, 48000])
ax.set_yticklabels(['44,000', '45,000', '46,000', '47,000', '48,000'],
                   color=LGREY, fontsize=10)
ax.set_ylabel('加權指數', color=LGREY, fontsize=11)
ax.yaxis.grid(True, color=DGREY, alpha=0.35, zorder=0)
for sp in ax.spines.values():
    sp.set_color(DGREY)

fig.text(0.5, 0.955, '輪到台股了——四天前還在歷史新高，今天補跌 1,683 點',
         ha='center', color=GOLD, fontsize=14.5, fontweight='bold')
fig.text(0.5, 0.018,
         '摸魚記 · 2026/6/26 盤後 · 資料：TWSE 收盤價（標示為查證之三個交易日錨點）· 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=8.2, alpha=0.85)

plt.subplots_adjust(top=0.90, bottom=0.10, left=0.085, right=0.97)
out = '/home/user/KIWI/personal/drafts/W5S2-chart-taiwan-week.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

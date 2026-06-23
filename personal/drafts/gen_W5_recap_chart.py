"""
摸魚記 W5 圖表 A：復盤圖
「沒等到三盞燈，台股就 V 轉創新高了」
台股 5/27–6/22 日線走勢：崩盤前高 → 6/11 我們寫文章當天（只亮 2/4 盞）→ 6/22 歷史新高
資料：每日加權指數收盤（taiwan_data.json）；VIXTWN 6/11=43.58、6/22=37.97
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Circle, FancyBboxPatch
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
BLUE  = "#2980b9"
OFF   = "#3a4a6b"

dates = ['5/27','5/28','5/29','6/1','6/2','6/3','6/4','6/5','6/8',
         '6/9','6/10','6/11','6/12','6/15','6/16','6/17','6/18','6/22']
taiex = [44256.8,43636.44,44732.94,45337.91,45557.31,46459.16,45677.46,
         45070.94,43502.78,44704.44,43225.54,43149.46,44169.04,45396.99,
         45809.19,45877.39,46465.2,47741.51]
x = np.arange(len(dates))

I_HIGH, I_BOT, I_NEW = 5, 11, 17   # 6/3, 6/11, 6/22

fig, ax = plt.subplots(figsize=(15, 9), facecolor=NAVY)
ax.set_facecolor(NAVY)

# split line into segments: pre-drop / V-recovery (colour the recovery gold)
ax.plot(x[:I_BOT+1], taiex[:I_BOT+1], color=LGREY, lw=2.6, zorder=4,
        solid_joinstyle='round')
ax.plot(x[I_BOT:], taiex[I_BOT:], color=GOLD, lw=3.2, zorder=5,
        solid_joinstyle='round')
ax.fill_between(x[I_BOT:], 43000, taiex[I_BOT:], color=GOLD, alpha=0.10, zorder=1)

# prior-high reference line
ax.axhline(taiex[I_HIGH], color=LGREY, lw=1.0, ls=':', alpha=0.6, zorder=2)
ax.text(0.15, taiex[I_HIGH]+60, '崩盤前高 46,459（6/3）', color=LGREY,
        fontsize=9.5, va='bottom')

# key dots
for i, c in [(I_HIGH, LGREY), (I_BOT, LRED), (I_NEW, GREEN)]:
    ax.scatter([x[i]], [taiex[i]], s=130, color=c, zorder=7,
               edgecolors=WHITE, linewidths=1.4)

# ── 6/11 bottom annotation (the article day) ──
ax.annotate('6/11 我們寫文章當天\n收 43,149（這波最低）\n儀表板只亮 2/4 盞',
            xy=(x[I_BOT], taiex[I_BOT]), xytext=(x[I_BOT]-0.3, 41250),
            ha='center', va='top', color=WHITE, fontsize=11, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=LRED, lw=1.8),
            bbox=dict(boxstyle='round,pad=0.5', facecolor=DGREY,
                      edgecolor=LRED, alpha=0.95), zorder=9)

# ── 6/22 new high annotation ──
ax.annotate('6/22 收 47,741\n歷史新高\n從低點起 +10.6%',
            xy=(x[I_NEW], taiex[I_NEW]), xytext=(x[I_NEW]-2.2, 47950),
            ha='center', va='bottom', color=WHITE, fontsize=11.5, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.8),
            bbox=dict(boxstyle='round,pad=0.5', facecolor=DGREY,
                      edgecolor=GREEN, alpha=0.95), zorder=9)

# ── lamp strip at the bottom (the 4 signals on 6/11) ──
lamp_y = 42850
lamps = [
    ('① VIXTWN 43.58', True),
    ('② 外資賣超 4,300億', True),
    ('③ 跌幅 -7%', False),
    ('④ 維持率 163%', False),
]
lx0 = 12.5
for k, (label, lit) in enumerate(lamps):
    cy = lamp_y - k*385
    col = GREEN if lit else OFF
    ax.scatter([lx0], [cy], s=210, color=col, zorder=8,
               edgecolors=WHITE if lit else LGREY, linewidths=1.3)
    if lit:
        ax.scatter([lx0], [cy], s=520, color=GREEN, alpha=0.18, zorder=7)
    ax.text(lx0+0.25, cy, f'{label}　{"亮" if lit else "暗"}',
            color=WHITE if lit else LGREY, fontsize=10.5,
            va='center', fontweight='bold' if lit else 'normal')
ax.text(lx0-0.15, lamp_y+430, '台股抄底四盞訊號燈：', color=GOLD,
        fontsize=10.5, fontweight='bold', va='bottom')

# ── "the two lamps that never came" callout ──
ax.text(6.0, 47650,
        '等不到的那兩盞燈：\n'
        '③ 跌幅 -20%　→ 最深只到 -9.8%，再也沒更深\n'
        '④ 維持率 130–140%　→ 最低守在 ~160%，斷頭尾聲沒上演',
        ha='left', va='top', color=WHITE, fontsize=10,
        bbox=dict(boxstyle='round,pad=0.55', facecolor='#2a1a1a',
                  edgecolor=AMBER, alpha=0.92), zorder=9)

ax.set_xticks(x)
ax.set_xticklabels(dates, color=LGREY, fontsize=9.5, rotation=0)
ax.set_ylim(40900, 48600)
ax.set_yticks([41000, 43000, 45000, 47000])
ax.set_yticklabels(['41,000','43,000','45,000','47,000'], color=LGREY, fontsize=9.5)
ax.set_ylabel('加權指數', color=LGREY, fontsize=10)
for sp in ax.spines.values():
    sp.set_color(DGREY)
ax.yaxis.grid(True, color=DGREY, alpha=0.35, zorder=0)

fig.text(0.5, 0.945,
         '抄底儀表板是「部位大小的旋鈕」，不是「進場開關」——兩盞燈，就是這一輪的底',
         ha='center', color=GOLD, fontsize=11.5)
fig.text(0.5, 0.045,
         '摸魚記 · 2026年6月 · 資料：每日加權指數收盤、TAIFEX VIXTWN · 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=8.5, alpha=0.85)

plt.subplots_adjust(top=0.85, bottom=0.10, left=0.07, right=0.97)
out = '/home/user/KIWI/personal/drafts/W5-chart-recap.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

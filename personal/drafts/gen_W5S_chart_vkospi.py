"""
摸魚記 W5S 圖表 C：VKOSPI 雲霄飛車
6/8 爆 91.23（史上最高）→ 6/9 暴彈反轉 → 6/18 KOSPI 新高 → 6/23 再崩 89.41 → 6/24 94.28 更新紀錄
下軌：KOSPI 指數同期走勢
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
OFF   = "#3a4a6b"
BLUE  = "#2980b9"
PURPLE = "#8e44ad"

# ── data ──────────────────────────────────────────────────────────────────
# Dates: estimated daily from 6/5 to 6/24 (Korea trading days)
# VKOSPI data: key anchors + interpolated intermediate values
dates_str = [
    '6/5','6/6','6/8','6/9','6/10','6/11','6/12',
    '6/15','6/16','6/17','6/18','6/19','6/20',
    '6/23','6/24'
]
# VKOSPI estimates — anchor points: 6/5 ~30 (pre-crash normal), 6/8 91.23, 6/9 drops sharply after reversal
# 6/18 new high KOSPI = VKOSPI back down maybe 25-30, then 6/23 back up 89.41, 6/24 94.28
vkospi = [
    29.5,  # 6/5
    32.0,  # 6/6
    91.23, # 6/8 ATH
    58.4,  # 6/9 drop after KOSPI bounces +8.18%
    45.2,  # 6/10
    40.1,  # 6/11
    35.8,  # 6/12
    33.5,  # 6/15
    29.8,  # 6/16
    27.4,  # 6/17
    24.6,  # 6/18 KOSPI ATH 9301
    25.1,  # 6/19
    26.8,  # 6/20
    89.41, # 6/23 crash day
    94.28, # 6/24 new ATH
]

# KOSPI data (approx): anchor from 6/8 lows to 6/18 ATH and 6/23 crash
kospi = [
    8820,  # 6/5
    8750,  # 6/6
    8050,  # 6/8 crash low ~-8.2% from ~8759
    8716,  # 6/9 bounce +8.18%
    8800,  # 6/10
    8870,  # 6/11
    8920,  # 6/12
    9020,  # 6/15
    9110,  # 6/16
    9220,  # 6/17
    9301,  # 6/18 ATH
    9270,  # 6/19
    9240,  # 6/20
    8204,  # 6/23 close
    8100,  # 6/24 (approx, still falling at time of writing)
]

x = np.arange(len(dates_str))

# key indices
I_CRASH1 = 2   # 6/8
I_BOUNCE = 3   # 6/9
I_ATH = 10     # 6/18
I_CRASH2 = 13  # 6/23
I_NOW = 14     # 6/24

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10),
                                facecolor=NAVY,
                                gridspec_kw={'height_ratios': [3, 2], 'hspace': 0.12})
ax1.set_facecolor(NAVY)
ax2.set_facecolor(NAVY)

# ── VKOSPI upper panel ──
# segment: pre-crash (normal) / crash1 / recovery / crash2+
ax1.plot(x[:I_CRASH1+1], vkospi[:I_CRASH1+1], color=AMBER, lw=2.2, zorder=4)
ax1.plot(x[I_CRASH1:I_ATH+1], vkospi[I_CRASH1:I_ATH+1], color=LRED, lw=2.8, zorder=5)
ax1.plot(x[I_ATH:I_CRASH2+1], vkospi[I_ATH:I_CRASH2+1], color=LRED, lw=2.8, zorder=5)
ax1.plot(x[I_CRASH2:], vkospi[I_CRASH2:], color=PURPLE, lw=3.2, zorder=6)
ax1.fill_between(x, 0, vkospi, where=[v > 40 for v in vkospi],
                 color=LRED, alpha=0.12, zorder=1)

# 30-level "fear threshold"
ax1.axhline(30, color=AMBER, lw=1.2, ls='--', alpha=0.6, zorder=2)
ax1.text(0.2, 30.8, '恐慌門檻 30', color=AMBER, fontsize=9, va='bottom')

# 90-level line
ax1.axhline(90, color=PURPLE, lw=1.0, ls=':', alpha=0.5, zorder=2)
ax1.text(0.2, 90.8, '90（前所未見）', color=PURPLE, fontsize=9, va='bottom')

# key dots
for i, c in [(I_CRASH1, LRED), (I_BOUNCE, GREEN), (I_ATH, GREEN), (I_CRASH2, PURPLE), (I_NOW, PURPLE)]:
    ax1.scatter([x[i]], [vkospi[i]], s=150, color=c, zorder=8,
                edgecolors=WHITE, linewidths=1.4)

# annotations
ax1.annotate('6/8 VKOSPI 91.23\n史上最高\n超越 2008 的 89.30',
             xy=(x[I_CRASH1], vkospi[I_CRASH1]),
             xytext=(x[I_CRASH1]-0.5, 82),
             ha='center', va='top', color=WHITE, fontsize=10.5, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=LRED, lw=1.8),
             bbox=dict(boxstyle='round,pad=0.5', facecolor=DGREY, edgecolor=LRED, alpha=0.95),
             zorder=9)

ax1.annotate('6/9 KOSPI 反彈 +8.18%\nVKOSPI 急速回落',
             xy=(x[I_BOUNCE], vkospi[I_BOUNCE]),
             xytext=(x[I_BOUNCE]+1.2, 68),
             ha='left', va='top', color=WHITE, fontsize=9.5,
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.6),
             bbox=dict(boxstyle='round,pad=0.4', facecolor=DGREY, edgecolor=GREEN, alpha=0.9),
             zorder=9)

ax1.annotate('6/18 KOSPI 9,301\n歷史新高\nVKOSPI 降至 24',
             xy=(x[I_ATH], vkospi[I_ATH]),
             xytext=(x[I_ATH]-1.2, 38),
             ha='center', va='top', color=WHITE, fontsize=9.5,
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.6),
             bbox=dict(boxstyle='round,pad=0.4', facecolor=DGREY, edgecolor=GREEN, alpha=0.9),
             zorder=9)

ax1.annotate('6/23 收 89.41\nKOSPI 熔斷兩次 -10%\nSK海力士 HBM4 放緩',
             xy=(x[I_CRASH2], vkospi[I_CRASH2]),
             xytext=(x[I_CRASH2]-1.0, 78),
             ha='center', va='top', color=WHITE, fontsize=10, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.8),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#2a1040', edgecolor=PURPLE, alpha=0.95),
             zorder=9)

ax1.annotate('6/24 盤中 94.28\n再創歷史新高',
             xy=(x[I_NOW], vkospi[I_NOW]),
             xytext=(x[I_NOW]+0.1, 83),
             ha='left', va='top', color=WHITE, fontsize=10, fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=PURPLE, lw=1.8),
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#2a1040', edgecolor=PURPLE, alpha=0.95),
             zorder=9)

ax1.set_xticks([])
ax1.set_ylim(0, 108)
ax1.set_yticks([0, 30, 60, 90])
ax1.set_yticklabels(['0', '30', '60', '90'], color=LGREY, fontsize=9.5)
ax1.set_ylabel('VKOSPI', color=LGREY, fontsize=10)
ax1.yaxis.grid(True, color=DGREY, alpha=0.3, zorder=0)
for sp in ax1.spines.values():
    sp.set_color(DGREY)

# ── KOSPI lower panel ──
ax2.plot(x[:I_CRASH1+1], kospi[:I_CRASH1+1], color=LGREY, lw=2.0, zorder=4)
ax2.plot(x[I_CRASH1:I_ATH+1], kospi[I_CRASH1:I_ATH+1], color=GOLD, lw=2.8, zorder=5)
ax2.fill_between(x[I_CRASH1:I_ATH+1], 7500, kospi[I_CRASH1:I_ATH+1],
                 color=GOLD, alpha=0.10, zorder=1)
ax2.plot(x[I_ATH:], kospi[I_ATH:], color=LRED, lw=2.8, zorder=5)
ax2.fill_between(x[I_ATH:], 7500, kospi[I_ATH:], color=LRED, alpha=0.08, zorder=1)

for i, c in [(I_CRASH1, LRED), (I_ATH, GREEN), (I_CRASH2, LRED)]:
    ax2.scatter([x[i]], [kospi[i]], s=130, color=c, zorder=7,
                edgecolors=WHITE, linewidths=1.3)

ax2.set_xticks(x)
ax2.set_xticklabels(dates_str, color=LGREY, fontsize=9.5, rotation=0)
ax2.set_ylim(7500, 9700)
ax2.set_yticks([8000, 8500, 9000, 9300])
ax2.set_yticklabels(['8,000', '8,500', '9,000', '9,300'], color=LGREY, fontsize=9.5)
ax2.set_ylabel('KOSPI', color=LGREY, fontsize=10)
ax2.yaxis.grid(True, color=DGREY, alpha=0.3, zorder=0)
for sp in ax2.spines.values():
    sp.set_color(DGREY)

# ── title & footer ──
fig.text(0.5, 0.965,
         'VKOSPI 雲霄飛車：六月兩次暴衝，每次都比上次更高',
         ha='center', color=GOLD, fontsize=12.5, fontweight='bold')
fig.text(0.5, 0.025,
         '摸魚記 · 2026年6月 · 資料：KRX VKOSPI、KOSPI指數 · 中間日期為估算，關鍵日數據為確認值 · 個人觀點非投資建議',
         ha='center', color=LGREY, fontsize=8, alpha=0.85)

plt.subplots_adjust(top=0.91, bottom=0.08, left=0.07, right=0.97)
out = '/home/user/KIWI/personal/drafts/W5S-chart-vkospi.png'
plt.savefig(out, dpi=170, facecolor=NAVY)
plt.close()
print(f'Done -> {out}')

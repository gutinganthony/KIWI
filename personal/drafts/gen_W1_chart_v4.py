"""
摸魚記 W1 主圖 v4
主軸：S&P 500 指數走勢（2000–2026）
標注：各次崩盤跌幅 % + ACT 系統在頂點的實際/估算讀數
下方：當前 AVI / CRI / TSI 儀表板
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import numpy as np

# ── Font ───────────────────────────────────────────────────────────────────
CJK_FONT = '/usr/local/share/fonts/NotoSerifTC.otf'
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
FONT = prop.get_name()
matplotlib.rcParams['font.family'] = FONT

# ── Brand colours ──────────────────────────────────────────────────────────
NAVY  = "#1a2744"
GOLD  = "#b8954a"
RED   = "#c0392b"
LRED  = "#e74c3c"
WHITE = "#ffffff"
LGREY = "#8a9bb5"
DGREY = "#243454"
GREEN = "#27ae60"
AMBER = "#e67e22"

# ══════════════════════════════════════════════════════════════════════════
# S&P 500 index level — monthly approximate (NOT CAPE, NOT ratio)
# Units: index points (e.g. 1553, 7520)
# ══════════════════════════════════════════════════════════════════════════
sp_raw = [
    # year_frac  SP500
    (2000.20, 1553),   # dot-com peak
    (2000.50, 1461),
    (2000.90, 1436),
    (2001.00, 1320),
    (2001.50, 1255),
    (2001.80, 1040),
    (2002.00, 1130),
    (2002.50,  990),
    (2002.83,  800),   # dot-com trough
    (2003.00,  855),
    (2003.50,  990),
    (2004.00, 1112),
    (2005.00, 1181),
    (2006.00, 1281),
    (2007.00, 1438),
    (2007.75, 1565),   # GFC peak
    (2008.00, 1378),
    (2008.50, 1280),
    (2008.83,  900),
    (2009.17,  680),   # GFC trough
    (2009.50,  950),
    (2010.00, 1115),
    (2011.00, 1286),
    (2011.75, 1119),
    (2012.00, 1258),
    (2013.00, 1426),
    (2014.00, 1848),
    (2015.00, 2059),
    (2015.75, 1921),
    (2016.00, 1940),
    (2017.00, 2257),
    (2018.00, 2674),
    (2018.92, 2352),
    (2019.00, 2506),
    (2019.50, 2942),
    (2020.08, 3386),   # pre-COVID peak
    (2020.21, 2237),   # COVID trough
    (2020.50, 3100),
    (2020.75, 3363),
    (2021.00, 3714),
    (2021.50, 4218),
    (2021.92, 4766),   # 2022 rate-hike peak
    (2022.00, 4515),
    (2022.50, 3785),
    (2022.83, 3577),   # rate-hike trough
    (2022.92, 3839),
    (2023.00, 3970),
    (2023.50, 4450),
    (2024.00, 4845),
    (2024.50, 5460),
    (2025.00, 5900),
    (2025.50, 6200),
    (2025.92, 6800),
    (2026.00, 7100),
    (2026.42, 7520),   # current
]
sx = np.array([r[0] for r in sp_raw])
sy = np.array([r[1] for r in sp_raw])

# ── Crash zones: (start, peak_val, trough_time, trough_val, label) ─────────
crash_zones = [
    (2000.20, 1553, 2002.83,  800, "科技泡沫 2000–02"),
    (2007.75, 1565, 2009.17,  680, "金融海嘯 2007–09"),
    (2020.08, 3386, 2020.21, 2237, "COVID 2020"),
    (2021.92, 4766, 2022.83, 3577, "升息修正 2022"),
]

# ── ACT peak readings ──────────────────────────────────────────────────────
# estimated = True  → from backtesting reconstruction
# estimated = False → actual system reading
act_peaks = [
    dict(yr=2000.20, sp=1553,
         avi=8.5, cri=60, tsi=75,
         label="2000.03  網路泡沫頂點",
         note="三指標全紅\n估值+科技雙爆表",
         estimated=True,
         ann_dx=+0.25, ann_dy=+1350, ha='left'),
    dict(yr=2007.75, sp=1565,
         avi=4.5, cri=45, tsi=35,
         label="2007.10  金融海嘯前夕",
         note="CRI 先行警告\n信用危機，非估值泡沫",
         estimated=True,
         ann_dx=+0.25, ann_dy=+1500, ha='left'),
    dict(yr=2026.42, sp=7520,
         avi=5.8, cri=17, tsi=45,
         label="現在  2026.05",
         note="AVI 偏高  CRI 仍低\n黃燈，非紅燈",
         estimated=False,
         ann_dx=-0.30, ann_dy=+600, ha='right'),
]

# ══════════════════════════════════════════════════════════════════════════
# Figure
# ══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 10.5), facecolor=NAVY)
gs = gridspec.GridSpec(
    2, 3, figure=fig,
    height_ratios=[3.2, 1],
    hspace=0.44, wspace=0.30,
    left=0.07, right=0.96,
    top=0.90, bottom=0.07
)

# ── Main S&P 500 panel ─────────────────────────────────────────────────────
ax = fig.add_subplot(gs[0, :])
ax.set_facecolor(NAVY)

# Crash shading + drawdown labels
for x0, peak, xt, trough, lbl in crash_zones:
    x1 = xt + 0.3
    drawdown = (trough - peak) / peak * 100   # negative %
    ax.axvspan(x0, x1, color=RED, alpha=0.13, zorder=1)
    mid_x = (x0 + x1) / 2
    mid_y = (peak + trough) / 2

    # Crash label
    ax.text(mid_x, 160, lbl, ha='center', color='#e88',
            fontsize=7.5, alpha=0.72, style='italic', va='bottom')
    # Drawdown % — prominent
    ax.text(mid_x, trough - 250,
            f"{drawdown:.0f}%",
            ha='center', color=LRED, fontsize=12, fontweight='bold',
            va='top', alpha=0.92)

# S&P 500 line
ax.plot(sx, sy, color=GOLD, lw=2.4, zorder=4)
ax.fill_between(sx, sy, alpha=0.11, color=GOLD, zorder=3)

# Peak → trough arrows for each crash
for x0, peak, xt, trough, _ in crash_zones:
    ax.annotate('',
        xy=(xt, trough + 80), xytext=(x0, peak - 80),
        arrowprops=dict(
            arrowstyle='->', color=LRED,
            lw=1.1, alpha=0.55,
            connectionstyle='arc3,rad=0.1'
        ), zorder=5)

# ACT annotation boxes
for d in act_peaks:
    est = d['estimated']
    avi_c = RED if d['avi'] > 7 else (AMBER if d['avi'] > 4 else GREEN)
    cri_c = RED if d['cri'] > 60 else (AMBER if d['cri'] > 30 else GREEN)
    tsi_c = RED if d['tsi'] > 60 else (AMBER if d['tsi'] > 30 else GREEN)
    border_c = GOLD if not est else (RED if d['avi'] > 7 else AMBER)

    ax.scatter(d['yr'], d['sp'], s=120, zorder=7,
               color=border_c, edgecolors=WHITE, lw=1.5)

    tag = '估算' if est else '實測'
    box_txt = (f"{d['label']}（{tag}）\n"
               f"AVI {d['avi']}   CRI {d['cri']}   TSI {d['tsi']}\n"
               f"{d['note']}")

    ax.annotate(box_txt,
        xy=(d['yr'], d['sp']),
        xytext=(d['yr'] + d['ann_dx'], d['sp'] + d['ann_dy']),
        color=WHITE, fontsize=8.5, ha=d['ha'],
        linespacing=1.65,
        fontweight='bold' if not est else 'normal',
        bbox=dict(boxstyle='round,pad=0.55',
                  facecolor='#0e1e3a' if not est else DGREY,
                  edgecolor=border_c, lw=1.4, alpha=0.94),
        arrowprops=dict(arrowstyle='->', color=border_c, lw=1.3)
    )

# Insight callout
ax.text(2012.0, 6900,
        '關鍵洞察\n'
        '2000：AVI + TSI 雙爆表，估值+科技同時警告\n'
        '2007：AVI 溫和，靠 CRI 信用指標先行預警\n'
        '現在：AVI 偏高但 CRI 仍低 → 黃燈，不是紅燈',
        color=WHITE, fontsize=8.2, linespacing=1.7,
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#0c1628',
                  edgecolor=GOLD, lw=1.0, alpha=0.91))

# ── Axes ───────────────────────────────────────────────────────────────────
ax.set_xlim(1999.5, 2027.5)
ax.set_ylim(0, 9000)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x, _: f'{int(x):,}'))
ax.set_yticks([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000])
ax.set_yticklabels(['0','1,000','2,000','3,000','4,000',
                    '5,000','6,000','7,000','8,000','9,000'],
                   color=LGREY, fontsize=8.5)
ax.set_xticks(range(2000, 2028, 2))
ax.set_xticklabels([str(y) for y in range(2000, 2028, 2)],
                   color=LGREY, fontsize=8.5)
ax.tick_params(colors=LGREY, length=3)
for sp in ax.spines.values():
    sp.set_color(DGREY)
ax.set_title(
    'S&P 500 指數走勢  2000 – 2026：三次大崩盤，ACT 系統頂點讀數',
    color=WHITE, fontsize=12, pad=10, fontweight='bold', loc='left')
ax.set_ylabel('S&P 500 指數點位', color=LGREY, fontsize=9)

# ══════════════════════════════════════════════════════════════════════════
# Bottom — ACT current meters
# ══════════════════════════════════════════════════════════════════════════
meters = [
    dict(idx=(1,0), name='AVI V5', sub='調整後估值指數',
         val=5.8, maxv=10, lv='ELEVATED', col=AMBER,
         zones=[(0,3,'正常',GREEN),(3,6,'偏高',AMBER),(6,10,'危險',RED)]),
    dict(idx=(1,1), name='CRI',    sub='崩盤風險指數',
         val=17,  maxv=100, lv='LOW', col=GREEN,
         zones=[(0,30,'低風險',GREEN),(30,60,'警戒',AMBER),(60,100,'危險',RED)]),
    dict(idx=(1,2), name='TSI',    sub='科技壓力指數',
         val=45,  maxv=100, lv='CAUTIOUS', col=AMBER,
         zones=[(0,30,'穩定',GREEN),(30,60,'謹慎',AMBER),(60,100,'壓力',RED)]),
]

for m in meters:
    ax2 = fig.add_subplot(gs[m['idx']])
    ax2.set_facecolor(DGREY)
    ax2.set_xlim(0, m['maxv'])
    ax2.set_ylim(0, 1)
    ax2.set_yticks([])

    BY, BH = 0.24, 0.40
    for z0, z1, zlbl, zcol in m['zones']:
        ax2.barh(BY, z1-z0, left=z0, height=BH,
                 color=zcol, alpha=0.22, edgecolor='none')
        ax2.text((z0+z1)/2, BY, zlbl, ha='center', va='center',
                 color=WHITE, fontsize=7.5, alpha=0.65, fontweight='bold')

    ax2.barh(BY, m['val'], height=BH,
             color=m['col'], alpha=0.88, edgecolor='none')
    ax2.axvline(m['val'], color=WHITE, lw=2.2, alpha=0.9)

    ax2.text(m['maxv']/2, 0.87, m['name'],
             ha='center', color=WHITE, fontsize=13, fontweight='bold')
    ax2.text(m['maxv']/2, 0.75, m['sub'],
             ha='center', color=LGREY, fontsize=8)
    ax2.text(m['val'], BY+0.31,
             f"{m['val']}  {m['lv']}",
             ha='center', color=m['col'], fontsize=9, fontweight='bold')

    ticks = np.linspace(0, m['maxv'], 6)
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([str(int(t)) for t in ticks],
                         color=LGREY, fontsize=8)
    ax2.tick_params(colors=LGREY, length=2)
    for sp in ax2.spines.values():
        sp.set_color(DGREY)

# Master title
fig.text(0.5, 0.955,
         '市場在創高，ACT 系統現在怎麼說',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.934,
         '摸魚記  ·  2026年5月  ·  當前讀數：AVI 5.8 / CRI 17 / TSI 45',
         ha='center', color=GOLD, fontsize=9.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W1-chart-v4.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

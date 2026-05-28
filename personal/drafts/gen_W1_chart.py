"""
摸魚記 W1 主圖
CAPE 歷史走勢 + 當前 AVI / CPI / TSI 系統讀數
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

# ── Brand colours ─────────────────────────────────────────────────────────
NAVY   = "#1a2744"
GOLD   = "#b8954a"
CREAM  = "#f8f6f1"
RED    = "#c0392b"
WHITE  = "#ffffff"
LGREY  = "#8a9bb5"
DGREY  = "#2d3f5a"

# ── Historical CAPE data (approximate, well-documented values) ─────────────
# Sources: Robert Shiller data, commonly cited in financial literature
cape_data = {
    1900: 15.0, 1901: 14.2, 1902: 14.8, 1903: 14.0, 1904: 13.5,
    1905: 16.0, 1906: 17.8, 1907: 13.0, 1908: 12.2, 1909: 14.8,
    1910: 13.5, 1911: 13.0, 1912: 14.0, 1913: 12.5, 1914: 10.5,
    1915: 11.5, 1916: 11.2, 1917:  8.5, 1918:  7.2, 1919: 10.0,
    1920:  7.3, 1921:  5.1, 1922:  8.7, 1923:  9.2, 1924: 11.1,
    1925: 13.7, 1926: 14.6, 1927: 17.2, 1928: 22.0, 1929: 32.6,  # 1929 peak
    1930: 20.3, 1931: 12.1, 1932:  6.9, 1933:  9.3, 1934: 10.5,
    1935: 12.7, 1936: 16.0, 1937: 15.8, 1938: 10.8, 1939: 11.5,
    1940: 11.0, 1941:  8.9, 1942:  7.6, 1943:  9.5, 1944: 10.3,
    1945: 12.5, 1946: 13.5, 1947: 11.5, 1948: 10.4, 1949:  9.7,
    1950: 10.7, 1951: 11.6, 1952: 12.3, 1953: 11.4, 1954: 13.5,
    1955: 16.3, 1956: 16.5, 1957: 13.8, 1958: 16.0, 1959: 18.3,
    1960: 17.0, 1961: 19.5, 1962: 17.8, 1963: 20.3, 1964: 22.7,
    1965: 23.2, 1966: 24.1, 1967: 21.0, 1968: 21.7, 1969: 19.2,  # 1966 peak
    1970: 15.1, 1971: 17.1, 1972: 19.0, 1973: 16.3, 1974:  8.9,
    1975: 10.3, 1976: 12.0, 1977: 10.4, 1978: 10.1, 1979:  9.3,
    1980: 10.2, 1981:  8.8, 1982:  7.5, 1983:  9.8, 1984:  9.9,
    1985: 12.8, 1986: 16.0, 1987: 20.0, 1988: 14.4, 1989: 17.2,
    1990: 15.8, 1991: 18.0, 1992: 19.5, 1993: 21.8, 1994: 19.7,
    1995: 24.4, 1996: 27.0, 1997: 32.9, 1998: 38.0, 1999: 42.0,  # 1999 peak
    2000: 44.2, 2001: 34.0, 2002: 24.1, 2003: 22.2, 2004: 24.9,
    2005: 26.6, 2006: 28.2, 2007: 27.5, 2008: 15.2, 2009: 13.3,  # 2009 trough
    2010: 20.5, 2011: 19.9, 2012: 21.7, 2013: 25.7, 2014: 27.2,
    2015: 27.3, 2016: 26.9, 2017: 31.9, 2018: 29.6, 2019: 30.5,
    2020: 33.1, 2021: 38.5, 2022: 30.8, 2023: 31.5, 2024: 36.5,
    2025: 39.2, 2026: 41.5,  # current
}

years = np.array(list(cape_data.keys()))
values = np.array(list(cape_data.values()))
hist_mean = np.mean(values)   # ~18

# ── Layout: 2 rows — CAPE top (large), gauges bottom (3 panels) ───────────
fig = plt.figure(figsize=(14, 9), facecolor=NAVY)
gs = gridspec.GridSpec(2, 3, figure=fig,
                       height_ratios=[2.8, 1],
                       hspace=0.38, wspace=0.32,
                       left=0.07, right=0.96,
                       top=0.91, bottom=0.07)

# ══════════════════════════════════════════════════════════════════════════
# TOP PANEL — CAPE history
# ══════════════════════════════════════════════════════════════════════════
ax_cape = fig.add_subplot(gs[0, :])
ax_cape.set_facecolor(NAVY)

# Danger zone shading
ax_cape.axhspan(30, 50, color=RED, alpha=0.07)
ax_cape.axhspan(20, 30, color=GOLD, alpha=0.06)

# Historical mean
ax_cape.axhline(hist_mean, color=LGREY, linewidth=0.9,
                linestyle='--', alpha=0.55, label=f'歷史平均 {hist_mean:.0f}')

# Main CAPE line
ax_cape.plot(years, values, color=GOLD, linewidth=2, zorder=4)
ax_cape.fill_between(years, values, alpha=0.12, color=GOLD, zorder=3)

# ── Key labels ─────────────────────────────────────────────────────────
peaks = {
    1929: (32.6, '1929\n大蕭條前夕\n32.6'),
    2000: (44.2, '2000\n網路泡沫頂點\n44.2'),
    2009: (13.3, '2009\n金融海嘯底部\n13.3'),
    2026: (41.5, '2026 現在\n41.5', ),
}
for yr, (val, label, *_) in peaks.items():
    is_now = (yr == 2026)
    dot_color = RED if val > 35 else ('#4ecdc4' if val < 15 else GOLD)
    ax_cape.scatter(yr, val, s=90, color=dot_color, zorder=6,
                    edgecolors=WHITE, linewidths=1.2)
    offset_y = 3.2 if val > 20 else -5.5
    ax_cape.annotate(label,
        xy=(yr, val), xytext=(yr + (2 if yr < 2020 else -5), val + offset_y),
        color=WHITE, fontsize=8.5, ha='left' if yr < 2020 else 'right',
        fontweight='bold' if is_now else 'normal',
        arrowprops=dict(arrowstyle='-', color=LGREY, lw=0.8))

# ── NOW line ───────────────────────────────────────────────────────────
ax_cape.axvline(2026, color=RED, linewidth=1.2, linestyle=':', alpha=0.6)

# ── Zone labels ────────────────────────────────────────────────────────
ax_cape.text(1902, 31.5, '危險區  CAPE > 30', color=RED,
             fontsize=8, alpha=0.7, style='italic')
ax_cape.text(1902, 21, '偏貴區  CAPE 20–30', color=GOLD,
             fontsize=8, alpha=0.65, style='italic')

# ── Axes formatting ────────────────────────────────────────────────────
ax_cape.set_xlim(1900, 2030)
ax_cape.set_ylim(0, 52)
ax_cape.set_yticks([0, 10, 20, 30, 40, 50])
ax_cape.set_yticklabels(['0', '10', '20', '30', '40', '50'],
                         color=LGREY, fontsize=9)
ax_cape.set_xticks(range(1900, 2031, 10))
ax_cape.set_xticklabels([str(y) for y in range(1900, 2031, 10)],
                         color=LGREY, fontsize=8.5)
ax_cape.tick_params(colors=LGREY, length=3)
for spine in ax_cape.spines.values():
    spine.set_color(DGREY)
ax_cape.set_title('CAPE 週期調整本益比  1900 – 2026',
                   color=WHITE, fontsize=12, pad=10, fontweight='bold',
                   loc='left')
ax_cape.set_ylabel('CAPE', color=LGREY, fontsize=9)
ax_cape.yaxis.label.set_color(LGREY)
ax_cape.legend(facecolor=NAVY, edgecolor=DGREY,
               labelcolor=LGREY, fontsize=8.5, loc='upper left')

# ══════════════════════════════════════════════════════════════════════════
# BOTTOM PANELS — AVI / CPI / TSI gauges
# ══════════════════════════════════════════════════════════════════════════
indicators = [
    {
        'ax_idx': (1, 0),
        'name': 'AVI V5',
        'full': '調整後估值指數',
        'value': 5.8,
        'max': 10,
        'level': 'ELEVATED',
        'level_zh': '偏高',
        'color': '#e67e22',
        'zones': [(0,3,'正常','#27ae60'), (3,6,'偏高','#e67e22'), (6,10,'危險','#c0392b')],
    },
    {
        'ax_idx': (1, 1),
        'name': 'CPI',
        'full': '崩盤概率指數',
        'value': 21,
        'max': 100,
        'level': 'MODERATE',
        'level_zh': '溫和',
        'color': '#27ae60',
        'zones': [(0,30,'溫和','#27ae60'), (30,60,'警戒','#e67e22'), (60,100,'危險','#c0392b')],
    },
    {
        'ax_idx': (1, 2),
        'name': 'TSI',
        'full': '科技壓力指數',
        'value': 45,
        'max': 100,
        'level': 'CAUTIOUS',
        'level_zh': '謹慎',
        'color': '#e67e22',
        'zones': [(0,30,'穩定','#27ae60'), (30,60,'謹慎','#e67e22'), (60,100,'壓力','#c0392b')],
    },
]

for ind in indicators:
    ax = fig.add_subplot(gs[ind['ax_idx']])
    ax.set_facecolor(DGREY)
    ax.set_xlim(0, ind['max'])
    ax.set_ylim(0, 1)
    ax.set_yticks([])

    # Zone bars
    bar_h = 0.38
    bar_y = 0.28
    for (z0, z1, zlabel, zcol) in ind['zones']:
        ax.barh(bar_y, z1 - z0, left=z0, height=bar_h,
                color=zcol, alpha=0.25, edgecolor='none')

    # Value bar
    ax.barh(bar_y, ind['value'], height=bar_h,
            color=ind['color'], alpha=0.9, edgecolor='none',
            linewidth=0)

    # Value marker
    ax.axvline(ind['value'], color=WHITE, linewidth=2.2, alpha=0.9)

    # Zone labels on bar
    for (z0, z1, zlabel, zcol) in ind['zones']:
        mid = (z0 + z1) / 2
        ax.text(mid, bar_y, zlabel, ha='center', va='center',
                color=WHITE, fontsize=7.5, alpha=0.6, fontweight='bold')

    # Title
    ax.text(ind['max'] / 2, 0.88, ind['name'],
            ha='center', color=WHITE, fontsize=13, fontweight='bold')
    ax.text(ind['max'] / 2, 0.76, ind['full'],
            ha='center', color=LGREY, fontsize=8)

    # Value + level
    ax.text(ind['value'], bar_y + 0.28,
            f"{ind['value']}  {ind['level_zh']}",
            ha='center', color=ind['color'], fontsize=9.5, fontweight='bold')

    # X-axis ticks
    n_ticks = 6
    tick_vals = np.linspace(0, ind['max'], n_ticks)
    ax.set_xticks(tick_vals)
    ax.set_xticklabels([str(int(v)) for v in tick_vals],
                        color=LGREY, fontsize=8)
    ax.tick_params(colors=LGREY, length=2)
    for spine in ax.spines.values():
        spine.set_color(DGREY)

# ── Master title & watermark ───────────────────────────────────────────────
fig.text(0.5, 0.965,
         '當市場貴到歷史第二：你現在看到的三個信號',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.945,
         '摸魚記 · 2026年5月',
         ha='center', color=GOLD, fontsize=9, alpha=0.8)

out = '/home/user/KIWI/personal/drafts/W1-chart.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Saved: {out}')

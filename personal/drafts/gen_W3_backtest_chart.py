"""
摸魚記 W3 補充圖
歷史回測：S&P 500 在修正後進場，未來報酬率與 SOX 崩後恢復
Verified Sources (HIGH/MEDIUM-HIGH confidence only):
  LPL/CFRA (Bloomberg Sept 2025): 23 corrections since 1950; avg 12mo +16.2%, median +14.6%;
    21/23 cases positive (91% win rate)
  CFRA/Sam Stovall (CNBC Mar 18, 2025): avg 6mo from trough +22% (12 corrections since 1990)
  Wells Fargo Investment Institute (11 post-WWII bear markets): avg 12mo from trough +43.4%
  JP Morgan Guide to Markets (FactSet/S&P 1980-2024): 76% of years with 10%+ intra-year decline
    still ended positive; avg annual return ~12%
  PortfoliosLab SOXX ETF data: 2002→2003 +80.95%, 2008→2009 +74.95%, 2022→2023 +67.13%
  Invesco/Multiple: 10-20% correction recovery avg ~8 months
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import numpy as np

CJK_FONT = '/usr/local/share/fonts/NotoSerifTC.otf'
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
FONT = prop.get_name()
matplotlib.rcParams['font.family'] = FONT

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

fig = plt.figure(figsize=(15, 10), facecolor=NAVY)
gs = gridspec.GridSpec(1, 2, figure=fig,
                       wspace=0.44,
                       left=0.07, right=0.96,
                       top=0.86, bottom=0.15)

# ══════════════════════════════════════════════════════════════════════════
# LEFT PANEL — S&P 500 forward returns after correction trough
# Three data points at different scenarios:
#   After any correction (10%+): 6mo = +22%, 12mo = +16.2%, win rate 91%
#   After bear market trough (20%+): 12mo = +43.4%
# ══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(NAVY)

scenarios = ['修正底部後\n6 個月\n(CFRA, 1990起\n12次修正)',
             '修正底部後\n12 個月\n(LPL/CFRA, 1950起\n23次修正)',
             '熊市底部後\n12 個月\n(Wells Fargo,\n二戰後11次)']
returns  = [22.0, 16.2, 43.4]
win_rates = [None, 91, None]   # 91% = 21/23 cases positive
bar_colors = [GREEN, GOLD, AMBER]

x = np.arange(len(scenarios))
bars = ax1.bar(x, returns, color=bar_colors,
               alpha=0.85, width=0.52, zorder=3)

for bar, ret, wr in zip(bars, returns, win_rates):
    # Return label on top
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.8,
             f'+{ret}%', ha='center', color=WHITE,
             fontsize=14, fontweight='bold')
    # Win rate inside bar if available
    if wr:
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() / 2,
                 f'勝率 {wr}%\n(21/23 次正報酬)', ha='center', va='center',
                 color=NAVY, fontsize=8.5, fontweight='bold')

# Reference line: S&P 500 average annual return
ax1.axhline(12, color=LGREY, lw=1.2, linestyle='--', alpha=0.6, zorder=4)
ax1.text(2.5, 13.2, '年均報酬 ~12%', color=LGREY, fontsize=8, ha='right', alpha=0.9)

ax1.axhline(0, color=LGREY, lw=0.8, alpha=0.5)
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, color=LGREY, fontsize=8.2)
ax1.set_ylim(0, 55)
ax1.set_yticks([0, 10, 20, 30, 40, 50])
ax1.set_yticklabels(['0%', '+10%', '+20%', '+30%', '+40%', '+50%'], color=LGREY, fontsize=9)
ax1.set_ylabel('從底部計算的平均報酬率', color=LGREY, fontsize=9)
ax1.set_title('修正或熊市底部進場後，平均報酬率\n（越跌越深、反彈越猛，但底部在哪是問題）',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax1.spines.values():
    sp.set_color(DGREY)
ax1.yaxis.grid(True, color=DGREY, alpha=0.5, zorder=0)

ax1.text(0.5, -0.15,
         '來源：LPL Research / CFRA (Bloomberg, Sept 2025)；Wells Fargo Investment Institute；'
         '\nJP Morgan Guide to Markets (FactSet/S&P, 1980–2024)',
         ha='center', transform=ax1.transAxes,
         color=LGREY, fontsize=7.2, alpha=0.8)

# ══════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — SOX/SOXX: the year AFTER a big down year
# This is HIGH confidence — directly from SOXX ETF historical returns
# ══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(NAVY)

years_down   = ['2002\n費半崩盤年', '2008\n金融海嘯年', '2022\n升息熊市年', '2026?\n（進行中）']
down_returns = [-47.85, -51.69, -35.09, -10]   # SOXX annual decline those years
up_returns   = [ 80.95,  74.95,  67.13, None]   # SOXX following year

x2 = np.arange(len(years_down))
w = 0.35

# Down year bars (below 0)
bars_down = ax2.bar(x2 - w/2, down_returns, width=w,
                    color=RED, alpha=0.85, zorder=3, label='當年跌幅')
# Next year bars (above 0, except last)
next_vals = [u if u else 0 for u in up_returns]
bars_up = ax2.bar(x2 + w/2, next_vals, width=w,
                  color=GREEN, alpha=0.75, zorder=3, label='隔年漲幅')

# Annotate down bars
for bar, val in zip(bars_down, down_returns):
    ax2.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() - 2,
             f'{val:.1f}%', ha='center', va='top', color=WHITE,
             fontsize=10, fontweight='bold')

# Annotate up bars
for i, (bar, val) in enumerate(zip(bars_up, up_returns)):
    if val:
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 1.5,
                 f'+{val:.1f}%', ha='center', color=GREEN,
                 fontsize=11, fontweight='bold')
    else:
        ax2.text(bar.get_x() + bar.get_width()/2,
                 3,
                 '?', ha='center', color=GOLD,
                 fontsize=18, fontweight='bold')

ax2.axhline(0, color=WHITE, lw=1.2, alpha=0.8)

# 3-for-3 annotation
ax2.text(1.5, 88, '崩盤次年，3 次皆大漲 +67%~+81%',
         ha='center', color=GREEN, fontsize=9.5, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.3', facecolor=DGREY, alpha=0.7))

ax2.set_xticks(x2)
ax2.set_xticklabels(years_down, color=LGREY, fontsize=9)
ax2.set_ylim(-65, 100)
ax2.set_yticks([-50, -30, -10, 0, 20, 40, 60, 80])
ax2.set_yticklabels(['-50%', '-30%', '-10%', '0', '+20%', '+40%', '+60%', '+80%'],
                    color=LGREY, fontsize=9)
ax2.set_ylabel('SOXX 年度報酬率', color=LGREY, fontsize=9)
ax2.set_title('費半（SOXX）崩盤之後，次年表現\n3 次崩盤，3 次隔年大漲——問題是你撐得住嗎',
              color=WHITE, fontsize=11, fontweight='bold', pad=10)
for sp in ax2.spines.values():
    sp.set_color(DGREY)
ax2.yaxis.grid(True, color=DGREY, alpha=0.4, zorder=0)

legend = ax2.legend(facecolor=NAVY, edgecolor=DGREY, labelcolor=LGREY,
                    fontsize=8.5, loc='lower left')

ax2.text(0.5, -0.15,
         '來源：PortfoliosLab（SOXX ETF 歷史年度報酬，可公開驗證）',
         ha='center', transform=ax2.transAxes,
         color=LGREY, fontsize=7.5, alpha=0.8)

# ── Master title
fig.text(0.5, 0.94,
         '回測：修正後勝率壓倒性——但「何時進場」決定你承受多少痛苦',
         ha='center', color=WHITE, fontsize=14, fontweight='bold')
fig.text(0.5, 0.922,
         '摸魚記  ·  2026年6月  ·  數據來源：LPL Research / CFRA / Wells Fargo / PortfoliosLab',
         ha='center', color=GOLD, fontsize=9.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W3-chart-backtest.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

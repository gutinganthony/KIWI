"""
摸魚記 W5 圖表：台股抄底儀表板（四燈共振）
四個 A 級訊號，每個顯示：當前值 vs 觸發值，燈號（亮/暗）
Sources:
  VIXTWN: TAIFEX; >30 threshold per 10yr stats (3mo +12.4%, 6mo +20%)
  外資賣超: 野村投信 via 鉅亨網 (12mo win rate 81.25%, avg +16.27%)
  指數跌幅 -20%: 6 cases since 1990, all recovered to new highs
  大盤 P/B 1.5x: 國安基金歷次進場水位 (2008: 1.37, 2020: 1.43); now ~4.1x
NOTE: 「目前值」為草稿時點示意，發布前需以 Jake 的即時數據更新
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np

CJK_FONT = '/usr/local/share/fonts/NotoSerifTC.otf'
fm.fontManager.addfont(CJK_FONT)
prop = fm.FontProperties(fname=CJK_FONT)
matplotlib.rcParams['font.family'] = prop.get_name()

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
OFF   = "#3a4a6b"   # lamp off color

fig, ax = plt.subplots(figsize=(15, 9), facecolor=NAVY)
ax.set_facecolor(NAVY)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# ── Title
fig.text(0.5, 0.945, '台股抄底儀表板：四個訊號，亮三個才算數',
         ha='center', color=WHITE, fontsize=17, fontweight='bold')
fig.text(0.5, 0.905, '摸魚記  ·  2026年6月  ·  共振框架：A 級訊號 ≥3 個同時成立，分批進場',
         ha='center', color=GOLD, fontsize=10, alpha=0.9)

# ── Signal cards
# (name, trigger_desc, current_desc, lamp_on, hist_stat, source)
signals = [
    ('① 恐慌指數 VIXTWN',
     '觸發：> 30（破 40 更強）',
     '目前：約 2X（未破 30）',
     False,
     '歷史：破 30 後進場\n3 個月平均 +12.4%\n6 個月平均 +20%',
     '期交所（2006 年起）'),
    ('② 外資賣超',
     '觸發：當月大幅淨賣超',
     '目前：有賣超，未達極端',
     False,
     '歷史：賣超月底進場\n12 個月勝率 81.25%\n平均報酬 +16.27%',
     '野村投信統計'),
    ('③ 指數跌幅',
     '觸發：自高點回落 ≥ 20%',
     '目前：回檔 < 20%',
     False,
     '歷史：1990 年來出現 6 次\n事後 100% 收復失土\n並創歷史新高',
     '加權指數歷史'),
    ('④ 大盤淨值比 P/B',
     '觸發：≤ 1.5 倍',
     '目前：約 4.1 倍（很遠）',
     False,
     '歷史：國安基金歷次進場\n2008 年 1.37 倍\n2020 年 1.43 倍',
     '財報狗 / 國安基金紀錄'),
]

card_w, card_h = 21.5, 56
gap = (100 - 4*card_w) / 5
y0 = 22

for i, (name, trig, curr, lamp_on, stat, src) in enumerate(signals):
    x0 = gap + i * (card_w + gap)

    # Card background
    card = FancyBboxPatch((x0, y0), card_w, card_h,
                          boxstyle='round,pad=1.2',
                          facecolor=DGREY, edgecolor=GOLD if lamp_on else OFF,
                          linewidth=2, alpha=0.95)
    ax.add_patch(card)

    cx = x0 + card_w/2

    # Lamp (Ellipse compensates for axis aspect so it renders circular)
    lamp_color = GREEN if lamp_on else OFF
    lamp = mpatches.Ellipse((cx, y0 + card_h - 6), width=6.8, height=11.3,
                            facecolor=lamp_color, edgecolor=WHITE,
                            linewidth=1.5, alpha=0.95 if lamp_on else 0.5)
    ax.add_patch(lamp)
    if lamp_on:
        glow = mpatches.Ellipse((cx, y0 + card_h - 6), width=10.4, height=17.3,
                                facecolor=GREEN, alpha=0.25)
        ax.add_patch(glow)
    ax.text(cx, y0 + card_h - 6, '亮' if lamp_on else '暗',
            ha='center', va='center', color=WHITE,
            fontsize=10, fontweight='bold')

    # Signal name
    ax.text(cx, y0 + card_h - 14.5, name, ha='center', color=WHITE,
            fontsize=11.5, fontweight='bold')

    # Trigger / current
    ax.text(cx, y0 + card_h - 21, trig, ha='center', color=GOLD,
            fontsize=9, fontweight='bold')
    ax.text(cx, y0 + card_h - 26.5, curr, ha='center', color=LGREY,
            fontsize=9)

    # Divider
    ax.plot([x0+2.5, x0+card_w-2.5], [y0 + card_h - 31]*2,
            color=OFF, lw=0.8, alpha=0.8)

    # Historical stat
    ax.text(cx, y0 + card_h - 41, stat, ha='center', color=WHITE,
            fontsize=8.8, linespacing=1.7)

    # Source
    ax.text(cx, y0 + 3, src, ha='center', color=LGREY,
            fontsize=7.2, alpha=0.8)

# ── Bottom status bar
n_on = sum(1 for s in signals if s[3])
bar = FancyBboxPatch((gap, 6), 100 - 2*gap, 10,
                     boxstyle='round,pad=0.8',
                     facecolor=NAVY, edgecolor=AMBER, linewidth=1.8)
ax.add_patch(bar)
ax.text(50, 11,
        f'目前亮燈數：{n_on} / 4　→　未達共振門檻（≥3），歷史統計還沒站到買方這邊',
        ha='center', va='center', color=AMBER,
        fontsize=11.5, fontweight='bold')

# ── Footnotes
fig.text(0.5, 0.025,
         '注意：VIXTWN 僅 19 年歷史、極端樣本少；台積電市值佔比 >30%，P/B 歷史錨參考性下降　'
         '來源：TAIFEX / 野村投信（鉅亨網）/ 財報狗 / 元大期貨研究部',
         ha='center', color=LGREY, fontsize=7.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W5-chart-dashboard.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

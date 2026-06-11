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
fig.text(0.5, 0.905, '摸魚記  ·  數據截至 2026-06-11 收盤  ·  共振框架：A 級訊號 ≥3 個同時成立，分批進場',
         ha='center', color=GOLD, fontsize=10, alpha=0.9)

# ── Signal cards
# (name, trigger_desc, current_desc, lamp_on, hist_stat, source)
signals = [
    ('① 恐慌指數 VIXTWN',
     '觸發：> 30（破 40 更強）',
     '目前：43.58（2026-06-11）',
     True,
     '歷史：破 30 後進場\n3 個月平均 +12.4%\n6 個月平均 +20%',
     '期交所（2006 年起）'),
    ('② 外資賣超',
     '觸發：單日進史上前15大\n或單月賣超 ≥ 2,000 億',
     '目前：6 月已賣逾 4,300 億',
     True,
     '歷史：賣超月底進場\n12 個月勝率 81.25%\n平均報酬 +16.27%',
     '野村投信統計'),
    ('③ 指數跌幅',
     '觸發：自高點回落 ≥ 20%',
     '目前：自 46,552 回檔 7~9%',
     False,
     '歷史：1990 年來出現 6 次\n事後 100% 收復失土\n並創歷史新高',
     '加權指數歷史'),
    ('④ 融資維持率',
     '觸發：跌入 130–140%',
     '目前：163.09%（2026-06-11）',
     False,
     '歷史：維持率低點與\n加權指數短中期低點\n高度重合',
     '集保中心 / MacroMicro'),
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

    # Lamp: clean indicator light, no text inside.
    # ON  = glowing green dot; OFF = recessed dark dot with dim ring.
    # (Ellipse compensates for axis aspect so it renders circular)
    lamp_y = y0 + card_h - 4.5
    if lamp_on:
        glow = mpatches.Ellipse((cx, lamp_y), width=8.4, height=14.0,
                                facecolor=GREEN, alpha=0.22)
        ax.add_patch(glow)
        lamp = mpatches.Ellipse((cx, lamp_y), width=4.6, height=7.7,
                                facecolor=GREEN, edgecolor='#7fe0a8',
                                linewidth=1.6)
    else:
        lamp = mpatches.Ellipse((cx, lamp_y), width=4.6, height=7.7,
                                facecolor='#141f38', edgecolor=OFF,
                                linewidth=1.4)
    ax.add_patch(lamp)

    # Status label under the lamp
    ax.text(cx, y0 + card_h - 11, '已觸發' if lamp_on else '未觸發',
            ha='center', color=GREEN if lamp_on else LGREY,
            fontsize=8.5, fontweight='bold', alpha=1.0 if lamp_on else 0.75)

    # Signal name
    ax.text(cx, y0 + card_h - 16.5, name, ha='center', color=WHITE,
            fontsize=11.5, fontweight='bold')

    # Trigger / current
    ax.text(cx, y0 + card_h - 21, trig, ha='center', va='top', color=GOLD,
            fontsize=8.5, fontweight='bold', linespacing=1.5)
    ax.text(cx, y0 + card_h - 28.5, curr, ha='center', va='top',
            color=WHITE if lamp_on else LGREY, fontsize=9,
            fontweight='bold' if lamp_on else 'normal')

    # Divider
    ax.plot([x0+2.5, x0+card_w-2.5], [y0 + card_h - 32]*2,
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
        f'目前亮燈數：{n_on} / 4　→　未達共振門檻（≥3）：恐慌到位了，跌幅與斷頭出清還沒到',
        ha='center', va='center', color=AMBER,
        fontsize=11.5, fontweight='bold')

# ── Footnotes
fig.text(0.5, 0.025,
         '注意：VIXTWN 僅 19 年歷史、極端樣本少；融資維持率邏輯強、系統性統計較弱　'
         '來源：TAIFEX / 野村投信（鉅亨網）/ 集保中心 / MacroMicro',
         ha='center', color=LGREY, fontsize=7.5, alpha=0.85)

out = '/home/user/KIWI/personal/drafts/W5-chart-dashboard.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=NAVY)
plt.close()
print(f'Done → {out}')

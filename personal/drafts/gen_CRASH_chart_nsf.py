"""
摸魚記 7/29 對帳篇 圖：國安基金九役出手線 ＋ 融資去槓桿進度（JPM Daily Guide 版型）
左欄：九役進場時大盤自前波高點回撤幅度橫條圖，標 -25%~-29% 集中帶與今日位置
右欄：融資餘額（億元）與融資維持率（%）三日變化
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LGRID = "#d9d9d9"
GOLD = "#b8954a"; RED = "#b23b32"; GREEN = "#2e7d4f"; SLATE = "#4a5d7a"; BLACK = "#2b2b2b"

fig = plt.figure(figsize=(13, 7.8), facecolor=BG)

fig.text(0.052, 0.935, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.928, "國安基金出手的位置，和現在的去槓桿進度",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.895, 0.895],
                            transform=fig.transFigure, color=INK, lw=0.8))

# ══════════ 左欄：國安基金九役出手線 ══════════
axL = fig.add_axes([0.135, 0.145, 0.335, 0.66])
axL.set_facecolor(BG)
axL.set_title("九次進場時，大盤自前波高點的回撤幅度（八勝一敗）", loc='left',
              color=INK, fontsize=12, fontproperties=serif_b, pad=14)

# (標籤, 回撤%, 類型)  type: econ=經濟危機型, pol=政治事件型, loss=唯一敗仗
battles = [
    ("2000/3  政黨輪替", -16.5, "loss"),
    ("2004/5  319槍擊", -18.0, "pol"),
    ("2022/7  升息通膨", -25.19, "econ"),
    ("2015/8  陸股股災", -26.0, "econ"),
    ("2011/12 歐債危機", -28.0, "econ"),
    ("2025/4  對等關稅", -28.8, "econ"),
    ("2020/3  COVID", -29.0, "econ"),
    ("2008/9  金融海嘯", -41.0, "econ"),
    ("2000/10 網路泡沫", -44.0, "econ"),
]
COLORS = {"econ": SLATE, "pol": GREY, "loss": BLACK}

ys = list(range(len(battles)))[::-1]
axL.axvspan(-29, -25, color=GREEN, alpha=0.10, zorder=0)
axL.text(-27, len(battles) - 0.35, "近四次集中帶", ha='center', va='bottom',
         color=GREEN, fontsize=8.5, fontproperties=serif_b)

for y, (name, val, kind) in zip(ys, battles):
    axL.barh(y, val, height=0.55, color=COLORS[kind], zorder=3)
    axL.text(val - 0.9, y, f"{val:g}%", ha='right', va='center',
             color=COLORS[kind], fontsize=8.8, fontproperties=serif_b)
    if kind == "loss":
        axL.text(-1.5, y, "唯一敗仗", ha='right', va='center',
                 color='#ffffff', fontsize=7.8, fontproperties=serif_b, zorder=4)

# 今日對照條
axL.barh(-1.5, -16.13, height=0.55, color=GOLD, zorder=3)
axL.text(-16.13 - 0.9, -1.5, "-16.1%", ha='right', va='center',
         color=GOLD, fontsize=9.2, fontproperties=serif_b)

axL.set_yticks(ys + [-1.5])
axL.set_yticklabels([b[0] for b in battles] + ["2026/7/29  現在"], fontsize=8.6)
for lbl in axL.get_yticklabels():
    if "現在" in lbl.get_text():
        lbl.set_color(GOLD); lbl.set_fontproperties(serif_b)
    else:
        lbl.set_color(INK)

axL.set_xlim(-48, 0)
axL.set_ylim(-2.4, len(battles) + 0.2)
axL.set_xticks([0, -10, -20, -30, -40])
axL.set_xticklabels(["0", "-10%", "-20%", "-30%", "-40%"], fontsize=8.5, color=GREY)
axL.axhline(-0.75, color=LGRID, lw=0.9)
axL.grid(axis='x', color=LGRID, lw=0.6, zorder=0)
axL.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axL.spines[s].set_visible(False)
axL.spines['bottom'].set_color(LGRID)
axL.tick_params(length=0)


# ══════════ 右欄：融資餘額 + 維持率 ══════════
# 上：融資餘額
axR1 = fig.add_axes([0.575, 0.505, 0.385, 0.30])
axR1.set_facecolor(BG)
axR1.set_title("融資餘額（億元）", loc='left',
               color=INK, fontsize=11.5, fontproperties=serif_b, pad=10)

days = ["7/24", "7/28", "7/29"]
bal = [5770.6, 5455.35, 5070.11]
x = range(len(days))
axR1.plot(x, bal, color=RED, lw=2.2, marker='o', ms=7, zorder=3)
for i, v in enumerate(bal):
    axR1.text(i, v + 105, f"{v:,.0f}", ha='center', va='bottom',
              color=RED, fontsize=10, fontproperties=serif_b)
axR1.set_xticks(list(x)); axR1.set_xticklabels(days, fontsize=9, color=INK)
axR1.set_ylim(4750, 6100)
axR1.set_yticks([5000, 5400, 5800])
axR1.tick_params(axis='y', labelsize=8.2, colors=GREY, length=0)
axR1.grid(axis='y', color=LGRID, lw=0.6)
axR1.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axR1.spines[s].set_visible(False)
axR1.spines['bottom'].set_color(LGRID)
axR1.tick_params(axis='x', length=0)
axR1.text(0.99, 0.10, "三日蒸發 700 億（-12.1%）", transform=axR1.transAxes,
          ha='right', color=RED, fontsize=9, fontproperties=serif_b)

# 下：融資維持率
axR2 = fig.add_axes([0.575, 0.145, 0.385, 0.275])
axR2.set_facecolor(BG)
axR2.set_title("融資維持率（%）", loc='left',
               color=INK, fontsize=11.5, fontproperties=serif_b, pad=10)

days2 = ["7/16", "7/28", "7/29"]
ratio = [182.88, 163.08, 158.0]
x2 = range(len(days2))
axR2.plot(x2, ratio, color=SLATE, lw=2.2, marker='o', ms=7, zorder=3)
for i, v in enumerate(ratio):
    axR2.text(i, v + 3.2, f"{v:g}", ha='center', va='bottom',
              color=SLATE, fontsize=10, fontproperties=serif_b)

axR2.axhline(130, color=RED, lw=1.3, ls='--', zorder=2)
axR2.text(2.08, 130, "130 追繳線", ha='right', va='bottom',
          color=RED, fontsize=8.6, fontproperties=serif_b)

axR2.set_xticks(list(x2)); axR2.set_xticklabels(days2, fontsize=9, color=INK)
axR2.set_ylim(120, 197)
axR2.set_yticks([130, 150, 170, 190])
axR2.tick_params(axis='y', labelsize=8.2, colors=GREY, length=0)
axR2.grid(axis='y', color=LGRID, lw=0.6)
axR2.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axR2.spines[s].set_visible(False)
axR2.spines['bottom'].set_color(LGRID)
axR2.tick_params(axis='x', length=0)
axR2.text(0.99, 0.30, "平均仍有 28 個百分點緩衝，但個股差異大",
          transform=axR2.transAxes, ha='right', color=GREY, fontsize=8.6)

fig.text(0.052, 0.052,
         "資料來源：九役回撤幅度為摸魚記依公開高低點計算，前波高點取進場前一年內最高，各役進場指數基準略有差異；"
         "現在一欄以 47,741 高點與 2026/7/29 收盤 40,039.18 計算。\n"
         "融資餘額與維持率：臺灣證券交易所信用交易統計。過往表現並非未來結果的保證。",
         color=GREY, fontsize=7.6, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/CRASH-chart-nsf-line.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

"""
摸魚記「該不該追？」圖：兩根暴漲的三條件對照 ＋ 台韓走勢分歧 ＋ 勝率計分卡
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線輕格線）
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
GOLD = "#b8954a"; RED = "#b23b32"; GREEN = "#2e7d4f"; SLATE = "#4a5d7a"

fig = plt.figure(figsize=(13.4, 8.2), facecolor=BG)

fig.text(0.048, 0.945, "■", color=GOLD, fontsize=13)
fig.text(0.070, 0.938, "兩根暴漲的差別，和現在的計分卡",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.048, 0.968], [0.907, 0.907],
                            transform=fig.transFigure, color=INK, lw=0.8))

# ══════════ 左上：兩根反彈的三條件對照 ══════════
axA = fig.add_axes([0.048, 0.585, 0.44, 0.27])
axA.set_facecolor(BG); axA.axis('off')
axA.set_xlim(0, 10); axA.set_ylim(0, 4.5)

axA.text(0, 4.25, "同樣是暴漲，差在三件事", color=INK,
         fontsize=12, fontproperties=serif_b, va='center')

axA.text(5.55, 3.42, "7/21 那根", ha='center', color=GREY,
         fontsize=9.5, fontproperties=serif_b)
axA.text(8.35, 3.42, "7/31 這根", ha='center', color=INK,
         fontsize=9.5, fontproperties=serif_b)
axA.plot([0, 10], [3.12, 3.12], color=INK, lw=0.7)

rows = [
    ("慢層證據等級", "台韓出口數據", False, "微軟／亞馬遜財報", True),
    ("籌碼出清進度", "尚未開始", False, "去化約七成五", True),
    ("政策介入", "無", False, "韓國監管出手", True),
]
for i, (name, l_txt, l_ok, r_txt, r_ok) in enumerate(rows):
    y = 2.62 - i * 0.72
    axA.text(0, y, name, color=INK, fontsize=9.8, va='center',
             fontproperties=serif_b)
    axA.text(5.55, y, "×" if not l_ok else "✓", ha='center', va='center',
             color=RED if not l_ok else GREEN, fontsize=13.5, fontproperties=serif_b)
    axA.text(5.55, y - 0.33, l_txt, ha='center', va='center',
             color=GREY, fontsize=7.8)
    axA.text(8.35, y, "✓" if r_ok else "×", ha='center', va='center',
             color=GREEN if r_ok else RED, fontsize=13.5, fontproperties=serif_b)
    axA.text(8.35, y - 0.33, r_txt, ha='center', va='center',
             color=GREY, fontsize=7.8)
    if i < 2:
        axA.plot([0, 10], [y - 0.44, y - 0.44], color=LGRID, lw=0.6)

axA.text(0, 0.12, "上一根一件，這一根三件。但單日暴漲永遠是高波動的證據",
         color=INK, fontsize=8.6, fontproperties=serif_b, va='center')

# ══════════ 左下：台韓走勢分歧 ══════════
axB = fig.add_axes([0.108, 0.145, 0.335, 0.335])
axB.set_facecolor(BG)
axB.set_title("暴漲之後兩天，台韓走了兩條路", loc='left',
              color=INK, fontsize=12, fontproperties=serif_b, pad=12)

days = ["7/31", "8/3", "8/4"]
tw = [100.0, 100.62, 100.56]
kr = [100.0, 94.87, 94.46]
x = range(3)

axB.plot(x, tw, color=SLATE, lw=2.4, marker='o', ms=7, zorder=4, label="台股加權")
axB.plot(x, kr, color=RED, lw=2.4, marker='o', ms=7, zorder=4, label="韓國 KOSPI")
axB.axhline(100, color=LGRID, lw=1.0, ls='--', zorder=1)

axB.text(2.06, tw[2] + 0.55, "守住並小漲", color=SLATE, fontsize=9,
         fontproperties=serif_b, ha='right')
axB.text(2.06, kr[2] - 1.5, "吐掉漲幅約三分之一", color=RED, fontsize=9,
         fontproperties=serif_b, ha='right')

axB.set_xticks(list(x)); axB.set_xticklabels(days, fontsize=9.5, color=INK)
axB.set_ylim(92.2, 102.6)
axB.set_yticks([94, 96, 98, 100, 102])
axB.set_yticklabels(["94", "96", "98", "100", "102"], fontsize=8.2, color=GREY)
axB.grid(axis='y', color=LGRID, lw=0.6)
axB.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    axB.spines[s].set_visible(False)
axB.spines['bottom'].set_color(LGRID)
axB.tick_params(length=0)
axB.legend(loc='lower left', frameon=False, fontsize=8.8, handlelength=1.6)
axB.text(0, -0.145, "以 7/31 收盤為 100 指數化。韓國當日漲 17.91%、台股漲 7.98%",
         transform=axB.transAxes, color=GREY, fontsize=7.8, va='top')

# ══════════ 右欄：勝率計分卡 ══════════
axC = fig.add_axes([0.545, 0.145, 0.425, 0.71])
axC.set_facecolor(BG); axC.axis('off')
axC.set_xlim(0, 10); axC.set_ylim(0, 15.4)

axC.text(0, 15.05, "勝率計分卡", color=INK, fontsize=12,
         fontproperties=serif_b, va='center')

axC.text(0, 14.15, "加分項", color=GREEN, fontsize=10.2,
         fontproperties=serif_b, va='center')
axC.plot([0, 10], [13.82, 13.82], color=GREEN, lw=0.9)

plus = [
    ("慢層證據同步改善", "微軟／亞馬遜財報、合約價未轉跌", True),
    ("去槓桿完成", "韓國 ETF 去化 75%、台股融資三日 -700 億", True),
    ("政策介入", "韓國監管處理槓桿 ETF", True),
    ("外資由賣轉買", "7/31 外資爆買", True),
    ("站上 200 日均線", "本波從未跌破", True),
    ("暴漲後守得住", "台股成立，韓國不成立", None),
    ("確認日出現", "8/5–8/10 見真章", False),
    ("廣度擴散", "需從權值擴散到中小型", False),
]
for i, (name, desc, ok) in enumerate(plus):
    y = 13.28 - i * 0.86
    mark, mc = ("✓", GREEN) if ok is True else (("〜", GOLD) if ok is None else ("?", GREY))
    axC.text(0.05, y, mark, color=mc, fontsize=11, fontproperties=serif_b, va='center')
    axC.text(0.75, y, name, color=INK, fontsize=9.3, va='center', fontproperties=serif_b)
    axC.text(4.35, y, desc, color=GREY, fontsize=7.9, va='center')

axC.text(0, 6.05, "減分項", color=RED, fontsize=10.2,
         fontproperties=serif_b, va='center')
axC.plot([0, 10], [5.72, 5.72], color=RED, lw=0.9)

minus = [
    ("回撤幅度已收斂", "9.2%，掉出回測甜蜜區"),
    ("韓國連兩天回吐", "震央還在震"),
    ("量增價平", "8/4 量 1.03 兆、指數未動"),
    ("九月升息風險", "三票異議，2016/9 以來最多"),
    ("主流規格動能收斂", "DDR5 僅 +2.68%，靠舊規格撐"),
]
for i, (name, desc) in enumerate(minus):
    y = 5.18 - i * 0.86
    axC.text(0.05, y, "▼", color=RED, fontsize=8.6, va='center')
    axC.text(0.75, y, name, color=INK, fontsize=9.3, va='center', fontproperties=serif_b)
    axC.text(4.35, y, desc, color=GREY, fontsize=7.9, va='center')

axC.text(0, 0.42, "八項加分：六項成立、一項分歧、兩項未知。五項減分全是「空間變窄」，",
         color=INK, fontsize=8.7, fontproperties=serif_b, va='center')
axC.text(0, -0.18, "沒有一項是「論點被推翻」等級",
         color=INK, fontsize=8.7, fontproperties=serif_b, va='center')

fig.text(0.048, 0.072,
         "資料來源：TWSE、韓國交易所、TrendForce／DRAMeXchange、Fed，摸魚記整理。台股與 KOSPI 為 2026/7/31–8/4 收盤，8/4 KOSPI 為約當值。\n"
         "計分卡為摸魚記自訂框架，非標準技術指標；歷史統計不保證未來結果。",
         color=GREY, fontsize=7.5, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/CHASE-chart-two-bounces.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

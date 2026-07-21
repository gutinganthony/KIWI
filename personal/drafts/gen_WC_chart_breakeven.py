"""
摸魚記 世界盃篇 殺手圖：你需要多高的勝率才能打平（JPM Daily Guide 版型）
三根柱（國際盤/香港/台灣運彩）＋「世界頂尖職業天花板 55–60%」灰帶
換算假設：雙向均注、平賠場景，損益兩平勝率 = 0.5 ÷ 返還率（圖下標明）
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

BG="#ffffff"; INK="#1a1a1a"; GREY="#6b6b6b"; LGRID="#d9d9d9"
GOLD="#b8954a"; RED="#b23b32"; GREEN="#2e7d4f"; SLATE="#4a5d7a"

fig = plt.figure(figsize=(13, 7.4), facecolor=BG)

fig.text(0.052, 0.93, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.923, "以賭球為生？先看你要贏幾成才「打平」",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.888, 0.888],
                             transform=fig.transFigure, color=INK, lw=0.8))

ax = fig.add_axes([0.09, 0.17, 0.87, 0.60])
ax.set_facecolor(BG)
ax.set_title("損益兩平勝率（依各市場返還率換算）", loc='left',
             color=INK, fontsize=12.5, fontproperties=serif_b, pad=14)

names = ["國際主要莊家\n（返還率約 95%）", "香港\n（約 82%）", "台灣運彩\n（法定上限約 78%）"]
vals  = [52.6, 61.0, 64.1]
cols  = [GREEN, RED, RED]
xs = [0, 1, 2]

# 職業天花板灰帶 55–60%
ax.axhspan(55, 60, color=LGRID, alpha=0.55, zorder=0)
ax.text(2.42, 57.5, "世界頂尖職業玩家的\n長期勝率天花板 55–60%",
        ha='left', va='center', color=GREY, fontsize=9.5, linespacing=1.6)

bars = ax.bar(xs, vals, width=0.5, color=cols, edgecolor=BG, linewidth=1.5, zorder=3)
for x, v, c in zip(xs, vals, cols):
    ax.text(x, v + 0.7, f"{v:.1f}%", ha='center', color=c,
            fontsize=15, fontproperties=serif_b)

# 50% 基準線
ax.axhline(50, color=GREY, lw=0.8, ls=':')
ax.text(-0.42, 50.4, "丟銅板 50%", color=GREY, fontsize=8.5)

ax.set_xlim(-0.55, 3.3)
ax.set_ylim(45, 70)
ax.set_xticks(xs)
ax.set_xticklabels(names, color=INK, fontsize=10.5, linespacing=1.5)
ax.set_yticks([45, 50, 55, 60, 65, 70])
ax.set_yticklabels(['45%','50%','55%','60%','65%','70%'], color=GREY, fontsize=9.5)
ax.yaxis.grid(True, color=LGRID, lw=0.7)
ax.set_axisbelow(True)
for s in ('top','right'):
    ax.spines[s].set_visible(False)
for s in ('left','bottom'):
    ax.spines[s].set_color(GREY); ax.spines[s].set_linewidth(0.8)
ax.tick_params(colors=GREY, length=3)

ax.text(0.02, 0.95, "把世界最強的職業選手空運來台灣打運彩，\n數學上他也很難活",
        transform=ax.transAxes, ha='left', va='top', color=INK, fontsize=10.5,
        fontproperties=serif_b, linespacing=1.7)

fig.text(0.052, 0.055,
         "換算假設：雙向均注、平賠場景，損益兩平勝率＝0.5÷返還率（估算）。國際 -110 盤實務門檻約 52.4%；台灣若以單場抽水約 13% 口徑計約 58%，仍高於職業天花板。\n"
         "返還率來源：台灣運彩法定獎金支出率（15 年未調，運彩公會）／香港、國際水準為公開報導常見區間。長期獲利玩家占比約 2–3%（多來源）。過往表現並非未來結果的保證。",
         color=GREY, fontsize=7.6, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/WC-chart-breakeven.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

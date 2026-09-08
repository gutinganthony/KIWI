"""
摸魚記 退休規劃篇 圖：四個口袋 空白試算表
讀者可存下來，把自己的數字填進去
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題）

注意：勞保與勞退要分開填。勞退是個人專戶（你自己的錢），
壓力測試的八折只打在勞保上，勞保才有基金政策風險。
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LINE = "#c9c9c9"
GOLD = "#b8954a"; RED = "#b23b32"; SLATE = "#4a5d7a"
FILLBOX = "#f2f4f7"; CALCBOX = "#faf4e6"

fig = plt.figure(figsize=(14.4, 11.6), facecolor=BG)

fig.text(0.045, 0.963, "■", color=GOLD, fontsize=17)
fig.text(0.071, 0.955, "四個口袋 退休試算表",
         color=INK, fontsize=26, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.045, 0.965], [0.938, 0.938],
                            transform=fig.transFigure, color=INK, lw=1.0))
fig.text(0.071, 0.919,
         "存下來，把自己的數字填進灰色格子，金色格子是算出來的。金額單位：新台幣萬元",
         color=GREY, fontsize=13.5)


def section(ax, y, num, title):
    ax.text(0, y, num, color=GOLD, fontsize=15,
            fontproperties=serif_b, va='center')
    ax.text(3.4, y, title, color=INK, fontsize=15,
            fontproperties=serif_b, va='center')
    ax.plot([0, 100], [y - 2.0, y - 2.0], color=INK, lw=0.8)


def row(ax, y, tag, label, calc=False, unit="萬", box_x=63, box_w=37):
    ax.text(0, y, tag, color=GOLD if calc else SLATE, fontsize=12,
            fontproperties=serif_b, va='center')
    ax.text(4.2, y, label, color=INK, fontsize=12, va='center')
    ax.add_patch(mpatches.FancyBboxPatch(
        (box_x, y - 1.75), box_w, 3.5,
        boxstyle="round,pad=0,rounding_size=0.6",
        facecolor=CALCBOX if calc else FILLBOX,
        edgecolor=GOLD if calc else LINE, lw=1.1, zorder=2))
    ax.text(box_x + box_w - 1.6, y, unit, color=GREY, fontsize=10.5,
            va='center', ha='right', zorder=3)


def note(ax, y, txt, color=GREY, bold=False, size=11):
    ax.text(4.2, y, txt, color=color, fontsize=size, va='center',
            fontproperties=serif_b if bold else sans)


# ══════════ 左欄 ══════════
axL = fig.add_axes([0.045, 0.105, 0.435, 0.788])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 100); axL.set_ylim(0, 100)

section(axL, 97.5, "０", "先算你的健康窗口")
row(axL, 91.0, "a", "你現在幾歲", unit="歲")
row(axL, 85.4, "b", "71.4 − a ＝ 還剩幾年是健康的", calc=True, unit="年")

section(axL, 77.0, "①", "地板：永遠不動的那一袋")
row(axL, 70.5, "c", "每月基本生存開銷")
row(axL, 64.9, "d", "退休後每月勞保年金")
row(axL, 59.3, "e", "退休後每月勞退（個人專戶）")
row(axL, 53.7, "f", "d × 0.8 ＋ e ＝ 壓力測試後的月年金", calc=True)
row(axL, 48.1, "g", "（c − f）× 12 ＝ 每年缺口", calc=True)
row(axL, 42.5, "h", "g ÷ 3.5% ＝ 地板要準備的錢", calc=True)
note(axL, 36.8, "只有勞保打八折。勞退是你自己的專戶，沒有基金政策風險。")

section(axL, 29.5, "②", "長照：鎖起來的那一袋")
row(axL, 23.0, "i", "每月自付（機構月費 − 補助 1 萬）")
row(axL, 17.4, "j", "i × 12 × 10 年 ＝ 長照要準備的錢", calc=True)
note(axL, 11.6, "已買長照險：j 可以扣掉保險的月給付部分")
note(axL, 7.0, "有自住房：j 可以只算一半，房子是最後一道防線")
note(axL, 2.2, "這是四袋裡唯一能用保費換掉資本佔用的，建議第一個處理。",
     color=INK, bold=True, size=11.5)

# ══════════ 右欄 ══════════
axR = fig.add_axes([0.530, 0.105, 0.435, 0.788])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 100); axR.set_ylim(0, 100)

section(axR, 97.5, "③", "傳承：主動決定，不是剩多少算多少")
row(axR, 91.0, "k", "想留給下一代多少")
row(axR, 85.4, "l", "打算幾歲給（不要等身後）", unit="歲")

section(axR, 77.0, "④", "體驗：只有這一袋刻意歸零")
row(axR, 70.5, "m", "可投資資產總額（不含自住房）")
row(axR, 64.9, "n", "m − h − j − k ＝ 體驗層", calc=True)

section(axR, 56.5, "⑤", "把體驗層分進時間桶，前重後輕")
row(axR, 50.0, "o", "n × 50% ÷ 10 ＝ 未來十年每年", calc=True)
row(axR, 44.4, "p", "n × 35% ÷ 10 ＝ 再下個十年每年", calc=True)
row(axR, 38.8, "q", "n × 15% ＝ 最後那幾年", calc=True)

axR.add_patch(mpatches.Rectangle((0, 29.0), 100, 6.2,
                                 facecolor=GOLD, alpha=0.13, zorder=0))
axR.text(2.0, 32.1, "o 不是「可以花」，是「必須花」。",
         color=INK, fontsize=13, fontproperties=serif_b, va='center')

section(axR, 22.0, "＊", "退休後還要租房的話，先做這一題")
row(axR, 15.5, "r", "退休後每月房租")
row(axR, 9.9, "s", "r × 12 ÷ 3.5% ＝ 要加進地板的錢", calc=True)
note(axR, 4.0, "房租是一輩子的支出，它進地板，不進體驗。",
     color=RED, bold=True, size=11.5)

fig.text(0.045, 0.076,
         "參考值：健康平均餘命 71.4 歲、平均壽命 80.77 歲（衛福部、內政部）；住宿式長照機構月費約 3 至 5 萬，政府補助最高每年 12 萬（衛福部）。\n"
         "地板提領率採 3.5%，較 Morningstar 2026 年報告的 3.9% 更保守，因為地板不允許失敗。勞保與勞退的月領金額，請到勞動部官方試算表查自己的數字。\n"
         "本表為摸魚記依《Die With Zero》框架調整整理，僅供自我檢視，不構成投資或保險建議。",
         color=GREY, fontsize=9.8, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/RETIRE-worksheet.png'
plt.savefig(out, dpi=150, facecolor=BG)
plt.close()
print(f'Done -> {out}')

"""
摸魚記 出場紀律篇 圖：三種出場條件的可執行性 ＋ 四層減倉順序與觸發器
JPM Daily Guide 版型（白底、金色章頭方塊、Serif Bold 標題、細線輕格線）
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

BG = "#ffffff"; INK = "#1a1a1a"; GREY = "#6b6b6b"; LGRID = "#d9d9d9"
GOLD = "#b8954a"; RED = "#b23b32"; GREEN = "#2e7d4f"; SLATE = "#4a5d7a"

fig = plt.figure(figsize=(13.6, 8.4), facecolor=BG)

fig.text(0.046, 0.945, "■", color=GOLD, fontsize=13)
fig.text(0.068, 0.938, "什麼時候該賣：把條件寫在訊號上，不寫在價格上",
         color=INK, fontsize=18, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.046, 0.968], [0.906, 0.906],
                            transform=fig.transFigure, color=INK, lw=0.8))

# ══════════ 左欄：三種出場條件 ══════════
axL = fig.add_axes([0.046, 0.115, 0.40, 0.775])
axL.set_facecolor(BG); axL.axis('off')
axL.set_xlim(0, 10); axL.set_ylim(0, 10)

axL.text(0, 9.62, "三種出場條件，只有一種會被執行", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')

methods = [
    ("憑感覺", "「漲夠了就賣」", RED, "0%",
     ["根本不是一個條件", "「夠了」永遠是下一個價位"]),
    ("綁價格", "「跌破多少就停損」", RED, "低",
     ["價格不知道你的成本，也不知道你的論點",
      "7/28–29 的停損多被斷頭賣壓打掉，", "而那個位置回頭看正是整波最低"]),
    ("綁訊號", "「當初買的理由還在不在」", GREEN, "接近 100%",
     ["訊號響的時候，不需要臨場判斷", "情緒最滿的那天，決定已經寫好了"]),
]

for i, (name, sub, c, rate, points) in enumerate(methods):
    top = 8.75 - i * 3.05
    axL.add_patch(mpatches.Rectangle((0, top - 2.45), 0.13, 2.45,
                                     color=c, zorder=3))
    axL.text(0.42, top - 0.32, name, color=INK, fontsize=13,
             fontproperties=serif_b, va='center')
    axL.text(0.42, top - 0.92, sub, color=GREY, fontsize=9.4, va='center')
    axL.text(9.95, top - 0.32, "執行率 " + rate, color=c, fontsize=11.5,
             fontproperties=serif_b, va='center', ha='right')
    for j, pt in enumerate(points):
        axL.text(0.42, top - 1.48 - j * 0.44, pt, color=INK,
                 fontsize=8.8, va='center')
    if i < 2:
        axL.plot([0, 10], [top - 2.72, top - 2.72], color=LGRID, lw=0.7)


# ══════════ 右欄：四層減倉順序 ══════════
axR = fig.add_axes([0.505, 0.115, 0.463, 0.775])
axR.set_facecolor(BG); axR.axis('off')
axR.set_xlim(0, 10); axR.set_ylim(0, 10)

axR.text(0, 9.62, "訊號響了，減倉的順序", color=INK,
         fontsize=12.5, fontproperties=serif_b, va='center')
axR.text(9.95, 9.62, "同一個前提：價格還在漲", color=GREY,
         fontsize=9, va='center', ha='right')

order = [
    ("1", "庫存增值層", "模組廠", RED,
     "存貨由增值轉為跌價，跌得比誰都快",
     "存貨已衝上 124 億新高"),
    ("2", "純產能瓶頸層", "NAND", "#c26a4a",
     "沒有技術、材料或政策保護",
     "券商已砍目標價 42%，理由是定價趨緩"),
    ("3", "排擠型意願層", "台廠 DDR4、利基型", GOLD,
     "護城河是別人不想擴，不是做不出來",
     "要盯的是 HBM 排擠會不會鬆"),
    ("4", "技術與材料層", "HBM 三雄、上游材料", GREEN,
     "3–4 倍晶圓係數擋著，新產能 2027 底才到",
     "可以抱久一點"),
]

for i, (num, layer, member, c, why, note) in enumerate(order):
    top = 8.72 - i * 2.14
    axR.add_patch(mpatches.Rectangle((0, top - 1.72), 10, 1.72,
                                     facecolor=c, alpha=0.05, zorder=0))
    axR.add_patch(mpatches.Circle((0.42, top - 0.42), 0.30,
                                  color=c, zorder=3))
    axR.text(0.42, top - 0.42, num, color='#ffffff', fontsize=11,
             fontproperties=serif_b, va='center', ha='center')
    axR.text(1.02, top - 0.42, layer, color=INK, fontsize=11.8,
             fontproperties=serif_b, va='center')
    axR.text(9.9, top - 0.42, member, color=c, fontsize=9.6,
             fontproperties=serif_b, va='center', ha='right')
    axR.text(1.02, top - 1.03, why, color=INK, fontsize=9, va='center')
    axR.text(1.02, top - 1.48, note, color=GREY, fontsize=8.4, va='center')

fig.text(0.505, 0.086,
         "主觸發器：DRAM 合約價實際轉跌／雲端業者資本支出指引下修\n"
         "次觸發器：HBM 排擠鬆動／政策前提消失／個別持有理由消失",
         color=INK, fontsize=8.8, fontproperties=serif_b,
         linespacing=1.8, va='top')

fig.text(0.046, 0.086,
         "執行率為個人紀錄，非公開統計。\n"
         "資料來源：TrendForce／DRAMeXchange、TWSE、券商報告、產業媒體，摸魚記整理。台股數據至 2026/8/11 收盤。\n"
         "分層與觸發器為摸魚記自訂框架，非標準產業分類；不構成投資建議。",
         color=GREY, fontsize=7.5, linespacing=1.8, va='top')

out = '/home/user/KIWI/personal/drafts/EXIT-chart-order.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

"""
摸魚記 反彈定性篇 圖：熊市反彈歷史 ＋ 五工具鑑定（JPM Daily Guide 版型）
左欄：三格歷史 stat（42% 最佳日在熊市／2000-02 +25% 後續跌／2008 十次反彈）
右欄：五工具鑑定這一次（checklist 行）
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

fig = plt.figure(figsize=(13, 7.6), facecolor=BG)

fig.text(0.052, 0.93, "■", color=GOLD, fontsize=13)
fig.text(0.075, 0.923, "這根反彈，是逃命窗還是回程票？",
         color=INK, fontsize=18.5, fontproperties=serif_b)
fig.lines.append(plt.Line2D([0.052, 0.965], [0.888, 0.888],
                             transform=fig.transFigure, color=INK, lw=0.8))

# ══ 左欄：歷史三格 ══
axL = fig.add_axes([0.055, 0.14, 0.40, 0.63])
axL.set_facecolor(BG)
axL.set_title("先上歷史課：死貓也會跳，而且跳很高", loc='left',
              color=INK, fontsize=12.5, fontproperties=serif_b, pad=18)
axL.set_xlim(0, 1); axL.set_ylim(0, 4.6); axL.axis('off')

stats = [
    ("42%", "過去 20 年 S&P 最強上漲日\n發生在熊市裡的比例"),
    ("+25% / 108 天", "2000–02 熊市中段的最大反彈\n之後市場掉頭續跌"),
    ("10 次", "2008 金融海嘯期間的熊市反彈次數\n最大一次 +24%、46 天"),
]
for i, (big, small) in enumerate(stats):
    y = 3.95 - i * 1.35
    axL.text(0.0, y, big, ha='left', va='center', color=RED,
             fontsize=21, fontproperties=serif_b)
    axL.text(0.0, y - 0.52, small, ha='left', va='center', color=INK,
             fontsize=9.5, linespacing=1.6)
    if i < 2:
        axL.plot([0, 1], [y - 0.85, y - 0.85], color=LGRID, lw=0.7)

axL.text(0, -0.07, "平靜的牛市，不需要一天 +5% 的日子",
         transform=axL.transAxes, color=INK, fontsize=10.5,
         fontproperties=serif_b, va='top')

# ══ 右欄：五工具鑑定 ══
axR = fig.add_axes([0.52, 0.14, 0.445, 0.63])
axR.set_facecolor(BG)
axR.set_title("五工具鑑定這一次（7/21 反彈）", loc='left',
              color=INK, fontsize=12.5, fontproperties=serif_b, pad=18)
axR.set_xlim(0, 10); axR.set_ylim(0, 5.6); axR.axis('off')

rows = [
    ("① 領漲者",   "美光+12%/SNDK+14% 有軋空味；費半+5.5% 廣度不差", "混合", SLATE),
    ("② 慢層證據", "台韓出口數據強＝AI 需求的海關背書",             "加分", GREEN),
    ("③ 觸發器",   "外資千億級賣超／VIXTWN 回 40：都沒響",          "加分", GREEN),
    ("④ 量能廣度", "台股量價與騰落，待確認",                        "待補", GREY),
    ("⑤ 事件位置", "FOMC＋月底合約價都還沒開獎：考前搶跑",          "打折", RED),
]
for i, (name, desc, tag, c) in enumerate(rows):
    y = 5.1 - i * 1.05
    axR.text(0.0, y, name, ha='left', va='center', color=INK,
             fontsize=11, fontproperties=serif_b)
    axR.text(2.55, y, desc, ha='left', va='center', color=GREY, fontsize=8.8)
    axR.text(10.0, y, tag, ha='right', va='center', color=c,
             fontsize=11, fontproperties=serif_b)
    if i < 4:
        axR.plot([0, 10], [y - 0.52, y - 0.52], color=LGRID, lw=0.7)

axR.text(0, -0.07, "初判：比較像「修正尾聲的第一次確認」，但要等第二根證據（合約價、FOMC）",
         transform=axR.transAxes, color=INK, fontsize=10,
         fontproperties=serif_b, va='top')

fig.text(0.052, 0.045,
         "資料來源：Hartford Funds（熊市最佳日統計）、Morningstar（2000–02 反彈）、Modern Wealth Management（2008 反彈次數）、Nasdaq/費半 21/07/26 收盤，摸魚記整理。\n"
         "過往表現並非未來結果的保證。",
         color=GREY, fontsize=7.8, linespacing=1.7, va='top')

out = '/home/user/KIWI/personal/drafts/REB-chart-deadcat.png'
plt.savefig(out, dpi=170, facecolor=BG)
plt.close()
print(f'Done -> {out}')

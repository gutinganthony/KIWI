# -*- coding: utf-8 -*-
"""PA Team 四週市場回顧 — 6-slide PPTX, KIWI TradingView dark theme."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Palette (TradingView dark) ──
BG_DARK  = RGBColor(0x13, 0x17, 0x22)
BG_CARD  = RGBColor(0x1E, 0x22, 0x2D)
BG_LIGHT = RGBColor(0x2A, 0x2E, 0x39)
WHITE    = RGBColor(0xD1, 0xD4, 0xDC)
MUTED    = RGBColor(0x78, 0x7B, 0x86)
GREEN    = RGBColor(0x26, 0xA6, 0x9A)
YELLOW   = RGBColor(0xF7, 0xC9, 0x48)
ORANGE   = RGBColor(0xFF, 0x98, 0x00)
RED      = RGBColor(0xEF, 0x53, 0x50)
BLUE     = RGBColor(0x42, 0xA5, 0xF5)
PURPLE   = RGBColor(0x7C, 0x4D, 0xFF)

W = Inches(13.33)
H = Inches(7.5)

prs = Presentation()
prs.slide_width = W
prs.slide_height = H
blank = prs.slide_layouts[6]


def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def tb(slide, text, x, y, w, h, size=24, bold=False, color=WHITE,
       align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.italic = italic
    return txb


def box(slide, x, y, w, h, fill_color, line_color=None):
    sp = slide.shapes.add_shape(1, x, y, w, h)  # rectangle
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill_color
    if line_color:
        sp.line.color.rgb = line_color
        sp.line.width = Pt(0.75)
    else:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def accent_bar(slide, x, y, h, color):
    box(slide, x, y, Inches(0.08), h, color)


def header(slide, title, subtitle, accent):
    box(slide, Inches(0), Inches(0), Inches(0.12), H, accent)
    tb(slide, title, Inches(0.5), Inches(0.36), Inches(12.4), Inches(0.7),
       size=29, bold=True, color=WHITE)
    tb(slide, subtitle, Inches(0.5), Inches(1.02), Inches(12.4), Inches(0.45),
       size=14, color=MUTED, italic=True)
    box(slide, Inches(0.5), Inches(1.5), Inches(4.5), Inches(0.045), accent)


# ── SLIDE 1: Title ──────────────────────────────────────────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
box(s, Inches(0), Inches(0), Inches(0.5), H, BG_CARD)
box(s, Inches(0), Inches(0), Inches(0.12), H, BLUE)

tb(s, "PA TEAM · 月度市場回顧", Inches(8.3), Inches(0.32), Inches(4.7), Inches(0.5),
   size=12, color=MUTED, align=PP_ALIGN.RIGHT)

tb(s, "市場四週回顧與展望", Inches(0.9), Inches(1.35), Inches(11.5), Inches(1.1),
   size=46, bold=True, color=WHITE)
tb(s, "AI 盈餘牛市  ×  油價衝擊  ×  聯儲鷹派轉向", Inches(0.92), Inches(2.5),
   Inches(11.5), Inches(0.8), size=26, color=BLUE)
box(s, Inches(0.95), Inches(3.35), Inches(4.5), Inches(0.05), BLUE)

tb(s, "彙整期間：2026/06/02 – 06/25     ·     12 份每日晨會重點摘要",
   Inches(0.95), Inches(3.6), Inches(11), Inches(0.5), size=15, color=WHITE)
tb(s, "來源：Goldman Sachs · Morgan Stanley · Deutsche Bank · Citi · BofA · Bloomberg",
   Inches(0.95), Inches(4.05), Inches(11.5), Inches(0.5), size=12, color=MUTED)

badges = [
    ("AI 牛市", "盈餘驅動 · 中場", YELLOW),
    ("通膨 / 油價", "Iran · Hormuz", ORANGE),
    ("聯儲鷹派", "10月加息定價", RED),
]
for i, (tag, desc, col) in enumerate(badges):
    bx = Inches(0.95) + i * Inches(2.55)
    box(s, bx, Inches(4.75), Inches(2.3), Inches(0.85), BG_CARD)
    accent_bar(s, bx, Inches(4.75), Inches(0.85), col)
    tb(s, tag, bx + Inches(0.18), Inches(4.82), Inches(2.1), Inches(0.45),
       size=16, bold=True, color=col)
    tb(s, desc, bx + Inches(0.18), Inches(5.22), Inches(2.1), Inches(0.3),
       size=11, color=MUTED)

tb(s, "一句話：基本面（盈餘）仍穩，但宏觀（通膨＋利率）轉向——市場在「相信 AI 敘事」與「預期透支」之間拉鋸。",
   Inches(0.95), Inches(6.2), Inches(11.6), Inches(0.6), size=13, italic=True, color=MUTED)


# ── SLIDE 2: Narrative timeline ─────────────────────────────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
header(s, "四週敘事主軸：從油價衝擊到鷹派轉向",
       "一條主線串起 12 份報告 — 盈餘牛市撞上滯脹隱憂與聯儲轉向", BLUE)

events = [
    ("6/02–04", "「1999 遇上 1990」：AI 熱潮撞上油價衝擊",
     "GS / DB 上調標普年底目標至 8000；通膨大幅上修、增長僅小修，央行被迫轉鷹", BLUE),
    ("6/05", "科技重挫",
     "那斯達克 −4.18%、費半 −10.26%，逾兆美元市值蒸發，韓股盤中熔斷", RED),
    ("6/09–11", "「健康調整」非見頂",
     "強勁就業推升加息預期、CPI 料見頂；大摩定調為部位去化，惟流動性指標轉緊", GREEN),
    ("6/16–17", "美伊臨時協議 + 大型科技去擁擠",
     "Hormuz 重啟在望，布倫特跌破 84；大型科技倉位由 97→48 百分位回到中性", ORANGE),
    ("6/18", "擁擠度創歷史新高",
     "做多半導體＝史上最擁擠交易（80%）；現金升至 4.1%，「AI 泡沫」成首要尾部風險", YELLOW),
    ("6/24", "FOMC 鷹派轉向（沃什首秀）",
     "點陣圖 18 人中 9 人指向加息；首次加息預期由 2027/3 提前至 2026/10", RED),
    ("6/25", "資產配置防禦微調",
     "大摩維持美股超配（標普 8300）、歐洲能源降至中性、偏好中期美債", PURPLE),
]
y0 = Inches(1.75)
step = Inches(0.74)
for j, (date, title, desc, col) in enumerate(events):
    ty = y0 + j * step
    box(s, Inches(0.6), ty + Inches(0.07), Inches(0.18), Inches(0.18), col)
    if j < len(events) - 1:
        box(s, Inches(0.665), ty + Inches(0.25), Inches(0.05), step - Inches(0.25), BG_LIGHT)
    tb(s, date, Inches(0.95), ty - Inches(0.02), Inches(1.15), Inches(0.4),
       size=13, bold=True, color=col)
    tb(s, title, Inches(2.15), ty - Inches(0.02), Inches(6.0), Inches(0.4),
       size=13, bold=True, color=WHITE)
    tb(s, desc, Inches(2.15), ty + Inches(0.32), Inches(6.2), Inches(0.4),
       size=10.5, color=MUTED)

# right tension card
cx = Inches(8.65)
box(s, cx, Inches(1.75), Inches(4.2), Inches(5.0), BG_CARD)
accent_bar(s, cx, Inches(1.75), Inches(5.0), PURPLE)
tb(s, "核心張力", cx + Inches(0.25), Inches(1.9), Inches(3.8), Inches(0.5),
   size=16, bold=True, color=PURPLE)
box(s, cx + Inches(0.25), Inches(2.45), Inches(3.7), Inches(0.03), BG_LIGHT)
pairs = [
    ("撐盤的力量", "Q1 盈餘超共識 13%；AI 資本開支超級週期；資金強勁流入", GREEN),
    ("壓頂的力量", "油價推升通膨、聯儲轉鷹、10Y 利率逼近紅線、估值與擁擠創高", RED),
    ("勝負手", "油價能否壓 CPI 回 3% 以下：花旗降息劇本 vs 美銀滯脹劇本", YELLOW),
]
yy = Inches(2.65)
for lab, txt, col in pairs:
    tb(s, lab, cx + Inches(0.25), yy, Inches(3.7), Inches(0.35), size=13, bold=True, color=col)
    tb(s, txt, cx + Inches(0.25), yy + Inches(0.36), Inches(3.7), Inches(0.9), size=11, color=MUTED)
    yy += Inches(1.42)


# ── SLIDE 3: Five themes ────────────────────────────────────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
header(s, "五大主題", "貫穿四週的結構性力量，彼此交織、互為因果", GREEN)

themes = [
    ("①  AI 牛市：中場、盈餘驅動、窗口收窄",
     "盈餘上修撐盤（非估值擴張），但「容錯率極低」；AI 股已佔標普 500 權重 39%，下行風險不對稱。", YELLOW),
    ("②  宏觀轉向：通膨再加速 × 聯儲鷹派",
     "增長小修、通膨大修；FOMC 點陣圖轉鷹、市場定價 10 月加息；核心之辯：1996 生產率紅利 vs 1999 需求過熱。", RED),
    ("③  油價＝總開關（地緣 / Hormuz）",
     "Iran 戰爭推升通膨；基準布倫特 86、事故情境 150；6/16 臨時協議後跌破 84。油價走向牽動全局。", ORANGE),
    ("④  利率＝股市紅線",
     "GS 視 10 年期美債 5% 為紅線，尚未觸及但為下半年關鍵變數；曲線熊平、財政赤字達 GDP 6.6%。", BLUE),
    ("⑤  部位與廣度：去擁擠、輪動、流動性收緊",
     "6/5 為大型科技去擁擠（非見頂），非科技倉位低、輪動基礎仍在；惟流動性領先指標轉緊、紀錄資金流入＝反向警訊。", GREEN),
]
y0 = Inches(1.72)
rh = Inches(0.98)
gap = Inches(0.06)
for i, (title, desc, col) in enumerate(themes):
    ty = y0 + i * (rh + gap)
    box(s, Inches(0.5), ty, Inches(12.33), rh, BG_CARD)
    accent_bar(s, Inches(0.5), ty, rh, col)
    tb(s, title, Inches(0.78), ty + Inches(0.12), Inches(11.9), Inches(0.4),
       size=15, bold=True, color=col)
    tb(s, desc, Inches(0.78), ty + Inches(0.52), Inches(11.9), Inches(0.42),
       size=11.5, color=MUTED)


# ── SLIDE 4: Regional divergence + market temperature ───────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
header(s, "區域分化與市場溫度", "誰在領跑、誰在承壓，以及情緒與擁擠度的讀數", ORANGE)

# Left: regions
tb(s, "區域分化", Inches(0.55), Inches(1.65), Inches(6.5), Inches(0.4),
   size=15, bold=True, color=WHITE)
regions = [
    ("美國", "最具韌性：盈餘＋設備投資穩；惟估值與擁擠度偏高", GREEN),
    ("亞洲（除日）", "強勢：韓國最佳，晶片超級週期，MSCI 韓股僅 7.2x，IT EPS 翻倍", GREEN),
    ("日本", "被油價改寫：能源進口逆風，日圓貶至 161.8（2024/7 以來最低）", ORANGE),
    ("歐洲", "最弱：近技術性衰退，服務業 PMI 走弱，2026 GDP 僅 0.5%", RED),
    ("中國", "資金持續流出（連 11 週）；市場廣度較優但集中度仍高", MUTED),
]
y0 = Inches(2.12)
for i, (reg, desc, col) in enumerate(regions):
    ty = y0 + i * Inches(0.92)
    box(s, Inches(0.5), ty, Inches(6.7), Inches(0.82), BG_CARD)
    accent_bar(s, Inches(0.5), ty, Inches(0.82), col)
    tb(s, reg, Inches(0.78), ty + Inches(0.1), Inches(2.0), Inches(0.4),
       size=14, bold=True, color=col)
    tb(s, desc, Inches(0.78), ty + Inches(0.45), Inches(6.2), Inches(0.35),
       size=10.5, color=MUTED)

# Right: market temperature
rx = Inches(7.45)
box(s, rx, Inches(1.75), Inches(5.38), Inches(5.0), BG_CARD)
tb(s, "市場溫度 · 情緒與擁擠", rx + Inches(0.25), Inches(1.9), Inches(5.0), Inches(0.4),
   size=15, bold=True, color=MUTED)
box(s, rx + Inches(0.22), Inches(2.4), Inches(4.95), Inches(0.03), BG_LIGHT)
stats = [
    ("39%", "AI 股佔標普 500 權重", YELLOW),
    ("80%", "做多半導體＝史上最擁擠交易", ORANGE),
    ("9.2", "美銀牛熊指標（深入「賣出」區）", RED),
    ("4.1%", "平均現金水位（防禦升高）", BLUE),
    ("$119bn", "美股單週淨流入（紀錄·反向訊號）", PURPLE),
    ("28%", "視「AI 泡沫」為最大尾部風險（5 月僅 5%）", GREEN),
]
yy = Inches(2.55)
for i, (num, label, col) in enumerate(stats):
    box(s, rx + Inches(0.22), yy, Inches(4.95), Inches(0.62),
        BG_LIGHT if i % 2 == 0 else BG_CARD)
    tb(s, num, rx + Inches(0.32), yy + Inches(0.08), Inches(1.45), Inches(0.5),
       size=19, bold=True, color=col)
    tb(s, label, rx + Inches(1.85), yy + Inches(0.15), Inches(3.3), Inches(0.42),
       size=11, color=MUTED)
    yy += Inches(0.68)


# ── SLIDE 5: Conclusion + allocation ────────────────────────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
header(s, "結論與資產配置建議", "綜合 GS / MS / DB / Citi / BofA / Bloomberg 觀點之整合視角", PURPLE)

box(s, Inches(0.5), Inches(1.66), Inches(12.33), Inches(0.92), BG_CARD)
accent_bar(s, Inches(0.5), Inches(1.66), Inches(0.92), PURPLE)
tb(s, "結論：維持「建設性、但防禦微調」", Inches(0.78), Inches(1.74), Inches(11.9), Inches(0.4),
   size=15, bold=True, color=WHITE)
tb(s, "在盈餘可見度高處增持、主動降低集中與槓桿、提高現金緩衝；油價與利率是兩大搖擺因子，緊盯油價能否壓 CPI 回 3% 以下與 10Y 是否逼近 5%。",
   Inches(0.78), Inches(2.14), Inches(11.9), Inches(0.42), size=11.5, color=MUTED)

cols = [
    ("▲  增持 OVERWEIGHT", GREEN, [
        "美股（品質 / 盈餘）：金融 · 工業 · 醫療，廣度外擴",
        "亞洲（除日）/ 韓國：晶片週期 + 低估值重估",
        "中期美債：殖利率年底回落，carry + 防禦",
        "新興市場低波動、高股息個股",
    ]),
    ("▼  減持 UNDERWEIGHT", RED, [
        "擁擠的大型科技 / 半導體集中部位（降槓桿）",
        "長天期債券：熊陡風險，10Y 逼近 5%",
        "歐洲股票 / 信用：近技術性衰退",
        "日圓 / 未對沖日股：結構性走弱",
    ]),
    ("●  中性 / 戰術 NEUTRAL", YELLOW, [
        "歐洲能源股：Hormuz 重啟 → 降至中性",
        "黃金：滯脹 / 地緣對沖，小幅配置",
        "現金：提高至 ~4%，保留乾火藥",
        "波動率資產：適度配置以防尾部",
    ]),
]
cw = Inches(3.97)
cy = Inches(2.78)
ch = Inches(3.95)
for i, (htxt, col, items) in enumerate(cols):
    cx = Inches(0.5) + i * Inches(4.18)
    box(s, cx, cy, cw, ch, BG_CARD)
    accent_bar(s, cx, cy, ch, col)
    tb(s, htxt, cx + Inches(0.22), cy + Inches(0.16), cw - Inches(0.3), Inches(0.5),
       size=14, bold=True, color=col)
    box(s, cx + Inches(0.22), cy + Inches(0.68), cw - Inches(0.44), Inches(0.03), BG_LIGHT)
    for k, it in enumerate(items):
        tb(s, "·  " + it, cx + Inches(0.22), cy + Inches(0.85) + k * Inches(0.74),
           cw - Inches(0.4), Inches(0.7), size=11.5, color=WHITE)

tb(s, "※ 配置觀點為彙整各投行研究之整合，非個別投資建議；花旗 / 大摩對聯儲路徑（仍見降息）與多數機構（轉向加息）存在分歧，請依自身風險屬性判讀。",
   Inches(0.5), Inches(6.95), Inches(12.3), Inches(0.4), size=9.5, italic=True, color=MUTED)


# ── SLIDE 6: Watch list ─────────────────────────────────────────
s = prs.slides.add_slide(blank)
bg(s, BG_DARK)
header(s, "下一步：關鍵觀察點", "決定劇本走向（1996 軟著陸 vs 1999 過熱）的六個變數", YELLOW)

watch = [
    ("🛢  油價 → CPI",
     "能否壓回 3% 以下？花旗降息劇本 vs 美銀滯脹劇本的勝負手", ORANGE),
    ("🏦  FOMC 路徑",
     "10 月加息已定價；美銀看年內 3 碼、德銀 2 碼，花旗逆勢看降息", RED),
    ("📈  10 年期美債",
     "逼近 5% ＝股市紅線；曲線熊陡、財政赤字與長端供給壓力", BLUE),
    ("🤖  AI 盈餘 / 資本開支",
     "2027 雲廠商 capex 看破 1 兆；盈餘可持續性是估值關鍵", YELLOW),
    ("🌀  擁擠度去化",
     "做多半導體 / Mag 7 若鬆動，恐引發連鎖去槓桿與波動放大", PURPLE),
    ("🗳  政治 / 日圓",
     "11 月中期選舉「股債匯三殺」風險；日圓 carry 平倉尾部", GREEN),
]
cols_n = 3
for i, (title, desc, col) in enumerate(watch):
    row = i // cols_n
    ci = i % cols_n
    fx = Inches(0.5) + ci * Inches(4.18)
    fy = Inches(1.85) + row * Inches(2.32)
    fw = Inches(3.97)
    fh = Inches(2.12)
    box(s, fx, fy, fw, fh, BG_CARD)
    accent_bar(s, fx, fy, fh, col)
    tb(s, title, fx + Inches(0.22), fy + Inches(0.16), fw - Inches(0.3), Inches(0.5),
       size=15, bold=True, color=WHITE)
    tb(s, desc, fx + Inches(0.22), fy + Inches(0.78), fw - Inches(0.4), Inches(1.2),
       size=12, color=MUTED)

box(s, Inches(0.5), Inches(6.72), Inches(12.33), Inches(0.62), BG_LIGHT)
tb(s, "底線：基本面仍穩，但市場容錯率低 —— 增持盈餘確定性、控制集中與槓桿，緊盯油價與利率兩大搖擺因子。",
   Inches(0.72), Inches(6.84), Inches(12.0), Inches(0.4), size=13, bold=True, color=WHITE)


# ── Save ──
out = "/home/user/KIWI/PA team/summaries/PA_Team_市場月報_2026-06-02_to_2026-06-25.pptx"
prs.save(out)
print("Saved:", out)
print("Slides:", len(prs.slides._sldIdLst))

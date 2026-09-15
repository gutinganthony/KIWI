#!/usr/bin/env python3
"""從模型直接產生圖 5，讓圖上的機率不可能和模型脫節。

用法：python3 make_fig5.py && python3 render.py fig5-scenarios.svg

資產欄是**從估值恆等式推出來的方向判斷**，不是回測結果——
文獻上並不存在乾淨的「獲利×通膨」2×2 資產報酬矩陣（二維交叉後樣本不足）。
每一格的推理寫在 REASONS 裡，數字來源見 projects/macro-scenarios/。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "projects", "macro-scenarios"))
import scenario_model as M  # noqa: E402

ASSETS = ["現金與短債", "長天期公債", "高估值成長股", "黃金", "能源"]

# -2 最不利 / -1 不利 / 0 普通 / 1 有利 / 2 最有利
VIEW = {
    "軟著陸":     [-1,  1,  2,  0, -1],
    "黏著":       [ 1, -1,  1,  0,  1],
    "成長驚嚇":   [ 1,  2,  0,  1, -2],
    "停滯性通膨": [ 2, -1, -2,  0,  1],
}

REASONS = {
    "軟著陸": "倍數擴張 +11.8%＋獲利中位數 +12% ⇒ 100% 的歷史窗都是正報酬；"
              "現金失去 carry；通膨降通常伴隨油價弱",
    "黏著": "倍數壓縮 −6.8%，打平門檻 +7.3%；但這一格的獲利成長中位數 +14.1%，"
            "81% 的歷史窗過關 ⇒ 成長股是正的，不是負的",
    "成長驚嚇": "長債最贏。成長股是**銅板翻面**：獲利中位數 −11%，但倍數擴張 +11.8% 幾乎剛好抵銷，"
                "歷史上 50% 的窗仍是正報酬。需求走弱直接打能源",
    "停滯性通膨": "倍數 −6.8%＋獲利 −8.8%，兩邊都不幫忙 ⇒ **0% 的歷史窗過關**，現金相對最好。"
                  "黃金只給普通：1890 年以來 7 次停滯性通膨，黃金只有 1973–75 真正發揮",
}

DESC = {
    "軟著陸": "通膨回到目標，獲利撐住",
    "黏著": "通膨沒回去，獲利撐住",
    "成長驚嚇": "通膨回到目標，獲利轉壞",
    "停滯性通膨": "通膨沒回去，獲利也轉壞",
}

FILL = {2: "#2a78d6", 1: "#dbe9fa", 0: "#f0efec", -1: "#fadedd", -2: "#c93030"}
INK = {2: "#ffffff", 1: "#1a5fb0", 0: "#52514e", -1: "#b02a2a", -2: "#ffffff"}
LABEL = {2: "最有利", 1: "有利", 0: "普通", -1: "不利", -2: "最不利"}
BOLD = {2: "700", 1: "700", 0: "400", -1: "700", -2: "700"}

W, ROW_H, TOP = 1040, 84, 162
COL_X = [390, 510, 630, 750, 870]
CELL_W, CELL_H = 112, 46


def build():
    total, _ = M.compute(M.PAIRS, M.RANK_INFL, M.RANK_EPS, M.SORTED_INFL)
    rows = sorted(((M.SCENARIOS[k][0], total[k]) for k in range(4)), key=lambda r: -r[1])
    h = TOP + ROW_H * len(rows) + 84
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" font-family="WenQuanYi Zen Hei, Noto Sans CJK TC, '
        f'PingFang TC, Microsoft JhengHei, sans-serif">',
        f'<rect width="{W}" height="{h}" fill="#fcfcfb"/>',
        '<text x="44" y="52" font-size="29" font-weight="700" fill="#0b0b0b">'
        '四種走法，誰會受益、誰會受傷</text>',
        '<text x="44" y="84" font-size="16" fill="#52514e">'
        '股價只有兩塊：<tspan font-weight="700" fill="#0b0b0b">公司賺多少</tspan>，'
        '乘上<tspan font-weight="700" fill="#0b0b0b">市場願意付幾倍</tspan>。'
        '所以只要問兩件事——</text>',
        '<text x="44" y="110" font-size="16" fill="#52514e">'
        '<tspan font-weight="700" fill="#0b0b0b">企業獲利撐不撐得住</tspan>（管第一塊）、'
        '<tspan font-weight="700" fill="#0b0b0b">通膨回不回得到目標</tspan>（管第二塊）。</text>',
        '<text x="44" y="150" font-size="14" font-weight="700" fill="#898781">情境</text>',
        '<text x="332" y="150" font-size="14" font-weight="700" fill="#898781" '
        'text-anchor="middle">機率</text>',
    ]
    for x, a in zip(COL_X, ASSETS):
        o.append(f'<text x="{x + CELL_W // 2}" y="150" font-size="14" font-weight="700" '
                 f'fill="#898781" text-anchor="middle">{a}</text>')
    o.append('<line x1="44" y1="162" x2="996" y2="162" stroke="#e1e0d9" stroke-width="1.5"/>')

    for r, (name, p) in enumerate(rows):
        y = TOP + r * ROW_H + 6
        o.append(f'<text x="44" y="{y + 20}" font-size="20" font-weight="700" '
                 f'fill="#0b0b0b">{name}</text>')
        o.append(f'<text x="44" y="{y + 44}" font-size="14" fill="#52514e">{DESC[name]}</text>')
        o.append(f'<text x="332" y="{y + 33}" font-size="28" font-weight="700" '
                 f'fill="#0b0b0b" text-anchor="middle">{round(p * 100)}%</text>')
        for x, v in zip(COL_X, VIEW[name]):
            o.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="5" '
                     f'fill="{FILL[v]}"/>')
            o.append(f'<text x="{x + CELL_W // 2}" y="{y + 29}" font-size="16" '
                     f'font-weight="{BOLD[v]}" fill="{INK[v]}" text-anchor="middle">'
                     f'{LABEL[v]}</text>')

    ly = TOP + ROW_H * len(rows) + 10
    o.append(f'<line x1="44" y1="{ly}" x2="996" y2="{ly}" stroke="#e1e0d9" stroke-width="1.5"/>')
    lx = 44
    for v in (2, 1, 0, -1, -2):
        o.append(f'<rect x="{lx}" y="{ly + 18}" width="26" height="18" rx="4" fill="{FILL[v]}"/>')
        o.append(f'<text x="{lx + 34}" y="{ly + 32}" font-size="14" fill="#52514e">'
                 f'{LABEL[v]}</text>')
        lx += 88 if len(LABEL[v]) == 3 else 76
    o.append(f'<text x="996" y="{ly + 32}" font-size="14" fill="#898781" text-anchor="end">'
             f'機率四捨五入到整數，誤差約 ±5 個百分點</text>')
    o.append('</svg>')
    return "\n  ".join(o) + "\n", rows


if __name__ == "__main__":
    svg, rows = build()
    path = os.path.join(HERE, "fig5-scenarios.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("寫出", os.path.basename(path))
    for name, p in rows:
        print(f"  {name:<12}{p*100:4.0f}%   {REASONS[name][:44]}…")

#!/usr/bin/env python3
"""從模型直接產生圖 5，讓圖上的機率不可能和模型脫節。

用法：python3 make_fig5.py   （會寫出 fig5-scenarios.svg，再用 render.py 轉 PNG）

資產欄的方向是**從折現式推出來的判斷**，不是回測結果——
文獻上並不存在乾淨的「成長×通膨」2×2 資產報酬矩陣（二維交叉後樣本不足），
所以這裡只標相對方向，不標報酬率。理由逐格寫在 REASONS 裡。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# figures → drafts → viralcontent → skills → repo root
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "projects", "macro-scenarios"))
import scenario_model as M  # noqa: E402

ASSETS = ["現金與短債", "長天期公債", "高估值成長股", "黃金", "能源"]

# 每個情境的資產方向。-2 最不利 / -1 不利 / 0 普通 / 1 有利 / 2 最有利
VIEW = {
    "軟著陸":     [-1,  1,  2,  0,  0],
    "黏著":       [ 1, -1, -1,  0,  0],
    "再加速":     [ 2, -2, -2,  0,  1],
    "成長驚嚇":   [ 1,  2, -1,  1, -2],
    "停滯性通膨": [ 1, -1, -2,  0,  0],
}

REASONS = {
    "軟著陸": "降息空間打開：折現率降、現金流沒事 ⇒ 長天期資產最受益，現金失去carry",
    "黏著": "不升不降但維持高檔：現金拿得到報酬，折現率壓著估值",
    "再加速": "折現率再往上 ⇒ 存續期間最長的最痛；能源通常是漲價來源本身",
    "成長驚嚇": "現金流受傷但折現率大降 ⇒ 長債最贏；需求走弱打能源",
    "停滯性通膨": "現金流受傷、折現率卻降不下來 ⇒ 兩邊都不幫忙。"
                  "黃金只給普通：1890 年以來 7 次停滯性通膨，黃金只有 1973–75 真正發揮",
}

FILL = {2: "#2a78d6", 1: "#dbe9fa", 0: "#f0efec", -1: "#fadedd", -2: "#c93030"}
INK = {2: "#ffffff", 1: "#1a5fb0", 0: "#52514e", -1: "#b02a2a", -2: "#ffffff"}
LABEL = {2: "最有利", 1: "有利", 0: "普通", -1: "不利", -2: "最不利"}
BOLD = {2: "700", 1: "700", 0: "400", -1: "700", -2: "700"}

DESC = {
    "軟著陸": "通膨回到目標，就業撐住",
    "黏著": "通膨卡在 2.5–3.5%，就業撐住",
    "再加速": "通膨衝破 3.5%，就業撐住",
    "成長驚嚇": "通膨回到目標，就業壞掉",
    "停滯性通膨": "通膨沒回去，就業也壞掉",
}

W, ROW_H, TOP = 1040, 80, 156
COL_X = [390, 510, 630, 750, 870]
CELL_W, CELL_H = 112, 44


def build():
    total, _ = M.compute(M.rank_pairs(M.PAIRS))
    rows = sorted(
        ((M.SCENARIOS[k][0], total[k]) for k in range(5)),
        key=lambda r: -r[1],
    )
    h = TOP + ROW_H * 5 + 84
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" font-family="WenQuanYi Zen Hei, Noto Sans CJK TC, '
        f'PingFang TC, Microsoft JhengHei, sans-serif">',
        f'<rect width="{W}" height="{h}" fill="#fcfcfb"/>',
        '<text x="44" y="52" font-size="29" font-weight="700" fill="#0b0b0b">'
        '五種走法，誰會受益、誰會受傷</text>',
        '<text x="44" y="82" font-size="16" fill="#52514e">兩個問題決定你在哪一格：'
        '<tspan font-weight="700" fill="#0b0b0b">通膨有沒有回到目標</tspan>、'
        '<tspan font-weight="700" fill="#0b0b0b">就業有沒有壞掉</tspan>。</text>',
        '<text x="44" y="128" font-size="14" font-weight="700" fill="#898781">情境</text>',
        '<text x="332" y="128" font-size="14" font-weight="700" fill="#898781" '
        'text-anchor="middle">機率</text>',
    ]
    for x, a in zip(COL_X, ASSETS):
        out.append(f'<text x="{x + CELL_W // 2}" y="128" font-size="14" font-weight="700" '
                   f'fill="#898781" text-anchor="middle">{a}</text>')
    out.append('<line x1="44" y1="140" x2="996" y2="140" stroke="#e1e0d9" stroke-width="1.5"/>')

    for r, (name, p) in enumerate(rows):
        y = TOP + r * ROW_H
        out.append(f'<text x="44" y="{y + 20}" font-size="19" font-weight="700" '
                   f'fill="#0b0b0b">{name}</text>')
        out.append(f'<text x="44" y="{y + 42}" font-size="14" fill="#52514e">{DESC[name]}</text>')
        out.append(f'<text x="332" y="{y + 32}" font-size="27" font-weight="700" '
                   f'fill="#0b0b0b" text-anchor="middle">{round(p * 100)}%</text>')
        for x, v in zip(COL_X, VIEW[name]):
            out.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="5" '
                       f'fill="{FILL[v]}"/>')
            out.append(f'<text x="{x + CELL_W // 2}" y="{y + 28}" font-size="16" '
                       f'font-weight="{BOLD[v]}" fill="{INK[v]}" text-anchor="middle">'
                       f'{LABEL[v]}</text>')

    ly = TOP + ROW_H * 5 + 8
    out.append(f'<line x1="44" y1="{ly}" x2="996" y2="{ly}" stroke="#e1e0d9" stroke-width="1.5"/>')
    lx = 44
    for v in (2, 1, 0, -1, -2):
        out.append(f'<rect x="{lx}" y="{ly + 18}" width="26" height="18" rx="4" fill="{FILL[v]}"/>')
        out.append(f'<text x="{lx + 34}" y="{ly + 32}" font-size="14" fill="#52514e">'
                   f'{LABEL[v]}</text>')
        lx += 90 if len(LABEL[v]) == 3 else 78
    out.append(f'<text x="996" y="{ly + 32}" font-size="14" fill="#898781" text-anchor="end">'
               f'機率四捨五入到整數，誤差約 ±3–5 個百分點</text>')
    out.append('</svg>')
    return "\n  ".join(out) + "\n", rows


if __name__ == "__main__":
    svg, rows = build()
    path = os.path.join(HERE, "fig5-scenarios.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("寫出", os.path.basename(path))
    for name, p in rows:
        print(f"  {name:<12}{p*100:4.0f}%   {REASONS[name][:40]}…")

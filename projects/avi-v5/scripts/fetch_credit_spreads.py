#!/usr/bin/env python3
"""信用利差監控（AFI 模組 B 層 4）— 唯一通過歷史驗證的「火柴級」訊號。

為什麼是這一格（見 topics/business/2026-09-03-signal-verification-credit-rpoc-tw-revenue.md §1）：
  - 2007 年高收益利差自 6 月低點走闊，S&P 500 於 10/12 才見頂 ⇒ **領先 4.4 個月**
  - 債券投資人拿不到上檔，對下檔的定價比股票投資人誠實
  - 機械因果：邊際 AI capex 若為債務融資，利差走闊直接縮小整張 AI capex Sankey 的分母

為什麼放在 runner：雲端 Claude 容器對 fred.stlouisfed.org 是 connect_rejected（實測 2026-09-03）。
runner 已有 FRED_API_KEY secret 且 dashboard 管線已在用 FRED。

輸出（供 research session 直接 git pull 取得）：
  data/ext/credit/hy_oas.csv          三條序列的日資料（近 3 年）
  data/ext/credit/STATUS.md           當前燈號與觸發判定（人可讀）

best-effort：任何失敗都只印訊息並 exit 0，永不擋住 dashboard 管線。
"""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "ext" / "credit"

# ICE BofA OAS 系列。整體 HY 是主訊號；CCC/BB 用來看品質分層是否比整體更早惡化。
SERIES = {
    "HY_OAS": ("BAMLH0A0HYM2", "ICE BofA US High Yield OAS（主訊號）"),
    "CCC_OAS": ("BAMLH0A3HYC", "ICE BofA CCC & Lower OAS（分層確認）"),
    "BB_OAS": ("BAMLH0A1HYBB", "ICE BofA BB OAS（分層對照）"),
}

# 門檻（🔧 先驗設定，未經回測——AI 融資週期歷史樣本 n=0，見 tracker §D）
WARN_BP = 100.0   # 自 12 個月低點走闊 ≥100bp ⇒ 🟡
ALERT_BP = 150.0  # ≥150bp ⇒ 🔴


def _get(url: str, timeout: int = 45) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "KIWI-credit-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_series(series_id: str, start: str) -> list[tuple[str, float]]:
    """回傳 [(date, value)]，優先用 API（有 key 較穩），失敗則退回免金鑰 CSV 端點。"""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={key}&file_type=json&observation_start={start}"
        )
        try:
            obs = json.loads(_get(url))["observations"]
            return [(o["date"], float(o["value"])) for o in obs if o.get("value") not in (".", "", None)]
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] API 失敗（{series_id}）：{e}；改試 CSV 端點")

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}"
    txt = _get(url).decode("utf-8", "replace").splitlines()
    rows: list[tuple[str, float]] = []
    for row in csv.DictReader(txt):
        vals = list(row.values())
        d, v = vals[0], vals[1]
        if v not in (".", "", None):
            try:
                rows.append((d, float(v)))
            except ValueError:
                pass
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    start = (date.today() - timedelta(days=365 * 3 + 30)).isoformat()

    data: dict[str, list[tuple[str, float]]] = {}
    for name, (sid, desc) in SERIES.items():
        try:
            rows = fetch_series(sid, start)
            if not rows:
                print(f"  [warn] {name}（{sid}）回傳空資料")
                continue
            data[name] = rows
            print(f"  ✅ {name} ({sid}): {len(rows)} 筆，最新 {rows[-1][0]} = {rows[-1][1]:.2f}%  — {desc}")
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] {name}（{sid}）抓取失敗：{e}")

    if "HY_OAS" not in data:
        print("❌ 主訊號 HY_OAS 未取得 → 不覆寫既有檔案（避免用空資料蓋掉好資料）")
        return 0

    # 合併成寬表寫 CSV
    all_dates = sorted({d for rows in data.values() for d, _ in rows})
    lookup = {n: dict(rows) for n, rows in data.items()}
    csv_path = OUT_DIR / "hy_oas.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + list(SERIES.keys()))
        for d in all_dates:
            w.writerow([d] + [lookup.get(n, {}).get(d, "") for n in SERIES])
    print(f"  → {csv_path}（{len(all_dates)} 列）")

    # 判定：自 12 個月低點走闊多少 bp
    hy = data["HY_OAS"]
    cutoff = (date.today() - timedelta(days=365)).isoformat()
    win = [(d, v) for d, v in hy if d >= cutoff] or hy
    lo_d, lo_v = min(win, key=lambda x: x[1])
    cur_d, cur_v = hy[-1]
    widen_bp = (cur_v - lo_v) * 100.0
    cur_bp = cur_v * 100.0

    if widen_bp >= ALERT_BP:
        light, verdict = "🔴", "利差顯著走闊 ⇒ 火柴級訊號。依 exit-playbook §0 執行規則，不重新論證。"
    elif widen_bp >= WARN_BP:
        light, verdict = "🟡", "利差開始走闊 ⇒ 提高警覺、改為每週看，但本身不構成減碼理由。"
    else:
        light, verdict = "🟢", "無警訊。柴火可能在堆積，但火柴沒點著。"

    def line(name: str) -> str:
        if name not in data:
            return f"| {name} | 查無 | — |"
        d, v = data[name][-1]
        w12 = [(dd, vv) for dd, vv in data[name] if dd >= cutoff] or data[name]
        _, lv = min(w12, key=lambda x: x[1])
        return f"| {name} | {v:.2f}%（{d}） | 自 12M 低點 {(v - lv) * 100:+.0f}bp |"

    status = f"""# 信用利差狀態（自動產生，勿手改）

> **這是 AFI 模組 B 層 4 — 本追蹤系統唯一通過歷史驗證的「火柴級」訊號。**
> 驗證：2007 年 HY 利差自 6 月低點走闊，S&P 500 於 10/12 見頂 ⇒ **領先 4.4 個月**。
> 完整驗證見 `topics/business/2026-09-03-signal-verification-credit-rpoc-tw-revenue.md` §1。

**更新時間（UTC）**：{date.today().isoformat()}
**主訊號最新讀數**：**{cur_v:.2f}%（{cur_bp:.0f}bp），{cur_d}**
**12 個月低點**：{lo_v:.2f}%（{lo_d}）
**自低點走闊**：**{widen_bp:+.0f} bp**

## {light} 判定

> {verdict}

| 門檻 🔧 | 條件 | 狀態 |
|---|---|---|
| 🟡 | 自 12M 低點走闊 ≥ {WARN_BP:.0f}bp | {"✅ 已觸發" if widen_bp >= WARN_BP else "未觸發"} |
| 🔴 | 自 12M 低點走闊 ≥ {ALERT_BP:.0f}bp | {"✅ 已觸發" if widen_bp >= ALERT_BP else "未觸發"} |

## 三條序列

| 序列 | 最新 | 自 12M 低點 |
|---|---|---|
{line("HY_OAS")}
{line("BB_OAS")}
{line("CCC_OAS")}

> **分層讀法**：**CCC 走闊快於 BB ⇒ 品質分層惡化，通常比整體走闊更早。** 若 CCC−BB 價差擴大而 HY 整體還沒動，優先查明原因。

⚠️ **門檻為先驗設定，未經回測**——AI 融資週期的歷史樣本數 n=0。
⚠️ **極緊 ≠ 安全**：2007 年 6 月的低點也是歷史極緊，四個月後股市見頂。極緊代表下檔沒有被補償，一旦轉向速度很快。
"""

    (OUT_DIR / "STATUS.md").write_text(status)
    print(f"  → {OUT_DIR / 'STATUS.md'}")
    print(f"\n{light} HY OAS {cur_v:.2f}% ({cur_v * 100:.0f}bp)，自 12M 低點 {widen_bp:+.0f}bp")

    # 供 workflow 判斷是否要推播（只在 🟡/🔴 時推）
    if widen_bp >= WARN_BP and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"alert={light}\n")
            f.write(f"body=HY OAS {cur_v:.2f}% ({cur_v * 100:.0f}bp)，自 12 個月低點走闊 {widen_bp:+.0f}bp。{verdict}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001  — best-effort，永不擋管線
        print(f"❌ 信用利差監控失敗（不影響 dashboard）：{e}")
        sys.exit(0)

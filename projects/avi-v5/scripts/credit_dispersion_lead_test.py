#!/usr/bin/env python3
"""
credit_dispersion_lead_test.py — CCC−BB 離散度是否「領先」HY 整體走闊？

背景（2026-09-22）：
  `fetch_credit_spreads.py` 產出的 STATUS.md 自己寫著：
    「CCC 走闊快於 BB ⇒ 品質分層惡化，**通常比整體走闊更早**。
      若 CCC−BB 價差擴大而 HY 整體還沒動，優先查明原因。」
  但 🟡/🔴 的警報門檻 **只看 HY_OAS**，所以這個「更早」的訊號永遠不會觸發警報。
  2026-09-22 當下正是這個狀態：CCC 自 12M 低點 +293bp、HY 只 +8bp、BB +5bp，判定卻是 🟢。

  ⚠️ 但「STATUS.md 這樣寫」不是證據。上線任何新門檻之前必須先驗——
  規矩同 `war_lead_test.py`（那一案的驗證結果是否證，據此沒有上線）。

本腳本要回答的唯一問題：
  **CCC−BB 離散度衝高，是否真的早於 HY 整體走闊？早多久？誤報多少次？**

方法：
  1. 定義「HY 事件」＝ HY_OAS 自其 12 個月低點走闊 ≥ ALERT_BP（沿用現行 🔴 門檻 150bp）。
     同一波段只記第一天（用 COOLDOWN_DAYS 去重）。
  2. 定義「離散度訊號」＝ CCC−BB 離散度 > 其過去 LOOKBACK 天的 DISP_PCTL 百分位。
  3. 對每個 HY 事件，往前找最近一次離散度訊號 ⇒ 領先天數。
  4. **誤報**：離散度訊號發生後 MAX_LEAD 天內沒有任何 HY 事件 ⇒ 誤報。
     只報領先天數而不報誤報率＝作弊，兩者必須一起看。
  5. 掃參數網格，避免挑到單一幸運參數。

環境：需要 FRED（runner 有 FRED_API_KEY；主對話的 egress proxy 擋 fred.stlouisfed.org）。
用法：cd projects/avi-v5 && python3 scripts/credit_dispersion_lead_test.py
"""
import csv
import datetime
import json
import os
import urllib.request

SERIES = {
    "HY": "BAMLH0A0HYM2",
    "CCC": "BAMLH0A3HYC",
    "BB": "BAMLH0A1HYBB",
}
START = "1996-12-31"          # ICE BofA 系列起點附近，涵蓋 1998/2000/2007/2015/2020
ALERT_BP = 150.0              # 沿用 fetch_credit_spreads.py 的 🔴 門檻
COOLDOWN_DAYS = 365           # 同一波段去重
MAX_LEAD = 365                # 離散度訊號後多久內出現 HY 事件才算命中


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "KIWI-credit-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch(series_id):
    """與 fetch_credit_spreads.py 同樣的雙路徑：有金鑰走 API，否則走免金鑰 CSV。"""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        url = ("https://api.stlouisfed.org/fred/series/observations"
               f"?series_id={series_id}&api_key={key}&file_type=json&observation_start={START}")
        try:
            obs = json.loads(_get(url))["observations"]
            return {datetime.date.fromisoformat(o["date"]): float(o["value"])
                    for o in obs if o.get("value") not in (".", "", None)}
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] API 失敗（{series_id}）：{e}；改試 CSV 端點")
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={START}"
    out = {}
    for row in csv.DictReader(_get(url).decode("utf-8", "replace").splitlines()):
        vals = list(row.values())
        try:
            out[datetime.date.fromisoformat(vals[0])] = float(vals[1])
        except (ValueError, TypeError):
            pass
    return out


def trailing_low(series, keys, i, days=365):
    d = keys[i]
    lo = d - datetime.timedelta(days=days)
    window = [series[k] for k in keys[max(0, i - 400):i + 1] if k >= lo]
    return min(window) if window else None


def pctl(values, cur):
    return 100.0 * sum(1 for v in values if v < cur) / len(values) if values else None


def main():
    print("抓 FRED …")
    data = {}
    for name, sid in SERIES.items():
        try:
            data[name] = fetch(sid)
        except Exception as e:  # noqa: BLE001
            print(f"\n🔴 抓不到 {name}（{sid}）：{type(e).__name__}: {e}")
            print("   本檢驗需要 FRED。主對話的 egress proxy 擋 fred.stlouisfed.org；")
            print("   請在 GitHub Actions runner 上跑（runner 有 FRED_API_KEY）。中止。")
            return 2
        print(f"  {name:4s} {sid}: {len(data[name])} 點  "
              f"{min(data[name]) if data[name] else '—'} → {max(data[name]) if data[name] else '—'}")
    common = sorted(set(data["HY"]) & set(data["CCC"]) & set(data["BB"]))
    if len(common) < 500:
        print(f"\n🔴 共同交集只有 {len(common)} 點，資料不足以做這個檢驗。中止。")
        return 1
    print(f"\n共同交集 {len(common)} 點：{common[0]} → {common[-1]}")

    hy = {d: data["HY"][d] for d in common}
    disp = {d: data["CCC"][d] - data["BB"][d] for d in common}

    # ---- 1. HY 事件 ----
    events = []
    for i, d in enumerate(common):
        lo = trailing_low(hy, common, i)
        if lo is None:
            continue
        if (hy[d] - lo) * 100 >= ALERT_BP:
            if not events or (d - events[-1]).days > COOLDOWN_DAYS:
                events.append(d)
    print(f"\nHY 🔴 事件（自 12M 低點走闊 ≥{ALERT_BP:.0f}bp，{COOLDOWN_DAYS} 天去重）：{len(events)} 次")
    for e in events:
        print(f"   {e}")
    if not events:
        print("🔴 沒有事件可驗。中止。")
        return 1

    # ---- 2-5. 掃參數網格 ----
    print("\n" + "=" * 86)
    print("離散度訊號 vs HY 事件：領先天數與誤報率（兩者必須一起看）")
    print("=" * 86)
    print(f"{'lookback':>9}{'百分位':>8}{'命中':>8}{'中位領先(天)':>14}{'訊號次數':>10}{'誤報率':>9}")
    print("-" * 86)
    rows = []
    for lb in (365, 730, 1095):
        for p in (90, 95, 98):
            sig = []
            for i, d in enumerate(common):
                lo_d = d - datetime.timedelta(days=lb)
                win = [disp[k] for k in common[max(0, i - 900):i + 1] if k >= lo_d]
                if len(win) < 100:
                    continue
                r = pctl(win, disp[d])
                if r is not None and r >= p:
                    if not sig or (d - sig[-1]).days > COOLDOWN_DAYS:
                        sig.append(d)
            leads, hit = [], 0
            for e in events:
                prior = [s for s in sig if 0 < (e - s).days <= MAX_LEAD]
                if prior:
                    hit += 1
                    leads.append((e - max(prior)).days)
            fp = sum(1 for s in sig if not any(0 < (e - s).days <= MAX_LEAD for e in events))
            med = sorted(leads)[len(leads) // 2] if leads else None
            fpr = fp / len(sig) if sig else None
            print(f"{lb:>9}{p:>8}{f'{hit}/{len(events)}':>8}"
                  f"{('—' if med is None else med):>14}{len(sig):>10}"
                  f"{('—' if fpr is None else f'{fpr:.0%}'):>9}")
            rows.append((hit / len(events), med or 0, fpr if fpr is not None else 1.0, lb, p, len(sig)))

    print("-" * 86)
    good = [r for r in rows if r[0] >= 0.7 and r[2] <= 0.4 and r[1] >= 30]
    print("\n>>> 判定標準（上線門檻，事前訂好，不得事後放寬）：")
    print("      命中率 ≥70%  且  誤報率 ≤40%  且  中位領先 ≥30 天")
    if good:
        best = max(good, key=lambda r: r[0] - r[2])
        print(f"\n✅ 有 {len(good)}/{len(rows)} 組參數通過。最佳：lookback={best[3]}天、百分位={best[4]}")
        print(f"   命中 {best[0]:.0%}、誤報 {best[2]:.0%}、中位領先 {best[1]} 天、共 {best[5]} 次訊號")
        print("   ⇒ 可以考慮把 CCC−BB 離散度門檻加進 fetch_credit_spreads.py（仍需 Jake 核准）")
    else:
        print(f"\n❌ {len(rows)} 組參數**沒有一組**通過。")
        print("   ⇒ CCC−BB 離散度的領先性未獲證實，**不該加門檻**。")
        print("   （這與 war_lead_test.py 是同一個結局：門檻的價值在於有東西被它擋下來。）")
    print(f"\n⚠️ 樣本上限：只有 {len(events)} 次 HY 事件。任何結論的統計力都受此限制。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""族群輪動偵測器 v0 — 找「營收已轉、股價未轉」的台股主題族群。

用途：回答「下一個主題是哪一個、什麼時候開始」，而不是「這個主題裡哪一檔最好」。
     後者是 skills/serenity（主題內選股器），本工具是它的上游。

三道關卡（缺一不可，每一關都是被實測救過的）：
  1. 位置   — 族群相對大盤指數貼近 12 個月低點
  2. 廣度   — 成分股 YoY 中位數為正、正成長廣度 >=75%、最大單一成分佔營收 <70%
              🔴 為什麼：合計口徑會被大公司綁架。實測 2026-09 的「矽智財IP +230%」
                 全部是世芯一家（佔族群營收 93.1%），晶心科其實是 -26%。
  3. 獲利   — 成分股營益率上升，且水準不是代工級
              🔴 為什麼：ODM 營收可以 +177% 而營益率只有 3%。實測 2026-09 的
                 「AI伺服器」廣度 100%、YoY +52%，但 5 檔有 3 檔營益率在下滑
                 （廣達 -1.8pp、緯創 -0.6pp、英業達 -0.5pp），水準 1.5~7.3%。
                 ⇒ 該族群相對股價下跌是理性的，不是錯價。

⚠️ 籃子是手建的 ⇒ 回頭挑「已經漲過的主題」驗證，必然得到好結果。
   唯一能消除選樣偏誤的辦法是：**把籃子凍結在這裡，往前跑**。
   THEMES 一旦定案就不要因為「某檔漲了想加進來」而改——那就是偏誤本身。
   要新增主題請另開一列並註記加入日期。

資料：FinMind（台股日線、月營收、季財報）。非投資建議。
"""
import json, os, time, statistics as st, urllib.request, collections, datetime, sys

API = "https://api.finmindtrade.com/api/v4/data"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

# ── 籃子凍結日 2026-09-15。新增請附日期，不要事後修改既有列。 ────────────
THEMES = {
    "記憶體":       ["2344", "2408", "8271", "5289", "4967", "3006", "2451"],
    "被動元件":     ["2327", "2492", "2375", "6449"],
    "低軌衛星":     ["3491", "2314", "8011", "6285", "5388"],
    "散熱液冷":     ["3017", "3324", "8210", "3013"],
    "光通訊CPO":    ["4979", "3234", "3163", "4977"],
    "AI伺服器":     ["2317", "2382", "3231", "2356", "6669"],
    "重電":         ["1503", "1504", "1513", "1514", "1519"],
    "軍工":         ["2634", "6753", "8033"],
    "機器人自動化": ["2049", "1590", "4526", "1560"],
    "矽智財IP":     ["3661", "6533", "3529", "6643"],
    "封測":         ["3711", "6239", "3264", "2441"],
    "ABF載板":      ["3037", "8046", "3189", "2368"],
}
PX_START, RV_START = "2023-01-01", "2021-01-01"
BREADTH_MIN, CONC_MAX = 75.0, 70.0   # 廣度下限 / 單一成分佔比上限


def fetch(dataset, data_id, start, sub):
    d = os.path.join(CACHE, sub); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{data_id}.json")
    if os.path.exists(f) and time.time() - os.path.getmtime(f) < 86400:
        return json.load(open(f))
    end = datetime.date.today().isoformat()
    for _ in range(3):
        try:
            url = f"{API}?dataset={dataset}&data_id={data_id}&start_date={start}&end_date={end}"
            rows = json.loads(urllib.request.urlopen(url, timeout=70).read()).get("data", [])
            if rows:
                json.dump(rows, open(f, "w")); return rows
            time.sleep(2)
        except Exception:
            time.sleep(3)
    return json.load(open(f)) if os.path.exists(f) else []


def main():
    ids = sorted({s for v in THEMES.values() for s in v})
    px = {s: {r["date"]: r["close"] for r in fetch("TaiwanStockPrice", s, PX_START, "px") if r["close"] > 0}
          for s in ids}
    px = {s: v for s, v in px.items() if v}
    rv = {s: {f"{r['revenue_year']}-{r['revenue_month']:02d}": r["revenue"]
              for r in fetch("TaiwanStockMonthRevenue", s, RV_START, "rv")} for s in px}
    tw = fetch("TaiwanStockTotalReturnIndex", "TAIEX", PX_START, "px")
    idx = {r["date"]: (r.get("price") or r.get("close")) for r in tw}
    idx = {k: v for k, v in idx.items() if v}

    themes = {t: [s for s in v if s in px] for t, v in THEMES.items()}
    dates = sorted(set(idx) & set.intersection(*[set(px[s]) for s in px]))
    me = {}; [me.__setitem__(d[:7], d) for d in dates]
    months = sorted(me); md = [me[m] for m in months]

    def rel(members):
        out = [1.0]
        for i in range(1, len(md)):
            p, c = md[i - 1], md[i]
            grp = st.mean([px[s][c] / px[s][p] - 1 for s in members])
            out.append(out[-1] * (1 + grp - (idx[c] / idx[p] - 1)))
        return out

    def yoys(members, m):
        y, mm = int(m[:4]), m[5:]
        out = []
        for s in members:
            c, p = rv.get(s, {}).get(m), rv.get(s, {}).get(f"{y - 1}-{mm}")
            if c is not None and p:
                out.append(100 * (c / p - 1))
        return out

    print(f"族群輪動偵測器 v0   資料截至 {dates[-1]}   籃子凍結日 2026-09-15")
    print(f"{'族群':<12s}{'相對':>6s}{'距12M高':>8s}{'距12M低':>8s} | {'YoY中位':>8s}{'廣度':>6s}{'集中度':>7s}  判定")
    print("-" * 96)
    rows = []
    for t, members in themes.items():
        if not members: continue
        R = rel(members); w = R[-13:]; cur = R[-1]
        dh, dl = 100 * (cur / max(w) - 1), 100 * (cur / min(w) - 1)
        rmon = next((months[j] for j in range(len(months) - 1, -1, -1)
                     if len(yoys(members, months[j])) == len(members)), None)
        if rmon:
            v = yoys(members, rmon)
            med = st.median(v); brd = 100 * sum(1 for x in v if x > 0) / len(v)
            cm = [rv.get(s, {}).get(rmon, 0) for s in members]
            conc = 100 * max(cm) / (sum(cm) or 1)
        else:
            med = brd = conc = None

        if dl < 5 and med and med > 0 and brd >= BREADTH_MIN and conc < CONC_MAX:
            verdict = "🟡 過關卡1+2 ⇒ 必須人工跑關卡3（營益率）"
        elif dl < 5 and med and med > 0:
            verdict = "⚠️ 低檔但廣度/集中度不過"
        elif dl < 5:
            verdict = "⬇️ 低檔、營收未轉"
        elif dh > -5:
            verdict = "🔴 貼近高點（已反映）"
        else:
            verdict = "—"
        rows.append((t, cur, dh, dl, med, brd, conc, verdict))

    for t, cur, dh, dl, med, brd, conc, v in sorted(rows, key=lambda x: x[3]):
        f = lambda x, s: (s % x) if x is not None else "n/a"
        print(f"{t:<12s}{cur:6.2f}{dh:7.0f}%{dl:7.0f}% | {f(med,'%+7.0f%%')}{f(brd,'%5.0f%%')}{f(conc,'%6.0f%%')}  {v}")
    print("\n⚠️ 本表是快照，不是訊號——三道關卡未經回測（樣本 n=12、籃子手建）。")
    print("⚠️ 關卡 3（營益率）刻意不自動化：它需要判斷「這個毛利水準合不合理」，那不是門檻能做的事。")


if __name__ == "__main__":
    main()

"""資料層：SEC companyfacts（XBRL）＋ Stooq 日股價 → 標準格式（見 features.py）。

三個必須處理的陷阱（每一個都會讓本益比系統性出錯）：

1. **時點**：同一季的數字會在後來的財報被重述。這裡一律取「第一次申報」的值與申報日，
   也就是當時的投資人真正看得到的數字。
2. **Q4**：10-K 只報全年，Q4 = 全年 − Q1 − Q2 − Q3，申報日＝10-K 申報日。
3. **股價口徑**：Stooq 的收盤價同時做了分割與**股利**還原（總報酬指數）。
   直接乘股數會把過去的市值低估「累積股利殖利率」那麼多（MSFT 2015 年約低 12%）。
   這裡用財報裡的每股股利把股利還原拿掉；分割則用稀釋股數的跳動偵測。
"""
import json
import os

import numpy as np
import pandas as pd

REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
       "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueGoodsNet"]
NI = ["NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss"]
GP = ["GrossProfit"]
OI = ["OperatingIncomeLoss"]
COST = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization"]
# 虧損季常用 BasicAndDiluted 標籤（稀釋＝基本），原始 10-Q 只在那裡，漏掉就只剩事後重述值
SH = ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
      "WeightedAverageNumberOfSharesOutstandingBasic"]
EPS = ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted", "EarningsPerShareBasic"]
DPS = ["CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid"]
INV = ["InventoryNet"]
EQ = ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
CASH = ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]
STI = ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]
DEBT = ["LongTermDebt", "LongTermDebtNoncurrent", "DebtInstrumentCarryingAmount"]
DEBT_ST = ["LongTermDebtCurrent", "ShortTermBorrowings", "CommercialPaper", "DebtCurrent"]
FORMS = {"10-Q", "10-K", "10-Q/A", "10-K/A", "10-KT", "20-F", "40-F"}
SPLIT_RATIOS = (2, 3, 4, 5, 7, 8, 10, 15, 20, 1.5)


def _facts(j, names, unit_pref=("USD", "USD/shares", "shares")):
    g = j["facts"].get("us-gaap", {})
    rows = []
    for pri, n in enumerate(names):
        if n not in g:
            continue
        for unit, xs in g[n]["units"].items():
            if unit not in unit_pref:
                continue
            for x in xs:
                if x.get("form") not in FORMS:
                    continue
                rows.append((pri, x.get("start"), x["end"], x["val"], x["filed"]))
    if not rows:
        return pd.DataFrame(columns=["pri", "start", "end", "val", "filed"])
    d = pd.DataFrame(rows, columns=["pri", "start", "end", "val", "filed"])
    for c in ("start", "end", "filed"):
        d[c] = pd.to_datetime(d[c])
    return d


def _first_filed(d, keys):
    """同一期間：先取最早申報，同日申報再取優先序最高的概念。"""
    return d.sort_values(["filed", "pri"]).drop_duplicates(keys, keep="first")


def flows(j, names):
    """單季流量：80–100 天的期間直接用；Q4 用全年減前三季。回傳 index=季末 的 (val, filed)。"""
    d = _facts(j, names)
    if d.empty:
        return pd.DataFrame(columns=["val", "filed"])
    d = d.dropna(subset=["start"])
    d["days"] = (d["end"] - d["start"]).dt.days
    q = _first_filed(d[(d["days"] >= 80) & (d["days"] <= 100)], ["start", "end"])
    a = _first_filed(d[(d["days"] >= 350) & (d["days"] <= 380)], ["start", "end"])
    q = q.sort_values("end").drop_duplicates("end", keep="first")
    out = {r.end: (r.val, r.filed) for r in q.itertuples()}
    for r in a.itertuples():
        inside = q[(q["start"] >= r.start - pd.Timedelta(days=5)) & (q["end"] <= r.end - pd.Timedelta(days=60))]
        if len(inside) == 3 and r.end not in out:
            out[r.end] = (r.val - inside["val"].sum(), r.filed)
    s = pd.DataFrame.from_dict(out, orient="index", columns=["val", "filed"]).sort_index()
    return s


def annual_as_q4(j, names):
    """股數這類「平均值」概念：Q4 沒有單季值，用全年值近似（只用於分割偵測與市值股數）。"""
    d = _facts(j, names)
    if d.empty:
        return pd.DataFrame(columns=["val", "filed"])
    d = d.dropna(subset=["start"])
    d["days"] = (d["end"] - d["start"]).dt.days
    q = _first_filed(d[(d["days"] >= 80) & (d["days"] <= 100)], ["start", "end"]).drop_duplicates("end")
    a = _first_filed(d[(d["days"] >= 350) & (d["days"] <= 380)], ["start", "end"]).drop_duplicates("end")
    out = {r.end: (r.val, r.filed) for r in q.itertuples()}
    for r in a.itertuples():
        out.setdefault(r.end, (r.val, r.filed))
    return pd.DataFrame.from_dict(out, orient="index", columns=["val", "filed"]).sort_index()


def instants(j, names):
    d = _facts(j, names)
    if d.empty:
        return pd.Series(dtype=float)
    d = d[d["start"].isna()] if d["start"].notna().any() else d
    d = _first_filed(d, ["end"])
    return d.set_index("end")["val"].sort_index()


def restatement_ratios(j):
    """分割的指紋：分割後的財報會把「分割前各季」的 EPS 重述成 ÷ 分割比例；併購不會。

    回傳 [(比例, 第一次申報日, 重述申報日)]：同一季 EPS 的第一次申報值 ÷ 後來的申報值 ≈ 分割比例。
    """
    d = _facts(j, EPS, unit_pref=("USD/shares",))
    if d.empty:
        return []
    d = d.dropna(subset=["start"])
    d = d[((d["end"] - d["start"]).dt.days.between(80, 100)) & (d["val"].abs() >= 0.05)]
    out = []
    for _, g in d.sort_values("filed").groupby(["start", "end"]):
        first = g.iloc[0]
        for r in g.iloc[1:].itertuples():
            if r.val != 0 and np.sign(r.val) == np.sign(first.val):
                ratio = first.val / r.val
                if ratio > 1.5:
                    out.append((ratio, first.filed, r.filed))
    return out


def _nearest_ratio(r):
    best = min((s for s in SPLIT_RATIOS if s >= 2), key=lambda s: abs(np.log(r / s)))
    return best, abs(np.log(r / best))


def detect_splits(sh, restated=None):
    """稀釋股數第一次申報值的跳動 = 分割。回傳 {季末: 比例}（該季起股數為分割後口徑）。

    兩種證據：
    ① 股數跳動 ≈ 常見分割比例，而且下一季維持在新水準；
    ② 有「EPS 重述」證據：某一季的 EPS 在跳動前第一次申報、跳動後被重述成 ÷ 同一個比例。
    有 ② 時，① 的容忍度放寬到 ±25%（虧轉盈時稀釋股數會多出選擇權，例 PANW 3:1 呈現為 3.44 倍）；
    沒有 ② 時只接受 ±4% 的乾淨倍數——避免把併購（LHX 2019 股數 ×1.87）當成分割。
    """
    splits = {}
    v = sh["val"].to_numpy(float)
    filed = sh["filed"].to_numpy() if "filed" in sh else None
    restated = restated or []
    for i in range(1, len(v)):
        r = v[i] / v[i - 1]
        if r < 1.5:
            continue
        s, dist = _nearest_ratio(r)
        if i + 1 < len(v) and abs(np.log(v[i + 1] / v[i - 1] / s)) > max(dist, 0.04) + 0.06:
            continue                                   # 單季怪值，下一季又回去
        evidence = False
        if filed is not None:
            f_prev, f_now = pd.Timestamp(filed[i - 1]), pd.Timestamp(filed[i])
            evidence = any(abs(np.log(rr / s)) < 0.05 and fa <= f_prev + pd.Timedelta(days=5) and fb >= f_prev
                           for rr, fa, fb in restated)
        if dist < 0.04 or (evidence and dist < np.log(1.25)):
            splits[sh.index[i]] = float(s)
    return splits


def company_quarters(path, ticker):
    j = json.load(open(path))
    rev = flows(j, REV)
    if rev.empty:
        return None, None
    ni = flows(j, NI)
    oi = flows(j, OI)
    gp = flows(j, GP)
    cost = flows(j, COST)
    dps = flows(j, DPS)
    sh = annual_as_q4(j, SH)
    eps = flows(j, EPS)
    q = pd.DataFrame(index=rev.index)
    q["rev"] = rev["val"]
    q["filed"] = rev["filed"]
    q["ni"] = ni["val"].reindex(q.index)
    q["oi"] = oi["val"].reindex(q.index)       # 營業利益：只用來辨識一次性項目（淨利 ÷ 營業利益 異常），不進模型
    q["filed"] = pd.concat([q["filed"], ni["filed"].reindex(q.index)], axis=1).max(axis=1)
    gpv = gp["val"].reindex(q.index)
    gpv = gpv.fillna(q["rev"] - cost["val"].reindex(q.index))
    q["gp"] = gpv
    q["sh"] = sh["val"].reindex(q.index)
    # 沒有稀釋股數（例：Alphabet 只按股別揭露）→ 用 淨利 ÷ 稀釋 EPS 反推
    implied = (q["ni"] / eps["val"].reindex(q.index)).where(eps["val"].reindex(q.index).abs() > 0.01)
    q["sh"] = q["sh"].fillna(implied.where(implied > 0))
    q["dps"] = dps["val"].reindex(q.index)
    for name, lst in (("inv", INV), ("equity", EQ), ("cash", CASH)):
        s = instants(j, lst)
        q[name] = s.reindex(q.index)
    sti = instants(j, STI).reindex(q.index).fillna(0)
    q["cash"] = q["cash"] + sti
    lt = instants(j, DEBT).reindex(q.index)
    st = instants(j, DEBT_ST).reindex(q.index).fillna(0)
    q["debt"] = lt.fillna(0) + st
    q = q[q.index >= "2007-01-01"].copy()
    q["sh"] = q["sh"].ffill()
    shf = q[["sh"]].rename(columns={"sh": "val"})
    shf["filed"] = q["filed"]
    splits = detect_splits(shf.dropna(subset=["val"]), restatement_ratios(j))
    # 換成「資料最後一天」的股數口徑：之後每一次分割都乘上去
    fac = pd.Series(1.0, index=q.index)
    for d, r in splits.items():
        fac[q.index < d] *= r
    q["split_fac"] = fac
    q["sh_now"] = q["sh"] * fac                  # 今日口徑的稀釋股數
    q["dps_now"] = q["dps"] / fac                # 今日口徑的每股股利
    q["ticker"] = ticker
    q.index.name = "period_end"
    q = q.reset_index()
    q["avail"] = q["filed"].where(q["filed"].notna(), q["period_end"] + pd.Timedelta(days=60))
    # 申報日不可能早於季末；太晚（>150 天）代表那是後來補的比較期數字，保留（保守）
    return q, splits


def stooq_monthly(path):
    d = pd.read_csv(path)
    d.columns = [c.strip("<>").lower() for c in d.columns]
    d["date"] = pd.to_datetime(d["date"].astype(str), format="%Y%m%d")
    d = d.set_index("date")["close"]
    m = d.resample("ME").last().dropna()
    return m


def unadjust_dividends(adj_m, q):
    """把 Stooq 的股利還原拿掉：F(t) = Π_{除息日 d > t} (1 − y_d)，真實價 = 還原價 ÷ F(t)。

    y_d 由財報的每股股利（今日口徑）與還原價反推：c = DPS × F(d) / A(d−)，y = c / (1 + c)。
    除息日近似為該季最後一個月（誤差 < 一季，對本益比影響約 0.1–0.5%）。
    """
    F = pd.Series(1.0, index=adj_m.index)
    divs = q[["period_end", "dps_now"]].dropna()
    divs = divs[divs["dps_now"] > 0].sort_values("period_end", ascending=False)
    f_after = 1.0
    for r in divs.itertuples():
        ex = r.period_end + pd.offsets.MonthEnd(0)
        before = adj_m[adj_m.index < ex]
        if before.empty:
            continue
        a_prev = before.iloc[-1]
        c = r.dps_now * f_after / a_prev
        if c > 1.0:          # 每股股利 > 股價：XBRL 標錯單位（例：STX 2024Q4 把總額標成每股），略過
            continue
        y = c / (1 + c)
        f_after *= (1 - y)
        F[F.index < ex] = f_after
    return adj_m / F, F


def splitonly_monthly(path):
    """只做分割還原的日收盤（blakeweaver17-del/ai-infra-data 格式：date,...,close,adj_close）。"""
    d = pd.read_csv(path, parse_dates=["date"]).set_index("date")["close"]
    return d.resample("ME").last().dropna()


def assemble_price(stooq_path, splitonly_path, q):
    """月底「只分割還原」股價。有分割專用序列就用它（精確），之前的年份用 Stooq 去股利還原後接上。"""
    adj = stooq_monthly(stooq_path) if stooq_path and os.path.exists(stooq_path) else None
    src = "stooq-unadj"
    if adj is not None:
        raw, _ = unadjust_dividends(adj, q)
    if splitonly_path and os.path.exists(splitonly_path):
        so = splitonly_monthly(splitonly_path)
        if adj is None:
            return so, "splitonly"
        ov = pd.concat([raw.rename("a"), so.rename("b")], axis=1).dropna()
        ratio = float(np.median((ov["b"] / ov["a"]).iloc[:6])) if len(ov) >= 6 else 1.0
        head = raw[raw.index < so.index.min()] * ratio        # 口徑對齊（也吸收兩序列之間的分割差）
        return pd.concat([head, so]).sort_index(), f"stooq-unadj<{so.index.min().date()}×{ratio:.3f}+splitonly"
    return raw, src


def load_universe(facts_dirs, stooq_dir, splitonly_dir, universe):
    """universe：DataFrame(ticker, cik, sector, start, end)。

    facts_dirs：依優先序（較新的快照放前面）。同一家公司取第一個找得到的檔。
    回傳 quarters、prices、每家公司的建檔紀錄。
    """
    qs, ps, log = [], [], []
    for r in universe.itertuples():
        fname = f"CIK{int(r.cik):010d}.json"
        fp = next((os.path.join(d, fname) for d in facts_dirs if os.path.exists(os.path.join(d, fname))), None)
        sp = os.path.join(stooq_dir, f"{r.ticker.lower().replace('.', '-')}.us.txt")
        so = os.path.join(splitonly_dir, f"{r.ticker}.csv") if splitonly_dir else None
        if fp is None or not (os.path.exists(sp) or (so and os.path.exists(so))):
            log.append(dict(ticker=r.ticker, status="missing"))
            continue
        q, splits = company_quarters(fp, r.ticker)
        if q is None or q["rev"].notna().sum() < 12:
            log.append(dict(ticker=r.ticker, status="no revenue"))
            continue
        start = pd.Timestamp(r.start) if isinstance(r.start, str) and r.start else None
        end = pd.Timestamp(r.end) if isinstance(r.end, str) and r.end else None
        if start is not None:
            q = q[q["period_end"] >= start]
        if end is not None:
            q = q[q["period_end"] <= end]
        px_raw, src = assemble_price(sp, so, q)
        # 市值 = 只分割還原的股價（最新口徑）× 最新口徑股數（當月以前最新一季）
        sh = q[["avail", "sh_now"]].dropna().sort_values("avail")
        px = pd.DataFrame({"month_end": px_raw.index, "px": px_raw.values})
        px = pd.merge_asof(px, sh, left_on="month_end", right_on="avail", direction="backward")
        px["mc"] = px["px"] * px["sh_now"]
        px["ticker"] = r.ticker
        px["month"] = px["month_end"] - pd.offsets.MonthBegin(1)
        if start is not None:
            px = px[px["month_end"] >= start]
        if end is not None:
            px = px[px["month_end"] <= end]
        ps.append(px[["ticker", "month", "mc", "px"]].dropna(subset=["mc"]))
        qs.append(q)
        log.append(dict(ticker=r.ticker, status="ok", facts=os.path.basename(os.path.dirname(fp)),
                        quarters=int(q["rev"].notna().sum()),
                        first=str(q["period_end"].min().date()), last=str(q["period_end"].max().date()),
                        last_filed=str(q["filed"].max().date()), px_last=str(px["month_end"].max().date()),
                        price_src=src, splits=";".join(f"{d.date()}:{v:g}" for d, v in splits.items())))
    return pd.concat(qs, ignore_index=True), pd.concat(ps, ignore_index=True), pd.DataFrame(log)


def load_macro(data_dir):
    y = pd.read_csv(os.path.join(data_dir, "us10y_monthly.csv"), parse_dates=["Date"])
    c = pd.read_csv(os.path.join(data_dir, "cpi_us_monthly.csv"), parse_dates=["Date"])
    m = pd.DataFrame({"month": y["Date"], "y10": y["Rate"] / 100.0})
    c = c.set_index("Date")["Index"]
    infl = (c / c.shift(12) - 1).rename("infl").reset_index().rename(columns={"Date": "month"})
    m = m.merge(infl, on="month", how="outer").sort_values("month")
    last = m.dropna(subset=["y10"])["month"].max()
    # 延伸到今天：總體資料比股價晚一兩個月，缺的月份沿用最後一個值（y10_asof 記錄實際用的是哪個月）
    ext = pd.DataFrame({"month": pd.date_range(m["month"].min(), pd.Timestamp.today().normalize(), freq="MS")})
    m = ext.merge(m, on="month", how="left")
    m["y10_asof"] = m["month"].where(m["y10"].notna()).ffill()
    m[["y10", "infl"]] = m[["y10", "infl"]].ffill()
    return m

#!/usr/bin/env python3
"""
early_warning_search.py — 用崩盤風險對照台現有的資料，找「能在大跌前提前預警」的指標組合，並誠實檢驗

問題設定
- 事件：S&P 500 15% 波段（zigzag）中，「新一輪大跌的第一個高點」＝前一個低點之後已反彈 ≥30% 的高點。
  1997 年以來共 9 次：1998、2000、2007、2010、2011、2018、2020、2022、2025。
- 「提前預警」：訊號在高點之前 6 個月內（[−126, −1] 交易日）亮過。
- 假警報：一段亮燈（間隔 <20 天視為同一段）開始後 126 天內，S&P 沒有從亮燈當天跌到 −10%。
- 防過度配適：
  ① 1997–2011（5 次）挑規則，2012–2026（4 次）驗證；
  ② 運氣基準：把訊號整段循環平移 300 次（保留亮燈的長度與叢集），看隨機時間點能「預警」幾次；
  ③ 只搜尋單一條件與兩兩 AND，門檻只用 70/80/90/95 百分位，不做細調。

用法：python scripts/early_warning_search.py [--cache DIR]
輸出：data/backtest/early_warning_search.json
"""
import argparse, itertools, json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from risk_board_backtest import build_board, yahoo, perf, hysteresis, COST  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "backtest", "early_warning_search.json")
START, SPLIT = "1997-01-02", "2012-01-01"
LEAD = 126
RNG = np.random.default_rng(7)


def zigzag(px, thr=0.15):
    ev, mode, hi, lo, prev_lo = [], "up", 0, 0, 0
    for i in range(1, len(px)):
        if mode == "up":
            if px[i] > px[hi]:
                hi = i
            elif px[i] / px[hi] - 1 <= -thr:
                mode, lo = "down", i
        else:
            if px[i] < px[lo]:
                lo = i
            elif px[i] / px[lo] - 1 >= thr:
                ev.append((hi, lo, prev_lo)); prev_lo = lo; mode, hi = "up", i
    if mode == "down":
        ev.append((hi, lo, prev_lo))
    return ev


def episodes(sig, gap=20):
    on = np.flatnonzero(sig)
    if not len(on):
        return []
    eps, s0, last = [], on[0], on[0]
    for i in on[1:]:
        if i - last > gap:
            eps.append((s0, last)); s0 = i
        last = i
    eps.append((s0, last))
    return eps


def evaluate(sig, tops, px, fwd_hit):
    hits = [bool(sig[max(0, p - LEAD):p].any()) for p in tops]
    leads = [int(p - (max(0, p - LEAD) + int(np.argmax(sig[max(0, p - LEAD):p])))) if h else None for p, h in zip(tops, hits)]
    eps = episodes(sig)
    good = [fwd_hit[s] for s, _ in eps if not np.isnan(fwd_hit[s])]
    return {"hits": int(sum(hits)), "of": len(tops), "hit_list": hits, "lead_days": leads,
            "on_pct": round(float(sig.mean()) * 100, 1), "alerts": len(eps),
            "alert_precision": round(float(np.mean(good)) * 100, 0) if good else None}


def chance(sig, tops, n=300):
    L = len(sig)
    res = []
    for _ in range(n):
        k = int(RNG.integers(252, L - 252))
        s = np.roll(sig, k)
        res.append(sum(bool(s[max(0, p - LEAD):p].any()) for p in tops))
    return float(np.mean(res)), np.array(res)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cache"); a = ap.parse_args()
    D, st, spy, ser = build_board(a.cache, live_cri=False)
    idx = D.index
    f = lambda s: s.reindex(idx.union(s.index)).ffill().reindex(idx)
    tnx, irx = f(ser["tnx"]), f(ser["irx"])
    # 額外特徵（都只用當天以前的資料）
    D["curve"] = tnx - irx                                           # 10Y−3M
    D["curve_min12"] = D["curve"].rolling(252).min()
    D["uninvert"] = np.where(D["curve_min12"] < 0, D["curve"] - D["curve_min12"], 0)   # 倒掛後回升幅度
    spx = D["spx"]
    D["spx_12m"] = (spx / spx.shift(252) - 1) * 100
    D["vix"] = f(ser["vix"])
    sx = f(ser["sox"])
    D["sox_rel63"] = ((sx / sx.shift(63)) - (spx / spx.shift(63))) * 100                # 半導體相對大盤 3 個月
    vw = f(ser["vwehx"]); D["credit_63"] = (vw / vw.shift(63) - 1) * 100
    roll = lambda x: x.rolling(756, min_periods=252).rank(pct=True) * 100       # 過去 3 年百分位
    for c in ("skew", "vix", "move", "cri", "credit_dd", "sox_rel63"):
        D[c + "_p3y"] = roll(D[c])
    D = D[D.index >= START]
    px = D["spx"].values
    n = len(px)
    fwd_dd = np.full(n, np.nan)
    for i in range(n - LEAD):
        fwd_dd[i] = px[i + 1:i + LEAD + 1].min() / px[i] - 1
    fwd_hit = np.where(np.isnan(fwd_dd), np.nan, (fwd_dd <= -0.10).astype(float))

    ev = zigzag(px)
    first = [(h, l) for h, l, pl in ev if pl == 0 or px[h] / px[pl] - 1 >= 0.30]
    tops = [h for h, _ in first]
    top_dates = [D.index[h].date().isoformat() for h in tops]
    split_i = int(np.searchsorted(D.index.values, np.datetime64(SPLIT)))
    tr = [p for p in tops if p < split_i]
    te = [p for p in tops if p >= split_i]
    print("新一輪大跌的第一個高點：", top_dates)

    # 候選條件：(名稱, 欄位, 方向)；方向 +1＝值越大越危險
    feats = [("10Y 12 個月變化", "y10_chg", +1), ("股債差 10Y−1/CAPE", "gap", +1), ("實質政策利率", "real_rate", +1),
             ("升息力道（國庫券 12 個月變化）", "bill_chg", +1), ("油價 12 個月漲幅", "oil_chg", +1),
             ("日圓 3 個月升值", "jpy_3m", -1), ("高收益債距一年高點", "credit_dd", -1), ("高收益債 3 個月報酬", "credit_63", -1),
             ("VIX 期限結構", "vix_term", +1), ("SKEW", "skew", +1), ("半導體距一年高點", "sox_dd", -1),
             ("半導體相對大盤 3 個月", "sox_rel63", -1), ("MOVE", "move", +1), ("CRI", "cri", +1),
             ("S&P 距 200 日線（過熱）", "ma", +1), ("S&P 距 200 日線（轉弱）", "ma", -1),
             ("S&P 12 個月漲幅（過熱）", "spx_12m", +1), ("VIX 過低（自滿）", "vix", -1), ("VIX 偏高", "vix", +1),
             ("殖利率曲線倒掛深度", "curve", -1), ("曲線倒掛後回升", "uninvert", +1), ("CAPE 股債差（同 gap）", "gap", +1),
             ("對照台總分", "board", +1), ("市場分項", "board_market", +1), ("總體分項", "board_macro", +1),
             ("SKEW 3 年百分位", "skew_p3y", +1), ("VIX 3 年百分位（高）", "vix_p3y", +1), ("VIX 3 年百分位（低＝自滿）", "vix_p3y", -1),
             ("MOVE 3 年百分位", "move_p3y", +1), ("CRI 3 年百分位", "cri_p3y", +1), ("信用回撤 3 年百分位（深）", "credit_dd_p3y", -1),
             ("半導體相對弱勢 3 年百分位", "sox_rel63_p3y", -1)]
    feats = list({(c, d): (nm, c, d) for nm, c, d in feats}.values())
    trainD = D.iloc[:split_i]
    conds = {}
    for nm, c, d in feats:
        x = D[c].values
        base = trainD[c].dropna()
        if len(base) < 500:
            continue
        for q in (70, 80, 90, 95):
            thr = np.percentile(base, q if d > 0 else 100 - q)
            sig = np.nan_to_num((x >= thr) if d > 0 else (x <= thr), nan=0).astype(bool)
            sig &= ~np.isnan(x)
            conds[f"{nm} {'≥' if d > 0 else '≤'} {thr:.2f}（{q} 分位）"] = sig

    def score(sig, tl):
        return evaluate(sig, tl, px, fwd_hit)

    rows = []
    names = list(conds)
    for k in names:
        rows.append((k, conds[k]))
    for k1, k2 in itertools.combinations(names, 2):
        if k1.split(" ")[0] == k2.split(" ")[0]:
            continue
        rows.append((f"{k1}  且  {k2}", conds[k1] & conds[k2]))
    print(f"候選規則 {len(rows)} 條")
    def chance_in(sig, tl, n=200):
        L = len(sig); r = []
        for _ in range(n):
            k = int(RNG.integers(126, L - 126)); s2 = np.roll(sig, k)
            r.append(sum(bool(s2[max(0, p - LEAD):p].any()) for p in tl))
        r = np.array(r); return float(r.mean()), r
    res = []
    for k, sig in rows:
        on = sig[:split_i].mean()
        if on < 0.02 or on > 0.20:
            continue
        e = score(sig[:split_i], tr)
        if e["hits"] < 4:
            continue
        mu, dist = chance_in(sig[:split_i], tr, 150)
        res.append((k, e["hits"], float((dist >= e["hits"]).mean()), e["hits"] - mu, sig))
    res.sort(key=lambda r: (-r[2], r[3]), reverse=True)            # p 值越小越前面，其次超額命中
    res.sort(key=lambda r: r[2])
    top = res[:15]
    out_rules = []
    for k, h, ptr, ex, sig in top:
        e_tr = score(sig[:split_i], tr)
        sig_te = sig[split_i:]; te_l = [p - split_i for p in te]
        e_te = score(sig_te, te_l)
        mu_te, d_te = chance_in(sig_te, te_l)
        e_all = score(sig, tops)
        mu, dist = chance(sig, tops)
        out_rules.append({"rule": k, "train": e_tr, "train_p": round(ptr, 3), "test": e_te,
                          "test_chance": round(mu_te, 2), "test_p": round(float((d_te >= e_te["hits"]).mean()), 3),
                          "test_on_pct": e_te["on_pct"], "all": e_all,
                          "chance_mean_hits": round(mu, 2), "p_value": round(float((dist >= e_all["hits"]).mean()), 3)})
    # 對照組：現有規則與單一指標
    refs = {"對照台總分 ≥35": np.nan_to_num(D["board"].values >= 35).astype(bool),
            "CRI ≥ 50": np.nan_to_num(D["cri"].values >= 50).astype(bool),
            "S&P 跌破 200 日線": np.nan_to_num(D["ma"].values < 0).astype(bool),
            "殖利率曲線倒掛（10Y<3M）": np.nan_to_num(D["curve"].values < 0).astype(bool)}
    ref_out = {}
    for k, sig in refs.items():
        e = score(sig, tops); mu, dist = chance(sig, tops)
        ref_out[k] = {**e, "chance_mean_hits": round(mu, 2), "p_value": round(float((dist >= e["hits"]).mean()), 3)}

    # 「全部抓到」需要多常亮？——每個單一條件在 9 次裡的最佳表現與亮燈率
    best_single = sorted(((k, score(conds[k], tops)) for k in names), key=lambda r: (r[1]["hits"], -r[1]["on_pct"]), reverse=True)[:10]

    # 最佳（訓練期挑出）規則的交易回測：亮燈＝出場，連續 20 天不亮才回場
    ret = spy.pct_change().reindex(D.index).fillna(0)
    cash = (f(ser["irx"]).reindex(D.index) / 100 / 252).fillna(0)
    bt = {}
    mad = D["ma"].values
    def armed_trend(warn, arm_days=126):
        armed = pd.Series(warn.astype(float)).rolling(arm_days, min_periods=1).max().values > 0
        return hysteresis(armed & (mad < 0), mad > 0)
    cands = {"買進持有": np.ones(n), "只看 200 日線": hysteresis(mad < 0, mad > 0),
             "總分≥35 且跌破 200 日線（現行規則 3 B）": hysteresis((np.nan_to_num(D["board"].values) >= 35) & (mad < 0),
                                                       (pd.Series(np.nan_to_num(D["board"].values) < 30).rolling(10).sum().values == 10) & (mad > 0))}
    for r in out_rules[:5]:
        cands["預警亮過＋跌破 200 日線：" + r["rule"]] = armed_trend(dict(rows)[r["rule"]])
    for k in ("對照台總分 ≥35",):
        cands["預警亮過＋跌破 200 日線：" + k] = armed_trend(np.nan_to_num(D["board"].values >= 35).astype(bool))
    for name, w in cands.items():
        bt[name] = {}
        for pn, (a0, a1) in {"全期": (START, None), "訓練 1997–2011": (START, "2011-12-31"), "驗證 2012–2026": (SPLIT, None)}.items():
            m = (D.index >= a0) & ((D.index <= a1) if a1 else True)
            bt[name][pn] = perf(ret[m], cash[m], w[m], D.index[m])[0]

    out = {"generated": pd.Timestamp.today().date().isoformat(), "first_tops": top_dates,
           "train_tops": [D.index[p].date().isoformat() for p in tr], "test_tops": [D.index[p].date().isoformat() for p in te],
           "n_candidates": len(rows), "top_rules": out_rules, "references": ref_out,
           "best_single_all_period": [{"rule": k, **v} for k, v in best_single], "trade_backtest": bt}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"references": ref_out}, ensure_ascii=False, indent=1, default=str)[:3000])
    print("\n訓練期最佳 15 條：")
    for r in out_rules:
        print(f"- {r['rule']}\n    訓練 {r['train']['hits']}/{r['train']['of']} p={r['train_p']} | 驗證 {r['test']['hits']}/{r['test']['of']}（運氣 {r['test_chance']}，p={r['test_p']}，亮燈 {r['test_on_pct']}%）"
              f" | 全期 {r['all']['hits']}/9 亮燈 {r['all']['on_pct']}% 警報 {r['all']['alerts']} 次 準 {r['all']['alert_precision']}% 運氣 {r['chance_mean_hits']} p={r['p_value']} {''.join('●' if x else '○' for x in r['all']['hit_list'])}")
    print("\n單一條件全期最佳：")
    for r in out["best_single_all_period"]:
        print(f"- {r['rule']}: {r['hits']}/9 亮燈 {r['on_pct']}% 警報 {r['alerts']} 準 {r['alert_precision']}%")
    print("\n交易回測（年化/最大回撤/Sharpe/進出次數）：")
    for k, v in bt.items():
        print(f"- {k}\n    " + " | ".join(f"{p} {x['cagr']}%/{x['mdd']}%/S{x['sharpe']}/{x['switches']}x" for p, x in v.items()))


if __name__ == "__main__":
    main()

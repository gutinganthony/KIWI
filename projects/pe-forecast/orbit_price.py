#!/usr/bin/env python3
"""本益比軌道模型：給 EPS（你的看法，可加市場共識），算 h 個月後的本益比與股價區間（README §16）。

    python3 orbit_price.py MU --eps 70 --eps2 85                       # 12 個月後；EPS＝那時已公布的最近四季（GAAP 稀釋）
    python3 orbit_price.py MU --eps 70 --eps2 85 --cons 65 --cons2 78  # 加上市場共識（同口徑）：模型分開算「市場預期」與「你的看法」
    python3 orbit_price.py MU --fy "2027-08:72,2028-08:90" --fy-cons "2027-08:65,2028-08:80"
                                                                       # 用會計年度 EPS（年度結束月:EPS），自動換算成目標日的最近四季
    python3 orbit_price.py MU --eps 55,70,85 --eps2 70,85,100          # 悲觀／基準／樂觀（逗號分隔，一一對應）
    python3 orbit_price.py NVDA --eps 9 --h 24                         # 6、12、24 個月
    python3 orbit_price.py MU --eps 70 --eps2 90 --cons auto           # 自動抓 Yahoo 共識（本財年、下一財年；pef/consensus.py），並用共識校正模型換成預期的 GAAP
    python3 orbit_price.py NVDA --eps 9 --cons auto --rate-view -1     # 利率情境：你認為 10 年期到目標日會降 1 個百分點（README §19.3）
    python3 orbit_price.py TSM --cons auto                             # 外國公司 ADR：讀 data/adr_now.csv（每 ADR 美元口徑，adr_fetch.py）
    python3 orbit_price.py MU --cons auto                              # 沒有自己的看法：共識模式，區間用 conformal 校準（README §26.2）
    python3 orbit_price.py MU --eps 70 --eps2 90 --cons auto --eb-kind market
                                                                       # EPS_b 是「市場在目標日會預期的下一年 EPS」（不是你的基本面預估）→ 成長定價的係數（README §26.1）
第十輪（README §26）起只有一個模型（pef/unified.py）：軌道是本體；EPS_b 標成基本面預估（預設）走軌道的小 β，標成市場預期走成長定價的係數；
只有共識時區間用 conformal；另給「相對大盤」（扣掉同一天 S&P 500 只用共識的預測中位，results/relative_dist.json）。
共識 EPS 也可以放在 data/consensus.csv（欄位：ticker, fy_end, eps, source, asof；同一年度取 asof 最新的一筆），
沒給 --cons／--fy-cons 時自動讀；你在命令列給的永遠優先。--cons auto：先用 7 天內的快照（data/consensus_snapshots/），
沒有就即時抓並存成今天的快照；再抓 quoteSummary（分析師人數、90 天修正、精確的會計年度、調整後實際 EPS），
再用共識校正模型（pef/eps_correct.py，README §19.1）把共識換成「預期的實際 GAAP EPS」（--no-correct：改用舊的
「GAAP ÷ 調整後最近四季」口徑係數；--cons-scale 自己指定，1＝不換）。係數先乘在會計年度共識上，再換算成目標日的最近四季。
今天的股價：先試 Yahoo（今天收盤），失敗就用 results/now_all.csv；不在裡面的外國公司 ADR 用 data/adr_now.csv。
不是投資建議。
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import growth_price as GP                       # noqa: E402
from pef import consensus, eps_correct, orbit, unified, yahoo    # noqa: E402

RES = os.path.join(HERE, "results")


def parse_list(s):
    return [float(v) for v in s.split(",")] if s else []


def parse_fy(s):
    """"2027-08:72,2028-08:90" → {年度結束日（月底）: EPS}"""
    out = {}
    for part in (s or "").split(","):
        if part.strip():
            k, v = part.split(":")
            out[pd.Timestamp(k.strip() + ("-01" if len(k.strip()) == 7 else "")) + pd.offsets.MonthEnd(0)] = float(v)
    return out


def consensus_from_file(ticker):
    path = os.path.join(HERE, "data", "consensus.csv")
    if not os.path.exists(path):
        return {}, None
    c = pd.read_csv(path, parse_dates=["fy_end", "asof"], comment="#", dtype={"ticker": str})
    c = c[c["ticker"].fillna("").str.upper().str.replace(".", "-", regex=False) == ticker]
    if c.empty:
        return {}, None
    c = c.sort_values("asof").groupby("fy_end").tail(1)
    fy = {pd.Timestamp(r.fy_end) + pd.offsets.MonthEnd(0): float(r.eps) for r in c.itertuples()}
    return fy, f"{c['source'].iloc[-1]}，{c['asof'].max().date()}"


def adr_row(t):
    """外國公司 ADR（data/adr_now.csv，adr_fetch.py）：股價、最近四季 EPS、共識都已換成每 ADR 美元；口徑檢查沒過的不給用。"""
    path = os.path.join(HERE, "data", "adr_now.csv")
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path, parse_dates=["period_end", "price_date", "last_fy"])
    hit = d[d["ticker"] == t]
    if hit.empty:
        return None
    row = hit.iloc[0].to_dict()
    if not bool(row.get("conv_ok")):
        sys.exit(f"{t}：ADR 的 EPS 口徑換算沒通過檢查（{row.get('conv_note')}）→ 不給算，以免股價和 EPS 單位對不上")
    row["adr"] = True
    return row


def today_row(t):
    d = pd.read_csv(os.path.join(RES, "now_all.csv"), parse_dates=["period_end", "price_date"])
    hit = d[(d["ticker"] == t) | d["aliases"].fillna("").str.split().apply(lambda s: t in s)]
    row = hit.iloc[0].to_dict() if len(hit) else adr_row(t)
    if row is None:
        sys.exit(f"找不到 {t}（results/now_all.csv 只有有季報的美股；外國公司 ADR 見 data/adr_now.csv，約 100 檔）")
    y = yahoo.chart(t, "5d", "1d")
    if y is not None and len(y["close"]):
        new_px = float(y["close"].iloc[-1])
        if row["px"] > 0 and abs(np.log(new_px / row["px"])) < 1.0:          # 防止分割造成的口徑跳動
            row["eps0"] = row["eps0"]                                          # EPS 口徑不變（股數同為分割調整後）
            row["px"], row["price_date"] = new_px, y["close"].index[-1]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--h", type=int, default=12, choices=[6, 12, 24])
    ap.add_argument("--eps", help="你的 h 個月後 EPS（那時已公布的最近四季；逗號＝多個情境）")
    ap.add_argument("--eps2", help="你的 h＋12 個月後 EPS（同上；和 --eps 一一對應）")
    ap.add_argument("--cons", help="市場共識：h 個月後的最近四季 EPS；或 auto＝自動抓 Yahoo 共識")
    ap.add_argument("--cons2", type=float, help="市場共識：h＋12 個月後的最近四季 EPS")
    ap.add_argument("--fy", help="你的會計年度 EPS，例如 \"2027-08:72,2028-08:90\"")
    ap.add_argument("--fy-cons", help="市場共識的會計年度 EPS，格式同 --fy")
    ap.add_argument("--cons-scale", type=float, default=None,
                    help="共識乘上這個數（調整後口徑 → GAAP，例如 0.8）；--cons auto 時預設用 GAAP ÷ 調整後的最近四季自動換算")
    ap.add_argument("--no-correct", action="store_true", help="--cons auto 時不用共識校正模型，改用舊的口徑係數（GAAP ÷ 調整後最近四季）")
    ap.add_argument("--rate-view", type=float, default=None,
                    help="利率情境：你認為到目標日 10 年期殖利率會變多少個百分點（-1＝降 1 個百分點）；市場已預期的部分已在軌道裡")
    ap.add_argument("--rate-regime", default="2022", choices=["2022", "2012"],
                    help="利率情境用哪段期間的反應：2022＝2022 以後的通膨期（預設）、2012＝2012–2021 低通膨期")
    ap.add_argument("--eb-kind", default="fund", choices=["fund", "market"],
                    help="--eps2 的意思：fund＝你的基本面預估（預設；軌道的小係數）、market＝你判斷市場在目標日會預期的下一年 EPS（成長定價的係數；只有 12、24 個月）")
    ap.add_argument("--erp", type=float, default=None, help="股權風險溢酬（預設 0.05）")
    ap.add_argument("--level", type=int, default=80, choices=[60, 70, 80, 90], help="外圍區間的涵蓋水準（預設 80；核心區間固定 50。越低越窄、命中率越低；README §27）")
    a = ap.parse_args(sys.argv[1:])
    t = a.ticker.upper().replace(".", "-")
    model = orbit.load_model(RES)
    row = today_row(t)
    notes = []
    y_new, y_m = orbit.latest_y10()
    if y_new is not None and not row.get("adr") and abs(y_new - float(row["y10"])) > 1e-9:
        notes.append(f"10 年期殖利率用 FRED 最新值 {y_new:.2%}（{y_m:%Y-%m}，data/rates_monthly.csv；results/now_all.csv 裡的是 {float(row['y10']):.2%}，較舊）")
        row["y10"] = y_new
    use_auto = str(a.cons or "").lower() == "auto"
    snap, snap_src = consensus.get_row(t, os.path.join(HERE, "data", "consensus_snapshots"), live=use_auto)
    cache = os.path.join(HERE, ".cache", "yahoo")
    qs = consensus.quote_summary(t, cache) if use_auto else None   # 完整分析師資料（要 fc.yahoo.com、query2 網域）
    rf = consensus.refresh_eps(row, snap, mrq=(qs or {}).get("mrq"))   # 快照比 now_all.csv 新、又公布了新的季 → 改用 Yahoo 的 GAAP 最近四季
    if rf["n_new"]:
        row["eps0"], row["period_end"] = rf["eps0"], rf["period_end"]
        notes.append(rf["note"])
    asof = pd.Timestamp(row["price_date"])
    ta, tb = asof + pd.DateOffset(months=a.h), asof + pd.DateOffset(months=a.h + 12)
    eps0 = float(row["eps0"])

    # 你的 EPS
    if a.fy:
        fy = parse_fy(a.fy)
        ea, how_a = orbit.calendarize(fy, ta, row["period_end"], eps0)
        eb, how_b = orbit.calendarize(fy, tb, row["period_end"], eps0)
        if ea is None:
            sys.exit(f"--fy 換算不出 {a.h} 個月後的最近四季 EPS：請多給一個會計年度，或直接用 --eps")
        mine = [(ea, eb)]
        notes.append(f"你的 EPS 由會計年度換算：a＝{how_a}；b＝{how_b or '換算不出（請多給一年或用 --eps2）'}")
    else:
        la, lb = parse_list(a.eps), parse_list(a.eps2)
        if not la:
            la = []
        if lb and len(lb) != len(la):
            sys.exit("--eps2 的個數要和 --eps 一樣")
        mine = [(v, lb[i] if lb else None) for i, v in enumerate(la)]

    # 市場共識：命令列數字（--cons／--cons2）> --fy-cons > data/consensus.csv > --cons auto（Yahoo）
    ca = None
    if a.cons is not None and not use_auto:
        try:
            ca = float(a.cons)
        except ValueError:
            sys.exit(f"--cons 要給數字或 auto（收到 {a.cons!r}）")
    cb, csrc = a.cons2, "命令列"
    fyc = parse_fy(a.fy_cons) if a.fy_cons else {}
    if fyc and ca is not None:
        notes.append("同時給了 --cons 和 --fy-cons：EPS_a 用 --cons，--fy-cons 只用在沒給 --cons2 時的 EPS_b")
    if not fyc and ca is None:
        fyc, src = consensus_from_file(t)
        if fyc:
            csrc = f"data/consensus.csv（{src}）"
            if use_auto:
                notes.append("data/consensus.csv 有這一檔 → 用檔案裡的共識，--cons auto 略過（要用 Yahoo 就先刪掉檔案裡那幾列）")
    scale, scale_src = None, None                       # 乘在共識上的係數（先乘會計年度共識，再換算）
    is_adr = bool(row.get("adr"))
    if not fyc and ca is None and use_auto and is_adr:
        lf = pd.Timestamp(row["last_fy"])
        fyc = {lf + pd.DateOffset(months=12 * k) + pd.offsets.MonthEnd(0): float(row[c])
               for k, c in ((1, "cons_0y"), (2, "cons_1y")) if pd.notna(row.get(c))}
        csrc = f"data/adr_now.csv（Yahoo，已換成每 ADR 美元，{pd.Timestamp(row['price_date']).date()}）"
        notes.append("外國公司 ADR：共識校正模型只用 S&P 500 訓練、沒有在外國公司驗證過 → 不校正（要換算請用 --cons-scale）；"
                     "ADR 回測見 README §19.4（扣掉大盤偏差後和 S&P 500 接近，但外國股 2024–25 年整體比軌道多漲）")
        use_auto = False
    if not fyc and ca is None and use_auto:
        au = consensus.auto(t, snap, snap_src, cache, qs=qs)
        if au is None:
            notes.append("--cons auto：Yahoo 沒有這一檔的共識（或抓不到會計年度），改用沒有共識的寫法")
        else:
            fyc, csrc = au["fy"], au["source"]
            k = [f"{e.date()} {v:,.2f}" for e, v in sorted(au["fy"].items())]
            notes.append(f"Yahoo 共識：本財年／下一財年 {'、'.join(k)}（本財年＝還沒公布的最早那一年）")
            v0 = sorted(au["fy"].items())[0][1]
            k_ok = au["basis_k"] is not None and 0.4 <= au["basis_k"] <= 1.15
            if eps0 > 0:
                notes.append(f"口徑對照：本財年共識 ÷ 目前 GAAP 最近四季 ＝ {v0 / eps0:.2f}"
                             + ("（> 1.5：可能是高成長，也可能是共識用調整後口徑——軟體、股票報酬費用高的公司通常是後者，"
                                "那就用 --cons-scale 換算）" if v0 / eps0 > 1.5 and not k_ok and a.no_correct else ""))
            elif v0 > 0:
                notes.append("⚠ 今天 GAAP 虧損、共識卻是正的：共識幾乎一定是調整後口徑。你的 EPS 若是 GAAP，"
                             "「你和共識的差距」會被系統性低估 → 用 --cons-scale、或手動給 GAAP 口徑的共識")
            notes += ["  " + i for i in au["info"]]
            notes += ["⚠ " + w for w in au["warn"]]
            k = au["basis_k"]
            cr = None
            big = str(row.get("in_sp500")).lower() == "true" or str(row.get("in_ndx")).lower() == "true"
            if a.cons_scale is None and not a.no_correct:
                t0 = ((qs or {}).get("trend") or {}).get("0y") or {}
                cr = eps_correct.for_ticker(t, row, v0, au["fy0"], t0.get("d30"), t0.get("d90"), (qs or {}).get("last_fy"), today=asof,
                                            scope="big" if big else "small")
            if cr is not None and cr["small_note"]:
                notes.append(cr["small_note"])
                cr = None
                k = None                                           # 中小型股、距離年報 ≥ 9 個月：共識照原樣用
            if cr is not None:
                scale, scale_src = cr["factor"], "共識校正模型"
                dr = "、".join(f"{n_}（{v:,.3g}）{e:+.2f}" for n_, v, e in cr["drivers"])
                notes.append(f"共識校正（README §19.1{'、§20.3 中小型股' if not big else ''}）：預期實際 GAAP ÷ 共識 ＝ {cr['factor']:.2f}"
                             f"（距離本財年年報約 {cr['feats']['lead']:.1f} 個月）；"
                             f"影響最大的線索：{dr}" + ("" if cr["known"] else "；這家沒有歷史共識紀錄，沒有「過去偏差」可用"))
                if cr["guard"]:
                    notes.append("  " + cr["guard"] + "（README §20.2）")
                notes.append(("  樣本外（S&P 500，2015 以後）：EPS 誤差中位 0.144 → 0.110（含同時點護欄）；12 個月本益比誤差（2022 以後）0.221 → 0.194；" if big else
                              "  樣本外（中小型股，2020–2024、距離年報 < 9 個月）：EPS 誤差中位 0.214 → 0.185；")
                             + "下一財年用同一個係數（沒驗證過）"
                             + (f"；舊做法的口徑係數＝{k:.2f}（加 --no-correct 改用它）" if k is not None else ""))
            elif a.cons_scale is None and k is not None:
                if 0.4 <= k <= 1.15:
                    if abs(k - 1) > 0.03:
                        scale, scale_src = k, "口徑係數：GAAP ÷ 調整後最近四季"
                        notes.append(f"口徑：GAAP 最近四季 ÷ 調整後最近四季 ＝ {k:.2f} → 共識自動 × {k:.2f} 換成 GAAP"
                                     "（不要換算就加 --cons-scale 1）")
                else:
                    notes.append(f"⚠ 口徑係數 {k:.2f} 不合理（GAAP 虧損或一次性損益）→ 不自動換算；你的 EPS 若是 GAAP，請用 --cons-scale 自己換")
    if a.cons_scale is not None:
        scale, scale_src = a.cons_scale, "--cons-scale"
    ca_cmd, cb_cmd = ca is not None, cb is not None
    if scale is not None and scale != 1.0:
        fyc = {e: v * scale for e, v in fyc.items()}
        manual = scale_src == "--cons-scale"                 # 命令列直接給的共識數字只乘你自己指定的係數，不乘自動算的
        ca = ca * scale if (ca_cmd and manual) else ca
        cb = cb * scale if (cb_cmd and manual) else cb
        notes.append(f"共識已乘上 {scale:.2f}（{scale_src}）" + ("；先乘在會計年度共識上，換算時已公布的季仍用 GAAP 實際值" if fyc else "")
                     + ("；命令列給的 --cons／--cons2 數字照原樣用" if (ca_cmd or cb_cmd) and not manual else ""))
    if fyc:
        if ca is None:
            ca, how_ca = orbit.calendarize(fyc, ta, row["period_end"], eps0, extrapolate=True)
        else:
            how_ca = "命令列"
        if cb is None:
            cb, how_cb = orbit.calendarize(fyc, tb, row["period_end"], eps0, extrapolate=True)
        else:
            how_cb = "命令列"
        notes.append(f"共識由會計年度換算：a＝{how_ca}；b＝{how_cb}")
        if "外推" in str(how_ca):
            notes.append("注意：EPS_a 用到外推——歷史上把成長率再延一年，約 24 個月後的 EPS 中位高估約 8%（科技約 21%、半導體約 24%；README §22.5），寧可保守或自己給 EPS")
    if not mine:
        if ca is None:
            sys.exit("請給你的 EPS（--eps／--fy），或提供市場共識（--cons 數字或 auto／--fy-cons／data/consensus.csv）")
        mine = [(None, None)]
        notes.append("沒有給你自己的 EPS：共識模式——EPS 用共識，區間用「只有共識」時的實際誤差校準（conformal，README §26.2）")
    if a.eb_kind == "market" and all(eb is None for _, eb in mine):
        notes.append("--eb-kind market 需要 --eps2（你判斷市場在目標日會預期的下一年 EPS）；沒有 → 當作只有 EPS_a")
    f0 = None                                            # 今天共識的未來 12 個月 EPS：沒有下一財年共識時，回歸的目標日成長預期用（pef/growth_price.py eps_b_hat）
    if fyc:
        f0 = orbit.calendarize(fyc, asof + pd.DateOffset(months=12), row["period_end"], eps0, extrapolate=True)[0]
    elif ca is not None and a.h == 12:
        f0 = ca

    rate = None
    if a.rate_view:
        pr = orbit.pe_rank(float(row["px"]), eps0)
        sl, how = orbit.rate_slope(a.h, a.rate_regime, pr)
        rate = (a.rate_view, sl)
        notes.append(f"利率情境（README §19.3）：10 年期到 {ta.date()} {a.rate_view:+.2f} 個百分點 × 每個百分點 {sl:+.3f} ＝ 股價 "
                     f"{np.exp(a.rate_view * sl) - 1:+.1%}（{how}；本益比百分位 {('—' if pr is None else f'{pr:.0%}')}）")
        notes.append("  這是情境不是預測：市場的升降息預期已在今天的 10 年期裡；同樣是降息，2012–2021 和 2022 以後的反應方向不同。區間不變")
    flag = lambda v: str(v).strip().lower() in ("true", "1", "1.0")
    kind = "adr" if row.get("adr") else (None if (flag(row.get("in_sp500")) or flag(row.get("in_ndx"))) else "small")
    bm = orbit.band_widen(kind, a.h)
    if bm != 1.0:
        notes.append(f"區間放寬 ×{bm:.2f}：" + ("外國公司 ADR 用 S&P 500 校準的區間只涵蓋 68–74%（2023-10～2025-09 起點；README §19.4）"
                                             if kind == "adr" else "不在 S&P 500／Nasdaq-100：中小型股用 S&P 500 校準的區間只涵蓋約 73%（2020–2026；README §19.4）"))
    qa = orbit.reported_quarter(row["period_end"], ta)
    print(f"{row['ticker']}　{row['name']}")
    pe0 = f"{row['px'] / eps0:,.1f}" if eps0 > 0 else "無定義（虧損）"
    print(f"  今天（{asof.date()}）：股價 {row['px']:,.2f}、最近四季 EPS {eps0:,.2f}、本益比 {pe0}；"
          f"類型：{orbit.GNAME[row['grp'] if row.get('grp') in orbit.GNAME else orbit.group_of(row.get('sector'))]}"
          + ("（外國公司 ADR，每 ADR 美元）" if row.get("adr") else ""))
    print(f"  {a.h} 個月後（{ta.date()}）：那時大概已公布到 {qa.date()} 那一季 → EPS_a＝季末 "
          f"{(qa - pd.DateOffset(months=9)).strftime('%Y-%m')}～{qa.strftime('%Y-%m')} 的四季合計；EPS_b＝再往後 12 個月（若公司實際公布得比 45 天快，可能多含一季）")
    if ca is not None:
        print(f"  市場共識（{csrc}）：EPS_a {ca:,.2f}" + (f"、EPS_b {cb:,.2f}" if cb is not None else ""))
    for n_ in notes:
        print("  " + n_)
    gm, cq = GP.load(), unified.load_conformal()
    res = [unified.predict(row, a.h, model=model, gm=gm, cq=cq, eps_a=ea, eps_b=eb, eb_kind=a.eb_kind, cons_a=ca, cons_b=cb, fwd0=f0,
                           rate=rate, band_mult=bm, erp=a.erp) for ea, eb in mine]
    o0 = res[0]
    mode_txt = {"共識": "共識（沒有自己的看法）", "軌道": "軌道（沒有共識）",
                "看法": "看法（EPS_b＝" + ("市場在目標日會預期的數字" if o0.get("kind") == "market" else "我的基本面預估") + "）"}[o0["mode"]]
    cqh = (cq or {}).get("h", {}).get(str(a.h))
    L = a.level if a.level in (o0.get("band_levels") or [50, 80]) else 80
    wfc = (cqh or {}).get("wf_cover") or {}
    cov = lambda k: (f"{wfc[k][str(L)]['avg']:.0%}（最差的一年 {wfc[k][str(L)]['min']:.0%}）" if wfc.get(k, {}).get(str(L)) else "—")   # noqa: E731
    band_txt = (f"conformal（{o0['band_group']}；只有共識時的實際誤差，股價與本益比分開校準）。{L}% 區間走動式實測涵蓋：股價 {cov('px')}、本益比 {cov('pe')}"
                if o0["band_kind"] == "conformal" else "成長定價的殘差校準（假設你的 EPS_a 和市場預期對）" if o0.get("kind") == "market"
                else "模型（假設你的 EPS 對，只含模型誤差）")
    print(f"\n  統一模型（README §26）｜模式：{mode_txt}｜寫法：{o0['spec']}｜軌道（資金成本 − 股利，{a.h} 個月）{np.exp(o0['mk']) - 1:+.1%}")
    print(f"  區間：{band_txt}；寬度：波動 {o0['vol']:.0%}{'' if o0['vol_known'] else '（沒有資料，用中位數）'}，是中位波動股票的 {o0['width']:.2f} 倍"
          + (f"（含放寬 ×{o0['band_mult']:.2f}）" if o0["band_mult"] != 1 else "")
          + (f"（EPS 變化大，再放寬 ×{o0['eps_widen']:.2f}，README §22.4）" if o0.get("eps_widen", 1) > 1.005 else ""))
    if o0.get("note"):
        print("  " + o0["note"])
    print(f"  EPS_a     EPS_b    本益比（中位）  本益比 50%       本益比 {L}%       股價（中位）  股價 50% 區間        股價 {L}% 區間       h 個月後 forward 本益比")
    for o in res:
        pe = (f"{o['pe']:10.1f}     {o['pe_lo50']:5.1f}–{o['pe_hi50']:<6.1f}   {o[f'pe_lo{L}']:5.1f}–{o[f'pe_hi{L}']:<6.1f}" if o["pe"]
              else "    無定義（EPS_a ≤ 0）                      ")
        fwd = f"{o['fwd_pe']:.1f}" if o["fwd_pe"] else "—"
        eb_s = f"{o['eps_b']:,.2f}" if o["eps_b"] is not None else "—"
        ea_s = f"{o['eps_a']:,.2f}" if o["eps_a"] is not None else "—"
        print(f"  {ea_s:>7}  {eb_s:>7}  {pe}  {o['px']:>10,.0f}   "
              f"{o['px_lo50']:>8,.0f}–{o['px_hi50']:<8,.0f}  {o[f'px_lo{L}']:>8,.0f}–{o[f'px_hi{L}']:<8,.0f}   {fwd}")
    if o0["band_kind"] == "conformal" and o0.get(f"eps_lo{L}") is not None:   # §27：共識 EPS 本身會錯多少
        print(f"  共識 EPS_a {o0['eps_a']:,.2f} 本身的 {L}% 區間（歷史共識誤差）：{o0[f'eps_lo{L}']:,.2f}–{o0[f'eps_hi{L}']:,.2f}；"
              "本益比區間比股價區間寬，主要就是這一塊（本益比誤差 ＝ 股價誤差 − EPS 誤差）；填自己的 EPS（--eps）就把它拿掉了")
    if o0.get(f"fwd_lo{L}") is not None:                  # §28：forward 本益比區間（分母是共識，不含 EPS 風險）
        fb = o0.get("fwd_band") or {}
        wc = (fb.get("wf_cover") or {}).get(str(L))
        print(f"  forward 本益比 {o0['fwd_pe']:.1f} 倍（股價 ÷ EPS_b）的 {L}% 區間：{o0[f'fwd_lo{L}']:.1f}–{o0[f'fwd_hi{L}']:.1f}；分母是共識、不含 EPS 風險，所以比本益比區間窄"
              f"（軌道在 Bloomberg 512 檔 2021–2026 的 forward 本益比 MdAPE {fb.get('mdape', float('nan')):.1%}"
              + (f"、{L}% 區間走動式涵蓋 {wc['avg']:.0%}（最差的一年 {wc['min']:.0%}）" if wc else "") + "；README §28）")
    print("\n  拆解（第一個情境）：")
    print(f"    軌道：股價 × exp({o0['mk']:+.3f})  ← 市場看法不變時的預期")
    for p in o0["parts"]:
        print(f"    {p['項目']}：{p['數值']:+.3f} × β {p['β']:+.3f} ＝ {p['影響']:+.3f}")
    d = o0.get("decomp")
    if d:                                                # §27：股價變化 ＝ EPS 成長 × 本益比重估
        print(f"    股價變化拆成兩塊：{float(row['px']):,.2f} → {o0['px']:,.2f}（{np.exp(d['total']) - 1:+.1%}）＝ EPS 成長 {np.exp(d['eps_g']) - 1:+.1%}（{eps0:,.2f} → {o0['eps_a']:,.2f}）"
              f"× 本益比重估 {np.exp(d['pe_ch']) - 1:+.1%}（{d['pe0']:.1f} → {o0['pe']:.1f} 倍）")
    ea0, eb0 = mine[0]
    alt, alt_txt = None, None                            # 對照：EPS_b 的另一種意思
    if o0.get("kind") == "market":
        alt, alt_txt = unified.predict(row, a.h, model=model, gm=gm, cq=cq, eps_a=ea0, eps_b=eb0, eb_kind="fund", cons_a=ca, cons_b=cb, fwd0=f0,
                                       rate=rate, band_mult=bm, erp=a.erp), "把 EPS_b 當我的基本面預估（軌道 β_sb）"
    elif o0.get("kind") == "fund" and eb0 is not None and gm is not None and str(a.h) in gm["h"]:
        alt = unified.predict(row, a.h, model=model, gm=gm, cq=cq, eps_a=ea0, eps_b=eb0, eb_kind="market", cons_a=ca, cons_b=cb, fwd0=f0,
                              rate=rate, band_mult=bm, erp=a.erp)
        alt_txt = "把 EPS_b 當「市場在目標日會預期的數字」（成長定價係數）" if alt.get("kind") == "market" else None
    if alt is not None and alt_txt:
        print(f"  對照（{alt_txt}）：本益比 {alt['pe']:.1f}（{L}% {alt[f'pe_lo{L}']:.1f}–{alt[f'pe_hi{L}']:.1f}）、股價 {alt['px']:,.0f}（{L}% {alt[f'px_lo{L}']:,.0f}–{alt[f'px_hi{L}']:,.0f}）"
              if alt.get("pe") else f"  對照（{alt_txt}）：股價 {alt['px']:,.0f}")
    rp = os.path.join(RES, "relative_dist.json")
    if os.path.exists(rp) and o0.get("pe") and eps0 > 0:    # 相對大盤（README §26.3）
        rd = json.load(open(rp))
        R = rd["h"].get(str(a.h))
        if R and R["n"]:
            v = float(np.log(o0["pe"] / (float(row["px"]) / eps0)))
            pc = float(np.searchsorted(np.array(R["v"]), v, side="right")) / R["n"]
            print(f"\n  相對大盤（README §26.3）：預測本益比 {float(row['px']) / eps0:.1f} → {o0['pe']:.1f} 倍（{np.exp(v) - 1:+.1%}）；"
                  f"S&P 500 {R['n']} 家只用共識的預測中位 {np.exp(R['med']) - 1:+.1%}（{rd['date']}；科技 {np.exp(R['med_tech']) - 1:+.1%}、非科技 {np.exp(R['med_other']) - 1:+.1%}）"
                  f"→ 相對大盤 {np.exp(v - R['med']) - 1:+.1%}，第 {pc:.0%} 百分位")
            lb = (rd.get("lab") or {}).get(str(a.h)) or {}
            if lb.get("rel") and lb.get("sp"):
                print(f"    大盤整體重新定價是最大的誤差來源、事前預測不了，相對的那一半比絕對水準可靠：回測（S&P 500，起點 2017–2024）{a.h} 個月相對誤差 "
                      f"{lb['rel'][0]:.3f} vs 絕對 {lb['rel'][1]:.3f}；每個起點月預測 vs 實際的 Spearman 中位 {lb['sp'][0]:.2f}（本益比不變 {lb['sp'][1]:.2f}）")
    if o0["widen"] > 1:
        print(f"  ⚠ EPS_a ≤ 0：本益比沒有定義（方案 A：只看股價），區間依回測放寬 ×{o0['widen']:.2f}；"
              "有給 EPS_b 時看最右欄的 forward 本益比（方案 B）")
    if o0["spec"] == "虧損：EPS 變化":
        print(f"  虧損版（README §20.5）：成長率算不出來，改用「EPS 變化 ÷ 今天股價」× β {o0['parts'][0]['β']:.2f}；"
              "S&P 500 回測 12 個月誤差 0.253 → 0.240（虧損→轉盈 0.240 → 0.218）"
              + (f"；今天虧損、EPS_a 轉正 → 區間放寬 ×{o0['widen']:.2f}" if o0["pe"] is not None and o0["widen"] > 1 else ""))
    if o0["spec"] == "軌道" and eps0 <= 0 and o0["pe"] is not None:
        print("  注意：今天虧損、又沒有共識 → 算不了 EPS 成長率，股價只用軌道（你的 EPS 只用在本益比的分母）；"
              "給共識（--cons）時可以用「你和共識的差距」")
    if ca is None and not use_auto:
        print("  提示：加 --cons auto 可以自動抓 Yahoo 共識，模型會分開算「市場已預期的成長」和「你和市場的差距」")
    if o0.get("group_key") == "cyclical" and o0["eps_b"] is None and o0["spec"] != "軌道":
        print("  提示：半導體／設備／記憶體的股價主要看「再下一年」的 EPS（回測 β_b ≈ 0.17、β_a ≈ 0）→ 建議加 --eps2")
    bt = model["backtest"].get(str(a.h), {})
    if bt:
        print(f"\n  回測（S&P 500，預測起點 2022 以後，EPS 完全正確時，中位 |ln 股價誤差|）：\n    "
              + "；".join(f"{k} {v:.3f}" for k, v in bt.items()))
    rc = (model.get("recent") or {}).get(str(a.h), {})
    if rc:
        print(f"  最近（起點 2024-10～2025-09，目標日到 2026-09）：" + "；".join(
            f"{g} 軌道 {v['軌道']:.3f}（市場偏離軌道 {v['市場偏離軌道中位']:+.2f}）" for g, v in rc.items()
            if g in ("全部", "科技", o0["group"])))
    print("\n  讀法：股價主要跟著軌道走；你的基本面 EPS 多 10% 通常只讓股價多 0.5–2%（半導體類較大、再下一年的 EPS 較重要），"
          "\n        所以本益比 ≈ 股價 ÷ 你的 EPS，主要由你的 EPS 決定。要讓本益比本身變高，得是「市場在目標日對下一年的預期」比共識高（--eb-kind market）。"
          "\n        誤差最大的來源是整個產業／大盤被重新定價，模型預測不了，區間已含這部分——看「相對大盤」那一行會比絕對水準可靠。不是投資建議。")


if __name__ == "__main__":
    main()

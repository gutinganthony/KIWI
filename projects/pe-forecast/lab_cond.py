#!/usr/bin/env python3
"""給定 EPS 的本益比模型：走動式樣本外回測（README §15）。

    python3 lab_cond.py --cache <暫存目錄>        # 單獨跑約 15 分鐘（不要和其他訓練樹模型的程式同時跑）

問題：你已經知道（或預估）h 個月後「那時已公布的最近四季 EPS」。那時的本益比會是多少？→ 股價 ＝ 本益比 × EPS。
回測做法：每年 1 月只用「答案在那時已揭曉」的配對訓練，預測當年每個月的 h 個月後本益比，
EPS 直接用事後實際公布的數字（＝「假設你的 EPS 完全正確」）。EPS 有誤差時的影響另外算。

比較的方法（全部在同一批樣本上）：
  unch     本益比不變：股價跟 EPS 一比一變動
  coe      資金成本：股價照 10 年期 + 5% 漲，完全不管 EPS
  coe_dy   同上，扣掉股利殖利率
  lin_abs  線性，直接學股價報酬（含利率等「整個市場」的線索）
  gbm_abs  梯度提升樹，直接學股價報酬（含利率、全市場本益比）
  gbm_xs   梯度提升樹，只學「相對大盤」的部分，大盤部分固定＝資金成本
  xs       正式模型：線性（Huber），只學相對大盤的部分，7 個現在也算得出來的線索
  xs2      正式模型的 12 個月版，另外知道再下一年（24 個月後）的 EPS
選模期 2015–2021 的預測起點；保留期 2022 以後。（注意：xs 的「只學相對大盤」這個設計，是看過保留期的年度結果之後
才定的——理由見 README §15.2；所以保留期對 xs 已經不是完全沒碰過的樣本，另存前瞻預測紀錄給之後驗收。）
另外（回應外部審查，README §15.7）：可評分的涵蓋率、倖存者偏誤（只看預測當時已是成分股的公司）、向基準收縮、本益比方向。
輸出：results/cond.txt、cond_scores.csv、cond_years.csv、cond_bands.csv、cond_band_alpha.csv、cond_noise.csv、cond_coverage.csv、cond_survivor.csv、
      cond_shrink.csv、cond_direction.csv、cond_predictions.csv.gz（逐筆預測，欄位說明見 README §15.8）
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef import cond, lab, universe                      # noqa: E402
from pef.load import panel_sp500                         # noqa: E402

RES = os.path.join(HERE, "results")
SEL = ("2015-01-01", "2021-12-31")
HOLD = ("2022-01-01", "2026-12-31")
ALL = ("2015-01-01", "2026-12-31")
PERIODS = {"選模期": SEL, "保留期": HOLD, "全期": ALL}
MAIN = ["unch", "coe", "coe_dy", "lin_abs", "gbm_abs", "gbm_xs", "xs"]
buf = io.StringIO()


def say(*a):
    print(*a)
    print(*a, file=buf)


def cached(cache, name, fn):
    path = os.path.join(cache, f"cond_{name}.pkl")
    if os.path.exists(path):
        return pd.read_pickle(path)
    x = fn()
    x.to_pickle(path)
    return x


def pm_band(med):
    """中位 |ln 誤差| → 一半的實際值落在「預測 × 這個範圍」裡（不對稱）。"""
    return f"{np.exp(-med) - 1:+.0%}～{np.exp(med) - 1:+.0%}"


BAND_LABEL = {"global": "全體同寬", "scale": "依波動縮放", "group": "依波動分三組", "group_c": "依波動分三組＋置中",
              "pow_c": "依波動^α縮放＋置中"}


def interval_eval(p, method, mode, period, cal_start="2012-01-01", alpha=cond.BAND_ALPHA):
    """80% 與 50% 區間：每個訓練年度只用「那時已揭曉」的樣本外誤差畫區間（走動式校準）。
    mode＝"global"：全體一樣寬；"scale"：誤差先除以（波動 × √(h/12)），區間再乘回來；
    "group"：依過去 36 個月股價波動分三組（門檻用校準樣本的三分位），每組各自的誤差分位數；
    "group_c"：同上，每組先減掉自己的中位數（置中）；
    "pow_c"：誤差先除以 波動^alpha、置中，區間再乘回來（正式版，cond.calib_table）。"""
    rows = []
    for h, g in p.groupby("h"):
        g = g[g[method].notna() & g["actual"].notna()].copy()
        g["e"] = g["actual"] - g[method]                         # ln(實際 ÷ 預測)
        out = []
        for Y, te in g[(g["origin"] >= period[0]) & (g["origin"] <= period[1])].groupby("training_cutoff"):
            cal = g[(g["target_available_at"] <= Y) & (g["origin"] >= cal_start)].copy()
            if len(cal) < 500:
                continue
            te = te.copy()
            vmed = cal["vol36"].median()                         # 沒有波動資料：用校準樣本（當時已揭曉）的中位數，和 calib_table 一樣
            for x in (cal, te):
                x["vol"] = x["vol36"].fillna(vmed)
                x["s"] = ((x["vol"] * np.sqrt(h / 12)).clip(0.08, 1.5) if mode == "scale" else
                          cond.band_scale(x["vol"], alpha) if mode == "pow_c" else 1.0)
                x["u"] = x["e"] / x["s"]
            if mode in ("group", "group_c"):
                cuts = cal["vol"].quantile([1 / 3, 2 / 3]).to_numpy()
                gc = np.searchsorted(cuts, cal["vol"].to_numpy())
                gt = np.searchsorted(cuts, te["vol"].to_numpy())
                qs = []
                for k in range(3):
                    uk = cal["u"][gc == k]
                    qs.append((uk - (uk.median() if mode == "group_c" else 0.0)).quantile([0.1, 0.25, 0.75, 0.9]).to_numpy())
                q = np.vstack(qs)[gt]
            else:
                u = cal["u"] - (cal["u"].median() if mode == "pow_c" else 0.0)
                q = np.tile(u.quantile([0.1, 0.25, 0.75, 0.9]).to_numpy(), (len(te), 1))
            te["lo80"], te["hi80"] = te["s"] * q[:, 0], te["s"] * q[:, 3]
            te["lo50"], te["hi50"] = te["s"] * q[:, 1], te["s"] * q[:, 2]
            out.append(te)
        if not out:
            continue
        t = pd.concat(out)
        in80 = (t["e"] >= t["lo80"]) & (t["e"] <= t["hi80"])
        in50 = (t["e"] >= t["lo50"]) & (t["e"] <= t["hi50"])
        w80 = t["hi80"] - t["lo80"]
        a = 0.2
        iscore = w80 + (2 / a) * (t["lo80"] - t["e"]).clip(lower=0) + (2 / a) * (t["e"] - t["hi80"]).clip(lower=0)
        vol_q = pd.qcut(t["vol"].rank(method="first"), 3, labels=["低波動", "中波動", "高波動"])
        by = {f"涵蓋80_{k}": float(in80[vol_q == k].mean()) for k in ["低波動", "中波動", "高波動"]}
        by["涵蓋80_波動45以上"] = float(in80[t["vol"] > 0.45].mean())
        rows.append(dict(h=h, 方法=method, 區間=BAND_LABEL[mode], alpha=alpha if mode == "pow_c" else np.nan,
                         n=len(t), 涵蓋80=float(in80.mean()), 涵蓋50=float(in50.mean()), 寬度80_ln=float(w80.median()),
                         區間分數=float(iscore.mean()), **by))
    return pd.DataFrame(rows)


def noise_runs(c, sigmas=(0.0, 0.1, 0.2, 0.3), seed=0):
    """EPS(t+h) 乘上 exp(N(0, σ)) 後重新預測（模型本身不變，訓練仍用實際 EPS）。正式模型 xs。"""
    rng = np.random.default_rng(seed)
    out = []
    for h in (12, 24):
        v = cond.view(c, h)
        elig = v["lfpe"].notna() & v["px"].gt(0)
        for Y in range(2015, 2026):
            cutoff = pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=1)
            tgt_end = v["month"] + pd.DateOffset(months=h) + pd.offsets.MonthEnd(0)
            tr = v[elig & (tgt_end <= cutoff) & v["target"].notna() & v["rp"].notna()]
            te = v[elig & (v["month_end"] > cutoff) & (v["month_end"] <= cutoff + pd.DateOffset(months=12)) & v["target"].notna()]
            if len(tr) < 1000 or te.empty:
                continue
            fm = cond.fit("xs", tr, h)
            for sig in sigmas:
                eps_err = rng.normal(0, sig, len(te)) if sig > 0 else np.zeros(len(te))
                t2 = te.copy()
                t2["lfpe"] = te["lfpe"] - eps_err                 # EPS 高估 → 今天股價下的前瞻本益比變低
                t2["geps"] = te["geps"] + eps_err
                lpe = t2["lfpe"].to_numpy(float) + cond.predict_rp(fm, t2)
                ln_eps_in = np.log(te[f"eps_f{h}"].to_numpy(float)) + eps_err
                out.append(pd.DataFrame({"h": h, "sigma": sig, "ticker": te["ticker"].to_numpy(), "origin": te["month"].to_numpy(),
                                         "lpe_pred": lpe, "px_pred": lpe + ln_eps_in, "actual": te["target"].to_numpy(),
                                         "px_target": te[f"px_f{h}"].to_numpy()}))
    return pd.concat(out, ignore_index=True)


def block_boot(g, a, b, n=400, seed=0, block=1):
    """自助法：a 相對 b 的中位 |誤差| 變化，90% 信賴區間。同一個月的所有公司一起抽（公司之間同月份的誤差相關）；
    block > 1 時一次抽「連續 block 個月」（移動區塊：h 個月的預測，相鄰起點的答案期間重疊，不是獨立事件）。"""
    rng = np.random.default_rng(seed)
    months = np.sort(g["origin"].unique())
    by = {m: g[g["origin"] == m] for m in months}
    M, L = len(months), max(1, min(block, len(months)))
    r = []
    for _ in range(n):
        starts = rng.integers(0, M - L + 1, int(np.ceil(M / L)))
        pick = np.concatenate([months[s:s + L] for s in starts])[:M]
        x = pd.concat([by[m] for m in pick])
        r.append(np.median(np.abs(x[a] - x["actual"])) / np.median(np.abs(x[b] - x["actual"])) - 1)
    return np.quantile(r, [0.05, 0.95]), M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    df, qf = panel_sp500()
    d = lab.build(df, qf)
    c = cond.build(d, df)
    say(f"面板：{c['ticker'].nunique()} 家 S&P 500 公司、{len(c):,} 個公司月（{c['month'].min():%Y-%m} ～ {c['month'].max():%Y-%m}）")
    for h in cond.HORIZONS:
        ok = c[f"lfpe_{h}"].notna() & c[f"lpe_f{h}"].notna()
        say(f"  h={h:2d}：有答案的配對 {ok.sum():,}（預測起點最晚 {c.loc[ok, 'month'].max():%Y-%m}，答案最晚 "
            f"{(c.loc[ok, 'month'] + pd.DateOffset(months=h)).max():%Y-%m}）")

    # 事實：股價對「已知 EPS 成長」的反應（全體，12 個月）
    v = c[c["lfpe_12"].notna() & c["lpe_f12"].notna() & (c["neg0"] == 0) & np.isfinite(c["geps_12"])]
    say("\n== 事實：12 個月後的 EPS 變化 vs 同期股價、本益比變化（全體 S&P 500，預測起點 2009–2024，中位數）")
    facts = []
    for lo, hi in [(-9, -0.3), (-0.3, -0.1), (-0.1, 0.05), (0.05, 0.15), (0.15, 0.3), (0.3, 0.6), (0.6, 9)]:
        m = (v["geps_12"] > lo) & (v["geps_12"] <= hi)
        lo_s = "−100%" if lo < -5 else f"{np.exp(lo) - 1:+.0%}"
        hi_s = "以上" if hi > 5 else f"{np.exp(hi) - 1:+.0%}"
        px_chg = np.exp(v.loc[m, "rp_12"].median()) - 1
        pe_chg = np.exp((v.loc[m, "lpe_f12"] - v.loc[m, "ln_pe"]).median()) - 1
        facts.append(dict(EPS變化下限=None if lo < -5 else np.exp(lo) - 1, EPS變化上限=None if hi > 5 else np.exp(hi) - 1,
                          n=int(m.sum()), 股價變化中位=px_chg, 本益比變化中位=pe_chg))
        say(f"  EPS 變化 {lo_s} ～ {hi_s}：n={m.sum():6,}  股價 {px_chg:+.0%}  本益比 {pe_chg:+.0%}")
    pd.DataFrame(facts).to_csv(os.path.join(RES, "cond_facts.csv"), index=False, float_format="%.6f")
    rs = v["rp_12"] - v.groupby("month")["rp_12"].transform("median")
    say(f"  12 個月股價報酬的變異裡，同月份所有公司的共同部分（大盤）占 {1 - rs.var() / v['rp_12'].var():.0%}")

    p = cached(a.cache, "walk", lambda: cond.walk(c, log=say))

    # 1) 點預測：今天有盈餘的共同樣本（「本益比不變」才有定義）
    rows = []
    for per, rng in PERIODS.items():
        s = cond.score(p, MAIN, base="coe", period=rng, sample=lambda g: g["ln_pe"].notna())
        rows.append(s.assign(期間=per, 樣本="今天有盈餘"))
        s2 = cond.score(p[p["h"] == 12], ["coe", "xs", "xs2"], base="coe", period=rng,
                        sample=lambda g: g["ln_pe"].notna())
        rows.append(s2.assign(期間=per, 樣本="也知道 24 個月後 EPS"))
    sc = pd.concat(rows, ignore_index=True)
    for per in PERIODS:
        x = sc[(sc["期間"] == per) & (sc["樣本"] == "今天有盈餘")]
        say(f"\n== {per}｜給定實際 EPS｜中位 |ln(預測 ÷ 實際)|（越小越好）")
        say(x.pivot(index="方法", columns="h", values="中位絕對誤差").loc[MAIN].round(4).to_string())
        say(f"== {per}｜相對「資金成本」的中位誤差變化（負＝比較準）")
        base = x[x["方法"] == "coe"].set_index("h")["中位絕對誤差"]
        rel = x.pivot(index="方法", columns="h", values="中位絕對誤差").loc[MAIN] / base - 1
        say(rel.round(3).to_string())
        say(f"== {per}｜技能（1 − Σe² ÷ Σe_資金成本²，不截尾）")
        say(x.pivot(index="方法", columns="h", values="技能").loc[MAIN].round(3).to_string())
        say(f"== {per}｜命中 ±20%（|預測 ÷ 實際 − 1| ≤ 20%）")
        say(x.pivot(index="方法", columns="h", values="命中20").loc[MAIN].round(3).to_string())
        y2 = sc[(sc["期間"] == per) & (sc["樣本"] == "也知道 24 個月後 EPS")]
        say(f"== {per}｜12 個月，也知道 24 個月後 EPS 的列：" + "、".join(
            f"{r.方法} {r.中位絕對誤差:.4f}" for r in y2.itertuples()) + f"（n={int(y2['n'].iloc[0]) if len(y2) else 0}）")
    s_neg = cond.score(p, ["coe", "gbm_xs", "xs"], base="coe", period=ALL, sample=lambda g: g["ln_pe"].isna())
    say("\n== 今天虧損、h 個月後有盈餘的公司（全期；xs 在這裡就是資金成本）：中位 |ln 誤差|")
    say(s_neg.pivot(index="方法", columns="h", values="中位絕對誤差").round(4).to_string())

    # 2) 逐年穩定性（12、24 個月，預測起點年度）
    yr = []
    for h in (12, 24):
        g = p[(p["h"] == h) & p["ln_pe"].notna() & p["actual"].notna()]
        g = g[g[MAIN].notna().all(axis=1)]
        for Y, x in g.groupby(g["origin"].dt.year):
            r = {"h": h, "預測起點年": Y, "n": len(x)}
            for m in ["unch", "coe", "gbm_abs", "xs"]:
                r[m] = float(np.median(np.abs(x[m] - x["actual"])))
            r["xs_vs_coe"] = r["xs"] / r["coe"] - 1
            r["gbm_abs_vs_coe"] = r["gbm_abs"] / r["coe"] - 1
            r["股價報酬中位"] = float(np.median(x["actual"] - x["lfpe"]))
            yr.append(r)
    yr = pd.DataFrame(yr)
    say("\n== 逐年（預測起點年度）：中位 |ln 誤差|；股價報酬中位＝那一年所有公司股價報酬（ln）的中位數")
    say(yr.round(3).to_string(index=False))

    # 3) 月份區塊自助法：xs 相對 coe 的改善有多穩（整個月一起抽，重疊的預測不當獨立樣本）
    for h in (12, 24):
        for per, rng in (("選模期", SEL), ("保留期", HOLD)):
            g = p[(p["h"] == h) & p["ln_pe"].notna() & p["actual"].notna() & p["xs"].notna()
                  & (p["origin"] >= rng[0]) & (p["origin"] <= rng[1])]
            (lo_, hi_), nm = block_boot(g, "xs", "coe")
            L = min(h, max(1, nm // 3))
            (lo2, hi2), _ = block_boot(g, "xs", "coe", block=L)
            pt = np.median(np.abs(g["xs"] - g["actual"])) / np.median(np.abs(g["coe"] - g["actual"])) - 1
            say(f"{h} 個月｜{per}：xs 相對資金成本 {pt:+.1%}（90% 信賴區間：單月區塊 {lo_:+.1%} ～ {hi_:+.1%}；"
                f"連續 {L} 個月區塊 {lo2:+.1%} ～ {hi2:+.1%}；{nm} 個預測月份）")

    # 4) 區間：全體同寬 vs 依波動縮放 vs 依波動分三組（走動式校準）
    # α（區間寬度 ∝ 波動^α）只在選模期挑：各預測距離區間分數的平均最低
    al = []
    for alpha in (0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
        x = interval_eval(p, "xs", "pow_c", SEL, alpha=alpha)
        al.append(dict(alpha=alpha, 區間分數平均=float(x["區間分數"].mean()), 涵蓋80平均=float(x["涵蓋80"].mean()),
                       涵蓋80_波動45以上平均=float(x["涵蓋80_波動45以上"].mean())))
    al = pd.DataFrame(al)
    say("\n== 區間寬度 ∝ 波動^α：α 在選模期挑（區間分數越低越好）")
    say(al.round(4).to_string(index=False))
    best = float(al.loc[al["區間分數平均"].idxmin(), "alpha"])
    say(f"  選到 α＝{best}；正式版用 cond.BAND_ALPHA＝{cond.BAND_ALPHA}" + ("" if best == cond.BAND_ALPHA else "（⚠️ 不一致，要改 cond.py）"))
    bands = []
    for per, rng in (("選模期", SEL), ("保留期", HOLD)):
        for mode in ("global", "scale", "group", "group_c", "pow_c"):
            bands.append(interval_eval(p, "xs", mode, rng).assign(期間=per))
    bands = pd.concat(bands, ignore_index=True)
    say("\n== 區間（xs；80% 與 50%；區間分數＝寬度 + 漏掉時的罰分，越低越好；「置中」＝誤差先減掉中位數，"
        "只留寬度、不留歷史平均偏差；正式版＝依波動^α縮放＋置中）")
    say(bands.round(3).to_string(index=False))

    # 5) EPS 有誤差時：股價與本益比的誤差
    noise = []
    fits = cached(a.cache, "noise", lambda: noise_runs(c))
    for (h, sig), g in fits.groupby(["h", "sigma"]):
        e_px = g["px_pred"] - np.log(g["px_target"])
        noise.append(dict(h=h, EPS誤差=sig, n=len(g), 股價中位絕對誤差=float(np.median(np.abs(e_px))),
                          股價命中20=float(np.mean(np.abs(np.exp(e_px) - 1) <= 0.2)),
                          本益比中位絕對誤差=float(np.median(np.abs(g["lpe_pred"] - g["actual"])))))
    noise = pd.DataFrame(noise)
    say("\n== EPS 有誤差時（xs，2015 以後全部預測起點）：EPS 乘上 exp(N(0, σ))")
    say(noise.round(4).to_string(index=False))

    # 6) 涵蓋率：哪些公司月能評分？本益比要有定義＝目標日那時已公布的最近四季 EPS > 0
    cov = []
    for h in cond.HORIZONS:
        v = cond.view(c, h)
        base = v[(v["month"] >= ALL[0]) & v["px"].gt(0) & v["rp"].notna()]
        ef = base[f"eps_f{h}"]
        ok_, loss_, na_ = ef.gt(0).to_numpy(), ef.le(0).to_numpy(), ef.isna().to_numpy()
        e_px = np.abs(cond.market_ret(base, h) - base["rp"].to_numpy(float))       # 只看股價：資金成本的誤差
        cov.append(dict(h=h, 兩端都有股價=len(base), 可評分=int(ok_.sum()), 目標日虧損=int(loss_.sum()), 目標日沒有財報=int(na_.sum()),
                        其中今天虧損=int((ok_ & (base["neg0"] == 1).to_numpy()).sum()),
                        股價誤差_可評分=float(np.median(e_px[ok_])), 股價誤差_目標日虧損=float(np.median(e_px[loss_]))))
    cov = pd.DataFrame(cov)
    say("\n== 涵蓋率（預測起點 2015 以後、兩端都有股價的公司月）：目標日虧損的列本益比沒有定義，不在上面的評分裡；"
        "它們的股價誤差（資金成本）另列")
    say(cov.round(4).to_string(index=False))

    # 7) 倖存者偏誤：面板是 2025 年的 S&P 500 名單（活下來、而且變大的公司）。只看「預測當時已經是成分股」的公司，結論一樣嗎？
    #    （之後被踢出指數的公司不在面板裡，這一塊查不到；能查的是「之後才加入」的那一半偏誤。）
    p["sp500_member_at_origin"] = universe.member_at(p["ticker"].to_numpy(), p["price_timestamp"].to_numpy()).to_numpy()
    sv = []
    for per, rng in (("選模期", SEL), ("保留期", HOLD)):
        for h in cond.HORIZONS:
            g = p[(p["h"] == h) & p["ln_pe"].notna() & (p["origin"] >= rng[0]) & (p["origin"] <= rng[1])]
            for nm, m in (("當時已是成分股", g["sp500_member_at_origin"]), ("當時還不是（之後才加入）", ~g["sp500_member_at_origin"])):
                x = g[m]
                if len(x) < 200:
                    continue
                e = {k: float(np.median(np.abs(x[k] - x["actual"]))) for k in ("unch", "coe", "xs")}
                sv.append(dict(期間=per, h=h, 樣本=nm, n=len(x), **e, xs_vs_coe=e["xs"] / e["coe"] - 1,
                               股價報酬中位=float(np.median(x["actual"] - x["lfpe"]))))
    sv = pd.DataFrame(sv)
    say("\n== 倖存者偏誤檢查：依「預測當時是不是 S&P 500 成分股」分開算（歷史成分股：github.com/fja05680/sp500）")
    say(sv.round(4).to_string(index=False))

    # 8) 向基準收縮：預測 ＝ 基準 ＋ λ ×（xs − 基準）；λ 只在選模期挑，保留期驗收（基準＝資金成本或本益比不變）
    grid = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
    shr = []
    for h in cond.HORIZONS:
        g = p[(p["h"] == h) & p["ln_pe"].notna()]
        sel = g[(g["origin"] >= SEL[0]) & (g["origin"] <= SEL[1])]
        hol = g[(g["origin"] >= HOLD[0]) & (g["origin"] <= HOLD[1])]
        for anc in ("coe", "unch"):
            err = lambda x, lam: float(np.median(np.abs(x[anc] + lam * (x["xs"] - x[anc]) - x["actual"])))
            es = [err(sel, lam) for lam in grid]
            best = grid[int(np.argmin(es))]
            shr.append(dict(h=h, 基準=anc, 選到的λ=best, **{f"選模期_λ={lam}": e_ for lam, e_ in zip(grid, es)},
                            保留期_選到的λ=err(hol, best), 保留期_λ1_xs=err(hol, 1.0), 保留期_λ0_基準=err(hol, 0.0)))
    shr = pd.DataFrame(shr)
    say("\n== 向基準收縮（中位 |ln 誤差|）：λ＝0 就是基準本身、λ＝1 就是 xs；λ 在選模期挑")
    say(shr.round(4).to_string(index=False))

    # 9) 本益比方向（h 個月後比今天高還是低）：預測和今天一樣算錯；對照「永遠猜跌」「永遠猜漲」
    dr = []
    for per, rng in (("選模期", SEL), ("保留期", HOLD)):
        for h in cond.HORIZONS:
            g = p[(p["h"] == h) & p["ln_pe"].notna() & (p["origin"] >= rng[0]) & (p["origin"] <= rng[1])]
            up = np.sign(g["actual"] - g["ln_pe"])
            r = dict(期間=per, h=h, n=len(g), 永遠猜跌=float((up < 0).mean()), 永遠猜漲=float((up > 0).mean()))
            for m in ("coe", "xs"):
                pr = np.sign(g[m] - g["ln_pe"])
                r[m] = float(((pr == up) & (pr != 0)).mean())
            dr.append(r)
    dr = pd.DataFrame(dr)
    say("\n== 本益比方向命中率（給定實際 EPS；平手算錯）")
    say(dr.round(3).to_string(index=False))

    cov.to_csv(os.path.join(RES, "cond_coverage.csv"), index=False, float_format="%.6f")
    sv.to_csv(os.path.join(RES, "cond_survivor.csv"), index=False, float_format="%.6f")
    shr.to_csv(os.path.join(RES, "cond_shrink.csv"), index=False, float_format="%.6f")
    dr.to_csv(os.path.join(RES, "cond_direction.csv"), index=False, float_format="%.6f")
    sc.to_csv(os.path.join(RES, "cond_scores.csv"), index=False, float_format="%.6f")
    yr.to_csv(os.path.join(RES, "cond_years.csv"), index=False, float_format="%.6f")
    bands.to_csv(os.path.join(RES, "cond_bands.csv"), index=False, float_format="%.6f")
    al.to_csv(os.path.join(RES, "cond_band_alpha.csv"), index=False, float_format="%.6f")
    noise.to_csv(os.path.join(RES, "cond_noise.csv"), index=False, float_format="%.6f")
    keep = ["ticker", "sector", "h", "origin", "price_timestamp", "training_cutoff", "feature_quarter_end", "feature_available_at",
            "target_month", "target_available_at", "target_quarter_end", "eps0", "eps_target", "px0", "px_target", "shares_basis",
            "ln_pe", "lfpe", "actual", "vol36", "y10", "dy", "sp500_member_at_origin", "xs_rule", "model_version"] + MAIN + ["xs2"]
    out = p[p["origin"] >= "2012-01-01"][keep]
    out.to_csv(os.path.join(RES, "cond_predictions.csv.gz"), index=False, float_format="%.6g", date_format="%Y-%m-%d",
               compression={"method": "gzip", "mtime": 0})      # mtime＝0：內容一樣時檔案位元組也一樣，重跑不會在 git 多存一份
    open(os.path.join(RES, "cond.txt"), "w").write(buf.getvalue())


if __name__ == "__main__":
    main()

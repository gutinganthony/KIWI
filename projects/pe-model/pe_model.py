#!/usr/bin/env python3
"""
pe_model.py — 模組化本益比模型（市場層）

  股價 = EPS × 本益比。EPS 看財報就知道；本益比是這個模型要算的東西。

  ln(P/E) = a + b₁·通膨 + b₂·實質利率 + b₃·通膨波動 + b₄·盈餘循環

  四個係數用 1950–2023 的席勒月資料估（n=882），不是判斷。
  為什麼是這四個、為什麼從 1950 起：--backtest 會把所有候選規格的樣本外表現印出來，
  通膨²、失業率、油價、配息率、10 年趨勢成長、3 年期波動都試過，樣本外沒有幫助或更差，剔除；
  戰前資料的通膨波動係數符號相反，所以估計樣本從 1950 起。
  用法：
    python3 pe_model.py                 # 規格比較 + 回測（決定要用哪一組因子）
    python3 pe_model.py --now --eps 295.36 --eps-date 2026-07
                                        # 用今天的總體數據算「合理本益比」
    python3 pe_model.py --grid          # 通膨 × 實質利率 的合理本益比表
    python3 pe_model.py --all

  只用 numpy。沒有 pandas／statsmodels。
"""
import argparse
import csv
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MACRO = os.path.join(HERE, "..", "macro-scenarios", "data", "monthly.csv")

# =============================================================================
# §0  資料
# =============================================================================


def _ym_range(start, end):
    y, m = map(int, start.split("-"))
    ye, me = map(int, end.split("-"))
    out = []
    while (y, m) <= (ye, me):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def load(eps_now=None, eps_date=None):
    """回傳 dict：每個序列都是對齊到 months 的 numpy 陣列，缺值為 NaN。"""
    sh = {r["Date"][:7]: r for r in csv.DictReader(open(os.path.join(DATA, "shiller_sp500.csv")))}
    cpi_m = {r["Date"][:7]: float(r["Index"]) for r in csv.DictReader(open(os.path.join(DATA, "cpi_us_monthly.csv")))}
    r10_m = {r["Date"][:7]: float(r["Rate"]) for r in csv.DictReader(open(os.path.join(DATA, "us10y_monthly.csv")))}
    macro = {}
    if os.path.exists(MACRO):
        macro = {r["date"]: r for r in csv.DictReader(open(MACRO))}

    months = _ym_range("1871-01", max(sh))
    n = len(months)
    price = np.full(n, np.nan)
    div = np.full(n, np.nan)
    eps = np.full(n, np.nan)
    cpi = np.full(n, np.nan)
    r10 = np.full(n, np.nan)
    unrate = np.full(n, np.nan)
    wti = np.full(n, np.nan)

    def f(x):
        try:
            v = float(x)
            return v if v != 0 else np.nan
        except (TypeError, ValueError):
            return np.nan

    for i, ym in enumerate(months):
        r = sh.get(ym)
        if r:
            price[i] = f(r["SP500"])
            div[i] = f(r["Dividend"])
            eps[i] = f(r["Earnings"])
            cpi[i] = f(r["Consumer Price Index"])
            r10[i] = f(r["Long Interest Rate"])
        # 席勒之後接鏡像（接縫已核對：2023-06 CPI 305.11 vs 305.109，10y 3.75 vs 3.75）
        if np.isnan(cpi[i]) and ym in cpi_m:
            cpi[i] = cpi_m[ym]
        if np.isnan(r10[i]) and ym in r10_m:
            r10[i] = r10_m[ym]
        mr = macro.get(ym)
        if mr:
            unrate[i] = f(mr.get("unrate"))
            wti[i] = f(mr.get("wti"))

    # 單一缺月（例：2025-10 政府關門，BLS 未發布 CPI）以前後兩月幾何內插補上，並記錄下來
    filled = []
    for name, arr in (("CPI", cpi), ("10y", r10)):
        for i in range(1, n - 1):
            if np.isnan(arr[i]) and not np.isnan(arr[i - 1]) and not np.isnan(arr[i + 1]):
                arr[i] = math.sqrt(arr[i - 1] * arr[i + 1])
                filled.append(f"{name} {months[i]}")

    eps_source = "席勒（as-reported，到 2023-06）"
    eps_last_real = months[max(i for i in range(n) if not np.isnan(eps[i]))]
    if eps_now is not None:
        # 席勒 EPS 停在 2023-06。之後到 eps_date 用「名目 EPS 線性內插」補到使用者給的值。
        # 這只影響盈餘循環那一項的 10 年平均，不影響任何係數。
        i0 = max(i for i in range(n) if not np.isnan(eps[i]))
        i1 = months.index(eps_date)
        if i1 <= i0:
            raise SystemExit(f"--eps-date 必須晚於席勒 EPS 的最後一月 {months[i0]}")
        for i in range(i0 + 1, i1 + 1):
            eps[i] = eps[i0] + (eps_now - eps[i0]) * (i - i0) / (i1 - i0)
        eps_source = f"席勒到 {months[i0]}，之後線性內插到 {eps_date} 的 {eps_now}（使用者輸入，來源層級見輸出）"

    return dict(months=months, price=price, div=div, eps=eps, cpi=cpi, r10=r10,
                unrate=unrate, wti=wti, eps_source=eps_source, filled=filled,
                eps_last_real=eps_last_real)


# =============================================================================
# §1  因子 —— 每一個都只用第 t 月以前的資料
# =============================================================================


def _roll_mean(x, w):
    out = np.full_like(x, np.nan)
    for i in range(w - 1, len(x)):
        seg = x[i - w + 1: i + 1]
        if not np.isnan(seg).any():
            out[i] = seg.mean()
    return out


def _roll_std(x, w):
    out = np.full_like(x, np.nan)
    for i in range(w - 1, len(x)):
        seg = x[i - w + 1: i + 1]
        if not np.isnan(seg).any():
            out[i] = seg.std(ddof=1)
    return out


def _lag_ratio_log(x, k):
    out = np.full_like(x, np.nan)
    out[k:] = np.log(x[k:] / x[:-k])
    return out


def features(d):
    cpi, eps, r10, price = d["cpi"], d["eps"], d["r10"], d["price"]
    dl_cpi = np.full_like(cpi, np.nan)
    dl_cpi[1:] = np.log(cpi[1:] / cpi[:-1])

    infl = _lag_ratio_log(cpi, 12)                       # 過去 12 個月通膨
    infl_tr = _roll_mean(dl_cpi, 60) * 12                # 過去 5 年平均通膨（預期通膨的代理）
    infl_vol = _roll_std(dl_cpi, 60) * math.sqrt(12)     # 通膨波動（5 年，年化）
    nom10 = r10 / 100.0
    real10 = nom10 - infl                                # 事後實質利率
    real10x = nom10 - infl_tr                            # 用 5 年平均通膨算的實質利率

    last_cpi = cpi[~np.isnan(cpi)][-1]
    real_eps = eps * last_cpi / cpi
    ecyc = np.log(real_eps / _roll_mean(real_eps, 120))  # 實質 EPS 相對 10 年平均（吸收分母效應）
    eg12 = _lag_ratio_log(real_eps, 12)                  # 實質 EPS 12 個月成長

    y = np.log(price / eps)                              # 目標：ln(P/E)，移動 12 個月 as-reported EPS

    infl_vol36 = _roll_std(dl_cpi, 36) * math.sqrt(12)   # 通膨波動（3 年）
    payout = d["div"] / eps                                # 配息率 D/E（Gordon：P/E ∝ payout/(r−g)）
    g10 = _lag_ratio_log(real_eps, 120) / 10.0            # 實質 EPS 10 年趨勢成長（g 的代理）

    F = {
        "infl_vol36": infl_vol36, "payout": payout, "g10": g10,
        "infl": infl, "infl2": infl ** 2, "infl_dev": np.abs(infl - 0.02),
        "nom10": nom10, "real10": real10, "real10x": real10x,
        "infl_vol": infl_vol, "ecyc": ecyc, "eg12": eg12,
        "unrate": d["unrate"] / 100.0,
    }
    # 油價：實質 WTI 的 12 個月變化（1946 起）
    real_wti = d["wti"] * last_cpi / cpi
    F["oil"] = _lag_ratio_log(real_wti, 12)
    return y, F


LABEL = {
    "infl": "通膨（12 個月）", "infl2": "通膨²", "infl_dev": "|通膨−2%|",
    "nom10": "名目 10 年期", "real10": "實質 10 年期（事後）", "real10x": "實質 10 年期（5 年均通膨）",
    "infl_vol": "通膨波動（5 年）", "ecyc": "盈餘循環（實質 EPS／10 年均）", "eg12": "實質 EPS 成長（12 個月）",
    "unrate": "失業率", "oil": "實質油價變化（12 個月）",
    "infl_vol36": "通膨波動（3 年）", "payout": "配息率 D/E", "g10": "實質 EPS 10 年趨勢成長",
}

SPECS = {
    "S0 常數（歷史平均）": [],
    "S1 Fed model：名目利率": ["nom10"],
    "S2 通膨": ["infl"],
    "S3 通膨＋通膨²": ["infl", "infl2"],
    "S4 S3＋實質利率": ["infl", "infl2", "real10"],
    "S4x S3＋實質利率(5年均)": ["infl", "infl2", "real10x"],
    "S5 S4＋通膨波動": ["infl", "infl2", "real10", "infl_vol"],
    "S6 S5＋盈餘循環": ["infl", "infl2", "real10", "infl_vol", "ecyc"],
    "S7 S6＋EPS 成長": ["infl", "infl2", "real10", "infl_vol", "ecyc", "eg12"],
}
SPECS_POSTWAR = {
    "P0 常數": [],
    "P1 Fed model：名目利率": ["nom10"],
    "P6 S6（含通膨²）": ["infl", "infl2", "real10", "infl_vol", "ecyc"],
    "P5L 線性通膨（無通膨²）": ["infl", "real10", "infl_vol", "ecyc"],
    "P5N 名目利率＋通膨（重參數化）": ["nom10", "infl", "infl_vol", "ecyc"],
    "P4 名目利率＋波動＋循環": ["nom10", "infl_vol", "ecyc"],
    "P5V 同 P5L，波動改 3 年": ["infl", "real10", "infl_vol36", "ecyc"],
    "P5P P5L＋配息率": ["infl", "real10", "infl_vol", "ecyc", "payout"],
    "P5G P5L＋10 年趨勢成長": ["infl", "real10", "infl_vol", "ecyc", "g10"],
    "P5PG P5L＋配息率＋趨勢成長": ["infl", "real10", "infl_vol", "ecyc", "payout", "g10"],
    "P8 P5L＋失業率": ["infl", "real10", "infl_vol", "ecyc", "unrate"],
    "P9 P5L＋油價（1987 起）": ["infl", "real10", "infl_vol", "ecyc", "oil"],
}

# 選定規格與估計樣本（由 --backtest 的樣本外結果決定，理由見 README）
CHOSEN = ["infl", "real10", "infl_vol", "ecyc"]
SAMPLE_START = "1950-01"

# =============================================================================
# §2  估計：OLS ＋ Newey-West HAC 標準誤（重疊觀測）
# =============================================================================


def design(F, cols, idx):
    X = np.column_stack([np.ones(len(idx))] + [F[c][idx] for c in cols])
    return X


def ols_hac(y, X, L=12):
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    XtX_inv = np.linalg.inv(X.T @ X)
    Xe = X * e[:, None]
    S = Xe.T @ Xe
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0)
        G = Xe[l:].T @ Xe[:-l]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.diag(V))
    sst = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - (e @ e) / sst
    adj = 1.0 - (1.0 - r2) * (n - 1) / (n - k)
    return beta, se, r2, adj, e


def valid_idx(y, F, cols, months, start=None, end=None):
    m = ~np.isnan(y)
    for c in cols:
        m &= ~np.isnan(F[c])
    if start:
        m &= np.array([ym >= start for ym in months])
    if end:
        m &= np.array([ym <= end for ym in months])
    return np.where(m)[0]


# =============================================================================
# §3  回測
# =============================================================================


def oos_expanding(y, F, cols, months, idx, first_pred="1921-01", refit=12):
    """擴張視窗：每 12 個月用『之前』的資料重估一次係數，預測接下來 12 個月。"""
    ym = [months[i] for i in idx]
    yy = y[idx]
    X = design(F, cols, idx)
    n = len(idx)
    t_start = max(next(i for i, m in enumerate(ym) if m >= first_pred), 120)
    pred = np.full(n, np.nan)
    b_mean = np.full(n, np.nan)
    b_20y = np.full(n, np.nan)
    for t0 in range(t_start, n, refit):
        beta, *_ = np.linalg.lstsq(X[:t0], yy[:t0], rcond=None)
        for t in range(t0, min(t0 + refit, n)):
            pred[t] = X[t] @ beta
            b_mean[t] = yy[:t0].mean()
            b_20y[t] = yy[max(0, t0 - 240):t0].mean()
    m = ~np.isnan(pred)
    sse = ((yy[m] - pred[m]) ** 2).sum()
    r2_vs_mean = 1 - sse / ((yy[m] - b_mean[m]) ** 2).sum()
    r2_vs_20y = 1 - sse / ((yy[m] - b_20y[m]) ** 2).sum()
    rmse = math.sqrt(sse / m.sum())
    mae_pe = np.median(np.abs(np.exp(yy[m]) - np.exp(pred[m])))
    mae_pe_b = np.median(np.abs(np.exp(yy[m]) - np.exp(b_mean[m])))
    return dict(r2_vs_mean=r2_vs_mean, r2_vs_20y=r2_vs_20y, rmse=rmse,
                mae_pe=mae_pe, mae_pe_bench=mae_pe_b, n=int(m.sum()),
                pred=pred, bench=b_mean, y=yy, ym=ym, mask=m)


def mean_reversion(res, h, lag=0):
    """gap_t = 實際 − 模型；回歸 (y_{t+h} − y_t) 對 gap_{t−lag}。係數趨近 −1 ＝ 完全回歸。"""
    yy, pred, bench, m = res["y"], res["pred"], res["bench"], res["mask"]
    n = len(yy)
    rows = []
    for t in range(lag, n - h):
        if m[t - lag] and m[t]:
            rows.append((yy[t + h] - yy[t], yy[t - lag] - pred[t - lag], yy[t - lag] - bench[t - lag]))
    A = np.array(rows)
    out = {}
    for name, col in (("model", 1), ("mean", 2)):
        X = np.column_stack([np.ones(len(A)), A[:, col]])
        beta, se, r2, _, _ = ols_hac(A[:, 0], X, L=h)
        out[name] = (beta[1], beta[1] / se[1], r2)
    return out, len(A)


# =============================================================================
# §4  輸出
# =============================================================================


def print_spec_table(y, F, months, specs, start=None, first_pred="1921-01", title=""):
    print(f"\n{title}")
    print(f"  {'規格':30s} {'k':>2s} {'n':>5s} {'樣本內R²':>8s} {'樣本外R²':>8s} {'vs20年均':>8s} {'中位誤差(倍)':>12s} {'基準誤差':>8s}")
    rows = {}
    for name, cols in specs.items():
        idx = valid_idx(y, F, cols, months, start=start)
        X = design(F, cols, idx)
        _, _, r2, adj, _ = ols_hac(y[idx], X)
        res = oos_expanding(y, F, cols, months, idx, first_pred=first_pred)
        rows[name] = (cols, res)
        print(f"  {name:30s} {len(cols):>2d} {len(idx):>5d} {r2:>8.3f} {res['r2_vs_mean']:>8.3f} {res['r2_vs_20y']:>8.3f} "
              f"{res['mae_pe']:>12.2f} {res['mae_pe_bench']:>8.2f}")
    return rows


def print_coef(y, F, months, cols, start=None, end=None, title=""):
    idx = valid_idx(y, F, cols, months, start=start, end=end)
    X = design(F, cols, idx)
    beta, se, r2, adj, e = ols_hac(y[idx], X)
    print(f"\n{title}  樣本 {months[idx[0]]}～{months[idx[-1]]}  n={len(idx)}  R²={r2:.3f}")
    print(f"  {'因子':28s} {'係數':>9s} {'HAC t':>7s}   意義")
    names = ["常數"] + cols
    for j, nm in enumerate(names):
        lab = LABEL.get(nm, nm)
        meaning = ""
        if nm == "infl":
            meaning = f"通膨 +1pp ⇒ P/E {100*(math.exp(beta[j]*0.01)-1):+.1f}%（線性項）"
        elif nm == "real10":
            meaning = f"實質利率 +1pp ⇒ P/E {100*(math.exp(beta[j]*0.01)-1):+.1f}%"
        elif nm == "infl_vol":
            meaning = f"通膨波動 +1pp ⇒ P/E {100*(math.exp(beta[j]*0.01)-1):+.1f}%"
        elif nm == "ecyc":
            meaning = f"實質 EPS 高於 10 年均 10% ⇒ P/E {100*(math.exp(beta[j]*math.log(1.1))-1):+.1f}%"
        elif nm == "常數":
            meaning = f"其他因子＝0 時 P/E = {math.exp(beta[j]):.1f}"
        print(f"  {lab:28s} {beta[j]:>9.3f} {beta[j]/se[j]:>7.1f}   {meaning}")
    return beta, idx


def run_backtest(d):
    y, F = features(d)
    months = d["months"]
    print("=" * 96)
    print("【規格比較】目標 ln(P/E)。樣本外＝擴張視窗、每 12 個月重估、只用之前的資料。")
    print("  「樣本外 R²」以『當時為止的歷史平均本益比』為基準：>0 才代表比『P/E 會回到長期平均』這句話有用。")
    print("  「中位誤差(倍)」＝樣本外 |實際 P/E − 模型 P/E| 的中位數；「基準誤差」＝同一指標但用歷史平均。")
    rows = print_spec_table(y, F, months, SPECS, title="【全樣本 1881–2023，樣本外從 1921 起】")
    print_spec_table(y, F, months, SPECS, first_pred="1950-01", title="【同上，但只看 1950 以後的樣本外表現】")
    print_spec_table(y, F, months, SPECS_POSTWAR, start="1950-01", first_pred="1975-01",
                     title="【戰後樣本 1950–2023（失業率／油價只有這段有資料），樣本外從 1975 起】")

    print("\n" + "=" * 96)
    print("【選定規格的係數】（Newey-West HAC，lag 12）")
    print_coef(y, F, months, CHOSEN, start=SAMPLE_START, title=f"估計樣本 {SAMPLE_START[:4]} 起")
    print("\n【子樣本穩定性】同一組因子，分段估：")
    for s, e in (("1950-01", "1985-12"), ("1986-01", "2023-06"), ("1881-01", "1949-12")):
        print_coef(y, F, months, CHOSEN, start=s, end=e, title=f"  {s[:4]}–{e[:4]}")
    print("\n【對照：含通膨² 的 S6 在同樣三段】只看通膨² 那一列：")
    for s, e in (("1950-01", "1985-12"), ("1986-01", "2023-06"), ("1881-01", "1949-12")):
        idx = valid_idx(y, F, ["infl", "infl2", "real10", "infl_vol", "ecyc"], months, start=s, end=e)
        X = design(F, ["infl", "infl2", "real10", "infl_vol", "ecyc"], idx)
        beta, se, r2, *_ = ols_hac(y[idx], X)
        print(f"  {s[:4]}–{e[:4]}  通膨² 係數 {beta[2]:>8.1f}  HAC t {beta[2]/se[2]:>5.1f}   R²={r2:.3f}")

    print("\n" + "=" * 96)
    print("【均值回歸檢定】模型有沒有找到「合理值」？")
    print("  gap = 實際 ln(P/E) − 模型 ln(P/E)（樣本外預測）。回歸「未來 h 個月 ln(P/E) 的變化」對 gap。")
    print("  係數應為負（高於合理值 ⇒ 之後往下）；−1 ＝ h 個月內完全回歸。對照組：gap 改用「歷史平均」算。")
    for label, cols, start, fp in (("全樣本 S6（含通膨²），樣本外 1921 起", ["infl", "infl2", "real10", "infl_vol", "ecyc"], None, "1921-01"),
                                   (f"戰後 選定規格，樣本外 1975 起", CHOSEN, SAMPLE_START, "1975-01")):
        idx = valid_idx(y, F, cols, months, start=start)
        res = oos_expanding(y, F, cols, months, idx, first_pred=fp)
        print(f"\n  ── {label} ──")
        print(f"  {'視窗':>8s} {'落後':>4s} │ {'模型 gap 係數':>12s} {'t':>6s} {'R²':>6s} │ {'歷史均 gap 係數':>14s} {'t':>6s} {'R²':>6s}")
        for h in (12, 36, 60):
            for lag in (0, 3):
                out, nobs = mean_reversion(res, h, lag=lag)
                mb, mt, mr2 = out["model"]
                bb, bt, br2 = out["mean"]
                print(f"  {h:>6d}月 {lag:>4d} │ {mb:>12.3f} {mt:>6.1f} {mr2:>6.3f} │ {bb:>14.3f} {bt:>6.1f} {br2:>6.3f}")
    print("  ⚠️ 重疊視窗 ⇒ t 值用 HAC(lag=h)。這裡看的是相對強弱，不是精確 p 值。")
    return y, F


def run_now(d, args):
    y, F = features(d)
    months = d["months"]
    idx = valid_idx(y, F, CHOSEN, months, start=SAMPLE_START, end=d["eps_last_real"])
    X = design(F, CHOSEN, idx)
    beta, se, r2, _, e = ols_hac(y[idx], X)
    resid_sd = e.std(ddof=len(CHOSEN) + 1)

    # 最新一個月：所有因子都有值的月份
    all_ok = [i for i in range(len(months)) if not any(np.isnan(F[c][i]) for c in CHOSEN)]
    t = all_ok[-1]
    x = np.array([1.0] + [F[c][t] for c in CHOSEN])
    yhat = x @ beta
    fair = math.exp(yhat)
    print("=" * 96)
    print(f"【現在的合理本益比】  資料月份：{months[t]}")
    print(f"  係數估計樣本：{months[idx[0]]}～{months[idx[-1]]}（n={len(idx)}，只用席勒真實 EPS；--eps 的內插不進估計）")
    print(f"  EPS 來源：{d['eps_source']}")
    if d["filled"]:
        print(f"  ⚠️ 缺月以幾何內插補上：{', '.join(d['filled'])}")
    print(f"  {'因子':28s} {'今天的值':>9s} {'係數':>8s} {'對 ln(P/E) 的貢獻':>16s}")
    print(f"  {'常數':28s} {'':>9s} {beta[0]:>8.3f} {beta[0]:>16.3f}")
    for j, c in enumerate(CHOSEN, start=1):
        v = F[c][t]
        disp = f"{v*100:.2f}%" if c in ("infl", "real10", "infl_vol", "nom10", "real10x", "unrate") else (f"{(v*100):+.1f}%" if c == "ecyc" else f"{v:.4f}")
        print(f"  {LABEL[c]:28s} {disp:>9s} {beta[j]:>8.3f} {beta[j]*v:>16.3f}")
    print(f"  {'合計 ln(P/E)':28s} {'':>9s} {'':>8s} {yhat:>16.3f}")
    print(f"\n  ⇒ 合理本益比 = {fair:.1f} 倍   （模型殘差 1σ ＝ ×/÷ {math.exp(resid_sd):.2f} ⇒ 區間 {fair/math.exp(resid_sd):.1f}–{fair*math.exp(resid_sd):.1f}）")
    if not np.isnan(y[t]):
        print(f"  實際本益比（{months[t]}，月均價 {d['price'][t]:.0f} ÷ EPS {d['eps'][t]:.2f}）= {math.exp(y[t]):.1f} 倍  ⇒ gap = {100*(math.exp(y[t]-yhat)-1):+.0f}%")
    if args.eps:
        print(f"  以 EPS {args.eps} 換算：合理價 = {fair*args.eps:.0f}（1σ 區間 {fair/math.exp(resid_sd)*args.eps:.0f}–{fair*math.exp(resid_sd)*args.eps:.0f}）")
    # 最新價格（可能比因子月份晚一個月）
    last_p = max(i for i in range(len(months)) if not np.isnan(d["price"][i]))
    if last_p > t and args.eps:
        print(f"  最新月均價 {months[last_p]}：{d['price'][last_p]:.0f} ⇒ 以 EPS {args.eps} 算實際本益比 {d['price'][last_p]/args.eps:.1f} 倍，gap {100*(d['price'][last_p]/args.eps/fair-1):+.0f}%")

    print("\n【敏感度】其他因子不動，只動一個：")
    shocks = [("infl", 0.01, "通膨 +1pp"), ("infl", -0.01, "通膨 −1pp"), ("real10", 0.01, "實質利率 +1pp"),
              ("real10", -0.01, "實質利率 −1pp"), ("infl_vol", 0.01, "通膨波動 +1pp"), ("ecyc", math.log(1.1), "實質 EPS 相對 10 年均 +10%"),
              ("ecyc", math.log(0.9), "實質 EPS 相對 10 年均 −10%")]
    for c, dv, lab in shocks:
        x2 = x.copy()
        j = CHOSEN.index(c) + 1
        x2[j] += dv
        if c == "infl" and "infl2" in CHOSEN:
            x2[CHOSEN.index("infl2") + 1] = x2[j] ** 2
        f2 = math.exp(x2 @ beta)
        print(f"  {lab:28s} ⇒ 合理本益比 {f2:.1f}（{100*(f2/fair-1):+.1f}%）")
    # 通膨波動是回頭看 5 年的量，現在的視窗（2021-08～2026-07）還含 2021–22 那段。
    # 給一個由資料算出的對照：若波動回到 1995–2019 的中位數，其他不動，合理本益比是多少。
    ref_idx = [i for i in range(len(months)) if "1995-01" <= months[i] <= "2019-12" and not np.isnan(F["infl_vol"][i])]
    vol_ref = float(np.median(F["infl_vol"][ref_idx]))
    x3 = x.copy(); x3[CHOSEN.index("infl_vol") + 1] = vol_ref
    f3 = math.exp(x3 @ beta)
    print(f"  {'通膨波動回到 1995–2019 中位數':28s} ⇒ 合理本益比 {f3:.1f}（{100*(f3/fair-1):+.1f}%）  [中位數 {vol_ref*100:.2f}%，今天 {F['infl_vol'][t]*100:.2f}%]")
    print("\n  （模型是 ln(P/E) 線性，換回倍數後 +1pp 與 −1pp 的百分比自然不對稱。）")
    print("  ⚠️ 通膨波動是回頭看的：2021–22 那段要到 2027 年中才會滾出 5 年視窗。市場可能已經先看過去了，模型不會。")


def run_grid(d):
    y, F = features(d)
    months = d["months"]
    idx = valid_idx(y, F, CHOSEN, months, start=SAMPLE_START, end=d["eps_last_real"])
    X = design(F, CHOSEN, idx)
    beta, *_ = ols_hac(y[idx], X)
    all_ok = [i for i in range(len(months)) if not any(np.isnan(F[c][i]) for c in CHOSEN)]
    t = all_ok[-1]
    vol, ecyc = F["infl_vol"][t], F["ecyc"][t]
    print("=" * 96)
    print(f"【合理本益比表】通膨波動與盈餘循環固定在 {months[t]} 的值（{vol*100:.2f}%、{ecyc*100:+.1f}%）")
    infls = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08]
    reals = [-0.01, 0.00, 0.01, 0.02, 0.03, 0.04]
    hdr = "通膨 ╲ 實質利率"
    print(f"  {hdr:>16s}" + "".join(f"{r*100:>8.0f}%" for r in reals))
    for inf in infls:
        row = []
        for r in reals:
            x = np.array([1.0, inf, r, vol, ecyc])
            row.append(math.exp(x @ beta))
        print(f"  {inf*100:>15.0f}%" + "".join(f"{v:>9.1f}" for v in row))
    print("  讀法：新的 CPI 或利率出來，橫列找通膨、直行找實質利率，交叉就是新的合理本益比。")


def run_history(d):
    y, F = features(d)
    months = d["months"]
    idx = valid_idx(y, F, CHOSEN, months, start=SAMPLE_START, end=d["eps_last_real"])
    X = design(F, CHOSEN, idx)
    beta, *_ = ols_hac(y[idx], X)
    fit = X @ beta
    mi = {months[i]: k for k, i in enumerate(idx)}
    print("=" * 96)
    print("【歷史對照】模型（樣本內配適）vs 實際，幾個大家知道發生了什麼的月份：")
    print(f"  {'月份':8s} {'實際P/E':>7s} {'模型P/E':>7s} {'gap':>6s}   通膨   實質利率  通膨波動  盈餘循環")
    for ym in ("1966-01", "1974-09", "1982-07", "1987-08", "1994-11", "2000-03", "2002-09", "2007-10",
               "2009-03", "2011-09", "2018-01", "2020-03", "2021-12", "2022-10", "2023-06"):
        if ym in mi:
            k = mi[ym]; i = idx[k]
            print(f"  {ym:8s} {math.exp(y[i]):>7.1f} {math.exp(fit[k]):>7.1f} {100*(math.exp(y[i]-fit[k])-1):>+5.0f}%  "
                  f"{F['infl'][i]*100:>5.1f}%  {F['real10'][i]*100:>6.1f}%  {F['infl_vol'][i]*100:>6.2f}%  {F['ecyc'][i]*100:>+6.0f}%")
    gap = y[idx] - fit
    order = np.argsort(gap)
    print("\n  樣本內 gap 最大的月份（實際遠高於模型）：" + ", ".join(f"{months[idx[k]]} {100*(math.exp(gap[k])-1):+.0f}%" for k in order[-5:][::-1]))
    print("  樣本內 gap 最小的月份（實際遠低於模型）：" + ", ".join(f"{months[idx[k]]} {100*(math.exp(gap[k])-1):+.0f}%" for k in order[:5]))
    print(f"  殘差 1σ ＝ ×/÷ {math.exp(gap.std(ddof=len(CHOSEN)+1)):.2f}；2009-03 那種 P/E 破百的月份，看盈餘循環那一欄就知道模型怎麼處理分母崩掉。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--eps", type=float, help="最新 12 個月移動 as-reported EPS")
    ap.add_argument("--eps-date", default="2026-07", help="該 EPS 對應的月份 YYYY-MM")
    a = ap.parse_args()
    if not (a.backtest or a.now or a.grid or a.history or a.all):
        a.backtest = True
    d = load(eps_now=a.eps, eps_date=a.eps_date) if a.eps else load()
    if a.backtest or a.all:
        run_backtest(d)
    if a.now or a.all:
        run_now(d, a)
    if a.grid or a.all:
        run_grid(d)
    if a.history or a.all:
        run_history(d)


if __name__ == "__main__":
    main()

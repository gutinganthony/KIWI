#!/usr/bin/env python3
"""EMA20/EMA50 黃金交叉趨勢跟隨策略 — 回測引擎（純運算，不碰網路）。

策略定義（使用者指定，不加任何額外過濾）:
  - 計算 EMA20 與 EMA50（Wilder 式遞迴 EMA，adjust=False）
  - EMA20 由下往上穿越 EMA50（黃金交叉）→ 全額做多，weight = 1
  - EMA20 由上往下穿越 EMA50（死亡交叉）→ 出場，weight = 0
  - 只做多，不放空，不加濾網

成交假設（本引擎的唯一自由度，策略本身未指定）:
  訊號在第 t 根 K 棒「收盤後」確認 → 第 t+1 根 K 棒「開盤價」成交。
  這是避免 look-ahead bias 的最保守設定；設 fill="close" 可切換成
  「收盤價當根成交」的樂觀版本，用來量化執行滑價的影響。

所有函式為純函式，可離線測試。
"""

from __future__ import annotations

import numpy as np

TRADING_DAYS_PER_YEAR = 252


# --------------------------------------------------------------------------
# 指標
# --------------------------------------------------------------------------
def ema(values: np.ndarray, span: int) -> np.ndarray:
    """遞迴 EMA（等同 pandas ewm(span=span, adjust=False)）。

    種子值用第一個有效值本身，因此前 `span` 根尚未收斂——呼叫端必須用
    `warmup_mask()` 把未收斂區間排除在訊號之外。
    """
    values = np.asarray(values, dtype=float)
    out = np.full(values.shape, np.nan)
    alpha = 2.0 / (span + 1.0)
    prev = np.nan
    for i, v in enumerate(values):
        if np.isnan(v):
            out[i] = prev
            continue
        prev = v if np.isnan(prev) else alpha * v + (1 - alpha) * prev
        out[i] = prev
    return out


def crossover_signals(
    close: np.ndarray,
    fast: int = 20,
    slow: int = 50,
    enter_on_warmup: bool = True,
):
    """回傳 (ema_fast, ema_slow, cross_up, cross_down)。

    cross_up[t]  = True 表示第 t 根收盤時 EMA_fast 由下往上穿越 EMA_slow
    cross_down[t] = 反之
    前 `slow` 根（EMA 尚未收斂）一律不產生訊號。

    `enter_on_warmup`（預設 True）處理「資料起點」邊界：若 warm-up 結束的那根
    EMA20 已經在 EMA50 上方，嚴格定義下「從未發生穿越」→ 整段樣本永不進場，
    結果會荒謬地取決於資料從哪一天開始。預設把該根視為一次進場訊號，
    等同「接手一個已經在多頭排列的市場」。設 False 可還原嚴格定義。
    本專案回測窗（近 24 個月）距樣本起點 5 年以上，兩種設定對回報數字無影響
    ——差異已由 scripts/sensitivity.py 實測確認。
    """
    close = np.asarray(close, dtype=float)
    n = len(close)
    ef = ema(close, fast)
    es = ema(close, slow)

    above = ef > es
    prev_above = np.roll(above, 1)
    prev_above[0] = above[0]

    cross_up = above & ~prev_above
    cross_down = ~above & prev_above

    # warm-up：EMA_slow 收斂前的穿越是雜訊，一律丟棄
    warm = np.arange(n) < slow
    cross_up[warm] = False
    cross_down[warm] = False

    if enter_on_warmup and n > slow and above[slow]:
        cross_up[slow] = True

    return ef, es, cross_up, cross_down


# --------------------------------------------------------------------------
# 逐棒模擬
# --------------------------------------------------------------------------
def simulate(
    open_: np.ndarray,
    close: np.ndarray,
    cross_up: np.ndarray,
    cross_down: np.ndarray,
    fill: str = "next_open",
    cost_bps: float = 0.0,
):
    """全額做多 / 全額空手的逐棒模擬。

    回傳 dict:
      equity    – 每根收盤的權益曲線（起始 1.0）
      in_market – 每根收盤是否持倉（bool）
      trades    – list of dict(entry_i, entry_px, exit_i, exit_px, ret)
                  未平倉的最後一筆 exit_i 為 None

    cost_bps 為「單邊」成本（含手續費＋滑價），進出各扣一次。
    """
    open_ = np.asarray(open_, dtype=float)
    close = np.asarray(close, dtype=float)
    n = len(close)
    cost = cost_bps / 10_000.0

    cash, shares = 1.0, 0.0
    equity = np.full(n, np.nan)
    in_market = np.zeros(n, dtype=bool)
    trades: list[dict] = []
    pending = None  # "buy" / "sell" / None
    open_trade = None

    for t in range(n):
        # 1) 先執行上一根收盤掛出的委託（next_open 模式）
        if pending == "buy" and shares == 0.0:
            px = open_[t]
            if np.isfinite(px) and px > 0:
                shares = (cash * (1 - cost)) / px
                cash = 0.0
                open_trade = {"entry_i": t, "entry_px": px}
                pending = None
        elif pending == "sell" and shares > 0.0:
            px = open_[t]
            if np.isfinite(px) and px > 0:
                cash = shares * px * (1 - cost)
                shares = 0.0
                open_trade.update(exit_i=t, exit_px=px)
                open_trade["ret"] = (
                    open_trade["exit_px"] / open_trade["entry_px"] * (1 - cost) ** 2 - 1
                )
                trades.append(open_trade)
                open_trade = None
                pending = None

        px_c = close[t]
        # 2) 收盤評估訊號
        if fill == "close":
            if cross_up[t] and shares == 0.0 and np.isfinite(px_c) and px_c > 0:
                shares = (cash * (1 - cost)) / px_c
                cash = 0.0
                open_trade = {"entry_i": t, "entry_px": px_c}
            elif cross_down[t] and shares > 0.0 and np.isfinite(px_c) and px_c > 0:
                cash = shares * px_c * (1 - cost)
                shares = 0.0
                open_trade.update(exit_i=t, exit_px=px_c)
                open_trade["ret"] = (
                    open_trade["exit_px"] / open_trade["entry_px"] * (1 - cost) ** 2 - 1
                )
                trades.append(open_trade)
                open_trade = None
        else:
            if cross_up[t] and shares == 0.0:
                pending = "buy"
            elif cross_down[t] and shares > 0.0:
                pending = "sell"

        # 3) 收盤市值
        equity[t] = cash + shares * (px_c if np.isfinite(px_c) else 0.0)
        in_market[t] = shares > 0.0

    if open_trade is not None:
        open_trade.update(exit_i=None, exit_px=None)
        open_trade["ret"] = close[-1] / open_trade["entry_px"] * (1 - cost) - 1
        trades.append(open_trade)

    return {"equity": equity, "in_market": in_market, "trades": trades}


# --------------------------------------------------------------------------
# 績效指標
# --------------------------------------------------------------------------
def max_drawdown(equity: np.ndarray) -> float:
    """最大回撤（負值，例如 -0.32 代表 -32%）。"""
    eq = np.asarray(equity, dtype=float)
    eq = eq[np.isfinite(eq)]
    if len(eq) < 2:
        return 0.0
    peak = np.maximum.accumulate(eq)
    return float(np.min(eq / peak - 1.0))


def annualised_sharpe(equity: np.ndarray) -> float:
    """年化 Sharpe（rf = 0，日報酬）。"""
    eq = np.asarray(equity, dtype=float)
    eq = eq[np.isfinite(eq)]
    if len(eq) < 3:
        return 0.0
    r = np.diff(eq) / eq[:-1]
    sd = np.std(r, ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return 0.0
    return float(np.mean(r) / sd * np.sqrt(TRADING_DAYS_PER_YEAR))


def window_metrics(
    equity: np.ndarray,
    bh_close: np.ndarray,
    in_market: np.ndarray,
    trades: list[dict],
    i0: int,
    i1: int,
) -> dict:
    """把 [i0, i1] 這段切出來、重新基準化成 1.0 後計算績效。

    i0/i1 皆為 inclusive 索引。策略與買入持有都以 i0 的收盤為基準點，
    因此兩者可直接比較。
    """
    eq = np.asarray(equity[i0 : i1 + 1], dtype=float)
    bh = np.asarray(bh_close[i0 : i1 + 1], dtype=float)
    if len(eq) < 2 or not np.isfinite(eq[0]) or eq[0] <= 0:
        return {}
    eq = eq / eq[0]
    bh = bh / bh[0]

    # 只計算「進場點落在窗內」的交易
    win_trades = [t for t in trades if i0 <= t["entry_i"] <= i1]
    closed = [t for t in win_trades if t["exit_i"] is not None and t["exit_i"] <= i1]
    wins = [t for t in closed if t["ret"] > 0]

    return {
        "bars": int(i1 - i0 + 1),
        "strat_return": float(eq[-1] - 1.0),
        "bh_return": float(bh[-1] - 1.0),
        "excess": float(eq[-1] - bh[-1]),
        "strat_mdd": max_drawdown(eq),
        "bh_mdd": max_drawdown(bh),
        "strat_sharpe": annualised_sharpe(eq),
        "bh_sharpe": annualised_sharpe(bh),
        "n_trades": len(win_trades),
        "n_closed": len(closed),
        "win_rate": (len(wins) / len(closed)) if closed else float("nan"),
        "avg_trade_ret": (
            float(np.mean([t["ret"] for t in closed])) if closed else float("nan")
        ),
        "exposure": float(np.mean(in_market[i0 : i1 + 1])),
    }


def run_backtest(
    dates,
    open_,
    close,
    fast: int = 20,
    slow: int = 50,
    fill: str = "next_open",
    cost_bps: float = 0.0,
    enter_on_warmup: bool = True,
):
    """一站式：訊號 → 模擬 → 回傳 (sim, ema_fast, ema_slow)。"""
    ef, es, cu, cd = crossover_signals(close, fast, slow, enter_on_warmup)
    sim = simulate(open_, close, cu, cd, fill=fill, cost_bps=cost_bps)
    sim["ema_fast"] = ef
    sim["ema_slow"] = es
    sim["cross_up"] = cu
    sim["cross_down"] = cd
    return sim

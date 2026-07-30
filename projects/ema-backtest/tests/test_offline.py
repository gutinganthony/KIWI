#!/usr/bin/env python3
"""離線測試：不碰網路，驗證回測引擎的正確性。

含正向案例（「應該成立的事有成立」）——只測「該被擋的有被擋」會漏掉
全域淘汰型缺陷（見 agents/LEARNINGS.md 2026-07-30）。

跑法：python3 projects/ema-backtest/tests/test_offline.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ema_backtest import (  # noqa: E402
    annualised_sharpe,
    crossover_signals,
    ema,
    max_drawdown,
    run_backtest,
    simulate,
    window_metrics,
)

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name}  {detail}")
        FAILED.append(name)


# ---------------------------------------------------------------- EMA
def test_ema_matches_pandas():
    print("test_ema_matches_pandas")
    import pandas as pd

    rng = np.random.default_rng(42)
    x = 100 + np.cumsum(rng.normal(0, 1, 300))
    for span in (20, 50):
        mine = ema(x, span)
        theirs = pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()
        check(
            f"span={span} 與 pandas ewm(adjust=False) 一致",
            np.allclose(mine, theirs),
            f"max diff={np.max(np.abs(mine - theirs)):.2e}",
        )


def test_ema_known_values():
    print("test_ema_known_values")
    # alpha = 2/(3+1) = 0.5；seed=10 → 10, 0.5*20+0.5*10=15, 0.5*30+0.5*15=22.5
    out = ema([10.0, 20.0, 30.0], span=3)
    check("手算三步值正確", np.allclose(out, [10.0, 15.0, 22.5]), str(out))


# ---------------------------------------------------------------- 訊號
def test_warmup_suppresses_signals():
    print("test_warmup_suppresses_signals")
    rng = np.random.default_rng(7)
    x = 100 + np.cumsum(rng.normal(0, 2, 400))
    _, _, cu, cd = crossover_signals(x, 20, 50, enter_on_warmup=False)
    check("前 50 根無任何訊號", not cu[:50].any() and not cd[:50].any())
    check("正向案例：整段有產生訊號", cu.sum() > 0 and cd.sum() > 0,
          f"cu={cu.sum()} cd={cd.sum()}")


def test_warmup_initial_state():
    print("test_warmup_initial_state")
    up = np.linspace(100, 400, 300)          # 起點即多頭排列，全程無穿越
    _, _, cu_strict, _ = crossover_signals(up, 20, 50, enter_on_warmup=False)
    _, _, cu_init, _ = crossover_signals(up, 20, 50, enter_on_warmup=True)
    check("嚴格定義下：無穿越即無訊號", cu_strict.sum() == 0)
    check("enter_on_warmup 在第 50 根補一次進場", cu_init.sum() == 1 and cu_init[50])

    down = np.linspace(400, 100, 300)         # 起點即空頭排列
    _, _, cu_d, _ = crossover_signals(down, 20, 50, enter_on_warmup=True)
    check("起點為空頭排列時不補進場（不會硬塞多單）", cu_d.sum() == 0)


def test_cross_direction_is_correct():
    print("test_cross_direction_is_correct")
    # 前 200 根下跌、後 200 根上漲 → 必定有一次黃金交叉，且在轉折之後
    x = np.concatenate([np.linspace(200, 100, 200), np.linspace(100, 300, 200)])
    ef, es, cu, cd = crossover_signals(x, 20, 50)
    idx = np.flatnonzero(cu)
    check("上升段出現黃金交叉", len(idx) >= 1, str(idx))
    if len(idx):
        t = idx[0]
        check("黃金交叉點 EMA20 > EMA50", ef[t] > es[t])
        check("前一根 EMA20 <= EMA50", ef[t - 1] <= es[t - 1])
        check("黃金交叉發生在趨勢轉折之後", t > 200, f"t={t}")


# ---------------------------------------------------------------- 模擬
def test_no_lookahead_next_open():
    print("test_no_lookahead_next_open")
    x = np.concatenate([np.linspace(200, 100, 200), np.linspace(100, 300, 200)])
    op = np.roll(x, 1)
    op[0] = x[0]
    sim = run_backtest(None, op, x, fill="next_open")
    cu_idx = np.flatnonzero(sim["cross_up"])
    check("有成交", len(sim["trades"]) >= 1)
    if len(sim["trades"]) and len(cu_idx):
        entry = sim["trades"][0]["entry_i"]
        check(
            "進場 K 棒嚴格晚於訊號 K 棒（無 look-ahead）",
            entry == cu_idx[0] + 1,
            f"entry={entry} signal={cu_idx[0]}",
        )
        check(
            "進場價用的是進場當根開盤價",
            sim["trades"][0]["entry_px"] == op[entry],
        )


def test_close_fill_is_same_bar():
    print("test_close_fill_is_same_bar")
    x = np.concatenate([np.linspace(200, 100, 200), np.linspace(100, 300, 200)])
    op = np.roll(x, 1); op[0] = x[0]
    sim = run_backtest(None, op, x, fill="close")
    cu_idx = np.flatnonzero(sim["cross_up"])
    check("close 模式當根成交", sim["trades"][0]["entry_i"] == cu_idx[0])


def test_monotonic_uptrend_tracks_buy_and_hold():
    print("test_monotonic_uptrend_tracks_buy_and_hold")
    # 全程單調上漲 → 黃金交叉後一路持有，最終權益應接近買入持有（差在進場前的空手段）
    x = np.linspace(100, 400, 500)
    op = np.roll(x, 1); op[0] = x[0]
    sim = run_backtest(None, op, x)
    eq = sim["equity"]
    entry = sim["trades"][0]["entry_i"]
    expected = x[-1] / op[entry]
    check("最終權益 = 出場價/進場價", abs(eq[-1] - expected) < 1e-9,
          f"eq={eq[-1]:.6f} exp={expected:.6f}")
    check("正向案例：單調上漲時策略確實在場內", sim["in_market"][-1])
    check("單調上漲時策略無回撤", max_drawdown(eq) > -1e-9)


def test_monotonic_downtrend_stays_flat():
    print("test_monotonic_downtrend_stays_flat")
    x = np.linspace(400, 100, 500)
    op = np.roll(x, 1); op[0] = x[0]
    sim = run_backtest(None, op, x)
    check("全程下跌不進場", len(sim["trades"]) == 0)
    check("權益維持 1.0", np.allclose(sim["equity"], 1.0))
    check("空手時無回撤（優於買入持有）", max_drawdown(sim["equity"]) == 0.0)


def test_costs_reduce_return():
    print("test_costs_reduce_return")
    rng = np.random.default_rng(3)
    x = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, 900)))
    op = np.roll(x, 1); op[0] = x[0]
    free = run_backtest(None, op, x, cost_bps=0.0)
    paid = run_backtest(None, op, x, cost_bps=25.0)
    check("有成本的權益較低", paid["equity"][-1] < free["equity"][-1],
          f"free={free['equity'][-1]:.4f} paid={paid['equity'][-1]:.4f}")
    check("正向案例：這段隨機序列確實有多筆交易", len(free["trades"]) >= 3,
          f"n={len(free['trades'])}")


def test_position_state_machine():
    print("test_position_state_machine")
    rng = np.random.default_rng(11)
    x = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1200)))
    op = np.roll(x, 1); op[0] = x[0]
    sim = run_backtest(None, op, x)
    tr = sim["trades"]
    ok = all(
        tr[i]["exit_i"] is not None and tr[i]["exit_i"] < tr[i + 1]["entry_i"]
        for i in range(len(tr) - 1)
    )
    check("交易不重疊（不會同時持有兩筆）", ok)
    check("每筆交易出場晚於進場",
          all(t["exit_i"] is None or t["exit_i"] > t["entry_i"] for t in tr))


# ---------------------------------------------------------------- 指標
def test_max_drawdown_known():
    print("test_max_drawdown_known")
    check("100→50→120 的 MDD = -50%",
          abs(max_drawdown([100.0, 50.0, 120.0]) + 0.5) < 1e-12)
    check("單調上升 MDD = 0",
          abs(max_drawdown([1.0, 2.0, 3.0])) < 1e-12)
    check("100→200→100 的 MDD = -50%",
          abs(max_drawdown([100.0, 200.0, 100.0]) + 0.5) < 1e-12)


def test_sharpe_sanity():
    print("test_sharpe_sanity")
    check("完全持平（空手）→ Sharpe 為 0（std=0 保護）",
          annualised_sharpe(np.ones(252)) == 0.0)
    check("短序列不崩潰", annualised_sharpe([1.0, 1.1]) == 0.0)
    rng = np.random.default_rng(1)
    eq2 = np.cumprod(np.r_[1.0, 1 + rng.normal(0.001, 0.01, 2520)])
    s = annualised_sharpe(eq2)
    check("正漂移隨機序列 Sharpe > 0", s > 0, f"sharpe={s:.3f}")


def test_window_metrics_rebases():
    print("test_window_metrics_rebases")
    eq = np.array([1.0, 1.1, 1.21, 1.331, 1.4641])
    bh = np.array([10.0, 11.0, 12.1, 13.31, 14.641])
    m = window_metrics(eq, bh, np.ones(5, bool), [], 2, 4)
    check("視窗內策略報酬 = 1.4641/1.21-1 = 21%",
          abs(m["strat_return"] - 0.21) < 1e-9, str(m["strat_return"]))
    check("買入持有同基準時兩者相等",
          abs(m["strat_return"] - m["bh_return"]) < 1e-9)
    check("超額為 0", abs(m["excess"]) < 1e-9)
    check("exposure 正確", m["exposure"] == 1.0)


def test_window_metrics_trade_counting():
    print("test_window_metrics_trade_counting")
    trades = [
        {"entry_i": 1, "exit_i": 3, "ret": 0.10},   # 全在窗前
        {"entry_i": 12, "exit_i": 18, "ret": 0.20},  # 窗內完整
        {"entry_i": 15, "exit_i": 40, "ret": -0.05},  # 窗內進場、窗外出場
    ]
    eq = np.linspace(1, 2, 50)
    m = window_metrics(eq, eq, np.ones(50, bool), trades, 10, 20)
    check("只算窗內進場的交易 → 2 筆", m["n_trades"] == 2, str(m["n_trades"]))
    check("窗內完整平倉 1 筆", m["n_closed"] == 1, str(m["n_closed"]))
    check("勝率 = 1/1", m["win_rate"] == 1.0)


def test_nan_gap_handling():
    print("test_nan_gap_handling")
    x = np.concatenate([np.linspace(100, 200, 300), np.linspace(200, 300, 200)])
    x[350:355] = np.nan
    op = np.roll(x, 1); op[0] = x[0]
    sim = run_backtest(None, op, x)
    check("含 NaN 缺口不致崩潰且權益全程有限",
          np.all(np.isfinite(sim["equity"])))


# ---------------------------------------------------------------- 報告層
def test_months_before():
    print("test_months_before")
    from datetime import date

    from run_report import months_before

    check("跨年", months_before(date(2026, 3, 15), 6) == date(2025, 9, 15))
    check("同年", months_before(date(2026, 7, 30), 1) == date(2026, 6, 30))
    check("24 個月", months_before(date(2026, 7, 30), 24) == date(2024, 7, 30))
    check("月底日不存在時退到當月最後一天",
          months_before(date(2026, 3, 31), 1) == date(2026, 2, 28))


def test_window_requires_real_coverage():
    print("test_window_requires_real_coverage")
    from datetime import date, timedelta

    from run_report import analyse

    # 只有 400 個交易日（約 19 個月）的新上市股 → 24M 窗必須留空，
    # 否則「上市至今」會被偽裝成「過去 24 個月」的報酬
    n = 400
    d0 = date(2026, 7, 10)
    dates = sorted(d0 - timedelta(days=int(i * 1.4)) for i in range(n))
    rng = np.random.default_rng(5)
    cl = 100 * np.exp(np.cumsum(rng.normal(0.001, 0.02, n)))
    op = np.roll(cl, 1); op[0] = cl[0]
    rec = analyse("NEWCO", dates, op, cl)
    check("24M 窗留空（資料不足）", rec["windows"]["24M"] == {})
    check("正向案例：3M 窗有值（資料足夠）", bool(rec["windows"]["3M"]),
          str(rec["windows"]["3M"])[:80])
    check("正向案例：6M 窗有值", bool(rec["windows"]["6M"]))


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print()
    if FAILED:
        print(f"❌ {len(FAILED)} 項失敗: {FAILED}")
        sys.exit(1)
    print("✅ 全部通過")

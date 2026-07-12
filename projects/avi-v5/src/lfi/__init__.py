"""LFI — Leverage/Funding Index (ACT 系統第四錶).

量的是「市場借錢買股的擁擠度」——AIR TRF 融資利差（AXW）的可計算替身。
真品（CME AIR TRF spread）歷史數據在付費牆後；本模組用免費可得的
VVIX/VIX（vol-of-vol 富貴度）＋ HYG−SPY（信用相對強度）合成 proxy。

實證依據：projects/avi-v5/scripts/leading_indicators_backtest.py
  lev_stress_proxy 在 1996-2020 深樣本是 16 個指標中最強的短線領先訊號
  （SPY 20 天 IC −0.164，8/8 資產×週期全過 BH-FDR 10%、樣本內外方向一致）。
  方向：高＝槓桿擁擠→未來 1-20 天報酬傾斜向下；極低（去槓桿洗完）→反彈傾斜。

輸出以 0-100 分位數呈現（與 CRI/TSI 同尺度）：
  分數 = 槓桿壓力在滾動窗內的百分位。高分＝擁擠＝紅（勿加槓桿）。
  >90 HIGH 🔴 · 10-90 NORMAL 🟡 · <10 LOW 🟢（回升時=去槓桿完成訊號）

純函式、無 I/O、對缺資料/短序列容錯——呼叫端（update_dashboard）須自行
try/except 並在失敗時降級，絕不可讓本模組的例外凍結整個 dashboard。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# 與 leading_indicators_backtest.py 一致的參數（保持可比）
Z_WINDOW = 756          # 3 年滾動；資料不足時自動縮短（見 _adaptive）
Z_MINP = 252            # z-score 最少樣本
PCTL_WINDOW = 756       # 分位數滾動窗
CREDIT_LOOKBACK = 5     # HYG/SPY 相對報酬回看天數
CLIP = 4.0              # z-score 截斷（防極端值主宰）

HIGH_PCTL = 90          # >= → HIGH（紅）
LOW_PCTL = 10           # <= → LOW（綠）


def _z(s: pd.Series, window: int, minp: int) -> pd.Series:
    m = s.rolling(window, min_periods=minp).mean()
    sd = s.rolling(window, min_periods=minp).std()
    return (s - m) / sd.replace(0, np.nan)


def compute_lfi_series(spy: pd.Series, hyg: pd.Series,
                       vvix: pd.Series, vix: pd.Series) -> pd.DataFrame:
    """回傳含 lfi_z（原始壓力 z）與 lfi_pctl（0-100 滾動分位）的 DataFrame。

    參數為收盤價/指數的 pandas Series（index 為日期）。長度可不同，會依日期對齊。
    """
    df = pd.concat(
        {"spy": spy, "hyg": hyg, "vvix": vvix, "vix": vix}, axis=1
    ).sort_index()
    # 只保留四者都有值的交易日（對齊；ffill 補假日差可能引入前視，故用 inner）
    df = df.dropna(subset=["spy", "hyg", "vvix", "vix"])
    if len(df) < Z_MINP + CREDIT_LOOKBACK + 5:
        raise ValueError(f"LFI 序列太短：{len(df)} 天（需 >= {Z_MINP + CREDIT_LOOKBACK + 5}）")

    n = len(df)
    zwin = min(Z_WINDOW, n)
    zminp = min(Z_MINP, max(60, n // 3))
    pwin = min(PCTL_WINDOW, n)

    vvix_vix = df["vvix"] / df["vix"]
    credit_rel = df["hyg"].pct_change(CREDIT_LOOKBACK) - df["spy"].pct_change(CREDIT_LOOKBACK)

    lfi_z = (_z(vvix_vix, zwin, zminp).clip(-CLIP, CLIP)
             - _z(credit_rel, zwin, zminp).clip(-CLIP, CLIP))

    # 滾動百分位（0-100）：今天的壓力在過去 pwin 天中的排名
    lfi_pctl = lfi_z.rolling(pwin, min_periods=zminp).rank(pct=True) * 100

    out = pd.DataFrame({
        "vvix_vix": vvix_vix,
        "credit_rel_5d": credit_rel,
        "lfi_z": lfi_z,
        "lfi_pctl": lfi_pctl,
    }, index=df.index)
    return out


def level_of(pctl: float) -> str:
    if pctl is None or (isinstance(pctl, float) and np.isnan(pctl)):
        return "──"
    if pctl >= HIGH_PCTL:
        return "HIGH"
    if pctl <= LOW_PCTL:
        return "LOW"
    return "NORMAL"


def _trailing_streak(pctl_series: pd.Series, threshold: float) -> int:
    """從最新一日往回數：LFI 分位連續 >= threshold 的交易日數（含最新日）。
    最新日就 < threshold → 回傳 0。用於 dashboard「目前在此水位已維持幾天」。"""
    vals = pctl_series.dropna().values
    n = 0
    for v in vals[::-1]:
        if v >= threshold:
            n += 1
        else:
            break
    return n


def latest_reading(spy, hyg, vvix, vix) -> dict:
    """回傳最新一日 LFI 讀數 dict（供 dashboard payload）。失敗時由呼叫端接例外。"""
    ser = compute_lfi_series(spy, hyg, vvix, vix)
    last = ser.dropna(subset=["lfi_pctl"]).iloc[-1]
    pctl = float(last["lfi_pctl"])
    lvl = level_of(pctl)
    # 上升/下降旗標：最新 pctl 是否比 10 日前高（用於「去槓桿完成=回升」判讀）
    tail = ser["lfi_pctl"].dropna()
    rising = bool(tail.iloc[-1] > tail.iloc[-11]) if len(tail) > 11 else None
    return {
        "score": round(pctl, 1),
        "level": lvl,
        "z": round(float(last["lfi_z"]), 2),
        "vvix_vix": round(float(last["vvix_vix"]), 3),
        "credit_rel_5d": round(float(last["credit_rel_5d"]) * 100, 2),  # %
        "rising": rising,
        # 目前水位已連續維持幾個交易日（見頂特徵驗證：≥95 才有一點統計味道）
        "days_ge_80": _trailing_streak(tail, 80),
        "days_ge_90": _trailing_streak(tail, 90),
        "days_ge_95": _trailing_streak(tail, 95),
        "as_of": ser.index[-1].strftime("%Y-%m-%d") if hasattr(ser.index[-1], "strftime") else str(ser.index[-1]),
    }

"""
ECY — Excess CAPE Yield（超額 CAPE 殖利率）

KIWI 的「脆弱度」讀數。它回答的問題是 AVI／CRI／TSI 三個都答不出來的那一個：
**如果出事，會有多痛？**

    ECY = 1/CAPE − 實質10Y殖利率
           ↑              ↑
      股票的實質殖利率   債券的實質殖利率（機會成本）

白話：「我多承擔股票的全部風險，市場多付我多少？」ECY 越薄，代表市場
對承擔風險的補償越少，同樣的壞消息會跌得越深。

──────────────────────────────────────────────────────────────────────
實證定位（scripts/erp_validation.py，Shiller 1871-2026）
──────────────────────────────────────────────────────────────────────
與未來實質總報酬的相關係數：
    1年 0.227 ／ 2年 0.297 ／ 3年 0.351 ／ 5年 0.441 ／ 10年 0.582

→ **ECY 做不到擇時預警**（1 年相關 0.227 等於沒用），不要拿它抓時點。
→ 但它做得到「量測曝險」，而且差異很大：

    ECY 分組        未來1年平均報酬    未來1年跌超過10%的機率
    最貴 20%            +1.7%              25.9%
    中間 60%            +7.8%              16.3%
    最便宜 20%         +16.1%               7.9%

    最貴與最便宜之間，一年內大跌的機率差 3.3 倍。

**為什麼不做成長調整**：原本設計提案要用高登模型加上 g（1/CAPE + g − 實質10Y）。
實測推翻：ECY+g20 相關 0.460 << 純 ECY 0.594。根因是盈餘成長強烈均值回歸
（過去30年 g → 未來10年 g 相關 −0.490），加 trailing g 等於加入一個與目標
負相關的項。因此本模組**直接用純 ECY，不做 g 調整**。

方法一致性：歷史分布與當期值都用「名目10Y − 過去10年 CPI 年化通膨」計算
實質殖利率。不混用 TIPS，避免當期值與歷史百分位的量測方法不一致。
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_SHILLER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "ext", "shiller_sp500.csv",
)

# 等級門檻用歷史百分位定義，不用絕對值——因為 ECY 的合理區間會隨利率環境移動。
# 百分位越低 = ECY 越薄 = 越脆弱。
_LEVELS = [
    (10, "EXTREME"),    # 歷史最薄的 10%：1920年代末、1990年代末、2024迄今
    (25, "HIGH"),
    (50, "ELEVATED"),
    (75, "NORMAL"),
    (101, "LOW"),
]


@dataclass
class ECYResult:
    ecy: float                 # 超額 CAPE 殖利率（%）
    percentile: float          # 歷史百分位（0-100，越低越脆弱）
    level: str                 # EXTREME / HIGH / ELEVATED / NORMAL / LOW
    cape: float
    earnings_yield: float      # 1/CAPE（%）
    real_10y: float            # 實質10Y（%）
    inflation_10y: float       # 過去10年年化通膨（%）
    hist_median: float         # 歷史中位數（%），供對照
    n_hist: int                # 歷史樣本數
    source: str                # "computed" / "fallback"

    def summary(self) -> str:
        return (
            f"ECY {self.ecy:.2f}%（歷史百分位 {self.percentile:.0f}%，{self.level}）"
            f"｜1/CAPE {self.earnings_yield:.2f}% − 實質10Y {self.real_10y:.2f}%"
            f"｜歷史中位數 {self.hist_median:.2f}%"
        )


def _level_of(pct: float) -> str:
    for thr, name in _LEVELS:
        if pct < thr:
            return name
    return "LOW"


def _load_history() -> Optional[pd.DataFrame]:
    """Shiller 1871- 資料集，用來建立 ECY 的歷史分布。"""
    if not os.path.exists(_SHILLER):
        logger.warning(f"Shiller history not found at {_SHILLER}")
        return None
    df = pd.read_csv(_SHILLER)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index().rename(columns={
        "Consumer Price Index": "cpi",
        "Long Interest Rate": "nom10y",
        "PE10": "cape",
    })
    # 最新幾列的衍生欄位為 0（資料集尚未填），視為缺值
    for c in ("cpi", "nom10y", "cape"):
        if c in df.columns:
            df[c] = df[c].replace(0.0, np.nan)
    return df


def _historical_ecy(df: pd.DataFrame) -> pd.Series:
    """用與當期值完全相同的方法計算歷史 ECY 序列（%）。"""
    infl10 = (df["cpi"] / df["cpi"].shift(120)) ** (1 / 10) - 1   # 過去10年年化通膨
    real10y = df["nom10y"] / 100.0 - infl10
    ecy = (1.0 / df["cape"]) - real10y
    return (ecy * 100).dropna()


def compute_ecy(
    cape: float,
    nominal_10y: float,
    cpi_now: Optional[float] = None,
    cpi_10y_ago: Optional[float] = None,
) -> Optional[ECYResult]:
    """計算當期 ECY 與其歷史百分位。

    Args:
        cape:        目前的 Shiller CAPE
        nominal_10y: 名目 10Y 公債殖利率（%，例如 4.4 代表 4.4%）
        cpi_now:     目前 CPI 指數水準（可省略，省略時用 Shiller 資料集末端外推）
        cpi_10y_ago: 十年前的 CPI 指數水準（同上）

    Returns:
        ECYResult，資料不足時回 None（呼叫端應視為「本期無 ECY 讀數」，
        不要用假值填補——見 agents/LEARNINGS.md 對靜默降級的教訓）。
    """
    if not cape or cape <= 0 or nominal_10y is None:
        logger.warning("compute_ecy: invalid cape/nominal_10y")
        return None

    hist_df = _load_history()
    if hist_df is None or hist_df.empty:
        return None
    hist = _historical_ecy(hist_df)
    if len(hist) < 240:
        logger.warning(f"compute_ecy: history too short ({len(hist)})")
        return None

    # 過去10年年化通膨
    if cpi_now and cpi_10y_ago and cpi_10y_ago > 0:
        infl10 = (cpi_now / cpi_10y_ago) ** (1 / 10) - 1
        src = "computed"
    else:
        # 退回用 Shiller 資料集末端可得的最後一個 10 年通膨
        c = hist_df["cpi"].dropna()
        if len(c) < 121:
            return None
        infl10 = (c.iloc[-1] / c.iloc[-121]) ** (1 / 10) - 1
        src = "fallback"
        logger.warning("compute_ecy: 用 Shiller 資料集末端通膨（當期 CPI 未提供）")

    ey = 1.0 / cape * 100.0
    real10y = nominal_10y - infl10 * 100.0
    ecy = ey - real10y
    pct = float((hist < ecy).mean() * 100)

    return ECYResult(
        ecy=round(ecy, 2),
        percentile=round(pct, 1),
        level=_level_of(pct),
        cape=round(cape, 2),
        earnings_yield=round(ey, 2),
        real_10y=round(real10y, 2),
        inflation_10y=round(infl10 * 100, 2),
        hist_median=round(float(hist.median()), 2),
        n_hist=len(hist),
        source=src,
    )

# TSI 真實數據回測資料集

## 資料來源（公開 GitHub 鏡像，2026-06 下載）

| 檔案 | 內容 | 期間 | 原始來源 |
|------|------|------|----------|
| `SPY.csv` | S&P 500 ETF 日線 | 1993-2020 | jacksoncrow Kaggle Stock Market Dataset |
| `QQQ.csv` | Nasdaq 100 ETF 日線 | 1999-2020 | 同上 |
| `HYG.csv` | 高收益債 ETF 日線 | 2007-2020 | 同上 |
| `SOXX.csv` | 半導體 ETF 日線 | 2001-2020 | 同上 |
| `SMH.csv` | 半導體 ETF 日線 | 2000-2020 | 同上 |
| `MU.csv` | Micron 記憶體股 日線 | 1984-2020 | 同上 |
| `NVDA.csv` | NVIDIA 日線 | 1999-2020 | 同上 |
| `VIX.csv` | CBOE 波動率指數 | 1990-2025 | CBOE 官方 VIX_History.csv |
| `VVIX.csv` | CBOE 波動率的波動率 | 2006-2025 | CBOE 官方 VVIX_History.csv |
| `tsi_history.csv` | 回測產生的每日 TSI 分數+各指標 | 2006-2020 | `real_backtest.py` 產生 |

涵蓋的重大崩盤：2000 網路泡沫、2008 金融海嘯、2010 閃崩、2011 歐債、
2015 人民幣貶值閃崩、2018 Volmageddon + 聖誕崩盤、2020 COVID。

## 回測腳本

- `scripts/real_backtest.py` — 逐日計算 TSI，評估崩盤偵測率/領先天數/假警報率/指標排名
- `scripts/tsi_optimize.py` — ROC-AUC 多時間窗評估 + 邏輯回歸權重最佳化

## 核心發現（詳見 git commit 訊息與 KIWI_INDEX_FRAMEWORK.md）

1. **最強預測指標**：tech_breadth (D1 AUC 0.93)、vvix_lead (0.82)、
   vix_tech_correlation (0.78)、tech_crash_day (0.76)
2. **TSI v4** 用實證最佳化權重，交叉驗證 AUC = 0.747（樣本外）
3. **誠實限制**：純粹「無預兆突發 1 日崩盤」的預測上限約 AUC 0.55-0.6；
   但「發展中的崩盤」可達 AUC 0.75，提前 1-3 天降風險有實際價值。

## 重現方式

```bash
cd projects/avi-v5
python scripts/real_backtest.py    # 重新生成 tsi_history.csv + 評估
python scripts/tsi_optimize.py     # 權重最佳化分析
```

資料下載（若需更新）：raw.githubusercontent.com 與 codeload.github.com
在本環境可連線，其餘金融 API（yfinance/FRED/stooq）被網路政策阻擋。

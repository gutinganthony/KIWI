---
title: AVI V5 + CPI 系統開發進度備份 (Session Progress Backup)
url: local
source: Claude Code Session
date_added: 2026-05-14
last_updated: 2026-05-14
topic: technology
tags: [avi-v5, cpi, crash-prediction, quant, personal-project, progress-backup]
version: 1.0
---

## AVI V5 系統

AVI V5（Aggregate Valuation Index 第五版）是一套月度更新的市場高估/低估綜合評分系統。

### 開發階段

- **Phase 1 — 資料來源整合**：完成。串接 FRED（聯準會經濟數據庫）、yfinance（Yahoo Finance）、multpl.com 三大數據源，涵蓋估值、總經、波動率、信用等面向。
- **Phase 2 — 計算引擎**：完成。以 20 年滾動百分位（rolling percentile）為基礎，將每個指標標準化為 0–10 分。
- **Phase 3 — 景氣循環 + GARCH**：完成。加入 Regime Detection（景氣循環偵測）及 GARCH 波動率模型，提供動態調整權重。
- **Phase 4 — 回測與比較**：完成。實作 V4 / V4.1 / V4.2 多版本回測比較框架。

### 核心規格

- **14 個指標**，分佈於 **6 個維度**（估值、信用、波動率、動量、廣度、總經）
- **20 年滾動百分位**標準化
- 月度更新頻率

### 回測成績

- **V4.2 Sharpe Ratio：0.73**
- **V4.2 Max Drawdown：-29%**（相比 Buy & Hold 的 -53%，大幅改善）
- 回測期間涵蓋 2000–2025 年

### 已知問題

- **Buffett Indicator（市值/GDP）**：FRED 系列偶爾回傳空值，需要 fallback 處理
- **P/S Ratio**：multpl.com 資料有間歇性缺口，已知但尚未完全修復

---

## CPI 崩盤概率指數

CPI（Crash Probability Index）是每日更新的 0–100 分崩盤概率指數，回答「接下來一個月市場崩盤的概率有多高」。

### 核心規格

- **10 個日頻指標**：VIX 期限結構、VIX 急升、GARCH-VIX 差距、信用利差加速、市場廣度背離、放量下跌天數、RSI 背離、均線距離反轉、殖利率曲線陡化、動量崩潰
- **0–100 分計分**
- **3 層壓力加成**（stress boost）：用於 7 天內短期偵測
- **Flash Alert**：當 4+ 個指標同時觸發時發出即時警報

### 回測成績

- **4/4 重大崩盤偵測成功**：
  - Dot-com (2000)：CPI 峰值 72，提前 38 天
  - GFC (2008)：CPI 峰值 89，提前 42 天
  - COVID (2020)：CPI 峰值 91，提前 26 天
  - 2022 Bear Market：CPI 峰值 61，提前 35 天
- **Lead Time：23–42 天**（符合 1 個月預警目標）
- **嵌入驗證（Embedded Validation）**：30 天窗口 5/5、7 天窗口 5/5

### 前端

- HTML Dashboard（深色主題 + 英中雙語切換）
- Pine Script 模板（TradingView 用）

---

## 檔案結構

```
projects/avi-v5/
├── .env                          # API keys (FRED etc.)
├── .env.example                  # 環境變數範例
├── .gitignore
├── ARCHITECTURE.md               # AVI V5 架構文件
├── CPI_ARCHITECTURE.md           # CPI 架構文件
├── requirements.txt
├── backtest/
│   ├── __init__.py
│   ├── compare.py                # V4/V4.1/V4.2 回測比較
│   ├── crises.py                 # 歷史危機事件定義
│   ├── metrics.py                # 績效指標計算
│   ├── portfolio.py              # 投資組合模擬
│   └── signals.py                # 交易信號產生
├── config/
│   ├── avi_weights.yaml          # AVI 指標權重設定
│   ├── indicators.yaml           # 指標定義
│   └── regime_params.yaml        # 景氣循環參數
├── dashboard/
│   ├── __init__.py
│   ├── cpi_dashboard.py          # Dashboard 產生器（含雙語支援）
│   └── template.html             # HTML 模板（深色主題 + i18n）
├── pine/
│   └── cpi_indicator.pine        # TradingView Pine Script 模板
├── scripts/
│   ├── run_backtest.py           # AVI 回測執行
│   ├── run_cpi.py                # CPI 日頻計算
│   ├── run_dashboard.py          # Dashboard 產生
│   └── run_monthly.py            # AVI 月度計算
├── src/
│   ├── __init__.py
│   ├── cpi/
│   │   ├── __init__.py           # CPI 核心引擎
│   │   ├── backtest.py           # CPI 回測邏輯
│   │   └── data.py               # CPI 資料擷取
│   ├── data/
│   │   ├── __init__.py
│   │   ├── collector.py          # 統一資料收集器
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── fred.py           # FRED API 資料源
│   │       ├── multpl.py         # multpl.com 資料源
│   │       └── yfinance_source.py # Yahoo Finance 資料源
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── avi_core.py           # AVI 核心計算引擎
│   │   └── percentile.py         # 百分位標準化
│   ├── garch/
│   │   ├── __init__.py
│   │   ├── garch_model.py        # GARCH 波動率模型
│   │   └── vix_comparison.py     # GARCH vs VIX 比較
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── avi_v5_pipeline.py    # 完整管線執行
│   └── regime/
│       ├── __init__.py
│       ├── feature_builder.py    # 景氣循環特徵建構
│       ├── regime_adjustment.py  # 景氣循環調整
│       └── regime_engine.py      # 景氣循環偵測引擎
└── tests/
    └── test_cpi_validation.py    # CPI 驗證測試
```

---

## 已知問題 & 下一步

### 已知問題

1. **FRED API 間歇性 500 錯誤**：目前偶爾會遇到 FRED 伺服器回傳 500，需要加入 yfinance fallback 機制作為備援。
2. **False Positive Rate 14%**：CPI 在部分非崩盤期間也會觸發偏高信號，需要進行閾值微調（threshold tuning）以降低誤報率。
3. **Buffett Indicator + P/S 數據缺口**：FRED 系列和 multpl.com 資料偶有缺失，需要更穩健的缺失值處理。

### 下一步規劃

1. **Phase 5 — TradingView 完整 MCP 整合（Playwright）**：使用 Playwright 自動化操作 TradingView，實現完整的 MCP（Market Context Panel）。目前仍為待辦。
2. **CPI 指標權重再校準**：隨著更多市場事件的發生，可能需要用更多樣本重新校準各指標的權重分配。
3. **yfinance fallback 實作**：為所有 FRED 指標加入 yfinance 備援數據源。
4. **Dashboard 增強**：已完成英中雙語切換功能。

---

## 指令備忘

```bash
python3 scripts/run_monthly.py --v5    # AVI V5 score
python3 scripts/run_cpi.py             # CPI current
python3 scripts/run_cpi.py --backtest  # CPI backtest
python3 scripts/run_dashboard.py       # Visual dashboard
python3 scripts/run_backtest.py        # AVI V4/V4.1/V4.2 comparison
```

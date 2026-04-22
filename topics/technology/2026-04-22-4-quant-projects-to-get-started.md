---
title: 四個量化交易入門專案 (4 Quant Projects to Get You Started)
url: https://docs.google.com/document/d/1qREcwG4E0FQUeYjtggLg3oEF9PlQ8Tq_3_KV7pEvCI8/edit?usp=drivesdk
source: Google Doc by @chrispathway
date_added: 2026-04-22
last_updated: 2026-04-22
topic: technology
tags: [quant-trading, python, portfolio-optimization, options, volatility, backtesting, HMM, CVaR, event-study, tutorial, weekend-project]
version: 1.0
---

## Summary

@chrispathway 整理的四個「週末就能做完」的量化交易入門專案，每個都附上簡短說明與教學連結。重點不是做出能賺錢的策略，而是**建立量化思維的基礎模組**：時間序列特徵工程、選擇權隱含波動率、尾部風險管理、事件驅動回測。四個專案剛好覆蓋了從「看市場」到「建投組」到「測策略」的完整流程。

---

## 四個專案總覽

| # | 專案名稱 | 核心技能 | 難度 | 關鍵工具 |
|---|---------|---------|------|---------|
| 1 | Market Regime Clustering | 時間序列特徵工程 + 非監督式學習 | ★★☆ | HMM / K-Means, pandas |
| 2 | Implied Volatility Surface Builder | 選擇權定價 + 數值方法 | ★★★ | Black-Scholes, scipy |
| 3 | CVaR Portfolio Optimisation | 尾部風險最佳化 | ★★☆ | CVXPY, numpy |
| 4 | Event-Driven Backtester | 條件報酬分析 + 回測框架 | ★★★ | pandas, statsmodels |

---

## 專案 1：Market Regime Clustering（市場狀態分群）

**你會做什麼：**
- 抓一段市場時間序列（例如 SPY）
- 建立特徵：滾動報酬率、已實現波動率、回撤幅度
- 用 HMM（Hidden Markov Model）或 K-Means 把市場切成不同「狀態」（regime）

**學到什麼：**
- 時間序列的特徵工程（rolling window, realized vol, drawdown）
- 市場行為在不同時期會根本性地改變（bull / bear / high-vol / low-vol）
- 這對風險管理和策略切換至關重要：**同一個策略在不同 regime 表現完全不同**

**教學連結：**
- [Market Regime Detection Using Hidden Markov Models in QSTrader](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/)

**延伸應用：**
- 可以用 regime label 當作策略的「開關」：只在特定市場狀態下才執行交易
- 也可以用來做動態資產配置：不同 regime 分配不同權重

---

## 專案 2：Implied Volatility Surface Builder（隱含波動率曲面）

**你會做什麼：**
- 拉一條選擇權鏈（option chain），包含各 strike 和到期日
- 用 Black-Scholes 反推隱含波動率（IV）
- 把 IV 畫成 3D 曲面（x = strike, y = expiry, z = IV）
- 額外畫出 skew（同到期不同 strike）和 term structure（同 strike 不同到期）

**學到什麼：**
- 選擇權價格 → 隱含波動率的轉換過程（數值求根，反解 BS 公式）
- **波動率微笑 / 偏斜（smile / skew）** 的含義：市場對下跌的恐懼定價
- **期限結構（term structure）**：短期 vs. 長期的不確定性預期
- 這是面試級別的視覺化輸出，放進 portfolio 非常加分

**教學連結：**
- [Build an Implied Volatility Surface with Python](https://www.pyquantnews.com/the-pyquant-newsletter/build-an-implied-volatility-surface-with-python)

**延伸應用：**
- IV surface 是選擇權交易的核心工具，可以用來找 mispricing
- 搭配 regime clustering：不同市場狀態下 IV surface 的形狀不同

---

## 專案 3：CVaR Portfolio Optimisation（條件風險值投組最佳化）

**你會做什麼：**
- 選 5–10 檔資產，拉歷史報酬
- 用 CVXPY（凸最佳化套件）建立最佳化問題
- 目標函數：最小化 CVaR（Conditional Value at Risk）= 最差 X% 情境下的期望損失

**學到什麼：**
- **CVaR vs. Variance**：大多數入門投組只做 mean-variance optimization（Markowitz），但這假設報酬是常態分布。CVaR 關注的是**尾部風險**——真正會讓你爆倉的那種損失。
- 凸最佳化的實務操作（CVXPY 語法、約束條件設定）
- 這更接近**實務中風險管理的做法**

**教學連結：**
- [Solving Conditional Value at Risk (CVaR) Portfolio Optimisation](https://quantjourney.substack.com/p/solving-conditional-value-at-risk)

**延伸應用：**
- 可以搭配 regime clustering：在高波動 regime 自動切換到 CVaR-optimized 的防禦性配置
- 加入 transaction cost 約束，讓結果更實務

---

## 專案 4：Event-Driven Backtester（事件驅動回測器）

**你會做什麼：**
- 收集真實事件資料（財報發布、CPI 公布、Fed 利率決議）
- 對每個事件，測量事件後 1–5 天的報酬分布
- 分析：平均報酬、hit rate（正報酬比例）、最大回撤

**學到什麼：**
- **條件報酬（conditional returns）** 的思維：不是問「這個策略長期表現如何」，而是問「在特定條件下，市場傾向怎麼動」
- 事件前後的風險特性（gap risk、liquidity dry-up）
- 不要只對技術指標做回測，要對**資訊事件**做回測

**教學連結：**
- [Event-Driven Backtesting with Python Part I](https://www.quantstart.com/articles/event-driven-backtesting-with-python-part-i/)

**延伸應用：**
- 可以用來建立「事件日曆策略」：在特定事件前調整倉位
- 搭配 NLP：用 AI 自動分類事件的 sentiment，加入回測

---

## 四個專案的學習路徑建議

```
[1] Regime Clustering ──→ 理解市場有不同「狀態」
        │
        ▼
[3] CVaR Optimisation ──→ 在不同狀態下做風險管理
        │
        ▼
[4] Event Backtester  ──→ 找出事件驅動的交易機會
        │
        ▼
[2] IV Surface        ──→ 用選擇權市場的資訊補強判斷
```

建議順序：**1 → 3 → 4 → 2**（由淺入深，從股票到衍生品）

---

## 與 KIWI 其他條目的關聯

- **[AI 量化交易系統教程](./2026-04-07-ai-quant-trading-system-tutorial.md)**：那篇是用 LLM 做加密貨幣交易，偏 AI-native。這篇是傳統量化基礎功，兩者互補。
- **[40 個 GitHub 賺錢倉庫](./2026-04-07-40-github-repos-to-make-money.md)**：裡面的金融投資區塊（Qlib、vnpy、Freqtrade）可以搭配這四個專案一起學。

---

## Update Log

- 2026-04-22 v1.0: Initial entry. 基於 @chrispathway Google Doc 全文整理，加入學習路徑建議與 KIWI 交叉引用。

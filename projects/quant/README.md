# Quant Projects

基於 [@chrispathway 的 4 Quant Projects](../../topics/technology/2026-04-22-4-quant-projects-to-get-started.md) 實作的完整 Python 程式碼。

## Quick Start

```bash
cd projects/quant
pip install -r requirements.txt

# 依序執行
python 01_market_regime_clustering.py
python 02_iv_surface_builder.py
python 03_cvar_portfolio_optimization.py
python 04_event_driven_backtester.py
```

## 專案列表

| # | 專案 | 核心概念 | 輸出 |
|---|------|---------|------|
| 1 | Market Regime Clustering | HMM + K-Means, 時間序列特徵工程 | regime_clustering_results.png |
| 2 | IV Surface Builder | Black-Scholes 反解, 波動率曲面 | iv_surface.png |
| 3 | CVaR Portfolio Optimization | 凸最佳化, 尾部風險管理 | cvar_portfolio_results.png |
| 4 | Event-Driven Backtester | 事件研究, 條件報酬分析 | event_study_results.png |

## 建議學習順序

```
1 (Regime) → 3 (CVaR) → 4 (Event) → 2 (IV Surface)
```

## 串接應用

- **1 + 3**: 用 regime 信號動態切換 CVaR/aggressive 配置
- **1 + 4**: 分析不同 regime 下事件效應是否不同
- **3 + 4**: 事件前自動切換到防禦性配置
- **2 + 4**: Fed 決議前後 IV surface 的形變

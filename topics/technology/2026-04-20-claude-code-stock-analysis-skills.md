---
title: Claude Code 股票分析 Skills 安裝筆記 (TradingView 生態)
url: null
source: 個人設定筆記
date_added: 2026-04-20
last_updated: 2026-04-20
topic: technology
tags: [claude-code, skills, mcp, tradingview, pine-script, stock-analysis, technical-analysis, setup]
version: 1.0
---

## Summary

安裝一組 TradingView 相關的 Claude Code skills 與 MCP servers，讓 Claude 能做技術分析、撰寫 Pine Script、以及呼叫 TradingView 的篩選器與指標 API。全部安裝在 global 範圍 (`~/.claude/`)，不綁特定專案。

## 概念釐清：Skill vs MCP Server

| | Skill | MCP Server |
|---|---|---|
| 是什麼 | `SKILL.md` 指引檔，教 Claude 「怎麼做」 | 外部行程，給 Claude 「能做的工具」|
| 位置 | `~/.claude/skills/<name>/SKILL.md` | `~/.claude.json` 的 `mcpServers` 區 |
| 提供 | 工作流程、模板、checklist | 實際的資料呼叫 / 指標計算 |
| 互相關係 | Skill 會在適當時機呼叫 MCP 工具 | |

兩者搭配效果最好：MCP 負責拿資料，Skill 負責「拿到之後怎麼分析、怎麼輸出」。

## 已安裝的 MCP Servers (global, `~/.claude.json`)

### 1. `tradingview-ta` — atilaahmettaner/tradingview-mcp
- GitHub: https://github.com/atilaahmettaner/tradingview-mcp
- 功能：30+ 技術指標、布林帶智能判讀、K 線型態、Yahoo Finance 後備、多交易所 (Binance/KuCoin/Bybit+) 即時篩選
- 無需 API key（用公開資料）
- 啟動方式：`uvx --from tradingview-mcp-server tradingview-mcp`

### 2. `tradingview-screener` — fiale-plus/tradingview-mcp-server
- GitHub: https://github.com/fiale-plus/tradingview-mcp-server
- 功能：TradingView 公開 scanner API — 股票 / 匯市 / 加密 / ETF 篩選
- 無需 API key
- 啟動方式：`npx -y tradingview-mcp-server`

### 其他未安裝但值得留意

| Repo | 用途 | 為何沒裝 |
|------|------|---------|
| [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) | 連線本機 TradingView Desktop 做圖表截圖分析 | 需要本機跑 TradingView Desktop，環境不符 |
| [bidouilles/mcp-tradingview-server](https://github.com/bidouilles/mcp-tradingview-server) | FastMCP v2 技術指標 + OHLCV | 要 clone repo 才能跑，沒有 pypi 快速安裝 |

## 已安裝的 Skills (global, `~/.claude/skills/`)

### 1. `stock-technical-analysis`
- 路徑：`~/.claude/skills/stock-technical-analysis/SKILL.md`
- 觸發：分析 ticker、問「是否看多」、「TradingView 怎麼說」
- 內容：
  - 多週期快照（1h / 4h / 1D / 1W 建議值）
  - 指標套裝：EMA stack, MACD, ADX / RSI, Stoch / ATR, BBands / OBV
  - 關鍵 pivots + 52 週高低點
  - 固定輸出格式（TL;DR + 多週期訊號 + 多空論點 + 失效價位）
  - Guardrails：不給價位目標、標注非投資建議、資料過期就說

### 2. `pine-script-writer`
- 路徑：`~/.claude/skills/pine-script-writer/SKILL.md`
- 觸發：寫 Pine Script、`//@version=5/6`、移植指標到 TradingView、Pine 編譯錯誤 debug
- 內容：
  - 預設 Pine v6（2026 年當前版本）
  - indicator / strategy 雙模板
  - Non-repainting checklist（6 項）
  - v5 → v6 遷移提示
  - 常見編譯錯誤對照表
  - 輸出規則（完整可編譯腳本 + 3 行使用說明）

## GitHub 熱門 TradingView 資源參考

Pine Script 資源集合（未做成 skill，但 skill 寫作時有參考）：
- [pAulseperformance/awesome-pinescript](https://github.com/pAulseperformance/awesome-pinescript) — Pine 生態彙整
- [Alorse/pinescript-strategies](https://github.com/Alorse/pinescript-strategies) — 50+ 策略 + 19 指標
- [kohld/tradingview-scripts](https://github.com/kohld/tradingview-scripts) — 技術分析 + 價值投資
- [grinay/geektrade-strategies](https://github.com/grinay/geektrade-strategies) — 實戰驗證、非 repaint、可自動化

## 使用驗證

重啟 Claude Code 後：
1. `/mcp` 應顯示 `tradingview-ta` 和 `tradingview-screener` 為 connected
2. 問 "analyze NASDAQ:NVDA" → 應觸發 `stock-technical-analysis` skill
3. 問 "write a Pine v6 indicator for VWAP bands" → 應觸發 `pine-script-writer` skill

## Related Entries

- [2026-04-07 為了让AI学会交易，我搭了一个量化交易系统](./2026-04-07-ai-quant-trading-system-tutorial.md)
- [2026-04-07 最能帮助你赚钱的40个GitHub仓库](./2026-04-07-40-github-repos-to-make-money.md)（Quant trading 類別）
- [AVI V4 — 美股市場風險指標](../business/2026-04-20-avi-v4-market-risk-index.md)

## Update Log

- **2026-04-20**: 初次安裝。2 個 MCP server (`tradingview-ta`, `tradingview-screener`) + 2 個 skill (`stock-technical-analysis`, `pine-script-writer`)。

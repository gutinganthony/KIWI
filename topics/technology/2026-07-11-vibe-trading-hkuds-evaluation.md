---
title: HKUDS Vibe-Trading 評估 — 港大 LLM 量化研究工作台能為 KIWI 做什麼
url: https://github.com/HKUDS/Vibe-Trading
source: GitHub HKUDS/Vibe-Trading（程式碼靜態分析 + 背景查證）
date_added: 2026-07-11
last_updated: 2026-07-11
topic: technology
tags: [LLM-agent, quant-trading, backtesting, MCP, alpha-factors, HKUDS, evaluation, tooling]
version: 1.0
---

## Summary

香港大學 Data Intelligence Lab（HKUDS，負責人黃超）2026-04 發布的開源專案，**一句話定位：LLM 驅動的「自然語言 → 資料載入 → 策略碼生成 → 回測 → 報告」金融研究工作台**，附一個實驗性的券商連接層。不是黑盒交易機器人，也不是論文 demo——是認真做的工程產品（3 個月 19.3k★、241 個測試檔、宣稱與程式碼一致性極高），但只有 3 個月歷史、0.1.x Beta、迭代極快。

本篇基於 2026-07-11 的淺 clone（v0.1.11）靜態分析 + WebSearch/GitHub API 背景查證。核心結論：**適合借它的「資料層、因子庫、回測引擎」當工具用（掛 MCP 或 CLI），不適合用它的 LLM loop 取代 KIWI 現有分析流程，更不建議接實盤。**

## 它是什麼（程式碼證據）

- **核心流程**：自然語言 prompt → ReAct agent loop（LangChain/LangGraph）→ LLM 產出 `config.json` + `signal_engine.py` → 白名單驗證後 subprocess 跑確定性回測引擎 → 產出 metrics/報告（HTML/PDF）/TradingView Pine 匯出。策略碼是 LLM 寫的，回測本身是傳統程式碼，不是 LLM 幻想數字。
- **三個入口**：`vibe-trading`（互動 TUI）、`vibe-trading serve`（Web UI）、`vibe-trading-mcp`（MCP server，54 tools）。
- **市場覆蓋**：9 個回測引擎（A股/美股/港股/印度/crypto/中國期貨/全球期貨/外匯/選擇權 + 跨市場 composite）；20 個 data loader 按封鎖風險排 fallback（美股：yahoo→stooq→sina→eastmoney→yfinance→…）；**市場資料零 API key 可跑**。
- **Alpha Zoo：460 個預建因子**（Qlib158 + Kakushadze Alpha101 + 國泰君安 GTJA191 + 學術因子），`vibe-trading alpha bench` 一行對整個因子庫做 IC 測試。
- **86 個金融 skill**：SKILL.md + frontmatter 格式，**與 KIWI 的 skills/ 結構同構**（含纏論、艾略特波浪、SMC 等）。
- **30 個 swarm preset**：multi-agent DAG（如 investment_committee 多空辯論），跑之前先抓真實 OHLCV 塞進 worker prompt 防幻覺（grounding.py）。
- **券商層**：11 家 connector（IBKR/Alpaca/Futu/OKX/Binance/老虎/長橋…）是真程式碼；paper trading 直下券商 sandbox；實盤有 mandate（標的域/單量/曝險/日限）+ 檔案系統 kill switch + fail-closed order guard + audit ledger。**但 README 自認「experimental、未對真實券商帳戶驗證、風險自負」**。

## 背景與同類位置

- HKUDS 特徵：出貨極快（LightRAG 37.6k★、nanobot 45k★），旗艦有長期維護紀錄,但同賽道自家雙專案並存（姊妹作 AI-Trader = 全自動下單路線，有 arXiv:2512.10971；Vibe-Trading = 人主導研究工作台，**本身無論文**）。
- 同類比較：TradingAgents（92k★，多 agent 辯論框架）與 ai-hedge-fund（61k★，教育用 PoC）先發且社群大，但 **Vibe-Trading 是「工程產品化」最徹底的**——MCP 原生、因子庫、多市場資料 fallback、券商連接。A 股特色數據（龍虎榜、北向資金、融資融券）最全。
- **查無任何獨立用戶回報真金白銀交易績效**。業界綜述共識：沒有一個此類框架是印鈔機。LLM 回測的 look-ahead/資訊洩漏是整個領域的系統性問題（arXiv:2510.07920 "Profit Mirage"）。

## 跑起來的門檻

- Python ≥3.11，`pip install vibe-trading-ai`，**只需一個 LLM API key**（預設 DeepSeek；或本地 Ollama 免 key）。
- **無原生 Anthropic provider**——16 家 provider 沒有 anthropic，要用 Claude 只能繞 OpenRouter。
- PDF 報告需系統層 weasyprint 依賴（pango/cairo）；Web UI 另需 Node 20。
- Token 成本無官方估計（每 run 存 llm_usage.json 但不估價）；swarm 上限設計不小（4 worker × 50 iter）。

## 對 KIWI 的用途（按摩擦由低到高）

1. **當資料/回測工具用（最低摩擦，推薦起點）**：`vibe-trading-mcp` 掛進 Claude 生態，借它 20 源 fallback 的行情資料層 + read-only 分析工具，不碰它的 LLM loop。或直接 CLI 跑回測——KIWI 的 Serenity/WaveTrend 訊號想做歷史回測時，不用自己再造引擎。
2. **Alpha Zoo 當因子超市**：拿 Serenity watchlist 當 universe 跑 `alpha bench`，看 460 個因子哪些在自己的股票池有 IC——為 WaveTrend 之外的技術/量價因子提供現成候選清單。
3. **Swarm preset 當第二意見機**：investment_committee（多空辯論）對 Serenity 結論做對抗檢驗，呼應 KIWI「高風險判斷需第二意見」的守則——但要自備 LLM key，且輸出品質未驗證。
4. **架構借鑑（不裝也有價值）**：它的 grounding 防幻覺（先抓真實價格再讓 agent 說話）、fail-closed order guard、mandate 到期自動失效——都是 KIWI 未來若做自動化決策時值得抄的安全模式。
5. **不建議**：接實盤（官方自認未驗證）、用它取代 Serenity 流程（KIWI 的價值在自己的判斷框架，不在生成通用策略）。

## 風險備忘

- 0.1.x Beta，兩個月內大改三次（CLI 重構、LangChain 1.x 遷移、EnvConfig 集中化），跟進成本高；建議 pin 版本、當工具用不深度耦合。
- README 內嵌 QVeris 付費資料市場 referral link（有揭露，但注意商業動機）。
- coverage 門檻 = 0（測試多但不設覆蓋率底線）。
- 實驗室多線作戰（AI-Trader 同賽道並存），長期維護是最大問號。

## 詳細分析檔案

本篇是彙整版。逐項證據（檔案:行號）見 session 產出的兩份完整報告（scratchpad，未入版控）：程式碼分析涵蓋 57 tools/460 因子逐一點數、風控層程式碼位置；背景調查含全部來源 URL 與同類專案即時 star 對照。

## Update Log

- 2026-07-11 v1.0：建檔。基於 v0.1.11（HEAD d456025）靜態分析 + 背景查證，未實際安裝執行。

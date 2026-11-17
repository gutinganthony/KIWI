# TradingAgents（雲端隨叫隨跑）

原版 [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)（Apache-2.0），釘在 commit `c454491`（2026-10-27），透過 GitHub Actions 執行。

## 怎麼跑（手機或電腦都行）
GitHub → Actions →「TradingAgents (on-demand multi-agent analysis)」→ Run workflow → 填代號 → Run。
- 美股：`BE`；台股上市：`2303.TW`；上櫃：`8271.TWO`
- 預估 5–15 分鐘（尚未實測）。結果在 `reports/<代號>/<日期>/complete_report.md`（另有 `.html` 單頁版），run 頁面的 Summary 會顯示評級。

## 產出
五級評級 Buy / Overweight / Hold / Underweight / Sell（解析失敗為 REVIEW）＋分析師報告、多空辯論、交易員提案、風控辯論、投資組合經理決策。
`memory/trading_memory.md` 是決策日誌：持有期（5 個交易日）過後，下次執行會自動結算實際報酬與相對大盤 alpha（台股對 ^TWII、美股對 SPY），寫反思並帶進之後的決策。

## 限制（使用前先知道）
- **非投資建議**；評級不受 `skills/serenity/exit-playbook.md` 約束，機械出場規則優先。
- 台股資料只有 Yahoo：財報薄、新聞以英文為主，基本面與新聞分析師對台股中小型股參考價值低。
- LLM 看過訓練截止日以前的行情，**對過去日期跑出的結果有偷看答案的偏差**；只有往後的紀錄才算數。
- **repo 是公開的**：報告與決策日誌任何人都看得到。目前沒有把持倉餵給它（`--portfolio`）。
- 費用走 repo secret `ANTHROPIC_API_KEY`（與 Serenity 週報共用），每次執行按用量計費。
- 選用 secret `SEC_EDGAR_USER_AGENT`（格式：`姓名 email`）：沒設也能跑（套件用佔位地址），SEC 建議填自己的聯絡方式。

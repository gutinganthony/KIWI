# Reprice — 重定價（watchlist / 週報 / 任意 ticker）

用途：把任意 ticker 的現價拉回來，供 watchlist 更新、週報重定價、臨時查價。
取代舊慣例「用 WebSearch snippet 當價格」——snippet 只准當交叉驗證，不當主來源。

## 指令

```bash
python3 projects/avi-v5/scripts/quote.py AAPL 6758.T 2330.TW        # 表格
python3 projects/avi-v5/scripts/quote.py --json AAPL 6758.T         # JSON（給 agent 用）
```

多源自動 fallback：Yahoo（免 key）→ stooq（免 key）→ FinMind（台股）→ Alpha Vantage
（需 `ALPHAVANTAGE_API_KEY`，選配）。台股（.TW/.TWO/純數字代碼）自動改走台股鏈。

## 執行分流（按當下環境選，寫報告時標明用了哪條）

1. **雲端 session**：先測連通 `curl -sS -m 5 "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d" | head -c 100`。
   - 通 → 直接跑 quote.py。
   - 403（CONNECT tunnel failed）→ 環境白名單未開通，走 2 或 3，並提醒使用者：
     在 claude.ai/code 的 environment 網路設定加上
     `query1.finance.yahoo.com`、`stooq.com`、`api.finmindtrade.com`、`www.alphavantage.co`。
2. **GitHub Actions**：runner 網路暢通，quote.py 可直接跑（FinMind 已在管線中證實可用）。
3. **Mac 本機**：直接跑。若雲端拿不到價又急用，把「跑 quote.py + 回報結果」
   append 進 topics/technology/mac-manual-homework.md 待辦區。

## 產出規範（配合 agents/JUDGMENT.md §5：數字必附來源）

- 每個價格標註：`價格（來源:yahoo/stooq/finmind，日期）`。
- 某檔全部來源失敗 → 寫「查無（各源錯誤: ...）」，禁止用記憶或 snippet 補值。
- 更新 watchlist.md 時：只改價格與日期欄，不動觸發/否證條件（那是使用者的判斷，保真第一）。

## 狀態

- 2026-07-08 建立。腳本已語法驗證；**網路路徑尚未實跑驗證**（雲端 proxy 全擋，
  已列入 mac-manual-homework 待辦）。Mac 驗證通過後把本行改為「已驗證（日期）」。

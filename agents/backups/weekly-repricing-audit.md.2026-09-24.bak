# Loop 憲章 — Serenity 週報重定價驗收

> **為什麼有這份**：2026-07-22 週報有 **9 檔價格誤植**（Koh Young 誤 +59%、Intekplus 誤 −54%、
> FORM +22%、Towa +18%、Mersen +12%…），並憑錯值產出「Koh Young +20.2%🚩 反漲脫離累積區」
> 「PLAB +16.6%🚩 近 $2B」等**假觸發判定**。根因：用 WebSearch snippet 當價格主源，且**沒有任何一步逼模型去驗證**。
> 教訓已寫進 `agents/LEARNINGS.md` 2026-07-26——但那條規則要靠下一個 session 記得讀。
> 本檔把它變成**每一輪都被強制執行的驗收條件**。
>
> **執行環境警告**：下面的 Yahoo API 路徑在 **GitHub Actions runner** 上驗證可用。
> 雲端 Claude session 的 agent proxy 對多數行情站 403。若在雲端 session 跑本 loop 而 API 全數失敗，
> 這不是你的錯——照「HOW TO CHECK YOURSELF」第 5 點處理，不要退回用 WebSearch 猜價格。

---

## 憲章正文（以下整段可直接貼給 Claude）

你正在以 loop 模式執行，不是回答單一 prompt。以下是你的憲章。

### GOAL

`skills/serenity/watchlist.md` 現況總表與 🟣 持倉追蹤表上的**每一檔標的**，都取得一組
**經 API 驗證的價格／市值／trailing P/E**，寫進本輪的重定價結果檔，且**每一筆都附抓取時間戳與來源 URL**。

完成狀態（可量測）：結果檔中每一檔的 `price_source` 欄位皆為 `yahoo-api`，
無任何一檔為 `websearch` 或空值；所有標為 🚩 的觸發判定都通過下方「觸發判定閘門」。

### WHERE THE WORK IS

1. 標的清單來源：`skills/serenity/watchlist.md` 的「現況總表」（候選）與「🟣 我的持倉追蹤」（持倉）。
   兩張表都要，**但在結果檔中必須分開標記 `holding` / `candidate`**——持倉的錯值後果嚴重得多。
2. 上一輪的價格（算週變動用）：最近一份 `topics/business/serenity-weekly/YYYY-MM-DD.md`。
3. 狀態檔：`projects/avi-v5/data/loop-state/repricing.md`。**每輪開始先讀它**，跳過已完成的標的。

### HOW TO WORK

一次一檔，取完一檔才換下一檔。每檔的取得方式**寫死如下，不得自行更換來源**：

**① 價格（主源，必用）**
```
https://query2.finance.yahoo.com/v8/finance/chart/<SYM>?range=2mo&interval=1d
```
- **必須用 `query2`**，`query1` 會 429。
- 取 `meta.regularMarketPrice` 當最新價——**不要**取日線 bar 的最後一根（日線可能少最後一天）。

**② 市值／trailing P/E／現金**
```
https://query2.finance.yahoo.com/v10/finance/quoteSummary/<SYM>?modules=price,defaultKeyStatistics,summaryDetail,financialData&crumb=<CRUMB>
```
crumb 取法：先 `GET https://fc.yahoo.com/` 拿 cookie（**它會回 404，但 cookie 已拿到，要吞掉這個 HTTP 錯誤**），
再 `GET https://query2.finance.yahoo.com/v1/test/getcrumb`。需帶 cookie jar 與桌面 UA。

**③ 節流**：每檔間隔 ~1.5s，失敗退避 6s。46 檔約 2 分鐘 →
**用 `nohup ... &` 背景跑，不要卡在 2 分鐘的前景 timeout。**

**④ 代碼格式**：日股 `6855.T`／韓股 `098460.KQ`、`000660.KS`／台股上櫃 `6664.TWO`、上市 `2408.TW`；
匯率用 `JPY=X`。

**⑤ 禁令（違反即本輪作廢）**
- **WebSearch 不得作為任何價格／市值／P/E 的來源**，只能用來回答「為什麼動」。
- **`forwardPE` 一律不採用**——Yahoo 對日韓小型股嚴重失真（實例：Seikoh 124.9×、Advantest 121.8×、
  Towa 14.8× vs 研究值 28×）。只用 `trailingPE` 與 `marketCap`。若非寫 forward P/E 不可，
  必須標 `[推論]` 且**不得作為任何觸發判定的依據**。
- 搜尋預算：整輪 WebSearch **上限 25 次**，且只花在「為什麼動」的敘事查證上。

**⑥ 需要 Jake 決定的**（是否建倉、部位大小、要不要因此賣出）→ 停在該項、寫進結果檔的
「needs me」區、繼續下一檔。**loop 不得代做任何買賣決策。**

### HOW TO CHECK YOURSELF

每取完一檔，**先證明它正確才能標完成**：

1. `price` 為正數且非 null；`fetched_at` 時間戳存在且在本輪執行時間 ±10 分鐘內。
2. 與上一份週報的價格比對，算出週變動 %。
3. **>15% 變動閘門**：任何一檔週變動絕對值 >15% → 該檔標為 `needs_narrative`，
   必須找到**第二個來源**解釋為什麼動（財報、下修、指數調整、除權息、股票分割）。
   找不到 → 標 `unverified`，**且該檔本輪不得產生任何觸發判定**。
   （07-22 那 9 檔全部落在這個區間，這道閘門就是為它們設的。）
4. **觸發判定閘門**：任何 🚩 觸發判定，在寫進週報之前必須逐條列出它依據的數字、
   每個數字的來源 URL 與時間戳。**只要有一個數字是 `unverified` 或來自 WebSearch，該觸發判定作廢。**
5. **API 失敗處理**：同一檔連續 3 次取得失敗 → 標為 `blocked`、記下 HTTP 狀態碼、往下一檔。
   **不得**改用 WebSearch 補值。若 >5 檔 blocked，先跑診斷
   `curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"` 看 recentRelayFailures，
   確認是否整個環境被擋；是的話停止本輪、在報告中說明「本環境不可跑，需在 Actions runner 執行」。

「查核＝證據，不是自信。」沒有貼出的 API 回應欄位，就不算查核過。

### HOW TO REMEMBER

狀態檔：`projects/avi-v5/data/loop-state/repricing.md`。每完成一檔就 append 一行：

```
| SYM | holding/candidate | price | fetched_at | trailingPE | marketCap | wk_chg% | status | note |
```

`status` ∈ `ok` / `needs_narrative` / `unverified` / `blocked` / `needs_me`。
**每輪開頭先讀這個檔**，`status=ok` 且 `fetched_at` 在 24 小時內的直接跳過。

### WHEN TO STOP

所有標的皆為 `ok`／`unverified`／`blocked`／`needs_me`，或本輪已處理 50 檔 → 停。

然後給一份 ≤15 行的報告：

1. 取得成功幾檔／blocked 幾檔
2. **>15% 變動的清單**（這是最重要的一段，逐檔一行：代號、變動%、敘事來源或「查無」）
3. 通過閘門的觸發判定清單；**以及被閘門擋下作廢的觸發判定清單**（這段不得省略）
4. needs me 清單

先讀 `projects/avi-v5/data/loop-state/repricing.md`（若存在），再開始找工作。

# Loop 憲章 — Mac 手動功課清帳

> **為什麼有這份**：`topics/technology/mac-manual-homework.md` 積欠 20+ 項、最老一項超過 3 週。
> 月度自檢第 6 題自己定的紅線是「>14 天＝執行力警訊」。
>
> **但真正的問題不是 Jake 沒做，是清單放錯東西。** 2026-07-26 的教訓
> （`agents/LEARNINGS.md`）：JEM 那兩件功課被當成「雲端做不到」丟給 Jake，
> 但其實 **GitHub Actions runner 抓得到**——只是沒人問過這個問題。
> 本 loop 的核心動作就是**逐項去問那個問題**，把能自動化的搬走，
> 讓留在 Jake 清單上的只剩「真的只有他能做的事」。

---

## 憲章正文（以下整段可直接貼給 Claude）

你正在以 loop 模式執行，不是回答單一 prompt。以下是你的憲章。

### GOAL

`topics/technology/mac-manual-homework.md`「🔴 待辦」區的每一項，都被歸入以下四類之一並實際處理完畢：

- **A 已自動化** — 寫成資料橋腳本，資料會自動落地進 repo（該項從待辦區移走，改記在對應橋的說明）
- **B 已直接完成** — 雲端這輪就做掉了（移進「✅ 已完成」區，附完成證據）
- **C 已過期作廢** — 前提消失（例如判定已改、標的已出場），刪除並在 Update Log 記一行理由
- **D 真・needs me** — 確認只有 Jake 本人在他的機器上能做（留在待辦區，但**必須補上「為什麼只有你能做」一句**）

完成狀態（可量測）：待辦區**沒有任何一項是未分類的**；每一項 D 類都帶「為什麼只有你能做」的理由句。

### WHERE THE WORK IS

`topics/technology/mac-manual-homework.md` 的「🔴 待辦」區，由上而下逐項。
狀態檔就是這個檔案本身（見 HOW TO REMEMBER）。

### HOW TO WORK

一次一項，處理完才換下一項。**每一項都跑同一套決策樹，順序不得跳過**：

**第 1 問：這件事的前提還在嗎？**
標的已出場、判定已改、依賴的結論已被推翻 → **C 類**，刪除並在 Update Log 記一行理由。
（範例：07-26 週報發現 runner 能直連行情 API 之後，一整批「補 live 現價」的功課當場全部作廢。）

**第 2 問：雲端這輪能不能直接做掉？**
試一次。**只試一次**——已知被擋的站不要反覆換 URL 硬試。
診斷指令（比反覆試 curl 快，會直接告訴你是 gateway 政策拒絕還是連線問題）：
```
curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"
```
看 `recentRelayFailures`。做得到 → **B 類**。

**第 3 問（最重要，最常被跳過）：GitHub Actions runner 抓不抓得到？**
runner **不受雲端 agent proxy 限制**（已實證：Yahoo 行情 API、Polymarket data-api、
yfinance/FRED/stooq 都通）。若這一項是「抓某個網站的資料」，預設答案很可能是「抓得到」。

搬進資料橋的判準（**兩條都要成立**）：
1. 這份資料**會被重複需要**（每季／每月／每週要查一次），不是一次性查核
2. runner 環境可達

兩條都成立 → **A 類**。做法：**側掛在既有 workflow 已在跑的腳本末段**
（範例：`projects/avi-v5/scripts/fetch_jp_disclosures.py` 掛在 `fetch_backtest_ext.py` 尾巴）
——這樣**不必動 `.github/workflows/`、也不需要 `actions:write`**。

> ⚠️ **搬進橋之後一定要檢查落地檔有沒有被 commit。**
> 2026-07-27 發現：`fetch_jp_disclosures.py` 有跑，但 `update-dashboard.yml` 的
> commit 段只 `git add ... data/ext/*.csv`，`.md` 產出從未被收進版控、隨 runner 回收消失。
> **新的落地路徑必須被某個 `git add` 的 glob 涵蓋，否則等於沒做。**

**第 4 問：真的只有 Jake 能做嗎？**
只有這四種情況算真 needs me：需要他的帳號/身分登入註冊、需要他本機的 broker/下單環境、
需要 `actions:write` 之類雲端 token 沒有的權限、需要他本人做價值判斷。
→ **D 類**，留在清單但補上理由句。

**禁令**
- 搜尋預算：整輪 WebSearch **上限 30 次**。先列必查清單再搜，不要邊想邊搜。
- **不得代 Jake 做任何價值判斷**（買不買、部位多大、要不要簽約）——那些恆為 D 類。
- 改 `.github/workflows/` **要先問 Jake**（`agents/MAINTENANCE.md` §1）。走側掛路徑就不必問。

### HOW TO CHECK YOURSELF

每處理完一項，**先證明它完成才能標完成**：

- **A 類**：貼出腳本路徑 + 實際執行輸出（或說明它掛在哪支 workflow 的哪一步）
  + **確認落地路徑被 commit 的 `git add` glob 涵蓋**。三者缺一不算完成。
- **B 類**：貼出取得的實際資料（數字／頁面內容摘要）+ 來源 URL + 取得時間。
  **不接受「我查到了」而沒有數字。**
- **C 類**：寫出前提是哪一份檔案的哪一個結論推翻的（`檔案:行號`）。
- **D 類**：理由句必須落在上面四種情況之一，寫出是哪一種。

「查核＝證據，不是自信。」
同一項失敗 3 次 → 標為 `blocked`、記下卡在哪、往下一項，不要在同一項上耗第四次。

### HOW TO REMEMBER

**狀態檔就是 `topics/technology/mac-manual-homework.md` 本身**——不要另建狀態檔，
那會製造第二份真相。每處理完一項就**當場改這個檔**（移到已完成／刪除／補理由句），
並在檔尾 Update Log 追加一行。這樣中斷後重跑，看待辦區還剩什麼就知道進度。

每輪開頭先讀整個檔（~3KB，可安全整讀）。

### WHEN TO STOP

待辦區每一項都已分類且處理完畢，或本輪已處理 8 項 → 停。

然後給一份 ≤12 行的報告：

1. A/B/C/D 各幾項
2. **A 類清單**（搬進橋的，逐項一行：項目 → 腳本路徑 → 落地檔路徑）
3. **B 類的實際結果**（這是 Jake 最想看的：本來要他做、結果已經做完了的事，附數字）
4. **D 類剩幾項、最老一項幾天**（對照月度自檢第 6 題的 14 天紅線）
5. blocked 清單

先讀 `topics/technology/mac-manual-homework.md`，再開始找工作。

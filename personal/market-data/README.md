# 摸魚記市場數據管線

## 怎麼運作

GitHub Actions（`.github/workflows/market-data.yml`）每個交易日台股收盤後
（06:30 UTC = 14:30 台北）自動執行，也可在 GitHub Actions 頁面手動觸發
（Run workflow）。結果 commit 到：

- `today.json`：最新快照
- `history.jsonl`：逐日累積

Claude 在任何 session 直接 `Read personal/market-data/today.json` 即可拿到數據，
不受 session 容器的網路白名單限制。

## 自動化狀態（2026-06-12）

| 數據 | 狀態 | 來源 |
|------|------|------|
| 加權指數收盤 | ✅ 全自動 | TWSE OpenAPI（FMTQIK）|
| 自高點回檔 % | ✅ 全自動 | 計算（ATH 錨 46,552，創新高時改 fetch.py 的 `ATH`）|
| 三大法人/外資買賣超 | ✅ 全自動 | TWSE rwd API（BFI82U）|
| VIXTWN | ❌ 需手動 | 期交所 MIS 反爬 + 玩股網 Cloudflare，瀏覽器也擋 |
| 大盤融資維持率 | ❌ 需手動 | 同上（MacroMicro 需登入）|

## VIXTWN / 維持率的手動補法

寫文章前 30 秒搞定：手機看一眼這兩個網站，把數字告訴 Claude：

- VIXTWN：https://www.wantgoo.com/index/vixtwn
- 維持率：https://www.macromicro.me/charts/53117/taiwan-taiex-maintenance-margin

或在本機跑 `python personal/market-data/update.py`（會互動式問你這兩個值，
其他自動抓），然後 commit。

## Session 內查證來源地圖（2026-10-07 白名單更新後）

雲端 session 的網路白名單是**逐字比對網址**：`who.int` 不含 `www.who.int`，要用 `*.who.int` 才涵蓋子網域。白名單改完約一分鐘內生效，不用開新 session。

**讀網頁**：用 `curl` 下載（帶瀏覽器 User-Agent）再轉文字。內建 WebFetch 在 2026-10-07 白名單更新後仍顯示被擋，不要等它。

| 用途 | 用這個 | 備註 |
|---|---|---|
| 美股個股收盤價 | FinMind `USStockPrice` | 2026-10-07 起取代 Yahoo Finance；與 Yahoo 報導比對一致 |
| 台股、美債殖利率 | FinMind `TaiwanStockPrice`、`GovernmentBondsYield` | 免 token，偶爾 402 要重試 |
| 台積電除息、營收、法說 | 公開資訊觀測站、證交所除權除息預告表（TWT48U） | 台積電 IR 網站擋程式連線，改用這兩個官方來源 |
| FOMC 行事曆 | federalreserve.gov | 可讀 |
| 國際機構 | who.int、news.un.org、ecdc.europa.eu | 可讀 |
| 美光**已發生**的財報日 | SEC `data.sec.gov/submissions/CIK0000723125.json` | 8-K 的 Item 2.02 申報日＝財報發佈日（例：2026-09-30、2026-06-24） |
| 美光**未來**財報日 | **請 Jake 截圖或存 PDF** | 預告新聞稿只在美光 IR 網站，該站擋程式連線 |
| 美國 CPI 數據 | BLS API `api.bls.gov/publicAPI/v1/` | 可讀；BLS 發佈時程網頁被擋 |

**白名單也解決不了的（網站自己擋程式連線）**：美光 IR、台積電 IR、CNBC、Benzinga、SEC 網頁與申報文件全文（`www.sec.gov`）、BLS 網頁（`www.bls.gov`）。Yahoo Finance 的資料介面會限流。SEC 申報文件全文若要讀，SEC 要求程式連線附上聯絡用 email，由 Jake 決定用哪個信箱。

## 除錯

每次 run 的 log 都有各端點的成功/失敗診斷（含失敗回應的開頭內容）。
要再嘗試自動化 VIXTWN，方向是：期交所 MIS 頁面的 websocket 來源、
或 TAIFEX 每日盤後 CSV（`vixMinNew` 頁的下載按鈕背後的 POST 端點）。

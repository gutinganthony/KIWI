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

## 除錯

每次 run 的 log 都有各端點的成功/失敗診斷（含失敗回應的開頭內容）。
要再嘗試自動化 VIXTWN，方向是：期交所 MIS 頁面的 websocket 來源、
或 TAIFEX 每日盤後 CSV（`vixMinNew` 頁的下載按鈕背後的 POST 端點）。

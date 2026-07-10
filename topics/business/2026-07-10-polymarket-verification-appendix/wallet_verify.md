# Polymarket 錢包戰績核實：0x25e28169faea17421fcd4cc361f6436d1e449a09

- 核實日期：2026-07-10（所有資料取得時間 06:56–07:10 UTC）
- 待驗聲稱來源：X 文章 2026-06-04 @waveking1314（90% 勝率／月 PnL >$50k／只做 CS:GO+LoL／~20 筆／餘額翻倍），引用 6/3 推文「30 天 $245→$89,000」

## 0. 資料取得方式與限制（重要前提）

本環境 egress 政策封鎖了所有直接資料源，**只有 WebSearch（搜尋索引快照）可用**：

- `curl https://data-api.polymarket.com/...` → `curl: (56) CONNECT tunnel failed, response 403`
  - 代理狀態原文：`"kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)", "host": "data-api.polymarket.com:443"`（2026-07-10T06:56 UTC）
- 同樣被擋（curl 回 000/CONNECT 403）：polymarket.com、gamma-api、clob、lb-api、etherscan.io、polygonscan.com、polymarketanalytics.com、predictfolio.com、lines.com、layerhub.xyz、hashdive.com、polymarketwhales.info
- WebFetch 本 session 整體失效：連 `https://example.com/` 都回 `The server returned HTTP 403 Forbidden`（政策級封鎖，非目標站拒絕）
- 結論：以下所有數字皆來自 Google 索引快照與媒體報導，**非即時 API 原始資料**；快照爬取日期未知（估計為近期）。精確數字需在 Mac 本機重跑 data-api（建議列入 mac-manual-homework 待辦）。

## 1. 錢包身分（高信心）

錢包 = Polymarket 用戶 **@xdd07070**，2025 年 10 月加入。三個獨立來源交叉印證：

1. lines.com 鯨魚檔案將該錢包與 xdd07070 關聯 — https://www.lines.com/whales/profile/xdd07070
2. X 用戶 @gabriel_zeras 的推文（經 sotwe.com 鏡像被索引）直接列出完整地址 0x25e28169faea17421fcd4cc361f6436d1e449a09 = xdd07070，描述為「電競專家，擅長 LoL/CS2/Valorant，歷史獲利 13 萬」— https://www.sotwe.com/gabriel_zeras
3. WebSearch 對 `"0x25e28169" polymarket xdd07070` 的內容摘要直接確認關聯

## 2. 成名戰績（2026 年 1 月中～2 月 16 日，媒體核實過）

| 項目 | 數字 | 來源 |
|---|---|---|
| 起始本金 | **$170**（非 $245） | esports.net、finbold |
| 一個月獲利 | **$118,748.16**（至 2/16；2/19 增至 $122,259） | esports.net、Tengen 推文 |
| 交易筆數 | 40 筆（2/19 為 41 筆），僅 4 筆錯 → **90% 勝率**（36/40） | finbold（另一處寫 80%） |
| 標的 | 電競：CS、LoL、**外加 Valorant**（非只有 CS:GO+LoL） | esports.net、finbold |
| 最大單筆贏 | $35,351 押 FaZe 勝 BC.Game（IEM Krakow），賺 $17,490 | esports.net |
| 手法 | 挑重favorite，70–85¢ 買入 $30k–50k 鎖 20–40% 收益 | Tengen 推文 |

來源 URL（皆 2026-07-10 取得）：
- https://www.esports.net/news/polymarket-user-generates-118000-in-a-month-of-esports-wagers/
- https://finbold.com/crypto-trader-turns-170-into-118000-in-a-month-betting-on-esports/
- https://x.com/0xTengen_/status/2024580594643157249（snowflake ID 解碼 = **2026-02-19T20:23 UTC**，證明成名時點是 2 月，不是 6 月）

## 3. 之後的崩盤（lines.com 鯨魚追蹤，涵蓋大額單）

lines.com/whales/profile/xdd07070 快照（2026-07-10 經搜尋索引取得）：

- 追蹤到 10 筆鯨魚級交易、8 個市場、總量 **$498.9k**、平均單筆 **$49.9k**、最大 $67.5k
- 已結算 **2 勝 6 敗（勝率 25.0%）**、已實現 PnL **−$311.4k**、ROI **−76.9%**
- 「0 and 8 on sports markets in 2026」（2026 年運動/電競盤 0 勝 8 敗）
- 最後一筆鯨魚單：**$33.4k 押 THEMONGOLZ @ ~100¢，約 3 個月前**（以爬取時點推算 ≈ 2026 年 4 月）
- 注意：此站只追蹤大額單，小額交易不計入；−$311.4k 不等於終身 PnL，但量級足以吞掉 2 月的 +$118k~130k 獲利

## 4. 錢包現況（2026-07-10 可得的最佳快照）

- Polymarket 官方個人頁（Google 索引快照）：**目前持倉價值 $0.00**、終身 81 筆預測、最大贏 $62.2K、87.9K 次瀏覽、2025/10 加入 — https://polymarket.com/@xdd07070
- 鏈上餘額（layerhub/etherscan 快照）：EOA 總值 **~$1,883.65**（USDC 83.8% + USDC.e 16.2%）— https://etherscan.io/address/0x25e28169faEa17421FCD4cC361F6436D1e449a09
- 終身淨 PnL 估算：2 月高點 +$118k~130k，之後鯨魚單已實現 −$311.4k → **極可能終身淨虧損（量級約 −$18 萬或更差）**；精確值無法取得（API 被擋）
- 最後可證交易：≈2026 年 4 月（$33.4k MONGOLZ 單）。**6/4 文章發表後無任何可證活動**；持倉歸零 + 錢包只剩 ~$1.9k
- 市場類別分布：可證交易幾乎全為電競（CS2/LoL/Valorant）；81 筆中 2 月佔 ~41 筆、鯨魚單 10 筆，其餘 ~30 筆小額單無法取得明細

## 5. 逐條判定

| 聲稱 | 判定 | 依據 |
|---|---|---|
| 90% 勝率 | **部分證實但過期**：1–2 月那波確為 36/40=90%（另有 80% 說法）；但 2026 年鯨魚單 2勝6敗（25%）、運動盤 0-8 | esports.net、finbold、lines.com |
| 一個月 PnL >$50k | **證實（僅限 1 月中–2/16 那一個月，+$118k）**；當作 6 月現況則屬誤導——4 月前後已實現 −$311.4k | 同上 |
| 只做 CS:GO+LoL | **大致證實**（電競專門戶），但實為 CS+LoL+**Valorant** 三項 | esports.net、finbold |
| 交易不多（發現時 ~20 筆） | **無法精確驗證**；媒體核實時點為 40–41 筆/月，終身 81 筆。「~20 筆」可能是 2 月上旬中途快照，也可能是誤傳 | finbold、polymarket.com 快照 |
| 30 天 $245→$89,000 | **證偽（照字面）**：媒體核實數字是 $170→$118,748（1 月中–2/16）。$245 與 $89k 不見於任何可查來源；且 6/3 前 30 天（5 月）該錢包鯨魚單全敗，不可能有這種跑分 | esports.net、finbold、lines.com |
| 把餘額翻倍 | **證偽/不自洽**：$245→$89k 是 363 倍不是翻倍；「PnL>$50k=翻倍」暗示本金 ~$50k，又與 $245 起步矛盾 | 內部邏輯 |

## 6. 兩個內部矛盾的檢查

(a) **「$245→$89k」vs「PnL>$50k、~20 筆、翻倍」**：兩組數字互不相容，也都不符媒體核實的 $170→$118,748/40 筆。最合理解釋：兩者都是 **2026 年 2 月同一個故事在轉發鏈中變形的版本**，waveking1314 於 6/4 當新聞轉賣。90% 勝率與 36/40 吻合這一點反而佐證素材源頭就是 2 月的報導。

(b) **6/4 發表後表現**：發表時該錢包早已崩盤（≈4 月最後一筆鯨魚單、2026 運動盤 0-8、已實現 −$311.4k）。6/4 之後**零可證活動**，持倉 $0.00，錢包餘額 ~$1.9k。跟單者若 6/4 才進場，跟的是一個已停止交易且淨虧損的帳戶。

## 7. 總結論

**文章嚴重誇大且時效造假**：它把 2 月中就結束的一波真實好戰績（$170→$118k，90% 勝率，媒體有報導）在 6/4 包裝成「現在進行式」，數字經轉發變形（$245/$89k/翻倍 皆對不上任何來源），並完全隱瞞了 3–4 月間該錢包以平均 $50k 的單量 2勝6敗、已實現虧損 $311k、餘額只剩 ~$1.9k 的事實。

## 8. 未檢查範圍

- Polymarket data-api / lb-api 原始 JSON（egress 403 全擋）→ 精確終身 PnL、逐筆 activity、確切最後交易時間戳未取得
- waveking1314 6/4 原文與 6/3 被引推文全文（X 不可達，僅依任務描述）
- lines.com 未涵蓋的 ~30 筆小額交易明細；各快照的確切爬取日期
- polymarketanalytics/predictfolio 的錢包頁（站點被擋，搜尋索引無該錢包頁快照）

## 9. Mac 手動功課候選（雲端做不到）

- 本機 `curl "https://data-api.polymarket.com/positions?user=0x25e28169..."`、`/activity?limit=500`、`/value` 取精確數字複核本報告（本 session egress 403：data-api.polymarket.com、polymarket.com、etherscan.io、lines.com 等全被擋；WebFetch 整體 403）

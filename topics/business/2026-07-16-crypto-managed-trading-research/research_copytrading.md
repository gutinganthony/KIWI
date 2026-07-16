# Copy Trading 帶單交易員研究：Binance / OKX / Bybit / Bitget

查詢日期：2026-07-16
研究者環境限制：雲端 proxy 封鎖 binance.com、bybit.com（含 bybit.global、help.bybit.com）、bitget.com（含 bitgetapp.com、bitget.site）之 HTTPS CONNECT（403）。**只有 OKX 官方頁直接核對成功**（okx.com 可直連，抓取繁中全球版）。Binance/Bybit/Bitget 各項均來自 WebSearch 對官方 help center 頁面的摘要，一律標註「未直接核對官方頁」。

## 證據等級標記

- ✅ 直接核對：本 session 用 curl 抓取官方頁原文
- 🔶 WebSearch 摘要：來源 URL 是官方 help center，但內容經搜尋引擎摘要轉述，未直接核對官方頁
- ⚪ 推論：由事實推出，無直接來源
- ❌ 查無

---

## 一、OKX（唯一全部直接核對官方頁的一家）

### ① 帶單資格
- 申請流程：提交個人資訊（聯繫方式、社交媒體帳號、個人簡介），平台審核約 3 天。✅
  來源：https://www.okx.com/zh-hant/help/11639154398221 （文章更新 2026-07-08，查詢 2026-07-16）
- 審核條件（合約/現貨帶單）：完成身份驗證（KYC）＋停止目前跟單＋指定帳戶模式（合約：合約帳戶或進階跨幣種保證金模式；現貨：現貨或合約帳戶模式）。✅ 同上來源。
- 策略（bot）帶單另有門檻：近 30 天在 OKX 策略交易投資超過 1,000 USDT＋近 30 天創建/運行 5 個以上策略。✅
  來源：https://www.okx.com/zh-hant/help/spot-copy-trading-product-cheatsheet-for-lead-trader （更新 2026-05-29，查詢 2026-07-16）
- 帳號必須本人實名：官方明列「帶單賬號不實名、借用其他人的 KYC 賬號」屬不受歡迎行為，可取消帶單權限。✅
  來源：https://www.okx.com/zh-hant/help/what-guidelines-are-there-for-spot-lead-traders （更新 2026-07-02，查詢 2026-07-16）

### ② 成本
- 申請費用：查無任何申請費／保證金要求。❌（官方頁面無此項）
- 實質資金門檻：帶單時交易帳戶須有 **500 USDT 以上**，低於此數帶單單不會被跟（合約：開倉時帳戶 <500 USDT 帶單失敗；現貨：帳戶 USDT＋現貨帶單資產合計須 >500 USDT）。✅
  來源：https://www.okx.com/zh-hant/help/copy-trading-faqs （FAQ #16，更新 2026-06-02）＋上列現貨帶單指南。
- 每日帶單上限 500 筆。✅ 來源：copy-trading-faqs FAQ #15。

### ③ 分潤機制
- 分潤比例按「交易員等級」（近 90 天平均帶單規模 AUM 決定）：普通/銅牌 L1 = 最高 10%、銀牌 L2 = 13%、金牌 L3 = 15%、傳奇 L4 = **最高 30%**（合約與現貨同表；策略帶單各級皆 30%）。✅
  來源：https://www.okx.com/zh-hant/help/what-guidelines-are-there-for-spot-lead-traders （更新 2026-07-02）
  注意：另一篇〈分潤規則〉（更新 2026-05-29）開頭仍寫「高達 13%」，與新表矛盾，研判為未同步的舊文案（等級表較新且與 lead trader FAQ「最高可達 30%」一致）。⚪
- 跟單者角度：官方 FAQ 寫跟單獲利的 8%–13% 分給帶單員（此頁亦可能未同步新表）。✅ 來源：copy-trading-faqs FAQ #4（更新 2026-06-02）。
- 結算：週結。每週一 0:00（UTC+8）結算上週盈虧；盈利單先按日預扣，結算日多退少補；分潤入帶單員「資金賬戶」。要求結算時雙方無未平倉跟單關係，否則順延。分潤比例每月最多改 3 次。✅
  來源：https://www.okx.com/zh-hant/help/lead-traders-trader-profit-sharing-rules （更新 2026-05-29）
- 交易所抽成：官方文件未提及 OKX 從分潤中抽成。❌ 查無（平台收入為正常交易手續費）。

### ④ 資金流向
- 跟單者資金存入**跟單者自己的交易帳戶**（"Deposit funds into your trading account to start copy trading"）。帶單員完全接觸不到跟單者資金，只輸出交易訊號；跟單者可自設單筆/總額上限。✅
  來源：copy-trading-faqs FAQ #6、#14（更新 2026-06-02）

### ⑤ 台灣可否申請
- 官方「不支援跟單交易的國家/地區」名單：香港、新加坡、古巴、伊朗、北韓、克里米亞、馬來西亞、敘利亞、美國、加拿大、英國、孟加拉、玻利維亞、馬爾他。**台灣不在名單上** → 台灣 KYC 使用者可用跟單功能。✅
  來源：copy-trading-faqs FAQ #2（更新 2026-06-02，查詢 2026-07-16）
- 帶單申請是否對台灣另有限制：官方帶單申請頁未列地區限制。⚪ 推論：台灣可申請（不支援名單未列台灣＋申請條件只有 KYC/帳戶模式），但最終以平台審核為準。

---

## 二、Binance（全部 🔶 未直接核對官方頁，binance.com 被 proxy 封鎖）

### ① 帶單資格
- 合約帶單：已完成驗證（KYC）的帳戶＋最低帶單金額 **1,000 USDT**，於 [Futures]-[Copy Trading] 建立帶單組合（Public/Private）。🔶
  來源：https://www.binance.com/en/support/faq/how-to-lead-trade-on-binance-futures-6acfb4c1f50c4db1b9e915181ff31a4c （WebSearch 摘要，查詢 2026-07-16）
- 現貨帶單：需已驗證帳戶；帶單組合規模須介於 500–250,000 USDT。🔶
  來源：https://www.binance.com/en/support/faq/binance-spot-copy-trading-guide-lead-traders-b9e5e3b2141149be826685d2c88536fa （WebSearch 摘要，2026-07-16）
- 每人限一個帶單身分；預設每組合跟單者上限 200 人，符合 Sharpe Star / Mega Whale 條件可增至 400。🔶
  來源：https://www.binance.com/en/support/faq/binance-futures-copy-trading-lead-trader-growth-plan-3160c961b2734d1cbb5342d1e86c6cdb （WebSearch 摘要，2026-07-16）
- Growth Plan 進階福利門檻：Sharpe Ratio ≥ 8.0（30 天）＋帶單保證金餘額 ≥ 10,000 USDT。🔶 同上來源。

### ② 成本
- 申請費用/保證金：查無申請費。❌ 實質成本＝自有帶單資金（合約至少 1,000 USDT）＋正常交易手續費。⚪

### ③ 分潤機制
- 帶單員可獲跟單者利潤分潤**最高 30%**＋跟單者交易手續費 **10% 返佣**；返佣週上限 = min[總手續費×10%, 跟單組合保證金餘額×3%×10%]。🔶
  來源：https://www.binance.com/en/support/faq/lead-trader-benefits-in-binance-futures-copy-trading-ea9bacf82b9e4ddfae50ebc98565241b （WebSearch 摘要，2026-07-16）
- 結算：週結，週一結算（週期 週一 00:00 UTC–週日 23:59:59 UTC）；2024-09-23 起按組合 Total PNL 結算。🔶 同上來源。
- 幣安是否從分潤抽成：查無。❌

### ④ 資金流向
- 跟單者資金從自己的錢包劃轉到**自己名下的 Copy Trading 錢包**（現貨：Spot Wallet→Spot Copy Trading Wallet），期間鎖定不可提領/轉出，關閉組合後全額退回自己帳戶。帶單員無法動用跟單者資金。🔶
  來源：https://www.binance.com/en/support/faq/binance-spot-copy-trading-guide-copy-trader-abc27f5949cf46d9801d31b5e33d0b38 （WebSearch 摘要，2026-07-16）

### ⑤ 台灣可否申請
- 官方〈Binance Futures Copy Trading Service List〉：服務開放地區名單中**包含台灣**（搜尋摘要顯示 "available to verified users from the following countries and regions: Taiwan, UAE, Egypt, Saudi Arabia, ..."）。🔶
  來源：https://www.binance.com/en/support/faq/binance-futures-copy-trading-service-list-d898460abbd14bd8aab54954ca0d606a （WebSearch 摘要，2026-07-16；完整名單未能直接核對）
- ⚪ 推論：該名單未明文區分「跟單」與「帶單」資格；台灣帳戶可否開帶單組合，建議實際登入後在 App 內確認申請入口是否開放。

---

## 三、Bybit（全部 🔶 未直接核對官方頁，bybit.com 被 proxy 封鎖）

Bybit 有兩套產品：Copy Trading（Classic，門檻低）與 Copy Trading Pro（邀請/審核制，條件高）。

### ① 帶單資格
- Classic Master Trader：Individual KYC Level 1（或企業認證）＋使用**子帳戶**申請＋不得同時是跟單者＋轉入至少 **100 USDT** 到 Master Trader 帳戶＋完成首筆交易；上榜審核約 2–3 個工作天。僅 USDT 永續合約的交易會被跟單。🔶
  來源：https://www.bybit.com/en/help-center/article/How-to-Become-a-Master-Trader ＋ https://www.bybit.com/en/help-center/article/How-to-Get-Started-Copy-Trading-on-Bybit-Master-Trader （WebSearch 摘要，2026-07-16）
- 等級制（Cadet/Bronze/Silver/Gold）：最低總資產 100 / 200 / 1,000 / 10,000 USDT；另有跟單者 7 日累計獲利與最大回撤（Silver ≤30%、Gold ≤15%）等升級條件；14 天無交易自動降級。🔶 同上來源。
- Copy Trading Pro（Pro Master）：現有 Master 須 Silver 級連續 3 週＋30 日 ROI ≥10%＋30 日 Sharpe ≥50%＋30 日最大回撤 ≤20%；外部交易者須由 Bybit 客戶經理推薦＋提交近 30 天交易紀錄截圖，審核 3–7 個工作天。🔶
  來源：https://www.bybit.com/en/help-center/article/How-to-Apply-to-Become-a-Pro-Master-Copy-Trading-Pro （WebSearch 摘要，2026-07-16）

### ② 成本
- 申請費用：查無。❌ 實質成本＝Master 帳戶至少 100 USDT 自有資金（Classic）＋交易手續費。⚪

### ③ 分潤機制
- Classic：分潤比例按等級 Cadet 10% / Bronze 10% / Silver 12% / Gold 15%；跟單者上限 100 / 250 / 1,000 / 3,000 人。僅當跟單者結算期內淨盈利才分潤；結算週期 週六 00:00 UTC–週五 23:59:59 UTC，每週一 03:00 UTC 發放。🔶
  來源：How-to-Become-a-Master-Trader ＋ https://www.bybit.com/en/help-center/article/Copy-Trading-Profit-Sharing-Explained （WebSearch 摘要，2026-07-16）
- Pro：Pro Master 可自設分潤比例**最高 30%**，採 High-Water Mark（NAV 制），每策略週期第 7 天按 NAV 結算。🔶
  來源：https://www.bybit.com/en/help-center/article/Copy-Trading-Pro-Profit-Sharing-Explained （WebSearch 摘要，2026-07-16）
- Bybit 是否從分潤抽成：查無。❌

### ④ 資金流向
- 跟單者資金自動劃轉到**跟單者自己名下的 Copy Trading Account**；停止跟單且平倉後自動退回自己的 Funding Account。Master Trader 用自己子帳戶的資金交易，平台隔離兩者，Master 無法動用跟單者資金。🔶
  來源：https://www.bybit.com/en/help-center/article/FAQ-Copy-Trading （WebSearch 摘要，2026-07-16）

### ⑤ 台灣可否申請
- 官方〈Service Restricted Countries〉：禁用清單為美國、中國大陸、香港、新加坡、加拿大、北韓、古巴、伊朗、烏茲別克、克里米亞/頓內茨克/盧甘斯克、塞瓦斯托波爾、蘇丹、敘利亞等；**台灣不在清單上**。🔶
  來源：https://www.bybit.com/en/help-center/article/Service-Restricted-Countries （WebSearch 摘要，2026-07-16）
- 但官方 FAQ 提及「Copy Trading Pro 在部分國家/地區受限」，具體名單查無。❌ → 台灣可否用 Pro 未確認；Classic 依一般服務清單推論可用。⚪

---

## 四、Bitget（全部 🔶 未直接核對官方頁，bitget.com 被 proxy 封鎖）

### ① 帶單資格（Elite Trader）
- 完成 KYC＋在 App 的 Copy Trading 區提交申請＋平台人工審核（看交易歷史、獲利穩定性、勝率、回撤控制），數個工作天內通知。🔶
  來源：https://www.bitgetapp.com/support/articles/12560603820685 （How to apply to Become an Elite Trader，WebSearch 摘要，2026-07-16）
- 合約 Elite：合約帳戶至少 **500 USDT**＋至少 1 筆已平倉合約單；現貨 Elite：現貨帳戶至少 **100 USDT**＋至少 1 筆已完成現貨單。🔶 同上來源＋ https://www.bitget.com/support/articles/12560603847588
- 上榜/分層另計：7 日合約帶單交易量 <100 USDT 則不入級、分潤上限 0%；≥100 USDT 起入 Bronze。🔶
  來源：https://www.bitget.com/support/articles/12560603803039 （WebSearch 摘要，2026-07-16）

### ② 成本
- 申請費用/保證金：查無。❌ 實質成本＝自有資金門檻（合約 500 USDT）＋手續費。⚪

### ③ 分潤機制
- 六級制：Bronze / Silver / Gold / Platinum / Extraordinary / Legend。分潤上限隨級別升高，Bronze 最高 10%，**Legend 最高 20%**（新戶促銷期可短暫 30%，14–21 天後回歸標準）。現貨 Elite 分潤上限 10%。🔶
  來源：https://www.bitget.com/support/articles/12560603792251 ＋ 12560603803039 ＋ 12560603840845 （WebSearch 摘要，2026-07-16）
- High-Water Mark 制：僅對跟單者「新高獲利」分潤，已結算部分不重複計。結算每週一 08:00（UTC+8），或關閉項目時提前觸發；結算時跟單帳戶不得有未平倉/未賣出部位，否則順延。🔶 同上來源。
- 跟單人數上限：隨級別提高，最高（Extraordinary/Legend）1,000 人。🔶 來源：12560603792251。
- Bitget 是否從分潤抽成：查無。❌

### ④ 資金流向
- 跟單者資金從**自己的合約帳戶**劃轉（Smart Copy 每位交易員獨立資金池，皆在跟單者名下）；平倉後自動退回自己的合約帳戶；跟單者可隨時加/退資金（有待分潤凍結規則：待分潤超過餘額 30% 時凍結對應金額）。Elite Trader 無法動用跟單者資金。🔶
  來源：https://www.bitget.com/support/articles/12560603847571 ＋ 12560603801044 （WebSearch 摘要，2026-07-16）

### ⑤ 台灣可否申請
- Bitget 官方限制地區清單在 Terms of Use（bitget.com/support/articles/360014944032-terms-of-use），本次無法直接核對（proxy 封鎖）。❌ 官方名單查無（未核對）。
- 第三方彙整（datawallet.com、coinperps.com，2026）：禁用美國、加拿大、新加坡、香港、南韓、荷蘭及受制裁國；**台灣不在清單上**，且台灣佔 Bitget 流量約 4.83%。⚪ 線索非證據，未直接核對官方頁。
  來源：https://www.datawallet.com/crypto/bitget-restricted-countries （查詢 2026-07-16）

---

## 五、跨平台共同事實與比較

### 資金流向（四家一致，這是本研究最重要的結論）
四家的跟單架構相同：**跟單者的錢永遠留在跟單者自己名下的帳戶/跟單錢包**（Binance: 自己的 Copy Trading Wallet；OKX: 自己的交易帳戶；Bybit: 自己的 Copy Trading Account；Bitget: 自己的合約帳戶劃轉的獨立跟單資金池）。帶單者只輸出交易訊號，**無法動用、提領或轉走跟單者資金**；跟單者隨時可停跟、平倉、把錢轉回。分潤由交易所系統自動計算與扣轉，不經帶單者之手。（OKX ✅ 直接核對；其餘 🔶）

### 門檻比較（帶單者自有資金）
| 平台 | 最低自有資金 | KYC | 審核 | 分潤上限 | 跟單人數上限 |
|---|---|---|---|---|---|
| Binance 合約 | 1,000 USDT 🔶 | 已驗證帳戶 🔶 | 系統開通（Growth Plan 另審）| 30%＋10% 手續費返佣 🔶 | 200→400/組合 🔶 |
| OKX | 500 USDT（帳戶低於此帶單失敗）✅ | 必須本人 KYC ✅ | 人工審核 ~3 天 ✅ | 等級制 10→30% ✅ | 查無總人數上限 ❌ |
| Bybit Classic | 100 USDT（Master 帳戶）🔶 | KYC L1＋子帳戶 🔶 | 上榜審核 2–3 天 🔶 | 10–15%（Pro 可 30%）🔶 | 100–3,000（按等級）🔶 |
| Bitget 合約 | 500 USDT 🔶 | KYC＋人工審核 🔶 | 數個工作天 🔶 | 10–20%（Legend）🔶 | 最高 1,000 🔶 |

### 台灣可用性
- Binance：官方合約跟單服務清單**明列台灣** 🔶
- OKX：官方不支援清單**無台灣** ✅（唯一直接核對）
- Bybit：官方服務限制清單**無台灣** 🔶（Pro 版地區限制查無）
- Bitget：官方清單未核對 ❌；第三方指台灣可用 ⚪

### 與使用者動機相關的推論（非法律意見）
⚪ 推論：跟單模式確實避開「經手他人資金」——朋友自己開戶、自己入金、自己承擔平倉與停跟決定，資金流向對雙方都可稽核。這比收朋友的錢代操（可能觸及台灣《信託業法》《證券投資信託及顧問法》《期貨交易法》的全權委託/代客操作與《銀行法》收受存款疑慮）在結構上乾淨得多。
⚪ 但不確定性仍在：(1) 台灣尚未開放境外交易所合法落地（金管會 VASP 登記制），使用境外平台本身處於灰色地帶；(2) 若向朋友收取分潤或以「帶單」為業並公開招攬，仍可能被認定為經營期貨顧問或投顧業務；(3) 分潤所得的稅務申報義務。這三點需要台灣執業律師/會計師意見，非本研究可證。

## 附錄：本次無法完成的核對（建議 Mac 手動功課）
1. binance.com / bybit.com / bitget.com 全域（含镜像域）被雲端 proxy CONNECT 403 封鎖——以下頁面需在本機瀏覽器人工核對：
   - Binance 合約跟單服務地區完整清單：binance.com/en/support/faq/detail/d898460abbd14bd8aab54954ca0d606a
   - Binance 帶單條件與分潤原文：faq/detail/6acfb4c1f50c4db1b9e915181ff31a4c、faq/detail/ea9bacf82b9e4ddfae50ebc98565241b
   - Bybit：help-center/article/How-to-Become-a-Master-Trader、Copy-Trading-Profit-Sharing-Explained、Service-Restricted-Countries
   - Bitget：Terms of Use 限制地區清單（articles/360014944032）、Elite 申請條件（bitgetapp.com/support/articles/12560603820685）
2. OKX「最高 13% vs 30%」兩篇官方文互相矛盾（等級表較新，判 30% 為準）——可在帳戶內帶單設定頁直接確認可設上限。

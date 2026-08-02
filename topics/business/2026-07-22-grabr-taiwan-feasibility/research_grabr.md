# Grabr (grabr.io) 研究報告

查詢日期：2026-07-22（除非另外標註）
方法：WebSearch × 19（硬上限 20，剩 1 次未用）；WebFetch × 4 次嘗試（grabr.io、Trustpilot、Crunchbase、LinkedIn 全部回傳 HTTP 403，本環境擋掉，未取得任何 WebFetch 內容——以下全部基於 WebSearch 摘要，非官方頁面原文）。

---

## 1. 現況結論：活著，但規模小、可能已轉型求生

**結論：Grabr 目前仍在營運（未關閉、未被併購），但公開證據顯示公司規模很小、且已經把重心分散到旁支的 fintech 產品線（GrabrFi）——這是「主業成長停滯、找第二曲線」的典型訊號。**

證據：
- Tracxn 公司檔案顯示 Grabr 截至 2026-03-26 僅 22 名員工，仍列為「Active」/Series C 公司。[Tracxn — Grabr Company Profile](https://tracxn.com/d/companies/grabr/__fhVmxJofB8efiHLunZWYU4RJL9Z0U9lY4TTuxn03Y9w)（查詢日 2026-07-22）
- 搜尋結果顯示 Grabr 在 2026 年仍有行銷活動（「featuring Amazon Prime Day deals」），代表平台仍在運作、仍在拉新交易。來源：WebSearch 摘要 "Grabr.io 2026"（查詢日 2026-07-22，原始頁面未能 WebFetch 驗證，僅間接引用）
- Trustpilot 上 Grabr 評論頁存在且持續累積（頁數達 46–47 頁），2025 年的評論仍在被撰寫，整體偏正面但夾雜關於身分驗證、帳戶被封鎖的抱怨。[Trustpilot — Grabr Reviews](https://www.trustpilot.com/review/grabr.io)（WebFetch 被 403 擋下，資訊來自 WebSearch 摘要，查詢日 2026-07-22）
- 沒有找到任何「Grabr shut down」「Grabr acquired」的直接新聞或公告。搜尋「Grabr shut down closed」「Grabr acquired acquisition」均未命中相關結果，只命中同名但無關的公司（Grab 東南亞超級 App、Grabble、GrabIt）。（查詢日 2026-07-22）
- **關鍵旁證**：Grabr Inc. 另外經營一個獨立品牌 **GrabrFi**（讓非美國居民開美金帳戶的 fintech 產品），有自己的募資（Wayra/Telefónica 領投）、自己的銀行合作夥伴遷移公告（2023 年從 Synapse 轉到 Regent Bank + Synctera）。[GrabrFi — Medium 公告](https://medium.com/@grabrfi/grabrfi-is-parting-ways-with-synapse-and-migrating-to-a-new-sponsor-bank-partner-and-platform-6c31310240a7)（查詢日 2026-07-22）。這代表公司把資源/敘事重心放到 fintech 而非核心代購媒合業務——常見於「主業撐不起估值故事，找 pivot」的階段。
- 未查到 2026 年的新一輪募資、用戶數、GMV 等公開更新數字；最近一次可查證的募資是「Series C，2024-02-15，$2.15M」，金額遠小於典型 Series C（2018 年 Series A 就已是 $8M），暗示成長趨緩或估值下修。[VC News Daily — Grabr Secures $8M](https://vcnewsdaily.com/grabr/venture-capital-funding/njxckgrpjx)、WebSearch 摘要「Grabr funding rounds」（查詢日 2026-07-22）

**不確定/查無**：無法獨立驗證創辦人姓名（Artem Fedyaev / Daria Rebenok，多個搜尋摘要一致提及，但未能 WebFetch 官方來源核實，列為「多方 WebSearch 摘要一致但未一手驗證」）；無法取得 2026 年的用戶數/GMV/交易量等硬數字。

---

## 2. 商業模式

- **運作方式**：買家（shopper）在平台發出「求購」（想要的商品+地點），旅客（traveler）出價承接，買家先付款、旅客代購並在旅途中面交/寄送給買家；也有旅客主動列出行程供買家下單的模式。[Grabr Help Center — How does Grabr work?](https://help.grabr.io/hc/en-us/articles/115008104108-How-does-Grabr-work)（查詢日 2026-07-22，經 WebSearch 摘要）
- **費用結構**：總費用約為商品價格的 **10–20%**，組成包含：商品價格本身、美國銷售稅（依州別自動試算）、旅客報酬（Grabr 用機器學習估算建議金額）、金流處理費。[WebSearch 摘要 — Grabr commission fee](查詢日 2026-07-22)、[Grabr Help Center — fee 說明](https://help.grabr.io/hc/en-us/articles/115004005714-Can-you-explain-all-the-fees-I-m-seeing)
- **金流/擔保**：買家付款後由 Grabr **代管於 escrow**，旅客完成交付、買家確認收貨後才撥款給旅客（商品款＋報酬）。[WebSearch 摘要 — Grabr escrow](查詢日 2026-07-22)
- **爭議處理**：平台明文規定「私下交易（跳出平台外的金流/交付）」違反使用條款，一旦如此雙方即失去平台的付款保障，暴露於詐騙風險——顯示 escrow/保障機制是平台核心賣點，也是平台試圖防堵繞過抽成的規則。[Grabr Help Center — What should I do if someone offers to pay or deliver outside of Grabr?](https://help.grabr.io/hc/en-us/articles/1260801843429)（查詢日 2026-07-22）
- 未查到旅客報酬的具體公式（僅知是 ML 估算），也未查到平台對「違禁品/海關罰款」責任歸屬的完整條款原文（WebFetch 被擋，無法讀取 ToS 全文）。

---

## 3. 規模與募資

- **累計募資**：$24.7M，共 7 輪，17 位投資人。[Crunchbase/Tracxn 摘要，查詢日 2026-07-22]
- **代表輪次**：2018-01-17 Series A 由 Foundation Capital 領投 $8M；另有 SignalFire 參與；最近一輪 Series C（2024-02-15）僅 $2.15M，天使投資人包含 Gokul Rajaram。[BusinessWire — Grabr Secures $8M in Funding Led by Foundation Capital](https://www.businesswire.com/news/home/20180307005469/en/Grabr-Secures-8M-in-Funding-Led-by-Foundation-Capital)、WebSearch 摘要（查詢日 2026-07-22）
- **GMV/營收**：僅查到 2019 年舊數字——GMV 約 $1,800萬美元，營收約 $170萬美元。無 2023-2026 任何新數字。[ExpandedRamblings — Grabr Statistics](查詢日 2026-07-22，經 WebSearch 摘要，未能一手核實原始頁面)
- **旅客累積收入**：官方宣稱自 2016 年以來，旅客透過 Grabr 累計賺取超過 $500萬美元、覆蓋 75+ 國家（此為平台自報數字，未經第三方查證）。[WebSearch 摘要 — Grabr.io 2026]（查詢日 2026-07-22）
- **主要市場**：官方自述最初預期買家多是「造訪阿根廷/巴西/俄羅斯的美國人」，實際上發現多數需求方在**拉丁美洲**（巴西、哥倫比亞、厄瓜多、秘魯、烏拉圭有專屬支付/提款選項），另有東南亞與俄語區用戶購買嬰兒奶粉等美國稀缺商品。傳聞「以拉美/俄語區為主」**部分查證屬實**：拉美是明確重心，俄語區證據較薄弱（僅提及俄羅斯/東南亞買嬰兒奶粉，非壓倒性證據）。[AdExchanger — Grabr Connects Community With Global Commerce](https://www.adexchanger.com/mobile/grabr-connects-community-global-commerce-collects-data-along-way/)、WebSearch 摘要（查詢日 2026-07-22）
- **員工數**：22 人（Tracxn，2026-03-26 資料）——對一個經營 9+ 年、募資 $24.7M 的公司而言是偏小的團隊規模。

---

## 4. 關鍵風險的公開證據

- **海關/違禁品責任**：查無 Grabr 對此的完整公開條款原文（WebFetch 被擋）；僅確認平台會提醒「私下交易 = 失去保障」，隱含官方立場是「按平台規則走才有保護」，責任歸屬細節未查得。
- **詐騙/糾紛案例**：
  - Trustpilot 2025 評論中有使用者反映：完成購買後被要求提供身分證件與「手持信用卡錄影」的驗證，拒絕後帳戶被封鎖——屬於使用者對平台驗證機制的具體抱怨案例。[WebSearch 摘要 — Grabr app reviews 2025](查詢日 2026-07-22)
  - 未查到任何法律訴訟、集體訴訟、監管機關調查案例——搜尋「Grabr lawsuit scam fraud dispute customs」只命中不相關的「Grab」（東南亞叫車 App）證券詐欺集體訴訟，與 Grabr 無關。**查無 = 沒有找到公開訴訟紀錄**，不代表不存在，僅代表未被搜尋工具索引到。（查詢日 2026-07-22）
  - Reddit 上的 Grabr 詐騙討論串未能透過 WebSearch 直接命中（搜尋引擎回傳的是「Grab」東南亞公司相關內容），此項**查無**，建議日後用 Reddit 站內搜尋工具補查。

---

## 5. 競爭格局

### 同模式競品現況

| 平台 | 現況 | 證據 |
|---|---|---|
| **Airfrov**（新加坡） | **已死**。2021-04-01 網站與 App 全面關閉，官方歸因為 COVID-19 重創國際旅行、模式失去依託。 | [Mothership.SG — Airfrov website & apps to shut down for good on Apr. 1, 2021](https://mothership.sg/2021/03/airfrov-close/)（查詢日 2026-07-22） |
| **PiggyBee**（法國起家，全球性） | **已死**。營運 10+ 年後於 2022-09-28 宣布關閉，創辦人明言「收入不足以支撐支出」，並直言「P2P 代送這個模式，從來沒有一個平台真正成功過」（原話：peer-to-peer delivery services never really took off with any platform）。 | [ShareTraveler — PiggyBee Shutters Crowdsourced Delivery Business](https://ugr.146.myftpupload.com/piggybee-shutters-crowdsourced-delivery-business/)（查詢日 2026-07-22） |
| **WorldCraze**（法國，crowd-shopping 模式與 Grabr 最相似） | **狀態不明，疑似停業**。官網 worldcraze.com 顯示「維護中」的法文改版訊息，非正常運作頁面；未找到官方停業公告。 | WebSearch 摘要，查詢日 2026-07-22（未能 WebFetch 驗證頁面實際內容） |
| **Nimber**（挪威/英國） | **未發現關閉證據**，FAQ 頁、Instagram 帳號仍列出，但也未查到近期活躍度或用戶量的新聞——狀態介於「小眾存活」與「沉寂」之間，查無定論。 | WebSearch 摘要，查詢日 2026-07-22 |
| **Friendshippr**（透過 Facebook 好友網絡代送） | **已死**，VentureRadar 標記為「permanently closed」。 | [VentureRadar — Friendshippr](https://www.ventureradar.com/organisation/Friendshippr/17da7505-dbb5-44c7-a4d7-f2e853ad77a2)（查詢日 2026-07-22） |
| **Zipments**（紐約在地配送）、**mmMule**（早期 crowdshipping） | 同屬 2008 金融海嘯後那波 crowdshipping 創業潮的成員，未查到明確終止日期，但均未見任何近期營運痕跡，推定已停業/沉寂。 | USPS OIG 報告《Using the 'Crowd' to Deliver Packages》提及三者同屬一批創業案例（查詢日 2026-07-22） |
| **Bringly** | 查無獨立於此名稱的平台資訊；搜尋結果只命中比利時郵政 bpost 旗下的 **Bringr**（不同拼法/不同公司），無法確認題目所指「Bringly」是否存在或已與其他品牌混淆。 | 查詢日 2026-07-22 |

### 替代方案侵蝕 P2P 代購空間

- **集運轉運商（Buyandship 類）**：Buyandship 2014 年香港起家，現有 **超過 120 萬用戶、覆蓋 12 個市場**（含台灣、馬來西亞、新加坡、泰國），已從「消費者的權宜解法」演變為「物流基礎設施的一層」（parcel forwarding is moving from shopper workaround to logistics layer）。[AJOT — Parcel forwarding is moving from shopper workaround to logistics layer](https://www.ajot.com/news/parcel-forwarding-is-moving-from-shopper-workaround-to-logistics-layer)（查詢日 2026-07-22）
- **官方跨境電商基礎建設擴張**：麥肯錫報告指出 2024 年歐盟低價值包裹量約 46 億件（每天約 1,200 萬件），較前一年翻倍，主因是 Shein/Temu 等巨型平台把庫存前置到目的地區域，讓「小額直送」規模化、成本下降，直接壓縮 P2P 代購/集運的價格優勢。[McKinsey — Signed, sealed, and delivered: Unpacking the cross-border parcel market's promise](https://www.mckinsey.com/industries/logistics/our-insights/signed-sealed-and-delivered-unpacking-the-cross-border-parcel-markets-promise)（查詢日 2026-07-22）
- 未特別查到 Amazon Global Store 或淘寶集運的最新滲透率數字（本輪搜尋額度用盡，建議後續補查）。

---

## 6. 這個品類的歷史死亡率

**結論：P2P crowdshipping/代購媒合這個品類的歷史死亡率非常高**——2008 金融海嘯後崛起一整批（Zipments、mmMule、PiggyBee、Deliv、Friendshippr），十餘年後幾乎全滅：

1. **PiggyBee**（10+ 年，2022 年關閉）——創辦人親口證實「這個模式從沒有一個平台真正成功過」，死因：收入撐不住營運成本。
2. **Airfrov**（新加坡，2021 年關閉）——死因：COVID-19 打斷國際旅行供給端，模式對「有人正好出國」的依賴是根本脆弱點。
3. **Friendshippr**（透過 Facebook 好友網絡）——已標記永久關閉，死因細節未查得，但屬於同期同類全滅名單成員。
4. Zipments、mmMule 同屬該波創業潮，均未見存活證據。
5. WorldCraze 疑似停業狀態，Nimber 狀態不明但無成長跡象。

**共同死因模式（依查得資料歸納）**：(a) 供給端（願意代購的旅客）依賴自然人出行意願與時程，COVID 級別的外部衝擊可直接摧毀供給；(b) 單位經濟脆弱——PiggyBee 明確說「收入不夠付支出」；(c) 官方跨境電商基礎建設（Shein/Temu 前置庫存、集運商規模化）持續壓低替代方案的價格與速度，侵蝕 P2P 模式原本的比較優勢。Grabr 是這波倖存者中少數還在檯面上的名字，但其員工規模小（22人）、最新募資輪金額萎縮（$2.15M）、以及分兵經營 fintech 副業（GrabrFi）等訊號，顯示它也未能走出這個品類的結構性難題，而是處於「勉力維持、尋找第二曲線」的狀態，而非高速成長。

---

## 來源清單（依出現順序）

- https://tracxn.com/d/companies/grabr/__fhVmxJofB8efiHLunZWYU4RJL9Z0U9lY4TTuxn03Y9w
- https://www.trustpilot.com/review/grabr.io
- https://vcnewsdaily.com/grabr/venture-capital-funding/njxckgrpjx
- https://www.businesswire.com/news/home/20180307005469/en/Grabr-Secures-8M-in-Funding-Led-by-Foundation-Capital
- https://help.grabr.io/hc/en-us/articles/115008104108-How-does-Grabr-work
- https://help.grabr.io/hc/en-us/articles/115004005714-Can-you-explain-all-the-fees-I-m-seeing
- https://help.grabr.io/hc/en-us/articles/1260801843429-What-should-I-do-if-someone-offers-to-pay-or-deliver-outside-of-Grabr
- https://medium.com/@grabrfi/grabrfi-is-parting-ways-with-synapse-and-migrating-to-a-new-sponsor-bank-partner-and-platform-6c31310240a7
- https://www.adexchanger.com/mobile/grabr-connects-community-global-commerce-collects-data-along-way/
- https://mothership.sg/2021/03/airfrov-close/
- https://ugr.146.myftpupload.com/piggybee-shutters-crowdsourced-delivery-business/
- https://www.ventureradar.com/organisation/Friendshippr/17da7505-dbb5-44c7-a4d7-f2e853ad77a2
- https://www.ajot.com/news/parcel-forwarding-is-moving-from-shopper-workaround-to-logistics-layer
- https://www.mckinsey.com/industries/logistics/our-insights/signed-sealed-and-delivered-unpacking-the-cross-border-parcel-markets-promise

（另有多筆事實僅存在於 WebSearch 回傳的摘要中、原始頁面因 403 無法 WebFetch 驗證，已在正文逐條標註「經 WebSearch 摘要」字樣，未直接引用一手內容。）

## 未能查證項目（誠實列出，非用記憶補）
- Grabr 創辦人姓名：多方摘要一致但未一手驗證
- 2023–2026 年 GMV / 交易量 / 活躍用戶數：查無
- 完整 ToS 中海關與違禁品責任歸屬條款原文：查無（WebFetch 被 403 擋）
- Reddit 上具體詐騙案例串：查無（搜尋引擎未能命中，與同名「Grab」混淆）
- Bringly 是否為真實存在的獨立平台：查無，可能與 Bringr（bpost 比利時）混淆
- 淘寶集運、Amazon Global Store 的具體滲透率數字：查無（額度用盡未查）

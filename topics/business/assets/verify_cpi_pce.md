# 核心 PCE vs 核心 CPI「罕見倒掛」主張 — 嚴格事實查核

驗證日期：2026-09-14（今日）
最新可得：核心 CPI＝2026 年 8 月（公布 2026-09-11）；核心 PCE＝2026 年 7 月（公布 2026-08-26）
工具限制：本環境 WebFetch 對 bls.gov / bea.gov / fred / clevelandfed / wolfstreet / substack / capitaleconomics 全部被 egress proxy 擋（curl 亦 403），
**無法取得原始月度序列自行驗算歷史排名**。以下數字全部來自 WebSearch 引用的公開報導與研究摘要，可信度逐欄標註。
可信度：高＝多來源一致且可追溯官方；中＝單一可信二手來源；低＝搜尋摘要轉述、未能核對原文。

---

## A. 兩個讀數本身

| 主張 | 結論 | 實際數字 | 來源 URL | 資料日期 | 可信度 |
|---|---|---|---|---|---|
| A1a 2026-08 核心 CPI YoY ＝ 2.4% | **成立** | 2.4% YoY（MoM +0.3%） | https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html ・ https://www.bls.gov/news.release/cpi.nr0.htm | 2026-08 資料 | 高 |
| A1b 市場預期 2.4% | **成立** | 「core annual rate came in at 2.4%, matching the estimate」；但**月增 +0.3% 高於預期** | 同上（CNBC） | 2026-09-11 | 高 |
| A1c 前值（7 月）2.5% | **成立** | 2026-07 核心 CPI YoY 2.5%（較 6 月 2.6% 降 0.1pp） | https://www.cnbc.com/2026/08/12/cpi-inflation-report-july-2026.html | 2026-07 資料 | 高 |
| A1d 公布日 2026-09-11 | **成立** | 週五 2026-09-11 08:30 ET | https://www.bls.gov/news.release/cpi.nr0.htm ・ https://www.usinflationcalculator.com/inflation/us-cpi-august-2026/100073342/ | 2026-09-11 | 高 |
| A2a 最新核心 PCE YoY ＝ 3.3% | **成立**（但是 **7 月**資料，非 8 月） | 3.3% YoY，MoM +0.2% | https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026 ・ https://finance.yahoo.com/economy/policy/articles/july-2026-pce-inflation-data-124921061.html | 2026-07 資料 | 高 |
| A2b 預期 3.3% | **成立** | 「核心 in line」；headline 高於預期 | 同上（Yahoo/CNBC 轉述） | 2026-08-26 公布 | 中 |
| A2c 前值 3.3% | **成立** | 2026-06 核心 PCE YoY 3.3%（MoM +0.1%），5 月為 3.4%（2023-10 以來最高） | https://www.advisorperspectives.com/dshort/updates/2026/07/30/core-pce-inflation-at-3-3-in-june-edging-down-from-may ・ https://www.cnbc.com/2026/06/25/pce-inflation-report-may-2026-.html | 2026-06 / 2026-05 | 中 |
| A2d 公布日 | 補充 | 7 月 PCE 於 **2026-08-26** 公布；8 月 PCE 尚未公布（約 9 月下旬） | https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026 | 2026-08-26 | 中 |
| A3a 同期 headline CPI YoY | 取得 | 2026-08 ＝ **3.4%**（MoM +0.4%，汽油 +3.9%）；7 月亦 3.4% | https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html | 2026-08 | 高 |
| A3b 同期 headline PCE YoY | 取得 | 2026-07 ＝ **3.7%**（6 月 3.7%、5 月 4.1%） | https://finance.yahoo.com/economy/policy/articles/july-2026-pce-inflation-data-124921061.html ・ https://qz.com/june-2026-pce-consumer-spending-personal-income-073026 | 2026-07 | 中 |

### ⚠️ A 段最大問題：**+0.9pp 是「跨月份相減」**
3.3%（**7 月** PCE）− 2.4%（**8 月** CPI）＝ 0.9pp，兩個讀數不同月。
**同月比較（2026-07）：3.3% − 2.5% ＝ 0.8pp**。文章若要寫「目前倒掛幅度」，正確寫法是 **0.8pp（7 月同月）**，
或明說「以各自最新一期計為 0.9pp，但月份不同」。直接寫 0.9pp 而不註明＝數據處理錯誤。
另注意：**headline 也是倒掛**（PCE 3.7% > CPI 3.4%，7 月同月 0.3pp），所以這不是「核心」獨有現象，
文章若把成因全推給核心籃子差異（住房權重、金融服務）會漏掉一半。

---

## B. 「常態關係」主張（最關鍵）

| 主張 | 結論 | 實際數字 | 來源 URL | 資料日期 | 可信度 |
|---|---|---|---|---|---|
| B4a 「PCE 比 CPI 低約 0.3–0.5pp」 | **大致成立，但要講清楚是 headline 還是 core、哪段樣本** | 官方：**自 1978 年起 CPI 通膨平均高於 PCEPI 0.3pp**（克里夫蘭聯準會）；**2000 年後平均 0.39pp** | https://www.clevelandfed.org/publications/economic-commentary/2020/ec-202006-cpi-pcepi-inflation-differential ・ PDF: https://www.clevelandfed.org/-/media/project/clevelandfedtenant/clevelandfedsite/publications/economic-commentary/2020/ec-202006-cpi-pcepi-inflation-differential/ec202006.pdf | 1978–2019 / 2000– | 中（原文被擋，數字來自搜尋摘要） |
| B4b 核心版本的長期差距 | **部分取得** | 核心差距常被引為 **0.2–0.5pp**；2011–2019 核心平均差 **0.34pp**（Konczal）；PIMCO 稱「歷史上 PCE 低 CPI 約 30–40bp」 | https://newsletter.mikekonczal.com/p/is-the-actual-inflation-rate-pce ・ https://www.pimco.com/us/en/insights/us-inflation-measures-tell-two-different-stories | 2011–2019 / 長期 | 中 |
| B4c 「1995-01～2013-05 headline CPI 2.4% vs PCE 2.0%」 | 成立（另一組官方樣本，差 0.4pp） | 2.4% vs 2.0% | https://www.stlouisfed.org/publications/regional-economist/july-2013/cpi-vs-pce-inflation--choosing-a-standard-measure | 1995–2013 | 中 |
| B5 歷史上出現過核心 PCE > 核心 CPI 嗎？ | **有，而且不罕見 → 「罕見」說法站不住** | Capital Economics：核心 CPI **自 1960 年以來只有「約 80% 的時間」高於核心 PCE**（＝**約 1/5 的月份是倒掛**）；PIMCO 稱本次是「**1985 年以來最大的反轉之一**」（＝1985 年前有更大的） | https://www.capitaleconomics.com/publications/us-economics-update/core-pce-cpi-inflation-gap-narrow-later-year ・ https://www.pimco.com/us/en/insights/us-inflation-measures-tell-two-different-stories | 1960–2026 / 1985–2026 | 中（原文被擋，未能逐月核對） |
| B5b 具體年月（2000 初、2009–10、2015、2021） | **無法驗證** | 未能取得逐月序列（FRED / BLS / BEA 全被擋），**無法列出具體倒掛年月與幅度** | — | — | 未取得 |
| B6 目前 +0.9pp 屬什麼等級？是否「史上首見」？ | **「史上首見」不成立，必須刪除** | ①本次倒掛**至少從 2025 年秋天就開始**（Konczal：「since last fall that has switched」）；②2026-01 核心 PCE 3.1% vs 核心 CPI 2.5%，已倒掛 0.6pp；③PIMCO 2026-05：由 −30~40bp 翻成 **+60bp**，「1985 年以來最大反轉**之一**」。**確切歷史排名：無法確認。** | https://wolfstreet.com/2026/03/13/core-pce-inflation-hits-3-1-worst-in-2-years-in-unique-twist-blows-way-past-cpi-inflation-driven-by-core-services/ ・ https://newsletter.mikekonczal.com/p/is-the-actual-inflation-rate-pce ・ PIMCO 同上 | 2025Q4–2026-08 | 中 |
| B7 官方 CPI/PCE 差異分解文件 | **存在，有兩份** | BLS《Differences between the CPI and the PCE price index》：四類效應＝**formula（公式，CPI 修正 Laspeyres vs PCE Fisher-Ideal）、weight（權重）、scope（範圍）、other**。BEA《A Reconciliation between the CPI and the PCE Price Index》(2007)：2002–2007 兩者成長率差 **0.4pp，其中近一半由公式差異解釋**，其餘主要由 **rent of shelter 權重差**解釋 | https://www.bls.gov/opub/btn/archive/differences-between-the-consumer-price-index-and-the-personal-consumption-expenditures-price-index.pdf ・ https://www.bea.gov/research/papers/2007/reconciliation-between-consumer-price-index-and-personal-consumption ・ https://apps.bea.gov/papers/pdf/cpi_pce.pdf | 2002–2007 樣本 | 中 |

### B 段結論（給文章的直接指引）
1. 「常態 PCE 低於 CPI 約 0.3pp」→ **可用**，引克里夫蘭聯準會 1978 年以來 0.3pp。
2. 「倒掛罕見」→ **需大幅弱化**。倒掛約佔 1960 年以來月份的 1/5（Capital Economics），
   且**本輪倒掛已持續近一年**（2025 秋起），不是 2026-09 才發生的新聞。
3. 「史上首見 / 史上最大」→ **必須刪除**。最強能寫到 PIMCO 的「1985 年以來最大反轉之一」，
   且要標明是二手研究、本查核**未能取得逐月序列驗證排名**。

---

## C. 機制主張

| 主張 | 結論 | 實際數字 | 來源 URL | 資料日期 | 可信度 |
|---|---|---|---|---|---|
| C8a 住房在 CPI 的權重 | 成立（但要分清 headline / core） | **CPI 住房（shelter）約 34–35%（全項）**；核心 CPI 內約 **44%**（44.3%，二手） | https://www.pimco.com/us/en/insights/us-inflation-measures-tell-two-different-stories ・ https://perc.tamu.edu/blog/2026/06/shelter-cpi.html ・ 官方表：https://www.bls.gov/cpi/tables/relative-importance/2025.htm | 2025-12 權重 | 中（全項）／低（核心 44.3%） |
| C8b 住房在 PCE 的權重 | 成立 | **約 16%**（PIMCO）；「住房＋水電約佔 PCE 服務的 15–18%」 | PIMCO 同上 ・ https://economics.td.com/us-cpi-pce | 2026 | 中 |
| C8c 差距來源 | 成立 | PCE 分母含「代消費者支付」(雇主付健保、政府醫療)，稀釋住房佔比；CPI 只算家庭自付 | https://www.bls.gov/opub/btn/archive/differences-between-the-consumer-price-index-and-the-personal-consumption-expenditures-price-index.pdf | — | 高 |
| C9a 金融服務與保險佔核心 PCE 多少% | **未取得確切百分比** | 僅取得：「financial services furnished without payment」佔**非市場型 PCE 籃子的 20.8%**（非全體 PCE） | https://www.richmondfed.org/research/national_economy/macro_minute/2026/tale_of_two_pces_market_nonmarket-based_prices | 2026 | 中 |
| C9b 投資組合管理費按資產規模計價？ | **成立，且已被官方認定為問題並正在修改** | PPI/PCE 舊法把**管理資產規模隨股市上漲**視為價格上漲；BEA 正將其改為**以公司營收相對服務量**衡量，預估**使 PCE 通膨再降約 0.2pp** | https://www.confluenceinvestment.com/asset-allocation-bi-weekly-aug-3-2026/ ・ https://www.etftrends.com/etf-strategist-content-hub/the-pce-makeover/ | 2026-08 | 中 |
| C9c 聯準會有無正式討論此機制 | **成立** | 里奇蒙聯準會 2026 Macro Minute：「股市走勢與非市場型 PCE 的部分金融服務分項之間存在**強正相關**」 | https://www.richmondfed.org/research/national_economy/macro_minute/2026/tale_of_two_pces_market_nonmarket-based_prices | 2026 | 中 |
| C9d PIMCO 對本輪倒掛的歸因 | 成立 | 「目前核心 CPI 與核心 PCE 的落差，**大致可由投資組合管理服務與軟體相關分類的權重與範圍差異解釋**，兩者都受 AI 相關發展（含股市強勢推升管理費）影響」 | PIMCO 同上 ・ https://investinglive.com/central-banks/pimco-says-ai-linked-categories-are-distorting-core-pce-readings/ | 2026-05 / 2026-08 | 中 |
| C10 FISIM 用存放款利差設算、升息機械性推高該項價格 | **只驗證到一半 → 不可照寫** | 已證實：FISIM ＝「金融機構未明確收費的中介服務」之**間接設算**，在 PCE 屬非市場型 imputed 項目，且 market-based PCE **刻意排除**它。**「用存放款利差對 reference rate 設算」與「升息機械性推高此分項價格指數」這兩句，本次查核未找到聯準會或學界的明確出處。** | https://www.bea.gov/help/glossary/market-based-personal-consumption-expenditures-pce-price-index ・ https://www.richmondfed.org/research/national_economy/macro_minute/2026/tale_of_two_pces_market_nonmarket-based_prices ・ https://www.unescwa.org/sd-glossary/financial-intermediation-services-indirectly-measured | — | 低 |
| C11a CPI shelter YoY 最新讀數與趨勢 | 成立 | **2026-08 shelter YoY ＝ 3.0%**，MoM +0.3%（CNBC 指其「前兩個月已趨緩」後回升） | https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html | 2026-08 | 中 |
| C11b PCE housing YoY 最新讀數 | **未取得** | 搜尋結果混入 2024 年舊文，無法確認 2026-07 PCE housing YoY | — | — | 未取得 |

---

## D. 月增率與三月年化（追加項）

### D1 核心 CPI 季調 MoM
| 月份 | 核心 CPI MoM | 核心 CPI YoY | 來源 | 公布日 |
|---|---|---|---|---|
| 2026-06 | **0.0%**（flat） | 2.6% | https://www.cnbc.com/2026/07/14/consumer-price-index-inflation-report-june-2026.html | 2026-07-14 |
| 2026-07 | **+0.2%** | 2.5% | https://www.cnbc.com/2026/08/12/cpi-inflation-report-july-2026.html | 2026-08-12 |
| 2026-08 | **+0.3%** | 2.4% | https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html | 2026-09-11 |

註：6 月 headline CPI 為 **−0.4%** MoM、YoY 3.5%；核心為 **0.0%**。兩者不可混用。

### D2 核心 PCE 季調 MoM
| 月份 | 核心 PCE MoM | 核心 PCE YoY | 來源 | 公布日 |
|---|---|---|---|---|
| 2026-05 | **+0.3%** | 3.4%（2023-10 來最高） | https://www.cnbc.com/2026/06/25/pce-inflation-report-may-2026-.html | 2026-06-25 |
| 2026-06 | **+0.1%** | 3.3% | https://www.advisorperspectives.com/dshort/updates/2026/07/30/core-pce-inflation-at-3-3-in-june-edging-down-from-may | 2026-07-30 |
| 2026-07 | **+0.2%** | 3.3% | https://www.bea.gov/news/2026/personal-income-and-outlays-july-2026 | 2026-08-26 |

### D3 驗算「三月年化 2.0%」與「單月 0.3% 年化 3.7%」
以上述**四捨五入後的官方 MoM** 計算（BLS 未修約指數會有小數點後第二位差異）：

- 核心 CPI 2026 年 6–8 月三月年化 ＝ (1.000 × 1.002 × 1.003)^4 − 1 ＝ **2.02%** → 「約 2.0%」**正確**
- 單月 +0.3% 年化 ＝ 1.003^12 − 1 ＝ **3.66%** → 「約 3.7%」**正確**（寫 3.7% 可，寫 3.66% 更精準）
- （對照）7 月單月 +0.2% 年化 ＝ **2.43%**
- （對照，文章可用的反擊數字）**核心 PCE 2026 年 5–7 月三月年化 ＝ 2.43%** —— 即核心 PCE 的**近期動能只有約 2.4%**，
  與核心 CPI 的 YoY 2.4% 幾乎相同。3.3% 這個 YoY 主要是**去年基期**造成的，不是當下動能。
  ⚠️ 此為本查核**自行計算**，非引用來源；若要寫進文章請標明「以官方月增率自行年化」。

---

## 🔴 被推翻或無法驗證的主張

1. **「+0.9pp 倒掛」— 算法有誤。** 那是 7 月 PCE 減 8 月 CPI，跨月相減。同月（2026-07）正確值為 **0.8pp**。
2. **「倒掛罕見」— 站不住。** 核心 CPI 自 1960 年以來只有約 **80%** 的時間高於核心 PCE（Capital Economics），
   意即約 **1/5 的月份本來就是倒掛**。「罕見」須改為「相對少見但非異常」。
3. **「史上首見 / 史上最大倒掛」— 必須刪除。** 最強僅能引 PIMCO「1985 年以來最大反轉**之一**」，
   且本查核**無法取得逐月序列確認排名**（FRED/BLS/BEA 在本環境全被擋）。
4. **「這是 2026 年 9 月新出現的現象」— 不成立。** 倒掛**自 2025 年秋季就已翻轉**，2026-01 已達 +0.6pp，
   2026-03（Wolf Street）、04（Capital Economics）、05（PIMCO）、08（PIMCO）均已被廣泛報導。這不是新聞。
5. **「倒掛是核心籃子特有現象」— 不成立。** **headline 也倒掛**（2026-07：PCE 3.7% vs CPI 3.4%）。
6. **FISIM「用存放款利差設算、升息機械性推高該分項價格」— 無法驗證。** FISIM 屬設算項確認無誤，
   但「利差設算 → 升息推高價格指數」的因果鏈**未找到聯準會或學界正式出處**，不可寫成已被證實的機制。
7. **金融服務與保險佔核心 PCE 的百分比 — 未取得。** 只查到「financial services furnished without payment 佔**非市場型** PCE 籃子 20.8%」，
   不能當成「佔核心 PCE 的比重」使用。
8. **PCE housing YoY 最新讀數 — 未取得。**
9. **歷史倒掛的具體年月（2000 初 / 2009–10 / 2015 / 2021）與幅度 — 未取得。**
10. **住房在核心 CPI 的 44.3% — 可信度低。** 官方 relative importance 表（2025-12）本環境讀不到，
    建議文章只寫「全項 CPI 約 34–35%、PCE 約 16%」這組有 PIMCO 背書的數字。
11. **反向證據（文章必須處理，否則會被打臉）：** BEA 已在**修改投資組合管理服務的計價方法**（脫離 AUM 計價），
    預估**再壓低 PCE 通膨約 0.2pp**；多家機構（Capital Economics 2026-04）預期**倒掛在年底前收斂**。
    把倒掛寫成「結構性新常態」會與官方正在進行的方法修正直接衝突。

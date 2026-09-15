# 核心 PCE > 核心 CPI「倒掛」：具體期間與事後資產表現

研究日 2026-09-15。**結論：能定位到具體期間**，且不是靠二手轉述——是用官方 FRED 序列自己算出來的。

## 資料與方法（可複驗）

FRED 對本環境 egress proxy 403，但 **GitHub raw 可通**，取到 FRED 官方序列鏡像：核心 CPI `CPILFESL`（1957-01～2026-08）、核心 PCE `PCEPILFE`（1959-01～2026-07）皆自 https://github.com/theodorewright11/macro_eco_dashboard/tree/main/public/data/fred ；S&P 500 月值（Shiller，1871～）https://github.com/datasets/s-and-p-500 ；黃金月值 https://github.com/datasets/gold-prices ；`GS10`／`FEDFUNDS`／`USREC`／廣義美元 `TWEXBGSMTH` 自 https://github.com/Gariyuuu/forecast-graveyard/tree/main/data/raw

**鏡像可信度已驗**：核心 CPI 兩個獨立 repo 共同 834 個月 **0 筆不符**；核心 PCE 三個 repo 共同 801–811 個月 0～2 筆不符（僅 2025 年 2 筆屬年度修正版次差，<0.01 點）。
**與前輪二手來源對點**：本算法得 2026-07 核心 PCE 3.34% vs 核心 CPI 2.47%（+0.88pp）、2026-01 +0.59pp，與 BEA/BLS 公布值及前輪「+0.6pp」完全吻合。
**全樣本 1960-01～2026-07 共 798 個月，倒掛 173 個月＝21.7%** — 獨立重現 Capital Economics「1960 年以來核心 CPI 僅約 80% 時間高於核心 PCE」。前提可信。
⚠️ 2025-10 核心 CPI **不存在**（政府關門，BLS 從未發布），計算中跳過。工作檔：`gap_series.csv`、`inv.py`、`assets.py`。

---

## 第一節：定位到的倒掛期間（≥6 個月者；連續月為一段）

全樣本共 34 段倒掛，多數為 1–4 個月的雜訊。以下為持續 ≥6 個月的 9 段 ＋ 2021 短段：

| # | 期間 | 長度 | 峰值缺口（月份） | 當時宏觀背景（由 FEDFUNDS／USREC／UNRATE 算出） |
|---|---|---|---|---|
| 1 | 1960-03 ～ 1961-06 | 16mo | +0.67pp（1960-12） | **衰退**（16 個月中 10 個月為 NBER 衰退期）；FF 3.84→1.73（降息 211bp）；失業 5.4→6.9%；通膨下行 |
| 2 | 1971-06 ～ 1972-07 | 14mo | +0.65pp（1971-12） | 擴張；尼克森工資物價管制期；FF 4.91→4.55；失業 5.9→5.6%；通膨快速下行（核心 5.1→2.9%） |
| 3 | 1973-04 ～ 1974-05 | 14mo | +0.94pp（1973-08） | 第一次石油危機；**升息 419bp**（FF 7.12→11.31）；末段入衰退（6 個月）；通膨**急升**（核心 3.3→7.1%） |
| 4 | 1977-07 ～ 1978-03 | 9mo | +0.47pp（1977-07） | 擴張；升息 137bp；失業 6.9→6.3%；通膨高檔盤整（核心 ~6.3–6.7%） |
| 5 | **1982-09 ～ 1983-11** | 15mo | **+2.00pp（1983-08）** | 衰退尾聲轉復甦；FF 10.31→9.34；失業 10.1→8.5%；通膨大幅下行（核心 6.1→4.5%）。**⚠️ 見下方方法論警告** |
| 6 | 2003-03 ～ 2004-08 | 18mo | +0.69pp（2004-01） | 通縮恐慌後的復甦；FF 1.25→1.43（升息循環剛啟動）；失業 5.9→5.4%；租金弱（租屋空置率 ~10%，史上高檔） |
| 7 | 2005-06 ～ 2006-04 | 11mo | +0.27pp（2005-09） | 擴張＋房市高峰；**升息 175bp**；失業 5.0→4.7%；通膨緩升 |
| 8 | 2010-01 ～ 2011-06 | 18mo | +0.70pp（2010-05） | 金融海嘯後復甦；FF ~0（ZIRP＋QE2）；失業 9.8→9.1%；**住房通縮**壓低核心 CPI |
| 9 | 2021-01 ～ 2021-04 | 4mo | +0.55pp（2021-03） | 疫後重啟；FF ~0；通膨自低基期**急升**（核心 PCE 1.7→3.1%） |
| 10 | **2025-11 ～ 2026-07（進行中）** | 9mo+ | +0.88pp（2026-07） | 擴張、失業 4.5→4.1%；FF 3.88→3.63（**降息中**）；核心 PCE **升**（2.8→3.3%）、核心 CPI **降**（2.6→2.5%） |

**本輪在歷史中的位置**：+0.88pp 是 **1985 年以來最大**（此後各段峰值：2010-11 +0.70、2003-04 +0.69、2021 +0.55、2005-06 +0.27）。
這與 PIMCO「1985 年以來最大反轉之一」**完全對得上**，且本算法給出它更精確：不是「之一」，是目前確實最大。1983 那段的 +2.00pp 才是全樣本第一。

⚠️ **1982-83 那段不要拿來當歷史教訓用**。BLS 在 **1983 年 1 月**把 CPI-U 的自有住宅成本從「含房價與房貸利率的 user cost」改為**租金等價（OER）**，CPI-W 到 1985-01 才跟進。
這個改版在雙位數利率剛回落時**機械性壓低了 CPI 的住房分項**，而 PCE 不受影響——所以 +2.00pp 至少有相當部分是**統計定義斷點，不是經濟現象**。
（來源：https://www.bls.gov/opub/btn/volume-2/owners-equivalent-rent-and-the-consumer-price-index-30-years-and-counting.htm ・ https://www.fullstackeconomics.com/p/why-the-government-took-home-prices-out-of-the-consumer-price-index ・ https://chodorowreich.scholars.harvard.edu/sites/g/files/omnuum7686/files/2025-07/CPI_and_Housing_1.pdf）
順帶一提：PIMCO 的分水嶺剛好落在 1985，很可能正是因為 CPI 住房口徑到那時才完全統一。

---

## 第二節：倒掛結束後的資產表現（自本研究計算，非引用）

以**倒掛段結束當月**為基準（t=0），往後 6／12 個月。S&P 500 為**價格報酬**（Shiller 月均值，不含股息）；10Y 為殖利率**變動 bp**；美元＝廣義美元指數（2006 年起才有）。

| 期間（結束月） | S&P+6m | S&P+12m | 黃金+6m | 黃金+12m | 10Y+6m | 10Y+12m | 美元+6m | 美元+12m |
|---|---|---|---|---|---|---|---|---|
| 1961-06 | +9.3% | **−15.2%** | 0.0% | 0.0% | +18bp | +3bp | n/a | n/a |
| 1972-07 | +10.4% | −1.3% | −1.5% | **+81.8%** | +35bp | +102bp | n/a | n/a |
| 1974-05 | **−20.0%** | +0.5% | +11.7% | +2.5% | +10bp | +48bp | n/a | n/a |
| 1978-03 | +17.0% | +12.7% | +15.2% | +31.5% | +38bp | +108bp | n/a | n/a |
| 1983-11 | −5.2% | +0.7% | −1.3% | −10.5% | +172bp | −12bp | n/a | n/a |
| 2004-08 | +10.2% | +12.4% | +5.5% | +9.2% | −11bp | −2bp | n/a | n/a |
| 2006-04 | +4.7% | +12.4% | −4.1% | +11.1% | −26bp | −30bp | −1.4% | −4.1% |
| 2011-06 | −3.4% | +2.8% | +7.3% | +4.6% | −102bp | −138bp | +6.1% | +8.0% |
| 2021-04 | +7.7% | +6.0% | +1.0% | +10.1% | −6bp | +111bp | +1.3% | +4.0% |
| **中位數** | **+7.7%** | **+2.8%** | +1.0% | +9.2% | +10bp | +3bp | — | — |

**對照組（同期無條件基準）**：1960–2025 全樣本 S&P 500 任意月起算 +12m 中位數 **+10.5%**、正報酬機率 75%（n=788）。
→ 倒掛結束後 12 個月的 +2.8% 中位數**明顯低於**無條件基準，9 次中 7 次為正。
⚠️ **但 n=9，且彼此高度重疊、橫跨三種貨幣制度與一次 CPI 改版——這在統計上完全不足以支撐任何結論。文章若引用，必須寫成「樣本太小、僅供描述」，不可寫成規律。**

**倒掛「開始」後 12 個月**（另一種切法，供參）：S&P 中位數 +14.2%，明顯較好——**這個訊號連方向都不穩定**，更說明它不是可用的擇時指標。

---

## 第三節：別人怎麼解釋這個缺口

**通用機制（跨期間都適用）**
- 官方拆解四類效應：**公式**（CPI 修正 Laspeyres vs PCE Fisher-Ideal，含替代效應）、**權重**、**範圍**、其他。BLS：https://www.bls.gov/opub/btn/archive/differences-between-the-consumer-price-index-and-the-personal-consumption-expenditures-price-index.pdf ・ BEA 2007 對帳（2002–07 差 0.4pp，近半來自公式差）：https://apps.bea.gov/papers/pdf/cpi_pce.pdf
- 克里夫蘭聯準會《The CPI–PCEPI Inflation Differential: Causes and Prospects》（1978 年起 CPI 平均高 0.3pp）：https://www.clevelandfed.org/publications/economic-commentary/2020/ec-202006-cpi-pcepi-inflation-differential

**住房權重（三項中最關鍵，且是歷史倒掛的共同主因）**
- 住房在 CPI 約 34%（核心 CPI 內 **逾 40%**），在 PCE 僅約 16%。→ **CPI 住房走弱時，核心 CPI 被拉下得比核心 PCE 多，就會倒掛。**
- **2010–11 那段已被聯準會明確如此解釋**：舊金山聯準會《The Housing Drag on Core Inflation》（2010-04）指 OER 下行是當時反通膨主因，且因 CPI 權重較高，對核心 CPI 的壓抑大於核心 PCE：https://www.frbsf.org/economic-research/publications/economic-letter/2010/april/housing-drag-core-inflation/
- 2003–04 那段同屬租金弱期（租屋空置率 ~10%，史上高檔；Census HVS：https://www.census.gov/housing/hvs/files/qtr304/q304tab2.txt）。**本研究的推論，未見專文如此歸因。**

**本輪（2025–26）的解釋，依來源分**
1. **住房＋醫療＋金融服務三項權重差**（正是你問的三項）：PIMCO《U.S. Inflation Measures Tell Two Different Stories》—— 住房 CPI 34% vs PCE 16%；醫療、金融服務、資通訊在 PCE 權重較高：https://www.pimco.com/gbl/en/insights/us-inflation-measures-tell-two-different-stories
2. **醫療範圍差**：PCE 含**雇主支付的健保與政府支付的醫療**（Medicare/Medicaid），CPI 只算家戶自付。2026 醫療成本加速 → 對 PCE 推力遠大於 CPI。KBC《Why US CPI and PCE inflation figures diverge》：https://www.kbc.com/en/economics/publications/why-us-cpi-and-pce-inflation-figures-diverge.html
3. **金融服務／投資組合管理費**：按資產規模計價，股市漲＝該分項「漲價」；BEA 正在改方法，預估使 PCE 通膨降約 0.2pp。里奇蒙聯準會證實股市與非市場型 PCE 分項強正相關：https://www.richmondfed.org/research/national_economy/macro_minute/2026/tale_of_two_pces_market_nonmarket-based_prices
4. **⚠️ 最重要且最少人講的一項：2025-10 政府關門造成的 CPI 住房測量斷點。** BLS 因關門無法收集租金調查，改用 **carry-forward**（視同租金未變），等於把 10 月住房通膨當成 0；住房佔核心 CPI 逾 40%，這個假設**「錨定了後續指數、效果會延續」**，**機械性壓低了核心 CPI 的年增率**。到 **2026-06** 才是修正後第一個完整月份。
   來源：https://www.morningstar.com/economy/how-navigate-shutdown-affected-november-cpi-report ・ https://www.mortgagenewsdaily.com/news/05152026-cpi-shelter-shutdown ・ https://fortune.com/2025/12/18/inflation-report-october-2025-shutdown-distorted-diane-swonk
   → **本輪倒掛的分母端（核心 CPI 偏低）有一部分是統計假象，不是通膨真的降。** 這點與 1983 那段的性質相同，文章值得並列講。
5. 其他：Wells Fargo《Wedge Issue》https://www.actionforex.com/contributors/fundamental-analysis/545993-wedge-issue-whats-driving-the-gap-between-cpi-and-pce-inflation/ ・ Konczal（倒掛自 2025 秋起）https://newsletter.mikekonczal.com/p/is-the-actual-inflation-rate-pce ・ Wolf Street https://wolfstreet.com/2026/03/13/core-pce-inflation-hits-3-1-worst-in-2-years-in-unique-twist-blows-way-past-cpi-inflation-driven-by-core-services/ ・ Capital Economics 預期缺口今年稍後收斂 https://www.capitaleconomics.com/publications/us-economics-update/core-pce-cpi-inflation-gap-narrow-later-year

---

## 第四節：這個題目查得到什麼、查不到什麼（誠實盤點）

**查得到（且品質好）**
- ✅ **具體倒掛期間**：可自行從官方序列精算，34 段、≥6 個月的 9 段，年月與缺口幅度俱全（第一節）。這比任何二手來源都精確。
- ✅ 倒掛頻率 21.7%，獨立重現 Capital Economics 的「80%」——「罕見」說法確定不成立。
- ✅ 本輪 +0.88pp 確為 1985 年以來最大，PIMCO 說法可用且可加強。
- ✅ 缺口的**成因**解釋非常充足：官方（BLS/BEA/克里夫蘭聯準會/舊金山聯準會/里奇蒙聯準會）＋賣方（PIMCO/Wells Fargo/Capital Economics/KBC）都有。
- ✅ 2010–11 那段的官方歸因（住房權重）明確存在，是本輪最好的歷史對照。

**查不到（重要，且是文章該誠實講的）**
- ❌ **沒有任何研究把「CPI-PCE 缺口」當成資產報酬的預測訊號。** 所有文獻都在解釋缺口「為什麼存在」與「對聯準會政策的意涵」，**沒有一篇做「缺口 → 股債後續報酬」的事件研究。**前一輪的判斷在本輪擴大搜尋後仍然成立。
- ❌ 沒有任何來源列出歷史倒掛期間清單（第一節是本研究自算，**不是引用**；文章若用需註明方法）。也沒有 1960/1971/1973/1977/2003/2005 各段的成因專文——第一節的宏觀背景是**由官方序列算出的事實**（利率、衰退月數、失業率），不是他人的因果解釋。
- ❌ 沒有把 1983 CPI 改版與「倒掛」連起來討論的文獻——兩件事各自有來源，**連結是本研究的推論**，文章要標明。

**給文章的三個可用結論**
1. 「這種狀態歷史上出現過嗎」→ **常出現，約每五個月就有一個月**；持續半年以上的明確段落自 1960 年來有 9 段。
2. 「後來怎麼了」→ **沒有一致的後續**。9 次樣本裡股票 12 個月中位數 +2.8%（低於無條件的 +10.5%），但 n=9、跨三種貨幣制度、且改用「倒掛開始」當基準結論就反轉。**誠實的答案是：這不是一個能拿來做決策的訊號。**
3. 真正該講的是**缺口的成因**：本輪分子端（核心 PCE 偏高：醫療範圍、投資組合管理費隨股市計價）與分母端（核心 CPI 偏低：住房權重＋2025-10 關門的 carry-forward 斷點）**各有一半是「測量」而非「通膨」**。

---

## 第五節：未取得清單

- 缺口作為**預測訊號**的任何研究／券商事件研究 → **查無**（已用多組關鍵字，判定為真的不存在）。
- 歷史各倒掛期間的**他人成因分析**（1960/1971/1973/1977/2003/2005 段）→ 未取得。
- 美元表現 1973–2005 各段 → **未取得**（可得的廣義美元指數 TWEXBGSMTH 自 2006-01 才開始）。
- 公債**總報酬**（非殖利率變動）→ 未取得；第二節僅有 GS10 殖利率變動 bp。
- 1961/1972 黃金 → 布列敦森林固定 35 美元，變動 0% 非市場價格，不具意義。
- 2026-08 核心 PCE → 尚未公布（約 9 月下旬），第一節末段以 2026-07 為最新。
- BLS 處理關門期間住房資料的**原始研究報告 PDF** → 僅取得二手轉述（bls.gov 被 proxy 擋）。
- 1983 CPI 改版對當年 CPI 年增率的**量化影響幅度**（幾 pp）→ 未取得，故第一節只說「相當部分」，未給數字。

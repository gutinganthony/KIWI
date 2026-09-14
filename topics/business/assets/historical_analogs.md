# 供給面油價衝擊 + 核心通膨溫和 → 央行仍升息：歷史前例與事後資產表現

**製作日期**：2026-09-14（今日，經 WebSearch 確認）
**方法限制**：本環境 WebFetch 對 fred.stlouisfed.org / eia.gov / multpl.com / ameriprise.com / seekingalpha.com 全數被 egress proxy 擋下，curl 亦被擋。
所有數字僅能來自 WebSearch 摘要，**未能取得日頻原始序列**，因此「事件日起算 3/6/12 個月報酬」多半只能用年度報酬代替，已逐項標註。
**本檔未做任何自行推估**；查不到就寫「未取得」。報酬口徑不確定者標「口徑不明」。

## 當下情境（作為對照基準，非歷史案例）

- Brent 自 7 月起因荷姆茲海峽／紅海軍事行動大漲，9 月初突破 $105、近期一度站上 $108。
  來源：https://fortune.com/article/price-of-oil-09-02-2026/（2026-09-02）、https://hoodline.com/2026/09/wholesale-prices-surge-as-oil-tops-105-fed-faces-rate-hike-gamble/（2026-09）
- 2026 年 8 月：核心 CPI 年增 **2.4%**（2021 年 3 月以來最低），整體 CPI 年增 **3.4%**，能源月增 2.1%、汽油月增 3.9%。
  來源：https://economics.td.com/us-cpi ・ https://www.cnbc.com/2026/09/11/cpi-inflation-report-august-2026.html（2026-09-11）
- 2026 年 7 月：核心 PCE 年增 **3.3%**（6 月同為 3.3%，5 月 3.4% 為 2023 年 10 月以來最高）。
  來源：https://www.cnbc.com/2026/08/26/feds-preferred-inflation-gauge-shows-core-prices-rose-3point3percent-annually-in-july.html（2026-08-26）
- 市場對 9 月 FOMC 升息押注 89–90%。來源：https://www.kiplinger.com/investing/economy/cpi-report-august-2026-what-to-expect
- ECB 已在伊朗戰爭引發的通膨疑慮下升息，且被經濟學家公開類比為「重演 2011 年錯誤」。
  來源：https://www.bloomberg.com/news/articles/2026-06-08/ecb-risks-repeating-2011-mistake-with-rate-hike-economists-warn（2026-06-08）

---

## 第一節：案例總表

| # | 案例 | 年份 | 油價變動 | 當時核心通膨 | 央行動作 | 6–12 個月後結果 | 是否衰退 | 符合本題情境？ |
|---|---|---|---|---|---|---|---|---|
| 1 | 伊拉克入侵科威特 | 1990-08 ~ 1991-02 | 月均 $17（7月）→ $36（10月）；WTI 自 8/2 至 10/11 高點 +90.2%，峰值 $36.04 | 未擴散，整體 CPI 跳升但核心未失控 | **Fed 是降息不是升息**：1990-07 至 1991-01-17 共降 6 次，8.25%→6.75%；至 1992-07 降到 2.75% | 油價 1991 Q1 迅速回落；戰爭結束後一年 S&P +約 29% | **是**（1990-07 起，NBER；GDP −1.6%、失業率 7.8%） | ❌ 不符（央行反向操作），但可作「油價衝擊＋核心未失控」前例 |
| 2 | 油價三倍 + Fed 收尾 | 1999-02 ~ 2000-09 | $11/桶（1999-02，25 年低點）→ 近 $35（2000-09 第一週） | 核心 CPI 1.9%（1999）→ 2.6%（2000），溫和偏上 | Fed 升息（一般紀錄為 4.75%→6.50%，**本次未直接查證原始出處**） | Nasdaq 2000-03-10 見頂 5,132.52，其後 2.5 年跌 78%；2001 年 Fed 降息 11 次 6.5%→1.75% | **是**（2001-03 起） | △ 部分符合（核心溫和、央行升息），但泡沫破裂是主因，非油價 |
| 3 | 中國需求推升油價 + Fed 連續升息 | 2004-06 ~ 2006-07 | WTI 年均 $56.46（2005）→ $66.10（2006）→ $72.29（2007）；1999–2005 自 $16 漲到 $50 | **核心受控**：核心 CPI 2.2%（2005）、2.6%（2006）；2006 Q1/Q2/Q3 核心 2.1%/2.7%/2.2% | Fed **連 17 次會議升息**，1.00%→5.25%；同期 PCE 通膨 2.9%→3.4% | 2006 下半年油價轉跌、整體通膨回落；股市續漲 | **未立即衰退**；衰退遲至 2007-12（與油價關聯薄弱） | ✅ 最接近「核心溫和但續升息且沒出事」的正面樣本 |
| 4 | **阿拉伯之春 / ECB 兩次升息** | 2011-04 ~ 2011-12 | Brent 2011 年均 **$111.26**（史上首次年均破 $100）；12 月均價 $107.87 | 歐元區核心溫和，ECB 幕僚與 SPF 預測顯示通膨在預測期內大致受控 | ECB **升息兩次**：2011-04-07 1.00%→1.25%；2011-07-07 →1.50% | **7 個月內全數回頭**：2011-11-03 降至 1.25%、2011-12-14 降回 1.00% | **是**：歐元區衰退 2011 Q3–2012 Q1，再二次衰退 2012 Q4–2013 Q1 | ✅✅ **可比性最高**（公認政策錯誤） |
| 5 | Fed 升到 2.5% + 油價崩 | 2018 全年 | WTI 10 月初近 $76 → 12 月中約 $42，Q4 約 −40% | 核心溫和（**具體核心 PCE 數值未取得**） | Fed 2018 全年升息 4 次至 2.25–2.50%（12 月最後一次） | 2019-01 Fed 轉鴿、2019 年降息 3 次；股市大幅反彈 | **否**（無衰退） | ❌ 不符（油價是崩不是漲），僅可作「升息撞上放緩」對照 |
| 6 | 俄烏戰爭 | 2022 | Brent 2022-03-08 收 **$123.64** 為峰值（$139 盤中價未查證） | **核心過熱**（核心 CPI 約 6%），不符「溫和」前提 | Fed 以數十年最快速度升息 | S&P 自 2022-01 高點至 10 月低點 −約 25% | 技術性爭議，NBER 未認定 | ❌ 不符（核心不溫和） |
| 7 | 1973 阿拉伯禁運 / 1978–79 伊朗革命 | 1973-10 / 1978-01 | 兩次大型供給衝擊 | **核心極高**（大通膨時代） | Volcker 1979 後升息至 20%（1981-06） | 見第二節 | 1973–75、1980、1981–82 三次衰退 | ❌ 不符（核心不溫和），僅作極端邊界 |

**來源（第一節）**
- 1990：https://en.wikipedia.org/wiki/1990_oil_price_shock ・ https://theberkshireedge.com/capital-ideas-what-does-the-1990-gulf-war-reveal-about-todays-stock-market/ ・ https://finance.yahoo.com/news/lessons-from-iraq-kuwait-invasion-225924707.html
- 1999–2000：https://www.resources.org/archives/the-surge-in-oil-prices-anatomy-of-a-non-crisis/ ・ https://www.bls.gov/opub/mlr/2001/04/art3full.pdf ・ https://trendspider.com/learning-center/the-dot-com-recession-2001/
- 2004–06：https://www.richmondfed.org/publications/research/economic_brief/2023/eb_23-26 ・ https://www.cbsnews.com/news/inflation-eased-in-2006/ ・ https://www.chicagofed.org/publications/chicago-fed-letter/2007/february-235 ・ https://www.federalreserve.gov/boarddocs/rptcongress/annual06/sec1/c1.htm
- 2011：https://money.cnn.com/2011/04/07/news/international/ecb_interest_rate/ ・ https://money.cnn.com/2011/07/07/news/international/ecb_interest_rates/index.htm ・ https://www.ecb.europa.eu/press/pr/date/2011/html/pr111103.en.html ・ https://tradingeconomics.com/articles/12082011125021.htm ・ https://www.eia.gov/todayinenergy/detail.php?id=4550 ・ https://econbrowser.com/archives/2022/05/sovereign-debt-crisis-or-oil-in-the-euro-area-recession-of-2011-13 ・ https://pitchbook.com/news/articles/the-ecb-hiked-rates-into-a-crisis-in-2011-4-charts-looking-back-on-european-private-markets
- 2018：https://www.schroders.com/en/global/individual/insights/quarterly-markets-review---q4-2018/ ・ https://www.washingtonpost.com/graphics/2018/business/stock-market-crash-comparison/
- 2022：https://www.dallasfed.org/research/economics/2022/0322

---

## 第二節：各案例事後資產表現

⚠️ **重要限制**：FRED、EIA 等原始資料源全數被擋，無法計算「事件日 +3/+6/+12 個月」精準報酬。
下表以「**年度報酬**」為主、僅少數有事件日起算的 12 個月數字（來自 Ameriprise 彙整）。口徑不明者標示。

| 案例 | S&P 500（3M / 6M / 12M） | 10Y 美債殖利率 | 美元 | 黃金 | 油價本身 | 是否衰退收場 |
|---|---|---|---|---|---|---|
| 1990 波灣 | 3M：未取得；**事件起算最大回檔 −19.9%（8 月→10 月）**，另一來源為 8/2→10/11 **−16.9%**；**12M：+8.6%**（Ameriprise，事件日起算，口徑不明）；戰爭結束後一年 +約 29% | 未取得 | 未取得 | 未取得 | 8/2→10/11 WTI **+90.2%**，峰值 $36.04；1991 Q1 迅速回落 | ✅ 衰退（1990-07 ~ 1991-03） |
| 1999–2000 | 未取得（3/6/12M 均無）；2000、2001 年度報酬**未取得** | 未取得 | 未取得 | 未取得 | $11 → 近 $35（約 3 倍） | ✅ 衰退（2001-03 起） |
| 2004–06 | 年度總報酬（slickcharts/chartrow 口徑，應為 TR）：**2005 +4.3%、2006 +16%、2007 +5.1%** | 未取得 | 未取得 | 2005 +17.5%、2006 +23.5%（年度，口徑不明） | WTI 年均 $56.46→$66.10→$72.29 | ❌ 未立即衰退（衰退遲至 2007-12） |
| **2011 ECB** | **S&P 500 2011 全年總報酬 +2.11%**（價格報酬約 0%）；**5 月→10 月回檔 −19%**；歐股：**Euro Stoxx 50 −15.26%**（另一來源稱 −17%，未能對齊；口徑不明）、**DAX −14.7%**、CAC −15%+ | 未取得精確值；已知 **美國長天期公債 2011 年總報酬 +33%**（2008 年以來最佳） | 未取得 | **+10.1%**（另一來源 +9.6%），年度 | Brent 年均 $111.26（史上首次破 $100）；12 月均 $107.87 | ✅ 歐元區衰退（2011Q3–2012Q1，再二次衰退 2012Q4–2013Q1）；美國未衰退 |
| 2018 | **Q4 2018 −13.5%**；2018 全年總報酬 **−4.6%**；**2019 全年 +31%** | 2018-11 月均 **3.12%** → 2018-12 月均 **2.83%**（Fed FSR 口徑） | 上漲（某來源稱 +6.66%，但其「120→128」數值明顯非 DXY，**判定不可用**） | 2018 收 $1,282.82、**−1.6%**（另一來源 −3.4%） | WTI 10 月初近 $76 → 12 月中約 $42，Q4 約 −40% | ❌ 無衰退 |
| 2022 俄烏 | **12M：−12.4%**（Ameriprise，事件日起算，口徑不明）；自 2022-01 高點至 10 月低點 −約 25% | 未取得 | 未取得 | 未取得 | Brent 峰值 $123.64（2022-03-08 收盤） | ❌ NBER 未認定衰退 |
| 1973 禁運 | **12M：−41.0%**（Ameriprise） | 未取得 | 未取得 | 未取得 | 未取得 | ✅ 1973–75 衰退 |
| 1978 伊朗革命 | **12M：+5.3%**（Ameriprise） | 未取得 | 未取得 | 未取得 | 未取得 | ✅ 1980、1981–82 衰退 |
| 2003 伊拉克戰爭 | **12M：+35.0%**（Ameriprise） | 未取得 | 未取得 | 未取得 | 未取得 | ❌ 無衰退 |

**Volcker 期（作為極端邊界）**：Fed funds 11.2% → 20%（1981-06）；兩次衰退（1980-01~07、1981-07~1982-11）。
S&P 500 於 **1982-08-12 觸底 102.42（−27.11%）**，**83 天後即收復前高**，多頭至 **1983-10-10 的 172.65（自底部 +68.57%）**。
來源：https://www.forbes.com/sites/davidmarotta/2017/10/11/volkers-bear-the-bear-market-of-1982/ ・ https://www.stlouisfed.org/-/media/project/frbstl/stlouisfed/publications/review/pdfs/2025/jan/volcker-tightening-cycle-explaining-1982-course-reversal.pdf

**來源（第二節）**
- Ameriprise 油價衝擊 12 個月報酬表：https://www.ameriprise.com/financial-news-research/insights/oil-shocks-history （WebFetch 被擋，數字來自搜尋摘要，**未能核對原表口徑，是否含股息不明**）
- S&P 年度總報酬：https://www.slickcharts.com/sp500/returns ・ https://chartrow.com/sp500/returns
- 2011 長天期公債 +33%、S&P +2.11%：https://www.slickcharts.com/sp500/returns ・ https://money.cnn.com/2011/12/30/markets/markets_newyork/index.htm
- 黃金年度報酬：https://www.visualcapitalist.com/charted-golds-annual-returns-2000-2025/
- 2018 殖利率：https://www.federalreserve.gov/publications/2019-may-financial-stability-report-accessible.htm
- 2011 歐股：https://money.cnn.com/2011/12/30/markets/markets_newyork/index.htm ・ https://curvo.eu/backtest/en/market-index/euro-stoxx-50

---

## 第三節：「核心 PCE > 核心 CPI 倒掛」的歷史

### 這個倒掛歷史上出現過嗎？——有，但極罕見

- **常態是反向**：自 1960 年以來，核心 CPI 高於核心 PCE 的時間佔**近 80%**，平均**高出 47 個基點（0.47pp）**。
- **目前的翻轉幅度**：PCE 減 CPI 的年增率差距從歷史常態的 **−30 至 −40bp** 翻轉為 **+60bp**，
  PIMCO 稱這是 **「1985 年以來最大的反轉之一」**。
- **上一次出現同型倒掛**：PIMCO 明言「在 1960 年以來最早可得的資料中，**除了 1980 年代初期這個顯著例外，此種倒掛前所未見**」。
- **本輪驅動因素**：PCE 權重較高的軟體（AI 投資潮推升）、醫療服務、金融服務加速；
  CPI 權重較高的房租（CPI 住房約 36%、PCE 約 15%）與車價則在減速。
- **目前數值**：核心 PCE 3.3%（2026-07）vs 核心 CPI 2.4%（2026-08）≈ 90bp 倒掛。
  ⚠️ 兩者參考月份不同，非嚴格同期比較；PIMCO 5 月時引用的是核心 CPI 2.8% vs 核心 PCE 3.3%（50bp）。

來源：https://www.pimco.com/us/en/insights/us-inflation-measures-tell-two-different-stories ・
https://www.advisorperspectives.com/commentaries/2026/05/08/u-s-inflation-measures-tell-two-different-stories ・
https://www.clevelandfed.org/publications/economic-commentary/2020/ec-202006-cpi-pcepi-inflation-differential

### 倒掛期間與之後 12 個月的股債表現？ → **查無**

**明確結論：查無任何專門研究「核心 PCE > 核心 CPI 倒掛」與後續股債報酬的量化分析。**
所有查到的文獻（PIMCO、Cleveland Fed、KBC、Capital Economics）都只討論**成因與政策意涵**，
沒有任何一篇把倒掛當成訊號去回測資產報酬。這很可能確實沒人做過。

唯一可提供的間接錨點：上一次倒掛期（1980 年代初）恰好落在 Volcker 雙底衰退中，
S&P 500 於 1982-08-12 見底 −27.11%，隨後 14 個月 +68.57%。
⚠️ **這是時間重疊，不是因果關係**；不應寫成「倒掛之後股市會怎樣」。

---

## 第四節：基準率統計（給讀者當錨）

### 4.1 油價衝擊後 12 個月 S&P 500 報酬（Ameriprise 彙整，事件日起算，含息與否未查證）

| 事件 | 起算日 | 後 12 個月 S&P 500 |
|---|---|---|
| 第一次石油危機（阿拉伯禁運） | 1973-10 | **−41.0%** |
| 第二次石油危機（伊朗革命） | 1978-01 | **+5.3%** |
| 第一次波灣戰爭 | 1990-08 | **+8.6%** |
| 第二次波灣戰爭（伊拉克） | 2003-03 | **+35.0%** |
| 俄烏戰爭 | 2022-02 | **−12.4%** |

**簡單平均約 −0.8%，中位數 +5.3%，5 次中 3 次為正。**（此為本檔依上表 5 個公開數字所做的算術，不是外部研究結論。）
同來源另註：**1973 年底至 2025 年底 S&P 500 年均價格報酬 +8.5%**。
來源：https://www.ameriprise.com/financial-news-research/insights/oil-shocks-history

### 4.2 「油價半年內漲 30%+ → 後 12 個月 S&P 平均報酬與衰退機率」的專門研究 → **未取得**

**查無符合該精確定義（+30% / 6 個月窗口）的公開統計研究。**
最接近的是一份被二手引用的統計：
- **Kedia Advisory**：1986 年以來 **7 次油價飆升事件，S&P 500 隨後一年平均報酬 +24%，7 次中 6 次為正**。
  例：2003 伊拉克戰爭後約 +25%、2016 OPEC 減產後約 +19%。
  ⚠️ **僅見於二手轉述，未能取得原始報告，事件定義與門檻不明，勿當硬數據引用。**
  來源：https://clark.com/personal-finance-credit/investing-retirement/what-happens-to-the-stock-market-when-oil-prices-spike/ ・
  https://www.fool.com/investing/2026/03/10/heres-how-stocks-react-when-price-of-oil-spikes/

### 4.3 油價與衰退的關聯（最扎實的公開統計）

- **Hamilton（UCSD）**：疫情前的 **11 次戰後美國衰退中，有 10 次在事前數月出現油價上漲**，唯一例外是 1960 年那次；
  典型領先時間約 **3/4 年**。Hamilton 本人強調**這不等於油價造成了這些衰退**，但證據顯示油價衝擊至少在部分衰退中是助力。
  來源：https://econweb.ucsd.edu/~jhamilto/oil_history.pdf ・ https://www.nber.org/system/files/working_papers/w16790/w16790.pdf
- 反向讀法（文章可用）：**油價漲不代表衰退，但幾乎每次衰退前油價都漲過**——這是條件機率方向完全不同的兩件事，讀者最常搞混。

### 4.4 Fed 升息循環的軟／硬著陸比例

- **原始研究**：Alan Blinder,《Landings, Soft and Hard: The Federal Reserve, 1965–2022》,
  *Journal of Economic Perspectives*, Winter 2023, 37(1): 101–20。
  來源：https://www.aeaweb.org/articles?id=10.1257%2FJEP.37.1.101 ・ https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.37.1.101
- **樣本**：1965 年以來 **11 次貨幣緊縮循環**。
- **分類定義**：soft（無衰退）／softish（GDP 收縮 < 1%）／hard（收縮更大）。
- **計數**：⚠️ **兩個二手摘要互相衝突，未能核對原文，兩者都列出**：
  - 版本 A：11 次中 **7 次「相當軟」**，另 3 次本來就無意軟著陸 → 7 軟 / 3 硬。
  - 版本 B：Blinder 以較寬鬆定義認為 **11 次中有 5 次**跟著不同程度的軟著陸。
  - **Blinder 本人的結論方向一致**：只要軟著陸標準不過度嚴苛、且 Fed 確實有意軟著陸，Fed 的紀錄**比一般認知好**。
- **Powell 常引用的三次軟著陸**：**1965（3.4%→5.8%）、1984（9.6%→11.6%）、1994–95（3%→6%）**，三次都未引發衰退。
  Powell 未提的硬著陸包括 **1973–75、1990–91、2001** 三次由緊縮觸發的衰退。
  來源：https://www.independent.org/article/2022/04/12/the-altimeter-for-powells-soft-landing/ ・ https://www.cato.org/blog/brief-history-hard-soft-landings-3

---

## 第五節：哪個案例最像現在、哪裡不像

### 最像：**2011 年 ECB**（可比性最高）

**像的三條**
1. 衝擊性質相同：都是**地緣政治造成的原油供給端衝擊**（2011 阿拉伯之春／利比亞，2026 伊朗／荷姆茲海峽），
   且都把 Brent 推上三位數（2011 年均 $111.26；2026 年 9 月 >$105）。
2. 政策邏輯相同：**整體通膨被能源推高、核心相對溫和，央行仍以「二輪效應／信譽」為由升息**。
   2011 年 ECB 幕僚與 SPF 預測顯示通膨在預測期內大致受控，Trichet 仍在 4 月、7 月各升一碼。
3. 市場的敘事也相同：當下已有經濟學家直接把 2026 ECB 升息稱為「重演 2011 錯誤」，
   2011 的教訓正被即時套用（Bloomberg, 2026-06-08）。

**不像的三條**
1. **2011 的背景是主權債務危機**：義大利、西班牙公債殖利率失控、銀行融資凍結、財政緊縮同步進行。
   2026 年**沒有同等級的系統性金融壓力**——ECB 那次是「升息踩進金融危機」，不只是「升息踩進供給衝擊」。
2. **「核心溫和」的前提在美國並不成立**：2011 歐元區核心通膨貼近甚至低於目標；
   2026 美國核心 PCE **3.3%**，明顯高於 2% 目標。核心 CPI 2.4% 看起來溫和，但那是被 PCE 反駁的那一半（見第三節）。
3. **政策空間完全不同**：2011 ECB 從 1.00% 起升、已近當時的有效下限、沒有 QE 與 OMT 之類後盾；
   2026 Fed 是從遠高於零的水準操作，要回頭降息的空間充足。錯了的修正成本不同量級。

### 次像：**2004–2006 年 Fed**（正面樣本）

**像的三條**
1. 油價持續上行（WTI 年均 $56→$66→$72），整體通膨被能源推高。
2. **核心 CPI 全程受控在 2.1–2.7%**，Fed 明確以「防止能源成本外溢到廣泛通膨」為由**連 17 次會議升息**。
3. **當下沒有出事**：2006 下半年油價回落、整體通膨降溫，股市 2006 年還漲 16%。

**不像的三條**
1. **油價的性質相反**：2004–06 是中國需求拉動的**需求面漲價**，不是供給被切斷；需求面漲價對央行是「經濟強」訊號，供給衝擊是「經濟弱 + 通膨高」的兩難。
2. **政策位置不同**：Fed 是從 1% 的緊急低點以「measured pace」**正常化**，並非把利率推進限制性領域；2026 是在已經偏緊的水準上再加。
3. **後來的衰退與油價無關**：2007-12 的衰退來自房市與信用，用 2004–06 說「升息熬過油價衝擊沒事」會誤導讀者忽略真正的風險來源。

### 第三像：**1990 波灣**

**像的兩條**：地緣供給衝擊、整體通膨跳升但核心沒有螺旋化。
**不像的三條**：(1) **Fed 當時是降息不是升息**，方向相反；(2) 衰退在油價衝擊**之前**（1990-07）就已開始，
所以不能當成「升息造成衰退」的案例；(3) 油價回落極快（1991 Q1），衝擊持續時間遠短於現在已延續兩個月以上的局面。

### 明確**不該**拿來類比的

- **2018**：油價是**崩盤**不是飆漲，Fed 升息的驅動因素完全不同。只能拿來說「Fed 過緊、市場抗議、次年轉向」這條政治經濟學，不能拿來談油價。
- **2022**：核心通膨當時約 6%，**不滿足「核心溫和」前提**，用它會讓整篇類比失效。
- **1973 / 1979**：核心通膨處於大通膨時代高檔，通膨預期已脫錨，制度環境（工資指數化、匯率制度）與今日無可比性。

---

## 第六節：未取得清單

1. **所有案例的事件日起算 3 / 6 / 12 個月精確報酬**：僅取得 Ameriprise 的 5 個 12 個月數字（口徑是否含息未查證）與各年度報酬。原因：FRED / EIA / multpl / stooq / Ameriprise / Seeking Alpha 皆被 egress proxy 擋（WebFetch 與 curl 均失敗）。
2. **各案例當時的 10 年期美債殖利率水準與變動**：除 2018 年 11/12 月（3.12% → 2.83%）外全部未取得。
3. **美元指數（DXY）年度表現**：1990、2000、2005–06、2011、2018 全部未取得。2018 有來源給出「120→128，+6.66%」，但該數值明顯不是 DXY 口徑，已判定不可用。
4. **黃金**：1990、2000、2018 僅有互相衝突的片段（2018：−1.6% vs −3.4%）；1990/2000 未取得。
5. **1999–2000 Fed 利率路徑**（一般紀錄為 4.75%→6.50%）未能取得直接出處。
6. **2000、2001 年 S&P 500 年度報酬**未取得。
7. **2018 年核心 PCE 具體數值**未取得。
8. **2022-03 Brent 盤中 $139** 未能證實；僅確認 2022-03-08 收盤峰值 $123.64。
9. **「油價半年內漲 30%+ → 後 12 個月 S&P 平均報酬與衰退機率」的專門研究**：未取得。唯一相近的 Kedia Advisory 統計（7 次、平均 +24%、6/7 為正）僅見二手轉述，事件定義不明。
10. **「核心 PCE > 核心 CPI 倒掛」與後續 12 個月股債報酬的研究**：**查無**（第三節已明寫）。
11. **Blinder 論文的精確軟／硬著陸計數**：二手摘要衝突（7 軟/3 硬 vs 5 軟），未能取得原文核對。
12. **Euro Stoxx 50 2011 年報酬**：−15.26% 與 −17% 兩個數字未能對齊，且價格報酬／總報酬口徑不明。

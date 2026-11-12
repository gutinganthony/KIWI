# 週掃描 2026-11-06 ～ 11-12（特查輝達）

> 研究日：2026-11-12（台灣）。方法：只用 WebSearch／WebFetch。
> 狀態定義：**兩源**＝兩個以上獨立來源一致；**待確認**＝只有一個來源，或是搜尋摘要沒能抓到原文；**矛盾**＝來源數字或說法互相衝突。
> 抓取限制：多數新聞站在本 session 無法 WebFetch（DNS 被擋：investor.nvidia.com、heygotrade、stocktitan、thestreet、cboe、npr、house.gov 等），CNN 回 451。能直接讀到原文的：SEC EDGAR、CNBC、NBC News、中央社、FRED。標示「搜尋摘要」的條目，代表只看到搜尋引擎的摘要，沒讀到原文。
> 美股指數收盤（SPX／NDX／SOX／VIX）一律取自 FRED 的資料檔，最權威。
> 撰寫者註：本稿由 Anthropic 的 Claude 產出；第 7 節有 Anthropic IPO，讀者請自行評估利益關係。

---

## 0. 本週最大事件（背景所列的事項之後才發生）

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 11/12 | **黃仁勳辭去輝達總裁、執行長及董事，即刻生效。** CFO Colette Kress 暫代 CEO（同時續任 CFO）。Harvey C. Jones 出任公司「史上第一位」董事長（1993 年進入董事會，前 Synopsys CEO）。董事會將從內部及外部人選中找正式 CEO。**Q3 財報日期不變：11/17 美西約 1:20pm 發布，2pm 開電話會議。** | SEC 8-K https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000082/nvidiaannouncesceotransiti.htm ；CNBC live https://www.cnbc.com/2026/11/12/nvidia-jensen-huang-ceo-live-updates.html ；Al Jazeera https://www.aljazeera.com/news/2026/11/12/ai-titan-jensen-huang-out-as-nvidia-ceo ；Newsweek https://www.newsweek.com/jensen-huang-resigns-from-nvidia-after-affair-scandal-12704855 | **兩源**（含官方 8-K） |
| 11/11 晚（美東） | 據報導，觸發辭職的是《紐約時報》11/11 刊出的第二段婚外情報導（對象是一位向他直屬匯報的輝達主管；CNBC 頁面點名為醫療事業副總）。NVDA 盤後 −8.61%。 | CNBC live（同上）；搜尋摘要：NPR https://www.npr.org/2026/11/12/nx-s1-6037833/jensen-huang-nvidia-stepped-down ；Yahoo live https://finance.yahoo.com/markets/live/stock-market-today-wednesday-november-11-dow-sp-500-nasdaq-nvidia-treasurys-veterans-day-140638547.html | 「有第二段關係」：**兩源**。對象姓名和盤後 −8.61%：**待確認**（姓名只見 CNBC，NYT 原文沒有讀到；這屬於私德指控，寫作時要謹慎） |

---

## 1. 輝達（NVDA）

### 1a. 財報與市場預期

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 10/28 公告 | FY27 Q3（10/25 結束）財報訂在 **11/17（二）美股盤後**：約 1:20pm PT 發布，2pm PT（台灣 11/18 早上 6 點）開電話會議。**不是 11/18。** 11/12 的 8-K 重申日期不變。 | NVIDIA IR https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Sets-Conference-Call-for-Third-Quarter-Financial-Results/ （搜尋摘要）；SEC 8-K（同上，有讀到原文） | **兩源** |
| 8 月財報時 | 公司給的 Q3 營收指引：**$108B ±2%**（$105.8–110.2B），**不含中國資料中心營收**。 | 搜尋摘要：Yahoo https://finance.yahoo.com/markets/stocks/articles/expect-nvidias-next-quarterly-earnings-151739351.html ；effectstory https://effectstory.com/en/articles/nvidia-2027-revenue-growth-70-percent-supply-chain-full | **兩源** |
| 預估 | Q3 營收共識：$108.8–109.0B（多家），但 Chartmill 是 $111.36B。 | 搜尋摘要：MarketPulse https://www.marketpulse.com/markets/nvidia-nvda-q3-earnings-preview-ai-spending-risks-and-governance-concerns-threaten-major-uptrend/ ；Chartmill https://www.chartmill.com/stock/quote/NVDA/estimates | **矛盾**（$109B 附近較多來源採用） |
| 預估 | Q3 EPS 共識 $2.47–2.49，Chartmill 為 $2.53。 | 同上 | **矛盾**（差距小） |
| 指引 | 毛利率：公司指引 Q3 約 74%（Q2 約 75%），主因記憶體成本飆升。有一篇前瞻稿說 Q4 可能降到 71–72%（這是分析師推估，不是公司指引）。 | 搜尋摘要：MarketPulse（同上） | 74% 指引：**待確認**（只有一源）。71–72%：**待確認** |
| 預估 | 資料中心營收共識：**沒找到**。Q2 參考值：總營收 $96.2B（+106%），資料中心 $89B（+117%）。 | 搜尋摘要：MarketPulse | **待確認** |
| 預估 | Q4（下季）營收指引共識：**沒找到**。全年 FY27 共識有 $411.6B 和 $418.7B 兩個數字。CFO 先前說 FY28 營收約成長 70%。 | 搜尋摘要：taekim substack https://taekim.substack.com/p/nvidia-blows-away-wall-streets-2027 ；effectstory（同上） | Q4 共識：**待確認**。FY27 共識：**矛盾** |
| 11/10 | 選擇權隱含的財報波動約 **±10.6%**，高於 10 年平均 ±7.8%（資料出處：EarningsWatcher）。注意：這是 CEO 辭職前的數字，現在很可能更高。 | 搜尋摘要：MarketPulse（同上） | **待確認**（只有一源） |
| 背景 | 輝達以約 $12.9B 收購 Hugging Face（9/3 宣布，預計 2027 上半年完成）。Reuters 10/28 報導 DOJ 正在詢問相關競爭影響，但不是正式訴訟。 | 搜尋摘要：Channel Insider https://www.channelinsider.com/ai/news-nvidia-hugging-face-acquisition-doj-antitrust-scrutiny/ ；PYMNTS https://pymnts.com/cpi-posts/nvidias-12-9-billion-hugging-face-deal-draws-justice-department-questions | **兩源** |

### 1b. 黃仁勳／Alice Huang／國會（時間軸）

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 10 月底或 11/6 | NYT 報導美方官員懷疑 Megaspeed（新加坡的輝達晶片買家）高層 Alice Huang 是中國國安部吸收的情報資產。第一篇報導的日期，各家說法不同。 | CNBC https://www.cnbc.com/2026/11/08/jensen-huang-nvidia-china-spy-congress.html （寫 11/6）；搜尋摘要寫「late October」 | **矛盾**（首報日期） |
| 11/4（信件日期） | 眾院共和黨三位委員會主席 Brian Mast、John Moolenaar、Rick Crawford 去信，要求黃仁勳 **11/18**（財報隔天）出席閉門簡報，並揭露防範間諜的內控。這是自願簡報的邀請，不是傳票。11/11 是回覆期限。 | CNBC（同上，寫 11/5 發出）；house.gov 信件 PDF https://chinaselectcommittee.house.gov/sites/evo-subsites/selectcommitteeontheccp.house.gov/files/evo-media-document/nvidia-letter-pdf.pdf （標題 November 4）；Axios https://www.axios.com/2026/11/07/jensen-huang-nvidia-congress-china | **兩源**（11/4 或 11/5 的一天差異是寄出日和信件日不同） |
| 11/7 | 民主黨參議員 Chris Coons（1 月起將任參院外委會主席）在 X 上說國會「will investigate」。眾議員 Seth Magaziner 要求商務部長 Lutnick 跟黃仁勳一起作證。共和黨參議員 Cornyn 也批評。追查是跨黨派的。 | CNBC 11/8（有讀到原文） | **待確認**（目前只有 CNBC） |
| 11/8（日） | 董事會宣布獨立調查，由獨立董事委員會負責，並聘外部律師（CNBC 稱是 Wachtell Lipton）。董事會說「沒有理由相信」國安或公司機密外洩。黃仁勳發員工信，承認婚外關係並道歉。公司當時表示他會續任 CEO。 | CNBC 11/8；NVIDIA 董事會聲明 https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors ；NPR（搜尋摘要） | **兩源** |
| 11/12 | Moolenaar 說黃仁勳已同意向委員會簡報，時間還在協調。Mast 說最快下週作證，談不攏可能發傳票。Warren 說輝達「仍欠國會答案」。NBC 已稱他為「前 CEO」。 | NBC https://www.nbcnews.com/tech/tech-news/jensen-huang-agrees-brief-congress-interactions-alleged-spy-lawmaker-s-rcna608990 ；CNBC live | **兩源** |
| 11/12 | Axios 報導：今年川普三度核准打擊 Megaspeed 的晶片轉運（5 月、8 月、11/5），每次都被商務部長 Lutnick 擋下。白宮回應對 Lutnick「完全信任」。Megaspeed 向輝達買的晶片金額，一說約 $4B，一說超過 $4.8B。 | BNN Bloomberg 轉 Axios https://www.bnnbloomberg.ca/business/company-news/2026/11/12/lutnick-stalled-trump-crackdown-on-diversion-of-nvidia-chips-to-china-axios-reports/ ；Gadget Review https://www.gadgetreview.com/howard-lutnick-reportedly-delayed-nvidia-chip-export-controls-three-times-despite-trump-sign-offs ；CNBC live | 報導內容：**兩源**。採購金額：**矛盾** |
| 11/12 | 川普在 Truth Social 發文，主張由 Tim Cook 接任輝達 CEO（「A Legend replaces a Legend!」）。背景：另有報導說蘋果 9 月已宣布由 John Ternus 接替 Cook。 | CNBC live（有讀到原文）；Cook 卸任：搜尋摘要 freepressjournal https://www.freepressjournal.in/world/tim-cook-is-an-incredible-guy-trump-praises-apple-ceo-in-lengthy-truth-social-post-after-resignation-announcement | **待確認**（川普這則貼文只有 CNBC 一源） |
| 11/6–11/12 | 黃仁勳本週沒有訪台或訪韓的報導，也沒有對 AI 監管或資料中心暫停的公開發言。他唯一的公開文字是 11/8 的員工信（內容是道歉，沒提 Megaspeed 和 Alice Huang 的名字）。 | 多次搜尋（中英文）都沒有結果 | **待確認**（沒找到不等於不存在） |
| H200 中國 | 本週**沒找到** H200 出口的新進展。背景：2025/12 川普准許 H200 賣給經核准的中國客戶，美方抽 25%。2026/1 BIS 公布框架。2026/2 拿到第一張少量許可。GTC 時黃仁勳說已拿到多家客戶許可並重啟生產。5 月報導指北京方面卡住出貨。Q3 指引不含中國資料中心營收。 | 搜尋摘要：TechRepublic https://www.techrepublic.com/article/news-nvidia-h200-ai-chip-sales-china-stalled/ ；Bloomberg Law https://news.bloomberglaw.com/international-trade/nvidia-gets-us-license-for-small-amount-of-h200-exports-to-china | 背景：**兩源**。11 月新消息：**待確認** |

### 1c. 輝達股價

| 日期 | 收盤／變動 | 來源 | 狀態 |
|---|---|---|---|
| 10/6 | 收盤歷史高點 $239.24 | CNBC live；StockStory（搜尋摘要） | **兩源** |
| 11/5 | −9.3%（同日 SPX −4.4%） | 搜尋摘要：heygotrade https://www.heygotrade.com/en/news/nvidia-nvda-stock-news-november-6-2026/ | **待確認** |
| 11/6 | $186.64（+2.78%）；另一源寫 $186.71（+$5.11） | 搜尋摘要：heygotrade https://www.heygotrade.com/en/news/nvidia-nvda-stock-news-november-9-2026/ ；StockInvest https://stockinvest.us/stock/NVDA | **矛盾**（差距很小） |
| 11/9 | $178.67（−4.27%），起因是董事會調查。同日 AMD +13%。 | 搜尋摘要：globalbankingandfinance https://www.globalbankingandfinance.com/nvidia-nvda-falls-2026-11-09/ ；Motley Fool https://www.fool.com/investing/2026/11/09/why-nvidia-stock-was-down-today/ ；CNBC 寫「約 −4%」 | **兩源** |
| 11/10 | 約 $168.9（約 −5.5%）。這是用 11/11 的 $173.73、+2.87% 倒推的，與「Nvidia's 5.5% drop」的報導吻合。 | 搜尋摘要：marketscholars https://www.marketscholars.com/market-outlook-november-10-2026/ ＋自行推算 | **待確認** |
| 11/11 | $173.73（+2.87%），CoreWeave 財報帶動 AI 股反彈。盤後因 NYT 報導大跌。年初至今約 −7%，正走向連續第 6 週下跌（2012 年以來最長）。 | CNBC live（有讀到原文）；Motley Fool https://www.fool.com/coverage/stock-market-today/2026/11/11/stock-market-today-nov-11-nvidia-rebounds-as-coreweave-earnings-reignite-the-ai-trade/ | **兩源** |
| 11/12 盤中 | CNBC：開盤跌逾 13%，市值跌破 $4T，可能是 2025/1 以來最慘的一天，盤中一度約 $160。Yahoo 11:10am ET：NVDA 約 −4.45%，SPX +0.32%。 | CNBC live；Yahoo live https://finance.yahoo.com/markets/live/stock-market-today-thursday-november-12-sp-500-nasdaq-dow-nvidia-invest-110027430.html | **矛盾**（可能是不同時點的快照；收盤待查） |
| 市值損失 | Al Jazeera 說「逾 $600B」；CNBC 說「上週五收盤以來逾 $740B，10/6 高點以來約 $2T」 | 同上 | **矛盾**（計算口徑不同） |
| 分析師 | Baird 降評至 Neutral，目標價 $500→$200。Stifel 目標價 $315→$205，維持買進。FactSet 統計本週至少 10 位分析師轉趨保守。 | CNBC live；Motley Fool 11/11；搜尋摘要：Yahoo | **兩源**（Baird 部分） |
| 受波及 | 輝達概念股：Nebius 約 −17~19%（財報後）、CoreWeave 約 −9~12%、Intel 和 Marvell 跌逾 4%（11/12）。AMD 自週一以來約 +17%，Broadcom +5%。 | CNBC live | **待確認**（只有一源） |

---

## 2. 美國總經與聯準會

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 11/6 | **10 月非農 +165k**，遠高於共識（Dow Jones 59k；其他來源 62k、65k）。失業率 4.1%（下降）。8–9 月合計上修 84k。專業服務 +70k、醫療 +42k。U-6 升到 7.9%（非自願兼職增加 339k）。薪資高於預期。 | BLS https://www.bls.gov/news.release/empsit.nr0.htm ；ABC7 https://abc7news.com/story/us-employers-added-surprising-165000-jobs-october-unemployment-rate-dipped-41/20020018/ ；IndustryWeek https://www.industryweek.com/talent/news/55417255/october-jobs-report-us-adds-165000-jobs-as-unemployment-falls-slightly-to-41 | 數據：**兩源**。共識數字：**矛盾** |
| 11/6 | 市場反應：NDX +1.35%（FRED），SPX 只漲 +0.31%（FRED）。債市大跌。12 月升息機率由約 73% 升到約 77–80%。 | FRED；24/7 Wall St https://247wallst.com/investing/2026/11/07/odds-of-a-december-rate-hike-jump-to-77-after-a-blowout-jobs-report/ ；Benzinga https://www.benzinga.com/node/62998202 | 升息機率：**矛盾**（77% 和 80% 兩說）。Benzinga 說 NDX「+2% 到 27,160」，與 FRED 的 26,989.99 不符，以 FRED 為準 |
| 11/10 | **10 月 CPI：整體 +0.4% m/m**（預期 0.3%），**核心 +0.3%**（預期 0.2%）。9 月整體為 +0.6%。能源 +0.7%、汽油 +1%、電力 +0.9%、食品 +0.5%、住房 +0.3%、二手車 −1.2%。**沒有年增率**：BLS 說 2025 年 10 月政府關門，當月沒有蒐集資料。 | CNBC https://www.cnbc.com/2026/11/10/cpi-inflation-report-october-2026.html （有讀到原文）；Fox Business https://www.foxbusiness.com/economy/cpi-inflation-october-2026 ；Yahoo https://finance.yahoo.com/economy/article/not-great-october-cpi-inflation-data-comes-in-hotter-than-expected-as-food-and-rent-costs-spike-142323507.html | **兩源** |
| 11/10 | 聯準會理事 **Waller**（在倫敦）表示，若 10 月核心 CPI 達 0.3%，他會考慮 12 月**一次升 50bp**，結果數據正好踩線。達拉斯 Fed 總裁 Logan 說「may be possible to move more rapidly」；Fox 引述她認為還需要再升兩碼。 | 搜尋摘要：Reuters 經 Investing.com https://www.investing.com/news/economy-news/investors-boost-odds-of-halfpoint-fed-hike-as-core-cpi-rise-meets-wallers-bar-5016055 ；Kitco https://www.kitco.com/news/off-the-wire/2026-11-10/fed-officials-open-door-half-percentage-point-rate-hike-inflation ；CNBC https://www.cnbc.com/2026/11/10/us-bonds-treasurys-yields.html | Waller：**兩源**。Logan：**待確認** |
| 11/10–12 | 利率期貨：**12 月（12/8–9 會議）升息機率 100%**，升 50bp 機率約 13%（CNBC 寫 13.6%，CPI 前約 0）。2 年債 11/10 單日 +17~18bp，到 4.736%，CNN 稱是 19 個月來最大的債市賣壓。**10 年債 11/12 到 5.068%**（11/10 一度破 5%）。政策利率 3.75–4.00%：10 月會議以 10:2 維持不動；Reuters 提到 9 月曾升息一碼。 | CNBC https://www.cnbc.com/2026/11/12/us-treasurys-bonds-yields.html （有讀到原文）；CNN https://www.cnn.com/2026/11/10/investing/bond-yields-inflation-fed ；FXStreet https://fxstreet.com/news/dow-jones-futures-remain-steady-amid-hawkish-fed-rate-outlook-nvidia-leadership-turmoil-202611120854 | **兩源**（50bp 機率各家在 9~15% 之間） |
| 11/12 | 油價：WTI $86.86、Brent $93.60。11/9 Brent 曾大跌 5.8%，是當天美股大漲的主因之一。 | CNBC 11/12；搜尋摘要：journalarta https://journalarta.com/en/2026/11/10/stock-market-today-sp-500-surges-2-35-to-7549-94-and-nasdaq-jumps-2-74-as-oil-falls-and-vix-drops/ | **待確認**（各只有一源） |
| 下一步 | 10 月 PCE 在 11 月底公布；11 月非農 12/4 公布；FOMC 12/8–9。 | CNBC；BLS | **兩源** |

---

## 3. 民主黨／國會與 AI 資料中心

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 先前提案 | Sanders 和 Ocasio-Cortez 提出《AI Data Center Moratorium Act》：在國會立法保障之前，暫停 AI 資料中心的興建和升級。**目前還卡在委員會。** 期中選舉後 Sanders 再度呼籲立即暫停。 | PBS https://www.pbs.org/newshour/politics/ocasio-cortez-and-sanders-push-bill-to-impose-ai-data-center-moratorium ；DCD https://www.datacenterdynamics.com/en/news/ocasio-cortez-and-sanders-introduce-ai-data-center-moratorium-act/ ；mlq.ai https://mlq.ai/news/democrats-data-center-moratorium-push-gains-momentum-after-midterms-but-congress-remains-a-long-shot/ | **兩源** |
| 選後（11 月） | **共和黨參議員 Josh Hawley 成為第一位支持全國性資料中心暫停的共和黨參議員**：國會通過保障民眾電費不漲的「bill of rights」之前，暫停新建資料中心。細節尚未公布。 | Benzinga https://www.benzinga.com/news/politics/26/11/63172338/first-gop-senator-joins-democrats-in-demanding-nationwide-data-center-moratorium-until-congress-passes-a-bill-of-rights-protecting-americans-from-rising-power-bills ；KuCoin 轉載 https://www.kucoin.com/news/flash/first-gop-senator-joins-democrats-in-calling-for-data-center-construction-moratorium ；TradingView 轉載 | **待確認**（轉載都源自 Benzinga；確切日期也還沒查到） |
| 9/30 | 跨黨派的《Ratepayer Protection Act》在參院表決失敗（沒達 60 票）。民主黨認為它只是「選擇性」規範，不夠強制。 | Al Jazeera https://www.aljazeera.com/news/2026/9/30/us-senate-rejects-bill-targeting-ai-data-centre-electricity-costs ；Newsweek https://www.newsweek.com/ai-data-center-bill-democrats-voting-republicans-list-12509123 | **兩源** |
| 其他 | Markey 7 月提出資料中心能源／污染框架草案。Wyden 提議取消資料中心的聯邦租稅優惠並加徵貨物稅。民主黨參議員 Fetterman 反對暫停，稱那是向中國「舉白旗」。兩黨多數議員仍反對暫停。 | 搜尋摘要：CEPA https://cepa.org/article/midterm-fallout-ai-and-data-centers-take-center-stage ；mlq.ai（同上） | **待確認** |
| 判讀 | 資料中心暫停目前還是「聲量升高、立法機率低」。新國會 1 月才上任。 | 綜合上列 | — |

---

## 4. 美股每日收盤（FRED：SPX、NDX、SOX、VIX；變動率自行計算）

| 日期 | S&P 500 | Nasdaq 100 | 費半 SOX | VIX |
|---|---|---|---|---|
| 11/4 | 7,688.62 | 28,437.17 | 10,268.65 | 16.61 |
| 11/5 | 7,353.73（−4.36%） | 26,629.81（**−6.36%**） | 9,011.14（**−12.25%**） | **28.18** |
| 11/6 | 7,376.86（+0.31%） | 26,989.99（+1.35%） | 9,390.25（+4.21%） | 25.64 |
| 11/9 | 7,549.94（+2.35%） | 27,907.63（+3.40%） | 10,033.93（+6.85%） | 19.92 |
| 11/10 | 7,520.93（−0.38%） | 27,740.80（−0.60%） | 9,998.33（−0.35%） | 19.46 |
| 11/11 | 7,619.38（+1.29%） | 28,374.25（+2.28%） | 10,564.11（+5.66%） | **17.49** |

- 來源：FRED SP500 https://fred.stlouisfed.org/series/SP500 ；NASDAQ100 https://fred.stlouisfed.org/series/NASDAQ100 ；NASDAQSOX https://fred.stlouisfed.org/series/NASDAQSOX ；VIXCLS https://fred.stlouisfed.org/series/VIXCLS 。狀態：**兩源**，背景所給的 11/5 數字（NDX −6.36%、SOX −12.25%）與 FRED 完全吻合。
- **VIX 這段期間從未收上 35**。高點是 11/5 收盤 28.18（單日 +69.7%，1990 年以來第三大單日漲幅），11/11 已回到 17.49，低於 10/30 的 19.42。狀態：**兩源**（FRED；24/7 Wall St https://247wallst.com/investing/2026/11/06/wall-streets-fear-gauge-just-had-its-third-biggest-jump-since-1990/ ）。11/9 的 VIX 有一源寫 20.02，與 FRED 的 19.92 **矛盾**，以 FRED 為準。
- 費半 11/11 有一源寫 +7.32%（10,730），**矛盾**，以 FRED 的 10,564.11 為準。
- 與崩盤前一天（11/4）相比，11/11 的收盤水位：SPX 99.1%、NDX 99.8%、SOX 102.9%（已超過 11/4）。**11/5 的跌幅幾乎全數收復**，但 NVDA 同期仍在破底（自算）。
- 其他：Nasdaq 綜合指數 11/9 收 25,253.14（+2.74%）、11/10 收 25,065.88（−0.74%）、11/11 收 25,466（+1.60%）。道瓊 11/9 收 52,389.75（+2.15%）、11/10 收 52,231.89（−0.30%）、11/11 約 +0.5%。蘋果 11/11 創新高。來源：搜尋摘要 thestar https://www.thestar.com.my/news/world/2026/11/10/us-stocks-close-higher ；WaPo https://www.washingtonpost.com/business/2026/11/10/wall-street-stocks-dow-nasdaq/a8f8d958-dd4c-11f1-912c-4fbb80d73f7f_story.html ；Motley Fool（同 1c）。狀態：**兩源**。
- Cboe 11/9 當週評論標題：「No Contagion (Yet): Equity Vol Spikes, Macro Vol Fades」 https://www.cboe.com/insights/posts/week-of-11-9-2026-no-contagion-yet-equity-vol-spikes-macro-vol-fades （原文讀不到，**待確認**）。

---

## 5. 台股

### 5a. 每日收盤與法人

| 日期 | 加權指數 | 外資（億元） | 三大法人／投信 | 台積電 | 來源 | 狀態 |
|---|---|---|---|---|---|---|
| 11/6 | 39,701.64（電子 −4.93%；早盤一度跌 3,737 點） | 上週外資累計賣超 5,243 億 | — | — | 中央社側欄標題；自由 https://ec.ltn.com.tw/article/paper/1777590 | **待確認**（標題層級） |
| 11/9 | **41,661.70（+1,960.06，+4.94%，史上第二大收盤漲點）**，成交 8,379.29 億；盤中一度漲逾 2,600 點 | 賣超「逾 900 億」 | 三大法人賣超 945.26 億 | 2,235（+100，+4.68%） | 中央社 https://www.cna.com.tw/news/afe/202611090124.aspx （有讀到原文）；ETtoday https://finance.ettoday.net/news/3268934 ；公視 https://news.pts.org.tw/article/834992 | 指數和台積電：**兩源**。法人數字：**待確認** |
| 11/10 | 42,711.92（+1,050.22，約 +2.52%） | **−341.16（連 9 賣，累計逾 8,298 億）**；台積電連 23 賣（−8,181 張） | 三大法人 −117.61 億（華視快訊寫 −148.23 億） | 約 2,285（從 11/11 數字推算） | 中央社 https://www.cna.com.tw/news/afe/202611100353.aspx ；鉅亨 https://news.cnyes.com/news/id/6656700 | 外資：**兩源**。三大法人：**矛盾** |
| 11/11 | **44,257.15（+1,545.23，+3.62%）**，成交 8,491.65 億。三天漲 4,555 點 | −7.66（連 10 賣），買超主力是主動式台股 ETF | 三大法人 +202.56 億（終止連 9 賣）；投信 +147.65 億（連 22 買）。mknews 寫投信 185.85 億、合計 240.76 億 | 2,395（+110，+4.81%），外資買超 6,038 張，終止連 23 賣 | 中央社 https://www.cna.com.tw/news/afe/202611110182.aspx ；經濟日報 https://money.udn.com/money/story/5607/9872013 ；風傳媒 https://www.storm.mg/article/11180589 ；mknews https://mknews.com.tw/2026/11/1016615/ | 指數和外資：**兩源**。投信金額：**矛盾** |
| 11/12 | **43,091.87（−1,165.28，−2.63%）**，成交約 1.01 兆。美股上漲，台股卻逆勢重挫 | −6.84～6.85（連 11 賣，累計 8,312.52 億）；外資大買台玻逾 14 萬張 | 三大法人 +51.6 億 | 2,340（−55，−2.3%）；聯發科 3,850（−140）；南電、景碩跌停；廣達、鴻海、台達電、奇鋐、京元電遭外資調節 | 鉅亨 https://news.cnyes.com/news/id/6660375 ；中時 https://www.chinatimes.com/realtimenews/20261112003016-260410 ；自由 https://ec.ltn.com.tw/article/breakingnews/5637839 ；經濟日報 https://money.udn.com/money/story/5612/9875021 | **兩源**（中時寫 43,097.87，是筆誤） |

### 5b. 國安基金與金管會

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 11/6 | 國安基金第 131 次臨時委員會在盤後召開，決議**授權執行秘書視情況動用資金**。這是史上第 10 次護盤，**上限 5,000 億**（2,000 億以國庫持股擔保借款，3,000 億借用郵儲、勞保、勞退、退撫基金）。 | Newtalk https://newtalk.tw/news/view/2026-11-06/1069763 ；經理人 https://www.managertoday.com.tw/articles/view/73282 ；鉅亨 https://news.cnyes.com/news/id/6650445 | **兩源** |
| 11/9–12 | **實際進場金額：沒有公布或報導。** 執行秘書阮清華表示過去實際動用約 2,000 億，希望把規模擴大到 1 兆，修法還要等三讀。 | Yahoo https://tw.stock.yahoo.com/news/%E5%9C%8B%E5%AE%89%E5%9F%BA%E9%87%91%E4%B8%8B%E5%91%A8-%E9%80%B2%E5%A0%B4%E8%AD%B7%E7%9B%A4-%E9%98%AE%E6%B8%85%E8%8F%AF%E5%AB%8C2000%E5%84%84%E4%B8%8D%E5%A4%A0-%E5%96%8A%E8%A9%B1%E6%93%B4%E8%87%B31%E5%85%86-%E4%B8%8A%E6%BC%94%E8%BB%8B%E7%A9%BA%E7%A7%80-020000916.html | 進場金額：**待確認**（依慣例通常要等季度報告才揭露） |
| 11/6 宣布、11/9 生效 | **金管會限空令（史上第 7 次）**：借券賣出限額由 30% 降到 3%，融券保證金由 90% 提高到 130%。放寬補繳差額的擔保品範圍，並鼓勵公司實施庫藏股、開法說會。**沒有限制平盤以下放空，也沒有調整融資維持率 130% 的追繳門檻。**目前沒有公布結束日期。 | 工商 https://www.ctee.com.tw/news/20261106701936-430301 ；財訊 https://www.wealth.com.tw/articles/c7957424-89b9-4bc8-8eab-516c429f1967 ；鏡週刊 https://www.mnews.tw/story/mm-20261106-185mon-190059 | **兩源** |
| 11/12 | 金管會公布成效：截至 11/11，盤中借券賣出成交值在 163.52～175.15 億之間，實施前一日為 392.7 億。中時以「台股漲幅優於日韓」報導。 | 中時 https://www.chinatimes.com/realtimenews/20261112004244-260410 | **待確認**（只有一源） |
| 融資 | 11/6 上市櫃融資單日減少 564 億，**創單日最大減幅**。11/3 整戶擔保維持率 165.5%，為 3 個月新低（追繳門檻 130%）。11/9 有報導說融資縮減逾 400 億。 | 自由 https://ec.ltn.com.tw/article/paper/1777590 ；自由 https://ec.ltn.com.tw/article/breakingnews/5628533 | **待確認**（單一媒體） |

### 5c. 黃仁勳辭職對台灣供應鏈的初步評估（11/12）

| 事實 | 來源 | 狀態 |
|---|---|---|
| 台新投顧：短期不影響輝達營運和供應鏈架構，但長期可能削弱輝達的競爭力，AMD、博通和雲端業者自研 ASIC 可能受惠。Counterpoint：先進製程需求「遠大於任何一位主管」，對台積電的直接衝擊有限。市場開始重估「創辦人溢價」。後續變數：新 CEO 是否延續生態系投資策略、美國是否藉機收緊對中國的晶片管制。 | 風傳媒 https://www.storm.mg/article/11181112 ；工商 https://www.chinatimes.com/realtimenews/20261112005467-260410 ；經濟日報 https://udn.com/news/story/7240/9875594 ；網路資訊 https://netmag.tw/2026/11/12/nvidia-names-interim-ceo | **兩源**（這些是觀點，不是事實） |
| 台股 11/12 收盤時辭職消息還沒正式公布，盤中反映的是「董事會可能撤換」的傳聞。**正式公告對台股的衝擊，要看 11/13 的開盤。** | 經濟日報 https://udn.com/news/story/7251/9873340 ；8-K 時間 | **兩源** |

---

## 6. 韓股、日股、記憶體

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 11/5 | KOSPI 收 5,059.69（−6.02%），SK 海力士 −10.44%，收 1,132,000 韓元 | 搜尋摘要：stockhub／Korea Times | **待確認** |
| 11/9 | KOSPI 收 5,018.85（−0.81%，外資賣超抹去漲幅）。三星 189,900（+0.64%），海力士 1,136,000（+0.35%） | Korea Times https://koreatimes.co.kr/economy/20261109/kospi-barely-holds-5000-fails-to-regain-momentum ；ad-hoc-news | **兩源** |
| 11/10 | KOSPI +4.39%（約 5,239，由 11/11 數字倒推吻合），日經 +2.87% | Yahoo 奇摩標題 https://tw.stock.yahoo.com/news/%E6%97%A5%E9%9F%93%E8%82%A1-%E6%97%A5%E7%B6%93%E6%94%B6%E6%BC%B22-87-kospi%E6%94%B6%E6%BC%B24-39-085400662.html | **待確認**（只看到標題，日期是推定的） |
| 11/11 | KOSPI 收 5,375.36（+2.60%）。三星 206,000（約 +3.5%），海力士約 1,277,000（約 +5.4%）。JoongAng 稱是「歷史新高」，但 11/4 收盤經倒推約 5,383.8，比 11/11 高。 | JoongAng https://www.koreajoongangdaily.com/business/kospi-jumps-26-as-tech-stocks-rally/12967946 ；TradingKey https://www.tradingkey.com/analysis/stocks/more/262300120-japan-korea-stocks-skhy-kospi-nikkei-samsung-skhynix-softbank-kioxia-nvda-hbm-tradingkey | 漲幅：**兩源**。「新高」：**矛盾** |
| 11/11 | 日經約 61,248.52（+1.31%，可能不是正式收盤），鎧俠和海力士都漲逾 5%，軟銀逆勢下跌 | TradingKey（同上） | **待確認** |
| 11/12 | KOSPI 收 5,342.73（−0.61%），Kosdaq −1.22%，三星和海力士漲跌互見。日經收約 60,819（−0.7%），市場擔心輝達撤換 CEO。 | 經濟日報 https://udn.com/news/story/125066/9874495 ；financefeeds https://financefeeds.com/kospi-steadies-on-samsung-gains-as-nvidia-turmoil-spreads/ ；Yahoo 奇摩 | **兩源** |
| 11/5–11/9 | 美光、SanDisk 一週內跌近 30% | Invezz https://invezz.com/news/2026/11/09/micron-sandisk-stocks-crash-nearly-30-in-a-week-has-ai-selloff-gone-too-far/ | **待確認** |
| 11/11 | **美光 +11.89%，收 $811.30；SanDisk +13.69%，收 $977.69。** 11/12 盤前美光 $790.92（−2.51%）、SanDisk $948.88（−2.95%）。兩檔自 11/5 收盤以來都已反彈逾 20%。 | 搜尋摘要：mexc https://www.mexc.com/crypto-pulse/article/why-were-memory-stocks-up-on-november-11-micron-sandisk-and-seagate-rally-188228 ；Invezz https://invezz.com/news/2026/11/12/micron-sandisk-stocks-fall-nvidia-memory-chip-crisis/ ；FourWeekMBA https://fourweekmba.com/ai-has-memory-peaked-spot-prices-slip-as-micron-rallies-24/ | **兩源** |
| 11/11 | TrendForce：Q4 PC DRAM 合約價季增 13–18%（漲幅比上季收斂），client SSD 漲不到 5%。另一份摘要寫「一般型 DRAM +10–15%、NAND +15–20%」。 | 同上 | **矛盾**（需核對 TrendForce 原稿） |
| 11/3–11/11 | **現貨價走弱**：三大主流 DRAM 現貨均價在截至 11/11 的 8 天內跌 2.1–4.1%，與合約價續漲、股價反彈形成背離。 | FourWeekMBA（同上） | **待確認** |
| 背景 | 美光 FY26 毛利率 81%（FY25 為 40%），10-K 有載。SanDisk 1 拆 8 據報 11/19 生效。 | SEC 美光 10-K https://www.sec.gov/Archives/edgar/data/0000723125/000072312526000023/mu-20260903.htm ；FourWeekMBA | 毛利率：**兩源**。分割：**待確認** |
| 長鑫 CXMT | 本週**沒找到新消息**。背景：7 月在上海科創板 IPO，募資 579.2 億人民幣（約 $8.6B）。 | 搜尋摘要：KuCoin／Yicai https://www2.yicaiglobal.com/news/chinese-dram-chipmaker-cxmt-gets-approval-for-mainlands-biggest-ipo-in-four-years | **待確認** |

---

## 7. Marvell–Lumentum、CoreWeave／新雲、SpaceX、Anthropic

| 日期 | 事實 | 來源 | 狀態 |
|---|---|---|---|
| 11/2 | Marvell 以全股票收購 Lumentum，隱含企業價值約 $115B。每股 Lumentum 換 4.5 股 Marvell（約 $1,132，較 10/28 溢價 23.9%）。合併後 Marvell 股東持股約 67%。綜效逾 $1B／年。首個交易日 Marvell −13%、Lumentum −19%。分析認為 2028 年前無法完成。**11/6–12 沒有監管面的新進展**；11/12 Marvell 跌逾 4%（受輝達拖累）。 | SEC 425 https://www.sec.gov/Archives/edgar/data/0001633978/000119312526455438/d172329d425.htm ；Light Reading https://lightreading.com/ai-machine-learning/marvell-strikes-115b-deal-for-lumentum ；Constellation https://www.constellationr.com/insights/news/marvell-bulks-115-billion-lumentum-acquisition ；CNBC live | **兩源** |
| 11/5–11/7 | CoreWeave 9.625% 2032 年到期公司債殖利率**逾 16%**（另一說「逾 17%」）。5 年期 CDS 超過 1,289bp。股價 11/5 −9.83%，收 $43.66。 | 24/7 Wall St https://247wallst.com/investing/2026/11/07/coreweaves-bonds-now-yield-more-than-16-days-before-earnings/ ；Quartz https://qz.com/coreweave-bond-yield-16-percent-ai-credit-stress-110626 ；Yahoo https://finance.yahoo.com/markets/stocks/articles/coreweave-bonds-now-yield-over-070401546.html | 16%：**兩源**。17% 和 15% 的說法：**矛盾** |
| 11/10 盤後 | **CoreWeave Q3：營收 $3.66B（預估 $3.55B，+168%）**；調整後 EPS $0.95（預估 $1.16）；GAAP 淨損 $709M；backlog $132.5B（6 月為 $104B）；全年營收指引上調到 $13–13.3B；全年資本支出 $37–39B；負債約 $47B（3 個月前 $35.1B）。CFO：「以目前殖利率，2027 年前不再發行母公司層級的無擔保債」，改發以客戶合約擔保的資產層級債（一源稱預期利率 7–7.5%）。過去一個月股價跌逾 40%。 | CNBC https://www.cnbc.com/2026/11/10/coreweave-crwv-q3-earnings-report-2026.html （有讀到原文）；Seoul Economic Daily https://en.sedaily.com/world/2026/11/11/coreweave-beats-estimates-but-debt-costs-mount-as-bond | 財報數字：**兩源**。7–7.5%：**待確認** |
| 11/11–12 | CoreWeave 11/11 一源寫 +16.33%，帶動整個 AI 族群反彈；11/12 約 −9~12%。Nebius 財報（營收年增約 571%，但下修全年營收、上修資本支出）後跌約 17–19%。 | Yahoo https://finance.yahoo.com/markets/stocks/articles/stock-market-today-nov-11-220503244.html ；CNBC live；Investing.com https://www.investing.com/news/stock-market-news/why-is-nebius-stock-tumbling-today-93CH-5022147 | **待確認**（各只有一源；Nebius 財報日期也待確認） |
| SpaceX | 已在 2026/6 掛牌 Nasdaq（SPCX），IPO 價 $135、募資 $75B。11/3 收 $141.31；11/6 一源寫 $134.27（+8.62%），市值 $1.82T。**11/9–12 沒找到新消息。** | NPR https://www.npr.org/2026/06/11/nx-s1-5853199/spacex-is-poised-for-blastoff-with-an-ipo-likely-to-break-records ；Bloomberg Law https://news.bloomberglaw.com/financial-accounting/spacex-seeks-75-billion-in-record-ipo-plan-to-fund-ai-launch ；TradingView／marketchameleon（11 月價格） | IPO：**兩源**。11 月價格：**待確認** |
| 11/10 | **Anthropic IPO**：價格區間 $70–78，發行 8.25 億股。中間價募資約 $61B，全稀釋估值 $1.33T；上緣募資 $64.4B，估值 $1.4T。只用流通股計算（Reuters）約 $1.02T。Morningstar 合理價 $92。5 月那輪估值為 $965B，10 月初華爾街曾喊到 $2T。 | Yahoo https://finance.yahoo.com/markets/article/anthropic-seeks-14-trillion-valuation-in-ipo-130300928.html ；CNN https://www.cnn.com/2026/11/10/investing/weve-never-seen-anything-like-anthropic-ipo ；Forbes https://www.forbes.com/sites/gabrielalinzainescu/2026/11/10/anthropic-ipo-targets-13-trillion-valuation-904-billion-raise/ ；Morningstar https://www.morningstar.com/stocks/anthropic-we-see-stock-undervalued-ipo-pricing-range | **兩源**（估值口徑不同） |
| 定價日 | **預計 11/18 定價、11/19 在 Nasdaq 以「ANT」掛牌**（也就是輝達財報隔天）。CNN 說時間可能變動；CBC 有分析師預期在 11/26 前。 | 同上；CBC https://www.cbc.ca/news/business/anthropic-ipo-9.7418028 ；CNBC live | 11/18、11/19：**兩源**，但仍可能變動 |
| 輝達參與 | CNBC 11/12 說輝達會在 IPO 後「立即」投資 Anthropic $10B。9 月 Reuters 只報導「洽談中，最多 $10B」。**是否已定案，或是否為 2025/11 承諾的那筆錢，目前不明。** | CNBC live；搜尋摘要：the-decoder https://the-decoder.com/nvidia-wants-to-pour-up-to-10-billion-into-anthropics-record-breaking-ipo/ | **待確認** |

---

## 8. 其他「出乎意料、值得寫」的題材

1. **黃仁勳下台，川普推 Tim Cook 接任**：政治人物公開點名民營企業 CEO 人選，背景還有 Lutnick 被指三度擋下晶片管制。這是治理風險與政治風險交織的題材。（Cook 那則：**待確認**）
2. **AMD 本週大約 +17%，Broadcom +5%**：輝達領導層真空，市場開始交易「替代者」。台廠的 ASIC 和 AMD 供應鏈是可以寫的切入點。（**待確認**：只有 CNBC 一源）
3. **AI 遇上升息循環**：Fed 9 月已升息，12 月升息機率 100%，討論 50bp，10 年債超過 5%。這跟過去兩年「降息撐估值」的劇本完全相反。（**兩源**）
4. **台股的內外資對決**：外資連 11 賣、累計 8,312 億；投信連 22 買，主動式台股 ETF 成為承接主力。國安基金和限空令推動 11/9–11 三天大漲 4,555 點，11/12 又回吐 1,165 點。（**兩源**）
5. **AI 信用壓力**：CoreWeave 公司債殖利率 16%，公司宣布 2027 年前不發無擔保債，改走資產擔保。新雲公司的融資模式正在轉向。（**兩源**）
6. **記憶體背離**：現貨價連跌，合約價還在漲，美光股價 $800 以上一週振幅 30%，「記憶體是否見頂」的問題浮上檯面。（現貨價：**待確認**）
7. **VIX 已低於崩盤前水準（17.49）**，SPX 和 NDX 已收復 11/5 的跌幅，但 NVDA 仍在破底。這是指數與龍頭股的背離。（**兩源**，FRED）
8. **一週內的 AI 事件密集排程**：11/17 輝達財報、11/18 黃仁勳原定的國會簡報日（現在改由他個人協調）、11/18–19 Anthropic 定價和掛牌、11/19 SanDisk 分割生效。

---

## 最值得寫的 3 個題材

1. **〈後黃仁勳時代的第一份財報〉**：11/17 財報（營收指引 $108B ±2%、毛利率 74%、隱含波動 ±10.6% 以上）由暫代 CEO Kress 主講。焦點是 Q4 指引和管理層能否穩住客戶信心。台灣供應鏈要分三層看：台積電（衝擊有限）、伺服器組裝和散熱電源（情緒衝擊大）、ASIC 和 AMD 鏈（相對受惠）。11/13 台股開盤是第一個檢驗點。
2. **〈AI 估值的三面夾擊：國會、聯準會、信用市場〉**：Hawley 跨黨派支持資料中心暫停（聲量大、立法機率低）；Fed 12 月必升，10 年債破 5%；CoreWeave 公司債 16% 轉向資產擔保債。這三者疊加在 11/18–19 Anthropic 的 $1.3–1.4T IPO 上。
3. **〈救市一週檢討：國安基金＋限空令 vs. 外資連 11 賣〉**：用數據拆解三天漲 4,555 點、11/12 回吐 1,165 點，以及借券賣出降到不到一半（392.7 億→約 170 億），並對照投信和主動式 ETF 的承接力道，說明護盤效果與可持續性。國安基金實際動用金額未揭露，這一點也要說清楚。

---

## 仍待確認清單

1. NVDA 11/12 收盤價與當日跌幅（CNBC 寫開盤 −13%，Yahoo 寫 −4.45%）；11/10 正式收盤（推算約 $168.9）。
2. 輝達 Q3 資料中心營收共識、Q4 營收指引共識、毛利率 74% 指引的原始出處；CEO 辭職後的最新選擇權隱含波動。
3. NYT 11/11「第二段關係」報導原文；CNBC 點名的主管姓名（只有一源）。
4. 川普「Tim Cook 接任」貼文（只有 CNBC 一源）；蘋果 9 月 CEO 換人一事的確認。
5. 黃仁勳國會簡報的實際日期（原訂 11/18，現在由他個人協調；Mast 提到可能發傳票）。
6. Hawley 支持資料中心暫停的確切日期與原話（Benzinga 原文讀不到）。
7. 國安基金實際進場金額（沒有公開資料）；金管會限空令成效數字（只有中時一源）。
8. 11/9、11/10 外資與三大法人的精確金額（各媒體數字不一）；11/11 投信金額（147.65 億 vs 185.85 億）。
9. KOSPI 11/10 和日經 11/10、11/11 的正式收盤；KOSPI 11/11 是否真的創新高。
10. TrendForce Q4 合約價的原始數字（13–18% vs 10–15%）；DRAM 現貨價跌幅；SanDisk 1 拆 8 的生效日。
11. 輝達 $10B 投資 Anthropic 是否已定案；Anthropic 定價日是否維持 11/18。
12. CoreWeave 財報後的公司債殖利率；資產擔保債 7–7.5% 的利率；Nebius 財報的確切日期。
13. SpaceX 11/9–12 的動態（沒找到）；長鑫 11 月新消息（沒找到）；H200 對中國出口在 11 月的新進展（沒找到）。
14. 黃仁勳 11/6–12 是否有訪台、訪韓行程或對 AI 監管的發言（中英文搜尋都沒有，判斷是沒有，但沒有最後確認）。
15. 網路限制：若要逐條補齊原文，需要在 session 網路設定中放行 investor.nvidia.com、cboe.com、npr.org、thestreet.com、stocktitan.net、heygotrade.com、house.gov 等網域。

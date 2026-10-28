# 查證：AI 的錢從賺來變借來 / 兩種缺（2026-10-28 台灣）

> 方法：WebSearch 為主，SEC EDGAR 與 Yahoo Finance 可直接 WebFetch 取原文；Bloomberg、CNBC、Investing.com、Korea Herald、SK hynix newsroom、Citadel Securities 官網、TradingView、biggo 等在本 session 網路白名單外（無法開啟原文），只能用搜尋摘要＋轉載交叉比對。
> 狀態定義：兩源＝至少兩個獨立來源一致；待確認＝僅一源或只有二手摘要；矛盾＝來源版本不一；查不到＝無來源。
> 日期均為美東/當地日期，除非註明。

---

## A. 融資

### A1. Meta 10/21 Q3 財報
- **2026 capex 指引**｜由 $130–145B 收窄為 **$135–145B**（下緣 +$5B）｜https://letsdatascience.com/news/meta-narrows-2026-capital-spending-range-to-135-billion-145-46f12e07 ｜ https://whtc.com/2026/10/22/metas-credit-risk-indicator-jumps-to-record-high-after-results/ （Reuters 轉載）｜**兩源**
  - 補：SEC FWP（10/26）亦寫 2026 capex $135–145B：https://www.sec.gov/Archives/edgar/data/0001326801/000119312526431036/d116268dfwp.htm
- **Q3 capex**｜約 **$34.9B**（含融資租賃本金）｜https://fourweekmba.com/ai-metas-q3-explained-capex-outran-its-cash-by-2-1-billion/ ｜ https://www.winzheng.com/en/article/meta-q3-2026-capex-exceeds-operating-cash-flow ｜**兩源（皆二手）**；10-Q 僅給九個月累計：購置 PP&E $83.06B、融資租賃本金 $2.77B（https://www.sec.gov/Archives/edgar/data/0001326801/000162828026066773/meta-20260930.htm）
- **營運現金流（Q3）**｜**$32.79B**（10-Q 九個月累計 $96.87B）｜fourweekmba（同上）｜Reuters/whtc（同上）｜**兩源**
- **自由現金流（Q3）**｜**−$2.12B**，2012 年以來首次負值；去年同期 +$10.63B；季末現金及有價證券 $82.45B｜fourweekmba ｜ whtc（Reuters）｜**兩源**
- **是否暫停回購**｜10-Q 顯示 2026 前九個月 **零回購**（Q3 亦為零）；Motley Fool 稱自 2025 Q3 起未再回購。**無「正式宣布暫停」的公告**——正確寫法是「實質停止回購」，不是「宣布暫停」｜SEC 10-Q（上）｜https://fool.com/investing/2026/07/20/meta-platforms-abandon-174-billion-investment-ai ｜**兩源**（措辭須修正）
- **新設無投票權股**｜**Class C 普通股**（公開上市、無投票權），現有 A/B 股每股配發 1 股 C 股（實質 2-for-1）；**生效 2027-01-19**（另有報導稱董事會 10/19 核准）；用途：籌資、員工薪酬、併購，同時保住祖克柏投票權（10/1 時投票權 60.6%、經濟權益 13.4%）。Moelis 估可在祖克柏投票權跌破 50% 前募約 $700B 股權｜https://decrypt.co/381640/meta-non-voting-stock-fund-ai-buildout-zuckerberg-control ｜ https://letsdatascience.com/news/meta-to-create-non-voting-share-class-to-fund-ai-expansion-47201f45 ｜**兩源**（生效日 1/19 僅 letsdatascience 等少數明寫，**生效日待確認**）
- **5 年 CDS 是否創新高**｜是。Markit（Reuters 引）：10/22 收 **114.79bp**（+7.6bp）歷史新高；ICE 盤中最高約 **119.3bp**（+8.9bp）｜whtc（Reuters）｜https://www.kucoin.com/news/flash/meta-s-debt-default-insurance-hits-record-as-ai-spending-rises ｜**兩源；數字因資料商不同而異**（Markit 收盤 vs ICE 盤中），有一源把 114.79 標在 10/23
- **10/22 收盤跌幅**｜收 **$648.85，−6.98%**（−$48.67，前收 $697.52）；另有報導寫「約 −6%、約 $655」（為盤中數字）｜https://www.heygotrade.com/en/news/meta-meta-stock-news-october-23-2026/ ｜ https://www.cnyes.com/ 鉅亨〈美股盤後〉https://news.cnyes.com/news/id/6636334 （同日費半報導，Meta −6.98% 亦見於 thewallstreetrepublic 標題）｜**兩源（收盤 −6.98%）；「−6%」為盤中版本**

### A2. Meta 股權融資規模（950 億 / 975 億 / 250 億五倍 / 輝達 30 億）
結論：**是同一套方案的不同階段/口徑，不是普通單次增資**。結構有三塊：
1. **Class A 普通股（搭配遠期銷售協議 forward sale）**：10/26 啟動 $22.5B → 10/27 定價時**上調至 $25.0B**（4,000 萬股 × **$625**，另有 600 萬股超額配售權）。遠期協議對手 Morgan Stanley、Goldman，交割最遲 2027-11-19，Meta 初始不收現金。
2. **強制可轉換特別股（Mandatory Convertible Preferred, 6.50% Series A）**：2.5 億存託股 × $50 = **$12.5B**（另有 3,750 萬存託股選擇權），約 2029-08-15 自動轉換，代號 METAM。
3. **ATM（市價增發）計畫**：最多 **$60B Class C 股**，Class C 開始交易後（2027 Q1）才啟動，尚未簽約。
- 口徑換算：啟動版 22.5+12.5+60 = **$95B（「最多 950 億」）**；定價上調後 25+12.5+60 = **$97.5B（「975 億」）**；實際已定價的承銷部分 = **$37.5B**（全行使超額配售約 $43.1B）。
- 「**250 億美元股票獲五倍認購**」：有 qz.com 標題「Meta $25 billion stock offering draws about five times demand」（原文網域被擋，無法開啟）；Bloomberg 稱前 15 大買家拿走約 70%、可轉特別股需求為發行量數倍。⚠️注意：2025-10 Meta $30B **公司債**（目標 $25B）也曾有 $125B 訂單「約五倍」，容易混淆。→ **股票五倍認購：待確認（單一來源且未讀到原文）**
- 「**輝達認購 30 億美元**」：**查不到**。SEC FWP 原文是 **NVIDIA、AMD、Broadcom 三家合計表示有意認購「最多 $5.0B」Class A 股，無約束力**；未拆分各家金額。另一報導稱 AMD 計畫投資 $1B（單源）。定價 FWP 未提三家實際認購額。→ 「輝達 30 億」**不可用**，建議改寫為「輝達、AMD、博通合計表態最多 50 億美元（非約束性）」。
- 性質：**不是可轉債**；是「普通股（遠期交割）＋強制可轉換特別股＋未來 Class C ATM」。Class C 是新股別，但 10/27 定價的普通股是 **Class A**。
- 來源：SEC 啟動 FWP https://www.sec.gov/Archives/edgar/data/0001326801/000119312526431036/d116268dfwp.htm ｜ SEC 定價 FWP https://www.sec.gov/Archives/edgar/data/0001326801/000119312526432549/d382225dfwp.htm ｜ https://www.tokenpost.com/news/business/42149 （$37.5B 定價）｜ https://rallies.ai/news/meta-eyes-record-975-billion-equity-raise-to-fund-ai-expansion-c3829f614dc61301 （$97.5B）｜ https://stocktwits.com/news-articles/markets/equity/meta-launches-35-b-stock-offering-plans-another-60-b-program-in-2027-nvidia-amd-broadcom-eye-up-to-5-b-investment/cZU3GQpRByl ｜ https://www.gurufocus.com/news/9143916/meta-platforms-increases-stock-offering-to-25-billion-adds-convertible-preferred-shares-meta
- 狀態：**結構與金額＝兩源（含 SEC 一手）；五倍認購＝待確認；輝達 30 億＝查不到（與一手文件不符）**

### A3. 博通 630 億美元融資（10/26）
- **結論**｜$63B 承諾融資，由**美銀、花旗、摩根士丹利（第一順位/first-lien 安排行）＋黑石（承諾第二順位/second-lien）**提供；新設 **SPV** 用資金購買博通晶片並**租給 Anthropic**；博通提供「**residual value support（殘值支撐）**」為部分融資兜底。
- **數字**｜第一順位約 **$43.5B（69%）**（Reuters 引兩位知情人）；另一報導：約 $42B 貸款＋最多約 $21B 投資級債券，最快明年起發；**交貨 2027 年起**。前一筆為 6 月 Apollo＋黑石約 $35B（報導稱博通為第一筆 $35B 擔保逾 80%；季報揭露最大損失上限 $29B）。
- **設備內容**｜Bloomberg/Yahoo 原文僅寫「chips」；早先報導提及 TPU（與 Google 合作的客製加速器）。**「加速器與網通設備」的說法：待確認**（未見明確寫網通設備）。
- **殘值支撐細節**｜Yahoo/Bloomberg 原文只說「backstopping a portion」，無條款；6 月平台的描述為「殘值與差額保證，違約後轉售晶片仍不足時補足 senior 缺口，junior 先吸收損失」。本次細節：**查不到**。
- **貸方退出**｜Benzinga 報導：部分貸方曾考慮退出，Hock Tan 以**提高利率與加強損失保護**挽回談判（單一來源）→ **待確認**。另有「美銀下調博通債信評估」說法亦單源。
- 來源1：https://finance.yahoo.com/technology/ai/articles/broadcom-arranges-63-billion-deal-203614048.html （Bloomberg 轉載，已讀原文）｜來源2：https://www.marketscreener.com/news/wall-street-banks-blackstone-line-up-63-billion-to-finance-broadcom-chips-for-anthropic-ce785cdcde8dff27 （Reuters）｜補：https://www.benzinga.com/markets/tech/26/10/62608696/broadcom-anthropic-63-billion-financing-banks-blackstone-ai-chips 、https://www.briefs.co/news/broadcom-lines-up-63-billion-to-equip-anthropic-with-banks-p/
- 狀態：**機構/金額/SPV 租賃結構＝兩源；交貨 2027＝待確認（二手摘要）；貸方退出＝待確認；網通設備＝待確認**

### A4. SpaceX × Apollo 約 400 億美元輝達晶片融資
- **結論**｜FT 10/6 首報（Reuters 轉述）：SpaceX 洽談約 **$40B** 債務融資購買輝達晶片，**Apollo 主導**，Pimco 等參與；約 **$10B 銀行貸款＋$30B 投資級債**；預計 **2027 年完成**；Bloomberg 稱談判初期、可能破局；各方未回應。
- **「融資租賃」？**｜**查不到**租賃結構的描述，報導是「債務融資購買晶片」。先前 Apollo 曾透過 Valor 為租給 xAI 的 GPU 叢集做 $3.5B、$3.4B 兩筆融資（那才是租賃式）。
- **Vera Rubin？**｜報導未指明本筆採購型號；僅 SpaceX 8 月財報會議稱「Vera Rubin 架構最好」並只用輝達平台 → 把本筆寫成「Vera Rubin 晶片」屬推論，**待確認**。
- 來源1：https://investinglive.com/stocks/spacex-seeks-40-billion-in-debt-led-by-apollo-to-fund-nvidia-chip-order-ft-says/ ｜來源2：https://www.inside.com.tw/article/42579-spacex-40-billion-nvidia-chips-apollo-debt ｜補：https://technews.tw/2026/10/07/spacex-looks-to-raise-40bn-to-buy-nvidia-chips-in-financing-led-by-apollo/
- 狀態：**$40B/Apollo/結構＝兩源（但均源自 FT 單一原始報導，且未成交）；租賃＝查不到；Vera Rubin＝待確認**

### A5. 美國投資級公司債 2026 發行是否創紀錄
- **結論**｜是。Bloomberg 10/26：年內發行 **$1.76 兆**，超越 2020 年 $1.75 兆紀錄；8 月單月 $145.2B 亦為月度紀錄。
- **AI 占比**｜JPM 資產管理：超大雲端商（hyperscaler）占美元 IG 發行由 2022–24 年約 2% 升至 2026 年預估 **9%**；年初至今 hyperscaler 發 IG 債 **$219B**（含 $62B 非美元）。另估 AI 相關供給約 **$300B**（Morningstar 彙整承銷台，單源）；Herald 稱五大 hyperscaler 前九月發 $230B。→ 「AI 占比」口徑不一（9% vs 300B/1.76T≈17%），**引用需註明口徑**。
- 來源1：https://www.bloomberg.com/news/articles/2026-10-26/ai-funding-needs-drive-us-high-grade-bond-sales-to-annual-record ｜來源2：https://247wallst.com/investing/2026/10/27/ai-is-pushing-corporate-bond-sales-to-an-all-time-record/ ｜JPM：https://am.jpmorgan.com/lu/en/asset-management/adv/insights/market-insights/market-updates/on-the-minds-of-investors/hyperscaler-debt-issuance-ai-buildout/
- 狀態：**創紀錄＝兩源；AI 占比＝矛盾（口徑不同）**

### A6. 三則原話
- **城堡（Citadel Securities）**｜發言人為 **Nohshad Shah（Citadel Securities EMEA 固定收益銷售主管）**，非 Ken Griffin；Bloomberg 10/26 標題：「AI trade leaves 'little margin for error'」，報告題為〈A Narrow Margin of Safety〉。原話大意：市場押注 AI 太重，若支出不回本「幾乎沒有容錯空間」。⚠️ 中文「城堡證券」≠「城堡投資（Citadel 對沖基金）」，兩家不同公司。
  - 「**一些船會沉沒**」：**查不到**任何來源（Shah 或 Griffin 皆無）。Griffin 10/20 在 Citadel「Future of Global Markets」會議說 AI「almost certainly」有泡沫、但倖存者將領先數十年——意思接近但**不是「船會沉」的原話**。
  - 來源1：https://www.bloomberg.com/news/articles/2026-10-26/citadel-securities-shah-says-ai-trade-has-no-margin-for-error ｜來源2：https://investinglive.com/stock-market-update/citadel-securities-warns-ai-trade-has-little-margin-for-error-as-three-risks-converge/ ｜Griffin：https://finance.yahoo.com/news/ken-griffin-almost-certainly-bubbles-122850413.html
  - 狀態：**「little margin for error」＝兩源（但原文英文是 little，不是 no；Bloomberg URL 寫 no）；「船會沉」＝查不到**
- **黑石總裁 Jon Gray**｜約 10/22 稱 AI 需求「**almost parabolic（幾乎是拋物線式）**」，並以 Blackstone 與 Anthropic 合資的 Ode「跟不上客戶需求」為例；強調瓶頸在晶片、電力、資料中心｜https://money.whatfinger.com/2026/10/22/blackstones-gray-says-ai-demand-is-parabolic/ ｜ https://www.odaily.news/en/newsflash/526740 ｜**兩源（皆二手；原話是 "almost parabolic"）**
- **Novogratz**｜10/27 Galaxy Q3 財報會議：信貸市場接近「**peak nervousness / peak anxiety（緊張情緒高峰）**」，市場在「消化不良（indigestion）」，若油價回落會改善；觸因含 CoreWeave 垃圾債殖利率升至困境水準｜https://www.benzinga.com/markets/private-markets/26/10/62640963/galaxy-digital-ceo-mike-novogratz-says-credit-markets-are-near-peak-nervousness-as-ai-spending-surges ｜ https://www.gurufocus.com/news/9145006/galaxy-digitals-novogratz-sees-signs-of-easing-anxiety-in-ai-credit-markets ｜**兩源**（注意 GuruFocus 標題框架是「焦慮見緩跡象」，語氣偏向「快見頂、之後會好轉」）

### A7. 高盛：對沖基金以「兩年來最快速度」拋售科技股（10/22）
- **結論**｜**查不到「兩年來最快」+ 10/22 的版本**。找到的是：高盛主經紀數據，**截至 10/15 當週**對沖基金拋售科技股速度為「**至少十年來最快／2016 年資料起最大比例**」，以多頭平倉為主，半導體金額最大；科技仍占全球主經紀簿 23.5%（五年第 90 百分位），淨槓桿降至 48.6%（一年低）。
- 來源1：https://247wallst.com/investing/2026/10/20/hedge-funds-dumped-tech-stocks-at-the-fastest-pace-in-a-decade-goldman-says/ ｜來源2：https://www.briefs.co/?p=26794 ｜補：https://www.tipranks.com/news/hedge-funds-are-selling-tech-stocks-at-a-record-pace-says-goldman-sachs-gs
- 狀態：**矛盾**（文章版本「10/22、兩年來最快」與查得「10/15 當週、十年來最快」不符；建議改用後者，或另找 10/22 當週新報告）

---

## B. 兩種缺

### B8. Lam Research 10/21 財報（9 月季，FY27 Q1）
- **營收**｜**$8.22B**（季增 22%，前季 $6.72B）；GAAP 毛利率 52.3%、營益率 40.0%；non-GAAP EPS $2.20｜SEC 8-K Ex.99.1 https://www.sec.gov/Archives/edgar/data/0000707549/000070754926000052/lrcx_exhibitx991xq1x2027.htm ｜ https://newsroom.lamresearch.com/2026-10-21-Lam-Research-Corporation-Reports-Financial-Results-for-the-Quarter-Ended-September-27,-2026 ｜**兩源（一手）**
- **財測（12 月季）**｜營收 **$8.60B ± $0.4B**、毛利率 52.5%±1%、營益率 40.5%±1%、EPS $2.33±0.15（共識約 $8.54B/$2.32）｜同上兩源｜**兩源**
- **供應鏈受限原話**｜CFO **Doug Bettinger**：若非「some near-term supply chain constraints that we are actively managing」，財測會「a bit higher / a little bit higher」，部分 12 月季出貨可能延至 3 月。CEO **Tim Archer**：**無塵室空間與部分零組件供應限制，可能使產業在 2027 年無法完全滿足需求**；正與供應商擴產。Lam 預估 2027 WFE > $200B（以 DRAM 為主）。BofA：「supply constrained, not demand constrained」｜https://www.marketbeat.com/instant-alerts/transcript-lam-research-q1-earnings-call-highlights-2026-10-21/ ｜ https://www.benzinga.com/node/62520150 ｜**兩源（皆為轉述，非逐字稿；Archer 逐字原話待確認）**
- **中國占比**｜**35%**（9 月季）｜SEC 8-K（上）｜Stocktwits 標題提「China slowdown looms」https://stocktwits.com/news-articles/markets/equity/lrcx-stock-record-profits-supply-snags-sales-hold-china-slowdown/cZxvH4rRBw4 ｜**一手單源，待確認第二源**
- **10/22 股價**｜收 **$230.15，約 −11.8%（−11.76%）**；盤中曾 −9.68%（$235.57）｜https://thearabianpost.com/semiconductor-shares-plunge-as-lam-flags-supply-constraints/ ｜ https://news.cnyes.com/news/id/6636334 ｜**兩源**
- **同日 KLA / AMAT / ASML**｜
  - AMAT：收 **−8.16%**（鉅亨）；盤中 −6%～−7.4%（247wallst、TIKR）→ 收盤 −8.16% 單源，**待確認**
  - KLA：盤中 −5.27%（$154.82，鉅亨速報）、−9.10%（FX168）；techtimes 稱「至少 −10%」/「逾 −9%」→ **矛盾，收盤未確認**
  - ASML：一說 **−6.93%**，另說「逾 −6%」，盤中 −4.83%／開盤約 −4% → **待確認（以 −6.9% 左右較可信）**
  - 來源：https://www.techtimes.com/articles/329406/20261023/chip-stocks-lose-200-billion-equipment-makers-warning-counters-nvidias-ai-optimism.htm ｜ https://www.fx168news.com/article/1106554 ｜ https://247wallst.com/investing/2026/10/22/lam-research-sinks-9-as-supply-constraints-cap-outlook-applied-materials-drops-6-asml-holding-falls-4/ ｜ https://www.tikr.com/blog/applied-materials-sinks-7-on-lams-outlook-a-bit-higher-wasnt-enough

### B9. SK 海力士 10/28 Q3 財報
- **營收**｜**104.6 兆韓元**（104.6155 兆），季增約 32%、年增約 328%，首度單季破 100 兆｜https://www.aol.com/articles/sk-hynix-q3-profit-jumps-234917000.html （Reuters）｜ https://news.sbs.co.kr/english/article.do?news_id=N1008818926 ｜**兩源**
- **營業利益**｜**83.3 兆韓元**（去年同期 11.4 兆；季增 38%、年增 632%）｜同上兩源｜**兩源**
- **營益率**｜約 **80%**（精算 79.7%）｜SBS（同上）｜ https://404kresearch.substack.com/p/sk-hynix-q3-2026-deep-dive-80-operating ｜**兩源**；淨利約 39.8 兆
- **HBM4**｜Q3 開始全面量產；**HBM4 自 Q4 起成為主力產品**，Q4 HBM4 出貨/營收將超越 HBM3E；長約（LTA）涵蓋 2027–28 年逾 50% 產能；預期記憶體短缺延續至 2030｜https://news.skhynix.com/en/q3-2026-business-results/ （網域被擋，經搜尋摘要）｜ https://www.kucoin.com/news/flash/sk-hynix-q3-revenue-surpasses-100-trillion-krw-for-first-time-hbm4-to-dominate-in-q4 ｜**兩源（二手）**
- **股東回饋（釐清 50–60 兆 vs 250 億美元）**——兩個口徑都對，但指不同東西：
  - **本次（10/28）新宣布**：Q3 每股股利 **20,000 韓元**（10,000 業績＋10,000 來自 Kioxia 投資收益的特別股利），總額約 **14 兆**；新增庫藏股 **20 兆**（其中 10 兆註銷、計入回饋；另 10 兆供員工酬勞、不計入）。→ CNBC 標題「return **$25 billion**」對應的就是這批（14+20≈34 兆韓元，約 $25B，換算為本人推算）。
  - **2026 全年目標**：**約 100 兆韓元**＝現金股利 **≥30 兆** ＋ 庫藏股買回/註銷 **≥60 兆**（含 8 月宣布並已於上週完成的 40 兆）。→ Reuters/Business Recorder 換算「**$75B**」。
  - 「**50–60 兆韓元**」：**查不到此口徑**；最接近的是「庫藏股 ≥60 兆」或「FCF 50% 以上回饋」政策，疑似把兩者混寫。
  - 來源：https://www.cnbc.com/2026/10/28/sk-hynix-third-quarter-profit.html （403 未讀原文，標題）｜ https://www.brecorder.com/news/40446286/sk-hynix-unveils-75-billion-shareholder-return-plan-after-posting-record-profit ｜ https://www.koreaherald.com/article/10917003 ｜ https://news.jkn.co.kr/editions/english/post/1054059
  - 狀態：**100 兆/$75B＝兩源；本次 14 兆股利＋20 兆買回＝兩源；$25B＝單源標題（待確認）；50–60 兆＝查不到**
- **股價反應**｜10/28 盤中**最高 +9.4%**（Reuters）；SBS：11:20 時 +7.9%；TradingKey：約 +4%（疑為 ADR/不同時點）；KOSPI 站上 6,000（Aju）｜Reuters/AOL（同上）｜SBS（同上）｜https://www.ajupress.com/view/20261028153342778 ｜**矛盾（時點不同）；收盤漲幅查不到**

### B10. 三星 Q3 初值與 Bernstein HBM
- **三星 Q3 初值（10/8）營益 107.4 兆韓元**｜**正確**。營收約 195 兆；營益年增 782.5%；營益率 55.1%；首家單季營益破 100 兆的韓國公司；FnGuide 共識營益 106.0 兆、營收 200.3 兆（營收低於預期、獲利略優）；正式財報 10/29｜https://news.samsung.com/global/samsung-electronics-announces-earnings-guidance-for-third-quarter-2026 ｜ https://biz.heraldcorp.com/article/10896441 ｜**兩源（含官方）**
- **Bernstein：三星 Q3 HBM 營收超越海力士（$8.7B vs $7.6B）**｜**有此報告**：Bernstein 以 7–9 月韓國出口資料回歸估算（10/27 前後），三星 **$8.7B（季增 33%）**、海力士 **$7.6B（季增 11%）**；三星估值比其先前預測低約 10%（先前約 $12B）；為**分析師估計，非公司公布**，且是營收反超、非獲利反超。注意 SK 海力士自身 Q3 財報未揭露 HBM 營收絕對值，無法用財報驗證。｜https://www.investing.com/news/stock-market-news/bernstein-says-samsung-overtook-sk-hynix-in-hbm-revenue-in-3q26-93CH-4965188 ｜ https://www.koreaherald.com/article/10915040 ｜**兩源**（⚠️2025 年 Q3 也有一份 Bernstein「三星 HBM 可能超越」報告，數字為 $11.4B vs $5.9–7.5B，勿混用）

### B11. TrendForce Q4 DRAM/NAND 合約價
- **最新官方版本（2026-09-30 新聞稿）**｜4Q26 一般型 DRAM 合約價 **季增 10–15%**；含 HBM 整體 DRAM **15–20%**；NAND Flash 整體 **15–20%**；企業級 SSD **23–28%**（唯一漲幅擴大品項）；驅動為雲端 AI 伺服器，消費端疲弱｜https://www.trendforce.com/presscenter/news/20260930-13258.html ｜ https://technews.tw/?p=1622115 ｜**兩源（含一手）**
- **是否有 10 月上修**｜StockHub 10/20 稱 TrendForce 預估 Q4 DRAM 合約價約 +20%（AI 生成摘要，單源）；9/23 DRAM Market Bulletin 稱已上修 4Q 展望但未給數字 → **10 月新版：待確認**

### B12. 費半 10/22
- **單日跌幅與收盤**｜收 **10,731.98，−773.58 點，−6.72%**；為入夏以來（四個多月）最大單日跌幅、7/29 以來最低收盤；30 檔成分股全數下跌、蒸發約 $200B 市值；同日 Nasdaq −2.60%（26,008.86）、S&P 500 −1.21%（7,663.43）｜https://finance.biggo.com/news/3b93c04b-86b4-4c73-8579-09f063e725eb ｜ https://news.cnyes.com/news/id/6636334 ｜**兩源**
- **主因報導**｜**來源框架不一**：英文來源（techtimes、arabianpost、Pluang）多歸因 **Lam Research 供應鏈受限警告**；鉅亨標題歸因 **Meta 財報重燃 AI 交易恐慌**（capex/負 FCF）；247wallst 另提 Anthropic 執行長週末呼籲放慢 AI 模型進展（單源、未驗證）；背景尚有布蘭特油價 >$113。合理寫法：「Lam 供應受限＋Meta 燒錢＝雙重打擊」｜https://www.techtimes.com/articles/329406/20261023/chip-stocks-lose-200-billion-equipment-makers-warning-counters-nvidias-ai-optimism.htm ｜ https://news.cnyes.com/news/id/6636334 ｜**矛盾（主因雙版本，可並陳）**

### B13. Solidigm 450 億美元美國廠（彭博 10/27）
- **結論**｜**屬實（報導層級）**。Bloomberg 10/27：SK 海力士子公司 Solidigm 與美國商務部洽談在美建 **$45B** NAND 廠，條件是**先獲准將美製設備運往大連廠升級**（大連「Mode B」閒置空間）；Solidigm 稱大連增產可協助為美國廠籌資；並向商務部表示總投資**最高可達 $100B**；紐約州為熱門選址，最快明年動工。背景：美國 2025-08 撤銷三星/海力士中國廠 VEU 資格，改年度許可。Solidigm 回應：全球評估中，尚未決定。SK 海力士 10/22 宣布停止評估 Solidigm 那斯達克 IPO。
- 來源1：https://www.bloomberg.com/news/articles/2026-10-27/solidigm-dangles-new-45-billion-us-plant-to-upgrade-china-site ｜來源2：https://www.koreajoongangdaily.com/business/solidigm-floats-45-billion-u-s-chip-plant-tied-to-dalian-license-bloomberg/12941815 ｜補：https://www.silicon.co.uk/workspace/components/solidigm-us-flash-632052 、https://en.sedaily.com/international/2026/10/28/bloomberg-solidigm-in-talks-with-us-on-45-billion-nand-plant
- 狀態：**兩源（但下游媒體皆轉述彭博單一原始報導；仍屬談判中）**。⚠️ 9 月 Reuters 版本估廠價 $15–30B，與 $45B 不同時期、不同口徑。

---

## 文章需修正的措辭（重點）
1. 「輝達認購 30 億美元」→ 改「輝達、AMD、博通合計表態最多 50 億美元（非約束性）」。
2. Meta 股權融資：$95B 是啟動口徑、$97.5B 是上調後口徑，**其中 $60B 是 2027 才啟動的 ATM 計畫**，已定價的只有 $37.5B；不是可轉債，是「普通股（遠期交割）＋強制可轉特別股」。
3. Meta「暫停回購」→「2026 年至今零回購」（無正式暫停公告）。
4. 城堡：說話者是 Citadel **Securities** 的 Nohshad Shah；「一些船會沉沒」查無出處，建議刪除或改引 Griffin「almost certainly a bubble」。
5. 高盛：應為「截至 10/15 當週、十年來（2016 年有資料以來）最快」，非「10/22、兩年來」。
6. SK 海力士：「250 億美元」＝本次新宣布股利＋買回；全年目標是 100 兆韓元（約 750 億美元）；「50–60 兆」無出處。
7. SpaceX 案無「租賃」與「Vera Rubin」的明確報導，且尚未成交。

## 仍待確認清單
- [ ] Meta Class C 生效日 2027-01-19（需 8-K/proxy 原文）
- [ ] Meta $25B 普通股「約五倍認購」（qz.com/Bloomberg 原文被擋）
- [ ] NVIDIA/AMD/Broadcom 在 Meta 增資的實際認購額（含 AMD $1B 單源）
- [ ] 博通 $63B：交貨 2027 起、是否含網通設備、殘值支撐條款、貸方曾考慮退出（Benzinga 單源）、$21B 債券拆分
- [ ] SpaceX $40B：是否為租賃結構、是否為 Vera Rubin、是否已成交
- [ ] AI 占 IG 發行比重的統一口徑（JPM 9% vs AI 相關約 $300B）
- [ ] Citadel Shah 報告逐字原文；「一些船會沉沒」出處
- [ ] 高盛 10/22 是否另有「兩年來最快」新報告
- [ ] Lam：Archer 2027 無塵室/零件原話逐字稿；中國 35% 第二來源
- [ ] 10/22 收盤：KLA（−5%～−10% 各版本）、AMAT（−8.16% 單源）、ASML（約 −6.9%）
- [ ] SK 海力士 10/28 收盤漲幅；CNBC「$25B」換算口徑原文；「50–60 兆韓元」出處
- [ ] TrendForce 是否在 10 月發布上修版 4Q26 合約價
- [ ] 本 session 被擋網域（需使用者在網路設定放行才能讀原文）：bloomberg.com、qz.com、stocktitan.net、investing.com、citadelsecurities.com、koreaherald.com、news.skhynix.com、tradingview.com、finance.biggo.com、thewallstreetrepublic.substack.com；cnbc.com 回 403

---

## 主對話補註（2026-10-28，對照 Jake 郵箱的彭博盤前簡報）

- **「一些船會沉沒」**：出處是 Jake 轉寄的彭博盤前簡報（10/27 07:08），原文「城堡投資聯席首席投資官警告 AI 融資風險，稱浪潮之下『一些船會沈沒』」。網路查無＝彭博終端獨家，依 Jake 10/20 的指示（彭博報告屬實可用），可引用，出處寫「彭博」。發言人姓名未載，正文只寫職稱。
- **海力士「50–60 兆韓元」**：出處同一份簡報，是彭博轉述《首爾經濟日報》10/26 的**事前預測**（「準備於 10/28 宣布」）。10/28 實際宣布的是 250 億美元股利＋庫藏股。正文用實際宣布值，不用事前報導。
- **Meta「950 億」**：同一份簡報的「尋求最多 950 億美元股權融資」＝啟動時口徑，與本檔 A2 一致。
- **高盛對沖基金拋售**：簡報原文為「上周四以兩年來最快速度拋售科技股」（10/27 刊，上周四＝10/22）。與本檔查到的「10/15 當週、十年來最快」可能是兩份不同的高盛 prime book 報告；正文若用，以彭博簡報版本並標出處，或兩個都不用。

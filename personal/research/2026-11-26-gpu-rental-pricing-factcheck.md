# GPU 租金反轉消息查證：SpaceX Blackwell 現貨價下修（SemiAnalysis，2026-11-25）

- 查證日：2026-11-26（美國感恩節休市）
- 查證者：研究 subagent（只用公開來源）
- **方法限制（重要）**：本 session 的 WebFetch 被網路白名單擋（cryptobriefing.com、finance.biggo.com、news.futunn.com 皆 ENOTFOUND），**所有內容來自搜尋引擎摘要，沒有逐字讀到任何一篇全文**。因此下文所有「引文」都標為「摘要」；要升級成「原文」需人工打開連結核對。
- 標記規則：**【兩源】** ≥2 個互相獨立的公開來源一致；**【單一來源→待確認】**；**【矛盾】** 來源互相衝突；**【查不到】**。
- 利益揭露：本文寫作者是 Anthropic 開發的模型；涉及 Anthropic 的段落只列事實、不評價。

---

## 0. 一句話結論

消息「確有其事、但只有一個上游」：所有媒體都轉述**同一份未公開的 SemiAnalysis 機構客戶報告**，SpaceX 與 Anthropic 皆未證實。數字（$15–15.5 → $10–12、Anthropic 退租約 5 萬顆 H200、SpaceX 以約 $5 轉租）在轉述中高度一致，但**原文無法公開取得**。更關鍵的是：11/24 費半 -7.9% 的主因**不是這則報告**（時序上多數媒體把報告標在 11/25），而是 11/23 黃仁勳復職暴漲後的獲利了結、HPE 融資警告、川普晶片關稅言論等；報告比較像是 11/25 neocloud 續跌的推力之一。

---

## 1. 報告本身

| 查證項 | 結果 | 標記 |
|---|---|---|
| SemiAnalysis 原文是否公開存在 | **沒有找到公開原文**（官網 newsletter、Substack、SemiAnalysis 官方 X 帳號都沒搜到對應貼文）。X 用戶 @SpaceInvestor_D 描述其為「a SemiAnalysis client note that hasn't been made public」（摘要）。https://x.com/SpaceInvestor_D/status/2125578664599302172 | 【查不到原文】 |
| 日期 | JKN、多家轉述稱「SemiAnalysis on Nov. 25」（摘要）。BigGo 則把 11/24 的 neocloud 大跌與 SemiAnalysis 的示警連在一起（摘要）。https://news.jkn.co.kr/editions/english/post/1122628 ・ https://finance.biggo.com/news/3650fded-d702-46d1-83c2-ddf952b8e749 ・ https://456xresearch.substack.com/p/spacex-cuts-blackwell-small-cluster（456X 標 11/25） | 【矛盾】11/24 晚 vs 11/25；多數標 11/25 |
| $15–15.5 → $10–12/GPU-hr | 所有轉述一致（cryptobriefing、Futu、Longbridge、JKN、BigGo、wisevoter、456X、wccftech 標題）。降幅換算 20–35%。但「上一次」有的寫約 $15、有的寫 $15–15.5。https://cryptobriefing.com/spacex-reportedly-slashes-blackwell-gpu-rents-as-anthropic-hands-back-50000/ ・ https://longbridge.com/en/news/306836236 ・ https://wisevoter.com/world/2026/11/25/spacex-cuts-blackwell-gpu-spot-rental-prices ・ https://wccftech.com/spacex-reportedly-slashes-blackwell-gpu-spot-rental-prices-to-10-12-hour-as-anthropic-dithers-on-renewing-its-compute-contract-for-50000-h200s/ | 【兩源】（但上游同一份報告，非獨立驗證） |
| 「與給 Anthropic、Google 的大型叢集價格一致」 | 轉述一致寫「in line with the bulk pricing it offers to major customers such as Anthropic and Google」（摘要）。另見下方 §1a 的交叉推算。 | 【兩源】（同上游） |
| Spot 還是長約 | 轉述一致為**小叢集現貨（spot）**；一篇明確寫「whether long-term contract pricing has moved in step is not established」（摘要）。BigGo 稱長約市場價格仍在上漲（摘要）。 | 【兩源】spot；長約走勢【單一來源→待確認】 |
| Blackwell 指哪一款 | @SpaceInvestor_D 寫「spot rates for **B200 and B300** chips on smaller clusters」（摘要）。SemiAnalysis 模型假設「**GB300** 約 $12/GPU-hr」（多家轉述）。**沒有來源明說 GB200**。 | 【單一來源→待確認】B200/B300 |
| 「上次 AI Cloud TCO Model 更新時租金仍在全曲線上漲」 | 轉述寫「just a few weeks ago when the firm last updated its model, GPU rental rates were still rising」（摘要）。「across the curve」字眼未在可見摘要出現。旁證見 §4（TrendForce 11/19、Ornn 月增、CoreWeave Q3 電話會議）。 | 【兩源】方向屬實；確切措辭【查不到】 |
| SemiAnalysis 自己的解讀 | 不認為市場見頂；模型仍假設 GB300 ≈ $12/hr（≈ $50M/IT MW/年），新報價仍在區間內；不預期拖慢 SpaceX 2027 擴張（摘要）。註：有轉述把「Vera Rubin 定價將顯著高於 Blackwell、不會拖慢 2027 建設」歸給 **NewStreet** 而非 SemiAnalysis——歸屬不清。https://news.futunn.com/en/post/1005674034/bearish-shock-to-compute-markets-rumors-of-slowing-enterprise-token | 【矛盾】觀點歸屬（SemiAnalysis vs NewStreet） |

### 1a. 交叉推算：「Anthropic、Google 大叢集也是 $10–12」合不合理

- Google：SpaceX 向 SEC 申報，Google 每月付 **$9.2 億**、約 **11 萬顆 GPU**、至 2029 年 6 月；2026/12/31 後雙方可 90 天通知解約。https://www.cnbc.com/2026/06/05/google-to-pay-spacex-920-million-a-month-for-xai-compute-capacity.html ・ https://www.datacenterdynamics.com/en/news/google-to-pay-920-million-to-spacex-monthly-for-ai-capacity/ 【兩源】
  - **自行換算**：$920M ÷ (110,000 × 730 小時) ≈ **$11.5/GPU-hr**，落在 $10–12 區間（推算，非公告數字）。
  - 但較早的 SemiAnalysis Weekly Ep.024 摘要稱 Google 合約約「**$14/GB300-hr**、市場均價約 $3」（摘要）。https://semianalysis.com/weekly/episodes/ep-024/ ・ https://firesidealpha.substack.com/p/semianalysis-spacex-can-make-100m → 與「$10–12」**【矛盾】**（可能是計價基礎不同：每 MW 換算 vs 每 GPU）。
- Anthropic：2026/5 起租 Colossus 1；S-1 顯示每月約 $12.5 億、GPU 數各家寫 22 萬～32.5 萬（H100/H200/GB200 混合），換算混合價約 $5.27～$7.78/GPU-hr（推算值，S-1 未揭露分型號價格）。https://www.forbes.com/sites/jonmarkman/2026/05/06/anthropic-just-signed-a-compute-deal-with-elon-musks-spacex/ ・ https://fourweekmba.com/ai-spacex-rents-nvidia-gpus-to-anthropic-at-about-5-27-an-hour/ ・ https://fortune.com/2026/07/19/spacex-ai-compute-renting-business-google-anthropic-pentagon-deals-revenue-valuation-elon-musk-colossus-data-centers/ 【矛盾】GPU 數
  - 混合價包含 Hopper，所以「Anthropic 的 Blackwell 部分約 $10–12」無法從公開資料直接驗證。【單一來源→待確認】

---

## 2. SpaceX 為什麼在出租 GPU

| 事實 | 來源 | 標記 |
|---|---|---|
| SpaceX 於 **2026 年 2 月與 xAI 合併**（全股票，合併估值約 $1.25 兆），取得 Colossus 園區 | CNBC（經搜尋摘要）・ https://www.agenticbrew.ai/news/4f08f479-30a7-4bf8-b013-ddf634c0a7eb/google-spacex-30b-gpu-lease-deal | 【兩源】 |
| 2026 年 6 月 IPO，NASDAQ: SPCX | https://en.wikipedia.org/wiki/Initial_public_offering_of_SpaceX | 【兩源】 |
| Colossus 1 混合架構（H100/H200/GB200）不利訓練 Grok，整座租給 Anthropic 做推論；xAI 訓練移到 Blackwell-only 的 Colossus 2 | https://www.tomshardware.com/tech-industry/artificial-intelligence/musks-colossus-1-ai-supercomputers-inefficient-mixed-architecture-design-couldnt-be-used-to-train-grok-so-anthropics-using-it-for-inference-instead-musk-readies-unified-blackwell-only-colossus-2-for-frontier-training-and-potential-ipo ・ https://thenextweb.com/news/spacex-colossus-1-technical-problems-rented-anthropic | 【兩源】（部分為軼聞性報導） |
| 客戶：Anthropic（約 $12.5 億/月）、Google（$9.2 億/月）、Reflection（GB300，約 $1.5 億/月，7 月起） | 同上 + wccftech 摘要 | 【兩源】Anthropic/Google；Reflection【單一來源】 |
| 規模：Q3 2026 AI 部門營收 **$75.6 億，約佔總營收 52%** | https://cryptobriefing.com/spacex-ai-compute-leases-anthropic-google/ | 【單一來源→待確認】（可查 10-Q） |
| SemiAnalysis 預估 SpaceX 2027 年底達 ~10GW、ARR 可達 $3,000 億（假設半數產能變現） | https://newsletter.semianalysis.com/p/spacex-10gw-in-2027-why-its-real ・ https://www.aicoin.com/en/news-flash/3022693 | 【兩源】（同上游） |
| 財務：11/20 前後發行約 $320 億美元債（最大一檔殖利率 8.259%）；Apollo＋高盛安排約 $440 億債務融資購買輝達 GPU | https://sg.finance.yahoo.com/news/spacex-stocks-drop-6-57-172646022.html ・ https://finance.yahoo.com/markets/stocks/articles/spacex-sinks-11-week-32-090521183.html | 【兩源】$320 億；$440 億【單一來源】 |
| **SpaceX 或 Anthropic 是否回應／否認本次報導** | 搜尋不到任何官方回應或否認；多篇明言「unconfirmed by SpaceX and Anthropic」。 | 【查不到】 |

---

## 3. Anthropic 不續租約 5 萬顆 H200（只列事實）

| 事實 | 來源 | 標記 |
|---|---|---|
| 出處：同一份 SemiAnalysis 客戶報告，經媒體轉述；Anthropic 不續租 SpaceX（Colossus 1）約 50,000 顆 H200 叢集 | cryptobriefing、Futu、Longbridge、wccftech、huggingnews 等 | 【兩源】（同上游） |
| 措辭差異：wccftech 標題用「dithers on renewing」（猶豫續約），其他用「will not renew／hands back／exits」 | 見 §1 wccftech URL | 【矛盾】確定退租 vs 仍在猶豫 |
| SpaceX 以約 **$5/GPU-hr**、**2027 年初交付** 找新租戶 | 同上 | 【兩源】（同上游） |
| 對照：Ornn H200 指數 11/24 約 $6.53（$5 約低於現貨 23%） | https://data.ornn.com/gpu-cloud-price-comparison ・ https://longbridge.com/en/news/306836236 | 【兩源】 |
| 更早背景：曾有賣方報告稱 Anthropic–SpaceX 算力合約不會延長超過 2027 年中／Q2；馬斯克在 X 回應願意收回全部算力 | https://blockspace.media/short/anthropic-reportedly-wont-renew-its-spacex-compute-deal-past-mid-2027/ ・ https://news.futunn.com/en/post/1004245793/anthropic-spacex-compute-deal-reportedly-unlikely-to-last-musk-responds | 【兩源】 |
| Anthropic 公開申報文件稱與 SpaceX 的協議修訂至 10 月，修訂後單價未揭露 | wccftech／fourweekmba 摘要 | 【單一來源→待確認】 |
| **Anthropic 是否說明** | 查不到 Anthropic 對 H200 報導的任何聲明。 | 【查不到】 |
| 背景事實：Anthropic 於 **2026/11/19 IPO**，定價 $83、首日收 $97.17；11/25 CNBC 標題提到其「難以回到 IPO 價之上」 | https://finimize.com/content/anthropics-ipo-popped-even-as-tech-stocks-slid ・ https://decrypt.co/383669/nvidia-amd-micron-ai-stocks-sink-anthropic-ipo-price ・ https://www.cnbc.com/2026/11/25/nvidia-ai-stock-tech-selloff.html | 【兩源】IPO；11/25 股價細節【單一來源】 |

---

## 4. 其他 GPU 租金數據交叉比對

| 指數／報價 | 最新讀數 | 趨勢 | 來源 | 標記 |
|---|---|---|---|---|
| **Ornn B200**（成交指數，Bloomberg ORNNB200） | 11/24 結算 **$9.07**；30 日區間 $9.06–9.94；11 月至今均值 $9.07 vs 10 月 $9.54（約 -4.9% 月減）；較 11/8 高點 -8.8% | 11 月中前上漲、之後回落 | https://data.ornn.com/markets/b200 | 【單一來源】（指數本身為一手數據） |
| **Ornn H200** | 11/24 $6.53；11/21 $6.00；11/22 $5.79；11 月中高點約 $7.75；較 11/11 高點 -16% | 先漲後跌 | https://data.ornn.com/markets/h200 ・ https://data.ornn.com/gpu-cloud-price-comparison | 【兩源】；各頁讀數不一【矛盾】 |
| Ornn B300 | 中文轉述「較近期高點回落 24%」 | 下跌 | https://longbridge.com/zh-CN/news/306839350 | 【單一來源→待確認】 |
| **Silicon Data H100（SDH100RT）** | 11/1 2.93 → 11/8 3.00（11/7 高點 3.04）；11/10 約 $3.06；2025/12/9 約 $2.00 | 一年來上漲約 50%，11 月上旬仍在漲 | https://www.silicondata.com/products/silicon-index/h100 | 【單一來源】；頁面「current $2.53」與表格不符【矛盾】 |
| Silicon Data H200 | 11/24 約 $3.56 | — | https://www.silicondata.com/products/silicon-index/h200 | 與 Ornn $6.53 差很多：方法不同（Ornn 為 neocloud 成交，計法不同）【矛盾】 |
| **SemiAnalysis H100 1 年期合約指數** | 2025/10 $1.70 → 2026/3 $2.35（+~40%）；完整期限結構付費 | 上漲 | https://newsletter.semianalysis.com/p/the-great-gpu-shortage-rental-capacity ・ https://gpu-index.semianalysis.com/ | 【兩源】；11 月最新值【查不到】（付費牆） |
| TrendForce（11/19） | 輝達 GPU 租金攀升；B300 自推出以來漲逾 60%、Hopper 最多翻倍（轉述自 wccftech） | 上漲 | https://www.trendforce.com/news/?p=66804 | 【單一來源→待確認】 |
| CoreWeave Q3 電話會議（11/10） | Ampere、Hopper 價格 Q3 季增 30–50%；2027–28 約 30 萬顆 GPU 到期，按現價重簽年營收可增近 $100 億 | 上漲 | https://s205.q4cdn.com/133937190/files/content_files/CoreWeave-3Q26-Transcript-_1_.pdf ・ https://fourweekmba.com/ai-coreweave-says-expiring-gpus-could-add-nearly-10b-a-year/ | 【兩源】 |
| 輝達代理 CEO Kress：舊 Hopper 重簽「最高達原價兩倍」 | — | 上漲 | https://www.tikr.com/blog/nvidias-interim-ceo-old-hopper-gpus-recontracted-at-up-to-twice-their-original-price-good-news-for-coreweave | 【單一來源】 |
| 公開牌價 B200 | CoreWeave HGX B200 8 卡 $49.24/hr ≈ **$6.16/GPU**；Lambda 約 $4.35–6.69（各追蹤站不一）；Vast.ai 約 $7–7.5（掛單稀少） | — | https://coreweave.com/pricing ・ https://www.spheron.network/blog/nvidia-b200-cloud-pricing-2026/ | CoreWeave 官網為一手；其他【矛盾】 |

**判讀**：
1. 「上次更新時租金仍在全曲線上漲」——**方向屬實**：9–11 月上旬 Ornn、Silicon Data、TrendForce、CoreWeave 都顯示上漲。
2. 11 月中以後 Ornn H200/B200/B300 從高點回落 9–24%，**不只 SpaceX 一家**，有獨立指數佐證「開始回落」。【兩源】
3. 但 SpaceX 降價後的 $10–12 **仍明顯高於** Ornn B200 $9.07、CoreWeave B200 牌價約 $6.2。也就是說，SpaceX 原本的 $15 是「大規模＋短交期」的溢價，這次降價比較像溢價收斂，還不算跌破市場價。

---

## 5. 市場反應（11/23–11/25）

**時序（重要）**：11/23（一）輝達董事會讓黃仁勳復職 → NVDA 單日 +31～33%（Yahoo：2003 年 5 月以來最佳單日；https://www.cnbc.com/2026/11/23/nvidia-jensen-huang-ceo.html）、費半 +14.03%（單一來源 startupfortune）。11/24（二）回吐。11/25（三）續跌，但收盤離低點有段距離。

| 標的 | 11/24（二） | 11/25（三） | 來源 | 標記 |
|---|---|---|---|---|
| 費半 SOX | **-7.88%**（約 8,832），30 檔成分股全跌，MU 約 -11% | — | https://www.kucoin.com/news/flash/u-s-tech-stocks-tumble-as-philly-semicon-index-falls-7-88-nvidia-loses-5-86 ・ https://startupfortune.com/chip-stocks-give-back-the-jensen-huang-rally-as-the-semiconductor-index-drops-79/ | 【兩源】（另有 7.6% 的說法） |
| NVDA | **-5.86%** | 約 -4%（Yahoo 收 $149.30，-3.91%） | 同上 ・ https://www.cnbc.com/2026/11/25/nvidia-ai-stock-tech-selloff.html | 【兩源】 |
| CRWV | **收 $42.61，-11.85%** | Motley Fool 稱週三收約 $42.57（幾乎平盤）；Yahoo 標題「CoreWeave Down 13%」；Robinhood 顯示 $38.37 | https://stockanalysis.com/stocks/crwv/ ・ https://www.fool.com/investing/2026/11/25/coreweave-stock-could-soar-130-according-to-one-wall-street-analyst-even-after-a-price-target-cut-is-it-a-buy/ ・ https://finance.yahoo.com/markets/stocks/articles/spacex-falls-4-coreweave-down-185758049.html | 11/24【兩源】；11/25【矛盾】 |
| NBIS | 盤中約 -12～13%（約 $85.5–86） | 盤前 -6.7～-8.7%，盤中 -12% 約 $76 | https://247wallst.com/investing/2026/11/24/iren-sinks-15-coreweave-tumbles-14-as-neocloud-stocks-backtrack-mondays-rally-nebius-drops-13/ ・ https://www.fxleaders.com/news/2026/11/25/crwv-stock-and-nbis-test-the-last-support-on-neocloud-debt-hpe-margin-risks-warning-for-nebius-and-coreweave/ | 收盤價【查不到】 |
| IREN | 盤中約 -13～15%（約 $12.5） | 查不到 | 同上 24/7 Wall St. | 收盤【查不到】 |
| ORCL | Yahoo 一度顯示 -4.25%（時間不明）；11/23 曾漲約 12% | 查不到 | 同上 | 【查不到】 |
| SPCX | **收 $125.81，-5.7%**（一週 -11%） | Yahoo 標題「SpaceX Falls 4%」（日期不明） | https://finance.yahoo.com/markets/stocks/articles/spacex-sinks-11-week-32-090521183.html | 11/24【單一來源】；11/25【待確認】 |
| Neocloud ETF NCLD | — | 盤前約 -6%；SOXX、SMH 盤前約 -4.6% | 搜尋摘要（tradingkey/longbridge 系） | 【單一來源→待確認】 |
| CoreWeave 2031 年到期債 | 殖利率逼近 18%、創紀錄低價 | | https://coinpaper.com/39419/ai-stocks-crash-as-nvidia-falls-8-broadcom-loses-6-and-core-weave-plunges-over-10 ・ Motley Fool 同上 | 【兩源】 |
| 台股（11/25） | 加權收 38,195，**-1,926.92 點（-4.8%）**，史上第 6 大跌點；盤中最低 -3,440 點；台積電收 2,150（-80，盤中 -210）；前一日 +3,310 點 | | https://www.cna.com.tw/news/afe/202611250068.aspx ・ https://money.udn.com/money/story/5607/9901124 ・ https://finance.ettoday.net/news/3278250 | 【兩源】 |

**新聞是否把下跌歸因於 SemiAnalysis 報告？**
- **11/24 費半 -7.88% 主因（多數報導）**：前一日黃仁勳復職暴漲後的**獲利了結**；HPE 執行長 Antonio Neri 稱其融資部門避免借錢給 neocloud 與高風險 AI 伺服器買家，引發 AI 資料中心融資疑慮（TipRanks 標題）；AI 投資回報疑慮；川普稱進口晶片「兩年後」關稅可達 200%（台媒與 Yahoo 摘要）。https://www.tipranks.com/news/why-hpes-financing-warning-is-pulling-coreweave-iren-and-nebius-lower-after-nvidias-rally ・ https://finance.yahoo.com/markets/stocks/articles/trump-warns-paying-200-percent-195922778.html ・ https://ec.ltn.com.tw/article/breakingnews/5651984 → 【兩源】（多重因素）
  - 註：HPE 那段話在搜尋中只看到 TipRanks／247 摘要，原話未讀到 → 【單一來源→待確認】
- **BigGo 把 11/24 的 NVDA -5.9%、CRWV -11.9%、NBIS -10.7% 歸因於 SemiAnalysis 示警** —— 但多數來源把報告標在 11/25。【矛盾】
- **11/25**：報告＋Ramp 企業 token 支出成長放緩的數據（Futu 稱「先有企業 token 使用增速放緩傳言，再爆 SpaceX 降價」）＋融資／債務疑慮（Coinpaper、FX Leaders）＋高於預期的通膨數據、升息擔憂（CNBC）。https://news.futunn.com/en/post/1005674034/bearish-shock-to-compute-markets-rumors-of-slowing-enterprise-token ・ https://cryptobriefing.com/ramp-ceo-ai-token-spending-slowdown/ → 報告是因素之一，但**沒有來源能單獨歸因**。
- 同日韓股記憶體：SK 海力士約 -11%、三星約 -10%，主因是 **BNP 把美光降評至中立、目標價 $1,700 → $775**，高盛下修三星／海力士目標價（假設 2028 DRAM 價格 -19%）——與 GPU 租金報導無直接因果。https://longbridge.com/en/news/306706015 ・ https://en.bloomingbit.io/feed/news/125207 【兩源】

---

## 6. 分析師與媒體對影響的解讀

### 6a. 偏空解讀
- **Neocloud 經濟模型**：小叢集 spot 降價最傷第二、三線、依賴 spot 的 neocloud（轉述）。GPU 折舊年限各方假設不一：輝達稱 8 年以上、CoreWeave 6 年、Nebius 2026 起從 4 年延長到 5 年、銀行放款多以 3–4 年核貸；Burry 主張經濟壽命 2–3 年。模型試算：若租金年衰減 20%、貸款成本比 64%，第 5 年 DSCR < 1.0x。https://nodiligence.substack.com/p/who-carries-the-gpu-depreciation ・ https://stackedai.net/stranded-gpu-assets-distressed-neoclouds ・ https://albeconca.substack.com/p/the-neocloud-problem 【兩源】（多為部落格／研究筆記，非賣方報告）
- **CoreWeave 重新定價風險**：Intrator 的「到期重簽加 $100 億」是用**現價**計算；有分析指出若供給追上，2027 年重簽價可能低於現價。CFO 稱這些重簽並未計入約 $1,330 億的 backlog。https://www.tikr.com/blog/coreweave-sees-10x-as-much-qualified-demand-as-capacity-as-old-nvidia-chips-reprice-higher 【單一來源→待確認】
- **輝達需求**：主要下行風險是 SpaceX 延後或縮減 Vera Rubin 部署（轉述）；SpaceX 購買 GPU 的融資與輝達下一代晶片綁在一起。【單一來源→待確認】
- **供給面**：BIS 11/16 公布、11/19 生效的「遠端存取先進晶片」暫行最終規則，中文轉述稱「預計將進一步壓低 2027 年現貨租金」（推論歸屬不明）。規則本身：https://www.wilmerhale.com/en/insights/client-alerts/20261117-us-government-restricts-remote-access-to-advanced-ai-chips-and-formally-rescinds-the-ai-diffusion-rule 【規則：兩源；對租金影響：單一來源→待確認】
- **需求面旁證**：Ramp 卡片數據顯示企業 AI token 支出成長在 8–10 月停滯（8–9 月合計約 +1.5%，10 月約 1–2%），但截至 11/15 那週回升（週增支出 +12%、用量 +27.2%）。https://cryptobriefing.com/ramp-ceo-ai-token-spending-slowdown/ ・ https://longbridge.com/en/news/306754361 【兩源】

### 6b. 反方／中性觀點（使用者提的「收斂論」有來源支持）
- **NewStreet Research**：SpaceX 只是**取消小叢集溢價**，讓價格向給 Anthropic、Google 的大叢集價看齊；「A return to normalcy is by no means a collapse」（Futu 轉述，摘要）。【單一來源→待確認】（原報告未公開）
- **SemiAnalysis 本身**：不認為見頂；新價仍在其 GB300 ≈ $12 的模型假設內；不會拖慢 SpaceX 2027 擴張（轉述）。【兩源】（同上游）
- 其他評論：小叢集 spot 已跌到大合約水準，現在下「整體市場轉弱」的結論太早；降價可在新產能上線前拉高既有 GPU 的利用率；單一租戶不續約＋Colossus 擴產，在沒有利用率數據前不足以證明全面過剩（轉述）。https://particle.news/story/spacex-cuts-blackwell-gpu-spot-rates-as-anthropic-returns-50000-h200s 【單一來源→待確認】
- 數據面支持：見 §4 判讀第 3 點——$10–12 仍高於 Ornn B200 $9.07、CoreWeave B200 牌價約 $6.2。

### 6c. 台灣 AI 伺服器供應鏈（廣達、緯創、鴻海）
- **查不到**任何把這則 GPU 租金報導連到廣達／緯創／鴻海營運或目標價的研究報告或新聞。【查不到】
- 已知背景：三大代工廠 Vera Rubin 訂單能見度到 2028（BigGo 摘要）【單一來源】；廣達 2026/7 曾在 AI 賣壓中辦大型現增，毛利率受 GPU 以美元計價擠壓，2026 下半年起轉 consignment 採購以緩解（TechTimes）【單一來源】。https://www.techtimes.com/articles/322022/20260729/quanta-computer-launches-largest-taiwan-equity-sale-decades-ai-selloff.htm
- 11/25 台股重挫的報導歸因是費半 -7.88%、AI 投資回報疑慮、川普關稅言論，**不是**GPU 租金報告本身。
- 推論（研究員意見，非來源）：租金→neocloud 現金流→2027–28 capex→伺服器 ODM 訂單，傳導有 2–4 季落後；短期影響主要在估值與風險偏好。

### 6d. 記憶體
- 同期記憶體賣壓的主軸是「超級循環見頂」辯論（BNP、高盛下修目標價；BNP 把 DRAM/NAND 供需平衡點提前到 2027 年中），**沒有來源把它和 GPU 租金報導直接連結**。【查不到直接連結】
- 反方：SK 海力士稱短缺持續到 2030；TrendForce 預期 HBM4 2027 年報價 $3–5.5/Gb（現約 $2.05）；美光稱 FY27 75% 量已以高於 2026 的價格鎖定。https://www.techtimes.com/articles/331031/20261118/hbm4-memory-price-forecast-trendforce-sees-3-550-per-gigabit-next-year-205-now.htm 【兩源】

---

## 7. 待確認清單（要升級成「原文／兩源」需要做的事）

1. **SemiAnalysis 原文**：客戶報告未公開。需有 SemiAnalysis 機構訂閱者提供原文，才能確認：確切日期（11/24 晚 vs 11/25）、「across the curve」措辭、型號（B200/B300 vs GB200/GB300）、是否明寫「Anthropic、Google 大叢集也是 $10–12」。
2. **Anthropic 退租 5 萬顆 H200**：Anthropic、SpaceX 皆無聲明；wccftech 的「dithers」（猶豫）與其他媒體的「won't renew」（不續約）不一致。可追蹤 SPCX／Anthropic 下一份 10-Q／8-K 或 S-1 修訂。
3. **Google 合約單價**：$14/GPU-hr（SemiAnalysis 早期）vs 推算 $11.5 vs 本次「$10–12」，計價基礎需核對。
4. **11/25 收盤**：CRWV（$42.57 vs -13% vs $38.37）、NBIS、IREN、ORCL、SPCX 的確切收盤價與漲跌幅——建議用 TradingView／Alpha Vantage 拉日線核對。
5. **HPE Neri 原話**與 **川普 200% 晶片關稅**原始出處（CNBC 訪談）。
6. **NewStreet 原報告**（「return to normalcy」）與「Vera Rubin 定價更高」觀點的歸屬。
7. **Ornn B300「較高點 -24%」**、TrendForce「B300 +60%」的原始數據。
8. 台灣供應鏈：等法人報告或 12 月上旬廣達／緯創／鴻海 11 月營收公布後再評估。
9. 網路限制：cryptobriefing.com、finance.biggo.com、news.futunn.com 在本 session 被擋，全文未讀；若要逐字核對，需在 session 網路設定放行這些網域，或改用 Mac 手動開啟。

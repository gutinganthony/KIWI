# 物理 AI（人形機器人/具身智能）投資假設驗證報告

查詢日：2026-07-24 ｜ 方法：主對話 WebSearch/WebFetch ＋ 4 個並行研究 subagent（需求側/供給側/TAM 政策資本/反面證據），共 ~125 次工具查證。多數官網原文（Goldman、Figure、BMW、BofA、NVIDIA IR、rodneybrooks.com、pi.website 等）被 proxy 403 擋——凡標「未直接核對」者為 WebSearch 摘要＋多來源交叉印證，URL 為原始出處。全部 2025-2026 數字均為當日查證，未用訓練記憶補數；查不到標「查無」。

---

## 0. 總判定

**假設「物理 AI 是下一個投資與產業大趨勢」：部分成立。**

| 子命題 | 判定 | 信心度 |
|---|---|---|
| 物理 AI 是未來 5-10 年的結構性產業趨勢（方向） | **成立** | 中高（~70%） |
| 現在（2026）已到規模採用引爆點（時點） | **不成立** | 高（~85-90% 確信未到） |
| 多頭時程（2027-28 大規模上量、2030 百萬台）會如期兌現 | **證據不足，歷史基率偏否** | 低（cobot/AV 前例：實際=預測的 1/5~1/7、晚 8-10 年） |

- **一句話週期**：2026 年處於「試點期」中段（全球有償商業部署僅約 1,500-4,000 台）；產線導入期樂觀 2028（BofA 的「量產起飛點」）、基準 2029-2031；通用化/服務業 2032+；家用普及 2035+。
- **最重要的三個領先指標**：(1) 宇樹掛牌（2026/8-9）後季報的客戶結構——工業營收占比是否 >50%（現在 <10%）；(2) Agility $3 億/約 1,000 台 RaaS backlog 的實際交付轉換率＋西方車廠/3PL 續約擴單；(3) 靈巧手壽命：從 Optimus 的 ~6 週提升到工業標準 30 萬次循環（Brooks 看空論的直接否證點）。
- **對使用者組合的直接含意**：UBS 估單機半導體 BOM ~$1,400（2025）；即使 2030 年出貨 100 萬台（BofA 樂觀情境）＝半導體增量僅 ~$14 億/年，約全球半導體市場 0.2%。**2029 年前物理 AI 對記憶體/半導體基本面是誤差項**；近期受益集中在訓練端（GPU/HBM），已含在既有 AI 資料中心邏輯內。加碼物理 AI 主題與現有重倉高度同因子（AI 情緒/利率），提供的是槓桿不是分散。

---

## 1. 需求側證據（試點 vs 規模採購逐一判定）

### 1.1 Tesla Optimus — 零商業部署、零外售（證據強度：強，官方財報會口徑）
- **2026-07-22 Q2 財報會（最強一手證據）**：Tesla 稱「正在安裝第一代 Optimus 產線」「即將開始生產」，首批機器人用於訓練資料收集與功能開發、非交付客戶；Musk 稱 Optimus 是「Tesla 史上最難量產的產品」（~10,000 個獨特零件）。**截至查詢日量產數＝0、外售＝0。** [CNBC](https://www.cnbc.com/2026/07/22/tesla-tsla-q2-2026-earnings-report.html)（2026-07-22）・[TechTimes](https://www.techtimes.com/articles/321012/20260720/tesla-optimus-production-count-remains-zero-q2-earnings-call-looms-wednesday.htm)（2026-07-20）
- 跳票時間線：2022「2023 production-ready」→2023「年底數千台在工廠工作」→2025 初目標 10,000 台→3 月 all-hands 下修 5,000 台→實際僅造數百台原型，Musk 2026/1 承認**無一台在做 useful work**。[Electrek](https://electrek.co/2026/07/02/musk-shuts-down-optimus-4d-chess-theory/)
- 關鍵人事與工程挫折：Optimus 負責人 Milan Kovac 2025/6 離職（[CNBC](https://www.cnbc.com/2025/06/06/tesla-optimus-robotics-vp-is-leaving-the-company.html)）、2026/1 轉投 Boston Dynamics（[Electrek](https://electrek.co/2026/01/16/hyundais-boston-dynamics-scoops-up-teslas-former-optimus-head-milan-kovac/)）；2025/10 因手/臂設計問題全面暫停組裝與零件採購（The Information 源頭，[TrendForce 轉述](https://www.trendforce.com/news/2025/10/10/news-tesla-reportedly-scales-back-optimus-production-as-hand-design-issues-stall-assembly/)，未直接核對原文）。
- 供應鏈變數：2025/4 中國稀土出口管制直接卡住 Optimus（Musk 2025-04-23 親口證實磁鐵問題；單台需 2-4 kg NdFeB，中國掌控重稀土近 100%、磁鐵產能 ~90%；至 2026/3 未公開確認已解）。[CNBC](https://www.cnbc.com/2025/04/23/teslas-optimus-hit-by-chinas-rare-earth-restrictions-says-musk.html)
- Capex 是真的：Fremont Model S/X 線 2026Q2 拆改為 Optimus 線（設計產能宣稱至 100 萬台/年）。[Electrek](https://electrek.co/2026/04/22/tesla-optimus-production-fremont-model-sx-line/)
- **判定：連試點都算不上（內部原型階段）；目標 vs 實績落差 >90%。「方向認真（真金白銓改線）、時程連年跳票」的典型。**

### 1.2 Figure AI — 估值與部署落差全市場最大（證據強度：中）
- 融資：2025/9 Series C >$1B、投後 $39B（Parkway 領投，NVIDIA/Intel/Microsoft/OpenAI Startup Fund/Bezos 參與；18 個月估值漲 15 倍）。[figure.ai/news/series-c](https://www.figure.ai/news/series-c)（403 未直接核對）
- BMW：Figure 02 在 Spartanburg 的 11 個月試點 2025/11 結束——**現場僅 2 台**、1,250 運轉小時、裝載 9 萬+零件、參與 3 萬+台 X3（[Repairer Driven News](https://www.repairerdrivennews.com/2025/11/25/humanoid-robots-complete-11-month-project-at-bmw-plant/)）。**Fortune 2025/4 調查曾查實現場僅 1 台、在非生產時段練習，與 Adcock「fleet/end-to-end」宣傳嚴重不符**（Adcock 揚言告誹謗，未見後續；[Yahoo/Fortune](https://finance.yahoo.com/news/ceo-heavily-funded-humanoid-robot-185637777.html)）。之後 BMW 仍續擴：Figure 03 物流排序新專案＋萊比錫歐洲首試點（[BMW 官方稿](https://www.press.bmwgroup.com/global/article/detail/T0458778EN/)，403 未直接核對；[The Robot Report](https://www.therobotreport.com/bmw-group-deploys-figure-03-humanoid-after-tests-previous-version/)）。**無任何台數/金額的採購合約公開。**
- 產能 vs 出貨：BotQ 宣稱年產能 12,000 台；實際至 2026/4 累計生產 Figure 03 逾 350 台（公司自報，宣稱產速 1 台/日→1 台/時）；Unitree 招股書第三方估 Figure 2025 全年出貨僅 ~150 台。第二客戶據報 UPS（未證實）。[Figure 官方](https://www.figure.ai/news/ramping-figure-03-production)（403）
- 負面：2025/11 前首席安全工程師 Gruendel 吹哨訴訟（機器人力量可「擊碎頭骨」、無正式安全流程、為 $39B 估值淡化安全；Figure 稱其績效解僱、指控不實）。[CNBC](https://www.cnbc.com/2025/11/21/figure-ai-sued.html)
- **判定：試點（現場個位數台）。$39B 估值對應的可驗證商業部署最少。**

### 1.3 Agility Robotics（Digit）— 西方唯一有公開合約金額者（證據強度：強，SEC 申報）
- GXO：業界首份人形多年期 RaaS（2024 簽）；至 2025/11 累計搬運 10 萬+ totes（單一場址、個位數機器人）。[Agility 官方](https://www.agilityrobotics.com/content/digit-moves-over-100k-totes) ・ [GXO](https://gxo.com/news_article/gxo-signs-industry-first-multi-year-agreement-with-agility-robotics/)
- Toyota 加拿大：2026/2 RaaS，7 台 Digit 進 Woodstock 廠（RAV4）。其他客戶：Schaeffler（投資＋採購協議，台數不明）、Mercado Libre、Amazon（測試）。
- **SPAC 上市（2026-06-24 宣布）**：與 Churchill Capital XI 合併，pre-money $2.5B、募 >$620M、代碼 AGLT；申報文件揭露**已簽約多年期 RaaS 營收 >$3 億、對應約 1,000 台**；2025 年燒現金 ~$1 億、未揭露實際營收；Salem 廠滿載目標年產 10,000 台。Unitree 招股書估其 2025 出貨僅 ~150 台。[The Robot Report](https://www.therobotreport.com/humanoid-maker-agility-robotics-go-public-through-spac-merger/) ・ [SEC Form 425](https://www.sec.gov/Archives/edgar/data/0002074973/000121390026071661/ea029583807-425_church11.htm)
- CEO 上市時公開說「別指望家用機器人很快到來」。[TechCrunch](https://techcrunch.com/2026/07/05/this-humanoid-robotics-company-is-going-public-but-its-ceo-isnt-promising-a-robot-in-your-home-anytime-soon/)
- **判定：實際部署仍試點量級（數十台），但 backlog（~1,000 台/$3 億）是西方陣營唯一可稽核的合約背書。注意 backlog ≠ 交付。**

### 1.4 Apptronik（Apollo）— 試點（證據強度：中）
- 2026-02-11 加募 $520M、估值 ~$5B（Series A 累計 >$935M；Google、Mercedes、Jabil、John Deere、QIA 等）。[CNBC](https://www.cnbc.com/2026/02/11/apptronik-raises-520-million-at-5-billion-valuation-for-apollo-robot.html)
- Mercedes 柏林＋匈牙利 Kecskemét 廠內物流試點（台數未公開；Mercedes 口徑：2025-26 試點、**2027 才可能商業數量交付**）。[Mercedes 官方](https://group.mercedes-benz.com/company/production/procuction-network/mbdfc-humanoid-robots.html) 另有 GXO、Jabil「指定區域」試行；與 Google DeepMind 合作搭載 Gemini。

### 1.5 中國隊 — 出貨量大，結構是關鍵（證據強度：中高，含招股書/年報）
| 公司 | 2025 實績 | 2026 動態 | 結構警訊 |
|---|---|---|---|
| 宇樹 Unitree | 人形出貨 5,500+ 台（招股書自稱全球第一）；營收 ¥17.08 億（+335%）、淨利 ¥2.78-6 億（口徑不一）、毛利率 ~60%；人形 ASP 從 2023 ¥59.3 萬崩至 2025 ¥16.8 萬 | 科創板 IPO 2026-07 註冊獲批（募 ¥42 億、上市前估值 ~¥420 億），預計 8-9 月掛牌；Q1 2026 營收增速降至 68.5%、淨利大跌（SCMP）；2026 出貨指引 1-2 萬台 | **買家主力為科研/教育/開發者/展演；工業部署 <10%**；R1 $4,900、G1 $13,500 是研究平台不是自主工人 |
| 智元 AgiBot | 出貨 5,168 台（Omdia，39% 全球市占第一——與宇樹「第一」互相打架，口徑不同，兩個第一都要打折） | 2026-06-28 累計第 15,000 台下線；騰訊領投、估值 ¥150 億；控股上緯新材布局 A 股；港股 IPO 傳聞未證實 | 出貨含大量資料採集/教育/展演機，工廠實作占比不透明 |
| 優必選 UBTech | Walker 系列 2025 訂單 >¥8 億（訂單≠交付）；交付 >500 台進工廠；**2025 年報：人形營收 ¥8.206 億（+2,203.7%）、占集團 41.1%；淨虧損收窄 32% 至 ¥7.9 億** | 2026 在手訂單 ¥10-12 億（約 2,500-3,000 台）；柳州廠月產能爬坡 600→1,000 台；Siemens 合作目標 2026 產能 1 萬台；客戶含 BYD/吉利/一汽 VW/東風/北汽/Foxconn/順豐/Airbus | 消費機 U1 的 13,361 台「預訂單」被揭露僅需 ¥3,000 可全退訂金（定焦One，[ad-hoc-news 轉述](https://www.ad-hoc-news.de/boerse/news/ueberblick/ubtech-robotics-consumer-humanoid-gamble-faces-twin-threats-price/69763109)）；訂單中關聯方/政府採購占比未披露 |
| 傅利葉 Fourier | 人形出貨量**查無** | GR-3 照護機器人（>¥20 萬）CES 2026 美國首秀；Series E ~¥8 億 | 主力轉向照護 B2B |

- 全球口徑：2025 全球人形出貨 ~13,000-14,000 台、中國占 ~90%；MS 預期中國 2026 出貨倍增至 ~5 萬台（6 月上修後口徑）。[Fortune](https://fortune.com/2026/06/06/chinese-humanoid-robots-global-market-sales-performative-functional/) ・ [SCMP](https://www.scmp.com/tech/article/3358210/morgan-stanley-raises-china-humanoid-robot-shipment-forecast-50000-units)
- **判定：UBTech 最接近「小規模採購」（具名合約金額＋數百台實際進廠）；宇樹/智元是「大量有償銷售但非部署做工」。**

### 1.6 亞馬遜與汽車廠
- Amazon：倉儲自動化主力仍是非人形（Sparrow/Vulcan 等，已部署第 100 萬台）；Digit 僅在 Sumner 研發設施測試；自研多臂 Blue Jay **上線不到 6 個月即於 2026/2 叫停**（無法處理商品多樣性）。[TechCrunch](https://techcrunch.com/2026/02/18/amazon-halts-blue-jay-robotics-project-after-less-than-six-months)
- 汽車廠是第一真實場景：BMW（Figure，個位數台）、Mercedes（Apptronik，試點）、BYD 等中國車廠（UBTech，訂單池一部分）、Toyota 加拿大（Agility，7 台）、NIO（Walker S 2024 起試用）。Xpeng 自研 IRON 宣稱 2026 底量產——目前零部署。

### 需求側總評
- 嚴格定義「有償商業部署」（客戶付費＋現場做生產性工作，排除科研/教育/展演/租賃/廠商自用）：西方 <150 台；中國 1,000-3,000 台（UBTech 為最大單一貢獻者＋宇樹/智元出貨中估 10-25% 真做工）。**全球最佳估計：約 1,500-4,000 台（2026 年中），八成在中國。**
- 可查證的真金白銀合約僅三筆：UBTech ¥8 億訂單、Agility $3 億 RaaS backlog、Schaeffler 採購協議（金額不明）。
- 「規模採購」（單一客戶 >1,000 台）：**全球零例。**「出貨量」與「部署做工量」之間有 ~10 倍落差。
- 2026 年主旋律是**資本化跑在商業驗證前面**（宇樹 IPO、Agility SPAC、智元/Figure 上市動作）。

---

## 2. 供給側 / 技術瓶頸（嚴重度 1-5，5=十年難題）

### 2.1 靈巧手 — 嚴重度 4/5（最硬的硬體瓶頸）
- 壽命是公開硬傷：Optimus 靈巧手壽命約 **6 週**（馬達散熱不足；[futunn 轉述](https://news.futunn.com/en/post/63774097/)，未直接核對）；業界普遍 ~20 萬次循環 vs 工業要求 ≥30 萬次；多數產品實際壽命 1-3 個月。Tesla 2025/10 為手/臂問題停線；Musk 公開稱手占 Optimus 難度 60%；Gen 3 手＝25 致動器/手、22 DOF（Gen 2 的 4.5 倍致動器）。[Basenor 專利解讀](https://www.basenor.com/blogs/news/tesla-optimus-gen-3-hand-patents-revealed-25-actuators-22-dof)
- 現況光譜：Shadow Hand 20 DOF/$110k（研究天花板）；中國旗艦 20+ DOF 帶觸覺 $7,000-28,000；開源 ORCA $1,500-6,100。觸覺已進入密度競賽（單手 1,956 感測元的展示）。供應商放量：因時 Inspire 2025 出貨 1 萬隻（前一年 2 千）、2026 計畫 5-10 萬隻。[Sourcebotics](https://sourcebotics.com/guides/chinese-dexterous-hands-2026-buyers-guide/) ・ [Gasgoo](https://autonews.gasgoo.com/articles/news/from-prototypes-to-production-dexterous-hands-kick-off-a-mass-production-race-2016425582734970881)
- 癥結：「壽命 × 觸覺 × 量產良率」三者同時達標無人做到。手占 BOM ~17%（MS 對 Optimus Gen-2 拆解 ~$9,500/雙）。

### 2.2 執行器/減速器 — 嚴重度 3/5，且在下降（中國 capex 暴力解題中）
- 格局：諧波減速器 Harmonic Drive ~80%、綠的諧波 ~10%（2025 營收 ¥5.7 億、+47%）；行星滾柱絲杠供應基礎更窄（SKF＋少數亞洲廠）、上游螺紋磨床依賴歐日進口。[KraneShares](https://kraneshares.com/humanoid-robotics-in-2026-the-race-from-pilot-to-platform/) ・ [faxiangongchang](https://faxiangongchang.com/en/reports/china-humanoid-robot-supply-chain-2026)
- 降本實績：Tesla 把關節滾柱絲杠採購價從 ~$3,000 壓到 ~$800（-75%）；中系絲杠單元 $800-1,200。擴產：五洲新春規劃 98 萬套產能、貝特科技投 ¥18.5 億。**這是供給側「真 capex」最硬的證據。**
- 判斷：這是產能與精度問題、不是物理原理問題；3 年內從瓶頸變紅海，瓶頸股超額利潤窗口比市場想的短。

### 2.3 電池續航 — 嚴重度 2/5（已降級為營運設計問題）
- 主流旗艦 2-4 小時（Unitree G1 ~2h、Digit ~2h、Figure 03 標稱 5h/2.3kWh）；換電方案成熟：Unitree 快拆 <30 秒、Apollo 換電 <5 分鐘、**Walker S2 可自主走到換電站自換（<3 分鐘）**。廠商標稱值，滿載工況通常打對折。[MANLY Battery](https://manlybattery.com/humanoid-robot-battery-program-guide-2026-outlook-and-beyond/) ・ [Next Humanoid](https://nexthumanoid.com/battery-technology-and-the-24-7-robot-challenge/)

### 2.4 數據瓶頸 — 嚴重度 4.5/5（唯一「路線未知」的瓶頸）
- 學界定調：**Ken Goldberg「10 萬年資料缺口」**（Science Robotics 正式論文）：LLM 等效吃了 10 萬年文本，機器人具身資料量級不存在，未來 2/5/10 年都不會有橫掃式突破，並警告泡沫反噬。[Science Robotics](https://www.science.org/doi/10.1126/scirobotics.aea7390) ・ [Berkeley News](https://news.berkeley.edu/2025/08/27/are-we-truly-on-the-verge-of-the-humanoid-robot-revolution/)（2025-08-27）
- 現況：locomotion 靠 GPU 大規模並行模擬基本解決；**contact-rich manipulation 的 sim-to-real 仍是最頑固缺口**（[Annual Reviews](https://www.annualreviews.org/content/journals/10.1146/annurev-control-031924-100130)）。遙操作 5-50 episodes/操作員小時；採集成本 $340/hr（2024）→$118/hr（2026）（單一來源，弱）。NVIDIA GTC 2026 自己點名示範數據是關鍵瓶頸。
- 龍頭路線公開分歧＝正解未知的證據：智元＝真機遙操作數據工廠（AgiBot World 2026 開源含觸覺）；**Tesla 2025/6 起放棄動捕/VR 遙操作、全面轉純視覺**（工人戴五鏡頭頭盔 8 小時重複做任務）；NVIDIA 押 world model 合成。VC 界自評：機器人處在「GPT-2.5 時刻」（[Bessemer](https://www.bvp.com/atlas/bessemer-predicts-robotics-and-physical-ai)）。

### 2.5 BOM 成本曲線 — 嚴重度 2.5/5（降本可信，斜率分歧大）
- 現況：中系 BOM ~$35k（BofA 2025）；美系工廠試點單機 ~$90-100k；Optimus 目標價 $20-30k（Musk 口徑）。低價端：Unitree G1 $16k、R1 $5.9k——**「能力強的平價研究平台，不是自主工人」**（出廠不會自主走陌生空間/做新穎操作；最吸睛展示為全遙操作）。[BofA Physical AI part 2 PDF](https://institute.bankofamerica.com/content/dam/transformation/physical-ai-part-2.pdf)（403，經 Forbes/futunn 交叉）・[Robotopian G1 拆解](https://robotopian.com/blogs/news/unitree-g1-humanoid-robot-teardown)
- 降本路徑：**BofA：中國製 $35k（2025）→ <$17k（2030）**；Goldman：製造成本已降 40%（其上修 6 倍的依據）；MS 較保守（中低收入國 $50k→$21k 要到 **2050**、並警告算力需求使 BOM 2025-2030 先升 15%）。賣方分歧極大（$17k@2030 vs $21k@2050），不宜取單點。
- 引爆閾值（推論）：工業 BOM <$30k＋2 年回本 → 產線導入期；家用 <$15k → 通用化期。

### 2.6 NVIDIA 生態 — 嚴重度 1.5/5（供給側最成熟的一層；注意賣鏟人立場）
- GR00T N1.6（真機驗證、權重開放）→ **N2**（GTC 2026-03 發表，world action model，自稱新任務成功率為主流 VLA 2 倍+，RoboArena/MolmoSpaces 生成式策略榜第 1——少見的第三方可比訊號；年底可用）。[NVIDIA Newsroom](https://nvidianews.nvidia.com/news/nvidia-and-global-robotics-leaders-take-physical-ai-to-the-real-world) ・ [GEAR Lab](https://research.nvidia.com/labs/gear/gr00t-n1_6/)
- Jetson Thor 2025-08-25 GA（$3,499 devkit）；採用者含 Agility、Boston Dynamics、Figure、Amazon、Meta、Caterpillar；出貨量**查無**（不拆分披露）。2026-06 GTC Taipei 發表 Isaac GR00T 參考人形機（Unitree H2 Plus＋Sharpa 觸覺手＋Thor，2026 底發售）。
- Jensen Huang 口徑演變：CES 2026「物理 AI 的 ChatGPT 時刻 nearly here」（新聞稿寫 "is here"，keynote 實際說 "nearly"——[Axios](https://www.axios.com/2026/01/05/nvidia-ces-2026-jensen-huang-speech-ai) 抓到差異）→ GTC 2026「Physical AI has arrived」。

### 2.7 基礎模型能力躍遷 — 嚴重度 4/5（方向真實、幅度存疑）
- Physical Intelligence：π0.5（2025/4）→π0.6/π*0.6（2025/11，RL 加成）→**π0.7（2026-04-16）：組合式泛化＋零訓練跨硬體**（未見過的 UR5e 雙臂上疊衣，自稱達專家遙操作員水準）。全部自報評估。[π*0.6 論文](https://www.pi.website/download/pistar06.pdf)（站點 403）
- Figure Helix：最強公開證據＝物流分揀直播 **200+ 小時連續自主、~25 萬件包裹、零硬體故障**（自控環境無第三方審計，但連續直播造假成本高，可信度比剪輯 demo 高一級）。[eWeek](https://www.eweek.com/news/figure-03-humanoid-robot-production-helix-ai/)
- Google DeepMind：Gemini Robotics 1.5（跨具身遷移：ALOHA 訓的任務直接上 Apollo/Franka）→ER 1.6（2026-04-14，API 開放＝**任何人可獨立驗證，證據品質最高**）。[DeepMind 官方](https://deepmind.google/blog/gemini-robotics-er-1-6/)
- Skild AI：2026-01-14 募 $1.4B、估值 $14B+（SoftBank 領投）；omni-bodied 主張；營收 0→~$30M；公開 benchmark 最少、證據最弱。[Businesswire](https://www.businesswire.com/news/home/20260114335623/en/)
- 誠實總評：**跨硬體零樣本遷移 2025-26 從無到有、三家獨立收斂——趨勢真實；但「demo→99.x% 經濟可靠性」的最後一哩，沒有任何一家給出第三方數據。**

### 供給側總評
3 年內可解：執行器產能/成本、電池（換電）、BOM 降到 $20k 級、算力工具鏈。5-10 年難題：**靈巧手「耐久×觸覺×量產」三合一**（判 ~5 年）；**數據×contact-rich manipulation**（樂觀 3-5 年、保守 10 年——唯一路線未知的瓶頸）。投資含義：硬體瓶頸股的超額利潤窗口短（中國擴產速度）；長期護城河在數據/模型側（車隊規模、數據工廠）。

---

## 3. 賣方 TAM 預測光譜（修正方向：2024 年以來全部上修，查無下修）

| 機構 | 2030 出貨量 | 其他關鍵數字 | 最新版本 | 修正方向 |
|---|---|---|---|---|
| Goldman Sachs | base >25 萬台（幾乎全工業） | 2035：140 萬台/$38B；2025 ~2 萬台 | 2022 首版 $6B → 2024 上修 6 倍 | **上修**（史上最著名一次） |
| Morgan Stanley | 中國 44.6 萬台（2026-06 由 26.2 萬上修，CAGR 106%） | 2050 全球在用 ~10 億台、營收 $4.7-5T；美國 TAM $3T | Humanoid 100（2025-02）＋2026-06-24 再上修 | **上修**（一年兩度倍增中國預測） |
| BofA | **120 萬台**（2026 9 萬台起、CAGR 86%） | 2035 1,000 萬台；2060 存量 30 億台；BOM $35k→<$17k@2030；**「量產起飛點 2028」** | Physical AI part 2（2026-03-12） | **上修** |
| Citi | 具名 2030 台數查無 | 2050 人形 6.48 億台、TAM **$7T** | The Rise of AI Robots（2024-06）＋2026-02 新報告 | 持平偏上 |
| UBS | 具名 2030 台數查無 | 2050 需求 8,600 萬台/年、在役 3 億台；人形半導體 TAM 2050 $177B | 2025-26 轉述 | 查無修正紀錄 |
| Bernstein | 2030-2032 年出貨破 100 萬台、$15-20B | 最看好整機 OEM、手指致動器、觸覺感測器 | ~2025 | 查無 |

- 門檻年（由軌跡推導，非機構原話）：**10 萬台/年**——BofA ~2027、MS 中國 ~2027、GS ~2028；**100 萬台/年**——BofA 2030、Bernstein 2030-32、GS ~2034；**1,000 萬台/年**——僅 BofA 給到（2035）。
- 讀法：2030 分歧 4-5 倍、2050 分歧一個數量級＝「早期趨勢、無人知道斜率」的光譜形狀。**全面上修是多頭最有力的結構證據——但 cobot（Barclays 2015）與 AV（2016-19）在泡沫頂點時賣方同樣只上修不下修；「修正方向由上轉下」歷史上是週期見頂的領先訊號，值得當指標盯。**
- 來源（2026-07-24；GS/MS/BofA 原文多為 403，經 CNBC/SCMP/Forbes/TechTimes 交叉）：[CNBC MS 上修](https://www.cnbc.com/2026/06/24/morgan-stanley-china-humanoid-robot-market-forecast.html) ・ [Forbes BofA 2028 起飛](https://www.forbes.com/sites/johnkoetsier/2025/04/30/humanoid-robot-mass-adoption-will-start-in-2028-says-bank-of-america/) ・ [Citi GPS](https://www.citigroup.com/global/insights/the-rise-of-ai-robots) ・ [Goldman](https://www.goldmansachs.com/insights/articles/the-global-market-for-robots-could-reach-38-billion-by-2035)

---

## 4. 政策與資本

### 4.1 中國（全球最強政策推力）
- 具身智能 **2025-03-05 首入政府工作報告**（培育未來產業）；2026 報告再列；**十五五規劃（2026-2030）**把機器人列八大戰略新興產業、具身智能入十大新賽道（觸發跨部委＋國有金融機構強制協調）。[新華網](http://www.news.cn/tech/20250311/70c6793481a94810a31a5835672ce718/c.html) ・ [The Diplomat](https://thediplomat.com/2026/03/chinas-new-five-year-plan-prioritizes-robotics-the-world-should-pay-attention/)
- 工信部《人形機器人創新發展指導意見》（2023/10-11）：2025 整機量產＋創新體系、2027 綜合實力世界先進。[商務部政策庫](https://policy.mofcom.gov.cn/claw/policyInfo.shtml?id=5743)
- 資金（具體金額）：**國家 AI 產業投資基金 ¥600 億**（大基金三期＋國智投發起，2026/1 工信部明示強化對人形支持）；北京機器人基金 ¥100 億＋千億級政府投資基金群；上海未來產業基金 ¥100 億；深圳 AI 與機器人基金 ¥100 億＋¥45 億政策資金；杭州「3+N」基金集群目標 ¥1,000 億、2026/5 出台**全國首部具身智能機器人立法**；另 ITIF 引述 ~¥1 兆國家創投引導基金聚焦機器人/AI。「國調基金二期投人形」：**查無**。[證券時報](https://www.stcn.com/article/detail/3604095.html) ・ [ITIF](https://itif.org/publications/2026/07/14/the-u-s-humanoid-robot-industry-is-falling-behind/)
- 另有報導稱 2026/6 政府下達「年底前 1 萬台人形上崗」指令（TechTimes，未直接核對原始文件——既是需求保底、也是行政催熟的泡沫風險）。

### 4.2 美歐
- 美國：**無聯邦級機器人戰略**。動態：2025/3 Tesla/Boston Dynamics/Agility 赴國會推國家戰略＋聯邦機器人辦公室；Humanoid ROBOT Act of 2025（S.3275）禁聯邦採購敵對國人形；2026/2 商務部圓桌＋醞釀機器人行政命令（未落地）；Section 232 機器人進口調查中。ITIF（2026-07-14）：2025 全球人形銷量美企占比 **<5%**、中企 ~90%。[Semafor](https://www.semafor.com/article/02/25/2026/us-government-to-meet-with-robot-makers-as-china-competition-intensifies) ・ [The Robot Report](https://www.therobotreport.com/bills-introduced-strengthen-u-s-robotics-competitiveness-humanoid-security/)
- 稀土武器化：2025/4 中國稀土管制已實際延誤 Optimus（見 §1.1）——**供應鏈地緣風險是西方量產時程的實質變數**。
- 歐盟：無人形專屬戰略（AI Act 高風險分類＝合規摩擦；euRobotics Vienna Statement 2026/6 僅為呼籲）。

### 4.3 一級市場融資（動能：加速，2026H1 已超 2025 全年）
- 人形專項（PitchBook）：**2024 $2.0B → 2025 $6.1B → 2026 YTD（7 月初）>$5B**。[PitchBook](https://pitchbook.com/news/articles/the-limits-of-vcs-humanoid-bet)
- 機器人整體（Crunchbase）：2024 $8.2B → 2025 ~$14-15B → **2026 YTD $18.8B 已破歷年全年紀錄**。[Crunchbase News](https://news.crunchbase.com/venture/ai-humanoid-robot-funding-apptronik/)
- 中國具身智能：2026 年初至 5/11 共 218 起、>¥577 億，已超 2025 全年。[chinabizinsider](https://chinabizinsider.com/15-embodied-ai-unicorns-in-6-months-chinas-robot-race-hits-a-reality-check/)
- 指標案例：Figure $39B、Apptronik $5B、Skild $14B+、PI $5.6B（2025/11；2026/3 傳 >$11B 未確證）、宇樹 IPO、Agility SPAC $2.5B、英國 Humanoid $1.35B（歐洲首隻純人形獨角獸）。
- 同時的分化訊號：中國二線公司融資急凍、欠薪與整併加速（36kr）；PitchBook 專文標題即為「The limits of VCs' humanoid bet」。

### 4.4 產業資本 capex（宣稱 vs 已投產）
| 主體 | 宣稱 | 已投產 |
|---|---|---|
| Tesla | Fremont 100 萬台/年設計產能、Giga Texas 千萬台級規劃 | **0**（產線安裝中，2026/7） |
| Figure BotQ | 1.2 萬台/年→4 年內 10 萬台/年 | Figure 03 累計 >350 台（自報） |
| UBTech | 2026 產能 5,000 台、2027 一萬台 | 柳州廠月產 600→1,000 台爬坡、已交付 >500 台 |
| 智元 | — | **已投產全球第一**：累計 15,000 台（2026-06-28） |
| 宇樹 | 2026 出貨 1-2 萬台 | 2025 已出貨 5,500+ 台 |
| 零部件 | 五洲新春 98 萬套絲杠、貝特 ¥18.5 億 | 產能建設中 |

### 4.5 半導體/記憶體連動（對使用者組合最相關）
- UBS：單機半導體 BOM 2025 ~$1,400（含 ~$500 主處理器＋記憶體＋感測器）→2050 ~$2,000；人形半導體 TAM 2025 **$21M** → 2050 $177B。[FMP 轉述](https://site.financialmodelingprep.com/education/financial-analysis/why-humanoid-robots-are-the-next--billion-tech-megatrend)（未直接核對原報告）
- Micron CEO（財報會）：人形記憶體含量約為 L2+ 車的 10 倍、「本十年後段」啟動數十年記憶體需求週期（網傳 3TB DRAM/台為二手推算，低可信度）。[cryptobriefing](https://cryptobriefing.com/micron-humanoid-robots-memory-demand-cycle/)
- Semiconductor Engineering：量產人形單機 1,100-1,500 顆分立半導體、類比:數位晶片數量比 20:1-50:1。[SemiEngineering](https://semiengineering.com/role-for-ics-expands-in-humanoid-robots/)
- **算術（推論）**：2030 出貨 100 萬台（樂觀）×$1,400≈$1.4B/年 ≈ 全球半導體 0.2%。**2029 年前對記憶體 EPS 是誤差項；真正近期受益在訓練端（GPU/HBM），與現有持倉重疊。**

---

## 5. 反面證據（實名，按殺傷力排序）

### 5.1 實名看空論點（8 條）
1. **Rodney Brooks**（MIT 榮譽教授、iRobot/Rethink 創辦人）：《Why Today's Humanoids Won't Learn Dexterity》（2025-09-26）——視覺中心＋模仿學習缺觸覺前端，數十年內達人類靈巧度是「pure fantasy」；2026-01-01 年度記分卡（連續第 8 年）：「2036 年前可部署靈巧度仍然可悲（pathetic）」、「數億台人形 5-10 年內部署」是 bullshit；預言 15 年後成功的「人形」會有輪子與多臂。**他是唯一有公開逐年打分、且在 AV 泡沫上驗證過準確的預測者。殺傷力：高。** [rodneybrooks.com](https://rodneybrooks.com/why-todays-humanoids-wont-learn-dexterity/)（403，經多來源印證）
2. **Ken Goldberg**（UC Berkeley）：「10 萬年資料缺口」——正式發表於 Science Robotics（2025）；未來 2/5/10 年都不會有橫掃式突破；警告泡沫反噬整個領域。直接打擊「LLM scaling 在機器人重演」的多頭核心假設。**殺傷力：高。** [Science Robotics](https://www.science.org/doi/10.1126/scirobotics.aea7390)
3. **朱啸虎**（金沙江創投）：2025-03-28 公開表示**正在批量退出具身智能項目**——「我問這些 CEO 潛在客戶在哪，感覺他們是自己想像客戶。誰會花十幾萬買機器人幹這些活？」用真金白銀投過然後選擇退出的一手行動。**殺傷力：高。** [新浪財經](https://finance.sina.com.cn/jjxw/2025-04-01/doc-inerraka0607733.shtml)（2025-04-01）
4. **Melonee Wise**（時任 Agility 產品長、Fetch 創辦人）：「我不認為有人找到單一設施需要幾千台人形的應用」＋99% 可靠度的機器人在要求 99.99% 的產線上是負資產。頭部人形公司產品長的業內自承，攻擊 TAM 模型的分母。**殺傷力：高。** [TechCrunch](https://techcrunch.com/2024/06/01/industries-may-be-ready-for-humanoid-robots-but-are-the-robots-ready-for-them/)（2024-06-01）
5. **Fortune 調查**：Figure×BMW「fleet」實查僅 1 台、非生產時段練習；BMW 發言人證實。頭部公司旗艦案例與宣傳嚴重不符（Adcock 揚言告誹謗未見下文；註：BMW 後續仍續擴至 Figure 03）。**殺傷力：高。** [Yahoo/Fortune](https://finance.yahoo.com/news/ceo-heavily-funded-humanoid-robot-185637777.html)（2025-04）
6. **Kyle Vogt**（前 Cruise CEO）＋Green Oaks/Khosla/Bain：頂級投資人押注**非人形**（輪式）form factor——「聰明做法是為用例選 form factor，不是塞進人形」。Vogt 本人是上一個泡沫的當事人。**殺傷力：中。** [The Robot Report](https://www.therobotreport.com/the-bot-company-led-by-kyle-vogt-brings-in-another-150m/)
7. **Adam Jonas**（Morgan Stanley，人形多頭）具名確認 2024/10 We Robot 的 Optimus「relied on tele-ops」；2026 Miami demo 摔倒再引遙操作質疑。demo≠能力的實錘。**殺傷力：中。** [TechCrunch](https://techcrunch.com/2024/10/14/tesla-optimus-bots-were-controlled-by-humans-during-the-we-robot-event)
8. **Robert Gruendel**（Figure 前首席安全工程師）聯邦告訴（2025/11）：安全計畫被「gutted」、涉嫌誤導投資人（未判決）。人形進入有人環境沒有安全認證標準可循是硬門檻。**殺傷力：中。** [CNBC](https://www.cnbc.com/2025/11/21/figure-ai-sued.html)
- 另：**Unitree 高管自承**「人形卡在三座大山、AI 模型還沒準備好」（BigGo 轉述，未直接核對原始訪談）——全球出貨王自己說模型不行。[BigGo](https://finance.biggo.com/news/60a3d99d-bc21-4662-91a8-3c355192fe8f)

### 5.2 失敗/收縮案例（2018-2026）
- **達闼 CloudMinds**（中國人形獨角獸，融資 >¥54 億）：2024 起欠薪裁員、2025/3 多地人去樓空、資金鏈斷裂——中國具身第一隻倒下的獨角獸。[新浪](https://finance.sina.com.cn/roll/2025-03-31/doc-inerpcss8385850.shtml)
- **K-Scale Labs**（美、YC 系）：2025-11-04 倒閉——手握 $2M 預購找不到領投、被中國價格戰輾壓，全額退款＋開源。[The Information](https://www.theinformation.com/briefings/exclusive-humanoid-robotics-startup-k-scale-shut-exploring-sale-1x-bot-co)（未直接核對）
- **Sanctuary AI**（加拿大人形先驅）：2024/11 兩創辦人出局＋裁員 ~30 人、靠 $10M 可轉債續命、之後又換兩任 CEO。[Bloomberg](https://www.bloomberg.com/news/articles/2024-11-15/robotics-startup-sanctuary-ai-cuts-jobs-after-two-co-founders-leave)
- **Rethink Robotics**（前車之鑑）：2018 倒閉、燒 ~$150M；至 2015/9 僅賣 ~1,000 台且**大部分給學術界**（同期 Universal Robots 賣 8,000+ 台給工業）——買家結構=今日中國人形出貨的鏡子。[IEEE Spectrum](https://spectrum.ieee.org/rethink-robotics-pioneer-of-collaborative-robots-shuts-down)
- 周邊：Boston Dynamics 裁 45 人（自承 burning through cash）；Amazon Blue Jay 6 個月夭折；Zebra 關閉 Fetch AMR 業務；中國二線融資急凍＋36 氪《人形機器人死亡報告》存目（403 未讀全文）。

### 5.3 試點不續約案例 — 大體查無，且有反例
- 「客戶公開不續約/聲明 ROI 不成立」：**查無**。反例：BMW 試點後續擴 Figure 03＋萊比錫；GXO×Agility 持續。
- 但替代證據強：**中國租賃市場崩塌**——商演日租從 2025 春晚後峰值 ¥3 萬/天 → 年底 ~¥3,000 → 2026/5 ¥800-1,500（18 個月 -95%）；二手工程機從 ¥30-80 萬跌到 ¥3-6 萬（-90%）、「¥5 萬一車」打包清倉。[新浪](https://finance.sina.com.cn/roll/2026-06-04/doc-iniafvzq0376426.shtml) ・ [證券時報](https://www.stcn.com/article/detail/3677998.html)
- 中性解讀警告：無不續約案例也可能只因試點基期小、時間短——續約大多是「試點升級成試點」，非量產採購。

### 5.4 泡沫類比量化
- **協作機器人（2015-18）**：Barclays 2015 預測 2020 年市場 $3.1B/15 萬台；實際 2020 ~$590M/2 萬台級——**營收差 5.3 倍、台數差 6-7 倍**；先驅 Rethink 死在半路。今日人形出貨曲線形狀與當年如出一轍。[robotonomics](https://robotonomics.wordpress.com/2016/01/11/the-facts-about-co-bot-robot-sales/) ・ [Springer（Gartner 案例）](https://link.springer.com/chapter/10.1007/978-3-031-43662-8_48)
- **自駕車（2016-21）**：全行業投入 >$100B（CNN 2022）；Cruise 燒 >$10B 後 GM 2024/12 關停；Argo（$3.6B+）2022 關閉；Alphabet Other Bets 燒 $37B；Musk「2020 百萬 robotaxi」等承諾全數落空——**時程晚 8-10 年**。[CNN](https://www.cnn.com/2022/11/01/business/self-driving-industry-ctrp/index.html)
- **事後看最早暴露過度樂觀的三個領先指標（綜合推論）——三項目前在人形上全部重現**：
  1. 買家結構錯位（Rethink 賣給學術界 ↔ 中國人形賣給科研/展演/租賃）；
  2. demo 依賴人工暗助（AV 安全員拿不掉 ↔ 遙操作 demo）；
  3. 試點→重複採購轉化率為零（AV 試點城市公告不轉營收 ↔ pilot-to-pilot）。
- **與前兩次泡沫的關鍵差異（給多頭的公道話）**：(a) 中國政策強制保底需求（AV 沒有）；(b) VLA 基礎模型是真實技術斷點（cobot 時代無等價物，跨硬體零樣本遷移三家獨立做出）；(c) 供應鏈 capex（減速器/絲杠/靈巧手）是實體投入非純軟體燒錢；(d) 已有一家獲利公司（宇樹）與一筆可稽核 backlog（Agility $3 億）。

### 5.5 「人形 form factor 偽需求」論
- 正方最強：世界為人建（brownfield 免改造）、通用平台攤薄 R&D、勞動力短缺定價的是「小時人工」；BMW 續擴是最佳實證。
- 反方最強：Wise 的需求密度論＋Vogt 的輪式路線＋結構性事實——真正賺錢的機器人是「拴在地上的無腿機器」（AMR/機械臂：$15-50k、ISO 安全認證、已知 MTBF、7×24），人形至今**沒有動態平衡雙足的安全認證標準**；Amazon 100 萬台機器人中人形≈0 是最重的實證投票。
- 裁決（推論）：新建設施反方勝、既有產線換人正方勝——故第一波真需求集中在汽車廠棕地產線，與 §1.6 觀察一致。

---

## 6. 週期階段劃分與可追蹤指標

### 階段劃分（判準：出貨結構與客戶行為，不是技術 demo）

**階段 0：技術驗證/表演期（2021-2024）— 已結束**

**階段 1：試點期（2025-2027/28）— 現在（2026=中段）**
- 特徵：年出貨萬台級但科研/展演/租賃為主；商業部署集中汽車廠與 3PL、每客戶 <100 台；RaaS 出現；融資（人形 $6.1B/2025）比全行業真實部署營收高 1-2 個數量級；資本化（IPO/SPAC）跑在商業驗證前。
- **確認進入階段 2 的指標（任兩項成立）**：
  1. 任一客戶單一場域 >500 台或單一客戶累計採購 >1,000 台（附合約金額，Agility backlog 交付完成即近似達標）；
  2. 宇樹/智元/優必選財報「工業/商業客戶」營收占比 >50%（宇樹 2026/8-9 掛牌後每季可查——**信號密度最高的單一指標**）；
  3. 靈巧手達 30 萬次循環＋雙手成本 <$5,000（Brooks 論點的直接否證）；
  4. Tesla Fremont 線實際下線並開始對外交付（10-K 單列 Optimus 營收）。
- **否證/延後指標（任兩項成立＝時程後移 ≥2 年）**：
  1. 人形專項融資年減（對照基期 2025 $6.1B/PitchBook）連續兩年；
  2. GXO/Toyota/Mercedes/BMW 任一 RaaS 到期不續或喊停；
  3. 中國「年底 1 萬台上崗」實質未達成或靜悄悄放棄；
  4. MS/GS 首次下修出貨預測（修正方向反轉＝週期頂訊號）；
  5. 宇樹掛牌後首兩季工業占比仍 <20% 且營收增速 <50%。

**階段 2：產線導入期（樂觀 2028 起＝BofA「量產起飛點」；基準 2029-2031；持續 3-5 年）**
- 特徵：全球年出貨跨 10 萬台（賣方共識 2027-28 達標）→邁向 25 萬-100 萬台（2030 分歧區）；千台級訂單常態化；工業 BOM $20-30k；出現第二、三家靠賣機器人獲利的公司。
- 進入階段 3 的指標：非結構化環境（零售/餐飲/醫護）付費部署破萬台；無遙操作全自主的第三方驗證（RoboArena 類榜單成熟）；人形安全認證/保險體系成形（類 ISO/UL）。
- **記憶體/半導體開始有感的起點在此階段末**：年出貨 50 萬台 × $1,500-2,000 ≈ $1B 級/年（2030 年代初）；Micron CEO 說的「本十年後段」與此吻合。

**階段 3：通用化/服務業期（2032+）**：年出貨百萬台級（本報告判斷 BofA 的「2030 年 120 萬台」更可能在 2032-2035 實現，依 cobot/AV 的 1/5 斜率法則）；家用早期市場（<$15k）啟動；單機 TB 級記憶體需求實質化。

**階段 4：家用普及期（2035+）**：不做推斷；MS 2035 在役 13M vs UBS 2M 的分歧會在階段 2 末被裁決。

### 進場時點含意（推論，非投資建議）
- 主題 beta 交易：階段 1 內每次回調都是敘事機會，但需接受 AV/SPAC 式 50%+ 回撤風險；宇樹掛牌（2026/8-9）是近期最大的定價事件——首日市值與其後首份財報會直接校準整個板塊的一二級落差。
- 基本面配置：等階段 2 確認指標出現 2 項再進（寧可買貴 30% 也不提早 3 年）；依歷史斜率，基準確認點 **2028-2029**。
- 組合警告：與現有 AI 半導體/記憶體重倉同因子，加碼＝加槓桿非分散；若要現在表達觀點，供應鏈上游（減速器/絲杠/靈巧手零部件）比整機 OEM 的財務兌現更早，但注意中國擴產會快速壓縮其利潤窗口。

---

## 附錄：證據品質聲明
- 事實 vs 推論：各節標「推論」「判定」「裁決」者為本報告推導；其餘為具名來源陳述。訓練記憶僅用於 2024 年以前歷史脈絡（Rethink/Argo/Cruise 結局等）且均有當日查證來源佐證。
- 一手已核對：Tesla Q2 2026 財報會（CNBC 當日報導）、Agility SEC Form 425、NVIDIA/DeepMind 官方稿、中國政府文件（商務部政策庫/新華網）。
- 未直接核對（403，經多來源交叉）：Goldman/MS/BofA/UBS 報告原文、Figure/BMW 官方稿、rodneybrooks.com、pi.website、The Information。
- 查無清單：傅利葉人形出貨量、Jetson Thor 出貨量、UBS 修正紀錄、國調基金二期投人形、政府/國資買家占比量化、優必選正式沽空報告、Agility RaaS 單價、具名試點不續約案例。
- 已知矛盾未決：宇樹 vs 智元「2025 出貨第一」（口徑不同）；宇樹淨利 ¥2.78 億 vs ¥5.91 億（不同轉述）；Figure 03 在 BMW 台數（40 台說 vs 官方未公布）；PI 2026 新輪是否完成。

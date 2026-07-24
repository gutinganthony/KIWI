# 人形機器人／具身智能供應鏈瓶頸地圖（BOM → 上游材料）

**查詢日：2026-07-24**。用途：Serenity 框架選股素材——找 AI capex 流向的上游隱藏瓶頸，偏好小市值、有定價權、多客戶的日台上游股，供 6–36 個月分批佈局。

**證據等級標記**（Serenity Step 3 慣例）：
- ★★★ [已知供應商]＝公司 IR／客戶公開確認
- ★★ [OSINT推論]＝具名媒體／研究報導，未經公司確認
- ★ [純推測]＝結構推理，無直接證據
- 「未直接核對」＝來源被擋（403），僅靠搜尋摘要
- 「查無」＝找不到，不用訓練記憶補數字

**本次調查的工具限制申報**：session 中段起 WebFetch/直連全被 proxy 403 擋下、WebSearch 額度用罄（200/200）。標「未直接核對」者即受此影響——多數個股頁面（stockanalysis.com 等）被擋，估值數字以搜尋摘要與子代理在被擋前抓到的為準。

---

## 0. 需求端現實校準（先看這個，決定整張地圖的時間軸）

任何「每台用幾顆」的乘法，都要先乘以「2026 年實際有幾台」。答案：**很少**。

| 事實 | 來源（2026-07-24 查） |
|---|---|
| Tesla Optimus：截至 2026-07-20 量產數≈0；Fremont 改裝 Model S/X 產線，量產「7月底或8月」啟動；Musk 2026-07-01：「Optimus production will be extremely slow at first…This is not like making a car」；1 萬個獨特零件 | techtimes.com/articles/321012（2026-07-20）＋ finance.yahoo.com（Musk X 回覆）＋ electrek.co/2026/04/22 [OSINT推論★★] |
| Optimus 2025 年實際產量「數百台」vs 目標 5,000 台；分析者統計 8 次里程碑跳票；Musk 2026-01 Davos：對外銷售「可能 2027 年底」 | optimusk.blog/blog/tesla-optimus-delay ＋ blog.robozaps.com（低權重來源，未直接核對）[OSINT推論★★] |
| Figure：2026-04-29 宣布 BotQ 達 1 台/小時（1月時 1 台/天），累計交付 350+ 台，年產能目標 12,000 台；BMW Spartanburg 部署 40 台 | figure.ai/news/ramping-figure-03-production ＋ eweek.com [已知供應商★★★（公司自述）] |
| TrendForce（2025-08-26）：人形機器人晶片市場 2028 年才 4,800 萬美元；全球人形出貨量約 **2032 年才破 10 萬台** | trendforce.com/presscenter/news/20250826-12685.html [OSINT推論★★，具名研究] |
| 中國隊出貨（Unitree 2026-03 IPO 招股書揭露三檔靈巧手產品線）——詳見 §A 中國節 | techbuzzchina.com robot-hands 報告 [OSINT推論★★] |

**判讀**：2026 年全球人形「真實出貨」量級在千台～低萬台之間（Figure 350+、Optimus≈0、中國隊數千台）。**所有「人形放量」財務模型在 2026-2027 都不會體現在上游營收**，體現的是「送樣、認證、小批量」。這決定進場策略：買的是「工業自動化本業撐底＋人形選擇權」，不是買人形營收。凡是靠人形本夢比撐估值的，時間都站在你的對面。

---

## 1. 供應鏈逐層拆解（下游→上游）

### BOM 總覽
- Morgan Stanley 估 Optimus Gen2 BOM $50-60k；2025 年中國鏈 BOM ≈$46k vs 非中國鏈 ≈$131k（差近 3 倍——這就是「中國破壞」的定量表述）。[未直接核對；來源：blog.robozaps.com 與 mexc.com 轉述 MS 報告，★★]
- 關節執行器占 BOM 30–50%＋；減速器＋滾柱絲杠合計約占 BOM 1/3。[未直接核對，多來源一致 ★★]

### Layer 1｜整機（不是本次標的，只當需求訊號）
Tesla（Fremont，量產未啟動）、Figure（BotQ 已 1台/hr）、Agility、Boston Dynamics（Hyundai）、1X、Apptronik；中國：Unitree（IPO 中）、UBTech、智元 Agibot、Galbot；台灣：鴻海（NVIDIA 合作）；韓國：Rainbow Robotics（Samsung）。

### Layer 2｜旋轉執行器：諧波減速器 —— **雙寡占→被侵蝕中**
- 結構：Harmonic Drive Systems（6324.T）是策波技術發明者與高端壟斷者；strain-wave 市場前五（HDS、Nabtesco、住友、Wittenstein、Nidec-Shimpo）合計約 61%（2025）[未直接核對，verifiedmarketreports ★]。中國綠的諧波為最大追趕者——詳見 §A。
- 用量：Optimus 每台 14 顆旋轉執行器（諧波方案）[OSINT推論★★，多方拆解一致]；市場研究稱一般人形 20–40 顆 [★，低權重]。**重要反例：低成本中國人形（Unitree 路線）大量改用行星齒輪＋準直驅（QDD），不用諧波**——諧波在人形的滲透率不是 100%，是設計路線之爭 [OSINT推論★★]。
- 製造壁壘：flexspline 壁厚 <1mm、高強度鋼、極限精度，是「現代齒輪加工最難任務之一」（EMAG 技術頁，emag.com/industries-solutions/workpieces/robotics/flexspline/ ★★★工藝事實）。
- RV 減速器（Nabtesco 6268.T 壟斷）：重、大扭矩，用於工業機器人底軸；**人形基本不用**（太重）——Nabtesco 是工業機器人股，不是人形股。[OSINT推論★★，詳見日本節]

### Layer 3｜線性執行器：行星滾柱絲杠 —— **本次調查最強瓶頸層**
- 結構：全球高端由瑞士系壟斷——GSA、Rollvis、Ewellix 等頭部合計 >70%，其中瑞士 GSA+Rollvis >50% [未直接核對，pmarketresearch/kggfa ★；Fast Company 2025 專文存在但被 403 擋]。**更正：Ewellix 現屬 Schaeffler（SKF 2019 分拆後 2022 被 Schaeffler 收購）** [OSINT推論★★]。美系：Moog、Nook、Creative Motion Control（查無細節）。市場規模：2025 約 $1.8B → 2034 $3.4B（verifiedmarketreports ★）。
- 用量：Optimus 每台 **14 顆線性執行器＝14 套倒置式行星滾柱絲杠**（定子絲杠、轉動螺帽，電機轉子直驅螺帽）[OSINT推論★★，多方拆解一致]。單價 $1,350–2,700/顆 [★未直接核對]。
- 供給約束證據：磨削＋熱處理公差 <5μm、全球僅少數公司具備；2023 年 Tesla 採購交期曾拉到 26 週 [★未直接核對，impactlab 轉述]。內螺紋磨床本身就是稀缺設備。
- 這層的特點：**市場極小、玩家極少、擴產靠螺紋磨床（設備交期長）、需求彈性最大**（人形線性化是 Tesla 路線的核心）。但瑞士頭部全是未上市（GSA、Rollvis 私人公司；Ewellix 在 SKF 體內占比極小）——**上市可投的純度標的稀缺，這正是台日二線（Hiwin、THK、NSK、TBI）的機會窗口**。詳見台日節。

### Layer 4｜電機：無框力矩電機＋空心杯電機
- 無框力矩電機（旋轉關節用）：Kollmorgen（Regal Rexnord 旗下）TBM/TBM2G 系列明確卡位人形（kollmorgen.com/en-us/solutions/robotics/humanoid-robots ★★★公司自述；已公開的設計採用：RobCo、HEBI——非人形）；Celera Motion（Novanta 旗下）、TQ RoboDrive、Nidec、國產多家。市場結構：分散偏寡占，壁壘中等。
- 空心杯/微型電機（靈巧手用）：maxon、Faulhaber、Portescap（Regal Rexnord）三強＋日本 Adamant Namiki；中國鳴志、兆威追趕。maxon/Faulhaber **未上市**。每手 6–17 顆微型電機（Optimus Gen3 手：17 電機在前臂）[OSINT推論★★]。
- 判讀：電機層「壟斷度」低於減速器/絲杠層，且中國空心杯供應鏈成熟快——定價權中等偏弱。

### Layer 5｜靈巧手 —— **複雜度最高、良率最低的次系統**
- Optimus Gen3 手：腱繩傳動、電機＋微型絲杠在前臂；國聯民生拆解：17 電機＋行星齒輪箱＋行星滾柱絲杠＋腱繩、22 顆霍爾感測、94 觸點觸覺 [OSINT推論★★，foxtechrobotics 轉述]。Musk 多次表示手/前臂是最難部分 [★★，本次未能直接核對原文]。
- 微型滾珠/滾柱絲杠（手指用，直徑 mm 級）：日本 KSS（未上市）、NSK；台灣 TBI Motion 有微型絲杠產品線 [詳見台灣節]。**這是「絲杠瓶頸」的縮小版，玩家更少。**
- 觸覺：XELA（uSkin，2025-12 整合 Tesollo 五指手）、GelSight、Bosch MEMS 進場（BCW 2026）[OSINT推論★★]。格局未定、太早，觀察層。
- 中國：LinkerBot 自稱高自由度靈巧手全球 80% 份額、月產千隻 [★★ techbuzzchina；自稱數據]；Unitree Dex5-1 20 DoF/94 觸點（IPO 招股書）。

### Layer 6｜感測：六維力/力矩、編碼器、視覺
- 六維力矩感測器：高端由外資主導——ATI Industrial Automation（**Novanta 旗下**）、Schunk、AMTI、Kistler、Epson、Wacoh-Tech、新東工業 Sintokogio、Nitta（與 ATI 有 JV）；2024 前五合計 >60% [未直接核對 ★★]；中國（宇立 SRI、坤維、藍點觸控）在中低端快速搶份額。人形用量：手腕×2＋腳踝×2＝4 顆/台（高配）。市場小而精，**壟斷度高但市場總量小**。
- 編碼器：每關節雙編碼器（輸入端＋輸出端）→ 位置編碼器 IC 每台 40–60 顆，有分析稱它是人形半導體中「數量最大、供給最緊」的品類 [未直接核對，semiconductorx.com 被 403；★]。玩家：磁編碼晶片 ams-OSRAM、MPS（MagAlpha）、iC-Haus；模組級 Tamagawa（未上市）、RLS（Renishaw 旗下）、Nidec Sankyo。
- 視覺：相機模組商品化（不是瓶頸）；LiDAR 由中國 Hesai/RoboSense 主導（人形多用純視覺或輕量 lidar）——非瓶頸層。

### Layer 7｜Edge 推論晶片 —— **事實壟斷（NVIDIA），但不是「隱藏」瓶頸**
- Jetson AGX Thor：2025-08-25 開賣，開發套件 $3,499、T5000 模組 $2,999（千顆量）；Blackwell、2,070 FP4 TFLOPS、128GB、130W；採用者：Agility（Digit 六代）、Boston Dynamics（Atlas）、Figure、Amazon、Caterpillar、Hexagon、Medtronic、Meta（nvidianews.nvidia.com ＋ cnbc.com 2025-08-25 ★★★）。
- 對照：TrendForce 估人形晶片市場 2028 僅 $48M——**晶片層短期金額極小**，NVDA 的人形故事是選擇權不是營收。高通/Ambarella 在人形無已證實大單［查無具名 design win；標查無］。
- 判讀：此層無「隱藏」可言，估值已含機器人夢——不符合 Serenity 找暗瓶頸的原則。

### Layer 8｜電池/電源
- 人形每台 2–3 kWh 級電池＋高壓密度 DC-DC/PMIC。電芯是商品（中韓大廠），**非瓶頸**；電源模組/馬達驅動板有整合價值（台達電角度，見台灣節）。48V 架構與高功率密度驅動器是差異點。[OSINT推論★★]

### Layer 9｜稀土磁鐵（釹鐵硼）—— **政策製造的供給約束層**
- 每台人形 NdFeB 用量：市場估 2–4kg（詳見 §B 子代理查證結果；來源品質中等）。
- 2025-04 中國重稀土（Dy/Tb 等）出口管制→ 2025 下半年多次加碼 → 非中國磁鐵產能成為戰略資產。MP Materials 獲 DoD 入股＋價格下限（2025-07）後股價已大漲——**已被定價**。日本鏈：Proterial（未上市）、信越 4063、TDK、大同特殊鋼 5471——磁鐵占營收比皆低（沾邊風險），詳見日本節。
- 反瓶頸風險：Tesla 曾宣稱下代驅動去稀土化；晶界擴散技術降低重稀土用量。管制本身也可能鬆動（政治變數）。

### Layer 10｜上游設備與材料 —— **最隱藏的一層**
- 齒輪磨床/螺紋磨床：flexspline 與滾柱絲杠的擴產都卡在磨床。玩家：Reishauer（私人）、Kapp Niles（私人）、Klingelnberg（**KLIN.SW，上市小型股**）、Gleason（私人）、Nidec Machine Tool（Nidec 體內）、日本濱井產業 6131、岡本工作機械 6125。磨床交期的量化證據：本次「查無」公開數字——列為待驗證假說 [★純推測→待驗證]。
- 精密軸承（諧波減速器內的交叉滾子軸承、薄壁軸承）：THK、Nippon Thompson（IKO 6480）、NB；此層日本壟斷度高、市值小——詳見日本節。
- 特殊鋼（flexspline 用高強度合金鋼）：大同特殊鋼、愛知製鋼——占營收比極低，沾邊 [★]。

---

## 2. 逐層瓶頸評分表

| 層 | 市場結構 | 人形需求彈性（顆/台） | 供給約束 | 上市純度標的（日台優先） | 綜合瓶頸分 |
|---|---|---|---|---|---|
| 行星滾柱絲杠 | 瑞士雙寡占（未上市為主） | 14＋手部微型絲杠 | 磨削 5μm、磨床稀缺、曾 26 週交期 | Hiwin/THK/NSK/TBI（都是二線進入者） | **★★★★★** |
| 諧波減速器 | HDS 高端壟斷、綠的追趕 | 0–20（路線之爭） | flexspline 工藝＋擴產慢 | HDS 6324（純度 100%） | **★★★★** |
| 六維力感測器 | 高端寡占（ATI 系） | 2–4 | 校準 know-how | Novanta（美）；新東工業/Nitta（日，占比低） | ★★★☆ |
| 上游磨床 | 私人公司寡占 | 間接（設備） | 交期（未量化） | Klingelnberg、濱井 6131、岡本 6125 | ★★★☆（證據不足） |
| 稀土磁鐵 | 中國政策壟斷 | 2–4kg | 出口管制 | MP（已漲）、Lynas；日系占比低 | ★★★（已定價大半） |
| 精密軸承（交叉滾子） | 日本寡占 | 每關節 1–2 | 中 | IKO 6480、THK | ★★★ |
| 無框/空心杯電機 | 寡占偏分散 | 28＋手 17 | 低–中 | Adamant Namiki 7772（小） | ★★☆ |
| 編碼器/編碼 IC | 晶片寡占 | IC 40–60 顆 | 待驗證 | MPS/ams（美歐）；Tamagawa 未上市 | ★★☆（證據不足） |
| Edge 晶片 | NVDA 壟斷 | 1–2 | 無（NVDA 供得起） | NVDA（無隱藏性） | ★★ |
| 電池/電源 | 分散 | 1 pack | 無 | 台達電（整合角度） | ★☆ |
| 觸覺感測 | 未定 | 手部數百觸點 | 格局未成形 | 無成熟標的 | 觀察 |

---

## 3. 日本股深查

> 子代理查證聲明：quote 網站（stockanalysis/minkabu/kabutan/Yahoo JP/irbank）與公司 IR 全被 egress 403 擋，估值數字均來自搜尋摘要＝**全部標「未直接核對」**；查無者不填。

### 3.1 Harmonic Drive Systems 6324 —— 內容最真、價格最貴
- 位置：諧波減速機發明者/高端壟斷；對工業機器人四大家族 [已知供應商★★★]；對 Tesla/Figure 為 [OSINT推論★★]（IR 未點名客戶）。
- 財務：FY2026/3 營收 595.6 億円、營業利益僅 25.7 億円（OPM 4.3%——景氣谷底＋擴產固定費）；中計目標營益 150 億円。
- 估值：2026-07-22 股價 6,920 円、市值 ~6,800 億円、**預估 PER 152 倍、PBR 8.3**（未直接核對）。
- 判讀：**估值已完全透支人形**。買它＝押「人形放量早於 2028＋綠的諧波攻不進高端」雙重命題。列 watch 不列 buy；等利潤驗證或估值腰斬級回調。

### 3.2 THK 6481 —— 日本首選
- 位置：LM 導軌全球第一＋滾珠螺桿/交叉滾子環；Morgan Stanley「Humanoid 100」名單成員 [OSINT推論★★]。roller screw 短缺下 ball screw 是現實替代方案→THK 直接受惠；人形客戶設計中標「查無」公開證據。
- 財務：FY2026 Q1 營收 690 億円 +27.4%、營益 76 億円 **+364%**——工業自動化週期反轉進行中（本業撐底成立）。
- 估值：市值 ~8,856 億円、預估 PER 36.7、PBR 3.3（歷史長年 1–2 倍）→ **已 re-rate 一半**，但 PER 分母在急速修復。
- 判讀：「本業復甦＋人形選擇權免費送一半」的結構，符合 Serenity 偏好。

### 3.3 Nippon Thompson（IKO）6480 —— 最像「隱藏 BOM 股」但已起漲
- 位置：交叉滾子軸承/滾針軸承——藏在每顆諧波減速機與機器人關節裡的隱形 BOM [OSINT推論★★]；人形設計中標查無（產品天然嵌入，不需點名）。
- 財務：FY2026/3 營收 630 億円 +15.9%、營益 41 億円 **+250%**。
- 估值軌跡：2026-05-08 股價 1,230 円（PBR 1.06、市值 904 億円）→ 2026-07-14 已 2,041 円：**兩個月 +66%**、市值 ~1,500 億円（未直接核對）。
- 判讀：市場 2026Q2 才發現它，起點 PBR 1 倍。小市值＋利基寡占＋多客戶——最符合使用者畫像，但**追高風險已現**，等回調分批。

### 3.4 MinebeaMitsumi 6479 —— 便宜的選擇權
- 微型滾珠軸承全球龍頭；FY2026/3 全分部創新高（營收 1.66 兆円、EPS 246.6 円）；2026-06-05 股價 4,994 円、市值 ~2.13 兆円→ **PER ~20 倍**。人形含量是免費選擇權。判讀：防守型參與方式。

### 3.5 其餘（含沾邊點名）
- **Nabtesco 6268**：RV 減速機與人形錯配（太重；人形用諧波/行星）→ **目前是沾邊股** [OSINT推論★★]。PER 34.2/PBR 2.32（2026-07-10 未直接核對）。已收購 Spinea、市調稱其在「人形用小型 RV」28% 份額［低可信市調★］。除非小型化 RV 進人形量產案，否則別當人形股買。
- **NSK 6471**：被多家市調列為人形 roller screw 玩家 [★★未直接核對]；估值本次查無。羅柱絲杠若成案是重要選擇權，待 Mac 補查。
- **Yaskawa 6506**：收購人形開發商 Tokyo Robotics（未核對原 PR）；本業轉型期（2026 年 3-5 月季純益 -22%）。人形是選擇權非本體。
- **Fanuc 6954**：未宣布進軍人形＝**沾邊**；FY2026/3 營收 8,578 億 +7.6%、經常利益 +15.6%（本業復甦是事實）。
- **Keyence 6861**：人形專屬產品**查無**＝**不是人形股**，是 FA 景氣股。
- **Sintokogio 6339**：PBR 0.47 深度價值，但人形力覺證據查無。**Nitta 5186**：PER 10.7 便宜，ATI 合作細節本次查無、力覺占比極小＝沾邊。
- **Adamant Namiki——原始框架錯誤更正**：已併入 **Orbray（未上市）**；「7772」對應公司查無核實。**勿按 7772 下單。**空心杯電機用於 Optimus 手指是業界共識 [★★]，但無任何來源證實 Orbray 供貨 Tesla [純推測]。
- Nidec 6594（FLEXWAVE 諧波型減速機＋齒輪磨床在體內，但巨型複合企業＝稀釋）、Tamagawa Seiki（未上市）、濱井 6131/岡本 6125（磨床「賣鏟子」邏輯成立但人形訂單證據查無 [純推測]）、磁石鏈大同 5471/TDK/信越（占比極小＝材料性沾邊）。

**日本排序（真實含量 × 未完全定價）**：①THK 6481 ②IKO 6480 ③MinebeaMitsumi 6479；HDS 6324 內容第一但價格最後。

## 4. 台灣股深查（子代理回報＋主線彙整）

<!-- TAIWAN_SECTION -->

## 5. 對照組：中國威脅、稀土、美歐韓

<!-- CHINA_US_SECTION -->

## 6. 進場時間點框架（分批佈局 6–36 個月）

<!-- TIMING_SECTION -->

## 7. 反面訊號與整體風險

<!-- RISKS_SECTION -->

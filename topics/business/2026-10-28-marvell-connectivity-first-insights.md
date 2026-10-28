# Marvell 的「Connectivity First」策略——核心重點與對 KIWI 投資邏輯的 input

> **緣起**：Jake 2026-10-28 上傳 Redefine Innovation〈Marvell's Connectivity First Strategy〉（Vince Liu，2026-10-28），請我摘錄核心重點並說明對投資邏輯的 input。
> **前文**：`2026-07-09-serenity-step1-9-cohr-mrvl-aaoi-replacement.md`（MRVL 上次完整 Step 1–9）、`2026-09-25-agent-cpu-bound-and-memory-interface.md`、`2026-10-08-hot-chips-2026-seven-ai-chips-plain-explainer.md`、`2026-10-22-semianalysis-datacenters-2027-50gw-verification.md`。
> **資料等級**：文章為**一手原文**（但內容大量引用 Marvell 自己的 Computex、Investor Day 簡報＝**公司敘事**）；Google 合約、Celestial AI 條款、Investor Day 目標為 `[二手，搜尋摘要]`；股價為 Yahoo 一手（10/27 收盤）。§三、§四是我的推論。
> **非投資建議。**

---

## 0. 三句話

1. **文章的主張**：Agentic AI 讓「記憶體」與「互連（interconnect）」成為兩大瓶頸；Marvell 押的是互連，而且是**從晶片 I/O、光電轉換到交換器整條路自己做**，目標是把 scale-up（多顆晶片當一顆用）的範圍**從一個機櫃擴大到多個機櫃**。
2. **對 KIWI 最有用的一句**：**單通道速度走到 448G 後，銅線只能撐約 2 公尺 ⇒ 跨機櫃的 scale-up 只能用光**——這是一個**新的光學需求來源**（取代銅線，不是取代既有光模組）。而且 Marvell 自己判斷，**在 CPO（共封裝光學）進到 XPU 之前，LPO 與板上光學會先撐住**。
3. **MRVL 本身**：論點強化，但**價格與規模都不符合 Serenity**——現價 $243.57，仍高於 KIWI 7 月訂的分批區 $175–195；營收目標與市場關注度都已在檯面上（B 條件不過）。**真正可用的 input 在它周圍：光學元件、銅線互連、CXL／記憶體介面這三條線的相對強弱**。

---

# 一、核心重點

## 1.1 為什麼互連變關鍵
- NVIDIA 在 Hot Chips 2026 點出 Agentic AI 兩大挑戰：**上下文長度爆炸**、**解碼延遲累積**——每一輪都要重讀整段歷史，每一步都要等上一步。根源是同一件事：**每個 token 都要從記憶體重讀越來越長的上下文**。
- **推論（decode）卡延遲、訓練卡頻寬**，兩者都和互連有關。
- 運算一旦離開機櫃，速度與延遲大幅變差（文中例：GB200 的 NVLink 每 GPU 900 GB/s，一張 800G 網卡只有 100 GB/s）。所以大家都想**擴大 scale-up domain**：模型多大，「當一顆晶片用」的範圍就要多大。

## 1.2 Marvell 的轉型（2016→2026）
| 階段 | 買進 | 賣出 |
|---|---|---|
| 第一波（2018–2022）：補齊產品線 | Cavium（處理器、NIC/DPU）、**Avera**（客製晶片，前身 IBM Microelectronics）、Aquantia（高速 PHY）、Innovium（Teralynx 資料中心交換器）、**Inphi**（光學 DSP）、Tanzanite（CXL 記憶體池化） | 消費性多媒體、Wi-Fi、G.hn、LTE |
| 第二波（2025–2026）：往「光還沒到的地方」走 | **Celestial AI**（光學 I/O、Photonic Fabric）、**XConn**（PCIe／CXL 交換器、UALink 團隊）、Polariton（電漿調變器，用於資料中心互連） | **車用乙太網路賣給 Infineon** |

## 1.3 三條主軸
**① 客製 XPU 與「XPU Attach」（現金牛）**
- 客製 XPU 的問題：**一個 socket 就是一整代的大賭注**，贏這代不保證下一代；2023 年單一 socket 佔整個市場 75%（Murphy 說法）。
- **Attach 的意義：不必贏下運算核心，也能吃到系統內容**——加速器周圍的 NIC、電源 IC、記憶體擴充、交換晶片、封裝內 I/O chiplet 都需要客製。
- 實例：**Google TPU 主要夥伴是 Broadcom**，但 Marvell 在 2026 年拿下 TPU 生態系周邊的儲存控制器、NIC、記憶體介面控制器、近記憶體運算。`[二手]`：合約 7/29 簽署，**Google 獲得最多 5,897 萬股、履約價 $206.58 的認股權證**（隨 Google 採購量到 FY2033 逐步歸屬；最大價值約 122 億美元）。
- Attach 用的 IP（SerDes、die-to-die、CXL）**和互連業務是同一套技術底**。

**② 互連業務（現金牛）**
- **Light engine（光引擎）**：把調變器、光偵測器、driver、TIA、微控制器整合成單一封裝。**路徑：先進 LPO 模組或板上光學（取代機櫃級銅線）→ 再成為 CPO 的基礎**。
- **端到端整合壓延遲**：XPU 端的 SerDes／die-to-die（來自 attach）＋中間的光引擎與光學 DSP＋另一端的 **UALink scale-up 交換器**（Teralynx 架構、224G SerDes）＋XConn 的 PCIe／CXL 交換器。各段分開最佳化會多出 retimer、DSP、協定轉換；**一家做完整條路，延遲才壓得下來**。

**③ 未來押注（選擇權）**
- **Scale-in（封裝內，約 100mm 以內）**：押「光終究會進到封裝裡」；開發 microLED／microVCSEL 光源的封裝內光學 I/O chiplet。Celestial 的光學 I/O 能**從晶粒中間出光**，省下晶粒邊緣放更多 HBM。**Murphy 自己說對 FY2031 營收不重要**。
- **Photonic Fabric（記憶體連接）**：HBM 太快，只能放在晶粒旁幾毫米 ⇒ 運算與記憶體被綁成固定比例。做法是**把 HBM 與 DDR5 放進同一個記憶體模組（HBM 當 DDR5 的快取），再用光接到 XPU**，把共享記憶體延伸到多個機櫃外，**用來放推論的 KV cache**。主張：**記憶體應該和運算分開擴充**。

## 1.4 時間表與數字 `[二手]`
| 項目 | 內容 |
|---|---|
| Celestial AI | 2026-02-02 完成，約 32.5 億美元預付（現金＋約 2,450 萬股），最高 55 億；**FY2028 下半年開始貢獻、Q4 FY28 年化 5 億、Q4 FY29 年化 10 億** |
| XConn | **FY2027 下半年**開始貢獻營收 |
| 2026-10-06 Investor Day | **FY2031 營收目標 700–900 億美元（中位 800 億）**；FY2028 約 200 億（市場共識約 182 億）；FY31 中位拆分約：互連 375 億、客製運算 300 億、交換與儲存 100 億、通訊與其他 25 億；每顆 XPU 配 1–2 個 attach socket、單價約 1,000 美元 |
| Scale-up optics | 從接近零開始，**明年（2027）起量** |
| NVIDIA | 對 Marvell 20 億美元優先股投資，綁定客製 XPU 與 scale-up 網路（Q1 FY27 10-Q） |

---

# 二、驗證與文章的盲點

| 說法 | 判斷 |
|---|---|
| 448G 時銅線限約 2 公尺 | **合理**：NVL72 機櫃內銅線本來就只有約 1 公尺量級；這是 Marvell 的說法，但方向與產業共識一致 |
| LPO／板上光學先於 CPO | **與 KIWI 先前讀數一致**：7 月週報引用 2026 年 CPO 滲透率約 0.5% |
| 客製 XPU 單一 socket 75% | Murphy 說法，未獨立查證；與 2023 年 Google TPU 主導的情況相符 |

**文章沒談、但投資上要補的：**
1. **競爭**：Broadcom 是客製 XPU 與交換器的一哥（KIWI 7 月評估：Broadcom 客製市佔 >70%、Marvell 20–25%）；**scale-up 協定還沒定案**——NVIDIA 有 NVLink（含 NVLink Fusion 開放給第三方）、Broadcom 推乙太網路系的 scale-up，**UALink 能否成為主流未定**。Marvell 押 UALink 是有風險的。
2. **稀釋**：Celestial 約 2,450 萬股＋最高 23 億美元或有對價、Google 最多 5,897 萬股認股權證、NVIDIA 20 億優先股。
3. **客戶集中**：KIWI 7 月已標記 Amazon／微軟 Maia 集中風險。
4. **文章立場**：Redefine 是顧問／媒體，本文大量引用 Marvell 簡報，**是在解釋公司策略，不是評估它會不會成功**。

---

# 三、對 KIWI 投資邏輯的 input（我的推論）

## 3.1 光學線：santec／Seikoh 的「可插拔延壽」命題——**短期偏利多，長期是倒數計時**
- KIWI 週報的**第 7 燈（T2 CPO 滲透）**在 8/27 MRVL 財報後記下「第一個非零證據，方向不利於 santec 與 Seikoh」。
- **本文給了更細的圖**：
  - **scale-up 跨機櫃是「新增」的光學需求**（取代銅線），不是吃掉既有的 scale-out 可插拔市場 ⇒ **光學總量變大**；
  - **第一步是 LPO（仍是可插拔模組）與板上光學**，CPO 進到 XPU 是更後面的事 ⇒ **可插拔／近封裝在 2027–28 年仍有一段**；
  - **但方向很清楚**：Marvell 的路線圖是「可插拔 → 近封裝 → 共封裝 → 封裝內（scale-in）」，**每往內一步，光纖連接器、模組組裝的價值就減少一些**。
- ⇒ **建議下次週報第 7 燈的寫法**：區分「**scale-out CPO 滲透**」（現有門檻）與「**scale-up 由銅轉光**」（新需求，偏利多）。**這正是 9/6 待辦「檢查燈與燈之間有無重複計數」想找的那種問題**——同一份 MRVL 消息在不同燈上方向相反，是因為它同時影響兩個不同市場。

## 3.2 銅線互連：**跨機櫃 scale-up 是銅線的天花板**
- 主動銅纜（AEC）在機櫃內與短距離仍有用，但**跨機櫃 scale-up 不是它的市場**。
- 價格面（Yahoo，10/27）：**Credo $167.43，自 6/22 高點 −45%、自 8/26 起 −26%**；同期 MRVL −1%、Astera −1%、COHR −20%。市場可能已經在反映這件事，**但我沒有查證 Credo 下跌的實際原因**，不能直接歸因。

## 3.3 CXL／記憶體介面：**Astera Labs 多了一個整合型對手**
- Marvell 透過 XConn 有了 PCIe／CXL 交換器，又有 UALink 交換器，**直接進入 Astera Labs 的核心產品區**；而且 Marvell 能把 XPU attach、光引擎、交換器綁在一起賣。
- 與 9/25 Agent CPU 報告的記憶體介面晶片（Rambus、Montage）：Marvell 的「記憶體介面控制器」attach（例如 Google TPU）**是相鄰但不同的產品**（XPU 側 vs DIMM 上的 buffer），**目前看不出直接搶 RCD／MRDIMM buffer 的市場**。[推論]

## 3.4 記憶體超級循環：**兩個方向都偏利多**
- **Photonic Fabric**：把 **DDR5 拉進 AI 推論的 KV cache 層**（HBM 當快取、DDR5 當容量）⇒ **每個系統用更多 DRAM**；也是緩解 HBM 短缺的一條路（用便宜的 DDR5 補容量）——**對一般 DRAM 利多、對「HBM 不可替代」的說法是溫和的利空**。
- **Celestial 從晶粒中間出光，邊緣放更多 HBM** ⇒ 長期每顆 XPU 可以掛更多 HBM。
- 但兩者都要到 **FY2028 下半年（約 2027 年底）** 才開始有營收，**對 2027 年的記憶體供需沒有影響**。

## 3.5 和其他報告串起來
| 報告 | 主張 | 本文的位置 |
|---|---|---|
| SemiAnalysis（10/22） | 2027–28 瓶頸是 HBM 與 N3；CoWoS 在緩解 | 本文補上第三個：**跨機櫃互連的延遲** |
| Agent CPU（9/25） | 記憶體頻寬與 I/O 頻寬要平衡 | 本文是同一件事在機櫃與多機櫃尺度上的版本 |
| Hot Chips 七顆晶片（10/8） | 各家都在把工作移出 HBM、加 SRAM | 本文的 Photonic Fabric 是另一種解法：**把記憶體用光拉遠、變成共享池** |

---

# 四、MRVL 本身：用 Serenity 的 A＋B 快速重看（不是完整 Step 1–9）

| | 判定 | 說明 |
|---|---|---|
| A 資金流動 | ✅ | 8/27 破紀錄財報、scale-up optics 展望上修；Investor Day 把 FY28 目標拉到約 200 億（高於共識）；Google 合約與 NVIDIA 投資都是**具名客戶** |
| B 認知落差 | ❌ | 全市場最受關注的 AI 晶片股之一；Investor Day 已把 FY31 目標公開 ⇒ **不是「還沒被發現」** |
| 象限 | **優質但貴**（同 7 月判定） | |
| 價格 | **$243.57（10/27）**，自 6/4 高點 $316.43 −23%；**仍高於 KIWI 7 月訂的分批區 $175–195** | Google 認股權證履約價 $206.58 可當參考錨點（不是買點） |
| 規模 | 超出 Serenity 原本的小型股射程 | 市值未重算 |

⇒ **維持「觀察、不追」**。MRVL 比較像 Serenity 的「**訊號來源池**」——它的財報與法說是光學、銅線、CXL 三條線的領先指標。

## 要盯的事件
| 時點 | 事件 | 看什麼 |
|---|---|---|
| 約 12 月初（日期為推估） | MRVL Q3 FY27 財報 | **XConn 是否如期在 FY27 下半年貢獻**；scale-up optics 的 2027 起量時程；客製 XPU 的客戶分布 |
| 2027 | scale-up optics 起量 | LPO／板上光學 vs CPO 的實際比例 ⇒ 第 7 燈的判讀 |
| 約 2027 年底 | Celestial AI 開始貢獻（FY28 下半年） | Q4 FY28 年化 5 億目標 |
| 持續 | UALink vs NVLink Fusion vs 乙太網路 scale-up 的採用 | 協定之爭決定 Marvell 交換器的市場大小 |

---

## 結案聲明
**本次涵蓋**：Marvell 的策略與產品主軸（原文）、近期合約與財務目標（二手）、對 KIWI 光學／銅線／CXL／記憶體四條線的推論
**本次明確未涵蓋**：**光引擎的上游**（雷射光源、矽光子代工、microLED／microVCSEL 供應商——若有 Serenity 瓶頸會在那裡）、Credo 與 Astera 的基本面、Broadcom 與 NVIDIA 的 scale-up 路線細節、MRVL 估值重算 ← 這幾層尚未關閉

## 誠實邊界
1. 文章內容大量來自 Marvell 自己的簡報，**是公司敘事**。
2. Google 合約、Celestial 條款、Investor Day 目標皆為**搜尋摘要轉述**，不同來源的拆分數字略有出入。
3. §三全部是我的推論；**Credo 下跌原因未查證**。
4. 持倉表本次未重讀（依 CLAUDE.md 應讀新 fileId `1FPmLp…`）；本文不涉及持倉建議。

## 來源
**一手**：Redefine Innovation〈Marvell's Connectivity First Strategy〉（2026-10-28，原文 PDF）・Yahoo Finance query1（MRVL、CRDO、ALAB、COHR 日線至 2026-10-27）・FinMind（AVGO）
**二手（搜尋摘要）**：TechWire Asia、MarketScale、CNBC、RCR Tech、Alpinum（Google–Marvell 合約與認股權證）・Evertiq、Photonics.com、SDxCentral、Counterpoint、Stocktwits、Marvell 10-K（Celestial AI 收購條款與營收時程）・Futurum、Investing.com、StockAnalysis 逐字稿、FUNDA（2026-10-06 Investor Day 目標）・Marvell Q1 FY27 10-Q（資料中心年增 27%、NVIDIA 20 億優先股）

## Update Log
- 2026-10-28 v1.0：建檔。核心：Agentic AI 讓記憶體與互連成為瓶頸；Marvell 三主軸＝客製 XPU 與 Attach、互連（光引擎＋端到端）、未來押注（scale-in、Photonic Fabric）；**448G 銅線限約 2 公尺 ⇒ 跨機櫃 scale-up 需要光；LPO／板上光學先於 CPO**。對 KIWI：①第 7 燈應區分 scale-out CPO 滲透（不利可插拔）與 scale-up 銅轉光（新需求、偏利多）②跨機櫃是銅線天花板（Credo 自高 −45%，原因未查證）③Astera 多了整合型對手 ④Photonic Fabric 把 DDR5 拉進 KV cache，對 DRAM 利多但要到約 2027 年底。MRVL 維持「優質但貴」、$243.57 仍高於分批區 $175–195，定位為訊號來源池。

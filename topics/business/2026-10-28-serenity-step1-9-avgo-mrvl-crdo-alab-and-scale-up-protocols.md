# Serenity 完整 Step 1–9：Broadcom、Marvell、Credo、Astera Labs＋scale-up 協定（NVLink／UALink／乙太網路）白話解說

> **緣起**：Jake 2026-10-28：「用 Serenity 框架跑 AVGO、MRVL、Credo 和 Astera Labs 完整 Step 1–9；以及什麼是 scale-up 協定 NVLink、UALink、乙太網路，請介紹並分析」。
> **前文**：同日 `2026-10-28-marvell-connectivity-first-insights.md`；`2026-07-09-serenity-step1-9-cohr-mrvl-aaoi-replacement.md`（MRVL 上次 Step 1–9）。
> **資料等級**：
> - **一手（SEC EDGAR）**：Broadcom Q3 FY26 8-K、Astera Labs Q2 2026 8-K
> - **一手（價格）**：Yahoo query1 日線至 2026-10-27
> - **二手（搜尋摘要）**：Marvell Q2 FY27、Credo Q1 FY27 財報數字；客戶集中度；前瞻本益比；協定現況（多數是產業部落格）
> - **未查證、依過往財報記憶**：§Step 7 計算成長率用的「前一年同期營收」（Broadcom Q4 FY25 約 180 億、Marvell Q3 FY26 約 20.75 億、Credo Q2 FY26 約 2.68 億、Astera Q3 2025 約 2.31 億）
> - 本次 **FinMind 額度用完**、**marvell.com／stocktitan.net 在雲端被擋**；市值用「財報稀釋股數 × 10/27 收盤」自算。
> **持倉**：已讀 Google Sheet「KIWI 持倉表」（最後更新 2026-09-08）——**四檔皆未持有**。
> **非投資建議。**

---

## 0. 一句話結論

| | **Broadcom（AVGO）** | **Marvell（MRVL）** | **Credo（CRDO）** | **Astera Labs（ALAB）** |
|---|---|---|---|---|
| 在互連的位置 | 交換器晶片＋客製 XPU 一哥 | 光學 DSP 雙頭＋客製 XPU 二哥＋scale-up 全線 | 主動銅纜（AEC）龍頭，轉進光學 | PCIe／CXL 重定時器與交換器 |
| A 資金流動 | ✅ 強 | ✅ 強 | ✅ 強 | ✅ 強 |
| B 認知落差 | ⚠️ **2/3（四家最接近）** | ❌ 1/3 | ⚠️ 2/3 | ❌ 1/3 |
| 象限 | **最接近甜蜜點，但不是 Serenity 標的**（兆美元公司） | 優質但貴 | **接近甜蜜點但有客戶集中風險** | 優質但貴＋🔴 **單一客戶 >70%** |
| 本次判定 | **觀察；若要買「互連」，四家中風險報酬最好** | 觀察（同 7 月） | **觀察；等 12 月財報確認光學轉型** | **避開** |

> 🔑 **最重要的發現**：用「**本益比 ÷ 營收成長率**」看，**Broadcom 是四家中最便宜的**（約 0.28），Credo 第二（約 0.36）；Marvell 最貴（約 1.06）。**市場最熱的兩檔（Marvell、Astera）反而最貴。**
> 🔑 **協定之爭的投資意義**：**交換器晶片押協定，實體層不押協定**。Credo 的線材與 DSP、Astera 的重定時器，不管最後是 NVLink、UALink 還是乙太網路贏都賣得到；Broadcom 押乙太網路、Marvell 與 Astera 的交換器押 UALink。

---

# 第一部分：scale-up 協定是什麼（白話）

## 1.1 先分清楚 scale-up 和 scale-out

| | **Scale-up（向上擴充）** | **Scale-out（向外擴充）** |
|---|---|---|
| 比喻 | **同一間辦公室裡的同事**，轉頭就能講話、共用白板 | **不同城市的分公司**，靠電話、Email 聯絡 |
| 做什麼 | 把幾十到上千顆 GPU 連得非常緊，**讓它們像一顆超大晶片** | 把很多個「超大晶片」連成整座資料中心 |
| 要求 | **極低延遲、極高頻寬**，可以直接讀寫對方的記憶體 | 頻寬大即可，延遲容許較高 |
| 範圍 | 目前約一個機櫃（72 顆 GPU），目標擴到多個機櫃 | 數萬到數十萬顆 GPU |
| 今天用什麼 | NVLink（NVIDIA）、各家自有協定 | 乙太網路、InfiniBand |

**「scale-up 協定」就是這間辦公室裡大家講話的規矩**：資料怎麼包裝、怎麼確認收到、出錯怎麼重傳、怎麼直接存取對方的記憶體。規矩不同，用的交換器晶片就不同。

為什麼現在變重要：AI 模型越來越大、Agent 的上下文越來越長，**一個機櫃的 72 顆 GPU 已經不夠「當一顆用」**；一旦要跨出去，就要決定用哪種規矩。

## 1.2 三種協定

### ① NVLink（NVIDIA 自家）
- **是什麼**：NVIDIA 專用的 GPU 互連，加上 NVSwitch 交換器晶片。GB200／GB300 的 **NVL72 機櫃就是用它把 72 顆 GPU 連成一顆**；文獻中 GB200 每顆 GPU 的 NVLink 頻寬約 900 GB/s（單向），一張 800G 網卡只有約 100 GB/s。
- **優點**：**現在唯一大規模出貨、經過驗證的方案**；軟體（CUDA、NCCL）與硬體一起調好。
- **缺點**：**封閉**——只能用 NVIDIA 的 GPU 和交換器。
- **NVLink Fusion**：NVIDIA 開放讓**別家的 CPU 或客製加速器**接上 NVLink 生態（Marvell 是合作夥伴之一），但交換器與規格仍在 NVIDIA 手上。**比喻：開了門讓你進來，但鑰匙還在它手上。**

### ② UALink（Ultra Accelerator Link，產業聯盟）
- **是什麼**：AMD、Intel、Google、微軟、Meta 等組成的聯盟，**想做一個「開放版 NVLink」**，讓不同廠牌的加速器都能用同一套規矩互連。
- **規格**：**UALink 1.0（2025-04）**：每條通道 200G、最多 **1,024 顆加速器**、支援直接讀寫對方記憶體；2026-04 又發布四份延伸規格（網內運算、chiplet、管理、效能）。
- **誰在用**：**AMD MI400 系列的 Helios 機櫃是主要採用者**（72 顆 GPU）；但多個來源指出，**初期是「把 UALink 包在乙太網路裡傳」（UALink over Ethernet），走 Broadcom Tomahawk 6 交換器**，因為**原生 UALink 交換器晶片還沒量產**。
- **交換器供應商**：Marvell（收購 XConn 取得 UALink 團隊）、Astera Labs（產品支援 UALink）、Cornelis 等。有報導稱 **Broadcom 早期支持 UALink，後來退出**（約 16 個月前的報導，可能過時）。
- **優點**：開放、能直接存取記憶體、規格為 scale-up 量身設計。
- **缺點**：**最晚上市、原生交換器還沒出貨**，採用者目前主要是 AMD。

### ③ 乙太網路做 scale-up（Broadcom SUE／OCP ESUN）
- **是什麼**：把大家最熟悉的乙太網路（scale-out 早就在用）**改造成夠快、夠低延遲**，拿來做 scale-up。
- **兩條路**：
  - **Broadcom SUE（Scale-Up Ethernet）**＋**Tomahawk Ultra** 交換器（第三方估約 250 奈秒延遲，足以支撐 1,024 顆加速器）——Broadcom 主導。
  - **ESUN（Ethernet for Scale-Up Networking）**：2025 年 10 月在 OCP（開放運算計畫）成立，成員包括 **AMD、Arista、Arm、Broadcom、Cisco、HPE、Marvell、Meta、微軟、NVIDIA、OpenAI、Oracle**；ESUN 1.0 加入無損傳輸、更短的封包標頭、多跳拓撲。
- **優點**：**生態最大、供應商最多、工程師最熟、價格競爭最激烈**；可以和 scale-out 用同一套設備與管理工具。
- **缺點**：傳統乙太網路的延遲與額外負擔較大（改造後已大幅改善，但還需要時間證明）。

## 1.3 三種協定比較

| | NVLink | UALink | 乙太網路（SUE／ESUN） |
|---|---|---|---|
| 主導者 | NVIDIA | 聯盟（AMD 主力） | Broadcom＋OCP（Meta、微軟主導） |
| 開放程度 | 封閉（Fusion 部分開放） | 開放 | 開放 |
| 成熟度 | ✅ 大量出貨 | ⚠️ 原生交換器未出貨 | ⚠️ 剛起步，但沿用既有生態 |
| 規模 | NVL72（下一代更大） | 最多 1,024 顆 | 1,024 顆以上（多跳） |
| 主要受惠上市公司 | **NVIDIA** | **AMD、Marvell、Astera** | **Broadcom、Arista、Marvell（Teralynx 也是乙太網路）** |

## 1.4 我的判斷：可能不會「一家獨大」，而是分市場（推論）
1. **NVIDIA 的系統會繼續用 NVLink**——GPU 市佔最大，所以 **NVLink 很可能仍是 scale-up 營收最大的一塊**（有市場預估認為到 2030 年 NVLink 仍拿走大部分 scale-up 交換器營收）。
2. **雲端業者自研晶片（Google TPU、Meta、OpenAI，多由 Broadcom 設計）最可能走乙太網路**——Broadcom 同時做 XPU 和交換器，自然往自家乙太網路方案帶；ESUN 由 Meta、微軟主導，也說明大客戶偏好這條路。
3. **UALink 目前的主要支柱是 AMD**；如果 AMD 的 GPU 市佔擴大、或某家大雲端業者明確選它，UALink 才會長大。**連 AMD 自己初期都走「UALink 包在乙太網路裡」**，這是個值得注意的訊號。
4. ⚠️ **ESUN 與 UALink 不完全互斥**：產業人士認為兩者可以互補，例如 UALink 的記憶體語意跑在乙太網路的實體層上。

## 1.5 對投資最重要的一句話
> **「交換器晶片押協定，實體層不押協定。」**
> - **押協定的**：交換器晶片（NVSwitch、Tomahawk、UALink 交換器）——**協定之爭的輸家，交換器就賣不掉**。
> - **不押協定的**：SerDes（高速收發電路）、重定時器、主動銅纜、光學 DSP、光模組——**不管哪種規矩贏，訊號都要從 A 點送到 B 點**。Credo、Astera 的 Taurus／Aries、Marvell 與 Broadcom 的 DSP 都屬於這一類。
> - ⇒ **實體層的風險不是協定，而是「銅轉光」**：跨機櫃之後銅線不夠用（448G 時約 2 公尺），**做銅線的要能轉到光，才不會被淘汰**。

---

# 第二部分：Serenity Step 1–9

## Step 1：適用性 ✅（四檔都在射程內）
AI 網路互連是 Serenity 射程內的核心主題（光通訊、超算）。**但四檔市值從 325 億到 1.7 兆美元，Serenity 原本是找「被忽視的小型瓶頸股」**——2026-09-14 已移除市值條件，改由 B 條件（認知落差）把關。

## Step 2：終端需求
| 需求 | 時點 | 誰受惠 |
|---|---|---|
| **雲端業者自研 XPU**（Google TPU、Meta、OpenAI、Anthropic） | 進行中，2027 年大幅放量 | Broadcom（FY27 AI 營收目標 1,150 億）、Marvell |
| **scale-up 從單機櫃擴到多機櫃** | 2027 起 | 交換器（Broadcom、Marvell、Astera）、光學（Marvell、Credo、Broadcom） |
| **200G／448G 世代的訊號完整性** | 2026–2028 | 重定時器（Astera）、AEC（Credo）、DSP（Marvell、Broadcom、Credo） |
| SemiAnalysis：2027 年新增約 51GW 資料中心（10/22 報告） | 2027 | 全部 |

## Step 3：供應鏈（由下往上）
| 層 | 內容 | 廠商 |
|---|---|---|
| L1 | AI 叢集（雲端業者、AI 實驗室） | Google、Meta、Amazon、微軟、OpenAI、Anthropic |
| L2 | 加速器（GPU／XPU） | NVIDIA、AMD；客製：Broadcom、Marvell |
| L3 | **scale-up／scale-out 交換器** | NVIDIA（NVSwitch、Spectrum）、**Broadcom（Tomahawk、Jericho）**、Marvell（Teralynx、UALink）、**Astera（Scorpio）** |
| L4 | **PCIe／CXL 交換器與重定時器** | **Astera（Aries、Taurus、Scorpio P、Leo）**、Broadcom（PEX）、Marvell（XConn） |
| L4 | **光學 DSP** | **Marvell（約 70%）**、Broadcom、Credo |
| L4 | **主動銅纜（AEC）** | **Credo（龍頭）**、Marvell 等 |
| L5 | **SerDes IP（高速收發電路）** | **Broadcom、Marvell、Credo**、Alphawave（已被 Qualcomm 收購）、Synopsys、Cadence |
| L6 | 晶圓、封裝、光源 | 台積電 N3／N2、CoWoS、矽光子；雷射：Coherent、Lumentum |

## Step 4：最深的瓶頸
1. 🔑 **224G／448G SerDes IP**：四家產品的核心都是同一種能力——**在極高速度下把訊號送得乾淨**。**真正有量產紀錄的 224G SerDes 供應商很少**（Broadcom、Marvell、Credo 是其中三家）。**這是四家共同的護城河，也是 Credo 能從 AEC 跳到光學 DSP 的原因。**
2. **交換器晶片**：寡占（NVIDIA、Broadcom 為主）；但受協定之爭影響。
3. **銅轉光的時點**：決定 AEC 的天花板。
4. **非瓶頸**：客製 XPU 的「設計服務」本身競爭激烈（還有 Alchip、GUC、MediaTek）。

## Step 5：硬條件

| 條件 | AVGO | MRVL | CRDO | ALAB |
|---|---|---|---|---|
| **壟斷／寡占** | ✅ 客製 XPU >70%（KIWI 7 月評估）、乙太網路交換器龍頭 | ✅ 光學 DSP 約 70%（與 Broadcom 合計 >90%）；客製 XPU 20–25% | ✅ AEC 龍頭（份額未查證） | ✅ PCIe 重定時器主導（份額未查證）；Scorpio 交換器面對 Broadcom PEX 競爭 |
| **論點純度 ≥30%** | ✅ AI 半導體 167 億 ÷ 總營收 296 億 ＝ **56%**（Q3 FY26） | ✅ 資料中心佔 **79%** | ✅ 約 100% 資料中心連接 | ✅ 約 100% |
| **多客戶** | ✅ Google、Meta、Anthropic、OpenAI 等 | ⚠️ 集中在 Amazon、微軟、Google（7 月已標記） | ⚠️ **最大客戶 39%（Q3 FY26）、前十大約 90%**；3–4 家 >10% | 🔴 **2025 年單一終端客戶 >70%、前三大約 86%**（第三方推測為 Amazon） |
| **資產負債表** | ✅ 現金 240 億、負債 594 億，但**單季自由現金流 137 億** | ✅ 獲利、淨負債可控（細項未讀到） | ✅ 現金約 7.6 億（本季明顯下降，原因未查證） | ✅ 現金與有價證券約 12.5 億 |

### A：資金流動證據——四家全過
| | 證據 |
|---|---|
| **AVGO** | Q3 FY26 營收 **296 億（+86%）**、AI 半導體 **167 億（+221%）**；**Q4 指引 348 億（+93%）**、AI **217 億（+236%）**；FY27 AI 營收目標 **1,150 億**；客製晶片需求仍大於供給 |
| **MRVL** | Q2 FY27 營收 **27.39 億（+37%）**、資料中心 21.7 億（+46%）；Q3 指引 31.5 億；FY28 目標約 200 億（Investor Day） |
| **CRDO** | Q1 FY27 營收 **4.79 億（+115%）**；Q2 指引 5.25–5.35 億；FY27 成長 >85%；**光學營收 >6 億**（新成長引擎） |
| **ALAB** | Q2 2026 營收 **3.92 億（+104%）**；**Q3 指引 5.4–5.6 億（季增約 40%）**；Scorpio 交換器提前一季成為最大產品線 |

⚠️ **毛利率方向不同**：Broadcom 非 GAAP 約 75%（穩）；Marvell 58.9% → 指引 57.5–58.5%（**客製晶片拉低**）；Credo 非 GAAP 68% → 67–69%；Astera 73.7% → 約 72%（交換器組合）。**GAAP 營益率 Credo 由 35.7% 掉到 25.2%**（與收購相關的攤銷與費用有關，細節未查證）。

### B：認知落差

**估值（10/27 收盤；「年化本益比」＝最近一季或下一季指引的非 GAAP EPS × 4，我的計算）**

| | 股價 | 自 6 月高點 | 一年 | 市值（自算） | 年化本益比 | 營收年增（最近／指引季） | **本益比 ÷ 成長** | 市場前瞻本益比 `[二手]` |
|---|---|---|---|---|---|---|---|---|
| **AVGO** | $342.33 | −29% | −5% | 約 1.69 兆（49.37 億股） | **約 26×**（Q3 非 GAAP EPS 3.32×4） | +93% | **約 0.28** | 未查到 |
| **MRVL** | $243.57 | −23% | +175% | 約 2,250 億（約 9.25 億股，推算） | **約 55×**（Q3 指引 1.10×4） | +52% | **約 1.06** | 56–62× |
| **CRDO** | $167.43 | −45% | +8% | 約 325 億（1.944 億股） | **約 35×**（Q1 1.20×4） | +98% | **約 0.36** | 27–35× |
| **ALAB** | $286.69 | −41% | +68% | 約 530 億（約 1.85 億股） | **約 60×**（Q3 指引 1.185×4） | +138% | **約 0.44** | 55–72× |

| B 的三項 | AVGO | MRVL | CRDO | ALAB |
|---|---|---|---|---|
| ① 低於同業中位（四家年化本益比中位約 45×） | ✅ 26× | ❌ 55× | ✅ 35× | ❌ 60× |
| ① 低於自身歷史 | 未計算（資料源受限） | ❌（7 月 fwd 約 60×，相近） | 未計算 | 未計算 |
| ② 自最近一次 A 證據（財報）起未重評價 | ✅ 9/11 收 361.99 → **−5.4%**（財報日為推估） | ❌ 8/28 收 216.62 → **+12.4%** | ✅ 9/9 收 167.92 → **−0.3%** | ✅ 8/5 收 318.43 → **−10.0%** |
| ③ 未被賣方點名 | ❌ | ❌ | ❌ | ❌ |
| **判定** | **✅ 2/3** | **❌ 1/3** | **✅ 2/3** | **❌ 1/3**（① 不過） |

## Step 6：紅旗

| 紅旗 | AVGO | MRVL | CRDO | ALAB |
|---|---|---|---|---|
| 無限制增資 | ❌ | ⚠️ 收購發股、**Google 最多 5,897 萬股認股權證**、NVIDIA 20 億優先股 | ❌ | ⚠️ **Amazon 認股權證**（條款未查） |
| **單一客戶 >50%** | ❌ | ❌ | ⚠️ 39%（接近但未過） | 🔴 **觸發：>70%** |
| 中國①②③ | ❌ | ❌ | ❌（台灣與中國有營運據點，非紅旗定義） | ❌ |
| 技術時點 >2028 | ❌ | ⚠️ Scale-in 與 Photonic Fabric 是遠期，但主業不是 | ❌ | ❌ |
| 毒性債務 | ❌（負債 594 億但現金流極強） | ❌ | ❌ | ❌ |
| （清單外）技術替代 | — | — | 🔴 **銅轉光**：跨機櫃 scale-up 不用銅 | ⚠️ 協定押注（UALink） |

## Step 7：估值（見 Step 5 B 表）
- **最便宜（成長調整後）**：Broadcom（約 0.28）＞ Credo（約 0.36）＞ Astera（約 0.44）＞ Marvell（約 1.06）。
- ⚠️ 這個比較**偏向成長快的季度**：Broadcom 的 +93% 有部分來自 VMware 以外的 AI 爆發，延續性要看 FY27 的 1,150 億 AI 營收能否兌現；Credo、Astera 的高成長基期較小。
- **Broadcom 的另一面**：半導體外還有 30% 軟體（VMware）營收，**AI 純度只有 56%**，是四家中最「不純」的。

## Step 8：催化劑時間表（日期多為推估，以公司公告為準）
| 時點 | 事件 | 看什麼 |
|---|---|---|
| **11/3** | **Astera Q3 財報**（已排定） | 能否交出 5.4–5.6 億；Scorpio X 放量；**最大客戶佔比是否下降** |
| 11 月 | OCP 全球峰會 | ESUN 規格進度、UALink 交換器展示 |
| **約 12/4** | Marvell Q3 FY27 | XConn 貢獻、scale-up optics 時程（同日報告） |
| **約 12 月初** | **Credo Q2 FY27** | **光學營收比重**（>6 億全年目標的進度）＝銅轉光的答案 |
| **約 12/10** | **Broadcom Q4 FY26** | AI 217 億是否兌現；**FY27 1,150 億是否重申** |
| 2026H2–2027 | AMD Helios 出貨 | UALink 是原生還是包在乙太網路裡 |
| 2027 | 原生 UALink 交換器量產 | 協定之爭的第一個真實數據 |

## Step 9：報告

### 🐻 熊市情境（先寫）
- **AVGO**：AI 營收高度集中在少數雲端客戶；客製 XPU 每代都要重新競爭（Google 已讓 Marvell 拿下 TPU 周邊）；負債 594 億；**股價一年 −5%、自高點 −29%，市場可能在擔心 AI 資本支出見頂**。
- **MRVL**：最貴；毛利率被客製晶片拉低；押 UALink；稀釋來源多。
- **CRDO**：**跨機櫃 scale-up 不用銅**，AEC 成長已在「正常化」；客戶集中（前十大 90%）；股價自高點 −45%、9 月財報後未反彈。
- **ALAB**：🔴 **單一客戶 >70%**；押 UALink 與 PCIe 交換器，Broadcom 與 Marvell 都在同一塊競爭；最貴之一。

### 🐂 牛市情境
- **AVGO**：**唯一同時是「客製 XPU 一哥」與「乙太網路交換器一哥」**，乙太網路若成為自研晶片的 scale-up 標準，它兩邊都吃；**成長調整後最便宜**；自由現金流驚人。
- **MRVL**：scale-up 全線（XPU attach＋光引擎＋交換器）＋Google 合約；FY31 目標 800 億。
- **CRDO**：SerDes 能力讓它從銅轉進光學 DSP（FY27 光學 >6 億）；**協定中立**；成長調整後第二便宜。
- **ALAB**：Q3 指引季增 40%；Scorpio 交換器成為最大產品線；Taurus 同時支援乙太網路、UALink、ESUN（實體層協定中立）。

### 否證條件
- **AVGO**：FY27 AI 營收目標下修；主要 XPU 客戶轉單；ESUN／SUE 被 UALink 取代
- **MRVL**：毛利率跌破 55%；XConn／scale-up optics 延遲（同日報告）
- **CRDO**：**光學營收全年 <6 億**；AEC 營收連兩季下滑
- **ALAB**：最大客戶佔比不降；Scorpio 被 Broadcom PEX 或 Marvell 替代

### 🔄 升級條件
- **AVGO**：自 B 的角度只差「自身歷史估值」與「賣方點名」；**若 12 月確認 FY27 AI 1,150 億且股價未反應** ⇒ 在 KIWI 框架下屬「品質＋成長調整後便宜」，可作為「互連」主題的核心持股候選（⚠️ 但它不是 Serenity 式的小型瓶頸 alpha）
- **CRDO**：**12 月財報光學營收佔比明顯上升**（證明銅轉光的風險已被管理）＋最大客戶 <35%
- **MRVL**：回到 KIWI 分批區 $175–195，或 FY28 EPS 上修使本益比降到 40× 以下
- **ALAB**：最大客戶佔比降到 50% 以下

## 結案聲明
**本次掃描涵蓋**：L2–L5（加速器、交換器、PCIe／CXL、光學 DSP、AEC、SerDes）四家公司的財報與估值；三種 scale-up 協定的現況
**本次明確未涵蓋**：**L6 光源與矽光子代工**（雷射、台積電 COUPE）、NVIDIA 與 Arista 的交換器業務、AMD Helios 實際出貨的協定模式、**各家在 AEC／重定時器的實際市佔**、Marvell 與 Credo 的資產負債表細項、四家的**自身歷史估值百分位** ← 這幾層尚未關閉
**結論僅對涵蓋的層級有效。**

## 誠實邊界
1. **Broadcom、Astera 財報為一手（SEC）；Marvell、Credo 為二手**（官網與 stocktitan 在雲端被擋）。Marvell 股數是由淨利 ÷ EPS 推算。
2. **成長率用的「前一年同期營收」是依過往財報記憶，本次未重新查證**；Broadcom 的 +93% 有公司公告佐證。
3. **年化本益比是我用單季非 GAAP EPS × 4 算的**，和市場的前瞻本益比定義不同（Credo、Astera、Marvell 兩者大致吻合）。
4. Broadcom Q3 財報日期（9/10）為推估；B-② 的起算點會因此差一兩天。
5. **協定部分多數來源是產業部落格與廠商相關文章**，AMD Helios 的實際協定模式各來源說法不一。
6. 自身歷史估值百分位**未計算**（本次無法取得長期 EPS 序列）。

## 來源
**一手**：Broadcom 8-K Ex.99（Q3 FY26，SEC）・Astera Labs 8-K Ex.99.1（Q2 2026，SEC）・Yahoo Finance query1（AVGO、MRVL、CRDO、ALAB 日線）・Google Sheet「KIWI 持倉表」
**二手（搜尋摘要）**：Marvell Q2 FY27（Futurum、Converge Digest、Quartz、BigGo、SEC 8-K 摘要）・Credo Q1 FY27（Alpha Spread、Nasdaq 新聞稿、Credo IR、Motley Fool 逐字稿、TradingKey）・Credo 客戶集中（Motley Fool、Investing.com 逐字稿、Credo 10-K 摘要）・Astera 客戶集中（Astera 10-K FY2025 摘要）・前瞻本益比（Motley Fool、Yahoo Finance、24/7 Wall St.）・Broadcom FY27 AI 目標（KuCoin、Investing.com 逐字稿）・協定：Spheron、HPCwire、Tom's Hardware、Introl、SiliconANGLE、OCP 官方公告、Broadcom 官方文章、Arista 部落格、SDxCentral、Converge Digest、simpletechtrend

## Update Log
- 2026-10-28 v1.0：建檔。**協定**：NVLink（封閉、唯一大量出貨；Fusion 部分開放）、UALink（開放聯盟、1.0 規格 200G／1,024 顆、原生交換器未出貨、主要採用者 AMD 且初期包在乙太網路裡）、乙太網路（Broadcom SUE＋Tomahawk Ultra、OCP ESUN 由 Meta／微軟主導）；**投資要點＝交換器押協定、實體層不押協定**。**Serenity**：四檔 A 全過；B：**AVGO 2/3（年化本益比約 26×、成長調整後約 0.28 最便宜）**、CRDO 2/3（約 35×、0.36；銅轉光是主要風險）、MRVL 1/3（約 55×、1.06 最貴）、ALAB 1/3（約 60×；🔴 單一客戶 >70%）。判定：AVGO、CRDO、MRVL 觀察；ALAB 避開。四檔皆未持有（Sheet 09-08）。

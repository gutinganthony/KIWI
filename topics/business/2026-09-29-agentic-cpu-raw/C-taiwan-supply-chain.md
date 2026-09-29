# Research C：Agentic AI → 伺服器 CPU 瓶頸｜台股受惠標的篩選

- 研究日期：2026-09-29
- 價格／本益比／營收：FinMind API（`TaiwanStockPrice` / `TaiwanStockPER` / `TaiwanStockMonthRevenue`），2026-09-29 抓取。
  - 股價：2026-09-29 收盤。YTD 的基準是 2025-12-31 收盤；「近 3 月」的基準是 2026-06-30 收盤。
  - 本益比（PER）：FinMind 的歷史本益比（用近四季 EPS 算）。日期標在欄位內，有些只更新到 09-24。
  - 營收 YoY：2026/06、07、08 三個月（9 月營收要到 10/10 前才公布）。
- 產業資訊：WebSearch（工商、經濟日報、MoneyDJ、TrendForce、CNBC、Tom's Hardware 等；文末附連結）。technews、cnyes、vocus、ctee 全文被 egress proxy 擋住，只能用搜尋摘要。
- `[推論]` = 我自己的推估，沒有公開資料直接佐證。

## 0. 主題前提：確認成立

- CPU:GPU 配置比，從訓練時代的 1:8、推論時代的 1:4，往代理式 AI 的 1:2～1:1 走。AMD 和 Intel 都公開講過會走到 1:1（工商 2026-09-01、T客邦）。Arm 估每 GW 資料中心需要的 CPU 核心數，從 3 千萬顆增加到 1.2 億顆。
- 2026 通用伺服器出貨預估從 1,601 萬台（+5%）上修到 1,784 萬台（+17%）。外資估 2026–28 通用伺服器 CAGR 約 26%。
- Intel／AMD 伺服器 CPU 缺貨：Intel 通路只能滿足約 4 成配額，交期 8–30 週以上。
- Meta 跟 AWS 簽了數十億美元合約，部署數千萬個 Graviton5 核心（TSMC 3nm）。Meta 也是 Arm 自有晶片「AGI CPU」（TSMC 3nm，136 核）的首發客戶。
- 自研 CPU 誰做：
  - Google Axion：創意（3443）。
  - Microsoft Cobalt 200：創意有參與（法人估 2027 年 Microsoft 相關營收 ≥2.5 億美元）。
  - AWS Graviton：Annapurna Labs 自己設計，查無台灣設計服務廠參與的公開證據。世芯（3661）接的是 AWS Trainium（加速器），不是 CPU。
  - Meta：外購 Graviton5 加上 Arm AGI CPU；創意傳可能拿到 MTIA 600（加速器，不是 CPU）。
  - 以上所有 Arm CPU 都在台積電 3nm 生產；AMD Venice 用台積電 2nm，搭配 SoIC-X（3D V-Cache 版本最高 1,152MB L3）。

## 1. 數據總表（FinMind；價格日 2026-09-29）

| 代號 | 名稱 | 股價 | PER（日期） | YTD | 近3月 | 距今年高點 | 營收 YoY（6/7/8月） |
|---|---|---|---|---|---|---|---|
| 3533 | 嘉澤 | 1,710 | 20.9（09-29） | +32.0% | −19.0% | −42.1% | +17 / +19 / +20% |
| 5274 | 信驊 | 19,395 | 132.3（09-24） | +167.1% | +17.6% | −11.0% | +67 / +98 / +118% |
| 3037 | 欣興 | 1,165 | 77.6（09-29） | +429.5% | +8.9% | −5.3% | +36 / +44 / +56% |
| 8046 | 南電 | 1,270 | 149.2（09-29） | +427.0% | +7.2% | −10.2% | +50 / +50 / +41% |
| 3189 | 景碩 | 955 | 177.2（09-29） | +500.6% | +7.2% | −4.1% | +32 / +36 / +41% |
| 3443 | 創意 | 7,925 | 218.5（09-24） | +272.9% | +63.6% | −7.3% | +104 / +158 / +111% |
| 3661 | 世芯-KY | 3,685 | 55.3（09-24） | +5.0% | −11.8% | −34.7% | +15 / +182 / +274% |
| 4966 | 譜瑞-KY | 569 | 18.2（09-24） | −2.6% | −9.5% | −38.8% | +12 / −4 / +0% |
| 5269 | 祥碩 | 1,475 | 15.7（09-29） | +21.9% | +0.3% | −11.1% | −22 / −38 / −33% |
| 2330 | 台積電 | 2,475 | 28.7（09-29） | +59.7% | +2.7% | −2.4% | +68 / +45 / +53% |
| 3711 | 日月光投控 | 687 | 49.7（09-29） | +174.3% | +1.0% | −5.8% | +33 / +43 / +46% |
| 2368 | 金像電 | 1,120 | 39.7（09-24） | +63.0% | −6.7% | −29.1% | +78 / +77 / +76% |
| 2383 | 台光電 | 4,920 | 76.9（09-29） | +199.1% | −8.7% | −24.0% | +121 / +129 / +130% |
| 2059 | 川湖 | 12,115 | 66.8（09-29） | +223.1% | +64.6% | −19.7% | +221 / +356 / +344% |
| **8271** | **宇瞻** | 199.5 | 5.0（09-29） | +76.5% | +2.6% | −26.4% | +201 / +165 / +177% |
| 3260 | 威剛 | 377 | 4.9（09-24） | +34.9% | −7.8% | −28.2% | +212 / +331 / +280% |
| **2303** | **聯電** | 153.5 | 23.2（09-24） | +211.7% | −6.7% | −17.3% | +23 / +19 / +31% |
| *3653* | *健策（補）* | 6,895 | 156.2（09-24） | +151.2% | +101.0% | −3.7% | +58 / +91 / +91% |
| *6515* | *穎崴（補）* | 5,675 | 92.9（09-29） | +99.8% | −29.8% | −50.6% | +288 / +156 / +233% |
| *6669* | *緯穎（補）* | 2,100（除權後） | FinMind 6.7 → **約 20 `[推論]`** | **約 +40% `[推論]`** | **約 +36% `[推論]`** | — | +30 / +39 / +50% |
| *2408* | *南亞科（補）* | 506 | 19.6（09-29） | +162.2% | +11.8% | −11.1% | +621 / +720 / +561% |

資料注意事項：
- **6669 緯穎** 在 9/2 除權（配股 20 元，等於每股配 2 股）。股價從 7,800 跳到 2,610，約 1 拆 3。FinMind 價格沒有還原，本益比也還用舊股本 EPS。
  - 還原後：2,100×3 ≈ 6,300，對應 YTD 約 +40%、近 3 月約 +36%，PER 約 6.7×3 ≈ 20。這些是 `[推論]`。
  - 除權前 8/26 的 FinMind PER 是 21.75，跟推估吻合。
- **8271／3260** 的 PER 約 5 倍，是記憶體循環高峰獲利（含低價庫存利差）撐出來的。這不代表便宜，循環股在高峰時 PER 最低。
- **5274／3443** 的 PER 用近四季 EPS 計算，高成長期會失真。信驊法人給 22,000 目標價，用的是 2027–28 平均 EPS 的 55 倍。換算回來，現價大約是 2027E 本益比 48 倍 `[推論]`。

## 2. 逐檔：跟 agent CPU 主題的連結

「階」＝ 1 階：直接賣給 CPU 或 CPU 伺服器的零組件／服務；2 階：透過伺服器台數或記憶體價格間接受惠。

| 代號 | 主題連結（產品／客戶） | 階 | 相關營收佔比 | 一句話風險 |
|---|---|---|---|---|
| 3533 嘉澤 | CPU socket（Intel、AMD 雙客戶；Venice SP7 socket 下半年放量）＋PCIe 6 連接器＋SoCAMM/CAMM2 連接器＋液冷 QD；NPO socket 2027 量產 | 1 | 伺服器佔 H1 營收 55.4%（法說），CPU socket 佔伺服器的大宗 `[推論]` | 8/14 三家外資下修：零組件缺料讓新平台 socket 放量延後；銅、金、塑膠佔成本 65%，毛利承壓 |
| 5274 信驊 | 每個 CPU 節點都要 1 顆 BMC。CPU 機櫃獨立化、台數增加，量價齊揚（AST2700 單價 22–25 美元，AST2600 是 16 美元）；2026 出貨 3,100 萬顆（+63%），2027 估 4,460 萬顆 | 1 | 約 100% 伺服器（BMC）；通用伺服器約 5–6 成 `[推論]` | 估值已經反映 2027 年；伺服器台數只要不如預期，股價下修的彈性很大 |
| 3037 欣興 | 大尺寸 ABF：AMD CPU 與 GPU／ASIC 都有；ABF 缺口估 2026 年 8%、2027 年 27%，Q3 起每季漲價 10–15% | 1 | CPU 載板約 2–3 成 `[推論]` | 已漲 4.3 倍；主要驅動力其實是 GPU／ASIC 載板，不是 CPU |
| 8046 南電 | ABF：Intel 伺服器 CPU 是傳統大客戶 `[推論]`，加上 GPU／ASIC | 1 | CPU 約 3 成 `[推論]` | PER 149，已漲 4.3 倍 |
| 3189 景碩 | ABF＋BT；高階 ABF 受注目 | 1–2 | CPU 比重查無 | PER 177，漲幅 6 倍 |
| 3443 創意 | **Google Axion**（Axion 2：2026 年 120–130 萬顆，約 9–10 億美元；2027 年 Google CPU 相關營收接近 28 億美元）＋**Microsoft Cobalt 200** | 1（純度最高） | 2026 年 Axion 佔營收 >30%（法人） | PER 218、近 3 月 +64%，已經在反映 2027–28 年 |
| 3661 世芯 | AWS **Trainium**（加速器）；**Graviton 由 Annapurna 自研，查無世芯參與** | 2 | CPU 相關：查無 | 主題上跟 CPU 關聯弱；Trainium 3 放量的節奏才是關鍵 |
| 4966 譜瑞 | PCIe 5/6 retimer（CPU 到 GPU、CXL 之間的 I/O）；2026 年出貨數百萬顆，2027 年目標翻倍 | 1（小） | 資料中心 <1 成 `[推論]`（主力仍是筆電 eDP／TCON） | 本業靠 PC 撐，營收 YoY 持平；retimer 這塊 Astera Labs 市佔很高 |
| 5269 祥碩 | PCIe Gen4/5/6 packet switch，目標今年佔營收 10% | 2 | 約 10% | **CPU 缺貨反而拖累 PC 主機板（−15～−20%）**，營收 YoY −33%，是主題的輸家 |
| 2330 台積電 | 所有 hyperscaler Arm CPU 都用 3nm（Graviton5、Axion、Cobalt 200、Arm AGI CPU）；AMD Venice 用 2nm＋SoIC-X（3D 堆疊快取）；Intel 部分 tile | 1 | 伺服器 CPU 約 8–12% `[推論]` | 權重太大、純度被稀釋；CPU 跟 AI 加速器搶產能 |
| 3711 日月光 | CPU 封測（Intel、AMD 的部分封測與測試）`[推論]` | 2 | 查無 | 已漲 1.7 倍，主力驅動是 AI 先進封裝 |
| 2368 金像電 | **全球最大通用伺服器 PCB**；Venice／Diamond Rapids 走 PCIe 6、16 通道記憶體，層數與材料升級，量價齊揚 | 1 | 通用伺服器板約 5 成以上 `[推論]` | 泰國廠投產的良率；AI 板競爭 |
| 2383 台光電 | 高階 CCL（伺服器、交換器）；CPU 平台換代，材料升級 | 2 | CPU 伺服器約 2–3 成 `[推論]` | PER 77；主力驅動是 GPU 與 800G 交換器 |
| 2059 川湖 | 滑軌：GB300、AWS／Google／Meta ASIC 機櫃，也包含通用伺服器 | 2 | 通用伺服器約 2–3 成 `[推論]` | 近 3 月 +65%，營收 YoY 3 倍多，基期風險 |
| 3653 健策（補） | 伺服器 CPU **ILM**（扣具，打進 Intel）＋均熱片 lid（主要是 GPU／ASIC，新 TR Lid） | 1 | CPU ILM 約 1–2 成 `[推論]` | 近 3 月翻倍，漲點主要來自 GPU lid，不是 CPU |
| 6515 穎崴（補） | HPC 晶片測試座／探針卡（CPU、GPU、ASIC 都有） | 2 | CPU 比重查無 | 從高點回檔一半，波動極大 |
| 6669 緯穎（補） | Meta／Microsoft 通用伺服器 ODM；Q3 AI 伺服器與通用伺服器出貨各半；外資估 2026–28 通用伺服器 CAGR 約 26% | 1 | 通用伺服器約 5 成出貨量（公司說法） | ODM 毛利低；除權後籌碼與填權表現 |
| 2408 南亞科（補） | DRAM 原廠：CPU 伺服器需要更多 DDR5／RDIMM。原廠產能優先給 HBM／LPDDR5X（SOCAMM），標準 DDR5 缺貨 | 2 | 伺服器 DRAM 約 3–4 成 `[推論]` | 記憶體循環反轉；LPDDR5X 與 SOCAMM 主要是三星、海力士、美光的份額 |

## 3. 使用者持股判斷

### 8271 宇瞻 → **間接受惠（2 階，吃價格，不吃產品）；以主題純度來看偏中性**

- 產品結構（H1 法說）：DRAM 模組 64.35%、NAND 35.40%。客戶是工控、網通資安、半導體設備、Edge AI 這類利基市場，**不是 hyperscaler 的 RDIMM／MRDIMM 主力供應商**。
- 它推出的 LPDDR5 SOCAMM2 模組，鎖定的是邊緣 AI、AI PC 和輕薄筆電，沒看到打進雲端 CPU 伺服器的報導。
- 真正的受惠路徑：代理式 AI 帶動 CPU 伺服器增加，原廠產能優先給 HBM／LPDDR5X（SOCAMM），擠壓標準 DDR4／DDR5 供給，模組價格上漲，加上 124 億庫存的利差。
- 公司自己說缺貨會延續到 2027 年中。Q2 EPS 20.93 元、H1 EPS 35.51 元都創新高，PER 約 5 倍。
- **結論**：獲利確實吃到記憶體超級週期，但這是「記憶體循環股」，不是「agent CPU 概念股」。它的風險跟這篇文章的論點無關，**要盯的是 DRAM 合約價何時反轉，以及 124 億庫存可能的跌價損失**。低 PER 是循環高峰的特徵，不是安全邊際。

### 2303 聯電 → **中性（跟主題弱相關）**

- 跟 Intel 合作的 12nm：2026 年交付 PDK 與 IP，2027 年投片，2027 年底量產。目標是 Intel Foundry 的外部客戶（通訊、影像、RF 等成熟特殊製程）`[推論]`，**不是替 Intel 代工伺服器 CPU**。
- 矽中介層：產能 3,000 片擴到 6,000 片，但 7 月法說明講「短期沒有大幅擴充 interposer 的壓力」，而且用途以 AI 加速器封裝為主。先進封裝已有 10 家以上客戶、35 個以上新案，但**查無用在伺服器 CPU 3D 快取的公開證據**。3D V-Cache 是台積電 SoIC 的獨家。
- 間接連結：伺服器 CPU 周邊的 PMIC、SPD hub、BMC 以外的電源晶片，可能在聯電的 22/28nm 投片 `[推論]`，推升成熟製程稼動率（Q3 >90%）與 2027 年漲價空間。這是一般性的伺服器景氣，不是 agent CPU 特有的。
- 今年股價 +212%，驅動因素是：成熟製程漲價、Q2 EPS 3.39 元創新高、Q3 毛利率 34–36%、矽光子與先進封裝題材。**持有理由應該跟這些驅動因素連結，不是 agent CPU**。

## 4. 排序表：相關度 × 估值／位置吸引力

評分定義：
- **相關度** 1–5：主題對公司獲利的邊際影響 × 確定性（1 階加分，佔比低則扣分）。
- **估值／位置** 1–5：5 = 本益比合理而且從高點回檔、有營收支撐；1 = 本益比極高、剛噴出，或基本面轉弱。

| 排名 | 代號 | 名稱 | 相關度 | 估值／位置 | 乘積 | 理由摘要 |
|---|---|---|---|---|---|---|
| 1 | 3533 | 嘉澤 | 5 | 4 | **20** | CPU socket 純 1 階。PER 21，今年高點回落 42%，是全清單唯一「主題最純 × 估值未炒」的標的；風險是放量延後、原物料成本 |
| 2 | 2368 | 金像電 | 4 | 4 | **16** | 通用伺服器 PCB 龍頭。營收 YoY +76%，PER 40，從高點回落 29% |
| 2 | 6669 | 緯穎 | 4 | 4 | **16** | Meta／Microsoft 通用伺服器 ODM。還原後 PER 約 20 `[推論]`，營收 YoY +50% |
| 4 | 2330 | 台積電 | 4 | 3 | 12 | 所有自研 Arm CPU 加 Venice 2nm、SoIC，確定性最高但純度被稀釋 |
| 5 | 2408 | 南亞科 | 3 | 3 | 9 | 記憶體頻寬方向的 2 階，PER 20 還在獲利爆發期；循環風險 |
| 5 | 4966 | 譜瑞 | 3 | 3 | 9 | PCIe 6 retimer 是 I/O 方向，PER 18 夠便宜，但營收持平、資料中心比重還小 |
| 7 | 5274 | 信驊 | 4 | 2 | 8 | BMC 是台數的最佳代理指標，但約 48 倍 2027E `[推論]`，股價靠近高點 |
| 7 | 3037 | 欣興 | 4 | 2 | 8 | ABF 缺貨加漲價，但已漲 4.3 倍、PER 78 |
| 7 | 3661 | 世芯 | 2 | 4 | 8 | 估值回落（PER 55、高點 −35%），但**不是 CPU 題材**（Trainium） |
| 7 | 6515 | 穎崴 | 3 | 2.5 | 7.5 | 腰斬後值得留意，但 PER 93 |
| 11 | 8271 | **宇瞻（持有）** | 2 | 3 | 6 | 見 §3：受惠於記憶體價格，不受惠於 agent CPU 產品 |
| 11 | 3260 | 威剛 | 2 | 3 | 6 | 同宇瞻，規模較大，AI 伺服器出貨在轉移中 |
| 11 | 2303 | **聯電（持有）** | 2 | 3 | 6 | 見 §3：中性 |
| 11 | 3711 | 日月光 | 3 | 2 | 6 | 2 階，已漲 1.7 倍 |
| 11 | 2383 | 台光電 | 3 | 2 | 6 | 材料升級，PER 77 |
| 11 | 5269 | 祥碩 | 2 | 3 | 6 | CPU 缺貨傷 PC 本業，是主題的反向受害者 |
| 17 | 3443 | 創意 | 5 | 1 | 5 | **主題純度第一**（Axion＋Cobalt 200），但 PER 218、近 3 月 +64%，價格已反映 2027–28 年 |
| 18 | 2059 | 川湖 | 3 | 1.5 | 4.5 | 近 3 月 +65%，營收基期極高 |
| 19 | 8046 | 南電 | 4 | 1 | 4 | PER 149 |
| 19 | 3653 | 健策 | 4 | 1 | 4 | 近 3 月翻倍，主要驅動是 GPU lid |
| 21 | 3189 | 景碩 | 3 | 1 | 3 | PER 177，漲幅 6 倍 |

**只看相關度的前 5 名**：創意（5）、嘉澤（5），以及台積電、信驊、金像電、緯穎、欣興、南電、健策（都是 4）。其中估值還沒被炒高的，只剩嘉澤、金像電、緯穎。

## 5. 限制

- 相關營收佔比大多是 `[推論]`，公司沒有揭露 CPU 與 GPU 的拆分。
- 法說與外資數字來自搜尋摘要，不是原文；ctee、cnyes、vocus、technews 全文被 proxy 擋住。
- 近 3 月的基準日是 06-30。緯穎的 FinMind 價格沒有還原除權，已經人工換算。
- 9 月營收尚未公布（10/10 前）。

## Sources

- FinMind API：https://api.finmindtrade.com/api/v4/data（TaiwanStockPrice／TaiwanStockPER／TaiwanStockMonthRevenue，2026-09-29 抓取）
- [工商：代理式AI工作負載大增 CPU需求回神 台鏈發燒（2026-09-29）](https://www.ctee.com.tw/news/20260929700074-439901)
- [工商：AMD：CPU／GPU配置走向1比1（2026-09-01）](https://www.ctee.com.tw/news/20260901700807-430704)
- [T客邦：Intel 預估 GPU 與 CPU 需求量提升至 1:1](https://www.techbang.com/posts/129129-intel-data-center-cpu-gpu-1-1)
- [TrendForce：2026 Agentic AI Wave: CPU Shortage](https://www.trendforce.com/research/download/RP260408AD)
- [Quartz：CPUs join the chip shortage](https://qz.com/ai-cpu-shortage-2026)
- [DCD：Meta signs agreement with AWS for Graviton5](https://www.datacenterdynamics.com/en/news/meta-signs-agreement-with-aws-for-large-scale-graviton5-deployment/)
- [CNBC：Arm launches its own CPU with Meta as first customer](https://www.cnbc.com/2026/03/24/arm-launches-its-own-cpu-with-meta-as-first-customer.html)
- [Tom's Hardware：Microsoft Cobalt 200](https://www.tomshardware.com/tech-industry/semiconductors/microsoft-unveils-azure-cobalt-200-cpu)
- [經濟日報：創意將為谷歌打造 Axion CPU](https://money.udn.com/money/story/5612/9126476)
- [旺得富：創意股價首破6000元](https://wantrich.chinatimes.com/news/20260826900199-420101)
- [優分析：創意 雙晶粒CPU](https://uanalyze.com.tw/articles/7492455434)
- [富果：嘉澤法說 2026-05-14](https://blog.fugle.tw/post/earnings-call-3533-2026-05-14)
- [MoneyDJ：嘉澤伺服器新品加速出貨](https://www.moneydj.com/kmdj/news/newsviewer.aspx?a=e8b25235-45b2-4473-87eb-c3400cd4ba92)
- [工商：信驊明年出貨拚4460萬顆（2026-08-07）](https://www.ctee.com.tw/news/20260807701008-430201)
- [豐雲學堂：Agentic AI 點燃 CPU 需求，ABF 載板三雄](https://www.sinotrade.com.tw/richclub/hotstock/Agentic-AI-%E9%BB%9E%E7%87%83-CPU-%E9%9C%80%E6%B1%82-ABF-%E8%BC%89%E6%9D%BF%E4%BE%9B%E7%B5%A6%E8%BD%89%E7%B7%8A-%E8%BC%89%E6%9D%BF%E4%B8%89%E9%9B%84%E6%99%AF%E7%A2%A9-%E5%8D%97%E9%9B%BB-%E6%AC%A3%E8%88%88%E6%80%8E%E9%BA%BC%E9%81%B8-%E8%82%A1%E5%B8%82%E8%A9%B1%E9%A1%8C-6a437daac99818e56349acea)
- [TechNews：AI 載板 2028 年短缺達 35%](https://finance.technews.tw/2026/04/27/ai-carrier-board-shortage/)
- [時報：PCIe迎成長週期 祥碩、譜瑞受惠](https://www.chinatimes.com/realtimenews/20260724002026-260410)
- [富果：譜瑞法說 2026-09-09](https://blog.fugle.tw/post/earnings-call-4966-2026-09-09)
- [富果：祥碩法說 2026-05-12](https://blog.fugle.tw/post/earnings-call-5269-2026-05-12)
- [AMD IR：Venice on TSMC 2nm](https://ir.amd.com/news-events/press-releases/detail/1287/amd-announces-production-ramp-of-next-generation-amd-epyc-processor-venice-on-tsmc-2nm-process-technology)
- [T客邦：AMD 第6代 EPYC](https://www.techbang.com/posts/131647-amd-aai-2026-epyc-cpu)
- [聯合：金像電 兩檔有戲](https://udn.com/news/story/7255/9522773)
- [工商：川湖成台股第三檔萬金股](https://www.ctee.com.tw/news/20260807700771-430502)
- [Yahoo：健策均熱片 目標價](https://tw.news.yahoo.com/%E7%9C%8B%E5%A5%BD%E6%96%B0%E5%9D%87%E7%86%B1%E7%89%87-%E5%81%A5%E7%AD%96%E7%9B%AE%E6%A8%99%E5%83%B9-%E7%8D%B2%E6%B3%95%E4%BA%BA%E8%AA%BF%E9%AB%98%E8%87%B3-%E9%80%99%E6%95%B8%E5%AD%97-024100450.html)
- [聯合：穎崴8月業績創高](https://udn.com/news/story/7252/9740951)
- [Digitimes：緯穎 AI／通用伺服器 3Q26 各半](https://www.digitimes.com.tw/tech/dt/n/shwnws.asp?id=0000768061_KNB10J8C5NKCLF2VRS2UG)
- [口袋學堂：緯穎 9/2 除權](https://www.pocket.tw/school/report/SCHOOL/7853/)
- [工商：宇瞻第二季每股賺20.93元](https://www.ctee.com.tw/news/20260725700157-439901)
- [富果：宇瞻法說 2026-07-24](https://blog.fugle.tw/post/earnings-call-8271-2026-07-24)
- [FTNN：記憶體模組廠存貨124億](https://www.ftnn.com.tw/news/564066)
- [財報狗：SOCAMM2 與 LPDDR 供應](https://statementdog.com/news/16719)
- [聯合：聯電與英特爾12奈米 2027年量產](https://udn.com/news/story/7240/9528066)
- [豐雲學堂：聯電法說 Q2 EPS 3.39元](https://www.sinotrade.com.tw/richclub/hotstock/%E8%81%AF%E9%9B%BB%E6%B3%95%E8%AA%AA-%E7%AC%AC%E4%BA%8C%E5%AD%A3EPS%E9%81%943-39%E5%85%83%E5%89%B5%E5%96%AE%E5%AD%A3%E6%96%B0%E9%AB%98-%E8%B3%87%E6%9C%AC%E6%94%AF%E5%87%BA%E4%B8%8A%E8%AA%BF%E8%87%B320%E5%84%84%E7%BE%8E%E5%85%83-Q3%E7%94%A2%E8%83%BD%E5%88%A9%E7%94%A8%E7%8E%87%E4%B8%8A%E7%9C%8B%E9%80%BE90--%E8%82%A1%E5%B8%82%E8%A9%B1%E9%A1%8C-6a69ce9b59e586efa18faba9)
- [經濟日報：聯電先進封裝獲10家客戶導入](https://money.udn.com/money/story/5612/9472367)
- [威剛法說 2026-08-06（富果）](https://blog.fugle.tw/post/earnings-call-3260-2026-08-06)

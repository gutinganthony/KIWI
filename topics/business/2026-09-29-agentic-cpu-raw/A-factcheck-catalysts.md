# Research A: 事實查核，〈AI Agent 如何改寫 AI 伺服器 CPU 的設計〉(Redefine Innovation / Andrew Hu, 2026-09-24)

查核日期：2026-09-29。方法：WebSearch 為主。WebFetch 對 arxiv / theregister / tomshardware / alphaxiv 等網域被 egress proxy 擋下（EGRESS_BLOCKED），所以**多數事實取自搜尋結果摘要，沒有逐字讀原文**。表內日期來自 URL 路徑或摘要內文。股價是用 Yahoo chart API 直接算的（收盤到 2026-09-28）。
標記：`已確認`＝至少一個具名來源寫明；`[推論]`＝由已確認事實推導；`[推測]`＝沒有來源，是我的判斷；`未證實`＝查不到。

---

## 1. 文章引用的三則新聞

### (a) 2026-02：Meta 大規模部署 NVIDIA Grace CPU-only 伺服器，下一代用 Vera，`已確認`
- 2026-02-17，NVIDIA 與 Meta 宣布多年合作，範圍涵蓋「數百萬顆」Blackwell/Rubin GPU 加 Grace CPU。其中 Meta 以大規模部署 **Grace CPU-only（不搭 GPU）** 伺服器，NVIDIA 稱這是首例；Meta 也和 NVIDIA 合作，**明年（2027）起**部署 Vera-only。Meta 表示部分 CPU 工作負載的 perf/W 最高改善 2X。
  - The Register 2026-02-17 https://www.theregister.com/2026/02/17/meta_nvidia_cpu/
  - Tom's Hardware https://www.tomshardware.com/pc-components/cpus/meta-will-deploy-standalone-nvidia-grace-cpus-in-production-with-vera-to-follow-company-sees-perf-per-watt-improvements-of-up-to-2x-in-some-cpu-workloads
  - XPU.pub 2026-02-18 https://xpu.pub/2026/02/18/meta-nvidia/
- 細節修正：Grace-only 部署在搜尋摘要中的用途是「跑 AI 模型（推論）而非訓練」。文章說「Vera 為下一代」正確，但 Meta 的 Vera-only 部署時點是 **2027**，不是 2026。

### (b) 2026-03：Arm 發表首顆自家晶片「AGI CPU」，`已確認`
- 2026-03-24 發表，是 Arm 35 年來第一顆自家量產晶片。首發客戶 Meta。規格：Neoverse V3 ×136 核、TSMC 3nm (N3P)、300W TDP、最高 3.7GHz。確認客戶有 Cerebras、Cloudflare、F5、OpenAI、Positron、Rebellions、SAP、SK Telecom。當時說法是「早期系統已可取得，2H26 擴大供應」。
  - CNBC 2026-03-24 https://www.cnbc.com/2026/03/24/arm-launches-its-own-cpu-with-meta-as-first-customer.html
  - TechCrunch 2026-03-24 https://techcrunch.com/2026/03/24/arm-is-releasing-its-first-in-house-chip-in-its-35-year-history/
  - The Next Platform 2026-03-25 https://www.nextplatform.com/compute/2026/03/25/arm-comes-full-circle-with-homegrown-ai-tuned-server-cpu/5211524
- 同場 Rene Haas 說：傳統 AI 資料中心約需 **30M CPU 核/GW**，agent 時代會到 **120M 核/GW（4×）**。這是 Arm 自己的說法，不是獨立估計（見 TrendForce 轉述 https://insights.trendforce.com/p/agentic-ai-cpu-gpu）。

### (c) 2026-04：Meta 採用 AWS Graviton（數千萬核），`已確認`
- 2026-04-24：Meta 與 AWS 簽多年協議，部署**數千萬顆 Graviton5 核心**，用途明確寫「agentic AI 的 CPU 密集工作負載」。Graviton5：192 核 Neoverse V3、DDR5-8800，比 Graviton4 效能 +25%。
  - Meta Newsroom 2026-04 https://about.fb.com/news/2026/04/meta-partners-with-aws-on-graviton-chips-to-power-agentic-ai/
  - Amazon Press 2026-04 https://press.aboutamazon.com/aws/2026/4/meta-signs-agreement-with-aws-to-power-agentic-ai-on-amazons-graviton-chips
  - The Register 2026-04-24 https://www.theregister.com/on-prem/2026/04/24/meta-to-use-millions-of-aws-graviton-cores/5227355
- Wccftech 標題引述：agentic AI「幾乎和 GPU 一樣是 CPU 的故事」https://wccftech.com/meta-is-adding-tens-of-millions-of-aws-graviton-cpu-cores-to-its-compute-portfolio/

**小結**：三則新聞都屬實。唯一要修正的細節是 Meta 的 Vera-only 部署在 2027。[推論] Meta 同時押注 Grace/Vera、Arm AGI、Graviton5 三條 Arm 路線，說明 hyperscaler 的 agent CPU 需求確實存在，但**受惠的不一定是 x86（INTC/AMD）**。

---

## 2. arXiv:2511.00739 的實際結論

- 題目：v1/v2 是 "A CPU-Centric Perspective on Agentic AI"，v3 改名 "Towards Understanding, Analyzing, and Optimizing Agentic AI Execution: A CPU-Centric Perspective"。作者 Ritik Raj、Hong Wang、Tushar Krishna（Georgia Tech + Intel），2025-11 首次提交。
  - https://arxiv.org/abs/2511.00739 ・ v3 https://arxiv.org/html/2511.00739v3 ・ code https://github.com/ritikraj7/cpu-centric-agentic-ai
- 論文實際寫的是：「**tool-dominated** 的 agentic 工作負載明顯受 CPU 端工具處理拖累，最高佔端到端延遲 **88%**」（v3 摘要）。其他轉述版本出現「最高 90.6%」`已確認為轉述`。「**50–90%**」這個區間出自 Intel 部落格的轉述，不是論文摘要原句：https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Avoid-the-GPU-Idle-Tax-Choosing-the-Right-CPU-to-GPU-Ratios-for/post/1749346
- 工作負載：5 個應用，涵蓋 web search、RAG、code generation、數學解題、化學研究。例如在 200GB 語料上跑 ENNS（精確最近鄰）檢索的 RAG，檢索就佔 >75% 延遲。
- 論文提出的解法是**排程**，不是買更多 CPU：COMB（CPU-aware overlapped micro-batching），P50 延遲最多降 1.7×，開放負載下 service/total 延遲最多降 3.9×/1.8×；另有 MAS（mixed agentic scheduling）。
- 條件與限制 `[推論]`：
  1. 數字只適用於「工具主導」的 workload，推理主導或長上下文生成的 agent 佔比會低很多。
  2. ENNS 精確檢索本來就是 CPU 重負載；改用 ANN 或 GPU 檢索，佔比就會大降。
  3. 作者群含 Intel，部落格也用來推 CPU:GPU 0.8:1–1.4:1，有利益立場。
  4. 論文自己證明「靠排程重疊」就能吃掉大部分延遲。所以「CPU 佔延遲比例高」不等於「CPU 算力需求等比放大」。
- 旁證（同向）：arXiv:2608.15127（HKUST + 阿里 + 字節，2026-08）的 AgentSysBench 有 10 個應用，其中 5 個的延遲由非 LLM 元件（沙箱、檢索、環境）主導；單一 session 的沙箱 working set 峰值 28GB。https://arxiv.org/abs/2608.15127

**結論**：文章「CPU 佔 agent 延遲 50–90%」的說法**有出處，但被過度泛化**。原文是「tool-dominated workload、最高 88%」，而且作者自己提出排程解法。

---

## 3. Hot Chips 2026（8 月，約 08-23～08-25）公開規格

| 晶片 | 關鍵規格 | 上市時點 | 來源 |
|---|---|---|---|
| **NVIDIA Vera** | 88 核自研 Olympus（Armv9.2），176 執行緒（spatial multithreading）；L2 2MB/核，L3 共享 164MB；**SOCAMM2 LPDDR5X** ×8，最高 1.5TB、9600MT/s、**1.2TB/s**（約 14GB/s/核）；單晶粒 monolithic；Scalable Coherency Fabric Gen2 雙向 3.4TB/s；227B 電晶體 | 已在出貨（2026-08-27 起交付 AWS，見 §6） | Tom's HW https://www.tomshardware.com/pc-components/cpus/hot-chips-2026-nvidia-breaks-down-88-core-vera-cpu-spatial-multithreading-benchmarked-1-2-tb-s-socamm2-memory-agentic-workloads-detailed-and-more ・ STH https://www.servethehome.com/nvidia-vera-cpu-at-hot-chips-2026/ ・ The Register 2026-08-01 https://www.theregister.com/systems/2026/08/01/nvidias-vera-cpu-and-the-olympus-cores-that-power-it-deep-dive/5282056 |
| **Arm AGI CPU** | 2× 70 核 chiplet（TSMC N3P），可用最高 136 核 Neoverse V3（另有 64/128 核版本）；全核 3.2GHz / boost 3.7GHz；300W；**12ch DDR5-8800**，>800GB/s（約 6GB/s/核），延遲目標 <100ns；**96 lanes PCIe Gen6 + CXL 3.0**；die-to-die UCIe 2TB/s；CMN-S3 mesh | 首批客戶出貨 Q4 2026 | Tom's HW https://www.tomshardware.com/pc-components/cpus/hot-chips-2026-arm-details-agi-server-cpu-with-two-70-core-n3p-chiplets-touts-2-tb-s-ucie-fabric-link-and-12-channel-memory-controller ・ STH https://www.servethehome.com/arms-agi-data-center-cpu-at-hot-chips-2026/ |
| **Intel Xeon 7 Diamond Rapids** | 最高 **256 P-core**（16 顆 CPU tile × 16 核，Intel 18A-P），**不支援 HT**；4 顆 Intel 3-T base tile，每顆 320MB，合計 **1.28GB LLC**；**16ch DDR5-8000 或 MRDIMM 12800**；AVX10.2/AMX/APX；die 互連改用 UCIe-S（不再用 EMIB）；PCIe 6.0 | **2027**（Intel 於 Computex 2026 確認；多方指向 mid/2H27） | Tom's HW https://www.tomshardware.com/pc-components/cpus/intel-xeon-7-diamond-rapids-comes-with-up-to-256-p-cores-1-28-gb-of-last-level-cache-next-gen-18a-p-cpu-also-brings-avx-10-2-and-uses-ucie-s-instead-of-emib ・ FPS Review 2026-08-25 https://www.thefpsreview.com/2026/08/25/specifications-for-the-intel-diamond-rapids-xeon-processor-reveal-it-has-256-p-cores-using-a-16-chiplet-design-paired-with-1-28gb-of-last-level-cache/ |
| **Fujitsu Monaka** | 144 核 Armv9；2nm 核心晶粒（TSMC N2P）＋5nm SRAM 晶粒（整個 LLC 堆疊在下方）＋5nm IO die；2×256-bit SVE2；FP8/INT8 矩陣；12ch DDR5-8800；350W 氣冷 / 500W 液冷兩款，最高 3.8GHz | 評估樣品已出；有報導稱 2026-11 開賣，**量產在 2027** | Tom's HW https://www.tomshardware.com/pc-components/cpus/fujitsus-monaka-cpu-stacks-its-entire-cache-on-a-separate-5nm-die-and-narrows-to-256-bit-sve2 ・ Chips and Cheese https://chipsandcheese.com/p/hot-chips-2026-fujitsus-monaka-cpu ・ Aroged 2026-09-15 https://www.aroged.com/2026/09/15/fujitsu-monaka-144-core-arm-processor-will-be-available-in-november/ |

[推論] 文章歸納的設計趨勢（高 IPC、記憶體頻寬、SOCAMM/MRDIMM、緊密 fabric、PCIe6/CXL）**與四家公開規格一致**：Vera 走單晶粒加 LPDDR5X；Arm/Intel 走 chiplet 加 UCIe；Intel 用巨量 LLC 加 MRDIMM。

---

## 4. 需求端量化

### CPU:GPU 比例
- **TrendForce（2026-04）**：agentic AI 部署會從 **1:4～1:8 往 1:1～1:2** 移動 `已確認`。https://insights.trendforce.com/p/agentic-ai-cpu-gpu ・ 報告 RP260408AD https://www.trendforce.com/research/download/RP260408AD
- **Intel（2026-04-24 財報期間）**：AI 推論把 CPU 比例「從 1:8 推向 1:1」`已確認`。https://www.trendforce.com/news/2026/04/24/news-intel-says-ai-inference-pushes-cpu-ratio-from-18-toward-11-18a-yield-target-reportedly-advanced-by-6-months-to-mid-year/
- **Intel 部落格**：在特定用例中，最佳 CPU:GPU 為 **0.8:1～1.4:1** https://community.intel.com/t5/Blogs/Tech-Innovation/Artificial-Intelligence-AI/Avoid-the-GPU-Idle-Tax-Choosing-the-Right-CPU-to-GPU-Ratios-for/post/1749346
- **AMD Lisa Su**：CPU 會與 GPU 達到 1:1，甚至可能反轉（CPU 多於 GPU）https://finance.yahoo.com/sectors/technology/articles/amd-ceo-lisa-su-says-175056272.html （日期未逐字確認，約 2026-05）
- **Arm Haas**：30M→120M 核/GW（2026-03-24，見 §1b）。
- **BofA（2026-09-25）**：GPU:CPU 從預訓練時的約 8:1，在 agentic 工作負載下可能接近 1:1（見下方 TAM）。

### 伺服器 CPU TAM
| 誰 | 數字 | 時點 | 來源 |
|---|---|---|---|
| AMD（Lisa Su） | 2030 年 **>US$120B**，CAGR >35%（6 個月前的估計是 $60B） | 2026-05（Q1 財報） | Benzinga https://www.benzinga.com/markets/tech/26/05/52311020/amd-lisa-su-ai-server-cpu-boom-120bn-revenue-opportunity ・ Wccftech https://wccftech.com/amd-doubles-server-cpu-forecast-to-120-billion-as-agentic-ai-rewrites-demand-ceo-says-epyc-verano-built-purely-for-ai/ |
| NVIDIA（Jensen） | Vera 開啟「全新 **$200B TAM**」；本年度 CPU 營收約 **$20B** | 2026-05-20（Q1 FY27） | TechCrunch 2026-05-20 https://techcrunch.com/2026/05/20/jensen-huang-says-hes-found-a-brand-new-200b-market-for-nvidia/ |
| BofA | 伺服器 CPU 營收 **$61.4B（2026）→ $210.6B（2030）**，AI 相關佔比從 69% 升到 86% | 2026-09-25 | Benzinga https://www.benzinga.com/markets/tech/26/09/61998240/amd-price-target-720-bofa-agentic-ai-cpu-market |
| Arm | AGI CPU 官方目標 **$1B**，客戶需求 **>$2B**（FY27–28）；FY2031 目標 AGI CPU 營收 $15B 加 IP 營收 $10B | 2026-05 / 2026-07-29 | Tom's HW https://www.tomshardware.com/pc-components/cpus/arms-usd2-billion-in-agi-cpu-sales-are-still-not-enough-to-penetrate-5-percent-of-overall-market-share-analyst-reveals-at-least-usd90-million-worth-of-cpus-to-be-shipped-before-fy2027 ・ Digitimes 2026-07-30 https://www.digitimes.com/news/a20260730VL211/arm-cpu-revenue-agi-2028.html |

注意：各家 TAM 定義不同。NVIDIA 的 $200B 可能包含 CPU 系統或更廣範圍 `[推論]`，不能直接和 AMD 的 $120B 相加或比較。

### 2026 缺貨與漲價，`已確認`（有實證，不只是敘事）
- **TrendForce（2026-04-27）**：1Q26 伺服器 CPU ASP **+27%**；Intel 把原本報廢的晶片也拿來出售。https://www.trendforce.com/news/2026/04/27/news-intel-reportedly-sells-chips-typically-scrapped-as-cpu-demand-surges-1q26-server-cpu-asps-up-27/
- Intel 與 AMD 在 1Q26 末都對部分 CPU 漲價（TrendForce 同上系列）。
- **Intel 2026-07-03 確認漲價**：旗艦 Xeon 6980P 從 $12,460 漲到 $13,955（+$1,495，約 +12%）。TrendForce 2026-07-07 https://www.trendforce.com/news/2026/07/07/news-intel-reportedly-raises-cpu-prices-flagship-xeon-up-us1495-select-desktop-chips-us30-50/ ・ Tom's HW https://www.tomshardware.com/pc-components/cpus/intel-confirms-price-hikes-on-select-consumer-and-server-cpus-citing-supply-costs-and-demand-select-xeon-processors-now-over-usd1-000-more-expensive
- **Intel Q2'26（2026-07-23）**：DCAI 營收 $6.3B，YoY +59%、QoQ +24%；伺服器 **ASP +48%**；公司明說需求超過供給。https://www.intc.com/news-events/press-releases/detail/1776/intel-reports-second-quarter-2026-financial-results ・ Futurum https://futurumgroup.com/insights/intel-q2-fy-2026-hyperscaler-server-demand-drives-59-dcai-growth/
- **AMD Q2'26（2026-08-04）**：資料中心營收 $6.7B（YoY +107%）；EPYC 營收 YoY >70%，連續第 5 季創紀錄。https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results
- 通路交期（Fusion Worldwide，**通路商說法，可信度中**）：Intel 經銷商只拿到約 40% 配額；EPYC 到年底實質售罄；交期 8–22 週，實際可達 30 週以上。https://www.fusionww.com/insights/server-cpu-shortage-2026
- SemiAnalysis（2026-02）：前沿實驗室的 **RL 訓練沙箱**把 CPU 用光，直接和雲端業者搶 x86 伺服器。https://newsletter.semianalysis.com/p/cpus-are-back-the-datacenter-cpu-landscape
- [推論] 缺貨同時有**供給端**因素：Intel 自家產能、TSMC N3/N2 排擠、記憶體漲價推高 BOM。漲價不能全部歸因於 agent 需求。

---

## 5. 市場已定價多少

### 股價（Yahoo 日收盤；基準 2025-12-31；最新 2026-09-28）
| 標的 | 2026 YTD | 近 3 個月（自 06-29） | 近 1 個月 | 2026 高點（日期） | 距高點 |
|---|---|---|---|---|---|
| INTC | **+214%**（36.90→116.03） | −12% | +30% | 140.94（06-22） | −18% |
| AMD | **+184%**（214.16→607.87） | +13% | +31% | 630.63（09-25） | −4% |
| ARM | **+159%**（109.31→283.33） | −18% | +19% | 439.46（06-18） | −36% |
| NVDA | +23% | +17% | +5% | 235.74（05-14） | −3% |
| RMBS | +11% | −18% | +19% | 170.66（06-03） | −40% |
| MU | +269% | −8% | +13% | 1213.56（06-25） | −13% |
| SOXX | +86% | −9% | +10% | 655.01（06-22） | −14% |
| QQQ | +20% | +2% | +3% | 747.46（09-22） | −2% |

資料來源：query1.finance.yahoo.com v8 chart API，2026-09-29 抓取。

### 解讀
- `[推論]` **「agentic CPU」題材在 2026 上半年已被大幅定價**。INTC、AMD、ARM YTD 是 SOXX 的 2 倍左右、QQQ 的 8–10 倍。6 月下旬見頂後修正 18–36%，9 月又反彈 19–31%。現在是**第二波行情**，不是初期。
- 在「CPU 題材股」裡，AMD 是唯一接近新高的。INTC 和 ARM 都還在高點下方很多。ARM 的弱勢主要來自手機權利金下修（2026-07-29 財報把全年權利金成長從約 20% 下修到 high-teens，原因是記憶體漲價壓手機），不是 AGI CPU 本身。https://www.tikr.com/blog/arm-stock-fell-8-after-reporting-record-q1-earnings-revenue-of-1-29-billion-heres-the-bigger-picture
- RMBS（MRDIMM/SOCAMM2 介面晶片）YTD 只有 +11%，距高點 −40%。原因是 Q1 財報 miss 加 Baird 降評（2026-04-28）。這是記憶體介面環節**相對沒被定價**的一段 `[推論]`。https://www.fool.com/investing/2026/04/28/why-rambus-plunged-today/

### 賣方報告與目標價
| 日期 | 券商 | 標的 | 動作 | 論點 | 來源 |
|---|---|---|---|---|---|
| 2026-09-25 | BofA | AMD | 目標 $620→**$720** | agent 推動伺服器 CPU 到 2030 年 $211B | https://www.benzinga.com/markets/tech/26/09/61998240/amd-price-target-720-bofa-agentic-ai-cpu-market |
| 2026-09 | BofA | INTC | Buy，目標 **$145**（重申） | 同上 | 同上頁轉述 |
| 2026-09-03 | Mizuho | INTC | 目標 $109→**$92**，Neutral | 看好 agent 需求，但「agentic AI 相關公司整體**本益比壓縮**」 | https://ca.investing.com/news/stock-market-news/mizuho-cuts-intel-stock-price-target-to-92-on-multiple-compression-93CH-4828198 |
| 2026 | Piper Sandler | AMD | 首評 OW，目標 $600 | — | https://www.thestreet.com/investing/stocks/top-analyst-raises-amd-stock-price-target-for-rest-of-2026 |
| 2026 | Raymond James | AMD | 升評 Strong Buy，目標 $641 | — | 同上 |
| 2026-09 | 共識 | ARM | 43 位分析師，平均目標約 **$288.7**（≈ 現價 $283） | — | https://www.ad-hoc-news.de/boerse/news/corporate-news/arm-holdings-stock-gains-as-analysts-adjust-price-targets-and-earnings/70136861 |
| 2026-04-07 | KeyBanc | NVDA | OW，目標 $275 | 同時報導 Rubin 下修（見 §6） | https://finance.biggo.com/news/-YFfZZ0ByH9TLH69jS0g |

`[推論]` INTC 現價 $116 落在 Mizuho $92 與 BofA $145 之間；ARM 現價約等於共識目標，**上檔空間已被共識吃掉**；AMD 現價約為 BofA 目標的 84%。

---

## 6. 催化時程（重點查核項）

- **Vera 出貨，`已確認`，沒受 Rubin 砍量拖累**：2026-06-01 GTC Taipei 宣布「Vera, the CPU for Agents」全面量產，下半年由夥伴供應（Dell/HPE/Lenovo/SMCI 等出 standalone 機種；CoreWeave 是首家提供 standalone Vera 的雲）。2026-08-27 NVIDIA 宣布 Vera 已在出貨，Ian Buck 親送 AWS 首台 Vera CPU server；之前已交付 OCI、Anthropic、OpenAI、SpaceXAI。2026-08-26 AWS 與 NVIDIA 宣布再部署 200 萬顆 GPU，AWS 會用 Vera（部分 standalone）。
  - https://nvidianews.nvidia.com/news/nvidia-unveils-vera-the-cpu-for-agents （GlobeNewswire 2026-06-01 https://www.globenewswire.com/news-release/2026/06/01/3303981/0/en/NVIDIA-Unveils-Vera-the-CPU-for-Agents.html）
  - https://blogs.nvidia.com/blog/vera-cpu-delivery/ ・ https://press.aboutamazon.com/aws/2026/8/aws-and-nvidia-to-deliver-2-million-additional-gpus-and-next-generation-infrastructure-for-agentic-and-physical-ai
- **Rubin/HBM4 放緩，`已確認`**：KeyBanc（2026-04-07）指 NVIDIA 把 2026 Rubin GPU 目標從 200 萬顆下修到 150 萬顆，VR 機櫃從 12–14k 下修到約 6k，原因是 SK hynix/Micron 的 HBM4 驗證延遲。TrendForce（2026-08-04）指 Rubin Ultra 可能降低 HBM 配置。https://www.trendforce.com/presscenter/news/20260804-13166.html ・ https://www.sdxcentral.com/news/nvidias-rubin-gpus-hit-the-brakes-as-hbm4-memory-drought-threatens-jensens-supply-chain-magic-report/
  - `[推論]` standalone Vera 用 LPDDR5X/SOCAMM2、不用 HBM4，所以**不受 HBM4 瓶頸直接影響**。反而 GPU 缺貨時，CPU-only 的 agent 部署相對更好推進。VR NVL72 裡的 Vera 則跟著 Rubin 的節奏走。
- **AMD Venice（EPYC 9006，Zen 6，TSMC 2nm），`已確認`**：2026-07-23 在 Advancing AI 發表，最高 256 核 / 512 執行緒、16ch DDR5、PCIe Gen6；2026-08-05 確認 2nm 全面量產。Q3 開始出貨，旗艦 **Q4 2026 全面供貨**，其餘 SKU 陸續在 2027 推出。SOCAMM2 支援要到 **Verano（2027）**。
  - https://www.techtimes.com/articles/321257/20260722/amd-advancing-ai-2026-opens-zen-6-venice-helios-open-ai-rack-bet.htm ・ https://www.tweaktown.com/news/112793/amd-announces-6th-gen-amd-epyc-venice-cpus-up-to-256-cores-and-512-threads-and-built-for-ai/index.html ・ https://videocardz.com/newz/amd-confirms-epyc-socamm2-support-starts-with-verano-in-2027
  - Venice 的 MRDIMM 速度上限：`未證實`。
- **Intel Diamond Rapids，`已確認`延到 2027**：Computex 2026 官方確認 2027 上市，多方判斷在 mid 到 2H27；Coral Rapids（恢復 HT）在 2028。空窗期由 Granite Rapids 與 Clearwater Forest（Xeon 6+）撐。https://www.tomshardware.com/pc-components/cpus/intel-xeon-7-diamond-rapids-cpus-officially-launching-in-2027-on-intel-18a-p-next-gen-p-core-xeon-features-pcie-6-0-50-percent-higher-core-counts-and-twice-the-memory-bandwidth ・ https://www.servethehome.com/intel-xeon-7-diamond-rapids-now-slated-for-2027/
- **Graviton5**：M9g/M9gd 已於 **2026-06-10 GA**；C9g/R9g 預計 2026 年內推出 `已確認（計畫）`。https://aws.amazon.com/about-aws/whats-new/2026/06/ec2-m9g-m9gd-instances-graviton5-processors-available/ ・ InfoQ 2026-06 https://www.infoq.com/news/2026/06/aws-graviton5-ga/
  - **re:Invent 2026：11-30～12-04，拉斯維加斯** `已確認`。https://newscenter.io/2026/08/aws-reinvent-2026-nov-30-dec-4-las-vegas/
  - re:Invent 是否發表 Graviton6：`[推測]`（歷來常在 re:Invent 發表新一代 Graviton，但沒有來源）。
- **Arm AGI CPU 量產**：2H26 開始生產，**首批客戶出貨在 Q4 2026**，該季預估出貨 $90–100M；官方目標 $1B，需求 $2B，瓶頸在供給；Digitimes 稱 FY2028 Q3 形成穩定營收流。https://www.digitimes.com/news/a20260730VL211/arm-cpu-revenue-agi-2028.html ・ Tom's HW（見 §4）
- **MRDIMM Gen2（12800MT/s）**：JEDEC 標準接近完成或已發布；Samsung 在 Computex 2026 展出 12800 MRDIMM。第一個明確支援的平台是 **Diamond Rapids（2027）** `已確認`，所以大量導入在 **2027** `[推論]`。https://videocardz.com/newz/jedec-publishes-new-ddr5-mrdimm-logic-standard-as-gen2-targets-12800-mt-s ・ https://www.servethehome.com/next-gen-server-memory-on-display-ddr5-8000-rdimms-and-mrdimm-gen2-hits-ddr5-12800/
- **SOCAMM2**：Vera 已經在用（2026 H2 出貨）；Rambus 2026-04-22 發表 SOCAMM2 chipset（SPD hub + PMIC）；AMD 要到 Verano（2027）才支援。https://www.businesswire.com/news/home/20260422571726/en/Rambus-Enables-Power-Efficient-AI-Platforms-with-SOCAMM2-Server-Module-Chipset

### 財報日
| 公司 | 下一次財報 | 確定度 | 來源 |
|---|---|---|---|
| MU（FQ4'26） | **2026-09-30** 盤後（指引營收 $50.0B±1B） | 已確認（公司公告） | https://www.stocktitan.net/news/MU/micron-technology-to-report-fiscal-fourth-quarter-results-on-db9s7g1vizzp.html |
| INTC（Q3'26） | 約 **2026-10-22**（估計區間 10-22～10-30） | 未經公司確認 | https://www.wallstreethorizon.com/intel-earnings-calendar |
| RMBS（Q3'26） | 約 **2026-11-02**（Investing.com 估計；歷年多在 10 月最後一週） | 未經公司確認 | https://www.investing.com/equities/rambus-inc-earnings |
| AMD（Q3'26） | **2026-11-03** 盤後 | 多個來源一致，但沒看到 AMD IR 正式公告 | https://www.tipranks.com/stocks/amd/earnings |
| ARM（Q2 FY27） | 約 **2026-11-04** | 未經公司確認 | https://www.investing.com/equities/arm-earnings |
| NVDA（Q3 FY27） | **2026-11-17** | 搜尋摘要稱 8-26 財報會上已確認；另有來源寫 11-25 | https://www.wallstreethorizon.com/nvidia-earnings-calendar |

---

## 7. 反方證據（CPU 瓶頸被高估？）

1. **延遲是「等待與串行」，不是算力不足**：Pebblous（2026-08）指出，工具主導的 agent 最高 88% 時間落在 CPU 端，但這些階段的 **CPU 使用率只有約 10%**。時間耗在序列化的資料路徑（檢索、解析、讀檔）上，加核心不會縮短等待。https://blog.pebblous.ai/report/agent-cpu-bottleneck-data-pipeline-2026-08/en/
2. **軟體排程就能吃掉大部分延遲**：原論文自己的 COMB/MAS 可讓延遲降 1.7–3.9×（§2）。[推論] 把 CPU 階段與 GPU 批次重疊，就能讓「CPU 佔延遲比」在不加硬體的情況下下降。
3. **ENNS→ANN、檢索上 GPU**：論文中最重的 CPU 工作（精確檢索 >75%）可以換成近似檢索或 GPU 檢索 `[推論]`，所以佔比對實作方式很敏感。
4. **便宜的 CPU 也夠用 / Arm 替代 x86**：Meta 同時買 Grace、Graviton5、Arm AGI，AWS 也大建 Graviton/Cobalt（SemiAnalysis）。[推論] agent 的 CPU 需求量是真的，但增量有很大一塊流向**自研 Arm 或 hyperscaler 內部晶片**，INTC/AMD 的份額邏輯不能直接套用需求總量。
5. **價格上漲有部分是供給與成本推動**：Intel 漲價理由含「供應鏈成本上升」；記憶體漲價推高整機 BOM（§4）。[推論] 2027 產能開出後，ASP 有均值回歸風險。
6. **比例預測多出自有利益的一方**：1:1 的說法來自 Intel（2511.00739 共同作者）、AMD、Arm、NVIDIA（賣 Vera）。TrendForce 是相對中立的第三方，給的是 1:1～1:2。
7. **估值面**：Mizuho（2026-09-03）以「agentic AI 相關公司本益比壓縮」為由下修 INTC 目標；INTC 9 月最後兩天跌近 10%（Invezz 2026-09-29 https://invezz.com/news/2026/09/29/intel-stock-has-erased-nearly-10-in-two-days-is-the-great-comeback-trade-breaking/）。
- **查無**：沒有找到有份量的研究正面主張「GPU 端直接執行工具呼叫可取代 CPU」，這一點`未證實`。

---

## 結論摘要
- **論點成立度：中高**。三則新聞屬實；規格趨勢與 Hot Chips 一致；需求有財報級證據（Intel 伺服器 ASP +48%、DCAI +59%；AMD EPYC >70%；Intel 7 月漲價；TrendForce 1Q ASP +27%）。但「CPU 佔延遲 50–90%」只適用於 tool-dominated workload，而且可以靠排程緩解。「CPU 佔延遲高」不等於「CPU 算力需求等比成長」。
- **市場定價：高**。INTC/AMD/ARM YTD +159～214%，是 SOXX 的 2 倍左右；賣方已在寫 2030 年 $120–211B TAM。邊際上較少被定價的是記憶體介面（RMBS −40% from high），還有 x86 以外的 Arm 份額變化。

---

## 催化時程表（2026-10 ～ 2027-06）

| 日期 | 事件 | 影響標的 | 確定度 |
|---|---|---|---|
| 2026-09-30 | Micron FQ4'26 財報（DRAM/HBM/SOCAMM 報價與 2027 供給） | MU、RMBS、NVDA、記憶體鏈 | 已確認 |
| 2026-10 ～ 2026-12 | Vera standalone 伺服器經 OEM 與雲（CoreWeave 等）擴大供貨；AWS 導入 | NVDA、SOCAMM2 鏈（MU、RMBS） | 已確認（已開始出貨，量未知） |
| 2026-10-22（估） | Intel Q3'26 財報（指引營收 $15.8–16.8B；關注 DCAI、ASP、供給缺口、18A） | INTC、AMD | 日期未確認 |
| 2026-11-02（估） | Rambus Q3'26 財報（指引營收 $210–216M；MRDIMM/SOCAMM2 companion chip） | RMBS | 日期未確認 |
| 2026-11-03 | AMD Q3'26 財報（指引約 $13B；Venice 放量、EPYC 供給） | AMD、INTC | 多源一致，公司尚未正式公告 |
| 2026-11-04（估） | Arm Q2 FY27 財報（AGI CPU 首季出貨 $90–100M、權利金） | ARM | 日期未確認 |
| 2026-11 | Fujitsu Monaka 開賣（量產在 2027） | Fujitsu、TSMC N2 | 媒體報導，中 |
| 2026-11-17 | NVIDIA Q3 FY27 財報（CPU 營收、當年約 $20B 目標進度、Rubin 量） | NVDA、MU | 大致確認（有 11-25 異說） |
| 2026-11-30 ～ 12-04 | AWS re:Invent（C9g/R9g；是否發表 Graviton6 屬 [推測]；Meta 與 agent 案例） | AMZN、ARM、INTC/AMD 份額 | 日期已確認 |
| 2026-12-01 | NVIDIA GTC DC keynote（2026-11-30 ～ 12-03） | NVDA | 已確認 |
| 2026-Q4 | AMD Venice 旗艦全面供貨；Arm AGI CPU 首批客戶出貨 | AMD、ARM | 已確認（公司指引） |
| 2026-12 中下旬（估） | Micron FQ1'27 財報 | MU | [推論]（依歷年節奏） |
| 2027-01 中（估） | CES 2027 | NVDA、AMD、INTC | [推測] |
| 2027-01 下旬 ～ 02 上旬（估） | INTC Q4、AMD Q4、ARM Q3 FY27 財報 | INTC、AMD、ARM | [推論] |
| 2027-02 下旬（估） | NVDA Q4 FY27 財報 | NVDA | [推論] |
| 2027-03（估） | NVIDIA GTC San Jose（Vera 下一步、Rubin Ultra） | NVDA | [推測] |
| 2027（未定） | Meta 開始 Vera-only 部署 | NVDA | 已確認為「2027」，月份未知 |
| 2027 H1 ～ H2 | AMD Verano（SOCAMM2）；Venice 其餘 SKU | AMD、MU、RMBS | 已確認為 2027 |
| 2027 mid ～ 2H | Intel Diamond Rapids 上市，MRDIMM Gen2（12800）正式放量 | INTC、RMBS、MU | 年份已確認；月份為 [推論] |
| 2027-04 下旬 ～ 05（估） | INTC/AMD/ARM/NVDA 下一季財報 | 全部 | [推論] |
| 2027-06 上旬（估） | Computex 2027 | 全部 | [推測] |

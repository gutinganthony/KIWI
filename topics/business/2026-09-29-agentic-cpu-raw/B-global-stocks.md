# Research B：「Agent CPU」主題全球標的曝險 × 估值（2026-09-29）

## 資料來源與時點（全表通用）
- **股價 / YTD / 3M / 52 週高點**：Yahoo Finance chart API `query1.finance.yahoo.com/v8/finance/chart/{ticker}`（抓取時間 2026-09-29）。
  美股 = 2026-09-28 收盤；日股、A 股 = 2026-09-29 收盤；BESI = 2026-09-29 11:09 CET 盤中。
  YTD 基準 = 2025-12-31 收盤；3M 基準 = 約 2026-06-29 收盤；52w 高點 = Yahoo `fiftyTwoWeekHigh`（盤中高點）。已按拆股調整過（Ibiden 在 2026-09 有 2:1 拆股，序列已調整）。
- **市值 / forward P/E / EV/Sales**：Yahoo fundamentals-timeseries（`trailingMarketCap`、`trailingForwardPeRatio`、`trailingEnterprisesValueRevenueRatio`），as-of 2026-09-18~23，**我再按最新價等比例換算到現價**。匯率（Yahoo，2026-09-29）：USDJPY 157.44、USDCNY 6.6955、EURUSD 1.134。
- Yahoo 沒給 forward P/E 的（RMBS、瀾起、Ibiden）是用公司指引／上半年實績自行推算，標 `[推論]`。
- 財報日：只有 MU 已經公司確認。其他是根據上一季的公告節奏推估，標 `[推估]`。

## 一、大表

| # | 標的 | 市值 USD | 股價（日期） | fwd P/E（或 EV/S） | YTD | 3M | 距 52w 高 | 主題曝險（產品線／占營收／階數） | 下次財報 | 最大風險 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **AMD** | ~$992B | $607.87（9/28） | 39.1x | +183.8% | +12.7% | -4.9% | EPYC 伺服器 CPU（Venice N2＋SoIC/3D V-Cache）。DC 部門占 58%（Q2 $6.7B/$11.5B），EPYC 約占總營收 30%±5 `[推論]`。**1 階** | 11/03（第三方推估） | 已在歷史高點附近、YTD +184%，Venice 放量或 MI 系列不及預期就會殺估值 |
| 2 | **INTC** | ~$613B | $116.03（9/28） | 59.9x | +214.4% | -11.9% | -18.5% | Xeon 6/6+（DCAI $6.3B，占 Q2 營收 $16.1B 的 39%）＋Foveros/EMIB 封裝代工。**1 階** | ~10/22 `[推估]` | 18A 良率拖累 Diamond Rapids 延到 2027；Q2 成長主要靠 ASP +48%，不是量 |
| 3 | **ARM** | ~$303B | $283.33（9/28） | 129.1x | +159.2% | -17.5% | -37.4% | DC 權利金年增超過一倍＋自研 AGI CPU（需求超過 $2B）。主題占營收約 20–25% `[推論]`。**1 階** | 11 月初 `[推估]` | 129x fwd P/E，而且自研晶片跟客戶（NVDA/hyperscaler）形成競合 |
| 4 | **NVDA**（只看 CPU） | ~$5.53T | $228.86（9/28） | （25.2x，不做評估） | +22.7% | +17.4% | -3.2% | Grace/Vera 獨立 CPU：2026 年約 $20B 的可見度 ÷ FY27 營收約 $400B，**約 5%** `[推論]`。**1 階，但純度低** | 11 月下旬 `[推估]` | CPU 只是邊角業務，股價主要跟 GPU capex 連動 |
| 5 | **RMBS** | ~$11.1B | $102.12（9/28） | ~31x `[推論：Q3 EPS 指引 $0.75–0.82 年化≈$3.3]` | +11.1% | -17.6% | -41.3% | DDR5 RCD／MRDIMM MRCD+MDB／PMIC；產品營收 $99M，占 Q2 營收 $207M 的 48%。記憶體介面晶片約占 45% `[推論]`。**1 階（記憶體頻寬）** | 10 月下旬 `[推估]` | 公司自己說 MRDIMM 要到 2027 年才「有意義」放量，取決於 Intel/AMD 平台時程；權利金在下滑 |
| 6 | **瀾起 688008.SS** | ~$38–39B（A 股總市值 2,546 億人民幣，9/28，Sohu） | ¥212.60 CNY（9/29） | ~58x `[推論：H1 淨利 19.97 億人民幣×2.2]`；TTM 85.6x | +80.5% | -31.4% | -36.1% | 互連晶片（RCD/MRCD/MDB/CKD/PCIe Retimer/CXL MXC）H1 營收 31.1 億，占 33.35 億人民幣的 **93%**。**1 階，純度最高** | Q3 報 ≤10/31（A 股法定期限）`[推估]` | 地緣政治：出口管制／韓國反壟斷調查；A+H 雙掛牌，籌碼面波動大 |
| 7 | **Renesas 6723.T** | ~$40.1B | ¥3,458（9/29） | 13.2x | +61.6% | -28.1% | -34.6% | DC 記憶體介面（RCD、Gen3 MRDIMM MRCD/MDB）＋數位電源。約占營收 5–10% `[推論]`。**1 階，但純度低** | 10 月下旬 `[推估]` | 主體還是車用／工業 MCU，主題曝險會被稀釋；Gen3 MRDIMM 要到 2H27 才量產 |
| 8 | **MU** | ~$1.19T | $1,053.98（9/28） | 6.7x | +269.3% | -8.0% | -16.0% | SOCAMM（LPDDR5X，Vera 主供應）占營收約 2–4% `[推論]`；伺服器 DRAM／MRDIMM 顆粒是更大的 2 階曝險。**SOCAMM 1 階、DRAM 2 階** | **9/30 盤後（明天，公司已確認）** | 處於景氣週期高峰（淨利率 68%），P/E 低是週期假象；CXMT 擴產威脅價格 |
| 9 | **ALAB** | ~$60.9B | $351.31（9/28） | 54.1x（EV/S 51x） | +111.2% | -23.0% | -29.7% | Aries PCIe6 retimer／Leo CXL／Scorpio switch。CPU 伺服器相關約占 20–30% `[推論]`，其餘偏 GPU scale-up。**1 階（I/O）** | 11 月初 `[推估]` | EV/S 51x；Q3 指引季增 40% 靠 Scorpio X，只要一季不及預期就重殺 |
| 10 | **CRDO** | ~$36.2B | $192.67（9/28） | 30.7x | +33.9% | -21.6% | -37.6% | AEC／光學 DSP／PCIe retimer；CPU 伺服器相關約 10–20% `[推論]`。**2 階** | 12 月初 `[推估]` | 客戶集中（前幾大 hyperscaler）；AEC 成長從三位數降到約 50% |
| 11 | **AMKR** | ~$13.2B | $53.18（9/28） | 18.8x（EV/S 1.8x） | +34.7% | -35.4% | -45.0% | 先進封裝（含 Intel EMIB 合作）；運算類占營收約 20–25%，CPU 相關約 10% `[推論]`。**2 階** | 10 月下旬 `[推估]` | Q3 指引 $1.95–2.05B 低於共識；通訊 SiP 移往越南，拖累到 2027 年初 |
| 12 | **BESI.AS** | ~$17.0B | €189.65（9/29 盤中） | 29.2x | +41.8% | -33.9% | -42.3% | 混合鍵合（Intel Foveros Direct、邏輯＋HBM）；混合鍵合約占營收／訂單 25–35% `[推論]`；Q2 訂單 +129%。**1 階（封裝差異化）** | 10 月下旬 `[推估]`（Q2 是 7/23） | HBM4 可能沿用 TCB，混合鍵合採用時點延後；併購（AMAT/Lam）卡在監管 |
| 13 | **Ibiden 4062.T** | ~$39.4B | ¥11,020（9/29，拆股後） | ~70x `[推論：FY3/27 OP ¥127B]`；TTM 91x | +227.4% | -7.5% | -19.8% | 伺服器 CPU／GPU ABF 載板：電子部門 ¥375B，占 ¥550B 的 68%；通用伺服器 CPU 約占 25–30% `[推論]`。**1 階** | 10 月底～11 月初 `[推估]` | YTD +227% 後估值已經先反映；載板擴產（Cell 8 之後）供給轉鬆就會壓 ASP |
| 14 | **Advantest 6857.T** | ~$155.5B | ¥33,910（9/29） | 37.9x | +72.7% | +4.9% | -12.4% | SoC 測試機（CY26 TAM 上修到 $10.5–11.5B，點名 CPU／推論 ASIC）；CPU 相關約占營收 10–15% `[推論]`。**2 階** | 10 月下旬 `[推估]`（Q1 是 7/29） | 測試機週期高峰，產能 +70% 可能在 2027 年變成過剩 |
| 15 | **NET** | ~$126.0B | $353.99（9/28） | 179x（EV/S 49.7x） | +79.6% | +45.2% | -3.7% | Workers／Isolates 沙箱、agent 開發者平台（740 萬開發者）；約占營收 10–15% `[推論]`。**1 階（軟體沙箱）** | 11 月初 `[推估]` | EV/S 50x 而且在歷史高點；營收成長 36% 撐不起 179x fwd P/E |
| +1 | **TSM**（補充） | ~$2.01T | $452.88（9/28） | 21.5x | +49.0% | -0.5% | -5.5% | 所有主流伺服器 CPU（AMD/ARM/NVDA Vera/Graviton）的 N3/N2 代工＋SoIC／CoWoS；先進封裝 2026 年超過營收 10%。**1 階（製造＋封裝）** | 10 月中 `[推估]` | 台海地緣；2026 capex $64B 壓毛利 |
| +2 | **MRVL**（補充） | ~$226B | $251.90（9/28） | 60.0x | +196.4% | -9.3% | -23.6% | 客製矽／Structera CXL 記憶體擴充／PCIe retimer；DC 占 79%，CPU／CXL 相關約 10% `[推論]`。**2 階** | 12 月初 `[推估]` | 成長主力是客製 XPU（Google 權證條款稀釋最多 7%），CPU 相關純度低 |
| +3 | **Ajinomoto 2802.T**（補充） | ~$30.1B | ¥4,978（9/29） | 32.9x | +50.1% | -15.2% | -21.5% | ABF 增層膜市占約 95%，所有 CPU 載板都要用；約占營收 5%、占獲利 20–30% `[推論]`。**2 階（封裝材料獨占）** | 11 月初 `[推估]` | 主體是食品，純度低；對中國減供 30% 引發的政治風險 |
| +4 | **Disco 6146.T**（補充） | ~$39.1B | ¥56,680（9/29） | 33.4x | +17.7% | -30.2% | -38.2% | 研磨／切割（市占 70% 以上）；混合鍵合＋HBM 薄化必備。約占 15–25% `[推論]`。**2 階（封裝設備）** | 10 月中下旬 `[推估]` | 設備週期與 HBM capex 高度連動 |

補充 4 檔的理由：文章結論把「封裝」列為主要差異化來源。TSM（SoIC／3D V-Cache 本身就是 3D 堆疊快取）、Ajinomoto（ABF 獨占）、Disco（混合鍵合前段一定要做的薄化）是封裝鏈裡**原清單漏掉的關鍵瓶頸**。MRVL 補上 CXL 記憶體擴充和 retimer 這條 I/O 線。

## 二、排序表：相關度（1–5）× 估值吸引力（1–5）

| 排名 | 標的 | 相關度 | 估值吸引力 | 乘積 | 一句話 |
|---|---|---|---|---|---|
| 1 | **RMBS** | 5 | 4 | **20** | 純記憶體介面（RCD/MRCD/MDB），推估 fwd P/E 約 31x，距高點 -41%，YTD 只漲 +11%，是全表最落後的 |
| 2 | **TSM** | 4 | 4 | **16** | 所有 agent CPU 都在它這裡生產＋SoIC 封裝，21.5x，是最便宜的 1 階 |
| 3 | **瀾起 688008** | 5 | 3 | **15** | 93% 營收是互連晶片，純度最高；3M -31%，但約 58x 仍然不便宜 |
| 4 | **Renesas 6723** | 3 | 5 | **15** | 13x fwd P/E、距高點 -35%，MRDIMM 是便宜的選擇權，但純度低 |
| 5 | **BESI** | 4 | 3 | **12** | 混合鍵合＝文章說的「封裝差異化」核心；29x、距高點 -42% |
| 6 | AMKR | 3 | 4 | 12 | 18.8x／EV/S 1.8x、距高點 -45%，但短期指引偏弱 |
| 7 | MU | 3 | 4 | 12 | 6.7x 是週期高峰的 P/E；9/30 財報是事件風險 |
| 8 | AMD | 5 | 2 | 10 | 主題的 1 階核心，但接近高點、YTD +184% |
| 9 | Ibiden | 5 | 2 | 10 | CPU 載板直接受益，但 YTD +227%，推估約 70x |
| 10 | CRDO | 3 | 3 | 9 | 30.7x、距高點 -38%，CPU 純度偏低 |
| 11 | Ajinomoto | 3 | 3 | 9 | ABF 獨占，但被食品業務稀釋 |
| 12 | Disco | 3 | 3 | 9 | 33x、距高點 -38%，混合鍵合薄化 |
| 13 | INTC | 4 | 2 | 8 | 60x、YTD +214%，靠 ASP 撐起來的成長 |
| 14 | ALAB | 4 | 2 | 8 | I/O 純度高，但 EV/S 51x |
| 15 | NVDA | 2 | 3 | 6 | CPU 只占約 5%，不適合當主題載體 |
| 16 | Advantest | 3 | 2 | 6 | 2 階、38x、接近高點 |
| 17 | MRVL | 3 | 2 | 6 | 60x，CPU 純度低 |
| 18 | ARM | 4 | 1 | 4 | 129x |
| 19 | NET | 4 | 1 | 4 | 沙箱論點最純的軟體標的，但 EV/S 50x、在高點 |

**排序邏輯**：相關度看的是「營收裡直接吃到 CPU 瓶頸四方向（單核／記憶體頻寬／封裝／I/O）＋沙箱的比例」，1 階而且純度高才給 4–5 分。估值吸引力綜合 fwd P/E、距 52 週高點的回撤、YTD 漲幅，專門懲罰已經在高點、漲超過 150% 的標的。結果是記憶體頻寬這條線（RMBS／瀾起／Renesas）和封裝瓶頸（TSM／BESI）勝出：它們同時有高純度，又因為 7 月以來的半導體回檔（SOX 從 6 月高點修正、9 月中又有「AI 放緩」言論）跌了 30–40%。AMD、Ibiden、ARM、NET 雖然最貼題，但漲幅已經先反映了。

## 三、每檔 2 行註記

- **AMD**：Q2 EPYC 年增 70%，Venice（N2＋SoIC）搶 Intel 市占。EPYC 在 2026 年供不應求（交期 30 週以上）。估值 39x 不算貴，但位置在高點。
  來源：[AMD Q2 2026 新聞稿](https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results)、[DCD](https://www.datacenterdynamics.com/en/news/amd-posts-q2-26-revenue-of-115bn-with-data-center-revenue-up-107-for-the-quarter/)、[Fusion Worldwide CPU 短缺](https://www.fusionww.com/insights/server-cpu-shortage-2026)
- **INTC**：DCAI $6.3B（年增 59%，營益率 39.5%），但伺服器量只 +9%，成長主要來自 ASP +48%。Diamond Rapids 傳延到 2027 年。
  來源：[Intel Q2 2026 新聞稿](https://www.intc.com/news-events/press-releases/detail/1776/intel-reports-second-quarter-2026-financial-results)、[Futurum](https://futurumgroup.com/insights/intel-q2-fy-2026-hyperscaler-server-demand-drives-59-dcai-growth/)
- **ARM**：Q1 FY27 營收 $1.29B，DC 權利金年增超過一倍，AGI CPU 需求超過 $2B，FY31 目標 $15B。毛利率偏低（30% 後段～40% 前段），會稀釋整體毛利率。
  來源：[Arm newsroom](https://newsroom.arm.com/news/arm-q1-fye27-results)、[DCD](https://www.datacenterdynamics.com/en/news/arm-says-agi-cpu-demand-has-surpassed-2bn-reports-record-royalty-and-licensing-results/)
- **NVDA**：Vera 定位是「CPU for Agents」，強調單核效能，公司稱 2026 年有約 $20B 獨立 CPU 營收的可見度；Q2 FY27 營收 $96.2B。對整體的占比很小。
  來源：[Yahoo/Nvidia $20B CPU](https://finance.yahoo.com/news/nvidia-says-it-will-see-20-billion-in-cpu-sales-this-year-221129958.html)、[Nvidia Q2 FY27 8-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000073/q2fy27pr.htm)
- **RMBS**：Q2 產品營收創新高 $99.2M，Q3 產品營收指引 $110–116M（季增約 14%）。MRDIMM TAM $600M，2028 年全面實現。7 月以後財報好但股價跌，位置低。
  來源：[Rambus Q2 8-K](https://www.sec.gov/Archives/edgar/data/0000917273/000119312526318063/rmbs-ex99_1.htm)、[Investing.com](https://www.investing.com/news/company-news/rambus-q2-2026-slides-record-revenue-tops-200m-on-ai-demand-93CH-4815211)
- **瀾起**：H1 營收 33.35 億（+26.7%）、淨利 19.97 億（+72%），互連晶片 31.11 億；新品 MRCD/MDB、Retimer、CXL MXC 營收都在攀升。9 月中受「AI 放緩」言論拖累，跟著類股下跌。
  來源：[騰訊新聞](https://news.qq.com/rain/a/20260828A0ASS700)、[Sohu 9/28 市值](https://www.sohu.com/a/1081796671_122014422)、[HKEX 公告](https://www.hkexnews.hk/listedco/listconews/sehk/2026/0717/2026071700056_c.pdf)
- **Renesas**：Q2 營收 ¥405.3B（+24.8%），營益率 32.7%，DC 記憶體介面與電源表現強勁。Gen3 MRDIMM（16,000 MT/s）要到 2H27 才量產。近 3 個月的跌幅查不到單一原因（同期類股普遍回檔）。
  來源：[BigGo 法說](https://finance.biggo.com/news/JP_6723.T_2026-07-31)、[Renesas Gen3 MRDIMM](https://www.renesas.com/en/about/newsroom/renesas-gen-3-mrdimm-chipset-solutions-advance-ddr5-memory-performance-16000-mts-next-gen-ai-and-hpc)
- **MU**：FQ4 指引 $50B，FQ3 淨利率 68%。**9/30 盤後公布財報**，建議等財報後再判斷。SOCAMM 營收沒有單獨揭露。
  來源：[GlobeNewswire 財報日](https://www.globenewswire.com/news-release/2026/08/26/3351673/14450/en/micron-technology-to-report-fiscal-fourth-quarter-results-on-september-30-2026.html)、[Alphastreet](https://news.alphastreet.com/micron-technology-mu-q4-2026-preview-eps-est-31-56-reports-september-30/)
- **ALAB**：Q2 營收 $392M（年增 104%），PCIe 6 占營收超過 50%；Q3 指引 $540–560M，Scorpio 成為最大產品線，代表重心往 GPU fabric 偏移。
  來源：[ALAB Q2 8-K](https://www.sec.gov/Archives/edgar/data/0001736297/000173629726000033/q226exhibit991.htm)、[Futurum](https://futurumgroup.com/insights/astera-labs-q2-fy-2026-earnings-pull-scorpio-switch-leadership-forward/)
- **CRDO**：Q1 FY27 營收 $479M（年增 115%），Q2 指引 $525–535M，FY27 成長超過 85%。跟 agent CPU 的連結主要透過 scale-out 網路，屬於間接。
  來源：[Motley Fool 逐字稿](https://www.fool.com/earnings/call-transcripts/2026/09/08/credo-crdo-q1-2027-earnings-call-transcript/)
- **AMKR**：財報好但指引差，股價從 7 月 28 日起一路走弱；通訊 SiP 移往越南是短期拖累。以估值來看，全表最便宜。
  來源：[Motley Fool](https://www.fool.com/investing/2026/07/28/why-amkor-plunged-today/)、[QuiverQuant](https://www.quiverquant.com/news/Amkor+Technology+Falls+as+Investors+Continue+to+Focus+on+Softer+Near-Term+Outlook)
- **BESI**：Q2 營收 €249.9M（+69%），訂單 €292.9M（+129%），混合鍵合客戶從 15 家增加到 21 家；Q3 營收指引季增 10–15%。股價的壓力來自「HBM4 沿用 TCB」的報導。
  來源：[Besi Q2 新聞稿](https://www.besi.com/investor-relations/press-releases/details/be-semiconductor-industries-nv-announces-q2-26-and-h1-26-results/)、[Miru](https://miru.com/analysis/besi-hybrid-bonding-delay-2026)、[TrendForce 併購傳聞](https://www.trendforce.com/news/2026/03/13/news-hybrid-bonding-leader-besi-reportedly-draws-takeover-interest-lam-applied-materials-rumored/)
- **Ibiden**：FY26 營收上修到 ¥550B、OP 上修到 ¥127B（原 ¥90B），明確點名通用伺服器 CPU 載板，被外界解讀為「agent CPU 的訂單簿證據」。
  來源：[I-Connect007](https://iconnect007.com/article/151076/ibiden-raises-fy2026-outlook-on-strong-ai-semiconductor-demand/151073/pcb)、[Wccftech](https://wccftech.com/agentic-ai-is-pulling-cpus-back-into-the-spotlight-and-major-suppliers-substrate-order-book-proves-it/)
- **Advantest**：Q1 營收 ¥367.5B（+39%），SoC 測試 TAM 上修到 $10.5–11.5B，明確提到推論 ASIC、CPU；產能 +70%。
  來源：[Advantest Q1 說明](https://www.advantest.com/document/en/investors/ir-library/result/JE_BIZ_260729_note.pdf)、[Investing.com](https://www.investing.com/news/company-news/advantest-q1-fy26-slides-record-results-raised-guidance-on-ai-demand-93CH-4821155)
- **NET**：Q2 營收 $696M（+36%），Workers 開發者超過 740 萬，Isolates 定位為 agent 沙箱；FY26 指引約 $2.87B。3 個月漲 45%，已經在反映「沙箱＝短期最大槓桿」的論點。
  來源：[Investing.com](https://www.investing.com/news/company-news/cloudflare-q2-2026-slides-agentic-internet-drives-36-revenue-growth-93CH-4844865)、[Yahoo 法說重點](https://finance.yahoo.com/technology/ai/articles/net-q2-earnings-call-highlights-140000285.html)
- **TSM**：Q2 營收 $40.2B、毛利率 67.7%，先進封裝在 2026 年超過營收 10%；Venice 採用 N2＋CoWoS-L＋SoIC。
  來源：[TrendForce](https://www.trendforce.com/news/2026/04/28/news-tsmc-cowos-wafer-asp-reportedly-nears-7nm-levels-advanced-packaging-poised-to-become-a-key-profit-driver/)、[BigGo capex](https://finance.biggo.com/news/5784aaf1-fcbc-4f76-8856-491b9e7175f6)
- **MRVL**：Q2 FY27 營收 $2.739B，DC 占 79%，Q3 指引 $3.15B；FY28 目標 $18B。
  來源：[Marvell 新聞稿](https://investor.marvell.com/news-events/press-releases/detail/1031/marvell-technology-inc-reports-second-quarter-of-fiscal-year-2027-financial-results)
- **Ajinomoto**：ABF 市占約 95%，2Q26 月產能超過 200 萬 m² 且滿載；ABF 的獲利沒有單獨揭露。
  來源：[ChemNet](https://news.chemnet.com/news-8738.html)、[Capital Blueprint](https://capitalblueprint.substack.com/p/ajinomoto-co-inc-deep-analysis-report)
- **Disco**：出貨連 6 年創新高，研磨／切割市占 70% 以上；混合鍵合＋薄晶圓是結構性需求。
  來源：[SemiAnalysis](https://newsletter.semianalysis.com/p/disco-corporation-the-world-leader)

## 四、限制
- stockanalysis、finviz、companiesmarketcap 被 proxy 擋（403）。估值只用 Yahoo timeseries（9/18–23 快照，已按現價換算），沒有第二來源交叉驗證。
- 「CPU 相關占營收 %」大部分是推估，公司都沒有單獨揭露（瀾起、Intel DCAI、AMD DC、Ibiden 電子部門例外）。
- 財報日除了 MU，都是推估，要用公司 IR 頁面再確認。

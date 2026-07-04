# 查證筆記：「1999 年的人到底錯在哪：泡沫裡的持倉指南」（W8）

查證日期：2026-07-04。原則：所有數字附來源；查不到的標「未查得」；計算欄位標明假設。

---

## 1. Nasdaq 1998–2002 關鍵數據

| 項目 | 數字 | 狀態 | 來源 |
|---|---|---|---|
| 1998/10 低點 | 盤中約 1,357（1998/10/8）；文章草稿的 1,419 未直接查得，建議用「約 1,400 附近」或再核對 | 需再確認精確值 | [fedprimerate Nasdaq history](https://www.fedprimerate.com/nasdaq-composite-history.htm)、[Yahoo Finance 歷史數據](https://finance.yahoo.com/quote/%5EIXIC/history/) |
| 1998/12/31 收盤 | 2,192.69 | ✅ 已核 | [fedprimerate](https://www.fedprimerate.com/nasdaq-composite-history.htm) |
| 1999 全年漲幅 | **+85.6%**（Composite；收 4,069.31）。注意：Nasdaq-100 為 +102%，兩者勿混用 | ✅ 已核 | [Wikipedia: Nasdaq Composite](https://en.wikipedia.org/wiki/Nasdaq_Composite)、[macrotrends 年度報酬](https://www.macrotrends.net/2623/nasdaq-by-year-historical-annual-returns) |
| 2000/3/10 頂點 | 收盤 **5,048.62**；盤中高點 5,132.52 | ✅ 已核 | [Wikipedia: Dot-com bubble](https://en.wikipedia.org/wiki/Dot-com_bubble)、[NPR 2015/4/23](https://www.npr.org/sections/thetwo-way/2015/04/23/397113284/15-years-after-the-dot-com-bust-nasdaq-closes-at-new-record) |
| 2002/10 底部 | 2002/10/10 盤中低點 1,108.49；收盤低點約 1,114（2002/10/9） | ✅ 已核（收盤 1,114.11 建議標 2002/10/9） | [Wikipedia: Nasdaq Composite](https://en.wikipedia.org/wiki/Nasdaq_Composite) |
| 最大回撤 | **-78%**（自頂點） | ✅ 已核 | [Wikipedia: Dot-com bubble](https://en.wikipedia.org/wiki/Dot-com_bubble) |
| 回到 5,048 | **2015/4/23** 收 5,056.06，距頂點 15 年 1 個月 13 天 | ✅ 已核 | [NPR](https://www.npr.org/sections/thetwo-way/2015/04/23/397113284/15-years-after-the-dot-com-bust-nasdaq-closes-at-new-record)、[Fortune](https://fortune.com/2015/04/23/nasdaq-supasses-internet-bubble-peak-to-set-new-record/) |

年末收盤（Composite，用於策略計算；與多來源年度報酬一致）：
1998: 2,192.69｜1999: 4,069.31｜2000: 2,470.52｜2001: 1,950.40｜2002: 1,335.51｜2003: 2,003.37｜2004: 2,175.44｜2005: 2,205.32
來源：[FRED NASDAQCOM](https://fred.stlouisfed.org/data/NASDAQCOM)、[fedprimerate](https://www.fedprimerate.com/nasdaq-composite-history.htm)

---

## 2. 三種策略的下場（以 1998/12/31 投入 $100 計，Nasdaq Composite 價格指數，不含股息與稅）

| 時點 | A. 1998 年底離場持現金* | B. 抱到底（buy & hold） | C. 200 日線離場（示意） |
|---|---|---|---|
| 1999/12/31 | $100（+利息約 $105） | **$185.6** | $185.6（仍在場） |
| 2000/3/10（頂點） | ~$106 | **$230.2**（=5048.62/2192.69） | $230.2 |
| 2000/12/31 | ~$110 | $112.7 | 約 $165–175（假設 2000/9–10 跌破 200 日線於 ~3,600–3,800 離場，**需回測確認**） |
| 2002/12/31 | ~$115 | **$60.9**（-39.1%） | 約 $165–175（持現金） |
| 2002/10/9 最低 | — | **$50.8**（若從 1999/1/1 算，等同 -49.2%） | — |
| 2005/12/31 | ~$122 | $100.6（**七年白忙**） | 約 $200+（若 2003 年重新進場，需回測） |

\* 現金假設 3 個月 T-bill，1999–2000 約 5%、2001 起大幅降息，累計約 +15–22%（粗估，**需用 FRED TB3MS 精算**）。

三個可直接引用的結論：
- **a. 1998 年底離場的人贏了**：他錯過 1999 的 +85.6%、在頂點時帳面落後抱股者 117%（$106 vs $230），被嘲笑整整 15 個月——但到 2002 年底，他的 $115 對上抱股者的 $61；直到 2005 年底抱股者仍未追上他。代價是「當 15 個月的傻子」。
- **b. 抱到底的人**：1999/1/1 進場，2002/10 最深 -49%；回到 1998 年底水位要到 **2005 年**（2005 年底收 2,205 才站回 2,192；精確突破日約 2005 年中，需再核）。若不幸在 2000/3/10 頂點進場，回本要等 **2015/4/23**。
- **c. 200 日線策略**：多家回測確認此法「避開了 2000–03 與 2007–09 兩次熊市的大部分跌幅」，S&P 500 上月線訊號版本使買入持有報酬近乎翻倍、回撤縮減約 1/3；代價是盤整期大量假訊號。**但針對 Nasdaq 2000–2002 的精確出場點位與最終淨值，未查得現成數字，需自行回測**。來源：[QuantifiedStrategies](https://www.quantifiedstrategies.com/200-day-moving-average-trading-strategy/)、[QuantPedia](https://quantpedia.com/avoid-equity-bear-markets-with-a-market-timing-strategy-part-1/)、[NewTraderU](https://www.newtraderu.com/2021/01/16/200-day-moving-average-strategy-that-beats-buy-and-hold/)

---

## 3. 賣太早／投降太晚的名人下場

### Julian Robertson（老虎基金）——「對，但死在對之前」
- 給投資人的告別信日期 **2000/3/30**：距 Nasdaq 頂點（3/10）**僅 20 天**。獵奇點：史上最著名的空頭在頂點後三週投降。
- AUM 從 1998 年高峰 **$22B** 掉到關門時約 **$6–6.5B**（1998–2000 投資人贖回約 $7.7B，其餘為虧損；虧損來源：做空科技股＋日圓部位）。
- 信中金句（可直接翻譯引用）："In an irrational market, where earnings and price considerations take a back seat to mouse clicks and momentum, such logic, as we have learned, does not count for much."（在理性讓位給滑鼠點擊與動能的市場裡，這種邏輯不值錢。）
- 來源：[Wikipedia: Julian Robertson](https://en.wikipedia.org/wiki/Julian_Robertson)、[原信全文 A Letter A Day #78](https://aletteraday.substack.com/p/letter-78-julian-robertson-2000)、[Goodwood Capital 信件摘錄](http://blog.goodwoodcapitalmgmt.com/blog/blast-from-the-past-julian-robertsons-letter-from-2000-rings-true-today)

### Stanley Druckenmiller（量子基金）——三段式死法
1. **1999 年初看空**：做空約 $200M 高價科技股 → 虧 **$600M**、當年一度落後。
2. **投降追高**：1999 下半年反手做多科技股，1999 全年反而 **+35%**。
3. **頂點被抬走**：2000/3 加碼買進 **$6B** 科技股，**六週虧 $3B**。
- 名言（多來源一致，可直接引用）："I bought $6 billion worth of tech stocks, and in six weeks I had lost $3 billion in that one play. You asked me what I learned. I didn't learn anything. I already knew that I wasn't supposed to do that. I was just an emotional basketcase and couldn't help myself."另有 "I might have missed the top by an hour."（「八局下」原句未查得，建議改用以上兩句。）
- 來源：[Novel Investor](https://novelinvestor.com/stan-druckenmillers-worst-mistake-ever/)、[TheStreet](https://www.thestreet.com/investing/this-wall-street-investing-legend-once-lost-3-billion-in-six-weeks)、[Yahoo Finance](https://finance.yahoo.com/news/stanley-druckenmillers-big-mistake-164332280.html)

### George Soros / 量子基金 2000/4
- **2000/4/28** Soros 召開記者會：量子基金年初至今 **-22%**（基金規模約 $9B 起算），Druckenmiller 與 Quota 基金經理 Nick Roditi 同日離職。
- 重組：Quantum 與 Quantum Emerging Growth 合併為 **Quantum Endowment Fund**，降槓桿、外包部分操作、裁員約 100 人、退還約 $4B（約 40%）外部資本。
- 來源：[Forbes 2000/4/28](https://www.forbes.com/2000/04/28/mu7.html)、[Wikipedia: Soros Fund Management](https://en.wikipedia.org/wiki/Soros_Fund_Management)

---

## 4. 「實體需求指標 vs 股價誰先轉」——1999/2026 報價對照

- **股價先轉，實體需求晚 3–4 季才轉**：Nasdaq 頂點 2000/3；但美國通訊設備投資**一路成長到 2000 Q4 才見頂**，之後連續七季年減，谷底 2001 Q4（僅為一年前的 69%）。來源：[TIA/FCC 檔案](https://standards.tiaonline.org/gov_affairs/fcc_filings/documents/Nov13-2002_CapEx_QoS_Final.pdf)、[Richmond Fed: Boom and Bust in Telecommunications](https://www.richmondfed.org/~/media/richmondfedorg/publications/research/economic_quarterly/2003/fall/pdf/wolman.pdf)
- 全體 IT 實質投資 **2001 年 -10.7%**（名目 -17%）。來源：[SF Fed 研究](https://www.frbsf.org/wp-content/uploads/er19-34bk.pdf)
- **思科時間線**（股價頂點 2000/3/27）：
  - 2000/11（FY01 Q1 財報）：營收年增仍 ~66%，訂單年增 >70% —— 股價已腰斬，基本面看起來完美。
  - 2001/2（FY01 Q2）：多年來首次 miss。
  - 2000/11 → 2001/4：訂單從 **+70% 直墜至 -30%**，Chambers 稱「同等規模公司史上最快減速」。
  - 2001/4：認列 **$2.2B 存貨減損**（全年含採購承諾共 $2.77B）＋ $1.17B 重組費用；FY01 Q3 實際淨損 $2.69B。
  - 來源：[Cisco 新聞稿 2001/5](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2001/m05/cisco-systems-reports-third-quarter-earnings.html)、[SEC 8-K FY2001](https://www.sec.gov/Archives/edgar/data/0000858877/000089161801500638/f72390ex99-1.txt)、[SupplyChainNuggets](https://supplychainnuggets.com/learning-from-ciscos-2-25-billion-inventory-collapse/)
- **對文章的含義**：2000 年的教訓是「實體需求指標（訂單/capex）是落後指標，股價領先它 9–12 個月」。所以 2026 年「DRAM 合約價還在漲」不能證明股價安全——1999 年的思科訂單也一路漲到股價頂點之後三季。這是全文最反直覺、最有力的一擊。

---

## 5. 估值對比：2000/3 vs 2026/7

| 指標 | 2000/3 | 2026/7 | 來源 |
|---|---|---|---|
| Cisco 市值 | >$500B，全球第一 | — | [Fool](https://www.fool.com/investing/2017/03/16/6-things-you-didnt-know-about-cisco-systems-inc.aspx) |
| Cisco 頂點 P/E | **~201 倍**（trailing；1999 一度 472 倍） | — | [Harding Loevner](https://www.hardingloevner.com/insights/nvidia-and-the-cautionary-tale-of-cisco-systems/)、[Liberty Through Wealth](https://libertythroughwealth.com/2022/03/22/cautionary-tale-of-cisco-systems/) |
| Cisco 頂點後一年 | -77.4%（2000/3/27–2001/3/27）；股價 2025/12 才創新高 | — | [Harding Loevner](https://www.hardingloevner.com/insights/nvidia-and-the-cautionary-tale-of-cisco-systems/)、[Slashdot](https://slashdot.org/story/25/12/11/2013233/cisco-stock-hits-new-all-time-high-25-years-after-the-dotcom-bubble-burst) |
| Nvidia forward P/E | — | **約 20–24 倍**（2026/7/2 各來源 19.9–24.0） | [GuruFocus](https://www.gurufocus.com/term/forward-pe-ratio/NVDA)、[stockanalysis.com](https://stockanalysis.com/stocks/nvda/statistics/)、[macrotrends](https://www.macrotrends.net/stocks/charts/NVDA/nvidia/pe-ratio) |
| 美光/其他 AI 龍頭 P/E | — | **未查得（本次未搜）**，寫稿前補查 stockanalysis.com/MU | — |

關鍵句：思科 200 倍 vs Nvidia ~22 倍 forward——「這次估值不像 2000」是誠實的；但第 4 節說明「訂單還在成長」在 2000 年也成立到最後一刻——「這次需求也不像」則是危險的推論。

---

## 可直接寫進文章 vs 需再確認

**可直接寫（已多來源核實）**
- 5,048.62（2000/3/10）、-78%、1,108/1,114（2002/10）、+85.6%（1999）、2015/4/23 回頂點
- 年末收盤序列與策略 A/B 的計算結果（-39.1%、$230 vs $106、2005 年約略回本）
- Robertson：3/30 關門距頂點 20 天、$22B→$6.5B、信件金句
- Druckenmiller：先虧 $600M（做空）、再六週虧 $3B（做多 $6B）、"I didn't learn anything…" 引言
- Soros：2000/4/28、-22%、重組為 Endowment、退還約 $4B
- 思科：201 倍 P/E、$500B 全球第一、訂單 +70%→-30%、$2.2B 存貨減損、通訊 capex 落後股價 3 季見頂
- Nvidia forward P/E ~20–24（標明查證日 2026/7/2–7/4）

**需再確認**
1. 1998/10 盤中低點精確值（1,357 vs 草稿的 1,419）。
2. 抱股者站回 2,192（1998 年底水位）的精確日期（約 2005 年中）。
3. 策略 C 的 Nasdaq 專屬回測：200 日線 2000–2002 精確出場點與 1999–2005 淨值曲線（現有來源只有 S&P 500 與定性結論）——建議自跑 Yahoo ^IXIC 日線回測。
4. 現金策略的 T-bill 精確累計報酬（FRED TB3MS）。
5. Druckenmiller「八局下 / eighth inning」原句未查得——勿用，改用已核引言。
6. 美光與其他 AI 龍頭 2026/7 P/E。
7. Quantum -22% 的分母（$9B 或 $11B AUM，來源不一）。

---

## 建議文章架構（六段）

1. **開場：一個 20 天的差距**——Robertson 在頂點後 20 天關門、Druckenmiller 在頂點前六週 all-in。史上最聰明的兩個人，一個對太早、一個錯太晚。問題不是「是不是泡沫」，是「在裡面怎麼活」。
2. **三種人的 1999–2005**——策略計算表＋資產曲線圖。核心反轉：早走的人要先當 15 個月的傻子（頂點時落後 117%）才能贏。
3. **「但訂單還在成長」**——思科時間線：股價頂點後 8 個月營收還 +66%、訂單 +70%；capex 晚 3 季才轉負。實體需求指標是落後指標。
4. **像與不像**——估值表：思科 201x vs Nvidia ~22x。誠實承認估值不像 2000；但「需求還在」的安全感在 2000 年一樣存在。
5. **泡沫裡的持倉框架**——從三種策略推出可操作規則：不猜頂（Druckenmiller 教訓）、不硬扛信仰到破產（Robertson 教訓）、用機械規則（趨勢線/減碼階梯）取代「感覺」，接受假訊號成本。
6. **收尾：1999 年的人錯在哪**——不是看錯泡沫，是把「對錯」當成「輸贏」。早走的人輸了辯論、贏了資產。

## 圖表規格

- **圖 1（主圖）**：三種策略資產曲線 1999/1–2005/12，起點 $100；A 現金（含 T-bill）、B 抱到底、C 200 日線（回測後補）。標註三個事件點：2000/3/10 頂點、2000/3/30 Robertson 關門、2000/4/28 Soros 記者會。
- **圖 2**：雙軸時間線 2000/1–2001/12：思科股價 vs 訂單年增率（+70%→-30%）＋通訊 capex 季度值——「股價先死、訂單後死」。
- **表 1**：像與不像對照表（頂點 P/E、市值/GDP、龍頭獲利真實性、capex 資金來源：2000 靠發債的電信商 vs 2026 靠現金流的巨頭）。
- **圖 3（可選）**：從不同進場點的回本年數條形圖（1997、1998、1999、2000/3 進場 → 回本於 1998?、2005、2007?、2015）。

# 記憶體類股 2026/6 下旬–7 月回檔研究報告

查詢日期：2026-07-21。所有近期價格/事件均來自當日網路查證，未使用訓練記憶補價格。
研究者註記：Forbes、stockanalysis.com、macrotrends、japanstockintel 直接抓取被 403 擋下，相關數字改以其他來源交叉核對；被擋且無替代來源者標「未直接核對」。

---

## 0. 總結論（先講答案）

1. **這波主要是「一台機器」的 AI 供應鏈 de-rate，不是記憶體基本面轉弱的開始。**記憶體、被動元件、日本半導體設備、光通訊的重挫日期高度重合（6/23、7/2、7/13–15、7/17、7/20），且每個重挫日的觸發源都是**市場結構/部位/宏觀事件**（韓國槓桿 ETF 強制平倉、SK hynix ADR 上市後的獲利了結＋券商下修、資金輪動報告、美伊戰爭升級），而非任一族群自己的基本面壞消息。
2. **記憶體基本面轉弱「查無實據」**：3Q26 合約價仍在上漲且 TrendForce 於 7 月「上修」預估（PC DRAM 由 +8~13% 上修至 +15~20%）；HBM4 明年價格預估翻倍；SK hynix CEO 7/10 稱 2027 將是「史上最嚴重缺貨」。合約價沒有轉跌、沒有 HBM 砍單證據、Nvidia Rubin 7 月開始放量（延遲已解決）。
3. **但「漲幅收斂＋LTA 封頂」是真實的二階導數轉折**：DRAM 漲幅從 1Q26 的爆量（使用者背景值 +81%，本次未重新核對）收斂到 3Q26 伺服器 DRAM +13~18%；NAND 從 2Q26 +70~75% 驟降至 3Q26 +10~15%；7/13 韓投證券（KIS）以「LTA 把 ASP 漲幅封頂」下修 SK hynix 2026/27 獲利 9%/11%，是這波唯一帶基本面內容的下修。市場正在把「2027 供給浪（CXMT/YMTC）＋LTA 壓平獲利高峰」的辯論提前 price in。
4. **對 2027 減倉時鐘的含義**：辯論提前了，數據還沒轉。減倉時鐘不需因這波股價下跌而提前，但需訂閱四個領先指標（見 §7）。

---

## 1. 事件時間軸（6/19–7/20）

| 日期 | 事件 | 來源 |
|---|---|---|
| 6/19 | Samsung 盤中創歷史新高 ₩374,500 | tradingkey（查詢日 2026-07-21，下同） |
| 6/22 | Kioxia 創歷史高 ~¥112,750；MU 財報前收 ~$1,133 | BigGo Finance / investing.com |
| **6/23（一）** | **KOSPI 收跌約 10%、兩度熔斷**。導火線：金融監督院長 Lee Chan-jin 表示悔未阻擋 5 月底上市的 16 檔 Samsung/SK hynix 單一個股槓桿 ETF（規模約 ₩14 兆、92% 散戶），引發強制平倉。Samsung/SK hynix 各 -12%、Kioxia -15%、**MU -13%（一年來最大單日跌幅）**、光通訊同跌（AOI -13%、Coherent -9%、Lumentum -8%）。Nasdaq 100 期指 -2%+ | investing.com「South Korea leveraged ETF crisis sparks global chip selloff」；Phemex；247wallst 6/23；Forbes 6/23（403，未直接核對原文，內容經上列來源交叉核對） |
| 6/24 | **MU FY26Q3 財報**：營收 $41.5B（超共識 $5.7B）、non-GAAP EPS $25.11、毛利率 84.9%；**Q4 指引 $50B ±$1B、毛利率 ~86%**（超共識 ~$7B）。盤後 +14.6% 至 ~$1,199 | Micron IR / GlobeNewswire 6/24；investinglive |
| 6/25 | MU 財報單手逆轉全球科技賣壓（Fortune：「memory tax」與估值 regime change 論）。**日經、費半、記憶體股同創高點——之後全球半導體市值自此蒸發 ~$1.5 兆** | Fortune 6/25；Yahoo Finance bear-market 專題 |
| 6/26 | MU 收 -6%「wild week」收尾；SK hynix -4%、Samsung -3%+（SK hynix 產能調配報導＋「AI 軍備競賽太貴」的 capex 疑慮開始發酵） | CNBC 6/26；KuCoin flash |
| 6/29 | Samsung -3%+：「AI 投資疑慮持續」 | Seoul Economic Daily 6/29；invezz 6/29 |
| 7/1 | 日經再破 70,000；**太陽誘電創年內高 ¥24,065**；**國巨創歷史高 NT$1,220**；Michael Burry 揭露 MU put（成本基準 ~$1,051） | note/Desk Research Design 7/1；udn；tw.stock.yahoo；Motley Fool 7/15 |
| **7/2（四）** | **全球連鎖跌第二波**：Samsung/SK hynix 各 -9%+（華爾街跌勢外溢）；日經跌破 70,000；Kioxia -12%；光通訊重挫（AOI -17%、Coherent/Lumentum -10%）；太陽誘電自 7/2 起連跌 | CNBC 7/2；invezz 7/2；247wallst 7/2；note（太陽誘電 -38.8%/7 個交易日專文） |
| 7/3 | TrendForce 引韓媒：Samsung 尋求 3Q26 DRAM 合約價最高 +20%、LPDDR 可能 >+20%（基本面反證） | TrendForce news 7/3 |
| 7/6 | 東京電子零組件重挫：太陽誘電 -10.58%、村田 -7.49%（估值疑慮，太陽誘電 PER ~150x） | Tokyo Market Pulse 7/6（403，未直接核對原文；數字取自搜尋摘要） |
| 7/7 | **Samsung 2Q26 初估：獲利創新高（YoY +~1800%）但股價下跌**——「未達 AI 高標」＋capex 疑慮 | CNBC 7/7；Marketplace 7/7 |
| 7/9 | TrendForce：3Q26 伺服器 DRAM 合約價 +13~18% QoQ（LTA 封頂）；**同時上修 PC DRAM 至 +15~20%（原 +8~13%）** | TrendForce press 20260709；KuCoin flash |
| 7/10 | **SK hynix ADR 於 Nasdaq 掛牌首日 +14%**；SK hynix CEO：2027 將現「史上最嚴重記憶體缺貨」、需求超供給至 2030 後 | indmoney；US News 7/10 |
| 7/12 | 首爾經濟日報：**HBM4 價格明年估翻倍**（2H26 ~$2/Gb → 2027 $4–5/Gb；~$500/stack） | en.sedaily.com 7/12 |
| **7/13（一）** | **SK hynix 首爾 -15.4%（史上最大單日跌幅）、KOSPI -9%、全市場暫停交易**。觸發：韓投證券（KIS）預估 2Q26 OP ₩60.4 兆、低於共識 ₩65 兆約 8%；下修 2026/27 OP 各 9%/11%；核心論點＝**LTA 使 2Q 混合 DRAM ASP QoQ 由市場預期 +50% 降為 +28.9%（漲價被封頂）**。Samsung -11%。外溢美股：SKHY ADR -9.3%、MU/SNDK/WDC -6% | CNBC 7/13；techtimes 7/13；Advisor Perspectives；247wallst 7/13 |
| 7/14 | Roundhill Memory ETF（DRAM）首次收在成立以來 VWAP 之下 | gurufocus 7/14 |
| **7/15（三）** | 記憶體再殺：**MU -9%（收 ~$983）**、SanDisk -11%、AMD/INTC/MRVL -5%+；光通訊同跌（AOI -12%、Coherent/Lumentum 下滑）；背景為 SK hynix 展望轉弱之外溢＋高檔情緒逆轉 | Yahoo Finance 7/15；247wallst 7/15；Motley Fool 7/15（403，未直接核對原文） |
| 7/16 | DRAM ETF 收 $52.71（-8.17%）；Kioxia 跌至 ~¥63,100 | financecharts/stockinvest；invezz 7/16 |
| **7/17（五）** | **日經 -4.03% 收 64,141（-2,694 點，年內最大跌幅），進入修正（較 6/25 紀錄 -11.4%）**。Kioxia -16.1%（一度跌停，一個月市值腰斬、蒸發 ~$185B）、Sumco -15.2%、Screen -12%；Advantest 距年高 -25%、TEL -21% | EBC 7/17；invezz 7/17；BigGo；tradingkey 7/17 |
| 7/18–19（週末） | **美伊衝突升級**：美軍因美軍人員陣亡發動新一輪空襲；Brent 一度 +3.8% 破 $91（一個月高）；荷莫茲海峽風險＝IEA 稱「史上最大石油供給中斷」 | Bloomberg 7/19；CNN 7/18；Reuters |
| **7/20（一）** | 亞股再殺：日經續跌（SoftBank/TEL/Kioxia）；**台灣被動元件多檔跌停（國巨、華新科、禾伸堂、日電貿、信昌電、雷科）**，國巨自 7/1 高點 -48%（1220→630）；國巨澄清陳泰銘家族未賣股。SK hynix 收 ₩1,829,000（距 6/25 高點 ₩2,987,000 **-38.8%**）。MU 收 $872.25（+0.78%，止穩） | invezz 7/20；壹蘋 7/20；udn 7/20；tradingview/investing（SK hynix 價格）；stockinvest.us（MU 收盤） |

---

## 2. 逐項回答

### 2.1 近 1 個月與 3 個月表現（截至 7/20–7/21 查證）

| 標的 | 高點（日期） | 最近價（日期） | 距高點 | 近 1 月（約） | 近 3 月 | 來源 |
|---|---|---|---|---|---|---|
| MU | ~$1,246（7 月上旬） | $872.25（7/20 收） | **-30%** | ~-23%（6/20 ~$1,133→872；7/14 前僅 -4.5%，殺盤集中在 7/13 後） | **未直接核對**（4 月中價位查無可靠免費來源；YTD 仍大幅為正——6/23 前一年內最大跌幅僅出現過一次） | tradingkey；stockinvest.us 搜尋摘要；gurufocus 7/14 |
| SK hynix（000660.KS） | ₩2,987,000（6/25） | ₩1,829,000（7/20） | **-38.8%** | ~-35% | YTD 高點時 +~260%，3 個月**估仍為正**（未逐日核對） | Yahoo/investing 歷史價；CNBC |
| Samsung（005930.KS） | ₩374,500 盤中（6/19） | -30% 區間 | **~-30%** | -18.5%（至 7/14）後再殺 | H1 漲逾 100%，3 個月估仍為正 | weex/tradingkey；gurufocus 7/14 |
| Kioxia（285A.T） | ~¥112,750（6/22） | ¥52,390（7/17）；7/20 續跌 | **~-52~54%** | 一個月市值腰斬（-$184.7B） | 未直接核對（IPO 後 YTD 曾漲逾三倍） | tradingkey 7/17；BigGo |
| SanDisk（SNDK） | ~$2,343 | ~$1,615–1,745（7 月中） | **~-31%** | 7/13 -6%、7/15 -11%、另有單日 -14.13% | 未直接核對 | tradingkey；coincentral |
| Roundhill Memory ETF（DRAM） | $81.34（52 週高） | $52.71（7/16） | **-35%** | 7/14 首次跌破成立 VWAP | 4 月初成立以來曾翻倍，**3 個月仍為正** | financecharts；gurufocus 7/14；Motley Fool 7/7 |

關鍵下跌日與觸發（全部經多來源核對）：**6/23**（韓槓桿 ETF 平倉）、**6/26–7/2**（capex 疑慮＋輪動）、**7/13**（KIS 下修＋ADR 後獲利了結）、**7/15**（延續殺）、**7/17**（日本補跌年內最大）、**7/20**（美伊升級＋被動元件跌停潮）。

### 2.2 基本面數據（記憶體）

**合約價——仍在漲，且被上修，但斜率大幅收斂：**
- 伺服器 DRAM 3Q26：**+13~18% QoQ**，供給仍短缺，LTA 封頂使漲幅受限；季內報價仍可能上修（TrendForce press 20260709，https://www.trendforce.com/presscenter/news/20260709-13140.html，查詢 2026-07-21）。
- PC DRAM 3Q26：**上修至 +15~20%**（原 +8~13%）（KuCoin 引 TrendForce，查詢 2026-07-21）。
- NAND 3Q26：**+10~15% QoQ**，較 2Q26 的 **+70~75%** 急劇收斂（TrendForce press 20260703，https://www.trendforce.com/presscenter/news/20260703-13134.html）。
- 消費型 DRAM 缺貨延伸到 DDR2，3Q26 續漲（TrendForce 20260622）。
- Samsung 尋求 3Q26 DRAM 最高 +20%、LPDDR >+20%（TrendForce news 7/3）。
- 使用者背景值「1Q26 +81%」本次未重新核對；「3Q26 +13~18%」已核實。**方向：續漲；斜率：續收斂。**

**HBM 供需與 HBM4 定價——偏多：**
- HBM4 價格 2H26 ~$2/Gb → 2027 估 $4–5/Gb（翻倍以上）；Samsung/SK hynix 掌握議價權，並取得「事後補價」（post-settlement）條款（Seoul Economic Daily 2026-07-12，https://en.sedaily.com/finance/2026/07/12/…，查詢 2026-07-21）。
- Nvidia HBM4 分配：SK hynix ~2/3、Samsung >30%（價格與 SK hynix 看齊）、Micron 亦爭取 16-Hi 訂單（TrendForce 1/28、digitimes、tweaktown）。
- SK hynix CEO（7/10）：2027 恐現**史上最嚴重供給短缺**、需求超過供給到 2030 之後（US News 7/10）。
- Rubin 延遲已解決、7 月起放量（KeyBanc，Gate/tradingkey 引述）；**查無 HBM 砍單、查無 Nvidia 供應鏈砍單**。反而 HBM4 供給不足才是 Rubin 的瓶頸（SDxCentral）。
- 反面：部分研究與外媒提出 HBM 價格 2026 後可能因競爭與擴產進入修正（sedaily 引述，未具名——證據等級低）。

**CXMT / YMTC 擴產——2027 的真實風險：**
- CXMT：2026 年底產能估 ~350K wspm，僅比 Micron 少 25K，將成全球第四→第二大 DRAM 生產體；~20%（60K）轉 HBM3，目標 2026 年底量產；上海新廠（合肥 2–3 倍規模）2027 量產（Tom's Hardware，查詢 2026-07-21）。
- YMTC：武漢新廠 2H26 量產，NAND 產能將超越 SK hynix/Micron 成第三；其中約半數產出轉 DRAM（~50K wspm）（Tom's Hardware / kr-asia / digitimes 5/14）。
- 分析師共識：**供給浪預計 2027 到頂撞上市場**（kr-asia、techwireasia）。中國隊目前產品主力仍在 DDR4/LPDDR/HBM3 等非尖端，2026 內對高階市場衝擊有限。

### 2.3 AI capex 消化疑慮：觸發了什麼

- **UBS 預估**：hyperscaler capex 2026 +76% 至 $673B → **2027 僅 +25% → 2028 +6%**——增速斷崖是 7 月中旬資金重倉調整的核心敘事（Reuters analysis 7/17，via 933thedrive/globalbankingandfinance，查詢 2026-07-21）。
- **Morgan Stanley（Mike Wilson）**：呼籲從記憶體/半導體輪動到 hyperscaler（tradingkey 7/17 引述）。
- 部分基金經理人「大砍記憶體與設備股、加碼 hyperscaler 與醫療」（Reuters 7/17）。
- **查無** hyperscaler 下修 capex 指引的實據（Q1 財報季確認 2026 合計 ~$673–725B）；**查無**Nvidia 砍單。疑慮=「2027 增速」預期，非「2026 金額」下修。
- 個股訊號：Burry 於 ~$1,051 建 MU put（7/1）；MU 內部人賣股達 2010 以來最高（CEO 為 10b5-1 預定計畫）（gurufocus/Forbes 系列，查詢 2026-07-21）。

### 2.4 共同因子檢定（核心問題）

**同跌日期重合度：極高。**四個族群在以下日期同步重挫（各自代表股與跌幅見 §1 時間軸）：

| 日期 | 記憶體 | 被動元件 | 日本設備 | 光通訊 |
|---|---|---|---|---|
| 6/23 | MU -13%、SKH/三星 -12%、Kioxia -15% | （日本零組件同日回落，幅度較小） | 日經重挫、SPE 下跌 | AOI -13%、COHR -9%、LITE -8% |
| 7/2 | 三星/SKH -9%+、Kioxia -12% | 太陽誘電開始連 7 日 -38.8% | 日經破 70,000 | AOI -17%、COHR/LITE -10% |
| 7/6 | （亞股弱） | 太陽誘電 -10.6%、村田 -7.5% | — | — |
| 7/13–15 | SKH -15.4%（史上最大）、MU -9%、SNDK -11% | 國巨「8 天跌逾 3 成」區間 | （日股跟跌） | AOI -12%、COHR/LITE 下滑 |
| 7/17 | Kioxia -16%（跌停） | （同日重挫） | 日經 -4%（年內最大）、Advantest/TEL 主跌 | — |
| 7/20 | Kioxia 續跌、SKH -38.8% 累計 | 台被動元件多檔跌停、國巨 -48% 累計 | SoftBank/TEL 續跌 | — |

**觸發源譜系（每個重挫日都是跨族群共同事件，非個別基本面）：**
1. 6/23＝韓國 16 檔單一個股槓桿 ETF（₩14 兆、92% 散戶）強制平倉——純市場結構事件。
2. 7/2＝華爾街 AI 高估值賣壓外溢——部位/估值事件。
3. 7/13＝KIS 對 SK hynix 的 LTA 封頂下修＋ADR 上市後獲利了結——**唯一帶基本面內容**，但內容是「漲價被合約平滑」而非「價格下跌」。
4. 7/17–20＝資金輪動（UBS 增速斷崖＋MS 輪動報告）＋美伊戰爭升級（油價 >$91、通膨/風險偏好）——宏觀事件。

**共同暴露因子**：四個族群共同點=「AI 供應鏈、YTD 漲 1–7 倍、估值極端（太陽誘電 PER 150–170x、村田 80x+、Coherent 189x、Lumentum 146x）、外資 H1 已在創紀錄減持亞洲 AI 集中部位」。Goldman Sachs 亦公開表示韓國賣壓反映新 ETF 部位平倉、**半導體週期基本面仍強**（techtimes 7/15 引述）。

**各自獨立利空的檢查**：
- 被動元件：有「放大器」但非獨立源——6 月 Morgan Stanley 降太陽誘電至 Underweight；台媒歸因=本益比過高＋漲價引發下游改設計減用量的「暗黑慣性」擔憂＋殺價競爭（陳重銘/股魚評論，屬觀點非數據）；國巨澄清大股東未賣股。**查無**被動元件砍單/降價的具名數據。跌幅（-40~50%）深於記憶體本身，反映其估值倍數更極端。
- 日本設備：Advantest/TEL 財報強勁後下跌（invezz 7/17 明言「earnings robust、屬情緒與獲利了結」）；日圓 ~162（40 年低）是先前的順風而非 7 月的利空；外資對日股在 7/11 當週仍淨買 ¥745.6B。**查無**獨立利空。
- 光通訊：估值 reset（247wallst 系列），Coherent/Lumentum 財報皆大幅成長。**查無**獨立利空。

**判定：一台機器（共同因子 de-rate），信心度高。**被動元件另有估值放大器與「週期慣性」記憶，跌幅最深，但下跌日曆與記憶體完全同步、且無獨立的基本面壞消息。

### 2.5 資金面

- **外資 H1 2026 以至少 16 年來最快速度賣超亞股（不含日本）$137.36B**；韓國 $70.8B、台灣 $29.6B 最重；6 月單月 $27.08B（韓 $12.63B、台 $8B）。H1 賣超 Samsung ₩72.57 兆、SK hynix ₩57.13 兆。性質＝**集中度再平衡與匯率避險，非單純 risk-off**（Reuters via marketscreener/investinglive 7/2；koreajoongangdaily，查詢 2026-07-21）。
- **台灣**：H1 外資賣超逾 NT$8,000 億但 TAIEX H1 +62%（內資/當沖撐盤）；上半年淨匯入創紀錄 NT$2.44 兆（BigGo Finance）。
- **日本為資金避風港**：外資 7/11 當週淨買日股 ¥745.6B（Reuters TABLE 7/15）；資金由韓台移往日本（koreajoongangdaily）。7/17 日本補跌因此更像「最後一個高地失守」而非外資先賣。
- **日圓**：USD/JPY ~162、日圓 40 年低（japan.co.jp 7/1、7/9）。弱圓先前是日本半導體股的三大順風之一（弱圓＋國策＋AI）；7 月回檔期間查無日圓急升觸發平倉的證據——日股下跌主因是美股半導體外溢，非匯率。

---

## 3. 「基本面轉弱」證據清點（驗收條件三）

**有實據者（真實但屬二階/前瞻）：**
- 合約價漲幅收斂：NAND +70~75%（2Q）→ +10~15%（3Q）；伺服器 DRAM +13~18%（3Q）。〔TrendForce，一手〕
- LTA 封頂：KIS 估 SKH 2Q 混合 DRAM ASP QoQ +28.9% vs 市場預期 +50%；下修 2026/27 OP 9%/11%。〔KIS via CNBC/techtimes〕
- 中國供給浪：CXMT 2026 底 ~350K wspm＋HBM3 年底量產；YMTC 武漢 2H26 量產＋轉 DRAM。分析師指向 2027 撞牆。〔Tom's Hardware 等〕
- Hyperscaler capex 增速預估斷崖：2027 +25%、2028 +6%（UBS 預估，非公司指引）。

**無實據者（查無）：**
- 合約價轉跌：**查無**——3Q26 全線續漲且部分上修。
- HBM 砍單：**查無**——HBM4 分配/定價談判進行中、明年價格看倍增、Rubin 放量。
- Hyperscaler 下修 2026 capex：**查無**。
- Nvidia 供應鏈砍單：**查無**——Rubin 延遲反因 HBM4 短缺，7 月已解決放量。
- 記憶體公司財測下修：**查無**——MU 6/24 指引大超；Samsung 2Q 初估獲利創高；SKH 尚未發 2Q 正式財報（KIS 為券商預估）。

**判定：這波是估值/部位/情緒回檔疊加宏觀（美伊），不是基本面轉弱的開始。**但市場已把「2027 供給浪＋LTA 平滑獲利高峰」從 2027 的辯論提前到現在定價——這是估值 regime 的變化，不是週期數據的變化。

---

## 4. 反面訊號（會推翻上述判定的證據，按殺傷力排序）

1. **KIS 的 LTA 論點若普遍化**：若 SKH 7 月底正式財報證實 ASP 傳導遠低於市場模型，「超級週期獲利高峰被合約平滑」會從一家券商觀點升級為產業事實——MU 86% 毛利率指引是否可持續將被重新質疑。
2. **NAND 斜率**：+70~75% → +10~15% 的收斂速度極快；NAND（SanDisk/Kioxia 曝險）比 DRAM 更接近「見頂」，兩者本波跌幅最深（-31%/-52%）並非偶然。
3. **CXMT HBM3 若年底如期量產**且通過中國客戶驗證，2027 HBM 議價權故事將弱化——留意 4Q26 驗證新聞。
4. **UBS 2027 +25% 若再下修**：任一 hyperscaler 在 3Q 財報季（10 月）給出保守 2027 capex 展望，就是「消化期」實錘。
5. **被動元件的「暗黑慣性」**：漲價→下游改設計減用量→總需求崩——若 MLCC 出現實際砍單數據（目前僅是台媒評論的擔憂），代表 AI 硬體 BOM 通縮開始，會回頭傷記憶體的消費端。
6. **美伊戰爭**：荷莫茲中斷若持續，油價通膨壓制估值的時間會拉長，反彈窗口延後。
7. 內部人訊號：MU 內部人賣股 2010 以來最高＋Burry put——情緒面反指標，但 2010 那次之後的走勢值得警惕。

---

## 5. 事實 / 推論 / 不確定

**事實**（多來源核對）：時間軸各事件與跌幅；TrendForce 3Q26 價格預估；KIS 下修內容；外資流向數據；HBM4 定價報導；CXMT/YMTC 產能數字（研究機構估計）。
**推論**（作者判斷）：「一台機器」判定；被動元件跌幅深係因估值放大器；2027 減倉時鐘不需提前；日圓非本波主因。
**不確定/未核對**：MU 與各股精確 3 個月報酬（價格網站被 403）；使用者背景值 1Q26 +81%；「HBM 2026 後修正」傳聞（未具名）；村田確切 drawdown（台媒稱 ~-40%，未直接核對日方數據）；6/23 Forbes 與 7/15 Motley Fool 原文（403，經替代來源核對）；7/17 日經跌點兩來源略有出入（-2,694 收盤 vs -2,880/-2,940 盤中）。

---

## 6. 主要來源清單（查詢日期均為 2026-07-21）

1. TrendForce 3Q26 伺服器 DRAM +13~18%：https://www.trendforce.com/presscenter/news/20260709-13140.html
2. TrendForce 3Q26 總覽（NAND +10~15%、漲幅收斂）：https://www.trendforce.com/presscenter/news/20260703-13134.html
3. TrendForce：Samsung 尋求 3Q26 DRAM +20%：https://www.trendforce.com/news/2026/07/03/news-samsung-reportedly-seeks-up-to-20-3q26-dram-price-increase-lpddr-hikes-may-exceed-20/
4. Micron FY26Q3 財報（IR）：https://investors.micron.com/news-releases/news-release-details/micron-technology-inc-reports-record-results-third-quarter
5. 韓國槓桿 ETF 危機：https://finance.yahoo.com/markets/stocks/articles/south-korea-leveraged-etf-crisis-124927381.html
6. CNBC 7/13 SK hynix -15.4%：https://www.cnbc.com/2026/07/13/sk-hynix-shares-fall-after-stellar-nasdaq-debut.html
7. techtimes 7/13 KIS/LTA 細節：https://www.techtimes.com/articles/320352/20260713/sk-hynix-posts-worst-seoul-session-record-hbm-contracts-limit-earnings-upside.htm
8. Seoul Economic Daily HBM4 價格倍增：https://en.sedaily.com/finance/2026/07/12/hbm4-prices-to-double-next-year-as-samsung-sk-hynix-keep
9. SK hynix CEO 2027 缺貨：https://money.usnews.com/investing/news/articles/2026-07-10/sk-hynix-ceo-sees-worst-ever-memory-supply-shortage-in-2027-says-demand-to-outstrip-supply-beyond-2030
10. EBC 日經 7/17 修正：https://www.ebc.com/forex/nikkei-correction-chip-selloff-july-2026
11. invezz 7/17 TEL/Advantest/Kioxia：https://invezz.com/news/2026/07/17/heres-why-tokyo-electron-advantest-and-kioxia-stocks-are-plunging-today/
12. tradingkey Kioxia 腰斬：https://www.tradingkey.com/analysis/stocks/us-stocks/262036414-stock-ai-kioxia-price-japan-skhy-sndk-wdc-mu-tsmc-tradingkey
13. Reuters 外資 H1 賣超 $137B：https://investinglive.com/stock-market-update/foreigner-investors-pull-record-137bn-from-asia-stocks-as-ai-rally-forces-rebalancing-20260702/
14. koreajoongangdaily 韓→日資金移動：https://www.koreajoongangdaily.com/business/tokyo-drift-foreign-investors-abandon-korean-taiwanese-stocks-for-japan/12754589
15. Reuters/933thedrive UBS capex 減速與基金輪動：https://www.933thedrive.com/2026/07/17/analysis-among-ai-crowd-some-investors-position-for-slower-hyperscaler-spending-growth/
16. Tom's Hardware CXMT：https://www.tomshardware.com/pc-components/dram/cxmt-close-to-matching-microns-memory-capacity-in-2026-research-claims-would-put-china-on-track-to-become-worlds-second-largest-dram-producer
17. udn 國巨 1220→630：https://udn.com/news/story/12806/9640418
18. 壹蘋 7/20 被動元件跌停/家族澄清：https://news.nextapple.com/finance/20260720/CD725CDECB039C1EBCE7828625E443F9
19. note 太陽誘電 7 日 -38.8%：https://note.com/invest_news_lab/n/n0c79c8c99929
20. Bloomberg 7/19 美伊升級/油價：https://www.bloomberg.com/news/articles/2026-07-19/oil-climbs-as-middle-east-conflict-escalates-markets-wrap
21. 247wallst 光通訊系列（6/23、7/2、7/15）：https://247wallst.com/investing/2026/07/02/applied-optoelectronics-plunges-17-coherent-and-lumentum-sink-10-as-photonics-stocks-reset/
22. Reuters TABLE 外資淨買日股：https://www.tradingview.com/news/reuters.com,2026-07-15:newsml_AZN4T810L:0-table-foreign-investors-net-buyers-of-japan-shares-for-last-week/

## 7. 建議盯梢的四個領先指標（供 2027 減倉時鐘校準）

1. SK hynix 2Q26 正式財報（7 月底）：ASP 傳導 vs KIS 的 28.9%——LTA 論點的裁決。
2. TrendForce 4Q26 合約價預估（~10 月）：是否首次出現持平/轉跌。
3. CXMT HBM3 量產/驗證新聞（4Q26）＋YMTC 武漢投產。
4. 美系 hyperscaler 3Q 財報（10 月底）的 2027 capex 語氣 vs UBS +25%。

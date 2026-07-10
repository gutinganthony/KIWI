# 13F 機構持倉跟單：散戶可驗證超額報酬研究筆記

研究日期：2026-07-10。方法：WebSearch 快照（WebFetch/curl 被 403 擋，無法讀原文全文，數字以搜尋摘要為準）。
標註：【學術實證】同儕審查或廣被引用的工作論文｜【實務績效】真實資金/ETF 實盤｜【廠商宣稱】未經獨立驗證｜【推理】本筆記的推論。
信心層級：高＝多來源交叉一致；中＝單一可靠來源；低＝二手轉述或行銷材料。

---

## 一句結論

**13F 克隆「平均而言」不再賺錢（實盤 ETF 五支死三支、GURU 落後大盤），但「低週轉、集中持倉、長 horizon 的價值型管理人」子集仍有跨研究一致的正超額證據（+2.8%～+10.75%/yr 區間，多為 2019 年前樣本）。45 天延遲對這類慢錢幾乎無成本（巴菲特研究中僅吃掉 ~0.4pp/yr）。合理期望：篩選後 0～+4%/yr，且要忍受巨大 tracking error。**

---

## 1. 學術實證

### 1a. 巴菲特克隆（黃金標準研究）
- **Martin & Puthenpurackal (2008), "Imitation is the Sincerest Form of Flattery"**（SSRN 806246）：1976–2006 追蹤 Berkshire 13F。
  - Berkshire 本尊組合：31 年中 27 年贏大盤，平均超越 S&P 500 **+11.14%/yr**。
  - **克隆組合（公開揭露後次月月初才買入）：仍有 +10.75%/yr 超額，統計顯著。**
  - → **45 天延遲只吃掉約 0.4pp/yr**（11.14 → 10.75）。對極低週轉的管理人，延遲成本趨近於零。
  - 來源：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=806246 （2008）。信心：高（廣被引用，多來源數字一致）。
  - ⚠️ 樣本止於 2006。Berkshire 本尊 2010s–2020s 的 alpha 已歸零（見 §3），此數字**不可外推到現在**。

### 1b. Best Ideas（集中度＝資訊含量）
- **Cohen, Polk & Silli / Antón, Cohen & Polk, "Best Ideas"**（SSRN 1364827；HBS WP 21-004 更新版，2021）：
  - 主動型共同基金經理「最高信念持倉」（相對權重 tilt 最大的一檔）超越市場 **+2.8%～+4.5%/yr**（依基準而異）；其餘持倉無顯著超額。
  - 70%+ 的 best idea 只屬於單一經理人（非共識股）。樣本 1991–2005（更新版延伸）。
  - 來源：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1364827 ・ https://www.hbs.edu/ris/download.aspx?name=21-004.pdf （2010/2021）。信心：高。
  - 含義：**訊號在「超配集中度」，不在持倉本身**。克隆管線應加權「相對基金規模的超配幅度」，不是抄整個組合。

### 1c. Copycat 基金可行性
- **Verbeek & Wang (2013), "Better than the Original? The Relative Success of Copycat Funds"**，J. Banking & Finance 37(9)：
  - 免費搭便車複製共同基金揭露持倉，**扣除交易成本與費用後，平均略勝本尊**（本尊要付研究費用，克隆者不用）。2004 年 SEC 強制季度揭露後，克隆相對成功率顯著上升。
  - 來源：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1566794 （2013）。信心：高。

### 1d. 系統性對沖基金 13F 克隆（含經理人篩選）
- **Angelini, Iqbal & Jivraj, "Systematic 13F Hedge Fund Alpha"**（SSRN 3459526，2019/2020）：
  - 全體對沖基金 13F 的「best ideas」與總持倉**無顯著差異**（與共同基金研究相反——因為 13F 看不到空頭與衍生品）。
  - 但**篩選「長 horizon 選股型」經理人**後，結合 conviction＋consensus 的策略：超越 S&P 500 **+3.80%/yr，Sharpe 0.75**（2004Q1–2019Q2）。
  - 來源：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3459526 ・ https://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-090-Farouk-Jivraj.pdf （2019）。信心：高（對本研究問題最直接的一篇）。
- **Schroeder (2024/2025), "Outperforming the Market: Portfolio Strategy Cloning from SEC 13F Filings"**（SSRN 5399672）：宣稱 top-quartile 克隆組合風險調整後年化超越 S&P **+24.3%**。工作論文、未經同儕審查、數字離群。信心：低，**不採信為期望值依據**。
  - 來源：https://papers.ssrn.com/sol3/Delivery.cfm/5399672.pdf?abstractid=5399672&mirid=1
- 二手綜述（Quantpedia "Alpha Cloning – Following 13F Filings"：https://quantpedia.com/strategies/alpha-cloning-following-13f-fillings ）也收錄同方向結論。信心：中。

### 1e. 延遲與 alpha 半衰期
- 二手引用（exponential-tech.ai，2024/2025，轉述學術研究）：新買入持倉的增量 alpha 首月約 36bps，**半衰期約 4 個月**——對高週轉基金，45 天延遲吃掉大半；對低週轉基金影響小。信心：低（二手轉述，找不到原始論文名）。
  - 來源：https://www.exponential-tech.ai/post/13f-blind-spot
- 對照 §1a：低週轉極端值（巴菲特）延遲成本僅 0.4pp/yr。【推理】延遲成本與管理人週轉率成正比——這是「可跟畫像」的核心變數。

---

## 2. 哪類機構可跟（13F 版「可跟畫像」）

**可跟（有實證支持）**：
- 低週轉（年換手 <30%～50%）、集中持倉（top-10 佔比高）、長 horizon 選股型、long-only 或 long-bias 價值型（Berkshire、Pabrai 型）。§1a/§1d 的正結果全部來自這個子集。
- Pabrai 本人的「shameless cloning」實務（從 Buffett/Munger 等 9 家價值型抄）就是這個畫像的實踐；Dataroma 追蹤 ~81 位「superinvestors」即此類名單。來源：https://www.dataroma.com/m/holdings.php?m=PI ・ https://www.compoundwithrene.com/p/shameless-cloning-20-pabrais-idea （2026）。信心：中（策略描述可靠，Pabrai 克隆組合本身無公開審計績效——**查無**其克隆組合的可驗證實盤數字）。

**不可跟（有實證或結構性理由）**：
- **量化/高週轉基金**：45 天後持倉早已換掉，alpha 半衰期 ~4 個月（§1e）。
- **多空對沖基金**：13F 只揭多頭。空頭、put 對沖、私募、債券、現金、多數衍生品全部看不到——表面持倉可能與真實曝險**完全相反**（例：多頭 1% 現貨＋空頭 2% 的組合，13F 只顯示多頭）。來源：https://en.wikipedia.org/wiki/Form_13F ・ https://capitalgains.thediff.co/p/13f 。信心：高（結構性事實）。
- 有論文指控策略性誤報：Notre Dame "Do Hedge Funds Strategically Misreport Their Holdings?"（https://www3.nd.edu/~zda/Restatement.pdf ）。信心：中。
- 申報行為佐證：對沖基金刻意壓到最後一天申報——僅 24% 在第 40 天前交件，30% 集中在第 45 天（Wharton/Musto, "Why Do Institutions Delay Reporting Their Shareholdings?"：https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/13-15.musto_.pdf ）。信心：高。

**篩選條件（綜合 §1d 與畫像）**【推理】：
1. 換手率低（連續多季持倉重疊率 >70%）
2. 持倉集中（top-10 >50%）
3. 13F 佔其 AUM 比例高（long-only 型，衍生品/空頭少）
4. AUM 別太大（>500 億美元的巨獸建倉期長達數季，13F 快照失真）
5. 有長期選股紀錄（非 activist 一次性事件驅動）

---

## 3. 衰減與擁擠

- **巴菲特克隆本身已死**：Berkshire 過去十年年化 ~11.8% vs S&P 12.0%；滾動 10 年 value-add 目前為零；多篇分析指 Buffett 近 20 年無超額。1976–2006 的 +10.75% 是歷史文物。來源：https://www.ainvest.com/news/berkshire-hathaway-historic-underperformance-shift-ai-driven-markets-2512/ （2025）・ https://www.morningstar.com.au/markets/even-warren-buffett-lost-his-edge-20-years-ago ・ https://www.cordantwealth.com/underperformance-a-feature-not-a-bug/ 。信心：高。
  - 【推理】這是「本尊 alpha 消失」而非「克隆機制失效」——克隆的上限永遠是本尊的 alpha 減延遲成本。挑錯本尊，機制再好也是零。
- **克隆 ETF 的興衰模式**：GURU 成立（2012/6）至 2015/8 累計贏 S&P 12.26pp → 2015–16 修正中全數回吐 → 之後長期落後。Klement (CFA Institute, 2021)：近 10 年 GURU/ALFA 各落後 **-1.3%/-1.6%/yr 且波動更高**，是「晴天策略」（fair-weather）。來源：https://blogs.cfainstitute.org/investor/2021/09/22/does-guru-investing-work/ （2021）。信心：高。
- **申報日跳升**：個案證據——2026/2 Berkshire 13F 揭露新建倉 NYT，NYT 盤前跳 +2.6%。來源：https://finance.yahoo.com/news/berkshire-issues-last-13f-buffett-221005128.html （2026）。二手描述稱「熱門對沖基金持股在 13F 揭露時立即價格反應，壓縮跟隨者窗口」。**查無**正式 event-study 的系統性量化數字（本輪搜尋範圍內）。信心：個案高／系統性結論低。
- **擁擠的雙面性**：擁擠股在市場壓力期跌幅超出傳統風險指標預期（2020/3：S&P -19.6%，GVIP -21.4%，ALFA -25.1%）；散戶大規模跟單本身推高買入價、壓縮未來報酬。來源：https://blogs.cfainstitute.org/investor/2021/09/22/does-guru-investing-work/ ・ https://caia.org/blog/2014/10/23/hedge-funds-and-position-crowding/ 。信心：中-高。

---

## 4. 實務工具與數據源

### 免費、可程式化（管線可用）
- **SEC 官方 Form 13F Data Sets**（DERA）：結構化季度數據集，免費 bulk 下載，覆蓋 2013Q2 至今，每季 ~3,000–4,000 家申報機構，2024/3 起按 2/5/8/11 月週期出版。來源：https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets ・ https://catalog.data.gov/dataset/form-13f-data-sets 。信心：高。**管線首選——零成本、官方、結構化。**
- EDGAR 本身的 filing 索引/全文檢索 API 免費（sec-edgar-downloader、py-sec-edgar 等開源工具現成）。付費捷徑：sec-api.io（非必要）。

### 現成追蹤器（人工查核/名單來源）
- **Dataroma**：免費，~81 位 superinvestors（正是「可跟畫像」名單），人工比對 EDGAR 後才更新。https://www.dataroma.com
- **13f.info / Holdings Channel**：免費、無帳號查詢任何申報機構。
- **WhaleWisdom**：免費層（近 2 年數據＋回測）；API/Excel 匯出 $300/yr。其 **WhaleIndex** 宣稱 2006 年以來年化 20.74%、近 1/3/5 年翻倍於 S&P——【廠商宣稱】回測行銷數字，未經獨立驗證，信心：低。來源：https://whalewisdom.com/whaleindex ・ https://whalewisdomalpha.com/whaleindex-holds-best-ideas-of-leading-hedge-funds/index.html

### 克隆型 ETF 實盤成績單（最誠實的證據）【實務績效】
| ETF | 策略 | 成立 | 結局／績效 |
|---|---|---|---|
| GURU (Global X) | 對沖基金 top 持倉 | 2012/6 | 存活但落後：成立以來年化 **11.53%**（stockanalysis.com）vs 同期 S&P ~14%；AUM 萎縮到 $44.6M（2025/3）。早期（–2015/8）曾累贏 12.26pp，之後回吐轉負 |
| ALFA (AlphaClone) | 克隆＋對沖 | 2012 | **2022/8/31 清算**。近 10 年落後 -1.6%/yr、波動更高 |
| IBLN (iBillionaire) | 億萬富豪 top 持倉 | 2014/8 | **2018/4/6 清算**（資產不足） |
| ALFI (AlphaClone Intl) | 國際版克隆 | — | **2018/6 清算** |
| GVIP (Goldman) | 對沖基金 VIP（最常見 top-10 共識股 50 檔等權） | 2016/11 | 唯一贏家：成立以來年化 **17.65%**（stockanalysis.com，vs 同期 S&P ~15%）。但 tracking error 巨大：2021 +11.9% vs S&P +28.7%（落後 16.9pp）、2022 **-32.0% vs -18.1%**（多跌 13.8pp）；2023 +39.1%、2024 +29.8% 追回 |

來源：https://stockanalysis.com/etf/guru/ ・ https://stockanalysis.com/etf/gvip/ ・ https://www.prnewswire.com/news-releases/exchange-traded-concepts-to-close-and-liquidate-the-alphaclone-alternative-alpha-etf-301604138.html （2022）・ https://www.etfstrategy.com/insufficient-assets-prompts-direxion-to-close-its-billionaire-mimicking-etf-49409/ （2018）・ https://seekingalpha.com/article/4047913-etf-to-avoid-alphaclone-alternative-alpha-etf 。信心：高（GVIP 逐年數字為單一來源彙整，中）。

【推理】五支克隆 ETF：三支清算、一支苟活且落後、一支（GVIP）贏但靠的是「共識成長股傾斜」在 2023–24 AI 行情的 beta，2021–22 兩年合計落後 ~30pp——不是穩定 alpha，是高波動風格暴露。**機械式克隆的實盤總結：接近零或負。**

---

## 5. 散戶合理期望與紅線

### 合理期望（扣延遲與執行成本）
- **機械克隆全體/共識對沖基金持倉：0 至 -2%/yr**（GURU/ALFA 實盤；Klement 2021）。不要做。
- **篩選後的低週轉集中價值型（§2 畫像）克隆：0 至 +4%/yr**，中位期望 +1～2%/yr。依據：Angelini et al. +3.8%（2004–2019，篩選後）；Best Ideas +2.8–4.5%（共同基金、樣本偏舊）；Verbeek-Wang「約略打平本尊」；再扣近十年衰減與擁擠折價。**+10% 時代（Buffett 1976–2006）已不可複製。**
- 必要心理成本：單年落後大盤 10–17pp 是常態（GVIP 2021–22），集中組合的 tracking error 遠大於超額本身。

### 紅線（出現任一即不值得跟該機構）
1. 多空/量化/高週轉基金——13F 是半張牌桌，可能與真實曝險相反
2. 申報機構 AUM 巨大且持倉分散（>100 檔）——沒有 conviction 訊號
3. 連續兩季持倉重疊率 <50%——延遲成本吃光 alpha（半衰期 ~4 個月）
4. 該股在申報日已跳升 >5% 或已被大量媒體報導——擁擠折價已計入
5. 本尊自身近 5 年無超額（如現在的 Berkshire）——克隆上限＝本尊 alpha

### 對 KIWI 管線的判定
**值得建，但定位要對**：不是「自動跟單執行」，而是「**想法漏斗＋畫像篩選器**」——
- 數據零成本（SEC 官方結構化數據集）、季頻、工作量低，與鏈上「低頻慢錢」結論同構：13F 就是股票版的低頻慢錢訊號，且其可跟子集（低週轉集中價值型）與鏈上實證的「可跟畫像」一一對應。
- 管線產出＝候選股清單（多位畫像合格經理人的新建倉/加倉交集）→ 進 Serenity 框架做獨立基本面驗證，**永遠不直接下單**。
- 驗證設計：用 SEC 數據集回測「畫像篩選 vs 全體克隆」的分層報酬差，若分層無單調性即棄。

---

## 查無清單（明確找不到的）
- 13F 申報日跳升的正式學術 event-study 量化數字（只有個案與二手敘述）
- Pabrai「Shameless Portfolio」的可驗證實盤審計績效
- GVIP 與 S&P 500 自成立以來的同源精確年化對比（17.65% 為 stockanalysis.com 單方數字；S&P 同期 ~15% 為推算）
- Aiken et al. (2013) copycat 論文原文（僅見二手轉述「top 經理人克隆在 45 天延遲後仍有 alpha」，未能確認確切論文與數字）——信心：低

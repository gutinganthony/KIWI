# Form 4 內部人跟單訊號研究筆記

- 研究日期：2026-07-10
- 研究問題：跟隨美股內部人申報（SEC Form 4，交易後 2 個工作日內申報）對散戶是否有可驗證的超額報酬？哪種訊號最強？
- 方法限制：本次僅用 WebSearch（無法直接讀論文全文），效應數字以搜尋摘要與多來源交叉為準。每條標註【學術實證】/【實務】/【推理】＋信心層級（高/中/低）。

---

## TL;DR

內部人**買入**（不是賣出）有 40 年以上的學術實證超額報酬；最強訊號是「**非例行（opportunistic）內部人 + 集群買入 + 小市值 + 高管（尤其 CFO）**」的交集。學術毛超額約年化 6–10%，但 2002 後全市場異象普遍衰減，且 2025 年的可執行性研究顯示：按實際可成交量計算，「搶快跟單」的美元報酬趨近零甚至轉負——alpha 集中在低流動性小型股，只有小資金＋限價單＋持有 1–12 個月的「慢跟」模式能吃到。這與使用者鏈上調查的結論（只有慢錢可跟）同構。

---

## 1. 學術實證：核心文獻

### 1.1 Lakonishok & Lee (2001), *Review of Financial Studies* —【學術實證，信心：高】
- 樣本：NYSE/AMEX/Nasdaq 全部公司，1975–1995。
- **買賣不對稱**：預測力全部來自「買入」；內部人賣出對未來報酬**沒有**預測力（賣出動機多為流動性、分散、稅務、行權後出售）。
- 效應大小：
  - 內部人大量買入的公司，隨後 12 個月超額報酬約 **+4.8%**（全樣本）。
  - **小市值**公司中內部人買入的股票，12 個月超額約 **+7.4%**。
  - 賣出的股票沒有顯著落後。
- 其他發現：內部人整體是反向投資者（contrarian）；交易與申報當下市場幾乎沒有反應（＝資訊消化慢，跟單者有時間窗）。
- 來源：[RFS 原文摘要](https://academic.oup.com/rfs/article-abstract/14/1/79/1587398)、[LSV Asset 論文 PDF](https://www.lsvasset.com/pdf/research-papers/Insider-Trades-Informative.pdf)、[Quant Decoded 整理](https://quantdecoded.com/en/insider-trading-signals-informative-trades)

### 1.2 Jeng, Metrick & Zeckhauser (2003), *Review of Economics and Statistics* —【學術實證，信心：高】
- 樣本：1975–1996，用績效評估（calendar-time portfolio）法，避免事件研究法的偏誤。
- **內部人買入組合：年化超額 >6%**（風險調整後）；**賣出組合：無顯著超額**。
- 這是「買入有資訊、賣出沒有」最乾淨的證據之一。
- 來源：[MIT Press 原文](https://direct.mit.edu/rest/article/85/2/453/57400/Estimating-the-Returns-to-Insider-Trading-A)、[NBER w6913](https://www.nber.org/papers/w6913)、[2iQ 文獻回顧](https://www.2iqresearch.com/blog/profiting-from-insider-transactions-a-review-of-the-academic-research)

### 1.3 Cohen, Malloy & Pomorski (2012), "Decoding Inside Information", *Journal of Finance* —【學術實證，信心：高】★本題最重要的一篇
- 核心思想：把內部人交易分成 **routine（例行）** 與 **opportunistic（機會型）**。
  - **辨識法**：某內部人若連續 3 年以上都在「同一個日曆月」交易 → routine trader；其餘（有 3 年以上歷史但無固定月份模式）→ opportunistic trader。需要 ≥3 年交易史才能分類。
  - Routine 佔全部內部人交易**過半**，且**完全沒有**預測力。
- 效應大小：只跟 opportunistic 交易的組合——
  - 市值加權超額 **82 bps/月（≈ 年化 10%）**
  - 等權超額 **180 bps/月（≈ 年化 21.6%，實務不可達，見 §3.4）**
  - Routine 交易組合超額 ≈ 0。
- Opportunistic 交易能預測公司特定新聞、分析師預測修正與財報公告日報酬；routine 不能。
- 最有資訊的 opportunistic trader：**地方性、非最高階的內部人，來自地理集中、治理較差的公司**。
- 來源：[SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1692517)、[Journal of Finance](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01740.x)、[NBER w16454](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf)、[NBER Digest](https://www.nber.org/digest/apr11/decoding-inside-information)

### 1.4 買賣不對稱的機制 —【學術實證＋推理，信心：高】
- 三篇核心文獻一致：**賣出訊號雜訊極大**（薪酬股行權、分散、稅、買房），**買入是唯一動機單純的行為**——內部人只在認為股價低估時才掏自己的現金買。
- 例外（賣出偶爾有訊息）：Form 144/Form 4 申報時序倒置的策略性賣出（arXiv 2026 工作論文），及 10b5-1 計畫的策略性設計（見 §2.4）。這對「跟買不跟賣」的管線設計沒有影響。

---

## 2. 最強條件（訊號強度排序）

### 2.1 集群買入（cluster buys）—【學術實證，信心：高】
- Kang, Kim & Wang (2018), "Cluster Trading of Corporate Insiders"（樣本 1986–2016，美國）：
  - **21 個交易日**持有期：集群買入異常報酬 **3.8%** vs 非集群 **2.0%**（近 2 倍）。
  - 90 日視野差距擴大到 **+2.5%**。
  - 在同事買入後 2 日內跟進的內部人買入：次月異常報酬 **2.1%/月**，比單獨買入高 **0.9%**。
  - 集群多發生在資訊不對稱高的時期；高管與董事混合的集群比純高管集群更有資訊。
- 實務定義（OpenInsider 等）：7 天內 ≥2–3 名不同內部人公開市場買入，各筆超過最低金額門檻。
- 來源：[論文 PDF](https://opis-cdn.tinkoffjournal.ru/mercury/insider-pdf-002.pdf)、[2iQ Cluster Buying 指南](https://www.2iqresearch.com/blog/what-is-cluster-buying-and-why-is-it-such-a-powerful-insider-signal)

### 2.2 職位：CFO > CEO > 董事 —【學術實證，信心：高】
- Wang, Shin & Francis (2012), *JFQA*, "Are CFOs' Trades More Informative Than CEOs' Trades?"（1992–2002）：
  - **CFO 買入後 12 個月超額比 CEO 買入高約 5 個百分點**，控制風險因子後仍成立，且在公開申報後仍持續（跟單者吃得到）。
  - CFO 買入更能預測未來正向盈餘驚喜。
  - 後續研究（Emerald, 2016）支持「scrutiny hypothesis」：CEO 受監督/曝光更多所以不敢用資訊，不是 CFO 更懂財務。
- 注意與 §1.3 的張力：CMP 發現最有資訊的是「非最高階、地方性」內部人——兩者的共同點是**受監督越少的人越敢用資訊**。
- 來源：[JFQA](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/are-cfos-trades-more-informative-than-ceos-trades/B7DD71285F1326E694CC860193C87710)、[Emerald](https://www.emerald.com/insight/content/doi/10.1108/mf-02-2013-0035/full/html)

### 2.3 市值：小型股 >> 大型股 —【學術實證，信心：高】
- L&L (2001)：預測力幾乎全部由小型股驅動（小型股 7.4% vs 全樣本 4.8%）。
- arXiv 2026 微型股研究（$30M–$500M 市值，2018–2024，17,237 筆買入）：機器學習分類器樣本外 AUC 0.70；**申報前已漲 >10% 的買入反而 CAR 最高（6.3%）**——動能確認型買入比逢低攤平型買入強，違反直覺但重要。
- 來源：[arXiv 2602.06198](https://arxiv.org/abs/2602.06198)

### 2.4 10b5-1 計畫單 vs 自主單 —【學術實證＋實務，信心：高】
- Jagolinzer (2009), *Management Science*（>100,000 筆、3,000+ 高管、~1,250 公司）：10b5-1 **計畫內**的交易 6 個月打敗市場 >6%，同公司非計畫交易者只有 1.9%——證明計畫單也被策略性使用（提前知道壞消息才設計賣出計畫、選擇性終止計畫）。但這主要是**賣出端**的策略行為，對跟買管線的含義是：**計畫單≠無資訊，但自主買入單仍是最乾淨的訊號**。
- **2023 起可以直接區分**：SEC 2022-12-14 通過修訂（2023-02-27 生效），2023-04-01 起 Form 4/5 必須**勾選 checkbox** 標示交易是否依 10b5-1 計畫執行。→ 跟單管線直接過濾掉勾選的交易即可。
- 來源：[SEC 新聞稿](https://www.sec.gov/newsroom/press-releases/2022-222)、[SEC Fact Sheet](https://www.sec.gov/files/33-11138-fact-sheet.pdf)、[Jagolinzer SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=541502)

### 2.5 Opportunistic trader 辨識法（可程式化）—【學術實證，信心：高】
1. 對每個 insider 建 3 年以上交易史。
2. 連續 3 年同一日曆月交易 → 標記 routine，剔除。
3. 剩下的是 opportunistic；2023-04 後再疊加「非 10b5-1 checkbox」過濾。
4. 歷史不足 3 年者無法分類（CMP 原文將其排除；實務上可當「未知」降權）。

---

## 3. 衰減：效應還在嗎？

### 3.1 2002 後（SOX 兩日申報時代）—【學術實證，信心：中高】
- 多篇研究指出 2002 後股市異象普遍衰減；「難估值股票中內部人交易的超額」在 2002 後消失（與異象整體衰減同步）。
- SOX 把申報期限從「次月 10 日」縮到「2 個工作日」→ 資訊更快公開，理論上壓縮內部人 alpha、但**放大跟單者能吃到的比例**（訊號更新鮮）。
- 來源：[Insider Monkey 學術整理](https://www.insidermonkey.com/blog/the-insider-trading-anomaly-recent-academic-studies-591/)、[JBF 2020 異象消失研究](https://www.sciencedirect.com/science/article/abs/pii/S0378426620302284)

### 3.2 2015 後／2020 後 —【學術實證，信心：中】
- 2008–2024 複製研究（CMP 框架重跑）：**opportunistic 買入訊號仍然成立**，routine 仍無資訊，賣出端更弱。→ 訊號核心結構未死，但普遍認為幅度小於 1975–1995 黃金期。
- 英國 FTSE-350（2022, Frontiers）：買入異常報酬比早期文獻大幅縮水（早期文獻 +2.85% vs 新樣本不顯著甚至 −0.84%）——歐洲市場衰減比美國明顯。
- 沒有找到「美國內部人買入訊號 2020 後歸零」的明確證據；查無針對 2020–2025 美國大樣本的權威衰減估計（查無明說）。
- 來源：[FTSE-350 研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC8886886/)、[arXiv 微型股研究（2018–2024 樣本仍有效）](https://arxiv.org/abs/2602.06198)、[VerityData 2026 學術研究整理](https://verityplatform.com/wp-content/uploads/2026/04/VerityData-Insider-Academic-Studies.pdf)

### 3.3 2023 SEC 10b5-1 新規的影響 —【實務＋推理，信心：中】
- 新規內容：D&O 冷卻期 90–120 天、禁止重疊計畫、限制單筆交易計畫、good-faith 認證、Form 4 checkbox。
- **對跟單者是淨利多（推理）**：(a) checkbox 讓計畫單/自主單可機器區分——2023-04 之前的資料做不到；(b) 冷卻期壓縮了計畫單的策略性，殘留的自主單資訊純度更高。
- 尚無 2023 後 checkbox 資料的大樣本學術驗證（查無明說——規則太新）。

### 3.4 可執行性（最重要的衰減證據）—【學術實證，信心：高】
- **Finance Research Letters 2025, "Insider filings as trading signals — Does it pay to be fast?"**（後 SOX 樣本＋盤中數據）：
  - 快速反應申報公告有正的**百分比**異常報酬（但比早期文獻小）。
  - **把每筆訊號限制在「實際可成交的美元金額」後，超額歸零甚至轉負**；低成交量股票百分比報酬最高但美元報酬為負。
  - 報酬與流動性負相關 → 策略幾乎不可規模化，**連交易成本都還沒算**。
- 解讀：學術上的 82bps/月是「紙上組合」；真人下單時，alpha 藏在買不到量的小型股裡。散戶小資金反而比機構有優勢，但必須用限價單、接受部分成交、放棄「搶快」幻想。
- 來源：[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1544612324015435)

---

## 4. 實務工具與數據源

### 4.1 免費、可程式化 —【實務，信心：高】
- **SEC EDGAR 本體完全免費**：
  - Form 4 為結構化 XML，申報後近即時公開（EDGAR acceptance 後數秒–數分鐘）。
  - 官方限速：**10 requests/秒**（fair access policy，需帶 User-Agent），超速暫時封鎖 10 分鐘。
  - 有 daily/quarterly index、full-text search API、data.sec.gov JSON API、RSS/Atom feed。自建管線零數據成本。
  - 來源：[SEC Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)、[SEC Developer Resources](https://www.sec.gov/about/developer-resources)、[SEC rate control 公告](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits)
- **OpenInsider（openinsider.com）**：免費 Form 4 篩選器，有現成 [Latest Cluster Buys](http://openinsider.com/latest-cluster-buys) 頁（7 天內 ≥2 名內部人買入）。可爬表格，無官方 API。

### 4.2 付費 —【實務，信心：中】
- SecForm4.com：即時追蹤，付費層約 $50/月起。
- InsiderScore（VerityData）：機構級，$99–499/月，有 cluster buying 標記與研究支援。
- sec-api.io、2iQ、Apify scrapers 等：Form 4 解析 API，2003 至今 1,100 萬+ 筆交易。

### 4.3 實盤打包產品的紀錄（警訊）—【實務，信心：高】
- **Guggenheim/Invesco Insider Sentiment ETF（NFO）**：2006 年發行，追蹤 Sabrient 指數（混合內部人買入＋分析師上修，非純內部人訊號），成立以來曾以月均 ~50bps 領先市場，但 **2020-02 清算**（規模不足）。
- **Direxion All Cap Insider Sentiment（KNOW）**：**2020-10 清算**（吸不到資產）；2018 年度指數 +2.82% 而基金只有 +1.04%（實施成本吃掉大半）。
- 現存無知名的純內部人訊號 ETF（查無）。→ 打包成流動性產品後訊號活不下來，側面印證 §3.4：**alpha 在小型股，容量極小**。
- 來源：[etf.com 比較](https://www.etf.com/sections/news/2-insider-buying-etfs-very-different-returns)、[Direxion N-CSR](https://www.sec.gov/Archives/edgar/data/1424958/000110465919000390/a18-36871_1ncsr.htm)、[Seeking Alpha NFO 分析](https://seekingalpha.com/article/240442-gauging-guggenheim-insider-sentiment-etfs-performance)

---

## 5. 明確回答研究問題

### 5.1 散戶跟「內部人集群買入」的合理期望 —【推理（基於上述實證），信心：中】
- **紙面學術值**：opportunistic 買入 ~10%/年（VW）；集群買入 21 日 3.8%；小型股 12 個月 7.4%。
- **散戶實際合理期望**：小資金（每筆 ≤ 幾千美元）、限價單、集中小型股、持有 1–6 個月：**年化超額 3–6%（稅前、毛）**是務實區間；若只做大型股或用市價單搶快，期望應降到 ~0–2%。
- **紅線條件（不滿足就不進場）**：
  1. 只跟**買入**，永不跟賣出訊號反向操作。
  2. 只跟**自主單**（2023-04 後：Form 4 無 10b5-1 checkbox）。
  3. 優先 **≥2–3 名內部人 7 日內集群**；單人買入需 CFO/CEO＋金額佔其薪酬顯著比例才考慮。
  4. 剔除 routine trader（3 年同月規律）。
  5. 微型股用限價單、接受不成交；成交量低於自己單量 50 倍的不碰（§3.4 教訓）。
  6. 申報前已暴跌後的「護盤式買入」訊號弱；申報前已上漲 >10% 的動能確認買入反而更強（arXiv 2026）。
  7. 這是 1–12 個月的慢訊號，不是日內/週內訊號——搶快沒有超額（FRL 2025）。

### 5.2 與 13F 相比，2 天 vs 45 天換來什麼 —【學術實證＋推理，信心：中高】
- 13F：季後 45 天申報，看到時持倉已 45–135 天舊；機構新買入的 alpha 首月約 36bps、**半衰期約 4 個月**——45 天延遲直接燒掉約 1/3 以上的半衰期。
- Form 4：2 個工作日，近即時，且 L&L 證明申報當下市場反應很小、drift 持續 6–12 個月 → **跟單者能吃到訊號的大部分生命週期**，這是 Form 4 相對 13F 的結構性優勢。
- 但注意：Form 4 的優勢不是「快」本身（搶快無超額），而是「訊號生命週期幾乎完整保留」。
- 來源：[Arkolith 申報制度比較](https://arkolith.com/blog/13f-vs-13d-vs-13g-vs-form-4)、[Farouk & Jivraj 13F alpha 研究](https://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-090-Farouk-Jivraj.pdf)

### 5.3 判定
**值得建管線（有條件）**。訊號真實、文獻厚、數據免費、2023 checkbox 後純度更高；但期望值必須壓在年化 3–6% 超額、容量極小（只適合散戶規模）、且是 1–12 個月慢訊號。與鏈上跟單結論同構：**只有慢錢可跟，Form 4 的「慢錢」是內部人自掏現金的集群買入。**

---

## 附錄：關鍵數字速查表

| 訊號 | 效應 | 期間 | 來源 | 層級 |
|---|---|---|---|---|
| 內部人買入（全體） | +4.8%/12mo | 1975–1995 | Lakonishok & Lee 2001 | 學術 |
| 小型股內部人買入 | +7.4%/12mo | 1975–1995 | Lakonishok & Lee 2001 | 學術 |
| 買入組合（風調後） | >+6%/年 | 1975–1996 | Jeng-Metrick-Zeckhauser 2003 | 學術 |
| 賣出訊號 | ≈0 | 各期 | 三篇一致 | 學術 |
| Opportunistic 買入 | +82bps/月 VW（≈10%/年） | 1986–2007 | Cohen-Malloy-Pomorski 2012 | 學術 |
| Routine 交易 | ≈0（佔全體 >50%） | 同上 | 同上 | 學術 |
| 集群 vs 非集群買入 | 3.8% vs 2.0%（21 交易日） | 1986–2016 | Kang-Kim-Wang 2018 | 學術 |
| CFO vs CEO 買入 | CFO 高 ~5%/12mo | 1992–2002 | Wang-Shin-Francis 2012 JFQA | 學術 |
| 10b5-1 計畫單（賣出端策略性） | 6mo 打敗市場 >6% | ~2001–2006 | Jagolinzer 2009 | 學術 |
| 快速跟單的美元報酬 | ≈0 或轉負（限可成交量後） | 後 SOX | FRL 2025 | 學術 |
| 機構 13F 新倉 alpha 半衰期 | ~4 個月（首月 36bps） | — | Lancaster 13F 研究 | 學術 |
| 內部人 ETF 實盤 | NFO/KNOW 均已清算（2020） | 2006–2020 | etf.com / SEC | 實務 |
| EDGAR 成本 | 免費，10 req/s | 現行 | SEC.gov | 實務 |

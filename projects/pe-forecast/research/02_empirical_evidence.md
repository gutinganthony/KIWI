# 個股本益比的實證決定因素、可預測性，與「預估 EPS × 倍數」的準確度
## 文獻調查長版報告（查詢日期：2026-10-01）

---

## 0. 方法、限制與標記規則（先讀）

**取得方式的限制（重要）**：本次 session 的 WebFetch 被網路 egress proxy 全面封鎖（實測 link.springer.com、nber.org、papers.ssrn.com、onlinelibrary.wiley.com、jstor.org、business.columbia.edu、anderson.ucla.edu、arxiv.org、api.semanticscholar.org、citeseerx、econpapers 等皆回 `EGRESS_BLOCKED`）。因此**沒有任何一篇是逐字讀到全文或表格**；所有內容都來自 WebSearch 對原始出版頁（期刊頁、SSRN、NBER、作者網頁、CFA Institute 頁）所擷取的摘要文字。依任務規則，這屬於「打不開原文時用摘要或可信二手來源」，以下逐條標可信度：

| 標記 | 意義 |
|---|---|
| **[A]** | 搜尋結果引述的是原文摘要/出版頁文字，且多次搜尋一致 |
| **[B]** | 來自二手轉述（他篇論文、論文集、評論文章、學位論文）或單一搜尋摘要 |
| **[C]** | 不同搜尋給出彼此矛盾的數字，或無法確認 → 不應直接引用 |
| **事實／推論／不確定** | 「事實」= 文獻寫了什麼；「推論」= 我根據文獻推出的含意；「不確定」= 證據互相衝突或查無 |

所有網址的查詢日期一律為 **2026-10-01**。

---

## 1. 直接回答三個問題（摘要）

### (a) 實證上決定個股本益比的主要因素與相對重要性

| 排名（推論） | 因素 | 證據強度 | 關鍵證據 |
|---|---|---|---|
| 1 | **市場「預期」的盈餘成長（分析師長期成長預估），而非已實現成長** | 強 | Zarowin 1990：預估長期 EPS 成長是 E/P 橫斷面差異與持續性的「主導」決定因素，beta、短期成長、會計方法相對不重要 [A]。Delao-Han-Myers（RFS 待刊）：預期 1 年 EPS 成長約可解釋 P/E 離散度的 33%、4 年約 43%；**實際實現的成長只解釋約 8%** [B/C，版本間數字不同] |
| 2 | **未來報酬（折現率＋錯誤定價的修正）** | 強但有爭議 | Delao-Han-Myers 2025 JFE（1963–2020 全美股）：**約 75% 的橫斷面 P/E 離散度反映在之後的報酬差異，只有約 25% 反映在之後的盈餘成長差異** [B] |
| 3 | **盈餘的暫時性成分（分母雜訊／Molodovsky 效應）** | 強 | Beaver & Morse 1978：形成年 P/E 與當年盈餘成長負相關、與次年正相關 → 市場只把短暫扭曲當暫時 [A]；Ou & Penman 1989、Penman 1996 [A] |
| 4 | **產業** | 強（用於倍數估值） | Alford 1992：用 3 位數 SIC 產業選同業 ≈ 最佳 [B]；Liu-Nissim-Thomas 2002 [A]；Bhojraj-Lee 2002 [A] |
| 5 | **獲利能力（ROE）的「變化」** | 中 | Fairfield 1994：P/E 是預期獲利能力「變化」的函數，P/B 是「水準」的函數 [A]；Penman 1996：P/E 與未來 ROE 正相關、與當期 ROE 負相關 [A] |
| 6 | **會計方法** | 中（解釋長期持續差異） | Beaver & Morse 1978：P/E 差異持續的最可能解釋是會計方法，而非成長或風險 [A] |
| 7 | **系統風險（beta）** | 弱 | Beaver & Morse：市場風險在 2–3 年以上幾乎無法解釋 P/E 持續性 [A]；Zarowin：beta 相對不重要 [A] |

**推論**：「預期成長」決定了今天的 P/E 水準，但預期成長本身偏樂觀且幾乎不持續（Chan-Karceski-Lakonishok 2003 [A]；La Porta 1996 [A]），所以高 P/E 的一大部分最後以「低報酬／P/E 壓縮」而非「高成長」兌現——這正是第 1 和第 2 名同時成立的原因。

### (b) 個股本益比／股價變動中，盈餘消息 vs 折現率消息的比重

- **個股層級（時間序列報酬變異）**：Vuolteenaho 2002——典型個股**現金流（盈餘）消息的變異數是預期報酬消息的兩倍以上** [A]。推論：忽略共變異數時，現金流消息約佔 ≥2/3，折現率消息約佔 ≤1/3。**預期報酬消息在個股間高度相關（＝大盤層級的共同因子），現金流消息在投資組合中大多可分散掉** [A]。
- **用分析師預估直接量測**：Chen-Da-Zhao 2013——現金流消息的重要性隨期限增加；**期限超過 2 年時，現金流消息遠大於折現率消息**；個股與大盤都成立 [A]。1 年期限的確切比例：**查無**。
- **大盤層級（對照組）**：Campbell 1991——現金流消息只佔非預期報酬變異的 1/3 到 1/2 [A/B]；Cochrane 2011——「幾乎所有」股價/股利比變動對應折現率變動 [A]。**反面**：De la O & Myers 2021 用調查預期，發現現金流成長預期至少解釋 S&P 500 P/D 的 93%、P/E 的 63%（依摘要措辭 "respectively" 的順序）[A/B]。
- **橫斷面「水準」（不是變動）**：結論相互矛盾——Cohen-Polk-Vuolteenaho 2003：B/M 的橫斷面變異中**預期 15 年報酬只佔 20–25%**，其餘是獲利能力與估值持續性 [A]；Delao-Han-Myers 2025：**P/E 離散度約 75% 反映在未來報酬** [B]。見 §6。

### (c) 「預估盈餘 × 倍數」或 12 個月目標價的已知準確度

| 情境 | 準確度 | 來源 |
|---|---|---|
| 同期（不是預測）用產業 forward P/E 對今天的股價定價 | **約一半樣本誤差在 ±15% 內**（1982–1999，19,879 公司年） | Liu-Nissim-Thomas 2002 [A] |
| 同期用產業 trailing P/E | 中位數絕對誤差約 **24–25%**（1978/1982/1986，4,698 家） | Alford 1992 [B] |
| 12 個月目標價（美國 2000–2009） | **平均絕對誤差 45%**；期末達標 **38%**；期間內曾觸及 **64%**；目標價隱含報酬平均比實際**高 15 個百分點** | Bradshaw-Brown-Huang 2013 [A] |
| 12 個月目標價（16 國 2002–2009） | 平均絕對誤差 **44.7%**（日本 37.3% 到丹麥 58.2%） | Bilinski-Lyssimachou-Walker 2013（工作論文版）[B] |
| 12 個月目標價（美國明星分析師 1997–1999） | **略高於一半**達標（二手記為 54%／54.3%）；未達標者平均只到目標價的 **84%** | Asquith-Mikhail-Au 2005 [A/B] |
| 12 個月目標價（義大利 2000–2006） | 達標率約 **33%**；誤差持續、自我相關、不均值回歸 | Bonini et al. 2010 [A/B] |
| 目標價的「同產業相對排序」 | 有顯著的超額報酬價值；**絕對水準資訊量低**；全市場排序無顯著 alpha | Da & Schaumburg 2011 [A/B] |

**推論**：同期倍數估值（已知今天價格與同業倍數）的誤差下限約 ±15%（半數樣本），而 12 個月後的預測要再加上「未來 12 個月的 P/E 變動」與「EPS 預估誤差」，實證上專業分析師的平均絕對誤差約 45%。任何新模型都應把這兩個數字當作「下限」與「要打敗的基準」。

---

## 2. 本益比的決定因素：逐篇

### 2.1 Beaver & Morse (1978), "What Determines Price-Earnings Ratios?"
- 期刊：Financial Analysts Journal 34(4): 65–76，1978 年 7/8 月 [A]
- 樣本：依 P/E 分組成投資組合後長期追蹤；**確切樣本期間與公司數：查無**（原文 PDF 打不開）。
- 主要發現 [A]：
  1. 各 P/E 投資組合的初始 P/E 差異**持續長達 14 年**。
  2. **成長幾乎無法解釋**持續的 P/E 差異。
  3. **市場風險在超過 2–3 年後幾乎無法解釋** P/E 持續性。
  4. 持續性最可能的解釋是**會計方法差異**，而不是成長或風險。
  5. P/E 與**形成年**盈餘成長**負**相關、與**次年**盈餘成長**正**相關 → 投資人只把短暫的盈餘扭曲當成暫時性（＝暫時性盈餘／均值回歸的直接證據）。
- 來源：https://rpc.cfainstitute.org/research/financial-analysts-journal/1978/what-determines-price-earnings-ratios （2026-10-01）

### 2.2 Zarowin (1990), "What Determines Earnings-Price Ratios: Revisited"
- 期刊：Journal of Accounting, Auditing & Finance 5(3): 439–457 [A]
- 樣本：使用「先前研究者沒有的預期資料庫」（分析師預估）；**確切期間：查無**。
- 主要發現 [A]：
  - **預估長期 EPS 成長**是 E/P 橫斷面差異與時間序列持續性的**主導**決定因素。
  - 先前研究（含 Beaver & Morse）的結論來自用「已實現成長」代理「預估成長」，而兩者**相關性不高**。
  - 風險（beta）、預估短期成長、會計方法**相對不重要**。
- 來源：https://journals.sagepub.com/doi/abs/10.1177/0148-558X1989005003007 （2026-10-01）

### 2.3 Molodovsky 效應
- 原文：Nicholas Molodovsky (1953), "A Theory of Price-Earnings Ratios," Financial Analysts Journal 9(5): 65–80（1995 年 FAJ 51(1) 重刊）[A]。原文摘要強調「資本化的獲利能力（earning power）才是價值的操作性表達」，並推導當期盈餘、獲利能力與 P/E 的關係。
- 「Molodovsky 效應」這個名稱與「景氣谷底 EPS 低 → P/E 高；景氣高峰 EPS 高 → P/E 低」的描述，主要見於 CFA 課程與教學資料 [B，二手]。
- **個股層級量化研究「以 Molodovsky 效應為名」：查無**。其實證對應物是 Beaver & Morse 的形成年/次年成長模式，以及 Ou & Penman 1989、Penman 1996 的「P/E 校正暫時性盈餘」結果。
- 來源：https://www.tandfonline.com/doi/abs/10.2469/faj.v9.n5.65 ；https://rpc.cfainstitute.org/research/financial-analysts-journal/1995/a-theory-of-priceearnings-ratios ；（二手）https://breakingdownfinance.com/finance-topics/finance-basics/molodovsky-effect/ （皆 2026-10-01）

### 2.4 Fuller, Huberts & Levinson (1993)
- 題目："Returns to E/P Strategies, Higgledy-Piggledy Growth, Analysts' Forecast Errors, and Omitted Risk Factors"，Journal of Portfolio Management 19(2): 13–24，1993 冬季號 [A]
- 主要發現 [B]：把 E/P 當市場對未來盈餘變動的隱含預測；**高 E/P（低 P/E）股票之後盈餘成長較低，低 E/P（高 P/E）股票之後成長較高**，反駁「盈餘成長是隨機的（higgledy-piggledy）」說法。論文同時檢驗低 P/E 的超額報酬能否被風險因子與分析師預估誤差解釋。
- **E/P 五分位的具體成長差距與報酬數字：查無**。
- 來源：https://jpm.pm-research.com/content/19/2/13 ；（二手）https://files.core.ac.uk/download/pdf/268103798.pdf （2026-10-01）

### 2.5 Chan, Karceski & Lakonishok (2003), "The Level and Persistence of Growth Rates"
- 期刊：Journal of Finance 58(2): 643–684 [A]
- 主要發現 [A]：
  - 長期盈餘成長的**持續性不超過隨機機率**；即使用大量預測變數，**可預測性也很低**。
  - **I/B/E/S 長期成長預估過度樂觀，預測力很低**。
  - **估值比率預測未來成長的能力也有限**。
  - 假設高成長能長期持續的估值「基礎不穩」。
- 來源：https://ideas.repec.org/a/bla/jfinan/v58y2003i2p643-684.html ；https://www.nber.org/papers/w8282 ；https://www.lsvasset.com/pdf/research-papers/Level+Persistence_of_Growth_Rates_FINAL.pdf （2026-10-01）

### 2.6 補充：與決定因素直接相關的其他研究
- **Fairfield (1994)**, "P/E, P/B and the Present Value of Future Dividends," FAJ 50(4): 23–31 [A]：P/E 是**預期獲利能力變化**的函數，P/B 是**預期獲利能力水準**的函數；不同 P/E–P/B 組合對應不同的未來獲利路徑，實證支持模型。https://rpc.cfainstitute.org/research/financial-analysts-journal/1994/pe-pb-and-the-present-value-of-future-dividends
- **Penman (1996)**, "The Articulation of Price-Earnings Ratios and Market-to-Book Ratios and the Evaluation of Growth," Journal of Accounting Research 34: 235–259 [A]：P/E 與**預期未來 ROE 正相關、與當期 ROE 負相關**；P/B 只反映預期未來 ROE；約 **34%** 樣本的 P/E 與 P/B 排序方向相反；**當期 ROE 不是 P/E 的好指標**（極端值除外）。https://business.columbia.edu/faculty/research/articulation-price-earnings-ratios-and-market-book-ratios-and-evaluation-growth
- **Ou & Penman (1989)**, JAR 27: 111–144 [A/B]：P/E 能預測未來盈餘（低 P/E → 低未來成長），因為它把會重複的盈餘與暫時性盈餘分開。https://ideas.repec.org/a/bla/joares/v27y1989ip111-144.html
- **Penman & Reggiani (2013)**, RAST 18: 1021–1049 [A/B]：E/P 與 B/P 合起來可以辨認「有風險的預期成長」；這種成長伴隨較高平均報酬 → P/E 同時包含成長與風險資訊。https://link.springer.com/article/10.1007/s11142-013-9226-y
- **Delao, Han & Myers**, "The Cross-section of Subjective Expectations: Understanding Prices and Anomalies"（RFS 待刊；2024 EFA 最佳論文）[A 摘要／C 數字]：用專業預估分解 P/E 水準的橫斷面差異；**高 P/E 同時來自低預期報酬與「過高」的預期盈餘成長**；盈餘意外是逐步（而非一次）反映在報酬中。各版本數字不一：預期 1 年成長約 33.1%、4 年約 43.3%（某版本）；另一版 51% vs 實現 5 年成長 8.1%；另一來源 35.8% vs 7.8% → **方向一致（預期成長 ≫ 實現成長），但確切比例不確定**。https://faculty.wharton.upenn.edu/wp-content/uploads/2025/09/cross-section-subjective-expectations.pdf ；https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4279862
- **Collins & Kothari (1989)**, JAE 11(2–3): 143–181 [A/B]：盈餘反應係數（ERC，可視為「盈餘消息的邊際 P/E」）隨成長、風險、持續性而變。具體符號與係數：**查無原文確認**。https://ideas.repec.org/a/eee/jaecon/v11y1989i2-3p143-181.html

---

## 3. 盈餘消息 vs 折現率消息

### 3.1 大盤層級
- **Campbell & Shiller (1988a)**, "The Dividend-Price Ratio and Expectations of Future Dividends and Discount Factors," RFS 1(3): 195–228 [A]：對數 D/P 可以線性寫成預期未來折現率與股利成長；以 VAR 檢驗兩者的相對重要性。https://academic.oup.com/rfs/article-abstract/1/3/195/1580239
- **Campbell & Shiller (1988b)**, "Stock Prices, Earnings, and Expected Dividends," JF 43(3) [A]：美國 1871–1986；長期移動平均盈餘有助預測未來股利現值；VAR 預估的股利現值約是「移動平均盈餘」與「當前價格」的加權，**盈餘權重 2/3 到 3/4**。https://campbell.scholars.harvard.edu/publications/stock-prices-earnings-and-expected-dividends
- **Campbell & Shiller (1998)**, "Valuation Ratios and the Long-Run Stock Market Outlook," JPM 24(2): 11–26 [A/B]：P/E 高時，之後 10 年報酬持續偏低。2001 年更新版：估值比率**預測股利成長、盈餘成長、生產力成長都很差**，主要預測的是**未來股價變動**。https://www.nber.org/papers/w8221 ；https://www.pm-research.com/content/iijpormgmt/24/2/11
- **Campbell (1991)**, "A Variance Decomposition for Stock Returns," Economic Journal 101(405): 157–179 [A/B]：NYSE 市值加權 1927–1988；**現金流消息只佔非預期報酬變異的 1/3 到 1/2**；預期報酬上升 1% 約伴隨 4–5% 資本損失。https://academic.oup.com/ej/article-abstract/101/405/157/5188371 ；https://www.nber.org/papers/w3246
- **Cochrane (2008)**, "The Dog That Did Not Bark: A Defense of Return Predictability," RFS 21(4): 1533–1575 [A]：若報酬不可預測，股利成長就必須可預測；**股利成長「不可預測」本身就是更強的證據**——在虛無假設下股利成長不可預測的機率只有 1–2%。https://www.johnhcochrane.com/research-all/the-dog-that-did-not-bark-a-defense-of-return-predictability ；https://faculty.washington.edu/ezivot/econ589/CochraneRFS2008.pdf
- **Cochrane (2011)**, "Presidential Address: Discount Rates," JF 66(4): 1047–1108 [A]：「現在看來**所有**價格/股利變動都對應折現率變動」。https://ideas.repec.org/a/bla/jfinan/v66y2011i4p1047-1108.html

### 3.2 個股層級（本題關鍵）
- **Vuolteenaho (2002)**, "What Drives Firm-Level Stock Returns?" JF 57(1): 233–264 [A]
  - 方法：個股 VAR（對數報酬、對數 B/M、對數獲利能力）分解成現金流消息與預期報酬消息。
  - 結果：(1) 個股報酬**主要由現金流消息驅動**，典型個股**現金流消息變異數 > 2 × 預期報酬消息變異數**；(2) 預期報酬消息**在公司間高度相關**，現金流消息在投資組合中**大多可分散**；(3) 小型股的預期報酬衝擊與現金流衝擊**正相關**。
  - **樣本期間與公司年數：查無確認**。
  - **推論**：忽略共變異數時，現金流消息約 ≥2/3、折現率消息約 ≤1/3；而且這 ≤1/3 大部分是「大盤共同的」倍數變動。
  - 來源：https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00421 ；https://dx.doi.org/10.2139/ssrn.190812 （2026-10-01）
- **Callen & Segal (2004)**, JAR 42(3): 527–560 [A/B]：把 Vuolteenaho 架構擴充成應計／現金流／預期報酬三部分；**應計消息與營業利益消息顯著主導預期報酬消息**。https://wrap.warwick.ac.uk/id/eprint/125013/
- **Chen, Da & Zhao (2013)**, "What Drives Stock Price Movements?" RFS 26(4): 841–876 [A]：用分析師盈餘預估反推公司別折現率，**不靠報酬可預測性**直接量測；現金流消息的重要性隨投資期限增加，**超過 2 年時遠大於折現率消息**；**個股與大盤都成立**，分散化只扮演次要角色。https://academicweb.nd.edu/~zda/CDZ.pdf
- **Lochstoer & Tetlock (2020)**, "What Drives Anomaly Returns?" JF 75(3): 1417–1455 [A]：大盤報酬以折現率消息為主，但**異常報酬投資組合（含價值類）由系統性現金流消息驅動**。https://business.columbia.edu/sites/default/files-efs/citation_file_upload/Lochstoer%20Tetlock%2020%20JF%20-%20What%20Drives%20Anomaly%20Returns.pdf

### 3.3 橫斷面「水準」的分解（P/E 為何高低不同）
- **Cohen, Polk & Vuolteenaho (2003)**, "The Value Spread," JF 58(2): 609–641 [A]：B/M 的橫斷面變異中，**預期 15 年報酬只佔 20–25%**，其餘由預期 15 年獲利能力與估值持續性解釋；這個比例在各時期、各國穩定。https://ideas.repec.org/a/bla/jfinan/v58y2003i2p609-641.html
- **Cohen, Polk & Vuolteenaho (2009)**, "The Price Is (Almost) Right," JF 64(6): 2739–2782 [A]：讓折現率隨現金流 beta 變動時，P/B 橫斷面變異中**錯誤定價的變異份額可忽略**。https://ideas.repec.org/a/bla/jfinan/v64y2009i6p2739-2782.html
- **Keloharju, Linnainmaa & Nyberg (2021)**, "Long-Term Discount Rates Do Not Vary Across Firms," JFE 141(3): 946–967 [A]：**長期預期報酬在個股間幾乎沒有差異**；長期反轉來自預期報酬快速收斂。https://www.nber.org/papers/w25579
- **Delao, Han & Myers (2025)**, "The Return of Return Dominance: Decomposing the Cross-Section of Prices," JFE 169: 104059 [B]：1963–2020 全部 NYSE/AMEX/NASDAQ 普通股；**約 75% 的 P/E 離散度反映在未來報酬差異，25% 反映在未來盈餘成長差異**；估值比率主要預測報酬、只溫和預測盈餘成長；長期限下缺乏盈餘成長差異。https://www.sciencedirect.com/science/article/pii/S0304405X25000674 ；（二手）https://www.morningstar.com/markets/price-primarily-predicts-future-returns-not-future-earnings-growth

### 3.4 對「個股 12 個月 P/E 預測」的含意（推論）
1. 個股股價變動主要是現金流消息（≥2/3），但這裡的「現金流消息」是**對所有未來現金流的預期修正**，不只是未來 12–24 個月 EPS。即使使用者給的 12–24 個月 EPS 完全正確，第 12 個月的 P/E 仍取決於對 24 個月以後成長的重新評估——而依 Chan et al. 2003，長期成長幾乎不可預測。→ **P/E 殘差有一大塊本質上是不可預測的「新聞」**。
2. 折現率消息在個股間高度共同 → 個股 P/E 變動中「折現率」那塊大致可以用「大盤/產業倍數的變動」來代理；預測個股 P/E 時，大盤倍數的不確定性是共同、不可分散的誤差項。
3. 橫斷面上，高 P/E 相對同業傾向「以低報酬方式」修正（Delao-Han-Myers 2025；Basu 1977；LSV 1994；La Porta 1996）→ 模型應該讓「相對同業／相對自身歷史偏高的 P/E」向下收斂，但收斂速度慢（Beaver & Morse：差異可持續 14 年）。

---

## 4. 用倍數估值的準確度

- **Alford (1992)**, "The Effect of the Set of Comparable Firms on the Accuracy of the Price-Earnings Valuation Method," JAR 30: 94–108 [A 題目／B 數字]
  - 樣本：1978、1982、1986 年共 **4,698 家**；比較 7 種同業選法（產業、資產規模、ROE 及組合）[B]。
  - 結果：**中位數百分比誤差 23.9%–25.3%** [B]；產業定義從 2 位數 SIC 縮到 3 位數時誤差下降，4 位數**沒有進一步改善** [B]；以 3 位數 SIC 全體產業同業的效果不輸考慮槓桿、ROE、資產的方法 [B]；**大公司估值較準** [B]。
  - 來源：https://www.semanticscholar.org/paper/THE-EFFECT-OF-THE-SET-OF-COMPARABLE-FIRMS-ON-THE-OF-Alford/fbe35e65a67882ce572ae631443f7ee53d2ad372 ；（二手）https://professional.sauder.ubc.ca/re_creditprogram/course_resources/courses/content/452/lie-multiples.pdf ；https://lup.lub.lu.se/luur/download?fileOId=8877532&func=downloadFile&recordOId=8877531
  - 不確定：有一個搜尋摘要說「分析師長期成長預估是對準確度貢獻最大的基本面」——**無法確認是否出自 Alford，不採用** [C]。
- **Liu, Nissim & Thomas (2002)**, "Equity Valuation Using Multiples," JAR 40(1): 135–172 [A]
  - 樣本：美國 **19,879 公司年，1982–1999** [A/B]。
  - 衡量：價格標準化的定價誤差分布的四分位距（IQR）；倍數用產業同業的**調和平均**（harmonic mean 較好）[A/B]。
  - 結果 [A]：**forward 盈餘倍數最準，約一半樣本的定價誤差在 ±15% 以內**；排名：forward 盈餘 > 歷史盈餘 > 現金流 ≈ 帳面價值 > 營收（最差）；**幾乎所有產業排名一致**（反駁「不同產業有不同最佳倍數」的說法）；允許截距對表現差的倍數有改善。
  - **各倍數 IQR 的確切數字：查無**（只有一筆搜尋摘要提到 EPS2 的數值「0.290」，無法確認它是哪個統計量 → [C]）。
  - 重要限制（推論）：這是**同期**定價（用今天的同業倍數解釋今天的價格），不是預測 12 個月後的價格 → 對前瞻預測來說是**誤差下限**。
  - 來源：https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00042 ；https://papers.ssrn.com/sol3/papers.cfm?abstract_id=241266 （2026-10-01）
- **Liu, Nissim & Thomas (2007)**, "Is Cash Flow King in Valuations?" FAJ 63(2): 56–65 [A]：檢查 (1) 用預估而非實際數字、(2) 股利而非營業現金流、(3) 個別產業、(4) 非美國市場——**所有情況下盈餘都勝過營業現金流與股利**。https://rpc.cfainstitute.org/research/financial-analysts-journal/2007/is-cash-flow-king-in-valuations ；http://www.columbia.edu/~dn75/Doron%20Nissim%20-%20is%20cash%20flow%20%20%20%20%20Thomas%20et%20al%20X.pdf
  - 註：任務提到的「LNT 2007」若指另一篇國際倍數論文，**查無**；此處採 FAJ 2007。
- **Bhojraj & Lee (2002)**, "Who Is My Peer? A Valuation-Based Approach to the Selection of Comparable Firms," JAR 40(2): 407–439 [A]
  - 方法：把 EV/Sales 與 P/B 對 **8 個成長、獲利、風險代理變數**做橫斷面迴歸，得到每家公司的「**應有倍數**（warranted multiple）」，再挑應有倍數最接近的公司當同業 [A/B]。
  - 測試：預測**未來 1 到 3 年**的 EV/S 與 P/B [A]。
  - 結果：**大幅優於產業與規模配對** [A]；調整後 R² 通常是只用產業＋規模配對的**兩倍以上** [B]。具體數字兩個二手摘要不一致（「1 年後 P/B：產業變數 13% → 加同業 25%」 vs「模型解釋 1 年後 54.0%、3 年後 52%」）→ **[C]，不引用具體數字**。
  - 來源：https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00054 ；https://www.researchgate.net/publication/227672139_Who_Is_My_Peer_A_Valuation-Based_Approach_to_the_Selection_of_Comparable_Firms
- **其他倍數準確度證據**：
  - **Kaplan & Ruback (1995)**, JF 50(4): 1059–1093 [A/B]：51 件高槓桿交易 1983–1989；DCF 平均在交易價的 10% 以內；**DCF 與 EBITDA 倍數約一半估計值落在 ±15% 以內**。https://www.ssrn.com/abstract=6609
  - **Kim & Ritter (1999)**, "Valuing IPOs," JFE 53: 409–437 [A/B]：同業 P/E、P/B、P/S 未經調整時對 IPO 的**預測力只算普通**；**forward P/E 優於其他倍數**，用次年 EPS 預估優於當年 EPS。https://ideas.repec.org/a/eee/jfinec/v53y1999i3p409-437.html
  - **Lie & Lie (2002)**, FAJ 58(2) [A/B]：資產倍數（市值/資產帳面價值）通常比營收與盈餘倍數更精確、偏誤更小（**部分反面**）；用預估盈餘取代歷史盈餘可改善估計；準確度隨公司規模、獲利能力、無形資產比重大幅變化。https://www.biz.uiowa.edu/faculty/elie/valbymult.pdf
  - **Geertsema & Lu (2023)**, "Relative Valuation with Machine Learning," JAR 61(1): 329–376 [A]：樣本外 ML 估值**大幅優於傳統倍數法**且跨時間、跨公司類型穩定；被高估的股票下個月跌、被低估的漲；最重要的價值驅動因子是**獲利比率、成長指標、效率比率**。https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.12464

---

## 5. 12 個月目標價的準確度

- **Bradshaw, Brown & Huang (2013)**, "Do Sell-Side Analysts Exhibit Differential Target Price Forecasting Ability?" RAST 18(4): 930–955 [A]
  - 樣本：**2000–2009 年**的 12 個月目標價（**筆數：查無**）。
  - 結果：目標價隱含報酬**平均比實際報酬高 15%**；**絕對誤差平均 45%**；**期末達標只有 38%**，但 **64% 在期間內某個時點達到過**；分析師間有統計顯著但經濟上很弱的持續能力差異；市場對「過去較準的分析師」的目標價調整**沒有差別反應**。
  - 來源：https://link.springer.com/article/10.1007/s11142-012-9216-5 ；https://www.ssrn.com/abstract=2535100 ；http://assets.csom.umn.edu/assets/37727.pdf （2026-10-01）
- **Asquith, Mikhail & Au (2005)**, "Information Content of Equity Analyst Reports," JFE 75(2): 245–282 [A]
  - 樣本：Institutional Investor 全美明星分析師（All-American）1997–1999 年的報告。
  - 結果：目標價**略高於一半的時間**達成（二手記為約 54%／54.3% [B]）；**沒達標時，期間內最高（或最低）價格平均只到目標價的 84%**；分析師越樂觀（預測漲幅越大）達標機率越低 [B]。
  - 來源：https://www.nber.org/papers/w9246 ；https://www.nber.org/digest/apr03/information-equity-analyst-reports ；https://papers.ssrn.com/sol3/papers.cfm?abstract_id=336362
- **Bonini, Zanetti, Bianchini & Salvi (2010)**, "Target Price Accuracy in Equity Research," JBFA 37(9–10): 1177–1217 [A]
  - 樣本：**2000–2006 年 47 家研究機構對米蘭交易所 98 家公司的 17,397 份報告**（約佔市值 82%）[B]。
  - 結果 [A]：預測準確度**非常有限**；誤差**持續、自我相關、不均值回歸**且大（摘要寫「up to 36.6%」；另一摘要寫「up to 46%」→ [C]）；**預測漲幅越大、公司越大、虧損公司誤差越大**；研究密度與市場動能對準確度有負面影響。達標率約 **33.1%** [B]。
  - 來源：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=676327 ；https://onlinelibrary.wiley.com/doi/10.1111/j.1468-5957.2010.02209.x
- **Bilinski, Lyssimachou & Walker (2013)**, "Target Price Accuracy: International Evidence," The Accounting Review 88(3): 825–851 [A 題目／B 數字]：16 國、2002–2009；**平均絕對誤差 44.7%（日本 37.3% 到丹麥 58.2%）**（出自 2012 年工作論文版）；國家間差異可由揭露品質、法源、文化、IFRS 解釋；過去較準、經驗較多、國家專精、大券商的分析師較準。https://eprints.lancs.ac.uk/id/eprint/71029/1/Analyst_TP_accuracy_Feb2012.pdf
- **Brav & Lehavy (2003)**, JF 58: 1933–1967 [A/B]：1997–1999；**12 個月目標價平均比當前價格高 28%**。https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00593
- **Da & Schaumburg (2011)**, "Relative Valuation and Analyst Target Price Forecasts," Journal of Financial Markets 14: 161–192 [A/B]：1997–2004；**同產業內**目標價隱含的相對估值有價值、超額報酬顯著；**絕對估值本身資訊量低得多**；全市場排序**沒有顯著 alpha**。https://academicweb.nd.edu/~zda/TargetPrice.pdf
- **方法選擇與準確度**：
  - **Demirakos, Strong & Walker (2010)**, European Accounting Review 19(1): 35–72 [A/B]：94 家英國公司 490 份報告（2002/7–2004/6）；依某些指標 PE 勝 DCF，依其他指標無差異；控制估值難度後 DCF 改善，依 miss_err 勝過 PE。https://ideas.repec.org/a/taf/euract/v19y2010i1p35-72.html
  - **Gleason, Johnson & Li (2013)**, CAR 30: 80–115 [B]：分析師採用較嚴謹的基本面估值（類剩餘所得模型）時，目標價表現**顯著優於**用簡單啟發式（如 PEG）。https://www.semanticscholar.org/paper/Valuation-Model-Use-and-the-Price-Target-of-Equity-Gleason-Johnson/23568c0ae1e54a607068acb9002914f228d45b53
- **EPS 預估本身的準確度（因為使用者會自己提供 EPS）**：
  - **Bradshaw, Drake, Myers & Myers (2012)**, RAST 17: 944–968 [A]：在**較長期限、小型或年輕公司、分析師預測大幅或負向變化時，簡單隨機漫步 EPS 預測比分析師準**；預測 2–3 年後盈餘時，**直接外推分析師 1 年期預估最準**。https://link.springer.com/article/10.1007/s11142-012-9185-8
- **爭議數字**：**Kerl (2011)**, Business Research 4(1)（德國 2002–2004）：搜尋摘要同時出現「12 個月後準確度 73.64%」與「56.53%」，指標定義不明 → [C]。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1806927

---

## 6. 個股本益比的均值回歸／可預測性

### 6.1 持續性與均值回歸
- **Beaver & Morse 1978** [A]：P/E 投資組合差異**持續長達 14 年**；但形成年的暫時性盈餘扭曲很快反轉（形成年與次年盈餘成長的相關性正負相反）。**推論**：個股 P/E ≈「持續性成分（會計方法、產業、長期預期）」＋「暫時性成分（分母雜訊，1–2 年內回歸）」。
- **Fama & French (2000)**, "Forecasting Profitability and Earnings," Journal of Business 73(2): 161–175 [A/B]：部分調整模型下，**獲利能力每年均值回歸約 38%**（另一來源記為約 40%）；**低於均值、離均值越遠時回歸越快**（非線性）。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=216588
- **Nissim & Penman (2001)**, RAST 6: 109–154 [A/B]：多數財務比率會回歸典型值；提供歷史比率基準以做預測。http://www.columbia.edu/~dn75/Ratio_analysis_and_equity_valuation_From_research_to_practice.pdf
- **個股 P/E 的半衰期／回歸速度的直接估計（多少年回歸一半）：查無**可信原始研究（搜尋只找到大學部論文與大盤 S&P 500 研究，不採用）。

### 6.2 P/E 預測未來的「盈餘」（P/E 的資訊內容）
- **Ou & Penman 1989**、**Fuller-Huberts-Levinson 1993**、**Fairfield 1994**、**Penman 1996**：P/E 對**未來盈餘成長**有預測力（見 §2）[A/B]。

### 6.3 P/E 預測未來的「報酬」（＝P/E 相對壓縮）
- **Basu (1977)**, JF 32(3): 663–682 [A/B]：**低 P/E 投資組合的風險調整後報酬高於高 P/E**。https://ideas.repec.org/a/bla/jfinan/v32y1977i3p663-82.html
- **Lakonishok, Shleifer & Vishny (1994)**, JF 49(5): 1541–1578 [A/B]：價值策略報酬較高，是因為投資人把熱門股過去的成長**外推過頭**，而不是價值股風險較高。https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1994.tb04772.x
- **La Porta (1996)**, JF 51(5): 1715–1742 [A]：分析師**長期成長預估最樂觀的股票，之後報酬最低**；預期太極端。https://ideas.repec.org/a/bla/jfinan/v51y1996i5p1715-42.html （高低組報酬差「15%」只見於單一二手摘要 → [C]）
- **Bordalo, Gennaioli, La Porta & Shleifer (2019)**, "Diagnostic Expectations and Stock Returns," JF 74(6): 2839–2874 [A]：以代表性捷思（對新聞過度反應）解釋高 LTG 股票的低報酬。https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12833
- **Delao-Han-Myers 2025** [B]：估值比率**主要預測報酬**（見 §3.3）。

### 6.4 直接預測「未來倍數」的研究
- **Bhojraj & Lee (2002)** [A]：唯一找到、**直接以「未來 1–3 年的倍數（EV/S、P/B）」為預測目標**的經典研究；方法＝橫斷面迴歸出應有倍數 → 挑同業 → 用同業倍數預測未來倍數；勝過產業與規模配對（具體 R² 見 §4，[C]）。**注意：它預測的是 EV/S 與 P/B，不是 P/E。**
- **Bhojraj, Lee & Ng (2003)**, "International Valuation Using Smart Multiples"（工作論文）[B]：把應有倍數法延伸到國際。https://people.duke.edu/~charvey/Teaching/BA453_2006/Ng_2003_Smart_multiples.pdf
- **Babii, Ball, Ghysels & Striaukas (2024)**, "Panel Data Nowcasting: The Case of Price-Earnings Ratios," Journal of Applied Econometrics 39(2): 292–307 [A]：用稀疏群組 LASSO 與混頻資料（總經、金融、新聞文本）即時預測企業盈餘／P/E。**樣本外成績的具體數字：查無**。https://ideas.repec.org/p/arx/papers/2307.02673.html
- **直接預測「個股 12 個月後 P/E」並報告樣本外誤差的同儕審查文獻：查無**（搜尋到的只有 2025 年 IRFE 的 LSTM＋情緒研究，未讀到數字，不採用）。

---

## 7. 反面證據與互相矛盾的結果（必讀）

| # | 主流說法 | 反面證據 | 我的判讀 |
|---|---|---|---|
| 1 | 橫斷面估值差異主要是**基本面（獲利／現金流）**（CPV 2003：預期報酬只佔 B/M 變異 20–25%；CPV 2009：錯誤定價份額可忽略；Keloharju et al. 2021：長期折現率不因公司而異） | **Delao-Han-Myers 2025 JFE：約 75% 的 P/E 離散度反映在未來報酬，只有 25% 反映在盈餘成長** | **不確定**。可能原因（推論）：P/B 的分母不含獲利能力，所以 ROE 差異會進入 B/M 的「基本面」份額；P/E 已經除以盈餘，剩下的主要是「成長預期＋折現率」，而成長預期又幾乎不可預測，所以殘差落在報酬上。兩者衡量對象不同，不一定真的互斥 |
| 2 | 個股報酬由現金流消息主導（Vuolteenaho 2002） | **Chen & Zhao 2009 RFS 22(12): 5213–5249**：VAR 分解中現金流消息是**殘差**，折現率預測力弱時無法可靠推論兩者相對重要性；用照理現金流變異為零的公債測試，方法會誤判 | Vuolteenaho 的「>2 倍」**有方法論風險**；但 Chen-Da-Zhao 2013 用分析師預估直接量測，方向一致（現金流消息隨期限變重要）→ 方向可信、精確比例不可信 |
| 3 | 大盤 P/E/D/P 變動「幾乎全是」折現率（Cochrane 2011） | **De la O & Myers 2021**：用調查預期，現金流成長預期至少解釋 P/D 93%、P/E 63% 的變異；**Chen-Da-Zhao 2013**：期限 >2 年時大盤也以現金流消息為主 | **不確定**，取決於用「理性預期」還是「主觀（調查）預期」 |
| 4 | 成長無法解釋 P/E（Beaver & Morse 1978） | **Zarowin 1990**：改用**預估**成長後，成長變成主導因素 | 已解決：差別在「已實現成長」 vs「預期成長」。但 Chan et al. 2003 指出預期成長偏樂觀且無持續性 → P/E 反映「預期」，而預期常常錯 |
| 5 | forward 盈餘倍數最準（LNT 2002；Kim & Ritter 1999） | **Lie & Lie 2002**：資產倍數比盈餘倍數更精確、偏誤更小 | 部分矛盾；Lie & Lie 估的是企業價值、樣本含虧損公司，準確度強烈依規模、獲利能力、無形資產而定 |
| 6 | 目標價準確度低（BBH 2013：期末 38%） | **Asquith et al. 2005**：略高於一半達標；**Kerl 2011**：德國有 56–74% 這類較高數字（[C]） | 「達標」定義不同（期末 vs 期間內任一時點；明星分析師 vs 全體），期間內曾觸及 64% vs 期末 38% 的落差本身就說明定義的影響很大 |
| 7 | 分析師 EPS 預估優於時間序列 | **Bradshaw et al. 2012**：長期限、小／年輕公司、大幅或負向變動時，隨機漫步更準 | 使用者自備 EPS 時，EPS 誤差本身可能就主導價格誤差 |

---

## 8. 對新模型的設計含意（全部為推論，供參考）

1. **分母一定要用「正常化／預估」EPS，不要用暫時性被壓低或拉高的 trailing EPS**（Molodovsky、Beaver-Morse、Penman 1996、LNT 2002、Kim-Ritter 1999）。景氣循環股在盈餘谷底時 P/E 天然偏高，如果使用者給的 forward EPS 回升，模型應預期 P/E 壓縮。
2. **P/E 的橫斷面錨點**：產業（3 位數 SIC 等級）＋應有倍數迴歸（成長、獲利能力變化、風險）（Alford、LNT、Bhojraj-Lee、Geertsema-Lu）。
3. **回歸方向**：相對同業偏高的 P/E 傾向以「低報酬」修正（Delao-Han-Myers 2025、Basu、LSV、La Porta），但持續性高（Beaver-Morse 14 年）→ 12 個月內只會部分回歸；**個股 P/E 回歸半衰期沒有可信的現成數字，必須自己回測估計**。
4. **不可約的不確定性**：12 個月後的 P/E 取決於對 24 個月以後成長的重新評估（Chen-Da-Zhao 2013：長期限以現金流消息為主；Chan et al. 2003：長期成長不可預測）以及大盤共同的折現率變動（Vuolteenaho 2002）→ 區間要寬，且應該分成「大盤倍數變動」與「個股特有」兩塊。
5. **要打敗的基準**：(i) 隨機漫步價格；(ii) 共識目標價（12 個月平均絕對誤差約 45%、期末達標約 38%，且平均偏樂觀約 15 個百分點）；(iii) 使用者 EPS × 當前 P/E；(iv) 使用者 EPS × 產業／應有 P/E。**同期倍數估值「半數誤差 ±15%」是理論下限，不是可以期待的 12 個月表現。**
6. **評估方式**：用「期末」價格評估（不要用「期間內曾觸及」，它會把命中率從約 38% 灌到約 64%）；並分別報告「同產業相對排序」能力（Da-Schaumburg 2011 指出相對排序比絕對水準更有資訊）。

---

## 9. 查無清單

- Beaver & Morse 1978、Zarowin 1990、Vuolteenaho 2002、Bradshaw-Brown-Huang 2013 的**確切樣本筆數／期間**（BBH 只確認 2000–2009）。
- Liu-Nissim-Thomas 2002 **各倍數的 IQR 數字**。
- Bhojraj-Lee 2002 的**確切 R²**（二手數字互相矛盾）。
- Fuller-Huberts-Levinson 1993 的 E/P 五分位成長與報酬數字。
- Chen-Da-Zhao 2013 **1 年期限**的現金流／折現率確切比例。
- **個股 P/E 均值回歸的半衰期**、**直接預測個股 12 個月後 P/E 的同儕審查樣本外誤差**。
- 以「Molodovsky 效應」為名的個股層級量化研究。
- 任務中「Liu, Nissim & Thomas (2007)」若指 FAJ 以外的另一篇國際倍數論文。

---

## 10. 來源總表（查詢日期皆為 2026-10-01；取得方式皆為搜尋摘要，WebFetch 被封鎖）

| 文獻 | 網址 |
|---|---|
| Beaver & Morse 1978 | https://rpc.cfainstitute.org/research/financial-analysts-journal/1978/what-determines-price-earnings-ratios |
| Zarowin 1990 | https://journals.sagepub.com/doi/abs/10.1177/0148-558X1989005003007 |
| Molodovsky 1953 | https://www.tandfonline.com/doi/abs/10.2469/faj.v9.n5.65 |
| Fuller-Huberts-Levinson 1993 | https://jpm.pm-research.com/content/19/2/13 |
| Chan-Karceski-Lakonishok 2003 | https://ideas.repec.org/a/bla/jfinan/v58y2003i2p643-684.html |
| Fairfield 1994 | https://rpc.cfainstitute.org/research/financial-analysts-journal/1994/pe-pb-and-the-present-value-of-future-dividends |
| Penman 1996 | https://business.columbia.edu/faculty/research/articulation-price-earnings-ratios-and-market-book-ratios-and-evaluation-growth |
| Ou & Penman 1989 | https://ideas.repec.org/a/bla/joares/v27y1989ip111-144.html |
| Campbell & Shiller 1988a | https://academic.oup.com/rfs/article-abstract/1/3/195/1580239 |
| Campbell & Shiller 1988b | https://campbell.scholars.harvard.edu/publications/stock-prices-earnings-and-expected-dividends |
| Campbell & Shiller 1998/2001 | https://www.nber.org/papers/w8221 |
| Campbell 1991 | https://academic.oup.com/ej/article-abstract/101/405/157/5188371 |
| Cochrane 2008 | https://www.johnhcochrane.com/research-all/the-dog-that-did-not-bark-a-defense-of-return-predictability |
| Cochrane 2011 | https://ideas.repec.org/a/bla/jfinan/v66y2011i4p1047-1108.html |
| Vuolteenaho 2002 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00421 |
| Callen & Segal 2004 | https://wrap.warwick.ac.uk/id/eprint/125013/ |
| Chen-Da-Zhao 2013 | https://academicweb.nd.edu/~zda/CDZ.pdf |
| Chen & Zhao 2009 | https://academic.oup.com/rfs/article-abstract/22/12/5213/1575569 |
| Cohen-Polk-Vuolteenaho 2003 | https://ideas.repec.org/a/bla/jfinan/v58y2003i2p609-641.html |
| Cohen-Polk-Vuolteenaho 2009 | https://ideas.repec.org/a/bla/jfinan/v64y2009i6p2739-2782.html |
| Keloharju-Linnainmaa-Nyberg 2021 | https://www.nber.org/papers/w25579 |
| Lochstoer & Tetlock 2020 | https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.12876 |
| De la O & Myers 2021 | https://onlinelibrary.wiley.com/doi/10.1111/jofi.13016 |
| Delao-Han-Myers 2025 (JFE) | https://www.sciencedirect.com/science/article/pii/S0304405X25000674 |
| 同上二手（Swedroe/Morningstar） | https://www.morningstar.com/markets/price-primarily-predicts-future-returns-not-future-earnings-growth |
| Delao-Han-Myers (RFS 待刊) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4279862 |
| Alford 1992 | https://www.semanticscholar.org/paper/THE-EFFECT-OF-THE-SET-OF-COMPARABLE-FIRMS-ON-THE-OF-Alford/fbe35e65a67882ce572ae631443f7ee53d2ad372 |
| Liu-Nissim-Thomas 2002 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00042 |
| Liu-Nissim-Thomas 2007 | https://rpc.cfainstitute.org/research/financial-analysts-journal/2007/is-cash-flow-king-in-valuations |
| Bhojraj & Lee 2002 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00054 |
| Kaplan & Ruback 1995 | https://www.ssrn.com/abstract=6609 |
| Kim & Ritter 1999 | https://ideas.repec.org/a/eee/jfinec/v53y1999i3p409-437.html |
| Lie & Lie 2002 | https://www.biz.uiowa.edu/faculty/elie/valbymult.pdf |
| Geertsema & Lu 2023 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.12464 |
| Bradshaw-Brown-Huang 2013 | https://link.springer.com/article/10.1007/s11142-012-9216-5 |
| Asquith-Mikhail-Au 2005 | https://www.nber.org/papers/w9246 |
| Bonini et al. 2010 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=676327 |
| Bilinski et al. 2013 | https://eprints.lancs.ac.uk/id/eprint/71029/1/Analyst_TP_accuracy_Feb2012.pdf |
| Brav & Lehavy 2003 | https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00593 |
| Da & Schaumburg 2011 | https://academicweb.nd.edu/~zda/TargetPrice.pdf |
| Demirakos-Strong-Walker 2010 | https://ideas.repec.org/a/taf/euract/v19y2010i1p35-72.html |
| Gleason-Johnson-Li 2013 | https://www.semanticscholar.org/paper/Valuation-Model-Use-and-the-Price-Target-of-Equity-Gleason-Johnson/23568c0ae1e54a607068acb9002914f228d45b53 |
| Kerl 2011 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1806927 |
| Bradshaw-Drake-Myers-Myers 2012 | https://link.springer.com/article/10.1007/s11142-012-9185-8 |
| Fama & French 2000 | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=216588 |
| Nissim & Penman 2001 | http://www.columbia.edu/~dn75/Ratio_analysis_and_equity_valuation_From_research_to_practice.pdf |
| Basu 1977 | https://ideas.repec.org/a/bla/jfinan/v32y1977i3p663-82.html |
| Lakonishok-Shleifer-Vishny 1994 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1994.tb04772.x |
| La Porta 1996 | https://ideas.repec.org/a/bla/jfinan/v51y1996i5p1715-42.html |
| Bordalo et al. 2019 | https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12833 |
| Penman & Reggiani 2013 | https://link.springer.com/article/10.1007/s11142-013-9226-y |
| Collins & Kothari 1989 | https://ideas.repec.org/a/eee/jaecon/v11y1989i2-3p143-181.html |
| Babii et al. 2024 | https://ideas.repec.org/p/arx/papers/2307.02673.html |

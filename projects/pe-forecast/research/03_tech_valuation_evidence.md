# 科技成長股該用哪種估值／本益比理論當骨架？理論特殊性與模型準確度實證
## 文獻調查長版報告（查詢日期：2026-10-06）

> 用途：替「給定未來 EPS 路徑 → 預估 12 個月後本益比與股價」的科技股模型選骨架。
> 接續：`01_theory_lineage.md`（Gordon、MM-PVGO、Leibowitz-Kogelman、Ohlson 1995、OJ 2005、Penman 1996、Campbell-Shiller）與 `02_empirical_evidence.md`（P/E 決定因素、可預測性）。本檔只補**科技／高成長／高研發**的理論與實證，不重講一般理論。
> 作者：subagent（只用 WebSearch／WebFetch）。

---

## 0. 方法、限制與標記規則（先讀）

**取得方式的限制**：本 session 的 WebFetch **仍然全面被 egress proxy 擋下**。實測 nber.org、ideas.repec.org、pietroveronesi.org、onlinelibrary.wiley.com、anderson.ucla.edu、marcosammon.com、papers.ssrn.com、pages.stern.nyu.edu 都回 `EGRESS_BLOCKED`。所以：
- **每一篇都「只看到摘要」**：內容來自 WebSearch 對期刊頁、SSRN、NBER、作者網頁、出版社頁擷取的摘要文字。**沒有任何一篇讀到全文、表格或附錄。**
- 「原文第幾式、第幾表」都沒有核對過。要逐字引用之前，請在一般瀏覽器開原文確認。

| 標記 | 意義 |
|---|---|
| **[A]** | 搜尋結果引的是原文摘要或出版頁文字（期刊頁／SSRN／NBER／作者頁），書目資料一致 |
| **[B]** | 二手轉述（引用它的論文、書評、投資部落格、新聞稿）或只出現在單一搜尋摘要 |
| **[C]** | 數字來源不明、搜尋摘要之間互相矛盾，或無法確認是哪篇論文說的 → **不要直接引用** |
| 事實／推論／不確定 | 事實＝文獻寫了什麼；推論＝我自己整理或推導的含意；不確定＝查無或證據衝突 |

- 所有網址查詢日期一律 **2026-10-06**。
- 標【推論・已驗算】的數字是我用 Python 算出來的示意值（腳本：scratchpad `tech_check.py`，不在 repo 內），**不是任何論文的結果**。

---

## 1. 直接回答（摘要）

### (a) 科技成長股在理論上的特殊性，哪些理論處理得了

| 特殊性 | 為什麼會讓標準 P/E 理論失效 | 能處理的理論／模型 | 處理不了的 |
|---|---|---|---|
| **① 超額成長期有限**（競爭會追上來） | Gordon／常數成長 P/E 假設成長永續；科技股的高 ROE 會衰退 | Leibowitz-Kogelman franchise（已在 01）、**Pástor-Veronesi 2003/2006**（超額獲利只維持 T 年，之後 M/B→1）、Ohlson 1995 的 ω 持續性參數、Damodaran 兩階段／三階段 | 單階段 Gordon、PEG 經驗法則 |
| **② 研發費用化**（投資被當成費用） | 投資期 EPS 被壓低、帳面淨值被低估 → P/E、P/B 都虛高，且偏誤方向會隨研發成長率變號 | **Lev-Sougiannis 1996** 研發資本化、**Lev-Sarath-Sougiannis 2005** 偏誤模型、Penman-Zhang 2002 hidden reserves、Damodaran 研發資本化步驟；理論上 RIM 對「保守會計」有自我修正，但要靠很長的預測期或對的終值 | 直接用 GAAP EPS 的 P/E、有限期 RIM 但終值亂設 |
| **③ 不確定性高** | 價值是成長率的**凸函數**，不確定性本身會推高今天的價格（Jensen 不等式）；點估計 EPS 路徑會系統性低估 | **Pástor-Veronesi 2003/2006/2009**（學習＋不確定性）、**Schwartz-Moon 2000/2001**（營收與成長率隨機，蒙地卡羅模擬）、實質選擇權 | 所有「單一路徑、確定性」的 DCF／RIM／P/E 公式 |
| **④ 虧損** | EPS ≤ 0 時 P/E 沒有定義；網路股研究發現盈餘根本不被定價 | Schwartz-Moon（以營收為主）、Damodaran 年輕公司 DCF（營收→目標利潤率→再投資→破產機率）、EV/Sales、非財務指標（Amir-Lev 1996、Trueman-Wong-Zhang 2000） | 任何以 EPS 當分母的倍數 |
| **⑤ 低／零派息** | DDM 在有限預測期幾乎全靠終值；PV 2003 指出**不配息公司 M/B 對不確定性更敏感** | RIM、AEG（OJ 2005，不受股利政策影響）、Pástor-Veronesi | 有限期 DDM（Penman-Sougiannis 1998 的實證最差） |
| **⑥（額外）股權報酬 SBC 與庫藏股** | SBC 是真實成本卻常被非 GAAP 排除；買回讓帳面淨值很小甚至為負 → RIM 不穩 | Core-Guay-Kothari 2002（稀釋 EPS 修正）、Mohanram-White-Zhao 2020、AEG（只用 EPS，不需帳面淨值） | 用非 GAAP EPS 當輸入的任何模型 |

**推論**：沒有一個理論同時處理 ①–⑥。可行的組合是「**Ohlson／OJ 會計估值（處理 ⑤，且 P/E 可以從中導出）＋明確的有限超額期與衰退率（①）＋研發／SBC 調整後的 EPS（②⑥）＋對 EPS 路徑做分布而非點估計（③）**」；EPS ≤ 0 的公司（④）不要用 P/E，改用營收基礎模型。

### (b) 實證上，高成長／高研發樣本裡哪個模型比較準

**一句話：直接在科技股子樣本做「模型賽馬」的大樣本研究非常少；找到的證據大多是間接的，而且都指向「終值與成長衰退的假設」比「選哪個模型」更重要。**

| 證據 | 樣本 | 結論 | 等級 |
|---|---|---|---|
| Klobucnik & Sievers 2013 | 約 30,000 筆科技公司季資料，1992–2009 | Schwartz-Moon 模型 ≈ EV/Sales 倍數一樣準；在製藥與電腦業更準；EV/Sales 的中位估值誤差 59%、平均 75% | 結論 [A]；數字 [B] |
| Liu-Nissim-Thomas 2002 | 美股全產業（81 個產業） | **forward EPS 倍數最準**，約一半樣本誤差在 ±15% 內；排名「幾乎所有產業都一樣」 | [A] |
| Kim & Ritter 1999 | 美國 IPO | 倍數中 forward P/E 最準、下一年 EPS 預估優於當年 EPS；但整體解釋力只有「modest」 | [A] |
| Penman & Sougiannis 1998 | 全樣本，事後實現的 payoff | 應計盈餘（RIM）誤差 < DCF < DDM；但 **RIM 在 P/E、P/B 高的公司表現不好**（終值成長貢獻太大） | 前半 [A]；後半 [B] |
| Courteau-Kao-Richardson 2001 | Value Line 預測 | 終值用 **Value Line 預測股價** 的模型誤差最小，「大幅」勝過任意成長率的終值 | [A] |
| Jorgensen-Lee-Yoo 2011 | 美股 | AEG（OJ）的估值準確度**普遍不如** RIM；拉長到 5 年預測期改善但仍較差；原因是預測期後的成長假設 | [A] |
| Bradshaw 2004；Gleason-Johnson-Li 2013 | 分析師報告 | 分析師推薦跟 PEG／長期成長走，但 **RIM 估值才預測未來報酬**；分析師用 RIM 的目標價投資表現較好，**但 EPS 預估不準時優勢縮小** | [A]（Bradshaw 的報酬結果 [B]） |
| Bartov-Mohanram-Seethamraju 2002；Trueman-Wong-Zhang 2000 | 網路 IPO／網路股 | 網路公司**盈餘不被定價**（甚至負相關）；負的現金流被當投資而定價；毛利有價值關聯 | [A]／[B] |
| Huang-Tan-Wang-Yu 2023 | 分析師報告文字分析 | 盈餘品質低、風險高的公司，分析師較常改用 DCF；市場對 DCF 目標價變動反應較大 | [A] |
| Francis-Olsson-Oswald 2000 在高研發子樣本的結果 | — | **查無**（只確認全樣本 AE 模型勝出，子樣本結果搜尋不到） | 不確定 |

### (c) 有沒有科技股專用的本益比理論

- **事實**：搜尋不到任何一篇以「科技股本益比」為名、輸出 P/E 的專用理論（**查無**）。
- 有「科技／高成長專用的**估值**模型」，但它們的輸出是價值或 M/B，不是 P/E：
  1. **Pástor-Veronesi（2003 JF、2006 JFE、2009 AER）**：學習＋獲利能力不確定性 → 解釋高 M/B、高波動、隨公司年齡下降。
  2. **Schwartz-Moon（2000 FAJ、2001 Financial Review）**：營收與營收成長率都是隨機過程的實質選擇權／蒙地卡羅模型，為網路公司設計。
  3. **Damodaran（2009 SSRN）**：年輕／高成長公司 DCF 流程（營收成長、目標利潤率、sales-to-capital、存活機率）。
- **PEG**：實務經驗法則。Easton 2004 證明它是 AEG 的一個特例（未配息、第 2 年之後異常成長不變）；排名跟較完整的隱含報酬率高度相關，**但用 PEG 推出的預期報酬率偏低** [A]。
- **推論**：所謂「科技股本益比」應該當成**導出量**：用上面的估值框架算出 12 個月後的價值，再除以當時的 forward EPS，而不是直接建一條 P/E 方程式。

### 建議骨架（推論）

> **以 Ohlson 1995 剩餘收益（帳面淨值很小或為負時改 OJ／AEG）為主體；用 Pástor-Veronesi 的「超額獲利只維持有限期，且不確定性具凸性」當結構；輸入 EPS 先扣 SBC、可選擇性做研發資本化；對 EPS 路徑做情境或分布，最後才算出 P/E＝V₁₂/EPS_fwd。EPS ≤ 0 的公司改用 Schwartz-Moon 精簡版或 EV/Sales，以 forward P/E 同業倍數當基準，用來對照。**

細節見 §9。

---

## 2. 成長不確定性推高估值：Pástor & Veronesi 系列

### 2.1 Pástor & Veronesi (2003) "Stock Valuation and Learning about Profitability", *Journal of Finance* 58(5): 1749–1789
- 網址：https://onlinelibrary.wiley.com/doi/10.1111/1540-6261.00587 ；NBER w8991：https://www.nber.org/papers/w8991 ；RePEc：https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1749-1789.html
- 【事實 A】模型：投資人對公司「平均獲利能力」不確定，並逐年學習。
- 【事實 A】主要預測與發現：
  1. **M/B 隨「平均獲利能力的不確定性」上升而上升，對不配息公司尤其明顯。**
  2. M/B 隨公司存續時間下降（學習讓不確定性下降），**年輕公司下降得更陡**。
  3. 實證：公司年齡與 M/B 有顯著的負橫斷面關係，控制其他 M/B 決定因素後仍成立；年輕股票和不配息股票報酬波動較大；公司獲利能力近年變得更不穩定，這有助解釋特有波動上升之謎。
- 【事實 B】機制（引自 Pástor-Veronesi 2009 年的綜述 "Learning in Financial Markets"，https://www.sfu.ca/~kkasa/Pastor_Veronesi_09.pdf ；NBER w14646 https://www.nber.org/papers/w14646 ）：價格對成長率是凸的，例如 Gordon 的 1/(r−g) 對 g 是凸函數，所以由 Jensen 不等式，g 的不確定性本身會推高價格。
- 【推論・已驗算】示意：r=9%、g 平均 5%，確定時 P/D＝25。g 的標準差 1% → E[1/(r−g)]≈26.9；1.5% → ≈28.4（模擬時 g 截斷在 <8%，否則期望值發散）。**不確定性越大、越接近 r，凸性溢價越大，而且數值很不穩定**，這也是終值假設主導科技股估值的原因。
- 【推論，非原文公式】若超額 ROE 在 T 年內累積、ρ 服從常態 N(μ, σ²)，那麼 E[e^{ρT}] = e^{μT + σ²T²/2}：不確定性項按 **T²** 放大。T=15 年時，σ=2% → 價值乘數約 1.05；σ=4.86% → 約 1.30；σ=6% → 約 1.50【已驗算】。這只是說明凸性的量級，不是 PV 原文的計算。
- **對科技股 P/E 模型的含意（推論）**：
  - 用「EPS 路徑的期望值」代入確定性公式，會**系統性低估**合理價值；應該對路徑做分布（至少悲觀／基準／樂觀三情境並加權），或明確加上凸性溢價。
  - 「上市年數」「是否配息」可以當不確定性的代理變數：越年輕、不配息 → 合理倍數越高，但之後的倍數壓縮也越快（M/B 隨年齡下降）。

### 2.2 Pástor & Veronesi (2006) "Was There a Nasdaq Bubble in the Late 1990s?", *Journal of Financial Economics* 81(1): 61–100
- 網址：https://www.sciencedirect.com/science/article/abs/pii/S0304405X05002163 ；NBER w10581：https://www.nber.org/papers/w10581 ；工作論文 PDF：https://conference.nber.org/confer/2004/apf04/pastor.pdf 、https://users.nber.org/~confer/2004/entf04/pastor.pdf
- 【事實 A】核心主張：公司基本面價值隨「平均未來獲利能力的不確定性」上升而上升，而這種不確定性在 1990 年代末異常高。校準模型後，要符合 Nasdaq 高峰估值所需的不確定性「高但合理」，同一個不確定性也能解釋當時 Nasdaq 異常高的報酬波動。
- 【事實 B（工作論文版搜尋片段，可能和期刊版不同）】
  - 2000-03-10 Nasdaq 的 M/B＝6.85；1999 年 ROE＝12.79%/年。
  - 競爭在隨機時點 T 到來，之後 M/B 收斂；基準情境 E(T)＝20 年，另測 15、25 年。
  - 預期超額獲利能力和股權風險溢酬都設 4% 時，所需不確定性為 4.86%。
  - 以符合 2000 年 3 月水準與波動的先驗出發，模型預測的峰後跌幅和實際相近。
- 【事實 A】此文獲 JFE Fama/DFA 獎（資本市場與資產定價領域第二名）。
- **含意（推論）**：
  - 這是最接近「科技股專用」的理論骨架：**價值 ＝ 有限期超額獲利（T）× 不確定性的凸性**。
  - 12 個月 P/E 預測要特別注意：**不確定性解除（學習）本身就會讓倍數下降**，即使 EPS 照預期實現也一樣（PV 2003 的 M/B 隨年齡下降）。

### 2.3 Pástor & Veronesi (2009) "Technological Revolutions and Stock Prices", *American Economic Review* 99(4): 1451–83
- 網址：https://www.aeaweb.org/articles?id=10.1257%2Faer.99.4.1451 ；NBER w11876：https://www.nber.org/papers/w11876
- 【事實 A】一般均衡模型：技術革命期間，創新公司的股價會出現「泡沫狀」型態與高波動，來源是對新技術平均生產力的高度不確定。技術一旦被大規模採用，不確定性從特有轉成系統性，於是股價在初期飆漲後下跌。實證支持：1830–1861 年鐵路、1992–2005 年網路。獲 Stephen A. Ross 獎。
- **含意（推論）**：AI／新平台題材股可能同時有「不確定性推高倍數」和「採用確定後折現率上升、倍數下降」兩階段；12 個月 P/E 預測應納入「題材所處階段」這種狀態變數，不能只看 EPS。

---

## 3. 高成長公司的專用估值模型

### 3.1 Schwartz & Moon (2000) "Rational Pricing of Internet Companies", *Financial Analysts Journal* 56(3): 62–75
- 網址：https://www.semanticscholar.org/paper/Rational-Pricing-of-Internet-Companies-Schwartz-Moon/307a120148f0546f7413f698bc4fe48611c36959 ；https://www.researchgate.net/publication/2612771_Rational_Pricing_Of_Internet_Companies
- 【事實 A】方法：用實質選擇權理論與資本預算處理網路股估值。模型以連續時間寫成，再離散化、估計參數、用模擬求解並做敏感度分析。核心是讓**營收和營收成長率都不確定**：預期成長率本身是隨機、且會均值回歸的過程。以 Amazon.com 為例。
- 【事實 A】摘要原句大意：「即使公司有相當真實的破產機率，只要初始成長率夠高、成長率的波動夠大，估值就可能高到原本看起來不可思議的程度。」
- 【事實 B】結果：估值對初始條件和參數設定**非常敏感**；以模型看 Amazon 股權被高估；要讓模型價格符合市價，需要「顯著更高的獲利能力」或不切實際的營收分布。
- 【不確定 C】「初始成長率錯 ±10% → 估值偏差 35%」「每 1 個百分點初始成長率 → 3.53% 價值變動」：搜尋摘要沒有標明出自哪篇，不引用。
- 【事實 A】續篇 Schwartz & Moon (2001) "Rational Pricing of Internet Companies Revisited", *Financial Review* 36(4): 7–26：加入隨機成本、未來融資、資本支出與折舊，以 eBay 示範。https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6288.2001.tb00027.x ；工作論文 https://www.anderson.ucla.edu/documents/areas/fac/finance/26-00.pdf
- **含意（推論）**：
  - 這是處理 ③④ 最直接的模型，但**輸出是價值，不是 P/E**。
  - 實務上最難的參數（成長率的初始波動、均值回歸速度）正好對應 KIWI 模型的「EPS 路徑分布寬度」與「衰退率」。可以借用它的結構：**EPS（或營收）成長率 g_t 以 κ 的速度回歸長期 ḡ，且 g_t 本身帶波動 σ_t，σ_t 也隨時間遞減**。

### 3.2 Klobucnik & Sievers (2013) "Valuing High Technology Growth Firms", *Journal of Business Economics* 83(9): 947–984
- 網址：https://link.springer.com/article/10.1007/s11573-013-0684-2 ；SSRN：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2084180 ；PDF：https://leeds-faculty.colorado.edu/bhagat/high-tech-firm-valuation.pdf
- 【事實 A】第一個大樣本實作 Schwartz-Moon：約 30,000 筆科技公司季資料（1992–2009），用實際會計資料，並以 EV/Sales 倍數為比較基準。
- 【事實 A】S-M 模型的準確度和傳統營收倍數相當；在小型與未上市公司估值上有優勢；能指出嚴重的市場高估或低估，以此建構的交易策略有顯著投資價值。
- 【事實 B】EV/Sales 的中位估值誤差 59%、平均 75%；S-M「平均幾乎一樣準」，在製藥與電腦業更準。
- **含意（推論）**：
  - 這是唯一找到的**科技股子樣本大樣本模型賽馬**：結構化的不確定性模型 ≈ 營收倍數，沒有大幅勝出。
  - 科技股估值誤差本來就大（中位數 59% 量級），12 個月股價區間必須**很寬**；不要期待點預測的準確度能接近 Liu-Nissim-Thomas 全市場「一半樣本 ±15%」的水準。

### 3.3 Damodaran：年輕／高成長公司與研發資本化（講義與 SSRN 論文）
- 【事實 A】"Valuing Young, Start-up and Growth Companies: Estimation Issues and Valuation Challenges"（2009-06，SSRN 1418687，67 頁）：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1418687 ；PDF https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/younggrowth.pdf
  - 用「同業成熟公司資料＋公司自身特性」預測營收、盈餘、現金流；以 sales-to-capital 比率決定再投資；估計私人資本的折現率；**把破產／失敗機率另外調整進今天的價值**；主張常用的創投法有缺陷、應被取代。
- 【事實 A／B】研發資本化步驟（講義與論文）：https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/R_D.pdf ；https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/intangibles.pdf （2009-09 "Valuing Companies with Intangible Assets"）；投影片 https://pages.stern.nyu.edu/~adamodar/podcasts/valspr21/session8slides.pdf
  - 設定研發的攤銷年限（2–10 年），把攤銷年限內的過去研發支出加總成「研究資產」。
  - **調整後營業利益 ＝ 營業利益 ＋ 當期研發 − 研究資產攤銷**；研發持續成長的公司，調整後利益通常會上升。
  - 調整後淨資本支出 ＝ 淨資本支出 ＋ 當期研發 − 攤銷；資本報酬率會被同時改變。
- 【事實 A】P/E 決定因素（講義）：P/E 是成長、風險、配息率的函數，高成長公司要分高成長期與穩定期兩段估計。https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/pe.pdf
- **含意（推論）**：Damodaran 的方法是「營收驅動 DCF」，跟 Schwartz-Moon 的結構相同但改成確定性情境。對 KIWI 模型最可以直接拿來用的是：(1) 研發資本化公式；(2) 用 sales-to-capital 檢查 EPS 路徑是否隱含不可能的再投資；(3) 存活機率加權。

---

## 4. 研發費用化、會計扭曲，與盈餘對科技公司的解釋力

### 4.1 Lev & Sougiannis (1996) "The Capitalization, Amortization, and Value-Relevance of R&D", *Journal of Accounting and Economics* 21(1): 107–138
- 網址：https://experts.illinois.edu/en/publications/the-capitalization-amortization-and-value-relevance-of-rampd/ ；https://www.semanticscholar.org/paper/The-capitalization,-amortization,-and-of-R&D-Lev-Sougiannis/4ce1b17522ec533307adedfa9ca54727e14d904c
- 【事實 A】方法：估計各產業研發投入與後續營業利益的關係，推出各產業的研發攤銷率，然後資本化研發，重算盈餘與帳面淨值。
- 【事實 A】發現：
  1. 資本化並攤銷研發後，調整後的盈餘和帳面淨值**與股價、報酬的關聯顯著提高**，對投資人有「統計上可靠、經濟上有意義」的資訊。
  2. 研發資本和**後續**股票報酬顯著相關：可能是研發密集公司被系統性錯誤定價，也可能是研發帶有額外風險因子的補償。
- 【事實 B】製藥業的研發折舊率約 11.2%（出自 Li & Hall 2018 對文獻的整理 https://eml.berkeley.edu/~bhhall/papers/LiHall18_ROIW.pdf ；不確定是否就是 Lev-Sougiannis 的估計值）。
- **含意（推論）**：研發密集的科技股，GAAP EPS 不適合直接當 P/E 分母。可以用「研發資本化後 EPS」做為第二套輸入，看兩套 P/E 的差距。

### 4.2 Chan, Lakonishok & Sougiannis (2001) "The Stock Market Valuation of Research and Development Expenditures", *Journal of Finance* 56(6): 2431–2456
- 網址：https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00411 ；NBER w7223：https://www.nber.org/papers/w7223
- 【事實 A】**有做研發的公司，平均歷史報酬和沒做研發的公司一樣**（市場平均而言沒有錯誤定價研發）。
- 【事實 A】例外：研發占股權市值比高的公司（通常過去報酬很差）之後有大幅超額報酬，看起來市場對「被打趴的研發密集科技股」太悲觀。
- 【事實 B（NBER 工作論文版片段）】研發占市值比高的組合，形成後超額報酬平均 **6.12%/年**；研發密集的 glamour 股（經規模與 B/M 調整）超額報酬 **2.45%/年**。
- **含意（推論）**：
  - 這是重要的反面證據：「市場系統性低估研發」只成立在特定子集（研發/市值高、過去表現差），**不是所有科技股**。
  - 對 P/E 模型而言，「研發/市值」可以當狀態變數：比值高時，模型預測的倍數擴張機率應該較高。

### 4.3 盈餘對科技／無形資產密集公司的解釋力下降
- **Lev & Zarowin (1999) "The Boundaries of Financial Reporting and How to Extend Them", *Journal of Accounting Research* 37(2): 353–385**
  - https://www.semanticscholar.org/paper/The-boundaries-of-financial-reporting-and-how-to-Lev-Zarowin/0b1cb7119f7df04781a8edf0e54022c4a6bf8584 ；https://cris.tau.ac.il/en/publications/the-boundaries-of-financial-reporting-and-how-to-extend-them
  - 【事實 A】過去 20 年，盈餘、現金流、帳面淨值的有用性持續惡化。驅動變化的大型投資（研發、重組）立刻費用化，效益卻較晚認列，造成成本與效益不配合。
- **Lev & Gu (2016) *The End of Accounting and the Path Forward for Investors and Managers*（Wiley）**
  - https://www.wiley.com/en-us/The+End+of+Accounting+and+the+Path+Forward+for+Investors+and+Managers-p-9781119191094 ；書評 https://rpc.cfainstitute.org/research/financial-analysts-journal/2016/the-end-of-accounting-and-the-path-forward
  - 【事實 B（書評轉述）】以盈餘與帳面淨值對市值做迴歸：1950 年代 R² 約 80–90%，到 2010 年代約剩一半；財報只貢獻股價變動資訊的約 5%。
- **Lev (2018) "The Deteriorating Usefulness of Financial Report Information and How to Reverse It", *Accounting and Business Research* 48(5): 465–493**
  - https://www.tandfonline.com/doi/pdf/10.1080/00014788.2018.1470138
  - 【事實 A】大多數公司的報告盈餘已不再反映企業績效；財報約只提供投資人所用資訊的 5%。
- **Srivastava (2014) "Why Have Measures of Earnings Quality Changed over Time?", *JAE* 57: 196–217**
  - https://ideas.repec.org/a/eee/jaecon/v57y2014i2p196-217.html
  - 【事實 A】每一批新上市世代的盈餘品質都比前一批差，主因是**無形資產密集度更高**；整體下降主要來自樣本組成改變，而不是 GAAP 改變。
- **Srivastava (2023) "Trivialization of the Bottom Line and Losing Relevance of Losses", *RAST* 28: 1190–1208**
  - https://link.springer.com/article/10.1007/s11142-023-09794-5
  - 【事實 A】新世代公司的營業費用由「與當期營收不配合」的無形投資主導，所以它們的獲利與利潤率（**特別是負值時**）對未來獲利幾乎沒有資訊量。
- **Enache & Srivastava (2018), *Management Science* 64: 3446–3468**
  - https://dl.acm.org/doi/abs/10.5555/3272525.3272550
  - 【事實 A】SG&A 中「非維持性」的部分行為像投資：與未來獲利、報酬、盈餘波動相關。
- **Allen, Lewis-Western & Valentine (2026) "Intangible-Intensive Firms and Performance Reporting", *RAST* 31: 1877–1923**
  - https://link.springer.com/article/10.1007/s11142-026-09966-z
  - 【事實 A】無形密集公司在 GAAP 盈餘缺乏攸關性時更常揭露非 GAAP 指標，且排除項目品質較高。**排除 R&D 能提升績效指標的預測攸關性。**
- **Kothari, Laguerre & Leone (2002), *RAST* 7: 355–382**
  - https://link.springer.com/article/10.1023/A:1020764227390 ；工作論文 https://www.mit.edu/~kothari/attach/klR&D%20pap%20May%20%202001.pdf
  - 【事實 A／B】研發帶來的未來效益比 PP&E 投資不確定得多；在未來盈餘波動對研發、資本支出的迴歸中，**研發係數約為資本支出的 3 倍**。
  - 【事實 B，反面細節】Amir, Guan & Livne (2007, *JBFA*) 指出，研發比資本支出更增加未來盈餘波動的現象**只出現在研發密集的產業**。https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-5957.2006.00651.x
- **Penman & Zhang (2002) "Accounting Conservatism, the Quality of Earnings, and Stock Returns", *TAR* 77: 237–264**
  - https://business.columbia.edu/faculty/research/accounting-conservatism-quality-earnings-and-stock-returns
  - 【事實 A／B】保守會計＋投資成長 → 盈餘被壓低、形成 hidden reserves；投資放緩時這些準備會釋放進盈餘，使盈餘「虛增」。這些衡量指標能預測股票報酬，表示投資人沒看懂保守會計與投資變化的交互作用。
- **Lev, Sarath & Sougiannis (2005) "R&D Reporting Biases and Their Consequences", *CAR* 22(4): 977–1026**
  - https://onlinelibrary.wiley.com/doi/abs/10.1506/7XMH-QQ74-L6GG-CJRX ；https://ideas.repec.org/a/wly/coacre/v22y2005i4p977-1026.html
  - 【事實 A】研發費用化不會在公司一生中都是保守的：偏誤由「研發成長 vs 盈餘成長」與「研發成長 vs 資本報酬率」決定。研發成長高於獲利能力的公司（多為生命週期早期）報告**偏保守**，研發成長低的成熟公司報告**偏激進**。1972–2003 年資料顯示，投資人固著於報告獲利：保守報告的公司被低估、激進報告的被高估，偏誤反轉時錯誤定價隨之修正。
  - **含意（推論）**：對 P/E 模型非常關鍵。研發成長放緩的成熟科技股，GAAP EPS 會**虛高**，P/E 看起來便宜其實不便宜；研發加速的公司則相反。模型應該放「研發成長率 − 盈餘成長率」這個變數。
- **Amir & Lev (1996), *JAE* 22: 3–30**（行動通訊業）
  - https://econpapers.repec.org/RePEc:eee:jaecon:v:22:y:1996:i:1-3:p:3-30
  - 【事實 A】單獨看時，盈餘、帳面淨值、現金流對股價**大致無關**；非財務指標（POPS、市場滲透率）高度相關；但和非財務資訊合併後，盈餘仍有貢獻。
- **Trueman, Wong & Zhang (2000) "The Eyeballs Have It", *JAR* 38(Suppl.): 137–162**
  - 【事實 B】63 家網路公司：淨利與股價**無正相關（甚至顯著負相關）**；拆解後毛利有價值關聯；網路流量與股價正相關。轉述來源：https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf
- **Bartov, Mohanram & Seethamraju (2002) "Valuation of Internet Stocks—An IPO Perspective", *JAR* 40(2): 321–346**
  - https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.00050 ；https://ideas.repec.org/a/bla/joares/v40y2002i2p321-346.html
  - 【事實 A】非網路公司符合傳統：正的盈餘與現金流被定價，負的不被定價。**網路公司則是盈餘不被定價**，負的現金流被定價，可能因為被視為投資。
- **Darrough & Ye (2007) "Valuation of Loss Firms in a Knowledge-Based Economy", *RAST* 12: 61–93**
  - https://link.springer.com/article/10.1007/s11142-006-9022-z
  - 【事實 B】虧損公司的研發支出有正的評價乘數。

**反面證據（重要）**
- **Collins, Maydew & Weiss (1997), *JAE* 24(1): 39–67**：https://ideas.repec.org/a/eee/jaecon/v24y1997i1p39-67.html
  - 【事實 A／B】盈餘＋帳面淨值的**合計**價值攸關性過去 40 年沒有下降，甚至略升，只是從盈餘轉移到帳面淨值。轉述文獻說他們發現無形密集產業的價值攸關性和非密集產業一樣高 [B]。
- **Core, Guay & Van Buskirk (2003) "Market Valuations in the New Economy", *JAE* 34(1–3): 43–67**：https://repository.upenn.edu/accounting_papers/128/
  - 【事實 A】新經濟期間各子樣本的迴歸解釋力**都**下降，但模型結構（係數）和其他期間相比**並不異常**。
- **Barth, Li & McClure (2023) "Evolution in Value Relevance of Accounting Information", *TAR* 98(1): 1–28**：https://publications.aaahq.org/accounting-review/article-abstract/98/1/1/378/Evolution-in-Value-Relevance-of-Accounting
  - 【事實 A】納入更多會計項目後，1962–2014 年合計價值攸關性**沒有下降**；與無形資產、成長機會、替代績效指標有關的項目，攸關性反而上升。
- **Wallis (2026) "Has Accounting Really Lost Its Value Relevance?", *Accounting & Finance* 66(1): 3–23**：https://onlinelibrary.wiley.com/doi/10.1111/acfi.70127
  - 【事實 A】「價值攸關性下降」對合理的方法變化不穩健，主要取決於樣本期間選擇。但**年輕公司**等子群的攸關性較低且在下降，只是它們占美股比例越來越小。
- **推論**：「會計已死」對整體市場是誇大的；但對**年輕、虧損、無形密集**的科技股確實成立。KIWI 模型應**依公司類型切換輸入**：成熟、獲利的大型科技股可以用 EPS；年輕、虧損股不行。

### 4.4 股權報酬（SBC）對 EPS 與估值的影響
- **Core, Guay & Kothari (2002) "The Economic Dilution of Employee Stock Options: Diluted EPS for Valuation and Financial Reporting", *TAR* 77(3): 627–652**
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=183068 ；http://www.mit.edu/~kothari/attach/CGK%20May%202001.pdf
  - 【事實 A／B】FASB 庫藏股法用內含價值計算選擇權稀釋，**低估經濟稀釋**。731 個員工選擇權計畫的資料中，他們提出的稀釋衡量平均比報告的稀釋 EPS **大 100%**（另一說法「低估近 50%」，兩者其實一致：真實稀釋＝報告值 2 倍）。
- **Mohanram, White & Zhao (2020) "Stock-Based Compensation, Financial Analysts, and Equity Overvaluation", *RAST* 25: 1040–1077**
  - https://link.springer.com/article/10.1007/s11142-020-09541-0 ；摘要轉述 https://www.fjrg.johnson.cornell.edu/2021/07/07/stock-based-compensation-financial-analysts-and-equity-overvaluation/
  - 【事實 A】SBC 高的公司評價倍數較高、未來報酬較低，顯示被高估。分析師在 DCF 中常忽略 SBC；忽略 SBC 的分析師目標價偏樂觀，把 SBC 當費用的分析師平均無偏。
  - 【事實 B】高 SBC 樣本中，忽略 SBC 的分析師目標價隱含報酬約樂觀 **9%**。
- **Bhojraj (2020) "Stock Compensation Expense, Cash Flows, and Inflated Valuations", *RAST* 25: 1078–1097**
  - https://link.springer.com/article/10.1007/s11142-020-09549-6
  - 【事實 A】現金流量表把 SBC 當非現金項目會誤導估值，建議改成「營業現金流出＋籌資現金流入」。
- **Griffin & McInnis (2025) "Gone but Not Forgotten: Investor Reaction to 'Excluded' Recurring Expenses", *JAE* 80(1)**（反面）
  - https://www.sciencedirect.com/science/article/abs/pii/S0165410125000357
  - 【事實 A】盈餘公告短窗口內，不論公司是否在非 GAAP 中排除 SBC／收購無形攤銷，投資人對意外 SBC 的反應都差不多；在排除者中，**含 SBC 的盈餘反而更能解釋市場反應**。
  - 【事實 B（新聞稿）】意外 SBC 增加時，短期報酬低 1–2 個百分點；排除 SBC 的公司沒有得到更高估值。https://phys.org/news/2025-10-companies-omit-stock-based-compensation.html
- **推論**：
  - 兩派證據不完全矛盾：**公告當下**市場有扣 SBC（Griffin-McInnis），但**長期**高 SBC 公司仍偏高估（Mohanram et al.）。
  - KIWI 模型的 EPS 一律用 **GAAP 稀釋 EPS（含 SBC）**，這和 `target_price.py` 現行的 GAAP 稀釋口徑一致；分析師的非 GAAP 共識要先扣回 SBC 才能輸入。

---

## 5. 各估值模型的準確度比較，以及在高成長樣本的表現

### 5.1 經典賽馬（全樣本）
- **Penman & Sougiannis (1998) "A Comparison of Dividend, Cash Flow, and Earnings Approaches to Equity Valuation", *CAR* 15(3): 343–383**
  - https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1911-3846.1998.tb00564.x ；https://business.columbia.edu/faculty/research/comparison-dividend-cash-flow-and-earnings-approaches-equity-valuation
  - 【事實 A】方法：用事後實現的平均 payoff，在不同預測期、有無終值下估值，再和事前市價比較。**應計盈餘法的誤差低於現金流與股利折現法**。
  - 【事實 B】**RIM 在 P/E 與 P/B 高的公司表現不好**，因為這些公司的終值成長率貢獻很大；文中的分組指出 GAAP 會計在哪些情況表現較好或較差。轉述來源：Penman "Valuation Models: An Issue of Accounting Theory" https://business.columbia.edu/sites/default/files-efs/pubfiles/6208/Valuation%20Models%20Routledge.pdf
  - **含意**：科技成長股正好是高 P/E、高 P/B 那一組，RIM 的「全樣本最準」**不能直接外推**過來。
- **Francis, Olsson & Oswald (2000), *JAR* 38(1): 45–70**
  - https://ideas.repec.org/a/bla/joares/v38y2000i1p45-70.html
  - 【事實 A】比較股利、自由現金流、異常盈餘（AE）三種模型的價值估計，**AE 的準確度與解釋力都較好**。
  - 【不確定】高研發／高成長子樣本的結果：**查無**。
- **Courteau, Kao & Richardson (2001), *CAR* 18(4): 625–661**
  - https://onlinelibrary.wiley.com/doi/10.1506/77TK-1N3Q-82QU-UATR ；https://ideas.repec.org/a/wly/coacre/v18y2001i4p625-661.html
  - 【事實 A】用 Penman 的「理想」終值時，5 年期 DCF 與 RIM 在實證上等價。終值改用 Value Line 預測股價的模型誤差最小，價格基礎模型大幅勝過任意成長率假設的非價格模型；非價格終值下 RIM 勝過 DCF。
  - **含意（推論）**：準確度主要來自**終值**。對科技股，「5 年後的倍數」就是整個問題的核心，這正好是 KIWI 模型要預測的東西。所以應該把「終值倍數」當成獨立的子模型，例如以同業成熟公司的 P/E 分布為終點，而不是用永續成長率。
- **Lundholm & O'Keefe (2001), *CAR* 18(2): 311–335**
  - https://ideas.repec.org/a/wly/coacre/v18y2001i2p311-335.html
  - 【事實 A】正確實作時，DCF 與 RIM 對所有公司、所有年度給出**完全相同**的價值。過去的準確度比較其實是在比「不一致的假設」，比較本身是誤導的。
  - **反面意義**：「哪個模型比較準」本身是錯的問題，該問的是「哪組終值與衰退假設比較準」。
- **Dechow, Hutton & Sloan (1999), *JAE* 26: 1–34**
  - https://ideas.repec.org/a/eee/jaecon/v26y1999i1-3p1-34.html
  - 【事實 A】Ohlson 模型的實證實作，比「把短期盈餘預估資本化成永續」的做法**只有小幅改善**；資訊動態（剩餘收益持續性 ω）大致獲得支持。
  - 【不確定】「ω≈0.62」：搜尋摘要沒有確認，不引用。
- **Sougiannis & Yaekura (2001), *JAAF* 16(4): 331–362**
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=279204
  - 【事實 A】4 年分析師預估下，「有終值（剩餘收益以固定率成長）的 RIM」平均表現最好，但只在 **48%** 的公司比其他模型準。

### 5.2 PEG、AEG、隱含報酬率
- **Easton (2004) "PE Ratios, PEG Ratios, and Estimating the Implied Expected Rate of Return on Equity Capital", *TAR* 79(1): 73–95**
  - https://publications.aaahq.org/accounting-review/article-abstract/79/1/73/2788/PE-Ratios-PEG-Ratios-and-Estimating-the-Implied ；SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=423601 ；延伸專書 https://care-mendoza.nd.edu/assets/152233/eastoncoc.pdf
  - 【事實 A】以盈餘與盈餘成長（異常成長 agr）建模，同時估計隱含預期報酬率和預測期後異常成長的變化率，用來精煉 PEG 排名。PEG 是「agr₂＝agr₃＝…（異常成長不再變化）」的特例。
  - 【事實 A】PEG 推出的報酬率和精煉估計高度相關，可作為簡約排名工具，**但 PEG 推出的預期報酬率偏低**。實證上估得的異常成長率常為負值。
  - 【事實 B】修正 PEG：P₀ ＝ (eps₂ ＋ r·dps₁ − eps₁) / r²；dps₁＝0 時，r_PEG ＝ √((eps₂ − eps₁)/P₀)。
  - **含意（推論）**：
    - PEG 只用到第 1→2 年的 EPS 增量，假設第 2 年後異常成長「不衰退」。科技股異常成長幾乎一定衰退（見 §7），所以 PEG 會**高估**持續高成長公司的合理 P/E。
    - Easton 的精煉法等於把「異常成長衰退率」設成可估參數，**正是科技股模型要的東西**。
- **Botosan & Plumlee (2005) "Assessing Alternative Proxies for the Expected Risk Premium", *TAR* 80: 21–53**
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=565001
  - 【事實 A】五種隱含報酬率代理（DIV、GLS、GOR、OJN、PEG）中，**DIV 與 PEG 和風險的關係一致且可預測**，其他不是，所以這兩者占優。
- **Gode & Mohanram (2003) "Inferring the Cost of Capital Using the Ohlson–Juettner Model", *RAST* 8: 399–431**
  - https://link.springer.com/article/10.1023/A:1027378728141
  - 【事實 A】OJ 隱含風險溢酬和 beta、特有風險、盈餘波動、槓桿方向一致；但作者結論是 GLS（剩餘收益型）優於 OJ。
- **Easton & Monahan (2005) "An Evaluation of Accounting-Based Measures of Expected Returns", *TAR* 80: 501–538**
  - 轉述來源：https://onlinelibrary.wiley.com/doi/10.1111/abac.12069
  - 【事實 B】控制現金流消息與折現率消息後，各種隱含報酬率對實現報酬的解釋力很差（7 個中有 4 個係數顯著為負）；**最簡單的 forward E/P 和複雜代理一樣可靠**。分析師預估可靠的情況是：**低成長預估、大公司、低 P/E、高 M/B**。
  - **含意（推論）**：反面訊號。高成長、高 P/E 的科技股正好是分析師預估**最不可靠**的區域，任何依賴 EPS 路徑的模型在這裡誤差最大。
- **Jorgensen, Lee & Yoo (2011), *JBFA* 38(3–4): 446–471**
  - https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-5957.2011.02241.x
  - 【事實 A】OJ（AEG）估值的準確度普遍不如 RIM；預測期從 2 年拉長到 5 年顯著改善但仍較低；差距來自預測期後的成長假設。
  - **含意（推論）**：如果用 AEG 處理帳面淨值很小的科技股（大量庫藏股），要至少 5 年明確 EPS 路徑，並審慎設定長期 γ。

### 5.3 分析師怎麼用估值模型，以及哪種做法比較準
- **Bradshaw (2004) "How Do Analysts Use Their Earnings Forecasts in Generating Stock Recommendations?", *TAR* 79(1): 25–50**
  - https://publications.aaahq.org/accounting-review/article-abstract/79/1/25/2737/How-Do-Analysts-Use-Their-Earnings-Forecasts-in ；https://www.jstor.org/stable/3203311
  - 【事實 A】分析師推薦和經驗法則（PEG、長期成長）的相關性高於現值模型；用分析師 EPS 預估做的現值模型，報酬比照推薦操作更高。
  - 【事實 B】1994–1998：推薦與 RIM 估值**負**相關、與 PEG／LTG 正相關；未來報酬與 RIM 估值**正**相關、與經驗法則負相關；分析師最推薦成長股，尤其是 PEG 價值高於股價的那些。轉述來源：https://care-mendoza.nd.edu/assets/152422/gleason_6_06.pdf
- **Gleason, Johnson & Li (2013) "Valuation Model Use and the Price Target Performance of Sell-Side Equity Analysts", *CAR* 30(1): 80–115**
  - https://www.researchgate.net/publication/228258257_Valuation_Model_Use_and_the_Price_Target_Performance_of_Sell-Side_Equity_Analysts
  - 【事實 A】控制 EPS 預估準確度後，看起來用 RIM 的分析師，12 個月目標價投資表現優於用 PEG 的；**但 EPS 預估不準時，這個優勢會縮小。**
  - **含意（推論）**：科技股 EPS 預估誤差大，RIM 對 PEG 的優勢會被侵蝕。換句話說，**輸入品質（EPS 路徑）比模型選擇更重要**。
- **Demirakos, Strong & Walker (2004) "What Valuation Models Do Analysts Use?", *Accounting Horizons* 18(4): 221–240**
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3479656
  - 【事實 A】26 家英國大型公司（飲料、電子、製藥）的 104 份報告：分析師的主要模型通常是 P/E 或多期 DCF；飲料業用同業比較較多，電子、製藥較少。
- **Demirakos, Strong & Walker (2010) "Does Valuation Model Choice Affect Target Price Accuracy?", *European Accounting Review* 19(1): 35–72**
  - https://www.researchgate.net/publication/227613789_Does_Valuation_Model_Choice_Affect_Target_Price_Accuracy
  - 【事實 B】DCF 目標價相對比 P/E 倍數準，但多數設定下差異不顯著，只有一個設定顯示 DCF 較佳。
- **Huang, Tan, Wang & Yu (2023) "Valuation Uncertainty and Analysts' Use of DCF Models", *RAST* 28: 827–861**
  - https://link.springer.com/article/10.1007/s11142-021-09658-w
  - 【事實 A】盈餘品質低、風險高（不確定性高）的公司，分析師更常用 DCF 並討論更多現金流與折現率資訊；市場對基於 DCF 的目標價變動反應更強，尤其是高不確定性公司。

### 5.4 倍數法的準確度（含 IPO／年輕公司）
- **Liu, Nissim & Thomas (2002) "Equity Valuation Using Multiples", *JAR* 40(1): 135–172**
  - https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00042 ；https://business.columbia.edu/sites/default/files-efs/pubfiles/318/Equity_Valuation_Using_Multiples.pdf
  - 【事實 A】forward EPS 倍數最好（約一半樣本誤差在 ±15% 內）＞歷史盈餘＞現金流＝帳面淨值＞營收（最差）；**排名在幾乎所有產業都一樣**，和「不同產業有不同最佳倍數」的流行看法相反。
  - **反面意義**：這是「科技股不需要專用模型」的最強證據之一。但注意它是「同業倍數的定價誤差」，衡量的是**橫斷面相對定價**，不是 12 個月後的 P/E 預測。
- **Kim & Ritter (1999) "Valuing IPOs", *JFE* 53(3): 409–437**
  - https://khu.elsevierpure.com/en/publications/valuing-ipos-2/
  - 【事實 A】用同業近期 IPO 倍數定價時，forward P/E 優於其他倍數，下一年 EPS 優於當年；**但整體只有中等解釋力**。
- **Bhojraj & Lee (2002) "Who Is My Peer?", *JAR* 40: 407–439**
  - https://www.researchgate.net/publication/227672139_Who_Is_My_Peer_A_Valuation-Based_Approach_to_the_Selection_of_Comparable_Firms
  - 【事實 A／B】用成長、獲利、風險等 8 個變數做迴歸，得到「應有倍數」（warranted multiple）來挑同業，解釋力明顯高於產業分類；**成長和（次要的）研發有增量解釋力**。

---

## 6. 成長股的基本面分析

### 6.1 Mohanram (2005) "Separating Winners from Losers among Low Book-to-Market Stocks using Financial Statement Analysis", *RAST* 10: 133–170
- 網址：https://link.springer.com/article/10.1007/s11142-005-1526-4 ；SSRN：https://ssrn.com/abstract=403180
- 【事實 A】GSCORE 結合傳統基本面（盈餘、現金流）和**成長股專用指標**（盈餘與成長的穩定性、研發／資本支出／廣告強度）。多空策略賺到顯著超額報酬；在規模、分析師追蹤、流動性分組下都穩健；控制動能、B/M、應計、規模後仍存在。高 GSCORE 公司之後的盈餘驚喜與市場反應較正面，表示市場沒有充分理解當期基本面的含意。
- 【事實 B（CXO Advisory 等二手）】八個訊號（都和產業中位數比）：G1 ROA、G2 現金流 ROA、G3 CFO＞淨利、G4 ROA 波動較低、G5 營收成長波動較低、G6 研發強度、G7 資本支出強度、G8 廣告強度。多 6–8 分、空 0–1 分的策略，形成後第 1、2 年平均原始報酬 8.2%、9.0%；經規模調整，**策略主要是在辨識大輸家而非贏家**。https://www.cxoadvisory.com/fundamental-valuation/classic-paper-mohanrams-efficient-growth-investing/
- **含意（推論）**：
  - 在 12 個月 P/E 預測中，GSCORE 類變數適合當「**倍數壓縮風險**」的指標：低 GSCORE 的高倍數股，倍數下修機率高。
  - 研發強度在 GSCORE 裡是**加分**項目，和「研發造成 EPS 低估」一致。

### 6.2 Penman & Reggiani：成長是有風險的
- Penman & Reggiani (2013) "Returns to Buying Earnings and Book Value: Accounting for Growth and Risk", *RAST* 18: 1021–1049：https://link.springer.com/article/10.1007/s11142-013-9226-y
  - 【事實 A】E/P 與 B/P 一起預測報酬，和理性風險定價一致。會計「遞延原則」帶來的預期盈餘成長是**有風險的**，伴隨較高平均報酬。
- Penman & Reggiani (2018) "Fundamentals of Value versus Growth Investing and an Explanation for the Value Trap", *FAJ* 74(4): 103–119：https://rpc.cfainstitute.org/research/financial-analysts-journal/2018/ip-v3-n1-16-explaining-value-vs-growth-investing
  - 【事實 A】在相同 E/P 下，高 B/P 表示較高但有風險的預期成長，和「低 B/P＝成長且低風險」的慣例相反。
- Penman (2016) "Valuation: Accounting for Risk and the Expected Return", *Abacus* 52(1): 106–130：https://onlinelibrary.wiley.com/doi/10.1111/abac.12067
  - 【事實 A】主張要理解「以風險為由遞延收入」的會計原則如何產生與風險評估有關的資訊。
- **含意（推論）**：在 Penman 的框架裡，「高 P/E 來自研發費用化（遞延）」本身就是風險訊號。科技股的折現率不應因為「大型、穩定」就壓低；EPS 成長越依賴遞延，r 應越高。

---

## 7. 科技股的盈餘成長／ROE 衰減速度（fade rate）

| 研究 | 樣本 | 衰減證據 | 等級 |
|---|---|---|---|
| Fama & French (2000) "Forecasting Profitability and Earnings", *J. Business* 73(2): 161–175 https://www.jstor.org/stable/10.1086/209638 | 美股 1964–1996 | 簡單部分調整模型下獲利能力均值回歸約 **38%/年**；獲利低於平均時、離平均越遠時回歸越快（非線性） | [A] |
| Nissim & Penman (2001), *RAST* 6: 109–154 http://www.columbia.edu/~dn75/Ratio_analysis_and_equity_valuation_From_research_to_practice.pdf | 美股 | 給出剩餘收益驅動因子的典型 fade 型態；ROE 離長期水準越遠回歸越快；**5 年後 ROE 排名仍和基期相似**（沒有完全回歸） | [A]／[B] |
| Chan, Karceski & Lakonishok (2003) "The Level and Persistence of Growth Rates", *JF* 58(2): 643–684 https://ideas.repec.org/a/bla/jfinan/v58y2003i2p643-684.html ；NBER https://www.nber.org/papers/w8282 | 美股 | **長期盈餘成長沒有超出機率的持續性**；IBES 成長預估中位數約 **14.5%**，實現 5 年成長中位數約 **9%**；IBES 前後五分位的預估差 16.4%，實現差只有 7.5%；**營收成長比盈餘成長更穩定、更持續** | [A]（數字 [B]） |
| Anagnostopoulou & Levis (2008) "R&D and Performance Persistence: Evidence from the UK", *Int. J. Accounting* 43(3): 293–320 https://ideas.repec.org/a/eee/accoun/v43y2008i3p293-320.html | 英國 1990–2003 | 研發強度和**持續的營收、毛利成長**有關，但**只在因產業需要而從事研發的公司**；高研發公司的超額報酬也較持續 | [A] |
| Pástor & Veronesi (2003) | 美股 | M/B 隨公司年齡下降，年輕公司下降更陡（不確定性被學習消除） | [A] |
| Wiggins & Ruefli (2005) "Schumpeter's Ghost", *Strategic Management Journal* 26(10): 887–911 https://digitalcommons.memphis.edu/facpubs/12059/ | 跨產業 | 持續超額績效的期間**隨時間縮短**，而且**不限於高科技業** | [A] |
| La Porta (1996), *JF* 51: 1715–1742 https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1996.tb05223.x ；Bordalo-Gennaioli-La Porta-Shleifer (2019), *JF* 74(6): 2839–2874 https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12833 | 美股 | 長期成長預估最樂觀的股票未來報酬較低；原因是分析師對消息過度反應（代表性捷思） | [A] |
| **反面**：Tengulov, Zechner & Zwiebel (2025 e-pub) "Valuation and Long-Term Growth Expectations", *JFQA* https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/valuation-and-longterm-growth-expectations/677A63FF27B758BBE12BD6C008B0A97C | 美股 | 以公司、產業、市場特徵估計長期成長；**市價沒有完全反映長期成長資訊**，預期長期成長高的公司有顯著**正**超額報酬 | [A] |
| Beaver & Morse (1978) "What Determines Price-Earnings Ratios?", *FAJ* 34(4): 65–76（CFA 重印 http://efinance.org.cn/cn/fm/What%20Determines%20Price-Earnings%20Ratios.pdf ） | 美股 | P/E 組合間的差異可持續到 14 年，但成長差異 2–3 年內就消散 | [A]／[B] |

- 【查無】**專門針對「科技股」估計 ROE 或盈餘成長 fade rate 的論文**：沒有找到可信的一手研究。上表只有 Anagnostopoulou-Levis（研發密集）和 PV 2003（年輕公司）跟科技特性直接相關。
- 【推論・已驗算】換算：38%/年的回歸對應持續性 φ＝0.62，超額獲利半衰期約 **1.45 年**；φ＝0.7 → 1.94 年；φ＝0.8 → 3.11 年。Ohlson LIM 的剩餘收益永續乘數 ω/(1+r−ω)（r=9%）：ω=0.62 → 1.32；0.8 → 2.76；0.9 → 4.74。**ω 從 0.62 改成 0.9，終值裡剩餘收益的價值就變成 3.6 倍**，所以科技股的估值幾乎就是「你相信 ω 是多少」。
- 【推論・已驗算】若照 CKL 的「預估 14.5% vs 實現 9%」，5 年後實際 EPS 約只有預估路徑的 **78%**。使用者給的 EPS 路徑若來自分析師共識，應該有系統性折減的選項。
- **含意（推論）**：
  - 科技股不應直接套全市場的 38%/年；研發密集、平台型公司的**營收**持續性可能較高（CKL、Anagnostopoulou-Levis）。
  - 但**盈餘成長**仍無持續性（CKL），分析師也系統性樂觀（La Porta、BGLS）。
  - 最穩健的做法是：營收用較慢的衰減，利潤率用較快的均值回歸，EPS 由兩者組合出來，而不是直接讓 EPS 成長率衰減。

---

## 8. 反面證據匯總（模型在全樣本好、在科技股差，或主流看法有反例）

1. **RIM 全樣本最準，但在高 P/E、高 P/B 公司表現差**（Penman-Sougiannis 1998 [B]）；AEG 又比 RIM 差（Jorgensen et al. 2011 [A]）。→ 科技股上沒有「已證明最準」的會計模型。
2. **用 RIM 的分析師目標價較好，但 EPS 預估不準時優勢縮小**（Gleason et al. 2013 [A]）。科技股正好 EPS 預估最不準（Easton-Monahan 2005 [B]）。
3. **網路／年輕公司的盈餘不被定價**（Bartov et al. 2002 [A]；Trueman et al. 2000 [B]；Amir-Lev 1996 [A]；Srivastava 2023 [A]）→ 任何 P/E 模型在這群股票上失效。
4. **反主流：會計攸關性整體沒有下降**（Collins et al. 1997；Barth-Li-McClure 2023；Wallis 2026 [A]）；新經濟期間迴歸結構也不異常（Core et al. 2003 [A]）→ 對成熟、獲利的大型科技股，EPS 基礎模型仍然可用。
5. **反主流：研發平均沒有被錯誤定價**（Chan-Lakonishok-Sougiannis 2001 [A]），只在「研發/市值高、過去表現差」的子集被低估。
6. **不確定性能否合理化高估值，兩派結論相反**：Pástor-Veronesi 2006 認為 Nasdaq 高峰在合理不確定性下說得通 [A]；Schwartz-Moon 2000 自己的模型卻判定 Amazon 被高估、要符合市價需要不切實際的營收分布 [B]。
7. **長期成長預估：La Porta 1996／BGLS 2019 說高 LTG 之後報酬低；Tengulov-Zechner-Zwiebel 2025 說模型估計的高長期成長之後報酬高** [A]。差別可能在「分析師 LTG」vs「以特徵估計的 LTG」。
8. **倍數排名不分產業**（Liu-Nissim-Thomas 2002 [A]）→ 反對「科技股需要專用倍數」。
9. **SBC：短窗口市場有扣（Griffin-McInnis 2025），長期高 SBC 公司仍偏高估（Mohanram et al. 2020）** [A]。
10. **研發比資本支出更增加盈餘波動，但可能只在研發密集產業成立**（Kothari et al. 2002 vs Amir et al. 2007 [B]）。
11. **模型賽馬本身可能是假議題**（Lundholm-O'Keefe 2001 [A]）：一致實作下 DCF＝RIM，差異全來自終值與假設。
12. **持續超額績效期間縮短不限於高科技業**（Wiggins-Ruefli 2005 [A]）→ 「科技股 fade 特別快」沒有直接證據。

---

## 9. 對 KIWI 科技股 P/E 模型的含意與建議規格（推論）

### 9.1 為什麼選這個骨架
- **選 Ohlson RIM／OJ AEG 當主體**：
  - 全樣本準確度證據最多（PS 1998、FOO 2000、CKR 2001、JLY 2011）。
  - 不受配息政策影響（處理 ⑤）。
  - P/E 可以直接導出，也能吃使用者給的 EPS 路徑。
  - 帳面淨值因大量買回而變小或為負時，改用 AEG（只需 EPS）。
- **加 Pástor-Veronesi 的兩個結構**：
  - 超額獲利只維持有限期 T，之後回歸（處理 ①）。
  - 對 EPS 路徑取分布而非點值，保留凸性溢價（處理 ③）。
- **輸入用 GAAP 稀釋 EPS（含 SBC）**（處理 ⑥）。另外算一版「研發資本化後 EPS」（Lev-Sougiannis、Damodaran），兩版 P/E 的差距本身就是資訊（處理 ②）。
- **EPS ≤ 0 時停用 P/E**：改用 Schwartz-Moon 精簡版（營收成長＋利潤率回歸），或 EV/Sales 同業法（處理 ④）。Klobucnik-Sievers 顯示兩者準確度相當。
- **基準與驗證**：以 forward P/E 同業倍數當 benchmark（LNT 2002、Kim-Ritter 1999）。新模型若贏不過「同業 forward P/E 中位數 × 使用者 EPS」，就沒有存在價值。

### 9.2 草擬公式（推論，非任何論文原式）
- 價值（t=1，也就是 12 個月後的時點）：
  V₁ ＝ B₁ ＋ Σ_{t=2}^{N} (EPS_t − r·B_{t−1})/(1+r)^{t−1} ＋ [ω·RI_N /(1+r−ω)]/(1+r)^{N−1}
  - B_t ＝ B_{t−1} ＋ EPS_t − DPS_t（clean surplus；買回要另外扣）。
  - RI_t ＝ EPS_t − r·B_{t−1}；ω＝剩餘收益持續性（全市場基準可從 Fama-French 38%/年 → ω≈0.62 出發，研發密集／平台公司可以讓資料決定是否較高）。
- 12 個月後本益比：P/E₁₂ ＝ V₁ / EPS₂（forward 口徑），或 V₁ / EPS₁（trailing 口徑）。
- 不確定性：對 EPS 路徑做 K 組情境（或對成長率 g_t ~ 均值回歸＋波動 σ_t，σ_t 隨時間遞減，借 Schwartz-Moon 結構）模擬，取 E[V₁]，**不要**用 V₁(E[EPS])。
- 折現率 r：不要因「大型、穩定」而壓低；遞延程度（研發/營收、SBC/營收）越高，r 越高（Penman-Reggiani）。

### 9.3 建議的狀態變數（給 12 個月倍數變化子模型）
| 變數 | 方向（推論） | 文獻依據 |
|---|---|---|
| 上市年數、是否配息 | 越年輕、不配息 → 倍數越高，但下降越快 | PV 2003 |
| 研發成長率 − 盈餘成長率 | 正 → GAAP EPS 偏保守 → 倍數被低估；負 → 偏激進 → 高估 | Lev-Sarath-Sougiannis 2005 |
| 研發/市值 | 高（且過去報酬差）→ 倍數擴張機率高 | Chan-Lakonishok-Sougiannis 2001 |
| SBC/營收 | 高 → 長期偏高估 | Mohanram-White-Zhao 2020 |
| GSCORE（或其中的盈餘、營收成長穩定性） | 低 → 倍數壓縮風險高 | Mohanram 2005 |
| 分析師 LTG 的極端程度 | 越極端越可能過度反應 | La Porta 1996、BGLS 2019（反面：TZZ 2025） |
| EPS ≤ 0 或毛利主導 | 切換到營收模型 | BMS 2002、TWZ 2000、Srivastava 2023 |

### 9.4 預期準確度（管理期望）
- 科技股的估值誤差量級：EV/Sales 中位數約 59%（Klobucnik-Sievers [B]）。全市場 forward P/E 約一半樣本 ±15%（LNT [A]），科技股大概落在兩者之間（推論，**未經驗證**）。
- 12 個月股價區間應該輸出**分布**（例如 10/50/90 分位），而且**區間寬度要隨不確定性代理變數放大**。

---

## 10. 查無／不確定清單

- 【查無】科技股專用、以 P/E 為輸出的學術理論。
- 【查無】Francis-Olsson-Oswald 2000、Courteau-Kao-Richardson 2001、Penman-Sougiannis 1998 在**高研發子樣本**的具體誤差數字。
- 【查無】專門估計科技股 ROE／盈餘成長 fade rate 的一手論文（只有研發密集與年輕公司的間接證據）。
- 【不確定 C】Schwartz-Moon 的「初始成長率 ±10% → 估值偏差 35%」「3.53%」等數字：出處不明。
- 【不確定 B】Pástor-Veronesi 2006 的 6.85、12.79%、4.86%、E(T)=20 年：工作論文搜尋片段，期刊版可能不同。
- 【不確定】Dechow-Hutton-Sloan 的 ω 估計值（常被引為約 0.62）：本次搜尋未確認，不引用。
- 【不確定 B】Lev-Gu 2016 的 R² 數字（80–90% → 約一半）、Mohanram GSCORE 的報酬數字：都是書評或部落格轉述。
- 【不確定 B】Chan-Lakonishok-Sougiannis 的 6.12%、2.45%：NBER 工作論文版片段，期刊版可能不同。

---

## 11. 來源清單（全部查詢於 2026-10-06；全部「只看到摘要」）

| # | 文獻 | 主要網址 |
|---|---|---|
| 1 | Pástor & Veronesi 2003 JF | https://onlinelibrary.wiley.com/doi/10.1111/1540-6261.00587 |
| 2 | Pástor & Veronesi 2006 JFE | https://www.sciencedirect.com/science/article/abs/pii/S0304405X05002163 ；https://conference.nber.org/confer/2004/apf04/pastor.pdf |
| 3 | Pástor & Veronesi 2009 AER | https://www.aeaweb.org/articles?id=10.1257%2Faer.99.4.1451 |
| 4 | Pástor & Veronesi 2009 綜述 | https://www.sfu.ca/~kkasa/Pastor_Veronesi_09.pdf |
| 5 | Schwartz & Moon 2000 FAJ | https://www.semanticscholar.org/paper/Rational-Pricing-of-Internet-Companies-Schwartz-Moon/307a120148f0546f7413f698bc4fe48611c36959 |
| 6 | Schwartz & Moon 2001 FR | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6288.2001.tb00027.x |
| 7 | Klobucnik & Sievers 2013 JBE | https://link.springer.com/article/10.1007/s11573-013-0684-2 |
| 8 | Damodaran 2009 young/growth | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1418687 |
| 9 | Damodaran R&D／無形資產 | https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/R_D.pdf ；https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/intangibles.pdf |
| 10 | Lev & Sougiannis 1996 JAE | https://experts.illinois.edu/en/publications/the-capitalization-amortization-and-value-relevance-of-rampd/ |
| 11 | Chan, Lakonishok & Sougiannis 2001 JF | https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00411 ；https://www.nber.org/papers/w7223 |
| 12 | Lev & Zarowin 1999 JAR | https://cris.tau.ac.il/en/publications/the-boundaries-of-financial-reporting-and-how-to-extend-them |
| 13 | Lev & Gu 2016（書評） | https://rpc.cfainstitute.org/research/financial-analysts-journal/2016/the-end-of-accounting-and-the-path-forward |
| 14 | Lev 2018 ABR | https://www.tandfonline.com/doi/pdf/10.1080/00014788.2018.1470138 |
| 15 | Kothari, Laguerre & Leone 2002 RAST | https://link.springer.com/article/10.1023/A:1020764227390 |
| 16 | Amir, Guan & Livne 2007 JBFA | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-5957.2006.00651.x |
| 17 | Penman & Zhang 2002 TAR | https://business.columbia.edu/faculty/research/accounting-conservatism-quality-earnings-and-stock-returns |
| 18 | Lev, Sarath & Sougiannis 2005 CAR | https://onlinelibrary.wiley.com/doi/abs/10.1506/7XMH-QQ74-L6GG-CJRX |
| 19 | Srivastava 2014 JAE | https://ideas.repec.org/a/eee/jaecon/v57y2014i2p196-217.html |
| 20 | Srivastava 2023 RAST | https://link.springer.com/article/10.1007/s11142-023-09794-5 |
| 21 | Enache & Srivastava 2018 MS | https://dl.acm.org/doi/abs/10.5555/3272525.3272550 |
| 22 | Allen, Lewis-Western & Valentine 2026 RAST | https://link.springer.com/article/10.1007/s11142-026-09966-z |
| 23 | Amir & Lev 1996 JAE | https://econpapers.repec.org/RePEc:eee:jaecon:v:22:y:1996:i:1-3:p:3-30 |
| 24 | Trueman, Wong & Zhang 2000（轉述） | https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf |
| 25 | Bartov, Mohanram & Seethamraju 2002 JAR | https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.00050 |
| 26 | Darrough & Ye 2007 RAST | https://link.springer.com/article/10.1007/s11142-006-9022-z |
| 27 | Collins, Maydew & Weiss 1997 JAE | https://ideas.repec.org/a/eee/jaecon/v24y1997i1p39-67.html |
| 28 | Core, Guay & Van Buskirk 2003 JAE | https://repository.upenn.edu/accounting_papers/128/ |
| 29 | Barth, Li & McClure 2023 TAR | https://publications.aaahq.org/accounting-review/article-abstract/98/1/1/378/Evolution-in-Value-Relevance-of-Accounting |
| 30 | Wallis 2026 A&F | https://onlinelibrary.wiley.com/doi/10.1111/acfi.70127 |
| 31 | Core, Guay & Kothari 2002 TAR | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=183068 |
| 32 | Mohanram, White & Zhao 2020 RAST | https://link.springer.com/article/10.1007/s11142-020-09541-0 |
| 33 | Bhojraj 2020 RAST | https://link.springer.com/article/10.1007/s11142-020-09549-6 |
| 34 | Griffin & McInnis 2025 JAE | https://www.sciencedirect.com/science/article/abs/pii/S0165410125000357 |
| 35 | Penman & Sougiannis 1998 CAR | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1911-3846.1998.tb00564.x |
| 36 | Francis, Olsson & Oswald 2000 JAR | https://ideas.repec.org/a/bla/joares/v38y2000i1p45-70.html |
| 37 | Courteau, Kao & Richardson 2001 CAR | https://onlinelibrary.wiley.com/doi/10.1506/77TK-1N3Q-82QU-UATR |
| 38 | Lundholm & O'Keefe 2001 CAR | https://ideas.repec.org/a/wly/coacre/v18y2001i2p311-335.html |
| 39 | Dechow, Hutton & Sloan 1999 JAE | https://ideas.repec.org/a/eee/jaecon/v26y1999i1-3p1-34.html |
| 40 | Sougiannis & Yaekura 2001 JAAF | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=279204 |
| 41 | Easton 2004 TAR | https://publications.aaahq.org/accounting-review/article-abstract/79/1/73/2788/PE-Ratios-PEG-Ratios-and-Estimating-the-Implied |
| 42 | Botosan & Plumlee 2005 TAR | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=565001 |
| 43 | Gode & Mohanram 2003 RAST | https://link.springer.com/article/10.1023/A:1027378728141 |
| 44 | Easton & Monahan 2005（轉述） | https://onlinelibrary.wiley.com/doi/10.1111/abac.12069 |
| 45 | Jorgensen, Lee & Yoo 2011 JBFA | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-5957.2011.02241.x |
| 46 | Bradshaw 2004 TAR | https://publications.aaahq.org/accounting-review/article-abstract/79/1/25/2737/How-Do-Analysts-Use-Their-Earnings-Forecasts-in |
| 47 | Gleason, Johnson & Li 2013 CAR | https://www.researchgate.net/publication/228258257_Valuation_Model_Use_and_the_Price_Target_Performance_of_Sell-Side_Equity_Analysts |
| 48 | Demirakos, Strong & Walker 2004 AH | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3479656 |
| 49 | Demirakos, Strong & Walker 2010 EAR | https://www.researchgate.net/publication/227613789_Does_Valuation_Model_Choice_Affect_Target_Price_Accuracy |
| 50 | Huang, Tan, Wang & Yu 2023 RAST | https://link.springer.com/article/10.1007/s11142-021-09658-w |
| 51 | Liu, Nissim & Thomas 2002 JAR | https://onlinelibrary.wiley.com/doi/abs/10.1111/1475-679X.00042 |
| 52 | Kim & Ritter 1999 JFE | https://khu.elsevierpure.com/en/publications/valuing-ipos-2/ |
| 53 | Bhojraj & Lee 2002 JAR | https://www.researchgate.net/publication/227672139_Who_Is_My_Peer_A_Valuation-Based_Approach_to_the_Selection_of_Comparable_Firms |
| 54 | Mohanram 2005 RAST | https://link.springer.com/article/10.1007/s11142-005-1526-4 |
| 55 | Penman & Reggiani 2013 RAST | https://link.springer.com/article/10.1007/s11142-013-9226-y |
| 56 | Penman & Reggiani 2018 FAJ | https://rpc.cfainstitute.org/research/financial-analysts-journal/2018/ip-v3-n1-16-explaining-value-vs-growth-investing |
| 57 | Penman 2016 Abacus | https://onlinelibrary.wiley.com/doi/10.1111/abac.12067 |
| 58 | Fama & French 2000 JB | https://www.jstor.org/stable/10.1086/209638 |
| 59 | Nissim & Penman 2001 RAST | http://www.columbia.edu/~dn75/Ratio_analysis_and_equity_valuation_From_research_to_practice.pdf |
| 60 | Chan, Karceski & Lakonishok 2003 JF | https://ideas.repec.org/a/bla/jfinan/v58y2003i2p643-684.html |
| 61 | Anagnostopoulou & Levis 2008 IJA | https://ideas.repec.org/a/eee/accoun/v43y2008i3p293-320.html |
| 62 | Wiggins & Ruefli 2005 SMJ | https://digitalcommons.memphis.edu/facpubs/12059/ |
| 63 | La Porta 1996 JF | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1996.tb05223.x |
| 64 | Bordalo et al. 2019 JF | https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12833 |
| 65 | Tengulov, Zechner & Zwiebel 2025 JFQA | https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/valuation-and-longterm-growth-expectations/677A63FF27B758BBE12BD6C008B0A97C |
| 66 | Beaver & Morse 1978 FAJ（重印） | http://efinance.org.cn/cn/fm/What%20Determines%20Price-Earnings%20Ratios.pdf |
| 67 | Ohlson & Juettner-Nauroth 2005 RAST | https://www.semanticscholar.org/paper/Expected-EPS-and-EPS-Growth-as-Determinants-of-By-Ohlson-Juettner-Nauroth/ef5d3128ca5b552169f37c843be62947912c6e20 |

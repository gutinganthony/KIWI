# 本益比（P/E）的學術推導：從實務起源到現代估值理論

> 用途：當作「預測個股 12 個月後本益比與股價」新模型的理論骨架。
> 查詢日期：所有網址皆於 **2026-10-01** 查詢。
> 作者：subagent 研究報告（僅用 WebSearch／WebFetch）。

---

## 0. 方法、限制與標記規則（先讀）

**重大限制（必讀）**：本 session 的 **WebFetch 對所有網域都被 egress proxy 擋下**（tandfonline、jstor、nber、ssrn、ideas.repec、pages.stern.nyu.edu、cfainstitute、wikipedia、arxiv、semanticscholar 都試過，全回 `EGRESS_BLOCKED`）。
因此：
- 所有「來源」都是透過 **WebSearch 的搜尋摘要**取得：我看得到網址和搜尋引擎摘出的段落，**沒有辦法打開原文 PDF 逐字核對**。
- 下文的網址都是搜尋結果中的真實公開頁面，一般瀏覽器應該能開；但「原文第幾頁、第幾式」我都沒有親眼核對過。
- 這次沒有任何一條可以算「我親自讀了原文」的一手核對。最高等級只到「期刊／出版社頁面＋摘要」。

**標記**：
- 【事實】＝有來源的摘要或書目支撐（附網址）。來源本身是二手（教材、部落格、引用文獻）時另標【二手】。
- 【推論】＝我依該模型的假設自己做的代數推導或整理。**所有推導公式都已用 Python 數值驗算**（腳本 `research/pe_check.py`、`research/cs_check.py`；結果見 §9）。
- 【不確定】＝查無、來源互相矛盾，或原文公式形式無法核對。

**統一符號**（推論，為了讓各理論可以互相比較）：
- P₀＝今日股價；E₀＝最近一期（trailing）盈餘；E₁＝下一期（forward）預期盈餘。
- D₁＝下一期股利；payout＝1−b，其中 b 是保留率（再投資率）。
- r（Gordon 寫成 k，MM 寫成 ρ）＝股東要求報酬率（權益資金成本）。
- g＝盈餘／股利的恆常成長率；ROE＝再投資的報酬率；B＝每股帳面價值。
- trailing P/E＝P₀/E₀；forward P/E＝P₀/E₁。兩者的關係是 P₀/E₀＝(P₀/E₁)(1+g)。

---

## 1. 實務起源：「times earnings」、Graham & Dodd、Molodovsky

### 1a. 「times earnings」與最早的盈餘殖利率資料
- 【事實】Cowles Commission 在 1938 年出版 *Common-Stock Indexes, 1871–1937*（Cowles Monograph No. 3，Principia Press），裡面有一個「Series R — Earnings-Price Ratios」，資料從 1871 年開始。
  https://cowles.yale.edu/research/cfm-31-common-stock-indexes-1871-1937 ；（Shiller 對 Cowles 盈餘資料的說明）http://www.econ.yale.edu/~shiller/data/chapt26.html
- 【不確定／查無】華爾街口語「N times earnings」最早是哪一年、出自何處：**查無**可靠的一手出處，不補年份。
- 本益比由什麼決定：這一階段只是**經驗倍數**，沒有理論。

### 1b. Graham & Dodd《Security Analysis》（1934，McGraw-Hill）
- 書目【事實】：Benjamin Graham & David L. Dodd，*Security Analysis*，1934 年初版（有 1934 年版重印本，ISBN 9780070244962）。
  https://books.google.com/books/about/Security_Analysis_The_Classic_1934_Editi.html?id=wXlrnZ1uqK0C
- 核心概念【事實／二手】：
  - **「earning power」**：一段多年的實際盈餘紀錄，加上「除非發生特殊情況，未來會大致重現」的合理預期。
    https://vinodp.com/documents/investing/security_analysis/chapter37.html （書中文字轉錄，二手）
  - **平均盈餘（正常化盈餘）**：把計算基準「從當期盈餘移到平均盈餘，期間不少於五年，最好七到十年」（"…average earnings, which should cover a period of not less than five years, preferably seven or ten years"）。
    https://www.evidenceinvestor.com/post/the-shiller-cape-10-how-to-use-it-not-abuse-it （二手引述）
  - **倍數上限**：「約 20 倍平均盈餘，是投資性買入普通股所能付的最高價格」。前景中性的一般公司應該付約 12–12.5 倍平均盈餘。
    https://www.hussmanfunds.com/wmc/wmc140915.htm ；https://hedgefundalpha.com/bull-market-a-warning-from-graham-and-dodd/ （二手）
  - 1929 年泡沫的批評：大眾從股利、資產、平均盈餘轉向只看「盈餘趨勢」。（同上二手來源）
- 【不確定】
  - 「20 倍」這句出自哪一版：上述二手來源沒寫是 1934 年初版還是後續版本。
  - 網路流傳的「16 倍」說法：**查無**來源支撐。
- 【事實／二手】廣為流傳的 V＝EPS×(8.5＋2g) 出自 1962 年（第 4 版）*Security Analysis*。但 Graham 自己對它有警告，提到它是為了說明成長預估不可靠。
  https://www.grahamvalue.com/article/understanding-benjamin-graham-formula-correctly ；https://www.gurufocus.com/news/192812/benjamin-grahams-misquoted-intrinsic-value-formula （二手）
- **公式**【推論整理】：
  - 規範性 P/Ē，其中 Ē＝過去 5–10 年平均 EPS。
  - 「合理」區間約 12–12.5 倍，投資上限約 20 倍（二手）。
  - 1962 年版：P/E_normal ≈ 8.5＋2g，g 以百分比的數字代入。
- **關鍵假設**：
  - 當期盈餘含有週期與一次性雜訊。
  - 「正常盈餘能力」才是估值基礎。
  - 倍數由分析師依品質與前景判斷，沒有明確的 r、g。
- **本益比由什麼決定（一句話）**：由**正常化（跨週期平均）的盈餘能力**，加上分析師對品質與前景的主觀倍數決定；當期盈餘偏離正常值會讓「表面 P/E」失真。

### 1c. Molodovsky（1953）"A Theory of Price-Earnings Ratios"
- 書目【事實】：Nicholas Molodovsky，*The Analysts Journal*（今 *Financial Analysts Journal*）Vol. 9, No. 5，頁 65–80，1953；DOI 10.2469/faj.v9.n5.65。同年同刊還有 "Some Aspects of Price-Earnings Ratios"（Vol. 9, No. 2）。
  https://www.tandfonline.com/doi/abs/10.2469/faj.v9.n5.65 ；https://www.tandfonline.com/doi/abs/10.2469/faj.v9.n2.65
- 【不確定】有一則二手摘要說這篇刊在 "January/February 1953"，和 DOI 的 No. 5 對不上（可能和 No. 2 那篇混淆了）。**以 DOI 為準。**
- 內容【二手】：
  - 「真正的投資價值永遠由未來股利與利率決定」。
    https://www.um.edu.mt/library/oar/bitstream/123456789/43161/1/An%20Analytical%20Approach%20to%20Comparing%20Actual%20Vs.%20Fundamental.pdf
  - 後人把「**Molodovsky effect**」歸給他：景氣谷底時盈餘被壓低，P/E 偏高；景氣頂部時盈餘偏高，P/E 偏低。解法是用跨週期正常化盈餘。
    https://corporatefinanceinstitute.com/resources/career-map/sell-side/capital-markets/molodovsky-effect/ ；https://breakingdownfinance.com/finance-topics/finance-basics/molodovsky-effect/ （教學網站，二手）
- 【不確定／查無】Molodovsky 原文的**具體公式**：查無，不補。
- **本益比由什麼決定**：由未來股利與利率決定。用當期盈餘算的 P/E 會因盈餘的**週期位置**而反向擺動，所以 P/E 含有「盈餘暫時性」的訊息（這點後來由 Penman 1996 形式化，見 §5e）。

---

## 2. 股利折現：Williams（1938）→ Gordon & Shapiro（1956）→ Gordon（1959/1962）

### 2a. John Burr Williams（1938）*The Theory of Investment Value*
- 書目【事實】：Harvard University Press，1938（Williams 的哈佛博士論文）。
  https://openlibrary.org/books/OL6369682M/The_theory_of_investment_value
- 核心主張【事實／二手】：
  - 股票的投資價值＝未來所有股利的現值。
  - 「Earnings are only a means to an end, and the means should not be mistaken for the end… a stock derives its value from its dividends, not its earnings.」
  - 「投資價值守恆律」（Law of the Conservation of Investment Value，書中第 72 頁）：企業價值與資本結構無關。
  - https://blogs.cfainstitute.org/investor/2012/08/03/dividend-investing-and-the-lasting-influence-of-john-burr-williams-the-theory-of-investment-value/ ；https://money.cnn.com/magazines/fortune/fortune_archive/2003/02/03/336460/index.htm ；https://www.mohammedamin.com/Reviews/The_theory_of_investment_value.html （二手）
- 公式：
  - 【二手】Williams 用的記號是 u＝1＋g、v＝1/(1＋i)，i 為利率。
    http://www.ftsmodules.com/public/texts/valuationtutor/VTChp6/topic3/topic3.htm
  - 【推論】V₀＝Σ_{t≥1} D_t·v^t。股利以 g 恆常成長時，V₀＝D₀·uv/(1−uv)＝D₀(1+g)/(i−g)。
  - 【不確定】這個恆常成長閉式解在書中的確切呈現形式（頁碼、式號）：未能核對。
- **P/E 形式**【推論】：
  - P₀/E₀＝Σ_t [payout_t × (E_t/E₀)] /(1+i)^t。
- **假設**：價值只來自分配給股東的現金；折現率已知且固定（書中是確定性框架）。
- **本益比由什麼決定**：由**未來每一期的派發率 × 盈餘相對於今天的成長路徑**，以及**折現率**決定。P/E 是「未來可分配現金流相對當期盈餘」的現值。

### 2b. Gordon & Shapiro（1956）
- 書目【事實】：Myron J. Gordon & Eli Shapiro，"Capital Equipment Analysis: The Required Rate of Profit"，*Management Science* 3(1)：102–110，1956 年 10 月；DOI 10.1287/mnsc.3.1.102。
  https://pubsonline.informs.org/doi/10.1287/mnsc.3.1.102 ；https://ideas.repec.org/a/inm/ormnsc/v3y1956i1p102-110.html
- 公式【二手】：**k＝D/P＋br**。k 是要求報酬率，b 是保留率，r 是保留盈餘的報酬率；成長率 g＝br。
  （搜尋摘要；另有 PDF 副本 https://psc.ky.gov/pscecf/2026-00099/allyson%40hloky.com/07072026110131/2026-00099_PSC_AG_DR_Set_1_No_161_Attachment_U.pdf ，未能開啟）
- 【推論】移項得 P＝D/(k−br)。
- 【不確定】原文 D 是 D₀ 還是 D₁ 的時間標註：未能核對。

### 2c. Gordon（1959）、Gordon（1962）
- 書目【事實】：
  - M. J. Gordon，"Dividends, Earnings, and Stock Prices"，*Review of Economics and Statistics* 41(2)：99–105，1959。
    https://www.semanticscholar.org/paper/Dividends,-Earnings,-and-Stock-Prices-Gordon/5c710c02f2e0d29aeeb5c7a6f3b04091dbf91d53 （PDF 副本 http://piketty.pse.ens.fr/files/Gordon1959.pdf ，未能開啟）
  - Gordon，*The Investment, Financing, and Valuation of the Corporation*，Irwin（Homewood, IL），1962。
    https://openlibrary.org/books/OL5851165M/The_investment_financing_and_valuation_of_the_corporation.
- 1959 年那篇的內容【事實／摘要】：用橫斷面資料檢驗投資人買股票時，付錢買的是（1）股利＋盈餘、（2）股利、（3）盈餘，這三種假說。
- 教材版公式【二手】：**P＝E(1−b)/(k−br)**，g＝br。
  - 假設：全權益、只用保留盈餘融資、r 與 k 固定、b 固定、公司永續、k > br。
  - https://efinancemanagement.com/dividend-decisions/gordons-theory-on-dividend-policy ；https://businessjargons.com/gordons-model.html
  - 【不確定】Gordon 1959 原文的方程式記號：未能核對。
- **推出的本益比公式**【推論，已數值驗算】：
  - forward：**P₀/E₁＝(1−b)/(r−g)**
  - trailing：**P₀/E₀＝(1−b)(1+g)/(r−g)**
  - 代入 g＝b·ROE（即 b＝g/ROE）：**P₀/E₁＝(1 − g/ROE)/(r − g)**
- **本益比由什麼決定**：由**r（折現率）、g（成長）、派發率**決定。等價地說，由 **r、g、ROE** 三者決定，因為派發率被 g/ROE 鎖住。
  - r−g 越小，P/E 對輸入越敏感（分母趨近 0）。【推論】

---

## 3. Miller & Modigliani（1961）：P＝E₁/r＋PVGO

- 書目【事實】：Merton H. Miller & Franco Modigliani，"Dividend Policy, Growth, and the Valuation of Shares"，*Journal of Business* 34(4)：411–433，1961 年 10 月；DOI 10.1086/294442。
  https://www.jstor.org/stable/2351143
- 主張【事實／二手】：
  - 在完美市場、理性行為、完全確定性下，股利政策不影響價值。
  - 他們推導出四種估值法：現金流折現、「當期盈餘＋未來投資機會」、股利流、盈餘流，並證明四者等價。
  - 「成長」的本質**不是擴張**，而是存在「以高於『正常』報酬率投資」的機會。
  - https://www.slideshare.net/slideshow/miller-modigliani-1961-dividend-policy-growth-and-the-valuation-of-shares/76665802 ；https://arxiv.org/pdf/2511.06274 （二手摘要）
- 公式：
  - 【二手】Mauboussin 轉述的 MM 形式（企業層級）：Value＝NOPAT/WACC＋I×(ROIC−WACC)×CAP/[WACC×(1+WACC)]。CAP 是競爭優勢期間。第一項是「steady-state value」，第二項是 PVGO。
    https://www.morganstanley.com/im/publication/insights/articles/article_theneglectedvaluedriver_ltr.pdf ；https://www.capatcolumbia.com/MM%20LMCM%20reports/MM%20on%20Valuation.pdf
  - 【不確定】MM 原文第 (12) 式的記號（X(0)/ρ、I(t)、ρ*(t) 等）：未能核對，**不引用記憶版本**。
- **權益版 P/E 拆解**【推論，已數值驗算】：
  - P₀＝E₁/r＋PVGO ⇒ **P₀/E₁＝1/r＋PVGO/E₁**。
  - 在 Gordon 的假設下（b、ROE 固定，g＝b·ROE）：**PVGO/E₁＝b(ROE−r)/[r(r−g)]**。
- 這說明（推論）：
  - ROE＝r 時，不論 b 多大，P/E 都＝1/r。數值驗算：r＝9%，b＝0／0.3／0.8，P/E 都是 11.11。
  - ROE > r 時，再投資越多，P/E 越高。
  - ROE < r 時，「成長」反而壓低 P/E。
- 【事實／二手】Ang & Zhang（2011）也用「no-growth value ＋ PVGO」拆解 P/E，見 §8。
- **本益比由什麼決定**：由 **1/r（無成長本益比）**，加上 **PVGO/E**，也就是**超額報酬幅度 (ROE−r) × 再投資規模 × 持續期間**決定。只有成長本身不會提高 P/E。

---

## 4. Leibowitz & Kogelman：Franchise Value（FAJ，1990 年代）

- 書目【事實】：
  - Martin L. Leibowitz & Stanley Kogelman，"Inside the P/E Ratio: The Franchise Factor"，*FAJ* 46(6)：17–35，1990；DOI 10.2469/faj.v46.n6.17。
    https://www.tandfonline.com/doi/abs/10.2469/faj.v46.n6.17 ；https://rpc.cfainstitute.org/research/financial-analysts-journal/1990/inside-the-pe-ratio-the-franchise-factor
  - 同系列：
    - "The Franchise Factor for Leveraged Firms"，FAJ 47(6)，1991。https://www.tandfonline.com/doi/abs/10.2469/faj.v47.n6.29
    - "Franchise Value and the Growth Process"，FAJ 48(1)，1992。https://www.tandfonline.com/doi/abs/10.2469/faj.v48.n1.53
  - 文集：*Franchise Value and the Price/Earnings Ratio*，Research Foundation of AIMR，1994。https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/1994/rf-v1994-n1-4442-pdf.pdf
  - 專書：Leibowitz，*Franchise Value: A Modern Approach to Security Analysis*，Wiley。
- 摘要【事實】：把 P/E 擴張的成分拆成兩部分。
  - **Franchise Factor**：以特定報酬率進行新投資，對 P/E 的衝擊。
  - **成長量測（growth equivalent）**：新投資機會的規模。
  - 只有報酬率高於市場的新投資，才會帶來正的 FF 與高於市場的 P/E；以市場報酬率投資時 FF＝0。
- 公式【二手】：
  - **P/E＝1/k＋FF×G**，**FF＝(R−k)/(r·k)**。R＝新投資報酬率，r＝現有帳面 ROE，k＝資金成本。
    https://getmoneyrich.com/how-to-calculate-full-p-e-using-base-p-e-and-the-franchise-factor/ （二手）
  - CFA 教材的簡化版（R＝r＝ROE、恆常成長）：tangible P/E＝1/r，**FF＝1/r − 1/ROE**，**G＝g/(r−g)**。
    http://cfaglossary.blogspot.com/2010/03/franchise-value-method.html （二手）
  - 【推論】G 的一般定義是「未來新投資的現值 ÷ 目前帳面價值」。
  - 【推論，已數值驗算】簡化版**等於 Gordon 的 forward P/E**，所以這裡的 P/E 是 **P₀/E₁**。驗算：r＝9%，ROE＝15%，b＝0.4，四種算法都是 20.0。
- 【事實】延伸：P/E 隨時間的軌跡。
  - Leibowitz（1999）"P/E Forwards and Their Orbits"，*FAJ* 55(3)：33–47（1999 Graham & Dodd Award of Excellence）。
    - 兩階段模型下，在共識不變時，P/E 會沿著一條逐年平滑下降的「**P/E orbit**」走到第二階段的終端 P/E。
    - 文中警告「**P/E myopia**」：直接把今天的 P/E 套到未來的共識盈餘上。
    - https://rpc.cfainstitute.org/research/financial-analysts-journal/1999/pe-forwards-and-their-orbits ；https://ideas.repec.org/a/taf/ufajxx/v55y1999i3p33-47.html
  - Kogelman, Bova & Leibowitz（2020）"The Fully-Anticipated P/E Promise and Its Realization"，*Journal of Investment Management* 18(1)：在「完全預期」的 franchise 投資下推算 P/E 的時間路徑。
    - 投資機會被執行時，價格不變，但新盈餘進入分母，所以 P/E 下降。
    - 之後 P/E 隨下一個機會臨近而回升。
    - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3595323
- **本益比由什麼決定**：由 **1/k（有形 P/E）**＋**FF（新投資的超額報酬強度）× G（新投資機會規模）**決定。在共識不變下，P/E 會因成長被「實現」而**機械性地沿 orbit 變化**。

---

## 5. 會計基礎估值：剩餘收益（RIV）、Ohlson、Feltham–Ohlson、AEG、Penman

### 5a. 剩餘收益模型的源流（Preinreich → Edwards & Bell 1961 → Peasnell → Ohlson 1995）
- 【事實／二手】這個模型的「剩餘收益」在文獻中有多種名稱：
  - excess earnings（Canning 1929；Preinreich 1938）
  - excess realizable profit（**Edwards & Bell 1961**）
  - abnormal earnings（Peasnell 1981/1982；Ohlson 1995）
  - https://en.wikipedia.org/wiki/Residual_income_valuation （僅當線索）；Penman 綜述 https://business.columbia.edu/sites/default/files-efs/pubfiles/6208/Valuation%20Models%20Routledge.pdf
- 書目【事實】：Edgar O. Edwards & Philip W. Bell，*The Theory and Measurement of Business Income*，University of California Press，1961。這本書的主軸是**重置成本**下的營業利潤與持有利得。
  https://archive.org/details/theorymeasuremen0000edwa ；https://afgr.scholasticahq.com/article/26971-what-the-old-guys-can-tell-us-edwards-and-bell-s-the-theory-and-measurement-of-business-income.pdf
- 【不確定】RIV 公式在 Edwards & Bell 書中的確切位置與記號：未能核對。
- **RIV 公式**【推論／教科書標準形式】：
  - 前提是 clean surplus：B_t＝B_{t−1}＋X_t−d_t。
  - V₀＝B₀＋Σ_{t≥1} E₀[X^a_t]/(1+r)^t，其中 X^a_t＝X_t − r·B_{t−1}，也就是 (ROE_t − r)·B_{t−1}。
- **本益比由什麼決定**（推論）：價值＝帳面＋未來「超額 ROE × 帳面」的現值。P/E 間接由 **B/E（即 1/ROE）** 與**未來超額盈餘路徑**決定。

### 5b. Ohlson（1995）
- 書目【事實】：James A. Ohlson，"Earnings, Book Values, and Dividends in Equity Valuation"，*Contemporary Accounting Research* 11(2)：661–687，1995；DOI 10.1111/j.1911-3846.1995.tb00461.x。
  https://onlinelibrary.wiley.com/doi/10.1111/j.1911-3846.1995.tb00461.x
- 假設【事實／摘要＋二手】：
  - clean surplus 成立；股利減少當期帳面，但不影響當期盈餘（股利無關）。
  - 風險中立（折現率＝無風險利率，R＝1＋r）。
  - **線性資訊動態（LIM）**：超額盈餘服從 AR(1)，參數 ω 是持續性；另有一個「其他資訊」ν_t，自身服從 AR(1)，參數 γ。
  - https://www.researchgate.net/publication/247201590_A_Test_of_the_Ohlson_1995_model ；https://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0186-10422007000300003
- 公式：
  - 【二手】P_t＝y_t＋α₁x^a_t＋α₂ν_t，**α₁＝ω/(R−ω)**。
    https://redfame.com/journal/index.php/afa/article/download/2969/3154 （二手）
  - 【推論】α₂＝R/[(R−ω)(R−γ)]。搜尋摘要顯示的 α₂ 有亂碼，此處是我依 LIM 推導的。
  - 【事實／二手】價值可以寫成「**經股利調整的資本化當期盈餘**」與「**當期帳面**」的加權平均；當期盈餘的資本化倍數＝R/r。
  - 【推論，已數值驗算】ν＝0 時：**P_t＝k(φx_t − d_t)＋(1−k)y_t**，φ＝R/(R−1)，**k＝(R−1)ω/(R−ω)**。
- **P/E 含意**【推論】：
  - P_t/x_t＝k(φ − d_t/x_t)＋(1−k)·(1/ROE_t)。
  - ω→1（超額盈餘永久）時，P/E →「正常」的 cum-div P/E＝R/r。
  - ω＝0（超額盈餘立刻消失）時，價格＝帳面，P/E＝1/ROE。
- **本益比由什麼決定**：由 **r**、**超額盈餘持續性 ω**、**當期 ROE（B/E）**、**其他資訊 ν（未入帳的成長訊息）** 決定。持續性越高，P/E 越接近資本化倍數；越暫時，P/E 越接近 1/ROE。

### 5c. 會計保守性：Feltham & Ohlson（1995）、Nezlobin–Rajan–Reichelstein（2016）
- 【事實】Gerald A. Feltham & James A. Ohlson，"Valuation and Clean Surplus Accounting for Operating and Financial Activities"，*CAR* 11(2)：689–731，1995；DOI 10.1111/j.1911-3846.1995.tb00462.x。
  - 模型參數代表超額盈餘的**持續性、成長與會計保守性**。
  - 金融活動的帳面＝市值；營業活動的帳面與市值可以不同。
  - https://scholars.cityu.edu.hk/en/publications/valuation-and-clean-surplus-accounting-for-operating-and-financia/
- 【事實】Alexander Nezlobin, Madhav Rajan & Stefan Reichelstein，"Structural properties of the price-to-earnings and price-to-book ratios"，*Review of Accounting Studies* 21(2)：438–472，2016。
  - P/E 與 P/B 的大小和行為，由**過去與預期的未來成長、經濟獲利力、會計保守性**共同塑造。
  - 用重置成本會計時（P/B＝Tobin's q），**P/E 是「永久盈餘模型的 P/E」與「Gordon 成長模型的 P/E」的凸組合，權重完全由 Tobin's q 決定**。
  - 在保守會計下，過去投資成長對 P/E 的影響方向取決於保守程度。
  - https://ideas.repec.org/a/spr/reaccs/v21y2016i2d10.1007_s11142-016-9356-0.html ；工作論文版 https://www.anderson.ucla.edu/documents/areas/fac/accounting/alex_determinants.pdf
- 【不確定】ScienceDirect 上有一篇 "Conservative accounting and equity valuation"（JAE），搜尋摘要沒有顯示作者，不補。https://www.sciencedirect.com/science/article/abs/pii/S0165410100000161
- **本益比由什麼決定**：除了 r、g、ROE，還有**會計保守性**（費用化的投資壓低當期 E、推高 P/E），以及**過去投資成長**和保守性的交互作用。

### 5d. Ohlson & Juettner-Nauroth（2005）異常盈餘成長（AEG）模型
- 書目【事實】：James A. Ohlson & Beate E. Juettner-Nauroth，"Expected EPS and EPS Growth as Determinants of Value"，*Review of Accounting Studies* 10：349–365，2005；DOI 10.1007/s11142-005-1535-3。
  https://link.springer.com/article/10.1007/s11142-005-1535-3
- 摘要【事實】：模型把每股價格連到四個量：
  - (i) 下一年預期 EPS
  - (ii) 短期 EPS 成長
  - (iii) 長期（漸近）EPS 成長
  - (iv) 權益資金成本
  - 立論基礎包括**股利政策無關**。
- AEG 定義【二手，Penman】：
  - AEG_t ≡ Earnings_t＋(ρ−1)d_{t−1} − ρ·Earnings_{t−1}，其中 ρ＝1＋r。
  - 「只有預期得到 AEG（也就是成長率高於要求報酬率）時，才值得付超過 1/(ρ−1) 倍的 forward 盈餘。」
  - https://business.columbia.edu/sites/default/files-efs/pubfiles/6208/Valuation%20Models%20Routledge.pdf （Penman 綜述）
- **forward P/E 公式**【推論，已數值驗算】：
  - 假設 AEG 從第 1 期起以 γ 衰減或成長：z_{t+1}＝γz_t，其中 z₁＝eps₂＋r·dps₁−(1+r)eps₁。
  - P₀＝eps₁/r＋z₁/[r(r−(γ−1))]
  - **P₀/eps₁＝[g₂ − (γ−1)＋r·dps₁/eps₁] / [r(r − (γ−1))]**，其中 g₂＝(eps₂−eps₁)/eps₁。
  - 這個形式和 Gode & Mohanram（2003）用 OJ 模型反推隱含資金成本的二次式一致：r＝A＋√(A²＋(eps₁/P₀)(g₂−(γ−1)))，A＝½((γ−1)＋dps₁/P₀)。我驗算過：用閉式解算出的價格反推，r 正好回到原值。
  - 【事實】Gode & Mohanram，*RAST* 8：399–431，2003；他們把 γ−1 設為無風險利率 −3%。https://link.springer.com/article/10.1023/A:1027378728141
  - 【不確定】OJ 原文的式號與記號：未能核對。
- **本益比由什麼決定**：forward P/E＝1/r＋（未來異常盈餘成長的現值）/(r·eps₁)。由 **r、短期成長 g₂、長期成長 γ−1、派發** 決定。**AEG＝0 時 forward P/E＝1/r**，與 ROE 高低無關（推論）。

### 5e. Penman（1996）P/E 與 P/B 的勾稽
- 書目【事實】：Stephen H. Penman，"The Articulation of Price-Earnings Ratios and Market-to-Book Ratios and the Evaluation of Growth"，*Journal of Accounting Research* 34(2)：235–259，1996。
  https://ideas.repec.org/a/bla/joares/v34y1996i2p235-259.html
- 發現【事實，CFA Digest 1997 摘要】：
  - 他用「**cum-dividend 盈餘**」推導 P/E 的表達式，實證資料是 1968–1985。
  - **P/E 與預期未來 ROE 正相關、與當期 ROE 負相關**。P/E 是未來成長的拙劣指標。
  - **P/B 反映未來獲利力**，是盈餘成長的好指標。
  - https://rpc.cfainstitute.org/research/cfa-digest/1997/05/the-articulation-of-priceearnings-ratios-and-market-to-book-ratios-and-the-evaluation-of-growt ；https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/cfa-digest/1997/dig-v27-n2-54-pdf.pdf
- 【事實／二手】
  - 預測固定的剩餘盈餘，得到「正常 P/E」＝ρ/(ρ−1)（trailing、cum-div）；預測成長的剩餘盈餘，P/E 就高於正常值。
  - 盈餘以要求報酬率成長（AEG＝0）時，forward P/E＝1/(ρ−1)。
  - 二手綜述把「盈餘反轉使 P/E 無法預測成長」稱為 Molodovsky effect：未來成長率主要取決於當期（常是暫時性的）獲利水準。
  - https://www.growingscience.com/ac/Vol3/ac_2016_24.pdf （二手綜述）
- **trailing P/E 恆等式**【推論，由 RIV 推導並已數值驗算】：
  - **(P_t＋d_t)/X_t＝[ρ/(ρ−1)] · [1＋(1/X_t)·Σ_{τ≥1} ρ^{−τ}·E_t(ΔX^a_{t+τ})]**
  - 也就是說，P/E 偏離「正常 P/E」的唯一來源，是**未來超額盈餘的「變化」**相對當期盈餘的大小。
  - 【不確定】Penman 1996 原文是否正是這個寫法：未能核對；公式和摘要的文字敘述一致。
- **本益比由什麼決定**：由 **未來盈餘相對當期盈餘的成長**決定，也就是**未來 ROE 相對當期 ROE**。當期盈餘若有暫時性成分（偏低或偏高），P/E 會反向偏離。P/E 衡量的是「成長＋暫時性」的混合，不是單純的長期成長。

---

## 6. 報酬分解恆等式：Campbell & Shiller（1988）、Vuolteenaho（2002）

### 6a. Campbell & Shiller（1988）
- 書目【事實】：
  - John Y. Campbell & Robert J. Shiller，"The Dividend-Price Ratio and Expectations of Future Dividends and Discount Factors"，*Review of Financial Studies* 1(3)：195–228，1988。
    https://ideas.repec.org/a/oup/rfinst/v1y1988i3p195-228.html ；PDF：https://pages.stern.nyu.edu/~dbackus/GE_asset_pricing/CampbellShiller%20RFS%2088.PDF
  - 同作者，"Stock Prices, Earnings, and Expected Dividends"，*Journal of Finance* 43(3)：661–676，1988。
    https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1988.tb04598.x ；NBER w2511：https://www.nber.org/papers/w2511
- 對數線性化【事實／二手講義】：
  - 對 log(1＋exp(d−p)) 在樣本平均點做一階泰勒展開：
    **r_{t+1} ≈ k＋ρ·p_{t+1}＋(1−ρ)·d_{t+1} − p_t**，ρ＝1/(1＋exp(mean(d−p)))，略小於 1（Cochrane 常用 0.96）。
  - 前推並假設 lim ρ^j(p−d)_{t+j}＝0，得到恆等式：
    **p_t − d_t ＝ k/(1−ρ)＋Σ_{j≥0} ρ^j·(Δd_{t+1+j} − r_{t+1+j})**
  - 這個式子事後成立；取條件期望後事前也成立。它是近似的**會計恆等式**，不含行為假設。
  - 假設：log D/P 定態（stationary），作為展開點。這個假設後來受到質疑。
  - https://www.johnhcochrane.com/s/lecture_notes.pdf ；https://jfimbett.github.io/teaching/empirical_asset_pricing/lesson_1A.pdf ；https://arxiv.org/pdf/1902.06053 （非定態批評）
- **P/E 版本**【推論，已數值驗算】：兩邊加上 (d_t − e_t)，再把股利成長拆成盈餘成長＋派發率變動，望遠鏡相消後得到
  **p_t − e_t ＝ k/(1−ρ)＋Σ_{j≥0} ρ^j·[Δe_{t+1+j} − r_{t+1+j}＋(1−ρ)(d−e)_{t+1+j}]**
  - 【事實／二手】文獻敘述與此一致：log 盈餘殖利率約為常數，加上「未來要求報酬」減「經股利比率調整的盈餘成長」的現值。
    https://jfimbett.github.io/teaching/empirical_asset_pricing/lesson_1A.pdf
- JF 1988 的實證發現【事實，摘要】：
  - 用 1871–1986 年美國市場資料做 VAR，未來實質股利的現值預測大致是「**長期移動平均盈餘**」與當期實質價格的加權平均，**盈餘權重 2/3 到 3/4**。
  - 長期歷史平均盈餘有助於預測未來股利的現值。
- **本益比由什麼決定**：在恆等式意義下，log P/E 完全由 **未來盈餘成長、未來報酬（折現率）、未來派發率** 三者的折現和決定，沒有第四個來源（理性泡沫項設為 0）。

### 6b. Vuolteenaho（2002）個股版本
- 書目【事實】：Tuomo Vuolteenaho，"What Drives Firm-Level Stock Returns?"，*Journal of Finance* 57(1)：233–264，2002。
  https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00421 ；NBER w8240：https://www.nber.org/papers/w8240
- 恆等式【二手】：
  - 用 clean-surplus 把 log 帳面市值比與 ROE 連起來：**mb_t ≈ Σ_j ρ^{j−1}·E_t[roe_{t+j} − r_{t+j}]**，其中 mb＝log(M/B)，roe＝log(1＋ROE)。
  - 低 B/M 必須由「高預期未來獲利力」或「低預期未來報酬」來合理化。
  - https://personal.lse.ac.uk/polk/research/jofi_5802005.pdf ；https://macrosynergy.com/research/a-market-to-book-formula-for-equity-strategies/
  - 【不確定】原文常數項與 ρ 指數的確切寫法：未能核對。
- 實證【事實，摘要】：
  - 個股報酬**主要由現金流消息驅動**；典型個股的現金流消息變異數是預期報酬消息的兩倍以上。
  - 預期報酬消息在公司之間高度相關，現金流消息在組合中大多可以分散掉。
- 延伸【事實】：Cohen, Polk & Vuolteenaho（2003）"The Value Spread"，*JF* 58(2)：609–641。
  - B/M 的橫斷面變異中，只有 **20–25%** 來自預期 15 年報酬，其餘來自預期 15 年獲利力與估值水準的持續性。
  - https://onlinelibrary.wiley.com/doi/abs/10.1111/1540-6261.00539
- **P/E 版本**【推論】：log(P/E)＝log(P/B) − log(E/B)＝mb_t − log(ROE_t)。所以 log P/E ≈ 未來 (roe − r) 價差的折現和，減去當期 log ROE。這和 Penman 1996 的「未來 ROE 相對當期 ROE」一致。
- **本益比由什麼決定**（個股層級）：由 **未來獲利力（ROE）相對報酬率的路徑**，以及**當期獲利力**決定。個股的變動以獲利力預期的修正為主，折現率的修正為次（實證）。

---

## 7. Damodaran 的「基本面本益比」整理

- 來源【事實／講義，搜尋摘要】：
  - Aswath Damodaran（NYU Stern），*Investment Valuation* 第 18 章 "Earnings Multiples"：https://pages.stern.nyu.edu/~adamodar/pdfiles/val3ed/c18.pdf
  - 講義：https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/earnmult.pdf ；https://pages.stern.nyu.edu/~adamodar/podcasts/valUGspr21/session22slides.pdf
- 公式【事實／講義】：
  - 穩定成長：**PE＝Payout Ratio × (1+g_n)/(r−g_n)**（trailing）。
  - forward：**PE＝Payout/(r−g_n)**。
  - **Payout＝1 − g_n/ROE_n**。
  - 公司若沒有把能發的都發出去，可以用 FCFE/Earnings 代替 payout。
- 摘要中的命題【事實】：
  - 高成長公司的 P/E 仍然是「成長、風險、派發」的函數，和穩定成長公司是同一組變數。
  - 成長越高 → P/E 越高；風險越高 → P/E 越低。
- **兩階段公式**：
  - 【不確定】搜尋摘要顯示的版本有亂碼。下面是我從兩階段 DDM 推導、並以暴力加總驗算過的版本（推論）：
  - **P₀/E₀＝Payout_hg·(1+g)·[1 − (1+g)^n/(1+r)^n]/(r − g)＋Payout_st·(1+g)^n·(1+g_n)/[(r − g_n)(1+r)^n]**
  - 驗算例：g＝25%、n＝5、payout 20% → g_n＝8%、payout 50%、r＝12%（r 是我自己設的，講義範例的 r 未取得）。閉式解＝24.784，暴力加總＝24.784。
  - 講義另可對兩階段設不同 r；這裡用單一 r。
- **本益比由什麼決定**：由 **r（風險）、高成長期的 g 與期間 n、各階段派發率（或 ROE）、穩定期 g_n** 決定。
  - 【推論】隨時間經過，剩下的 n 縮短，P/E 會機械性地往穩定期 P/E 收斂。這和 Leibowitz 1999 的「P/E orbit」相同。

---

## 8. 相關補充（和「預測未來 P/E」直接相關的實證）

- 【事實／摘要】Andrew Ang & Xiaoyan Zhang，"Price-to-Earnings Ratios: Growth and Discount Rates"，收錄於 *Rethinking the Equity Risk Premium*（Research Foundation of CFA Institute，2011）。
  - 把 P/E 拆成 no-growth value 與 PVGO，用的動態模型含時變風險溢酬與隨機成長機會。
  - S&P 500 五十多年資料顯示：**P/E 變動的 95% 來自成長機會的變動，而不是總折現率**。
  - 無風險利率、盈餘成長、派發率等總體變數也很重要。
  - https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2011/rf-v2011-n4-1-pdf.pdf
  - 【注意】這是**市場層級**的結論。
- 【事實】Beaver & Morse，"What Determines Price-Earnings Ratios?"，*FAJ*，1978 年 7/8 月。
  - 【查無】具體結論只取得二手零碎敘述，不引用。
  - 後續再檢驗：Zarowin（1990）"What Determines Earnings-Price Ratios: Revisited"。https://journals.sagepub.com/doi/abs/10.1177/0148-558X1989005003007

---

## 9. 數值驗算紀錄（推論公式的檢查）

腳本：`research/pe_check.py`、`research/cs_check.py`。

| 檢查 | 結果 |
|---|---|
| DDM 暴力加總 vs Gordon vs MM(PVGO) vs L&K（r=9%, ROE=15%, b=0.4） | 20.0 / 20.0 / 20.0 / 20.0 |
| ROE＝r 時，b＝0／0.3／0.8 的 P/E | 11.111 ×3＝1/r |
| Damodaran 兩階段閉式解 vs 暴力加總 | 24.784284 / 24.784284 |
| OJ 閉式解 vs AEG 暴力加總；Gode-Mohanram 反推 r | 36.0 / 36.0；r＝0.08（回到原值） |
| Penman trailing cum-div P/E 恆等式 左 vs 右 | 11.568283 / 11.568283 |
| Ohlson 直接式 vs 加權平均式 | 11.5 / 11.5 |
| Campbell-Shiller log P/E 恆等式（模擬路徑） | 3.0 / 3.0 |

---

## 10. 推論：把所有理論收斂成「預測未來 P/E」的骨架

1. **所有理論的共同核心**（推論）：
   P_t/E_t＝f( E_t[未來盈餘路徑 / E_t]、E_t[未來折現率]、再投資效率（ROE vs r）與派發 )。
   差別只在怎麼參數化「未來盈餘路徑」：
   - Gordon：用一個常數 g。
   - MM／L&K：用 (ROE−r)×規模×期間。
   - Ohlson：用 AR(1) 持續性 ω。
   - OJ：用短期 g₂ 衰減到長期 γ−1。
   - Penman：用 ΔX^a。
   - Campbell-Shiller：不參數化，直接寫成恆等式。
2. **一期動態恆等式**（純代數）：
   P_{t+1}/E_{t+1}＝(P_t/E_t) × (P_{t+1}/P_t)/(E_{t+1}/E_t)。
   預測 12 個月後的 P/E，等於同時預測「**價格報酬**」與「**盈餘成長**」。
   - 在任何參數不變的模型裡，預期價格報酬＝r − 股利殖利率。
   - 所以 **E[P/E_{t+1}] ≈ P/E_t × (1＋r − dy)/(1＋g^E_{t+1})**：
     - Gordon 穩態下兩者相等，P/E 不變。
     - 兩階段／franchise 模型下，高成長年度被消耗，P/E 沿 orbit 下降（Leibowitz 1999）。
     - 當期盈餘有暫時性成分時，盈餘回歸使 P/E 反向修正（Molodovsky／Penman）。
3. **理論提供的是「共識不變時的機械路徑」，加上「哪些變數的修正會讓它偏離」**：
   - 機械路徑：P/E orbit、正常化盈餘回歸。
   - 修正項：
     - 個股以**獲利力預期修正**為主（Vuolteenaho 2002；Cohen-Polk-Vuolteenaho 2003）。
     - 市場層級以**成長機會變動**為主（Ang-Zhang 2011）。
     - 折現率修正在各公司間高度相關，近似一個共同因子。

---

## 11. 總表：理論 → P/E 決定因素 → 能否直接預測未來某日的 P/E、缺什麼

| 理論（出處） | P/E 由什麼決定 | 能直接預測「T 日 P/E」嗎？ | 缺什麼 |
|---|---|---|---|
| Graham & Dodd 1934（Security Analysis） | 正常化（5–10 年平均）盈餘能力；分析師主觀倍數（二手：約 12–12.5 倍，上限約 20 倍） | 否。規範性的「該付多少」，不是市場 P/E 的實證模型 | 和 r、g 沒有連結；沒有動態；倍數版本出處【不確定】 |
| Molodovsky 1953（FAJ 9(5)） | 未來股利與利率；當期盈餘的週期位置（Molodovsky effect，二手） | 部分。暗示以當期 EPS 算的 P/E 會隨盈餘正常化而反轉 | 原文公式【查無】；需要正常盈餘的估計 |
| Williams 1938 | 整條未來派發 × 盈餘成長路徑、折現率 | 原理上可以，但要知道 T 日市場對整條路徑的預期 | 預期如何更新的動態模型 |
| Gordon（1956/59/62） | r、g、payout（或 r、g、ROE） | 只給穩態水準；參數不變時預測 P/E 永遠不變 | 時變的 r、g；r−g 小時極度敏感 |
| Miller-Modigliani 1961（JB 34(4)） | 1/r＋PVGO/E；(ROE−r)×再投資規模×期間 | 可拆解當期 P/E，但 T 日 P/E 取決於 PVGO 如何衰減（fade） | 超額報酬的衰減速度、競爭優勢期間 |
| Leibowitz-Kogelman 1990 起（FAJ 46(6)）；Leibowitz 1999（FAJ 55(3)） | 1/k＋FF×G；R vs k；新投資規模 | **最接近**：P/E orbit 給出共識不變下的 P/E 時間路徑 | 共識修正（orbit 之外的偏離）；G 與 R 難以觀察 |
| RIV／Edwards-Bell 1961／Ohlson 1995（CAR 11(2)） | B（1/ROE）、超額盈餘持續性 ω、其他資訊 ν、r | 部分。LIM 給出狀態變數 (x^a, ν, B) 的 AR(1) 動態，可推期望 P/E 路徑 | 風險中立與常數 r；ν 不可觀察；ω 要另外估 |
| Feltham-Ohlson 1995；Nezlobin-Rajan-Reichelstein 2016（RAST 21(2)） | 再加上會計保守性、過去投資成長、Tobin's q | 解釋橫斷面差異比時間預測強 | 投資成長路徑；保守程度的量測 |
| Ohlson-Juettner-Nauroth 2005（RAST 10） | eps₁、短期成長 g₂、長期成長 γ−1、r、dps | 可以：給 T 日的 eps_{T+1}、eps_{T+2} 預估與 r_T，就有 T 日 forward P/E | T 日的分析師預估本身要預測；r_T；γ 的設定（GM 用 rf−3%） |
| Penman 1996（JAR 34(2)） | 未來 ROE 相對當期 ROE；當期盈餘的暫時性 | 部分。高 P/E 若來自暫時性低盈餘，可預期 P/E 隨盈餘回升而下降 | 暫時性成分的識別；P/B 才是未來 ROE 的較好指標 |
| Campbell-Shiller 1988（RFS 1(3)；JF 43(3)） | 未來盈餘成長、未來報酬、未來派發率（恆等式） | 恆等式本身不預測；它說「預測 P/E 變動」≡「預測報酬 − 盈餘成長」 | 預期報酬模型；log D/P 定態假設【有爭議】 |
| Vuolteenaho 2002（JF 57(1)）；Cohen-Polk-Vuolteenaho 2003 | 個股：未來 (ROE − 報酬) 路徑；當期 ROE | 不直接預測；指出個股估值變動主要來自獲利力消息 | 獲利力預期的預測模型（VAR 狀態變數） |
| Damodaran 基本面 P/E（Investment Valuation ch.18） | payout、g（兩階段）、n、r | 同 Gordon／兩階段；推論出 P/E 隨 n 消耗而收斂 | T 日的市場 r 與成長修正 |
| Ang-Zhang 2011（CFA RF） | 時變折現率＋成長機會；95% 的 P/E 變動來自成長機會（市場層級） | 給了方向：預測 P/E 變動要預測成長機會的修正 | 個股層級的證據；模型細節未能讀到原文 |

---

## 12. 反面訊號與爭議

1. **P/E 不是好的成長預測指標**（Penman 1996）：P/E 混合了「成長」與「暫時性盈餘」。直接用 P/E 反推成長會被 Molodovsky effect 汙染。
2. **Campbell-Shiller 的定態假設有爭議**：log D/P 是否定態受到質疑（https://arxiv.org/pdf/1902.06053 ）；近似誤差在一般樣本中被認為很小，但不是零。
3. **哪個成分主導 P/E 變動，結論依層級而不同**：
   - 個股層級以現金流（獲利力）消息為主（Vuolteenaho 2002）。
   - 市場層級，Ang-Zhang（2011）也說成長機會解釋 95%。
   - 但傳統市場層級的報酬可預測性文獻（Campbell-Shiller、Cochrane）強調折現率。
   - 三者的定義（P/E 水準變異 vs 報酬變異）不同，不能直接比較。【不確定】
4. **Graham-Dodd 倍數的版本與數字**（16 倍 vs 20 倍）：查無可靠一手出處；20 倍來自二手引用。
5. **Molodovsky 1953 的刊期**：一則二手摘要說是 1/2 月號，和 DOI（Vol.9 No.5）衝突。
6. **原文核對缺口**：WebFetch 全面被擋，所有公式的「原文式號／記號」都沒有核對。推導公式在數學上已驗證，但「作者原文就是這樣寫」屬於推論。

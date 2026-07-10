# 線性關卡制 vs 權重評分制：多訊號選股架構的實證整理

研究日期：2026-07-10。方法：WebSearch（僅此工具可用），來源與年份標註於各段。
標籤說明：【學術實證】= 同儕審查論文/正式研究；【實務慣例】= 基金/實務界公開做法；【推理】= 由前述證據推導，非直接實證。

---

## 0. 結論先行

1. **純評分制有最強的學術實證**（Piotroski 2000、Mohanram 2005、AQR 2017、O'Shaughnessy 各版），**純關卡制幾乎沒有學術辯護者**——關卡制的已知代價（漏斗饑餓、邊界效應、互補性浪費）有實證與理論支持。
2. 但**實務主流不是純評分，而是兩段式混合**：負面/不可投資條件用硬關卡，正面 alpha 訊號用評分排名（Alpha Architect QVAL、Piotroski 論文本身、機構 exclusion-screen + alpha-model 結構）。
3. 權重：**訊號少、歷史短時用等權**，證據鏈極強（Dawes 1979、DeMiguel et al. 2009、forecast combination puzzle）。
4. 對本案（3–6 個慢訊號、事件驅動、含強負面訊號）：**負面濾網＝硬關卡；事件觸發＝資格條件（定義候選集，不打分）；其餘正面訊號＝等權評分排名取前 N**。

---

## 1. 評分制的實證代表

### 1.1 Piotroski F-Score（2000）
- Joseph Piotroski, "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers", *Journal of Accounting Research* 2000。9 項二元訊號（獲利、槓桿/流動性、營運效率）等權加總為 0–9 分。【學術實證】
- 報酬：1976–1996，高分（8–9）減低分（0–1）組合年差 **約 23%**；高分組平均市場調整報酬約 +7.5%/年。（來源：Piotroski 2000；Grokipedia/AAII/Quant Investing 整理，2024–2025 摘述）
- **關鍵架構細節：F-Score 本身就是混合制**——先用「最高 book-to-market 五分位」這個硬關卡界定 value 池，再在池內打分排序。不是全市場打分，也不是逐關淘汰。【學術實證】
- **為何等權加總、不估計權重**：Piotroski 明言相對 Ou & Penman (1989) 的估計式 logit 模型是刻意的「step back」——O&P 保留大量缺乏商業邏輯的會計變數、且入選變數隨估計期漂移，難以形成跨期一致的策略；簡單加總可解釋、不需統計背景、避免 sample-specific 權重。（Piotroski 2000 原文論述；alphaarchitect.com 與學位論文轉述）【學術實證＋作者自述】
- 樣本外驗證：Walkshäusl, "Piotroski's FSCORE: international evidence", *Journal of Asset Management* 2020——2000–2018 在非美已開發市場與新興市場皆有效；另有澳洲（2016）、波蘭、土耳其等在地複製。【學術實證】
- 把二元訊號改成連續值/加項改良（Alpha Architect FS-Score，10 項）：年化 15.9% vs 原版 15.2% vs S&P 500 11.2%——**改良幅度小**，顯示粗粒度等權加總已抓走大部分訊號，精緻化邊際效益低。（alphaarchitect.com, 2017–2018）【實務慣例＋實證回測】

### 1.2 Mohanram G-Score（2005）
- "Separating Winners from Losers among Low Book-to-Market Stocks", *Review of Accounting Studies* 2005。同樣架構：**先關卡（低 BM 成長股池）→ 池內 8 項二元訊號等權打分**。1979–1999 高分 vs 低分原始報酬 **17.4% vs −4.0%**（超額報酬多來自空方）。【學術實證】
- 意義：「gate 定義池、score 排序」這個架構在 value 池與 growth 池都複製成功。

### 1.3 Greenblatt Magic Formula（2006）
- 《The Little Book that Beats the Market》：earnings yield 排名＋ROC 排名，**兩個名次相加**再總排名——純評分制。原始回測 17 年，96% 的滾動 5 年期贏大盤。【實務慣例＋作者回測】
- 獨立樣本外：Robert Andrew Martin（reasonabledeviations.com, 2020）2003–2015 美股年化 **11.4% vs S&P 500 8.7%**；但 2007–2011 落後、2014 之後連年跑輸 S&P 500（quantifiedstrategies.com; gridoasis.com）。【獨立回測】
- 教訓：排名相加架構本身穩健，但雙因子太少、因子退潮時整體失效——與「訊號數多寡影響 composite 穩健度」一致。

### 1.4 O'Shaughnessy《What Works on Wall Street》(第4版 2011)
- 從早期單因子篩選改為 composite 排名：**多指標 value composite 在 82% 的期間勝過任何單一估值比率**；Value Composite Two 單獨年化 17.3%，加動能成 Trending Value（先 composite 排名取前 10%，再按 6 個月動能選 25 檔）45 年年化 **21.2%**。（AAII/quant-investing 整理）【實務回測，非同儕審查】
- 注意：Trending Value 本身也是兩段式——composite 分數關卡（前 10%）＋動能排序。

---

## 2. 整合 vs 混合之辯（評分制內部的架構戰爭）

### 2.1 正方：AQR — Fitzgibbons, Friedman, Pomorski, Serban (2017)
- "Long-Only Style Investing: Don't Just Mix, Integrate", *Journal of Investing* 26(4), 2017（SSRN 2802849, 2016）。
- 整合（先把多風格分數加總成單一分數再建組合）vs 混合（各風格分別建組合再拼裝）：整合組合**超額報酬 +1%/年、Information Ratio 提升約 40%**；因子越多、優勢越大。機制：混合法會持有「單一因子極好但其他因子極差」的股票，整合法避開對沖型暴露、納入均衡正暴露。【學術實證（practitioner journal）】
- 這是「評分加總優於逐因子分別篩選」最常被引用的量化證據。

### 2.2 條件反方：Ghayur, Heaney & Platt (2018)
- "Constructing Long-Only Multifactor Strategies: Portfolio Blending vs. Signal Blending", *Financial Analysts Journal* 74(3), 2018。
- 在暴露匹配（exposure-matched）框架下：**低至中等 tracking error 時 portfolio blending 的 IR 較高；高 tracking error（高主動度）時 signal blending 勝**。【學術實證】
- 含義：AQR 的結論不是無條件的；主動度越高（越集中、越偏離指數），整合評分越佔優。本案是高主動度的集中選股 → 落在 signal blending 勝出的區間。

### 2.3 中立方：Leippold & Rüegg (2018)
- "The Mixed vs the Integrated Approach to Style Investing: Much Ado About Nothing?", *European Financial Management* 24(5), 2018。
- 用更嚴格的統計檢定：兩法報酬差**不具統計顯著性**；整合稍改善風險報酬，但混合更簡單透明。【學術實證】
- 含義：整合 vs 混合的差距可能被 AQR 誇大，但**沒有任何一方主張「逐關淘汰」優於兩者**——這場辯論的雙方都在「評分/排名」陣營內。

---

## 3. 關卡制（conjunctive screening）的實證與適用場景

### 3.1 決策科學根源
- Einhorn (1970, 1971)：conjunctive/disjunctive 非補償模型 vs 線性補償模型——非補償模型在預測準確度上**大致打平或略遜**於線性加權，且後續文獻批評其數學形式仍是補償式近似。（Cambridge JDM; ASME; Marketing Science 2004 choice-model 文獻）【學術實證（心理/行銷領域）】
- Dawes (1979)：線性模型（即使等權）穩健勝過人類直覺與規則式判斷——支持「把訊號放進線性加總」而非「逐條否決」。【學術實證】

### 3.2 關卡制的真實優勢
- **截斷左尾**：對「單一訊號足以否決」的災難型風險（詐騙、下市、流動性歸零），關卡是對的工具——見 §4 Beneish 證據。【學術實證＋推理】
- **可解釋、零估計誤差**：不需權重、不需歷史校準——與 Piotroski 選等權的理由同源。【推理】
- 小樣本穩健：規則不需擬合 → 不會過擬合。【推理】

### 3.3 關卡制的代價（有據）
- **漏斗饑餓/樣本過小**：實務回測顯示通過檔數可從 3 檔到 100+ 檔劇烈波動；檔數過少 → 集中度風險暴增、且「好策略與爛策略會選到同一批股票」，統計上無法分辨策略優劣（pyinvesting.com；StockRover screener 研究；AAII screen 建構指南——皆為實務文獻，2020s）。【實務慣例＋推理】
- **邊界效應**：差一分全丟。F-Score 的改良研究（連續化）證明二元切點確實丟資訊，只是丟得不多（§1.1）；在只有 3–6 個訊號時每個切點的資訊損失佔比更大。【實證＋推理】
- **互補性浪費**：AQR 2017 的機制分析——逐因子處理無法利用「兩項皆中上」優於「一項頂尖一項墊底」的互補結構；關卡制是逐因子處理的極端版。【學術實證（機制）】
- **廣度損失**：Grinold & Kahn（*Active Portfolio Management*, 1999）基本定律 IR = IC×√Breadth——每加一道硬關卡就砍一次廣度，IR 隨 √N 下降。【學術實證（理論）】
- **關卡砍到報酬來源**：Hong & Kacperczyk, "The Price of Sin", *JFE* 2009——被排除的罪惡股 1965–2006 顯著跑贏（排除 = 放棄溢酬）；ESG 負面篩選文獻普遍發現排除常與 value/profitability/低風險因子對作（Harvard Law corpgov 2022 整理）。**教訓：硬關卡只該架在「與報酬溢酬無關的災難維度」上，不要架在 alpha 維度上。**【學術實證】

---

## 4. 混合架構：實務主流「負面硬關卡＋正面評分」

### 4.1 實證支持負面關卡
- Beneish, Lee & Nichols, "Earnings Manipulation and Expected Returns", *Financial Analysts Journal* 69(2), 2013：M-Score 高（疑似操縱財報）的公司在**每一個** size/BM/momentum/accruals/short-interest 十分位內報酬都較低——樣本外預測力強。操縱旗標適合當排除關卡，因為它在所有風格池內都成立、且與正面訊號幾乎無互補性可浪費。【學術實證】
- Skinner & Sloan, "Don't Let an Earnings Torpedo Sink Your Portfolio", *Review of Accounting Studies* 2002：成長股對負面驚喜的價格反應**不對稱地大**——左尾事件的損失結構不對稱，支持對「爆雷型」訊號採用否決而非扣分。【學術實證】
- 台股對應【推理】：董監售股/質押/掏空訊號屬 Beneish-型（治理災難預測子）而非 alpha 因子 → 適合硬關卡。

### 4.2 實務系統的兩段式結構
- **Alpha Architect QVAL 流程（公開說明書與方法論文件）**：可投資池（~1500 檔）→ 流動性＋forensic accounting 紅旗排除（含操縱/財務危機篩除，~1000 檔）→ 最便宜 10%（~100 檔）→ 品質 **composite 評分**砍半（50 檔）→ 持有。即「負面關卡 → 單一 alpha 關卡 → 評分排名」。【實務慣例】
- **Robeco（2025 白皮書）**等機構量化流程同樣是 exclusion/investability screen → multi-signal alpha model 排名。【實務慣例】
- **Piotroski 2000 與 Mohanram 2005 論文本身**就是「池關卡 + 池內評分」。【學術實證】
- Grinold-Kahn 派量化基金標準架構：先清洗宇宙（可交易性、紅旗），再在池內做 **IC 加權的連續 alpha 合成**——沒有人在 alpha 段用逐關淘汰。【實務慣例】

### 4.3 決策理論理由【推理】
- 負面關卡＝不對稱損失＋近乎確定性的證據：當單一訊號對「不可接受結果」有高精度（詐騙旗標、下市風險），期望損失無界 → 否決是貝葉斯最適（任何有限正分都補償不了）。
- 正面訊號＝有雜訊的加性證據：每個訊號是弱似然比，log-likelihood 相加（≈ 等權評分）是資訊上正確的聚合方式；硬切點等於把連續似然比壓成 0/1，丟棄排序資訊。
- 事件驅動訊號（Form 4 集群、投信買超）本質是**資格/觸發條件**：它定義「事件發生了沒」（候選集），而非強度排序——Cohen, Malloy & Pomorski, "Decoding Inside Information", *Journal of Finance* 2012 的做法即是先分類（opportunistic vs routine，機會型組合月超額 **82 bps**、常規型≈0），分類=gate，之後才談組合建構。【學術實證＋推理】

---

## 5. 權重怎麼定

- **Dawes, "The Robust Beauty of Improper Linear Models", *American Psychologist* 1979**（及 Wainer 1976 "it don't make no nevermind"）：小而雜訊多的樣本裡，等權與最適權重的預測力幾乎無差，估權重反而引入誤差；「把對的變數放進去」遠比「權重精確」重要。【學術實證】
- **DeMiguel, Garlappi & Uppal, "Optimal Versus Naive Diversification", *Review of Financial Studies* 22(5), 2009**：14 種最適化模型在 7 個資料集**沒有一個穩定打贏 1/N**（Sharpe、CEQ、周轉率）；均值-變異數法要贏 1/N，25 資產需 **約 3000 個月**、50 資產需 **約 6000 個月** 的估計窗——本案 3–6 個訊號、幾年歷史，遠遠不夠。【學術實證】
- **Forecast combination puzzle**（Clemen 1989 綜述；Stock & Watson 2004；Timmermann 2006；Smith & Wallis 2009 給出理論解釋）：估計出的「最適」組合權重系統性輸給簡單算術平均，因為權重估計誤差吃掉理論增益。【學術實證】
- IC 加權（Grinold-Kahn）是理論上限，但需要長歷史、多獨立觀測才能估 IC 與訊號相關矩陣。【實務慣例】
- 結論【推理】：本案訊號數 3–6、事件頻率低、歷史短 → **等權（或最多粗粒度 2:1「證據強度」分級）**。若未來累積數百個事件樣本，才考慮 IC 加權。避免任何逐期再擬合的最適化。

---

## 6. 本案架構建議（事件驅動、3–6 訊號、含強負面訊號）

**三層漏斗：資格層（gate）→ 否決層（gate）→ 排序層（score）**

1. **資格層（事件觸發，硬條件）**：Form 4 內部人集群買入（美股）／投信買超×營收動能同時成立（台股）——定義候選事件集。理由：事件訊號是二元性質的觸發器，不是強度排序（Cohen et al. 2012 的 opportunistic 分類即 gate）。
2. **否決層（負面濾網，硬關卡）**：董監負面濾網、可交易性（流動性/下市/處置股）、財報操縱紅旗。理由：Beneish 2013（操縱旗標在所有池內預測低報酬）＋ Skinner & Sloan 2002（左尾不對稱）＋ Hong & Kacperczyk 2009 的反面警告（**只否決災難維度，不否決 alpha 維度**）。
3. **排序層（正面訊號等權評分，取前 N）**：其餘正面慢訊號（13F 佐證、營收動能強度、集群規模/身分加分等）各自標準化後**等權加總**，排名取前 N 或設「分數 ≥ 中位」的軟門檻。理由：AQR 2017（整合評分 +1%/年、IR +40%）＋ Ghayur 2018（高主動度時 signal blending 勝）＋ Piotroski/Mohanram 的池內等權加總範式＋ DeMiguel 2009/Dawes 1979（等權穩健）。
4. **儀表安全閥**：監控每層通過檔數。若否決層＋資格層後候選 < ~10 檔，不再加關卡、改用排序消化（漏斗饑餓證據，§3.3）；若某正面訊號想升級成關卡，先檢查它是否屬於災難維度——不是就留在評分層。

**一句話**：負面與資格用關卡、alpha 用等權評分排名——這是學術實證（Piotroski/Mohanram/AQR/Beneish/DeMiguel）與實務慣例（QVAL 漏斗、機構 exclusion+alpha model）的交集，純逐關淘汰在文獻中找不到辯護者。

---

## 來源清單（主要）

- Piotroski (2000), *JAR* — F-Score 原始論文；23%/yr 高低分差。https://grokipedia.com/page/Piotroski_F-score ; https://www.aaii.com/journal/article/simple-methods-to-improve-the-piotroski-f-score
- Walkshäusl (2020), *Journal of Asset Management* 21:106–118 — F-Score 國際樣本外。https://link.springer.com/article/10.1057/s41260-020-00157-2
- Mohanram (2005), *RAST* — G-Score，17.4% vs −4.0%。https://link.springer.com/article/10.1007/s11142-005-1526-4
- Greenblatt Magic Formula 樣本外：https://reasonabledeviations.com/2020/06/08/greenblatt-magic-formula/ ; https://www.quantifiedstrategies.com/the-magic-formula-strategy/
- Fitzgibbons, Friedman, Pomorski & Serban (2017), *Journal of Investing* — Don't Just Mix, Integrate；+1%/yr、IR +40%。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2802849 ; https://www.aqr.com/Insights/Research/White-Papers/Long-Only-Style-Investing
- Ghayur, Heaney & Platt (2018), *FAJ* 74(3) — blending vs signal blending 條件結論。https://rpc.cfainstitute.org/research/financial-analysts-journal/2018/faj-v74-n3-5
- Leippold & Rüegg (2018), *European Financial Management* 24(5):829–855 — 無顯著差異。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2887117
- Beneish, Lee & Nichols (2013), *FAJ* 69(2):57–82 — M-Score 排除價值。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2241717
- Skinner & Sloan (2002), *RAST* 7:289–312 — earnings torpedo 不對稱。https://papers.ssrn.com/sol3/papers.cfm?abstract_id=172060
- Hong & Kacperczyk (2009), *JFE* — The Price of Sin；排除的代價。https://w4.stern.nyu.edu/sternfin/mkacperc/public_html/sin.pdf
- DeMiguel, Garlappi & Uppal (2009), *RFS* 22(5):1915–1953 — 1/N。https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901
- Dawes (1979), *American Psychologist* 34(7):571–582。https://www.cmu.edu/dietrich/sds/docs/dawes/the-robust-beauty-of-improper-linear-models-in-decision-making.pdf
- Smith & Wallis (2009) / forecast combination puzzle 綜述：https://arxiv.org/pdf/2205.04216
- Cohen, Malloy & Pomorski (2012), *JF* 67(3):1009–1043 — Decoding Inside Information；82 bps/月。https://www.nber.org/papers/w16454
- Alpha Architect QVAL 漏斗（實務）：https://alphaarchitect.com/the-quantitative-value-investing-philosophy/ ; https://funds.alphaarchitect.com/qval/
- O'Shaughnessy composite（實務回測）：https://www.aaii.com/journal/article/finding-value-and-financial-strength-based-on-what-works-on-wall-street ; https://www.quant-investing.com/blog/how-and-why-to-implement-james-o-shaughnessy-s-trending-value-investment-strategy-world-wide
- Grinold & Kahn (1999), *Active Portfolio Management* — IR = IC×√Breadth、IC 加權合成。https://analystprep.com/study-notes/cfa-level-2/state-and-interpret-the-fundamental-law-of-active-portfolio-management-including-its-component-terms-transfer-coefficient-information-coefficient-breadth-and-active-risk-aggressiveness/
- 漏斗饑餓（實務）：https://pyinvesting.com/blog/12/heres-why-every-investor-should-backtest-their-investment-strategy/ ; https://www.stockrover.com/blog/stock-research/real-world-screener-performance/
- Einhorn (1970/1971) 非補償模型文獻：https://pubsonline.informs.org/doi/10.1287/mksc.1030.0032

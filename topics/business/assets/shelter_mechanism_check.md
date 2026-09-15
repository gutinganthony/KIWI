# 住房落後性與「升息壓低租金」因果鏈 — 查證報告
查證日期：2026-09-15。所有數字均為引用，未做任何推估。

## A 段：引用查核

### A1 NBER w34113 是否存在 — **成立**
- 主張：圖說「住房落後性引自 NBER 工作論文 w34113」。
- 查證：編號正確。**Market Rents and CPI Shelter Inflation**，Laurence M. Ball、Kyung Woong Koh，NBER WP 34113，**2025 年 8 月**。
- 內容確實在講 CPI 住房項落後市場（新租客）租金：論文指出三個落後來源 —— (1) 多數租客簽長期租約；(2) 續約留存租客的租金被平滑；(3) CPI 住房項本身以六個月租金變動衡量。以 ZORI 當市場租金代理，對 2015 年起的月資料建模。
- URL: https://www.nber.org/papers/w34113 ；NBER Digest 2025-10 導讀 https://www.nber.org/digest/202510/understanding-lag-between-cpi-shelter-inflation-and-market-rents ；SSRN 鏡像 abstract_id=5386631
- ⚠️ 但：這篇的賣點是**落後的機制與模型**，不是一個「3–4 季」的頭條數字。把季數掛在 w34113 名下是**張冠李戴的邊緣案例**（正確出處見 A2）。
- 未取得：全文與確切落後季數點估計（nber.org / ssrn / ideas.repec.org 三站皆被 egress proxy 擋）。

### A2 「CPI 住房落後新租客租金約 3–4 季」 — **成立**（但出處不是 w34113）
- 最常被引用的來源：Cleveland Fed / BLS 的 New Tenant Repeat Rent（NTRR）研究 —— Adams、Loewenstein、Montag、Verbrugge，*Disentangling Rent Index Differences: Data, Methods, and Scope*，Cleveland Fed WP 22-38（2022）。結論：**新租客租金通膨領先官方 BLS 全體租客租金通膨約 4 季**，且兩者落差幾乎完全由「新租客 vs 全體租客」的租金成長差異解釋。
  - https://www.clevelandfed.org/publications/working-paper/2022/wp-2238-disentangling-rent-index-differences
  - BLS 版 https://www.bls.gov/osmr/research-papers/2022/ec220100.htm
- 與 Ball–Koh 相關討論一致：住房項落後其他常見租金指標「約 3 到 4 季」；因為 CPI 衡量全體租客而非新租客，相對市場租金指標約落後 4 季。
- 對照實例（Cleveland Fed 口徑）：2024Q1 CPI 住房 +5.7%，同期新租客指數僅 +0.4%。
- ⚠️ 一個未驗證的修正：Cleveland Fed EC 2024-17《New-Tenant Rent Passthrough and the Future of Rent Inflation》指傳導是**漸進的**而非乾淨的 4 季平移（clevelandfed.org 被擋，無法取得確切數字）。文章若寫「約 3–4 季」不算錯，但寫成「4 季後全部反映完」會過度簡化。
- 判定：**成立**。建議把引用改掛 Cleveland Fed WP 22-38。

### A3 「目前市場新簽約租金年增約 1.9–2.0%」 — **錯誤（資料過期，且方向已反轉）**
- 1.9% 確實存在，但那是 **ZORI 2026 年 2 月**的讀數（當時是 2020 年 12 月以來最慢）。
  - https://www.zillow.com/research/february-2026-rent-report-36167/
- 2026 年之後**一路回升**（ZORI YoY）：6 月 +2.2%（$1,965）→ 7 月 +2.3%（$1,962）→ **8 月 +2.5%（$1,948）**，Zillow 自己的標題是「一年多來最快增速」、且明說「從上月 2.3%、一年前 2.0% 加速上來」。
  - https://www.zillow.com/research/august-2026-market-report/ ；https://zillow.mediaroom.com/2026-08-18-Rents-near-2,000,-rising-at-the-fastest-pace-in-over-a-year
- 其他指標（2026 年 8 月）：
  - Apartment List 全國租金指數 **-0.8% YoY**（4 月觸底 -1.6%，已連 7 個月環比上升，中位 $1,390）；全國多戶空置率 **7.1%，為 2021 年底以來首度下降**。 https://www.apartmentlist.com/research/national-rent-data
  - Apartments.com / CoStar：**8 月公寓租金四年來首次轉正**。 https://www.cnbc.com/2026/08/27/august-apartment-rents-turn-positive-for-the-first-time-in-four-years.html
  - BLS R-CPI-NTR（新租客租金）：最近一次公布為 **-2.43% YoY**（約 2026 年 2 月發布），且 **2026 年 4 月起因預算中斷＋2025 年 10 月資料未採集而暫停公布**。 https://www.bls.gov/cpi/research-series/r-cpi-ntr.htm
- **沒有任何主要指標目前讀在 1.9–2.0%。** 文章用的是半年前的數字，而且錯過了最關鍵的轉折：新簽約租金已經在**重新加速**。

### A4 「2026 年住房落後效應還能再壓低核心 CPI 約 37bp」 — **成立（數字真實）但出處錯、條件被刪**
- 原句：「Under the baseline forecast, below-average new-tenant rent growth will lower **headline CPI by 29bp and core CPI by 37bp in 2026**, relative to if shelter prices grew at 3.1 percentage points.」
- 出處：**Understanding CPI shelter inflation: The importance of the new-tenant/all-tenant rent gap**，*Journal of Housing Economics*，線上發表 **2026-01-09**。 https://www.sciencedirect.com/science/article/abs/pii/S1051137725000762
  （同文被 Texas A&M PERC 2026-06 部落格轉述 https://perc.tamu.edu/blog/2026/06/shelter-cpi.html）
- 同文的住房通膨路徑預測（年化）：2026H1 2.5pp、2026H2 2.1pp、2027H1 2.0pp。
- 三個必須補上的但書：
  1. **不是 w34113 算的**。若文章把 37bp 也掛在 NBER w34113 名下，是錯的。
  2. 37bp 是**相對於「住房項年增 3.1pp」這個反事實基準**的差額，不是「核心 CPI 會再掉 37bp」。刪掉基準等於改變了意思。
  3. 該預測用的是 2025 年底前的資料，**早於 2026 年新簽約租金回升**（見 A3）。以今天的資料看，這個 37bp 很可能偏高。
- 未取得：作者名單與模型完整假設（ScienceDirect 被 egress proxy 擋）。

---

## B 段：因果機制查核

### B1 使用者的反駁在文獻上成立嗎 — **成立，而且是主流實證結果**
支持使用者的證據：
- **Dias & Duarte (2019)**, *Monetary policy, housing rents, and inflation dynamics*, Journal of Applied Econometrics（Fed IFDP No. 1248）：緊縮性貨幣政策衝擊後，**房租上升**（與房價方向相反）；同時**租屋空置率下降、自有率下降**。機制正是使用者說的 tenure choice —— 利率上升使持有房屋的實質成本上升，部分家戶改為租屋，推升租金的相對價格。作者並指出房租的這個反應**解釋了文獻上「price puzzle」的一大部分**。
  - https://www.federalreserve.gov/econres/ifdp/files/ifdp1248.pdf ；https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.2679
- **Fed FEDS Note, 2024-05-03**（更新 Dias–Duarte）：貨幣政策衝擊可解釋自有率變異的 **~15%（衝擊後第一季）→ 中期 20–40% → 之後穩定在 ~30%**。通道不只存在，而且量化上不小。
  - https://www.federalreserve.gov/econres/notes/feds-notes/estimating-the-importance-of-monetary-policy-shocks-for-variation-in-the-u-s-homeownership-rate-20240503.html
- 2026 年市場面佐證：買房約比租房貴 50%，需求從被擠出購屋的家戶流向租屋；首購族年齡中位數升至 **40 歲**（有紀錄以來最高）。 https://commercialobserver.com/2026/09/higher-mortgage-rates-2026-multifamily/

削弱使用者的證據（必須一起看）：
- **本輪自有率幾乎沒掉**：2022 年 65.8% → 2023 年 65.2% → 2024 年約 65.6% → 2025 年約 65.3% → **2026Q1 65.3%**。2022–23 的猛烈升息並沒有把自有率明顯推低，代表**這一輪 tenure-switch 的邊際流量有限**。 https://www.census.gov/housing/hvs/files/currenthvspress.pdf
- 同期供給潮的量級遠大於 tenure 流量（見 B3）。
- ⇒ 使用者的**方向**對，但不足以推出「租金應該上漲」；這個通道被更大的供給衝擊蓋過了。

### B2 反方向通道與淨效果
**往上推租金（與文章相反）**
- (a) tenure choice：升息 → 買不起 → 轉租 → 租屋需求↑（B1）。
- (b) **供給通道**：升息 → 開發融資成本↑ → 多戶開工大跌。2Q23→2Q24 多戶開工 **-37.1%**；2023→2025 多戶開工掉 **逾 40%**，且因建材成本、高利率與陽光帶供給過剩疑慮預期持續疲弱。新供給稀缺 → 未來租金回升。**這正是 2026 年正在發生的事**（空置率首度下降、租金再加速）。
  - https://naahq.org/news/multifamily-construction-trends-summer-2025 ；https://www.credaily.com/briefs/how-rising-apartment-returns-impact-new-housing-supply/

**往下壓租金**
- (c) **所得／家戶形成通道**：升息 → 經濟轉弱、住房成本與通膨壓力 → 合租、跟父母住 → 家戶形成停滯。實績：家戶淨增 2020→21 **+77 萬**、2021→22 **+198 萬**、2022→23 **僅 +23 萬**。 https://www.jchs.harvard.edu/blog/six-takeaways-americas-rental-housing-2024
  ⚠️ 注意：這條通道壓低租金靠的是**所得與家戶形成**，不是文章寫的「買房的人變少」。文章寫錯了機制。
- (d) 房價下跌 → 住房項下跌：**在美國 CPI 基本不成立**，因為 OER 是由租金推算、不是由房價推算。 https://www.brookings.edu/articles/how-does-the-consumer-price-index-account-for-the-cost-of-housing/

**文獻認定的淨效果方向**：Dias–Duarte 的 SVAR 淨效果是**緊縮 → 房租上升**。也就是說主流實證的淨方向與文章相反。

### B3 2023–2026 降溫的主流歸因 — **供給潮＋家戶形成正常化，假說成立**
- **完工量**：2024 年多戶完工 **608,000 戶，1986 年以來最高**；2025 年即使掉 20% 仍達 **488,000 戶**。這批案子是 **2021–22 低利率時期啟動**的。 https://www.jchs.harvard.edu/blog/six-takeaways-americas-rental-housing-2026
- **空置率**：2022 年初歷史低 2.5% → 2023Q3 5.5% → 2024 年底 5.2%（Census 口徑）；業界口徑自 2024 年底維持 9.2–9.4%，2026 年才首度回落至 8.9%。JCHS 明指**歷史性強勁的多戶完工是推高空置率的主因**。
- **租金**：2022Q1 年增 +15%（歷史高點）→ 2023Q3 +0.4% → 2023 年中起要價租金增速在零附近徘徊 → 2025Q4 專業管理公寓 **-0.6% YoY**。
- **Zillow 自己的歸因**：2026 年 2 月報告標題就是「**An Expanding Supply of Rentals Keeps Rent Growth in Check**」，理由列的是高空置、持續完工、更多單戶住宅轉入出租市場 —— 全是供給，沒有一項是「升息壓抑租屋需求」。
- **經濟學家歸因**：開發商在 2020–21 低利率與遠距工作移民潮下搶建，這波完工潮才是 2024–25 租金降溫的功臣；升息反而是**減少**供給的力量。 https://www.cnbc.com/2025/02/09/the-2025-renters-market-wont-last-economists-say.html ；https://www.redfin.com/news/rental-tracker-august-2025/
- 家戶形成正常化：見 B2(c) 的三年數字。

### B4 「住房對利率敏感」嚴格講站不站得住 — **要分層，混用會出錯**
- **高度敏感（升息 → 下降，方向明確且快）**：成屋銷售、房貸申請量、新屋與多戶開工、房價、建商股。
- **不敏感、短期甚至反向**：**租金**，以及 CPI 裡佔約三分之一權重的**住房項**。文獻上升息對租金的淨效果是**正的**，而且 CPI 住房項還要再落後 3–4 季才反映市場租金。
- ⇒ 「住房對利率敏感」在講**量與價（成交、開工、房價）**時成立；拿來推論**租金與 CPI 住房項會因為升息而降溫**，不成立。

---

## 我原本的因果鏈錯在哪、正確的說法應該是什麼

**原鏈**：升息 → 房貸變貴 → 買房的人變少 → 租金漲不動。

**錯在三處**
1. **中間那一步方向錯了**。「買房的人變少」的直接後果是那些人**留在租屋市場**，租屋需求上升。Dias–Duarte 的 VAR 實證正是：緊縮衝擊後房租上升、租屋空置率下降、自有率下降。使用者的反駁不只是直覺，是文獻的主流結論。
2. **漏掉了同方向的供給通道**。升息還會把多戶開工砍掉四成以上，未來供給更少，這也是推升租金的力量。升息的兩條直接通道（需求↑、供給↓）**都指向租金上漲**。
3. **把真正的原因誤植**。2023–26 租金降溫的主因是 **2021–22 低利率期間啟動、2023–25 交屋的多戶供給潮**（2024 年完工 608k 戶，1986 年以來最高）＋**疫情期間異常家戶形成的正常化**（家戶淨增從 2021–22 的 198 萬掉到 2022–23 的 23 萬）。這波供給是**低利率的產物**，不是升息的功勞 —— 把它算成升息的傳導成果，因果完全反過來。若真有「升息壓低租金」的通道，走的是**所得與家戶形成**（經濟轉弱 → 合租、跟父母住），不是「買房的人變少」。

**建議改寫**
> 住房的**成交量、開工與房價**對利率高度敏感，但 CPI 裡佔約三分之一權重的住房項衡量的是**租金**，它對利率不敏感、短期甚至反向：升息把邊際購屋者推回租屋市場（需求↑），同時砍掉多戶新建（供給↓），兩者都偏向推升租金。2023–25 的住房通膨降溫，主因是 2021–22 低利率時期啟動、2023–25 集中交屋的多戶供給潮，加上疫情期間異常家戶形成的正常化，再經由 CPI 住房項相對新租客租金約 3–4 季的統計落後遞延反映（Cleveland Fed WP 22-38）。這條落後管道現在正在**反向運作**：新簽約租金自 2026 年 2 月的 +1.9% 回升至 8 月的 +2.5%，空置率 2021 年底以來首度下降，**住房項在 2026 下半到 2027 年是通膨的上行風險，不是下行助力**。

**必須一併修的三件事**
- 圖說：37bp 的出處是 *Journal of Housing Economics*（2026-01-09），不是 NBER w34113；「3–4 季」的出處是 Cleveland Fed WP 22-38，也不是 w34113。w34113 只支持「有落後、落後的三個來源」。
- 內文「目前新簽約租金約 1.9–2.0%」：**改成 2026 年 8 月 ZORI +2.5%**（並註明 Apartment List -0.8%、BLS R-CPI-NTR 已於 2026 年 4 月停止公布）。
- 37bp 要補回反事實基準（相對於住房項年增 3.1pp），並註明該預測早於 2026 年租金回升。

**未取得**：Ball–Koh 全文與其確切落後季數點估計（nber.org / ssrn / ideas.repec.org 被擋）；JHE 該文作者與 37bp 完整假設（sciencedirect.com 被擋）；Cleveland Fed EC 2024-17 的 passthrough 確切數字（clevelandfed.org 被擋）；IFDP 1248 脈衝反應的量級與持續期（federalreserve.gov 被擋）；BLS R-CPI-NTR 2026Q1/Q2 讀數（已停刊）。

# 台股公開籌碼數據的預測力實證研究筆記

研究日期：2026-07-10。方法：WebSearch（多數台灣網站 WebFetch 被 403 擋，細節多來自搜尋快照）。
信心標籤：【學術實證】同儕審查期刊/博碩論文、【券商研究/量化實務】FinLab 等有回測數字的實務研究、【坊間說法】財經媒體與投顧教學文。

---

## 總判定（先講結論）

| 訊號 | 判定 | 一句話 |
|---|---|---|
| 外資買賣超 | **有實證支持，但可交易性有限** | 外資整體確實有 alpha（學術鐵證），但散戶「跟單外資」個股策略回測輸 0050；指數層級外資連賣反而是買點（反指標） |
| 投信買賣超 | **有實證支持（三者中最有價值）** | 年底作帳/window dressing 學術上確認存在且伴隨反轉；投信買超單獨用輸大盤，搭配營收動能才有顯著超額報酬 |
| 董監申報轉讓/質押 | **有實證支持（當風險濾網用）** | 申讓後負異常報酬（小型股尤甚）、高質押比預測財務危機與崩盤風險——台灣本土文獻最扎實的一塊 |
| 集保千張大戶比率 | **證據薄弱，接近坊間迷思** | 查無嚴謹公開學術實證；機制合理但充滿假訊號（信託/質押移轉、門檻不隨市值調整），連推廣它的平台都承認「無足夠統計數據」 |

**最有價值的組合條件**：投信首次/連續買超 × 小市值（市值後 50%）× 月營收動能，同時排除「董監近期申讓或質押比 >50%」的個股；外資現貨買超需對照期交所外資期貨淨部位過濾避險/套利雜訊。

---

## 1. 外資買賣超

### 學術實證
- **Barber, Lee, Liu & Odean, "Just How Much Do Individual Investors Lose by Trading?" (Review of Financial Studies, 2009)**：用台灣全市場完整成交資料（1995–1999）。散戶整體年績效落後 3.8 個百分點（≈台灣 GDP 的 2.2%）；機構整體年賺 1.5pp，其中**外資拿走機構利潤近一半**。這是「外資在台股有系統性 alpha」最強的學術鐵證。同作者群 "Who Gains from Trade? Evidence from Taiwan" 結論一致。【學術實證】
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=529062
- **"Foreign investors' trading behavior and market conditions: Evidence from Taiwan" (J. of Multinational Financial Management, 2019)**：外資資金流對**次日** TAIEX 報酬有顯著預測力，其他法人沒有；但外資也追漲（雙向因果），牛市時交易更積極。【學術實證】
  - https://www.sciencedirect.com/science/article/abs/pii/S1042444X19300490
- **"Structural changes in foreign investors' trading behavior..." (PMC, 2020)**：外資開放程度提高後對台股有穩定作用。【學術實證】
- **碩士論文（台大？Airiti 收錄，2021）「外資買賣超對於台灣股市的影響與投資策略研究」**：跟隨外資每日買賣超**只在小型股（日市值後 50%）有超額報酬**；有效期極短（約 1 天）；多空市場皆有效、牛市更強；CAPM 調整後 alpha 仍在。【學術實證（碩論等級）】
  - https://www.airitilibrary.com/Article/Detail/U0001-1801202112300400
- 市場狀態與法人群聚（herding）研究（Cogent Economics & Finance, 2025）：機構群聚在**空頭**時對未來超額報酬有正向貢獻，多頭時反而拖累——跟單訊號的價值視市場狀態而定。【學術實證】

### 券商研究/量化實務
- **FinLab（2012–2026 共 14 年外陸資資料）**：外資連續賣超越久，大盤後續報酬越高——連賣 ≥10 日後 60 日含息報酬中位數 **+8.2%**（指數層級「外資賣超」是反指標，因為外資賣超常伴隨匯率/避險因素而非資訊）。「外資連 5 日賣超就買進」個股策略年化僅 +8.8%、日 Sharpe 0.48，遠輸同期 0050 含息 +20.6%。【量化實務】
  - https://finlab.finance/blog/foreign-investor-selling-why-market-rises
- **FinLab 三法人策略回測（2015-01–2026-06，含費稅）**：任何**單一**法人籌碼訊號（順勢或逆勢）都輸買進持有 0050。【量化實務】
  - https://finlab.finance/blog/institutional-strategy

### 訊號失真來源
1. **假外資**：本土大股東/主力繞道香港等地以外資名義下單。金管會 2025 年全面清查約 400 個券商據點，朝「最終受益人」方向管理。辨識特徵：外資單集中在本土券商分點、頻繁隔日進出、標的為小型冷門股。→ 小型股的「外資買超」可信度要打折。【新聞/監管動態】
   - https://finance.ettoday.net/news/2952329
2. **期現貨對沖/套利**：外資現貨買超可能只是避險或套利腳（例：台指期大正價差時空期貨＋買權值股組合，每口約 911 萬元現貨），與方向性看多無關。判讀須搭配期交所三大法人期貨未平倉（https://www.taifex.com.tw/cht/3/futContractsDate）。【實務機制，無爭議】
3. 外資買賣超把「長線主權基金」與「外資自營/隔日沖」混在同一數字（豹投資有摩根大通隔日沖分點整理）。【坊間/實務】

---

## 2. 投信買賣超

### 學術實證
- **"Window Dressing, Fund Performance, and Fund Flows: Insights into Taiwan's Equity Mutual Funds"（台灣樣本，科技部補助，ResearchGate 2025 上架）**：台股股票型基金確有 window dressing；績效差的經理人、持股集中前十大的基金更會做；**年底效果 > 季底**；高 WD 基金長期績效與資金流入反而更差。【學術實證】
  - https://www.researchgate.net/publication/393618875
- **Portfolio pumping（拉尾盤灌淨值）國際文獻**：pumping-reversal 型態在**年底顯著、季底不顯著**；明星基金重倉股 12 月異常報酬與其後兩個月差距約 231bp（中國樣本，Emerging Markets Review 2019；美國 JFE 2024 同型態）。台灣本土 pumping 論文存在（NTOU JMSTT 有一篇 "Evidence from the Taiwan Mutual Fund Market"，全文 403 無法驗證細節——**查到篇名但內容未驗證**）。【學術實證（跨市場）＋台灣篇未驗證】
- 含義：**作帳行情真實存在但伴隨明確反轉**——作帳月買進的人在跨季/跨年後面臨統計上可測的賣壓。

### 券商研究/量化實務
- **FinLab 回測（2015-01–2026-06）**：投信買超**單獨**當訊號輸 0050；但「**投信買超 × 月營收動能**」年化 **+33.9%**（同期 0050 約 +20.6%）。代價：最大回撤 -45.5%、最差年度 -41.5%、僅 10 檔持股、平均持有約一個月（高週轉）、為樣本內回測。這是公開可查的最強籌碼組合證據。【量化實務】
- 投信買超訊號有效的結構性理由：投信規模小、集中買中小型股、受季/年度績效評比驅動 → 買超的「資訊+價格壓力」都集中在小票上。

### 坊間說法（標示為坊間）
- 「認養股」：投信低檔佈局→主升段；持股 >8% 多家認養時有「恐怖平衡」反向結帳風險；持股近 10% 上限時「只出不進」動能衰竭。（CMoney、StockFeel、豹投資教學文）
- 作帳月份重要性：年底 > 半年底 > 季底；行情多從 10 月起。
- 連推廣作帳行情的媒體（Money101 等）自己註明：「作帳行情是否有利可圖，目前並無足夠的統計數據證明」。

---

## 3. 董監事持股異動（申讓/質押/增持）

### 申報轉讓＝負訊號（有實證）
- **"The market response of insider transferring trades and firm characteristics in Taiwan" (Emerging Markets Review, 2013)**：內部人申讓公告日負異常報酬偏小、**其後累積負異常報酬擴大**（市場緩慢消化）；**公司越小、B/M 越高，負報酬越大**。台灣制度特點：申報後 3 日才能轉讓，訊號有法定前置期，散戶來得及反應。【學術實證】
  - https://www.sciencedirect.com/science/article/abs/pii/S1566014113000381
- **"Insider Trading Performance in the Taiwan Stock Market" (International Journal of Business, 2004)**：台灣內部人交易有超額報酬。【學術實證】
- **"Insider trading, accrual abuse, and corporate governance in emerging markets — Evidence from Taiwan" (Pacific-Basin Finance Journal, 2013)**：內部人**買進與未來盈餘正相關**、與過去報酬負相關——增持同時反映逆勢信念與對未來現金流的私有資訊 → 申報增持是正訊號有學理與實證支撐。【學術實證】
- 注意：申讓有五種方式（一般交易/盤後定價/贈與/信託/私下轉讓），**只有集中市場申讓與大額私下轉讓才是壞消息**，贈與/信託多為節稅（CMoney 教學）。【坊間但合理】

### 董監質押比＝風險訊號（台灣本土文獻最扎實）
- 台灣自 1998 年強制揭露控制股東質押。多篇研究（含中山管理評論 2013；TEJ 信用評等研究）：**質押比越高 → 次年財務危機機率越高、公司價值越低、股價崩盤風險越高、公司風險承擔越低**。質押的機制風險：股價跌 → 補擔保品/斷頭 → 賣壓自我強化。【學術實證】
  - https://mgtr.cm.nsysu.edu.tw/Upload/Journal/106/2010108/635215818037127724.pdf
- 制度佐證：公司法 197-1（2011 修法）——董事質押超過選任時持股 1/2，超額部分無表決權（立法者都認證這是治理風險）。
- 國際延伸：印度/中國 promoter pledging 與 crash risk 文獻結論一致。

---

## 4. 集保戶股權分散（千張大戶比率）

- **查無嚴謹學術實證**。針對「千張大戶持股比率變化 → 後續報酬」的期刊論文或博碩論文，多輪搜尋（中英文、ndltd）均未命中直接研究。台灣量化學術文獻本來就少，此為有效的「查無」結論。
- 現有內容全是【坊間說法】：StockFeel、CMoney、wistock、玩股網教學文。其論述：大戶連續加碼＋總股東人數下降＝籌碼集中＝偏多。但這些文章自己承認「並不是大戶增加股價就一定漲」「單一持股指標錯誤率明顯高於多指標交叉驗證」。
- 結構性缺陷（為何難有 alpha）：
  1. **週頻且遲滯**：每週五結算、週六早上公布，快錢早跑完；
  2. **1000 張固定門檻不隨市值調整**：台積電千張只是中實戶，小型股千張就是內部人——跨股不可比；
  3. **假訊號多**：內部人把持股移入信託/質押/借券，帳戶分級就變動，看似「大戶出貨/進貨」實則左手換右手；
  4. 與董監申報資料高度重疊（大戶常＝內部人），增量資訊有限。
- 判定：**證據薄弱**。當「排除訊號」（大戶連續數週減碼的小型股不要碰）可能比當「買進訊號」合理，但這也未經公開嚴謹檢驗。

---

## 5. 數據源可程式化（全部免費）

| 來源 | 內容 | 格式/端點 | 頻率 | 歷史深度 |
|---|---|---|---|---|
| TWSE OpenAPI | 上市各類盤後統計 | https://openapi.twse.com.tw/ （Swagger, JSON） | 每日 | 多為最近資料 |
| TWSE T86 | 三大法人個股買賣超日報 | https://www.twse.com.tw/zh/trading/foreign/t86.html （網頁可下 CSV；rwd JSON 端點同名） | 每日盤後 | 2012+ |
| TWSE TWT38U/TWT44U | 外資/投信買賣超彙總 | 同上 twse.com.tw | 每日 | 同上 |
| TPEx OpenAPI | 上櫃對應資料 | https://www.tpex.org.tw/openapi/ | 每日 | — |
| TAIFEX OpenAPI | 三大法人期貨/選擇權部位（過濾外資避險必備） | https://openapi.taifex.com.tw/ ＋ https://www.taifex.com.tw/cht/3/futContractsDate | 每日 | — |
| TDCC 集保股權分散 | 15 級距人數/股數/比例 | 開放資料專區＋ https://openapi.tdcc.com.tw/tdcc-opendata-api-docs ；data.gov.tw dataset 11452 | 每週（週五結算，週六 09:00 公布） | **官方開放資料僅最近一週全表；官網單檔查詢僅 1 年** |
| MOPS 公開資訊觀測站 | 董監持股明細/內部人申讓 | 無官方 API，但 AJAX POST 可爬：mops.twse.com.tw/mops/web/ajax_stapap1（董監持股）、t146sb05 等 | 每月＋事件申報 | 深 |
| **FinMind（GitHub 開源）** | 一站整合 50+ 資料集：三大法人（TaiwanStockInstitutionalInvestorsBuySell）、**集保分級 TaiwanStockHoldingSharesPer（歷史回補到 2007-07）**、外資持股、融資券、借券 | pip install finmind；REST api.finmindtrade.com/api/v4/data | 每日更新 | 2007+（集保）；有免費額度限制 |
| 其他 | 豹投資/Goodinfo/玩股網（分點、隔日沖整理） | 網頁，爬蟲灰色地帶 | — | — |

- 結論：**三類訊號全部可零成本程式化**。最省事路徑＝FinMind 開源套件（含集保 2007 年起歷史，解決 TDCC 官方只給一週的問題）；要去除第三方依賴則直接接 TWSE/TPEx/TDCC OpenAPI＋MOPS AJAX 爬蟲（Cupoy 教材與 GitHub SuYenTing/Quantitative_investment_material_in_R 有現成範例）。
- 相關 GitHub：FinMind/FinMind、twjackysu/TWSEMCPServer（TWSE OpenAPI 的 MCP server）、smalldan1022/Taiwan-Stocks。

---

## 6. 給使用者的操作含義（KIWI 慢訊號脈絡）

1. **值得建的慢訊號**：投信買超（首次出現/連續，配月營收 YoY）＞ 董監質押比＋申讓（負面濾網）＞ 外資買賣超（只在小型股、且要期貨部位過濾）＞ 大戶比率（最多當排除條件）。
2. 外資買賣超在**指數層級是反指標**（連賣後 60 日中位數 +8.2%），在**個股層級只有小型股短窗有 alpha**——「跟外資買權值股」是最常見的坊間迷思。
3. 投信訊號的風險窗口可預先排程：Q4（尤其 12 月）進場者要在 1 月面對 pumping reversal。
4. 台灣籌碼透明度確實是在地優勢（美股沒有每日法人別個股流量、沒有週頻股權分級），但「透明」不等於「未被定價」——單一籌碼訊號的超額報酬在 2015 後大多被吃掉（FinLab 回測），組合條件才有殘餘 alpha。

## 附：主要來源清單
- RFS 2009 Barber/Lee/Liu/Odean：https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/justhowmuchdoindividualinvestorslose_rfs_2009.pdf
- JMFM 2019 外資行為：https://www.sciencedirect.com/science/article/abs/pii/S1042444X19300490
- EMR 2013 內部人申讓：https://www.sciencedirect.com/science/article/abs/pii/S1566014113000381
- PBFJ 2013 內部人與應計：https://www.sciencedirect.com/science/article/abs/pii/S0927538X1300036X
- 台灣基金 WD 論文：https://www.researchgate.net/publication/393618875
- 中山管理評論 2013 質押：https://mgtr.cm.nsysu.edu.tw/Upload/Journal/106/2010108/635215818037127724.pdf
- 2021 外資碩論：https://www.airitilibrary.com/Article/Detail/U0001-1801202112300400
- FinLab 三法人回測：https://finlab.finance/blog/institutional-strategy
- FinLab 外資賣超 14 年統計：https://finlab.finance/blog/foreign-investor-selling-why-market-rises
- 假外資清查：https://finance.ettoday.net/news/2952329
- TDCC 開放資料：https://www.tdcc.com.tw/portal/zh/stats/openData ・ data.gov.tw/dataset/11452
- FinMind：https://github.com/FinMind/FinMind ・ https://finmind.github.io/tutor/TaiwanMarket/Chip/

## 未解／低信心事項
- NTOU JMSTT 台灣 portfolio pumping 論文全文 403，僅確認存在，量級未驗證。
- FinLab 回測為樣本內、含存活偏差可能；+33.9% 年化那條策略集中 10 檔、MDD -45.5%，不可直接當期望值。
- 大戶比率「查無實證」是基於公開文獻搜尋；付費學術庫（TEJ、Airiti 全文）可能有未公開命中。

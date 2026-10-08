# 06 分析師共識 EPS 資料來源盤點（回測用歷史時點＋日常用目前值）

> 查詢日：**2026-10-07**（本檔所有網址、HTTP 狀態都是當天的實測或查詢結果）
> 用途：pe-forecast 的「看法修正」參數 ＝ ln(使用者 EPS ÷ 市場共識 EPS)。
> 需要兩種資料：(A) **歷史時點共識**（美股、至少 S&P 500 科技股、FY1/FY2 或 NTM、2015 年以後每月一筆），用來估「股價對共識修正的反應係數」；(B) **目前共識**，讓工具日常可用。
>
> 標記：**【實測】**＝本 session 用 curl 實際打過｜**【來源】**＝有網頁或程式碼可查｜**【推論】**＝由事實推出、未直接驗證｜**【不確定】**＝查不到或互相矛盾，要再驗證。
> 樣本檔與探測腳本放在 scratchpad（`/tmp/claude-0/-home-user-KIWI/20132285-6aa6-5c00-b83e-be5e8c3faf5e/scratchpad/consensus_probe/`），**沒有**寫進 repo。

---

## 0. 結論

1. **目前共識（B）現在就有，不用開任何網域**【實測】：Yahoo 的「預設產業選股器」端點 `query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=ms_technology` 不需要 crumb，回 HTTP 200。每檔都有 `epsCurrentYear`（＝本財年，0y/FY1）、`epsForward`（＝下一財年，+1y/FY2）、`epsTrailingTwelveMonths`、`forwardPE`、價格。科技類共 402 檔（股價 >$5、在 NYSE/Nasdaq 掛牌），我列的 66 檔 S&P 500 科技股名單裡只缺 ENPH、APP。另外兩個類股選股器（通訊服務、非必需消費）可補上 GOOGL/META/AMZN/TSLA。缺點是只有平均值，沒有分析師數、高低值，也沒有 7/30/60/90 天前的數字。
2. **免費又有「歷史時點」的資料，我只找到一個勉強堪用的**【來源】：**Open Source Asset Pricing（Chen & Zimmermann）公開的 `FEPS` 訊號**。它就是 I/B/E/S 每月彙總裡 FY1 共識的平均值（`statsumu_epsus`，fpi=1，`meanest`，**未經分割調整**），以 permno×月份為單位，從 1983 年開始，最新版是 2025.10 release（資料迄日【不確定】，推論到 2024-12 左右）。限制：**只有 FY1、沒有 FY2**、以 permno 而不是 ticker 當鍵、數字沒做分割調整、財年換年那個月會跳一下、檔案放在 Google Drive（這裡被擋，要在 Mac 上下載或開放網域）。
3. **其他免費來源都不是 FY1/FY2 的月度歷史時點**：Yahoo/yfinance、Alpha Vantage、Estimize 的 GitHub 資料集，給的都是「每季財報公布前最後一刻的單季共識」（本質是盈餘驚喜資料），或「目前值＋7/30/60/90 天前的值」。真正的 FY1/FY2 月度共識歷史要靠付費或學術帳號：WRDS I/B/E/S、LSEG Workspace、FactSet、Bloomberg、Capital IQ／Koyfin／TIKR／YCharts。

**最佳方案排序**
① 日常用：在雲端直接抓 Yahoo 選股器（0y/+1y 時間加權成 NTM），工具保留手動覆寫欄位。
② 回測用：在 Mac 上下載 OSAP 的 `FEPS`（外加 `sfe`、`AnalystRevision`），先估 FY1 修正的反應係數。使用者若有 WRDS 或 LSEG/FactSet/Bloomberg 帳號，改匯出 FY1＋FY2 月度共識（最好）。
③ 從今天起每週存快照（雲端選股器＋Mac 上用 yfinance 抓 earningsTrend），慢慢累積自己的歷史時點資料。

---

## 1. 規格提醒（踩坑前先讀）

- **EPS 口徑不一致**【推論，重要】：pe-forecast 的 EPS 口徑是「目標日已公布的最近四季 **GAAP 稀釋** EPS」，市場共識通常是 **調整後（street／non-GAAP）EPS**。實測 Yahoo 選股器的 `epsTrailingTwelveMonths`（AAPL 8.72）＝ timeseries 的 `trailingDilutedEPS`（8.72，四季 1.85+2.84+2.01+2.02），所以 **Yahoo 的 TTM 是 GAAP**，但 `epsCurrentYear`/`epsForward` 很可能是調整後口徑（估計值的資料供應商與口徑【不確定】）。所以 ln(使用者 EPS ÷ 共識) 有兩種做法：一是使用者另外輸入一個「調整後口徑 EPS」只拿來算這個比值；二是估一個 GAAP 與調整後的差距係數。調整後與 GAAP 差距大的公司（股權激勵佔比高的軟體股、有攤銷的公司）會出現系統性偏差。
- **期間要對齊**【推論】：使用者的 EPS 是「12 個月後的 TTM」，相當於從現在起往後四季，所以對應的共識應該是 **NTM（未來 12 個月）**，而不是 FY1。常用近似：NTM ≈ w·FY1 + (1−w)·FY2，w ＝ FY1 剩下的月數 ÷ 12（TIKR 就是這樣算的【來源】）。只有 FY1 的歷史資料（例如 OSAP）在財年後段會偏離 NTM。
- **ADR 與外國公司的幣別陷阱**【實測】：選股器資料裡 BABA 的 `epsCurrentYear`＝44.07、`epsForward`＝9.23，兩個欄位幣別不一致（一個人民幣、一個美元）。TSM/ASML/SAP 的 `financialCurrency` 也跟報價幣別不同。**限定只用以美元報告的美國公司**，或逐檔檢查。舊教訓（agents/LEARNINGS.md 2026-07-26）：Yahoo 對日韓小型股的 forwardPE 嚴重失真。

---

## 2. 這個雲端環境現在就能抓到的（實測）

### 2.1 Yahoo 預設產業選股器 ★（目前共識，免 crumb）

| 項目 | 內容 |
|---|---|
| 端點 | `https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=<ID>&count=250&start=<位移>`（`/ws/screeners/v1/finance/screener/predefined/saved` 是同一支，同樣回 200） |
| HTTP | **200**【實測 2026-10-07】，連續約 10 次請求都沒被限流 |
| 需要什麼 | 什麼都不用（不用 cookie、crumb、key） |
| scrIds | `ms_technology`（共 402 檔）、`ms_communication_services`（144）、`ms_consumer_cyclical`（320）【實測】；其他 `ms_*` 類股選股器應該也有（推論） |
| 分頁 | 用 `start=250` 取第 2 頁【實測】（參數 `offset=` 沒有作用，會回到第 1 頁） |
| 欄位 | `epsCurrentYear`、`epsForward`、`epsTrailingTwelveMonths`、`forwardPE`（＝價格 ÷ epsForward，AAPL：333.63/9.58285＝34.815，跟欄位值一致）、`priceEpsCurrentYear`、`regularMarketPrice/Time`、`earningsTimestamp`、`marketCap`、`averageAnalystRating`、`currency/financialCurrency` |
| 欄位意義 | `epsCurrentYear`＝0y（還沒公布的本財年），`epsForward`＝+1y【推論，有佐證】：AAPL 的 FY2026 九月剛結束還沒公布，TTM 8.72、0y 8.83、+1y 9.58；MSFT 的 FY2026 已公布，0y 19.77 就是 FY2027 |
| 篩選條件 | 股價 >5、sector＝Technology、交易所 NMS/NYQ/NAS（從回應的 `criteriaMeta` 讀到）【實測】 |
| 涵蓋率 | 我列的 66 檔 S&P 500 科技股名單裡只缺 ENPH、APP，有列到的全都有 `epsForward`【實測】 |
| 歷史時點？ | **沒有**，只有當下值 |
| 限制 | 沒有分析師數、高/低、修正趨勢；不能指定任意 ticker（POST 自訂選股器回 401 "Invalid Crumb"）；Yahoo 隨時可能改版或限流 |

樣本：`consensus_probe/yahoo_screener_snapshot_2026-10-07.csv`（三個類股共 866 列，137KB）。腳本：`consensus_probe/snap_yahoo_screener.py`（標準函式庫、每頁間隔 1.5 秒）。

```bash
curl -sS -A 'Mozilla/5.0' 'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=ms_technology&count=250&start=0' \
 | jq '.finance.result[0].quotes[] | {symbol, epsCurrentYear, epsForward, epsTrailingTwelveMonths, regularMarketPrice}'
```

### 2.2 Yahoo fundamentals-timeseries 的歷史 forward P/E → 反推出的共識（很短）

| type | HTTP | 期間（AAPL 實測） |
|---|---|---|
| `quarterlyForwardPeRatio` | 200 | 5 個季末（2025-06-30 → 2026-06-30） |
| `annualForwardPeRatio` | 200 | 4 個財年末（2022-09-30 → 2025-09-30） |
| `trailingForwardPeRatio` | 200 | 7 個不規則日期（2024-06-10 → 2026-09-17） |
| `trailingPegRatio`/`quarterlyPegRatio` | 200 | 同上，期間短 |
| 自己猜的估計值 type（`annualEpsEstimate` 等 16 種） | 404 | 不存在 |

反推共識 ＝ 當日價格（v8 chart 抓得到）÷ forward P/E。**只有 1–4 年、而且點很稀**，不夠拿來估係數，只能拿來對照最近幾季。forward P/E 用的是哪個 forward 口徑（FY2 還是 NTM）【不確定】：AAPL 2026-09-17 的 trailingForwardPeRatio 是 35.2，跟選股器的 forwardPE 34.8 很接近。

### 2.3 Yahoo 其他 query1 端點（實測一覽）

| 端點 | HTTP | 備註 |
|---|---|---|
| `/v8/finance/chart`、`/v7/finance/spark`、`/v1/finance/search`、`/v1/finance/quoteType`、`/v6/finance/recommendationsbysymbol` | 200 | 沒有共識 EPS |
| `/ws/insights/v2/finance/insights` | 200 | Trading Central 技術面與估值訊號，沒有 EPS 共識 |
| `/v10/finance/quoteSummary?modules=earningsTrend` | **401** | 要 cookie＋crumb |
| `/v7/finance/quote`、`/v7/finance/options`、POST `/v1/finance/screener` | 401 | 要 crumb |
| `/v1/test/getcrumb` | 429 → 401 | 沒有 cookie 就拿不到 |
| `/v1/finance/visualization`（GET） | 405 | 是 POST 端點，要 crumb；yfinance 原始碼註記「2025 夏天起 Yahoo 停止更新這支」【來源】 |
| `/v11/...`、`/v6/finance/quoteSummary` | 404 | — |

### 2.4 GitHub 上找得到的公開資料集（raw.githubusercontent.com 與 `git clone` 可用，api.github.com 與 github.com 網頁用 curl 是 403）

| repo | 可下載？ | 內容 | 期間／更新 | 歷史時點？ | 能不能用 |
|---|---|---|---|---|---|
| [Iliyan0508/Estimize_EPS_Prediction](https://github.com/Iliyan0508/Estimize_EPS_Prediction) | raw 206（Range 請求）【實測】 | `data/eps.csv`（80MB）：每家公司每季有「Wall Street Consensus」＋最後修正日、Estimize 共識、每位個別預估、實際值。`eps_gt.csv` 有 80,038 列、2,220 檔，AAPL/MSFT/NVDA/AVGO/ORCL/CRM/ADBE/AMD 都有【實測】 | 2011–2020；只 commit 過 1 次（2026-04-19） | **只有單季、財報前最後一刻的共識**，不是 FY1/FY2 月度 | 可以拿來做盈餘驚喜，對「修正反應係數」幫助有限；授權【不確定】 |
| [OpenSourceAP/CrossSection](https://github.com/OpenSourceAP/CrossSection) | git clone 可以【實測】 | 程式碼。`Signals/pyCode/Predictors/FEPS.py`：`FEPS = meanest`（fpi=1）；`AnalystRevision = meanest_t / meanest_{t-1}`（**沒有檢查財年換年**）；`sfe` 用 medest 並排除距財年結束 90 天內的月份 | 資料本身放在 Google Drive（見 §3.3） | 是（月度） | **最佳免費歷史來源**，見 §3.3 |
| [nelpower/ai-earnings-calendar](https://github.com/nelpower/ai-earnings-calendar) | git clone 可以 | `outputs/events.json`＋`archive.jsonl`：114 檔 AI 股下一季的 `eps_estimate`（來自 yfinance `.calendar`） | 254 個 commit，2026-05-29 → 2026-10-07，每天更新 | git 歷史等於每天的快照，但**只有下一季**、只有 4 個月 | 太短，最多當交叉驗證 |
| [zzwjlwwdtg/quant-trading-framework](https://github.com/zzwjlwwdtg/quant-trading-framework) | git clone 可以 | `docs/data/equity_outlook__ticker-*.json`：`analyst_consensus.forward_eps`、`n_analysts` 等（NVDA forward_eps 15.8，跟選股器的 15.799 一致） | NVDA 那個檔案有 1,731 個 commit，從 2026-08-14 開始 | git 歷史是快照，但只有約 2 個月、只有少數 ticker | 太短 |
| [Lina-zar/Earnings-predictor](https://github.com/Lina-zar/Earnings-predictor) | git clone 可以 | 只有程式碼與報告。`reports/probe_summary_2026-09-26.csv` 是第三方實測：Alpha Vantage `EARNINGS` 的季度 `estimatedEPS` AAPL 可回溯到 1996-03；yfinance 財報日期有 100 列、可回溯到 2002 | — | 單季、財報前最後一刻 | 證明季度驚喜資料在 Mac 上抓得到 |
| [fundamental-research-labs/streetbench](https://github.com/fundamental-research-labs/streetbench) | git clone 可以 | 200 檔 2026Q2 的個案；README 說明**因授權問題沒有附共識數值** | 2026-09 | — | 不能用 |
| [JamesWhiteleyIV/Equity-Data-Web-Scraper](https://github.com/JamesWhiteleyIV/Equity-Data-Web-Scraper)、[disanalyst/earning_estimates_scrapper](https://github.com/disanalyst/earning_estimates_scrapper) | — | 只有爬蟲程式碼（2017–2019 / 爬 Yahoo），沒有資料 | — | — | 不能用 |

GitHub 程式碼搜尋 `"7daysAgo" "numberOfAnalysts"` 有 1,488 個結果，幾乎都是單次的 earningsTrend 樣本或快取。**沒有找到從 2015 年持續累積到現在的 FY1/FY2 快照 repo**。

Kaggle（kaggle.com **403**，雲端抓不到，Mac 可以）：[tsaustin/us-historical-stock-prices-with-earnings-data](https://www.kaggle.com/datasets/tsaustin/us-historical-stock-prices-with-earnings-data)（季度預估 EPS 對實際值，＋日線股價）、[adarsh1077/epsclassification](https://www.kaggle.com/datasets/adarsh1077/epsclassification)（S&P 500 2020–2026，11,282 筆，有估計值趨勢方向欄位）。兩者都是單季、財報前最後一刻，**不是 FY 月度**【來源：搜尋摘要，未下載驗證】。

### 2.5 被擋的（CONNECT 403，2026-10-07 實測）

Yahoo：`query2.finance.yahoo.com`、`fc.yahoo.com`、`finance.yahoo.com`、`guce.yahoo.com`、`consent.yahoo.com`。
API／資料商：`data.nasdaq.com`、`www.nasdaq.com`、`api.tiingo.com`、`api.polygon.io`、`api.massive.com`、`finnhub.io`、`eodhd.com`、`www.alphavantage.co`、`api.twelvedata.com`、`api.intrinio.com`、`api-v2.intrinio.com`、`financialmodelingprep.com`、`api.estimize.com`、`www.estimize.com`、`extractalpha.com`、`api.morningstar.com`、`api.koyfin.com`、`api.tikr.com`、`app.tikr.com`、`api.fiscal.ai`、`sharadar.com`、`www.quandl.com`、`api.openbb.co`、`api.stockanalysis.com`、`api.simplywall.st`、`api.stlouisfed.org`。
網站：`www.zacks.com`、`ycharts.com`、`www.koyfin.com`、`www.factset.com`、`insight.factset.com`、`www.spglobal.com`（含 sp-500-eps-est.xlsx）、`www.yardeni.com`、`www.marketwatch.com`、`www.wsj.com`、`api.wsj.net`、`www.morningstar.com`、`www.tipranks.com`、`www.gurufocus.com`、`www.macrotrends.net`、`www.investing.com`、`www.barchart.com`、`www.tradingview.com`、`scanner.tradingview.com`、`www.cnbc.com`、`quote.cnbc.com`、`www.reuters.com`、`www.valueline.com`、`www.visiblealpha.com`、`www.multpl.com`、`pages.stern.nyu.edu`。
學術／資料集：`www.kaggle.com`、`huggingface.co`、`zenodo.org`、`dataverse.harvard.edu`、`wrds-www.wharton.upenn.edu`、`wrds-cloud.wharton.upenn.edu`、`www.openassetpricing.com`、`mba.tuck.dartmouth.edu`、`drive.google.com`、`docs.google.com`、`index.commoncrawl.org`、`data.commoncrawl.org`、`www.quantconnect.com`、`gist.githubusercontent.com`、`data.sec.gov`、`www.sec.gov`、`efts.sec.gov`。
其他：`stooq.com` 連線被重置；WebFetch 對 `support.tikr.com`、`www.koyfin.com` 回 EGRESS_BLOCKED。

**連得到但要金鑰**：`api.benzinga.com`（沒帶 key 回 **401** "Access denied for user anonymous"）。Benzinga 財報行事曆有 `eps_est`（季度、公布前最後一刻）；使用者若有 Benzinga／Massive 的 key，這裡就能直接用【推論】。
**連得到但跟共識無關**：`fred.stlouisfed.org/graph/fredgraph.csv` 200（LEARNINGS 2026-09-24 記的是被擋，今天是通的）、`storage.googleapis.com` 400、`pypi.org`／`files.pythonhosted.org` 200（不經 proxy）。

---

## 3. 使用者幫忙的方案

### 3(a) 在雲端環境開放網域（最少的一組）

設定位置：session 標題列的 cloud environment 選單 → Edit → Network access → 把網域加進 Allowed domains（保留 Allow package managers 打勾）。步驟見 https://code.claude.com/docs/en/cloud-environments#network-access 。

| 優先 | 網域 | 打開後能拿到什麼 |
|---|---|---|
| **必要（1 個）** | `fc.yahoo.com` | 拿 A3 cookie → `query1…/v1/test/getcrumb` 拿 crumb → `query1…/v10/finance/quoteSummary/<T>?modules=earningsTrend,earningsHistory&crumb=…` |
| 備援 | `query2.finance.yahoo.com` | query1 被 429 時改用（舊教訓：曾經 query1 429、query2 正常） |
| 備援 | `guce.yahoo.com`、`consent.yahoo.com` | yfinance 的 csrf／同意流程（在歐盟 IP 或 basic 流程失敗時才需要） |
| 選配 | `finance.yahoo.com` | yfinance `get_earnings_dates(limit=100)` 會爬 `finance.yahoo.com/calendar/earnings?symbol=…` 的 HTML，拿到每季的 EPS Estimate／Reported／Surprise，最多 100 季（約 25 年） |
| 選配 | `drive.google.com`、`drive.usercontent.google.com`、`docs.google.com` | 在雲端直接用 `openassetpricing` 套件下載 OSAP 的 FEPS（套件靠 gdown 走 Drive）【推論】 |
| 選配 | `www.alphavantage.co` | 要免費 key：`EARNINGS`（季度 estimatedEPS，可回溯到 1996）、`EARNINGS_ESTIMATES`（目前共識＋7/30/60/90 天前＋分析師數） |
| 選配 | `web.archive.org` | Wayback 存的 Yahoo/Zacks 估計值頁面舊快照（見 §3.3-c） |

依據【來源】：yfinance 原始碼 `yfinance/data.py`（basic 流程：先 GET `https://fc.yahoo.com` 再 GET `https://query1.finance.yahoo.com/v1/test/getcrumb`；csrf 流程：`guce.yahoo.com/consent` → `consent.yahoo.com/v2/collectConsent` → `query2…/v1/test/getcrumb`）。agents/LEARNINGS.md 2026-07-26 記錄：在 Actions runner 上「先 GET fc.yahoo.com 拿 cookie 再 getcrumb」可行（當時實測）。**推論**：這個環境只要開放 `fc.yahoo.com` 就夠，因為 query1 本來就通；但 Yahoo 會依 IP 決定要不要跑同意流程，要開了以後實測才算數。

**開放後 earningsTrend 的欄位**【來源：[robdevops/finbot 的 Yahoo v10 earningsTrend 樣本](https://raw.githubusercontent.com/robdevops/finbot/master/doc/yahoo/sample_yahoo_v10_earningsTrend.json)，raw 200 實測下載；yfinance `scrapers/analysis.py`】
- 期間：`0q`、`+1q`、`0y`、`+1y`（另有 `+5y`/`-5y` 的成長率），每期都有 `endDate`。
- `earningsEstimate`：`avg`、`low`、`high`、`yearAgoEps`、`numberOfAnalysts`、`growth`。
- `epsTrend`：`current`、`7daysAgo`、`30daysAgo`、`60daysAgo`、`90daysAgo` ← **可回填 90 天的迷你歷史**。
- `epsRevisions`：`upLast7days`、`upLast30days`、`downLast30days`（`downLast90days` 常是空的）。
- `revenueEstimate`（同結構）；另一個模組 `earningsHistory`：最近 4 季的 epsEstimate 與 epsActual。
- **歷史時點？** 只有「現在」加上 7/30/60/90 天前；更早的沒有。

### 3(b) 在 Mac 上用 yfinance（`pip install yfinance`，最新版 1.7.0，2026-08-26 發布【實測 pypi】）

| yfinance 方法 | 底層來源 | 欄位 | 歷史 |
|---|---|---|---|
| `Ticker.earnings_estimate` | quoteSummary earningsTrend | 0q/+1q/0y/+1y 的 avg/low/high/yearAgoEps/numberOfAnalysts/growth | 只有現在 |
| `Ticker.eps_trend` | 同上 | current/7/30/60/90 天前 | 90 天 |
| `Ticker.eps_revisions` | 同上 | 7/30 天內上修、下修的分析師數 | 30 天 |
| `Ticker.revenue_estimate`、`growth_estimates` | 同上 | 營收、成長 | 只有現在 |
| `Ticker.earnings_history` | quoteSummary earningsHistory | 最近 4 季的估計值、實際值、驚喜 | 4 季 |
| `Ticker.get_earnings_dates(limit=100)` | 爬 finance.yahoo.com/calendar/earnings 的 HTML | 每季的 EPS Estimate、Reported EPS、Surprise(%) | **最多 100 季**（第三方實測 AAPL 可回溯到 2002）；是**財報前最後一刻的單季共識** |
| `Ticker.info` | quote＋quoteSummary | `forwardEps`、`trailingEps`、`forwardPE` 等 | 只有現在 |

限制【來源＋推論】：(1) **沒有 FY1/FY2 的月度歷史**，yfinance 只有「現在」與 90 天回看；(2) Yahoo 會限流（yfinance 遇到 429 會丟出 `YFRateLimitError`），每檔間隔 1–2 秒，S&P 500 科技股約 70 檔，一次 2–3 分鐘；(3) 估計值的供應商與口徑 Yahoo 沒寫清楚【不確定】；(4) Yahoo 的使用條款限個人用途，存進**公開** repo 有疑慮（`docs/` 會公開部署，絕對不要放那裡）。

Mac 每週快照腳本的骨架（只示意，不寫進 repo）：

```python
import yfinance as yf, pandas as pd, datetime as dt, time
TICKERS = ["AAPL","MSFT","NVDA","AVGO","ORCL","CRM","ADBE","AMD"]   # 換成完整清單
rows, today = [], dt.date.today().isoformat()
for t in TICKERS:
    tk = yf.Ticker(t)
    est, trend = tk.earnings_estimate, tk.eps_trend          # index: 0q,+1q,0y,+1y
    for p in est.index:
        rows.append({"asof": today, "ticker": t, "period": p,
                     **{f"est_{k}": v for k, v in est.loc[p].items()},
                     **{f"trend_{k}": v for k, v in trend.loc[p].items()}})
    time.sleep(1.5)
pd.DataFrame(rows).to_csv(f"consensus_{today}.csv", index=False)
```

### 3(c) 有「歷史時點」共識的服務（使用者若有帳號）

| 服務 | 歷史時點？ | 能拿到什麼／怎麼匯出 | 存取 | 依據 |
|---|---|---|---|---|
| **WRDS → LSEG I/B/E/S Summary History**（`ibes.statsum_epsus`／`statsumu_epsus`） | **是，月度，美股從 1976 年起** | 每月 `statpers` 一筆：`fpi`（1=FY1、2=FY2、6=本季…）、`meanest`、`medest`、`numest`、`stdev`、`highest/lowest`、`fpedats`。WRDS 網頁查詢可匯出 CSV/SAS/Stata，也可以 Python `wrds` 套件寫 SQL | 學校帳號；網域被擋，要在 Mac 上跑 | [Princeton](https://libguides.princeton.edu/econ-finance/earningsforecasts)、[VU](https://libguides.vu.nl/finding-data/ibes)；OSAP 的程式碼就是這樣下 SQL 的【來源】 |
| **LSEG Workspace**（原 Refinitiv Eikon） | 是 | Excel 增益集或 Python `lseg-data`：`TR.EPSMean`、`TR.EPSNumIncEstimates`，可設 `Period=FY1/FY2/NTM`、`SDate/EDate`、`Frq=M` → xlsx/DataFrame。2024 年起 I/B/E/S 走 Workspace | 付費 | [LSEG 開發者社群](https://community.developers.lseg.com/discussion/67306/historical-estimates)【來源；參數細節不確定】 |
| **FactSet** | 是（每日共識歷史） | Excel `=FDS(...)` 或 Workstation 匯出 xlsx/csv；FY1/FY2/NTM 都有 | 機構授權 | 一般常識【推論】 |
| **Bloomberg Terminal** | 是 | Excel `BDH(T,"BEST_EPS",start,end,"BEST_FPERIOD_OVERRIDE=1BF","Per=M")`（1BF/2BF＝FY1/FY2，另有 NTM 參數）→ xlsx | 終端機 | [Rblpapi bdh](https://search.r-project.org/CRAN/refmans/Rblpapi/html/bdh.html)、[WU Bloomberg forecasts 手冊](https://library.wu.ac.at/bib/fit4research/wp-content/uploads/2024/02/Forecasts_manuals_Bloomberg.pdf)【來源；參數寫法以 FLDS 為準】 |
| **S&P Capital IQ（Pro）／Visible Alpha** | 是 | Excel 增益集；Visible Alpha 是逐科目的細項共識 | 高價機構授權 | 【推論】 |
| **Koyfin** | 有 NTM/FY 估計值的時間序列圖（資料來自 Capital IQ） | Historical Graph →「Show Table」；Plus（約 $39/月，10 年資料）／Pro（約 $79/月）有下載功能。能不能匯出估計值的時間序列、可回溯到哪年【不確定】 | 付費；網域被擋 | [Koyfin data overview](https://www.koyfin.com/help/data-overview/)、[charts](https://www.koyfin.com/help/charts-and-graphs/amp/)（搜尋摘要） |
| **TIKR** | 有 NTM 倍數的歷史（價值評估頁），代表背後有 NTM 共識歷史【推論】 | **只有 Pro 能匯出 Excel**，Plus 只能複製貼上 | 付費 | [TIKR 匯出說明](https://support.tikr.com/hc/en-us/articles/38745516537115-How-can-I-export-and-download-data-to-Excel)、[Estimates](https://support.tikr.com/hc/en-us/articles/39071375390235-How-do-I-use-TIKR-s-Estimates-feature)（搜尋摘要） |
| **YCharts** | 有：`eps_est_0y`（本財年）、`eps_est_2y` 等的時間序列（S&P 共識） | 有匯出，要付費；可回溯多久【不確定】（摘要說某些股票只到 2023） | 付費 | [YCharts eps_est_0y 範例](https://ycharts.com/companies/CHD/eps_est_0y) |
| **Zacks**（Nasdaq Data Link／Intrinio 代售） | 是：每日共識 mean/high/low/std/券商數，年度估計值從 1978 年起 | API／CSV | 付費；網域被擋 | [Intrinio Zacks EPS Estimates](https://intrinio.com/products/eps-estimates) |
| Finnhub `/stock/eps-estimate` | 【不確定】：方案說明寫「10 年歷史」，但可能指過去期間的最終值，不是歷史時點 | API | Estimate-1 $75/月 | [Finnhub 估計值方案](https://finnhub.io/pricing-stock-estimates) |
| FMP `analyst-estimates`、EODHD `Earnings::Trend`、Alpha Vantage `EARNINGS_ESTIMATES` | 多半**不是**（目前值，或過去期間的最終值；AV/EODHD 有 7/30/60/90 天前） | API | 免費 key 或付費 | 搜尋摘要【不確定】 |

---

## 4. 若只能用免費資料：替代方案

### 4.1 OSAP 的 FEPS（免費、月度、FY1）── 先做這個就能估係數

- 取得方式（在 Mac 上）：`pip install openassetpricing` →
  `import openassetpricing as oap; d = oap.OpenAP(); df = d.dl_signal('pandas', ['FEPS','sfe','AnalystRevision'])`。套件 0.0.2 的 `urls.py` 列出 release `202510`（「Version 2.00: data release - 2025.10」）與 `202410`【實測：從 PyPI 下載 wheel 檢查】。
- 欄位：`permno, yyyymm, FEPS`（＝I/B/E/S 未調整的 FY1 meanest，`time_avail_m` ＝ statpers 所在月份）。`sfe` ＝ FY1 median ÷ 價格（排除距財年結束 90 天內）；`AnalystRevision` ＝ FEPS_t ÷ FEPS_{t−1}。
- **要自己處理的事**【推論】：
  1. permno 對到 ticker：**更正（2026-10-08，看過套件原始碼 `openap_download.py`）：OSAP 的 `Price`、`Size`、`STreversal` 三個訊號要用 WRDS 帳號從 CRSP 現抓（`wrds.Connection()`），沒有帳號拿不到**；其他訊號（含 `FEPS`、`Mom12m`、`Mom6m`）是公開 CSV、不用 WRDS。
     做法：下載 `Mom12m`／`Mom6m`（CRSP 報酬算的動能），和我們自己的股價算出的同一個動能逐月比對，相關最高且吻合的那個 permno 就是這家公司；
     或找公開的 permno–ticker 對照表交叉檢查。
  2. 分割：FEPS 沒做分割調整（`statsumu`），跟同月的未調整價格比沒問題，但**月對月的修正碰到分割月會跳**。分割日期可以從 Yahoo v8 chart 的 `events=split` 拿到（這裡抓得到）。
  3. 財年換年：`AnalystRevision` 在 FY1 從今年換到明年那個月會失真，要剔除（財年結束月份可以從 SEC 財報鏡像拿到，見 data/SOURCES.md）。
  4. 只有 FY1：財年後段 FY1 跟 NTM 差很多。要嘛只用前半年的觀測值，要嘛用 `fgr5yrLag`（長期成長率）粗估 FY2【推論，品質差】。
  5. 資料迄日【不確定】（推論到 2024-12 左右），2025 以後要靠自己的快照接上。
- 授權：OSAP 公開散布 I/B/E/S 的衍生訊號，學術用途是常態，商業用途【不確定】。

### 4.2 從今天起每週存快照（累積自己的歷史時點資料）

- **去哪裡跑**：
  (i) **這個雲端環境**：選股器今天實測 200，可以用排程 Routine 每週開一個新 session 跑 `snap_yahoo_screener.py`，再把 CSV commit 進 `projects/pe-forecast/data/consensus_snapshots/`（**不要放 `docs/`**）。要使用者決定，因為會寫入 repo。
  (ii) **Mac** 用 launchd/cron 跑 yfinance 版本，欄位比較完整（分析師數、高低值、7/30/60/90 天前）。
  (iii) **GitHub Actions：不建議**。LEARNINGS 2026-08-02 記錄 runner 打 Yahoo 全部 429；而且改 workflows 要先問使用者。
- 第一次跑 yfinance 版本時，用 `epsTrend` 的 7/30/60/90 天前值，馬上回填 4 個點。
- 每列存：`asof, ticker, period(0y/+1y/0q/+1q), endDate, avg, low, high, numberOfAnalysts, 7/30/60/90daysAgo, price, currency`，之後算 NTM 時間加權。
- 多久才夠用【推論】：約 70 檔 × 每月 1 筆 ≈ 每年 840 筆觀測；以 12 個月報酬回歸來說，重疊期間會降低有效樣本，**至少 2–3 年才能自己估出穩定係數**。在那之前用 OSAP 的歷史係數。

### 4.3 學術上常用的代理

- **Value Line**：一家公司一位分析師，約 1,700 檔，文獻常拿來替代 I/B/E/S；歷史檔（Value Line DataFile）要付費，部分大學圖書館有。valueline.com 被擋。
- **時間序列模型**：季節性隨機漫步（加漂移）、Foster (1977)、Brown–Rozeff (1979) ARIMA。可以用這個 repo 已有的 SEC 財報鏡像自己算；把它當成「機械式共識」，或當成分析師共識的工具變數。
- **橫斷面模型**：Hou–van Dijk–Zhang (2012, JAE) 的盈餘預測模型（文獻指出它在涵蓋率、偏誤、盈餘反應係數上不輸分析師）、Li–Mohanram (2014) 的 EP/RI 模型、So (2013)。這些都只要財報資料就能算，但**衡量的是「模型預期」，不是「市場共識」**，係數的意義不同【推論】。
- **指數或產業層級的共識歷史**（拿來估產業平均的反應係數）：Yardeni 的 S&P 500 各產業 forward earnings（I/B/E/S，每週）、FactSet Earnings Insight 週報、S&P DJI 的 `sp-500-eps-est.xlsx`。三者在雲端都被擋（403），在 Mac 上可以抓。
- **Wayback Machine 舊快照**【不確定】：Yahoo 的 `/quote/<T>/analysis` 與 Zacks 估計值頁，大型股可能有密集的歷史快照，可以用 CDX API 列出後解析（頁面改版過好幾次，解析成本高）。先在 Mac 上用一行驗證快照密度：
  `curl 'https://web.archive.org/cdx/search/cdx?url=finance.yahoo.com/quote/AAPL/analysis*&from=2015&to=2024&output=json&fl=timestamp,statuscode&collapse=timestamp:6' | head`
  每月都有快照，才值得做。

---

## 5. 建議落地順序（給 pe-forecast）

1. **馬上做（不用使用者幫忙）**：工具加一個 `--consensus auto|<數字>` 參數。`auto` 就抓 Yahoo 選股器的 0y/+1y，用財年結束月份算 NTM 加權；手動填數字就覆寫（保留使用者調整的空間）。同時顯示 0y、+1y、NTM 和抓取日期，並對 ADR 或幣別不一致的情況發出警告。
2. **使用者在 Mac 上花 10 分鐘**：`pip install openassetpricing yfinance`，下載 FEPS/sfe/AnalystRevision，加上 S&P 500 科技股的 `get_earnings_dates(limit=100)`，把 CSV 放進 `projects/pe-forecast/data/`（不是 `docs/`）。之後由雲端 session 估「FY1 修正 → 未來 12 個月報酬」的反應係數，並用季度驚喜資料交叉驗證。
3. **如果使用者有 WRDS／LSEG／FactSet／Bloomberg 任何一個**：改匯出 2015 年以後每月的 FY1＋FY2（或 NTM）mean、numest、fpedats，取代 OSAP。
4. **開放 `fc.yahoo.com`**（之後視情況加 `query2.finance.yahoo.com`），讓雲端也能抓 earningsTrend（分析師數、7/30/60/90 天修正）。並決定要不要用每週 Routine 存快照。

---

## 附錄 A：實測紀錄（2026-10-07，經 agent proxy，UA＝`Mozilla/5.0`）

| URL | HTTP |
|---|---|
| query1 `/v8/finance/chart/AAPL` | 200 |
| query1 `/v1/finance/screener/predefined/saved?scrIds=ms_technology&count=250`（`&start=250`） | 200（402 檔；第 2 頁 152 檔） |
| query1 `/ws/screeners/v1/finance/screener/predefined/saved?scrIds=most_actives` | 200 |
| query1 `/ws/fundamentals-timeseries/...type=quarterlyForwardPeRatio`／`annualForwardPeRatio`／`trailingForwardPeRatio` | 200 |
| query1 `/ws/fundamentals-timeseries/...type=annualEpsEstimate,...`（自己猜的估計值 type） | 404 |
| query1 `/v10/finance/quoteSummary/AAPL?modules=earningsTrend` | 401 |
| query1 `/v7/finance/quote`、`/v7/finance/options`、POST `/v1/finance/screener` | 401 |
| query1 `/v1/test/getcrumb` | 429（第一次）、401（之後） |
| query2／fc／finance／guce／consent `.yahoo.com` | CONNECT 403 |
| raw.githubusercontent.com（yfinance 原始碼、finbot 樣本、Estimize CSV Range 請求） | 200／206 |
| `git ls-remote`／`git clone --filter=blob:none` github.com 公開 repo | 成功 |
| api.github.com、github.com 網頁、codeload.github.com（用 curl） | 403 |
| pypi.org JSON、files.pythonhosted.org wheel | 200 |
| fred.stlouisfed.org/graph/fredgraph.csv | 200 |
| api.benzinga.com（沒帶 key） | 401 |
| §2.5 列出的其他網域 | CONNECT 403 |

## 附錄 B：本次參考的程式碼與文件（查詢日 2026-10-07）

- yfinance 原始碼（cookie/crumb 流程、analysis、earnings dates）：https://raw.githubusercontent.com/ranaroussi/yfinance/main/yfinance/data.py 、…/scrapers/analysis.py 、…/base.py
- Yahoo earningsTrend 樣本：https://raw.githubusercontent.com/robdevops/finbot/master/doc/yahoo/sample_yahoo_v10_earningsTrend.json
- OSAP 程式碼：https://github.com/OpenSourceAP/CrossSection （`Signals/pyCode/Predictors/FEPS.py`、`AnalystRevision.py`、`sfe.py`、`DataDownloads/IBESEPSUnadjusted.py`）；Python 套件：https://pypi.org/project/openassetpricing/ ；資料頁：https://www.openassetpricing.com/
- Estimize 資料集：https://github.com/Iliyan0508/Estimize_EPS_Prediction
- 第三方資料源探測：https://github.com/Lina-zar/Earnings-predictor （`reports/probe_summary_2026-09-26.csv`）
- Hou, van Dijk & Zhang (2012) "The implied cost of capital: A new approach", JAE；Li & Mohanram (2014) RAST。

# 資料來源（pe-forecast）

> **這一版用的是 GitHub 上別人放的公開鏡像，不是直接從 SEC 抓的。** 雲端 session 連不到
> data.sec.gov、FRED、Stooq、Yahoo（2026-09-24 實測，除了 GitHub 幾乎全擋）。
> 鏡像檔是 SEC companyfacts API 的**原始 JSON 格式**（含 `accn`、`filed`、`form`），
> 已做 CIK→公司名稱逐檔核對與兩個獨立鏡像交叉比對，但**最終還是要用 SEC 官方資料重跑一次**
> ——見 `topics/technology/mac-manual-homework.md` 的對應待辦。

## 原始檔（不進版控，約 330MB）

| 用途 | 來源 | 快照 | 範圍 |
|---|---|---|---|
| 逐季財報（68 家） | `github.com/hanumantjain/sp500_agentic_ai` `data/company_facts/CIK##########.json` | commit `4c70fc8`（2025-09-16） | 申報到 2025-06～09 |
| 逐季財報（14 家延伸到 2026） | `github.com/kotoba-lang/gov.sec.edgar` `raw/companyfacts/` | commit `948ab39`；README 載明抓取日 **2026-07-15** | 申報到 2026-04～06 |
| 日股價（68 家） | 同上 hanumantjain `data/sp500_stooq_ohcl/<t>.us.txt`（Stooq） | 同上 | 到 **2025-09-09** |
| 日股價（11 家，只做分割還原） | `github.com/blakeweaver17-del/ai-infra-data` `data/prices/<T>.csv` 的 `close` | commit `5a4a782` | 2015-01-02 → **2026-09-23** |
| 10 年期殖利率、CPI | `datasets/bond-yields-us-10y`、`datasets/cpi-us`（FRED／BLS 鏡像；沿用上一版 pe-model 已核對的檔） | — | 到 2026-07 |

14 家延伸公司：MSFT GOOGL META AMZN AAPL NVDA AMD INTC MU AVGO AMAT LRCX ORCL CSCO。
其中 AAPL、INTC、CSCO 在 ai-infra-data 沒有股價檔 → 股價只到 2025-09。

重建：`python3 build_data.py --facts <kotoba 目錄> <hanumantjain company_facts 目錄> --stooq <stooq 目錄> --splitonly <ai-infra-data prices 目錄>`

## 進版控的衍生檔

| 檔 | 內容 |
|---|---|
| `universe.csv` | 68 家：ticker、CIK、產業分類、排除期間與原因 |
| `quarters.csv` | 逐季：營收、毛利、淨利、稀釋股數、股利、存貨、權益、現金、負債；**全部是第一次申報值**與申報日 |
| `prices_monthly.csv` | 月底市值（只做分割還原的股價 × 同口徑稀釋股數） |
| `build_log.csv` | 每家公司：財報來源、季數、偵測到的分割、股價來源 |
| `us10y_monthly.csv`、`cpi_us_monthly.csv` | 總體 |

## 快照（`snapshot_run.py`）額外用的來源——只用於「現在」，不用於回測

這些來源的數字是**最後申報值**（事後重述過），filed 欄也不是第一次申報日，所以不能拿來做時點正確的回測；
快照只需要「今天的一列」，可以用。

| 來源 | 內容 | 用在哪些公司 |
|---|---|---|
| `github.com/yennanliu/finance_data` `data/fundamentals/<t>.csv`、`data/prices/<t>.csv` | 逐季財報（含營業利益、Q4 已拆出）到 2026-06；只分割還原的日股價（含分割欄） | SNDK、WDC、VST、PLTR、AVAV、KTOS、MRVL |
| `github.com/huangtop/AXIOM-RESEARCH-ENGINE` `canonical_financial_population/quarterly/` | 每家最近 3 季＋去年同期（營收、淨利、稀釋股數；**沒有 Q4、沒有營業利益**） | 接在 SEC 鏡像後面補最新季 |
| `github.com/loosygoosie/sec-dataset` `data/companies/<CIK>.json` | companyfacts 整理版，最近 12 季（含毛利、營業利益、存貨、權益） | COHR、LITE、CIEN、FN、AAOI、CRDO |
| `github.com/kotoba-lang/gov.sec.edgar` | 同上 2026-07-15 的 companyfacts 原檔 | TSLA（快照） |
| `github.com/Stell0/financealerts2` `data/<T>.csv`、`github.com/natezone/market-tracker` | yfinance 日股價到 2026-09-23 | 沒有只分割還原序列的公司（只用最新價與 6 個月報酬） |

財報落後的公司（最新季距今 >150 天）：錨點移回那一季仍是最新的月份，用那個月的股價——避免拿一年前的盈餘配今天的股價。
財報截止後才分割的（NFLX 2025-11 10:1）：用 Stooq（2025-09 口徑）與新股價來源在 2025-05～08 的比值自動偵測、補乘。

## S&P 500 回測（`build_broad.py`）與任何代號的現在預測（`now_run.py`）

| 來源 | 內容 | 用途 |
|---|---|---|
| `github.com/hanumantjain/sp500_agentic_ai` `data/company_facts/`、`data/sp500_stooq_ohcl/` | S&P 500 全部 500 家的 companyfacts 與 Stooq 日股價（到 2025-09） | 回測（§13） |
| 同上 `data/sp500_corporate_actions_yfinance.csv` | 每一次除息（日期、金額）與分割；分拆被記成非整數比例的分割 | 股利還原、辨識分拆 |
| 同上 `data/S_and_P_500_component_stocks.csv` | 名單、CIK、GICS 產業 | 名單 |
| `github.com/loosygoosie/sec-dataset` `data/companies/<CIK>.json`、`data/tickers.json` | 約 7,400 家最近 12 季（重述後的最後申報值）、SEC 代號對照表；每天更新 | 只用於「現在」 |
| `github.com/ozkanpakdil/top-us-stock-tickers` `tickers/all.csv` | 約 5,300 檔美股每日收盤與市值；git 歷史＝每日時間序列（2025-12-28 起） | 只用於「現在」 |

## 中小型股與 Nasdaq-100 回測（`build_small.py`、`lab_small.py`、`lab_window.py`、`lab_ndx.py`）

| 來源 | 內容 | 用途 |
|---|---|---|
| `github.com/kovagent/indexkit` 的成分股 parquet（`rut`、`sp400`、`sp600`） | IWM、IJH、IJR 每季向 SEC 申報的持股明細（N-PORT，2019-12 → 2026-06：公司名稱、CUSIP、持有股數、市值），加上 2026-09 的 iShares 每日持股檔（有代號） | 中小型股的季末股價（市值 ÷ 股數）與當時的成分股 |
| 同上 `ndx-2026-09.parquet`、`sp400/sp600/rut-2026-09.parquet` | 2026-09 的成分股代號 | 最近一段依指數分組、網頁標出每家公司屬於哪個指數 |
| `github.com/loosygoosie/sec-dataset` `data/v2/companies/<CIK>.json` 的 `v2_quarterly` | 2008 起逐季營收、淨利、稀釋股數、現金、權益、負債（**重述後的最後申報值**，沒有毛利、營業利益、存貨） | 中小型股的財報；可用日＝季末 +45 天、年報 +75 天 |
| `github.com/jmccarrell/n100tickers` `src/nasdaq_100_ticker_history/n100-ticker-changes-<年>.yaml` | 每年 1 月 1 日的 Nasdaq-100 成分股與年中異動 | 把 S&P 500 回測依「當年是否 Nasdaq-100」重新分組 |

持股明細只有公司名稱與 CUSIP：用正規化名稱對到 SEC 公司代碼（79% 的列對得到），再用 CUSIP 串起不同季。
對不到的多半是已下市或被併購的公司 → 中小型股回測只有「活到 2026 年」的公司。YAML 要用 BaseLoader 讀：代號 `ON`（安森美）會被一般讀法變成布林值 True。

## 已處理的資料陷阱（每一個都實測過）

1. **Stooq 的價格同時做了股利還原**：MSFT 2004-11-15 的 $3 特別股利當天沒有跳空。直接用會把過去市值
   低估累積股利殖利率那麼多（2015 年 AVGO 低 22%、MSFT 低 13%）。→ 用財報的每股股利反推還原。
   **核對**：還原後與 ai-infra-data 的「只分割還原」收盤價比，11 家 × 128 個月的中位比值 1.000–1.031。
   有分割專用序列的 11 家，2015 年起直接用它。
2. **Stooq 對分拆的處理不一致**：HPQ（2015 分拆 HPE）、EBAY（2015 PayPal）、DELL（2021 VMware）、
   WDC（2025 SanDisk）的價格在分拆日沒有斷點（被當成股利還原）；HPE 2017 的兩次分拆則有斷點。
   → `universe.csv` 把前四家的分拆前（WDC 是分拆後）期間排除。GEN（多次特別股利＋併購）整家剔除。
3. **分割**：用稀釋股數第一次申報值的跳動偵測。乾淨倍數（±4%）直接認定；±25% 以內則要有「EPS 重述」證據——
   分割後的財報會把分割前各季的 EPS 重述成 ÷ 分割比例，併購不會（LHX 2019 股數 ×1.87 是併購）。
   虧損季的「稀釋」股數＝基本股數，轉盈後會多出選擇權稀釋，例 PANW 3:1 分割呈現為 3.44 倍——**第一版用 ±4% 漏掉了
   PANW 2022 與 CRM 2013 的分割（2026-09-24 修正，回測 12 個月誤差不變）**。偵測到的分割見 `build_log.csv`，
   與已知分割（AAPL 7:1/4:1、NVDA 4:1/10:1、AMZN/GOOGL 20:1、AVGO/LRCX 10:1…）逐一吻合。
   偵測日期是「第一份用分割後口徑申報的季末」，不是分割生效日：SMCI 10:1（2024-10 生效）落在 2024-06-30，
   因為那季的 10-K 延遲到分割後才申報——股數與股價口徑仍一致。GOOGL 2014-04 的 Class C 分派不在偵測範圍，
   但 Alphabet（CIK 1652044）的財報從 2014-09 才開始，已在分派之後，不受影響。
   MSI 2009 年那筆「8 倍」是 Motorola 分拆前的雜訊，2011-02 以前的 MSI 資料整段排除，不影響。
4. **虧損季的 XBRL 標籤**：虧損季常只標 `EarningsPerShareBasicAndDiluted`／
   `WeightedAverageNumberOfShareOutstandingBasicAndDiluted`，只抓 Diluted 會漏掉原始申報、
   只剩事後重述值（PANW 2021 就是這樣）→ 三種標籤聯集取最早申報。
5. **Alphabet 只按股別揭露稀釋股數** → 股數用 淨利 ÷ 稀釋 EPS 反推。
6. **早期 XBRL 缺季**：四季加總必須橫跨 250–300 天才算數；否則作廢。
7. **STX 2024Q4 每股股利標成 2,799,997**（單位標錯）→ 每股股利 > 股價的值略過。
8. **稀釋股數的單位錯誤（2026-09-25 發現）**：有些季以千股或百萬股申報（GRMN 2014-03-29 寫 195,860，實際 1.96 億股；
   KO 2018 寫 4,306；COP 2012–2014 整段以千股申報），少數反過來大 10^3～10^6 倍（AIG 2008）。市值跟著錯 1000 倍，
   本益比被算成 0.01 或 3 萬倍。修正（`pef/data.py` 的 `fix_share_scale`）：市銷率 0.02～200 倍的季當可信季，
   跟前後 3 年可信季的中位數差 10^3 或 10^6 倍的季乘回來；沒有可信季（多半是銀行）時用前後 3 年的多數。
   修不回來的（合併前空殼公司的 100 股之類）：市銷率 < 0.02 或 > 5000 倍的月份不用。
   S&P 500：63 家、261 季修正；中小型股：187 家、893 季。**68 家科技股的 `quarters.csv` 沒有重建**
   （8 家、31 季，除 JBL 2017、TER 2023 外都在 2014 年以前），§3–§12 的數字是修正前的；正式模型用的是已修正的 S&P 500 資料。

## 抽查（子代理與我各自核對）

- MSFT 2023Q4（季末 2023-12-31）：稀釋 EPS 2.93、營收 $62.02B、淨利 $21.87B，10-Q 申報 2024-01-30。
  hanumantjain 與 yennanliu 兩個鏡像一致。
- MU FQ1'24（季末 2023-11-30）：稀釋 EPS −1.12、營收 $4.726B、淨利 −$1.234B，申報 2023-12-21。兩鏡像一致。
- MU FQ2'26（季末 2026-02-26）：稀釋 EPS 12.07、營收 $23.86B，申報 2026-03-19。kotoba 與 AXIOM 一致。
- 還原後 MSFT 2015-12-31 收盤 $55.74（ai-infra-data 只分割還原序列在重疊期的中位比值 1.005）。

## 已知缺口

- **SNDK、MRVL 不在任何找得到的鏡像裡**（SNDK 2025-02 才上市；MRVL 不是 S&P 500 成分股）。
- **倖存者偏誤**：名單是 2025 年的 S&P 500 成分股——全部是活下來、而且變大的公司。
- 54 家公司的財報只到 2025 年中、股價只到 2025-09；只有 14 家延伸到 2026。

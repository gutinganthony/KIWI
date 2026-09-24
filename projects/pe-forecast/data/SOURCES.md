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

## 已處理的資料陷阱（每一個都實測過）

1. **Stooq 的價格同時做了股利還原**：MSFT 2004-11-15 的 $3 特別股利當天沒有跳空。直接用會把過去市值
   低估累積股利殖利率那麼多（2015 年 AVGO 低 22%、MSFT 低 13%）。→ 用財報的每股股利反推還原。
   **核對**：還原後與 ai-infra-data 的「只分割還原」收盤價比，11 家 × 128 個月的中位比值 1.000–1.031。
   有分割專用序列的 11 家，2015 年起直接用它。
2. **Stooq 對分拆的處理不一致**：HPQ（2015 分拆 HPE）、EBAY（2015 PayPal）、DELL（2021 VMware）、
   WDC（2025 SanDisk）的價格在分拆日沒有斷點（被當成股利還原）；HPE 2017 的兩次分拆則有斷點。
   → `universe.csv` 把前四家的分拆前（WDC 是分拆後）期間排除。GEN（多次特別股利＋併購）整家剔除。
3. **分割**：用稀釋股數第一次申報值的跳動偵測（容忍 15%，因為虧損季的「稀釋」股數＝基本股數，
   轉盈後會多出選擇權稀釋，例 PANW 3:1 分割呈現為 3.44 倍）。偵測到的分割見 `build_log.csv`，
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

# 資料來源與取得方式

## monthly.csv

| 欄位 | FRED 代號 | 內容 | 範圍 |
|---|---|---|---|
| `core_cpi` | `CPILFESL` | 核心 CPI（不含食物與能源），指數 | 1957-01 ～ 2026-08 |
| `core_pce` | `PCEPILFE` | 核心 PCE 物價指數 | 1959-01 ～ 2026-07 |
| `unrate` | `UNRATE` | 失業率 % | 1948-01 ～ 2026-08 |
| `wti` | `MCOILWTICO` | WTI 原油月均價 USD/bbl | 1986-01 ～ 2026-08 |
| `brent` | `MCOILBRENTEU` | Brent 原油月均價 USD/bbl | 1987-05 ～ 2026-08 |
| `sp500_eps` | （非 FRED） | S&P 500 十二個月移動每股盈餘，**名目** | 1871-01 ～ 2023-09 |
| `cpi_shelter` | `CUSR0000SAH1` | CPI 住房分項（shelter），指數 | 1953-01 ～ 2026-07 |

⚠️ **`sp500_eps` 是「獲利軸」的唯一資料來源**（78.4%／19.5%／R²=0.165／780 組全部來自它），
來源是本 repo 既有的 `projects/avi-v5/data/ext/shiller_sp500.csv` 的 `Earnings` 欄，
即 Robert Shiller 公開的 S&P 500 長期資料集。逐月核對與該檔一致（例：1948-01 為 1.6433）。
**三個已知限制**：(a) 它是**十二個月移動**的，所以比市場落後——這正是「市場比財報早動」那個結論的來源；
(b) 季資料內插成月資料；(c) **不含股息**，所以本專案所有股票報酬都是價格報酬。

**取得方式**：本環境的 egress proxy 擋掉 `fred.stlouisfed.org` 與 `api.stlouisfed.org`（curl 回 HTTP 000／403），
但 `raw.githubusercontent.com` 可通。序列取自 FRED 官方 CSV 的 GitHub 鏡像：

- `CPILFESL` / `PCEPILFE` / `UNRATE`：`theodorewright11/macro_eco_dashboard` → `public/data/fred/<代號>.csv`
- `MCOILWTICO` / `MCOILBRENTEU` / `CUSR0000SAH1`：`Gariyuuu/forecast-graveyard` → `data/raw/<代號>.csv`

⚠️ **核心商品（`CUSR0000SACL1E`）與核心服務（`CUSR0000SASLE`）兩個鏡像都沒有**，已逐一試過
（連同 apparel、新車、二手車、PCE 財貨/服務分項），全部 404。
⇒ 核心 CPI 目前只能拆成「住房」與「其餘」，**無法把核心商品單獨拆出來**。這是已知資料缺口。

這條路徑與 `topics/business/2026-09-15-core-pce-cpi-inversion-798-months.md` §7 記錄的是同一條，
該輪已做過鏡像可信度交叉驗證（核心 CPI 兩個獨立 repo 共同 834 個月 **0 筆不符**）。

**本輪的獨立驗證**（自算 vs 官方公布值）：

| 項目 | 自算 | 官方／外部 | 判定 |
|---|---|---|---|
| 核心 CPI 年增（2026-08） | 2.45% | 2.4%（2026-09-11 公布） | ✅ |
| 核心 PCE 年增（2026-07） | 3.34% | 3.3%（2026-08-26 公布） | ✅ |
| 失業率（2026-08） | 4.1% | 4.1% | ✅ |
| 核心 PCE − 核心 CPI 缺口 | +0.90pp | 前輪自算 2026-07 為 +0.88pp | ✅ 一致 |

⚠️ **月均價 vs 現貨**：`brent` 是**月均價**（2026-08 為 $91.08）。模型裡的 `BRENT_NOW = 107.35`
是 **2026-09-15 現貨**，來自外部查證，不在本檔內。兩者不可混用。

⚠️ **2025-10 核心 CPI 缺漏**：政府關門期間 BLS 未發布，該月為空值，計算時自動跳過。

---

## 外部機率錨（寫在 scenario_model.py §1，非本檔資料）

| 項目 | 數值 | 日期 | 來源 |
|---|---|---|---|
| 紐約聯準銀行殖利率曲線 12 個月衰退機率 | 13.9% | 資料至 2026-08，發布 2026-09-06 | newyorkfed.org/research/capital_markets/ycfaq |
| 費城聯準 SPF anxious index（2026Q4 負成長） | 20.0% | Q3 2026 調查，發布 2026-08-14 | philadelphiafed.org SPF Q3 2026 |
| SPF 失業率預測 | 4.2–4.3% | 同上 | 同上 |
| SPF 核心 CPI 預測 | 2.7% | 同上 | 同上 |
| Goldman Sachs 12 個月衰退機率 | 15% | 2026 年年中 | thestreet.com 轉述 |
| 摩根大通 / WSJ 經濟學家調查 | 20% / 25% | 2026-07 | ⚠️ 無直接 URL |
| Brent 現貨 | $107.35 | 2026-09-15 | home.saxo Options Brief 09-14 |
| 1 年期通膨交換 | 2.70% | 2026-09 | — |
| 9 月 FOMC 升息機率 | 84.1% | CME FedWatch 2026-09-14 | — |

⚠️ **這些數字全部只取得搜尋摘要層，未能開原頁逐字核對**（WebFetch 對所有網域回 EGRESS_BLOCKED）。
完整紀錄與被擋站點清單見本輪研究檔（session scratchpad `research-external-anchors.md`，未入庫）。

⚠️ **查不到**：CPI cap/floor 隱含的通膨機率、Brent 選擇權隱含的破 $115 機率、
OVX 隱含波動率。**所以模型裡的油價三態機率是判斷，不是市場定價。**

⚠️ **沒有任何機構公開發布「軟著陸／停滯性通膨／衰退」的三分情境機率**（6 次搜尋後確認）。
⇒ 本模型的五情境機率**沒有直接的外部對照物**，只能逐格對照（就業那一格有，通膨那一格沒有）。

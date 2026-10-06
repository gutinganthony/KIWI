# 客戶資產管理台（client-desk）

代操客戶的持股管理、月結與月報 PDF 產生器。以 claude.ai Artifact 形式運作。

- 線上版：https://claude.ai/artifact/FqAADwg6nBkVwA9o3WnWW1（私人；只有擁有者能開）
- 原始碼：`client-desk.html`（**不含任何客戶資料**——資料存在 Artifact 的私人資料庫，
  存取規則 `read/write: owner`，連被分享的編輯者都讀不到）
- ⚠️ 不要把本工具或任何客戶資料放進 `docs/`（會被部署到公開 GitHub Pages）。

## 資料模型（Artifact db）

| 路徑 | 內容 |
|---|---|
| `settings/main` | 品牌名稱、經理人、即時 USD/TWD、無風險利率、漲跌色慣例 |
| `settings/bench` | `rows[YYYY-MM] = {taiex, spx, fx}` 月底收盤，所有客戶共用 |
| `clients/{id}` | 客戶基本資料、費率、基準權重、`holdings[]`、現金 |
| `clients/{id}/months/{YYYY-MM}` | 月底資產 `value`、淨入出金 `flow`、匯率、持股快照、經理人評論 |
| `clients/{id}.flows[]` | 資金進出紀錄 `{date, ccy, amt, fx, twd, note}`；月結「淨入金」自動加總 |
| `clients/{id}/pos/{YYYY-MM-DD}` | 自該日起生效的完整部位（股數＋現金）；異動以 delta 套用到生效日之後所有紀錄 |
| `quotes/latest` | 最新報價 `px[fkey]`、`fx`、無報價清單 `na` |
| `quotes/h-YYYYMM` | 每日收盤 `p[fkey][DD]`、`fx[DD]`、`spx[DD]` |

## 自動報價（Google Finance）

頁面透過使用者的 Google Drive 連接器（mcp capability）在 Drive 建一份試算表，
每檔一列 `GOOGLEFINANCE` 公式（現價、成交時間、4 段 15 天的收盤歷史 JOIN 成字串——
連接器讀回時單格約 800 字會被截斷，所以拆段），再用 `read_file_content` 讀回解析。
- 新代號出現 → 重建試算表（create_file）並 trash 舊檔；`META:NOW` 未變且距上次讀取 >20 分鐘 → 視為未重算，重建。
- 已知限制：**上櫃（TPEx）股票、加權指數 GOOGLEFINANCE 都沒有資料**（2026-10-06 實測），前者手動現價、後者月底手動填。
- S&P 500 與 USD/TWD 月底值由收盤歷史自動補進 `settings/bench`（不覆蓋手填值）。

## 計算口徑

- 月報酬：修正 Dietz `(V1 − V0 − F) / (V0 + 0.5F)`；首月 `(V1 − F) / F`（初始資金視為月初投入）。
- 單位淨值：起始 10，逐月連乘（時間加權，排除出入金影響）。
- 比較基準：`w × 加權指數報酬 + (1−w) × S&P 500 台幣報酬`（價格指數，不含股利）。
- 年化：滿 12 個月才計；波動度 = 月報酬標準差 × √12；夏普未滿 12 個月以月均 ×12。
- 績效分潤高水位：上一年底以前最高單位淨值。
- 每日淨值：Σ 股數 × 當日收盤（週末/休市沿用前一收盤，最多 12 天）× 匯率 ＋ 現金；當天用即時報價。
- 管理費：Σ 每日淨值 × 年費率 ÷ 365（日曆日計提）。

## Claude 可代勞的維護

在 Claude Code 對話中說「更新客戶管理台的股價」或「補上 10 月基準指數」，
Claude 可用 ArtifactData 直接寫入 `clients/*.holdings[].px` 與 `settings/bench`。

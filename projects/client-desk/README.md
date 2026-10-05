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

## 計算口徑

- 月報酬：修正 Dietz `(V1 − V0 − F) / (V0 + 0.5F)`；首月 `(V1 − F) / F`（初始資金視為月初投入）。
- 單位淨值：起始 10，逐月連乘（時間加權，排除出入金影響）。
- 比較基準：`w × 加權指數報酬 + (1−w) × S&P 500 台幣報酬`（價格指數，不含股利）。
- 年化：滿 12 個月才計；波動度 = 月報酬標準差 × √12；夏普未滿 12 個月以月均 ×12。
- 績效分潤高水位：上一年底以前最高單位淨值。

## Claude 可代勞的維護

在 Claude Code 對話中說「更新客戶管理台的股價」或「補上 10 月基準指數」，
Claude 可用 ArtifactData 直接寫入 `clients/*.holdings[].px` 與 `settings/bench`。

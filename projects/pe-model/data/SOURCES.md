# 資料來源（pe-model）

三個檔案，全部是官方序列的 GitHub 鏡像（FRED／BLS／S&P 本輪皆被 egress proxy 擋，`raw.githubusercontent.com` 可通）。

| 檔案 | 內容 | 範圍 | 來源 |
|---|---|---|---|
| `shiller_sp500.csv` | S&P 500 月均價、**12 個月移動 as-reported EPS**（季資料線性內插）、股息、CPI、10 年期殖利率、實質序列、PE10 | 價格 1871-01～**2026-08**；**EPS 到 2023-06**；CPI／10y 到 2023-09 | `datasets/s-and-p-500`（Robert Shiller 公開資料的 datahub 鏡像；與 repo 既有 `projects/avi-v5/data/ext/shiller_sp500.csv` 逐月一致，多一個月價格） |
| `us10y_monthly.csv` | 10 年期美債殖利率，月均 | 1953-04～**2026-07** | `datasets/bond-yields-us-10y`（FRED `GS10` 鏡像） |
| `cpi_us_monthly.csv` | CPI-U 全項目指數（headline），未季調 | 1913-01～**2026-07** | `datasets/cpi-us`（BLS `CUUR0000SA0` 鏡像） |

## 接縫檢查（2023-06，兩邊都有值的月份）

| 序列 | 席勒檔 | 鏡像 | 判定 |
|---|---|---|---|
| CPI | 305.11 | 305.109 | 一致 |
| 10y | 3.75 | 3.75 | 一致 |

⇒ 2023-09 以後的 CPI 與 10y 直接接鏡像，口徑相同。

## ⚠️ 缺口：2023-07 以後的 S&P 500 移動 EPS

席勒的 EPS 停在 2023-06（181.17）。**這是唯一拿不到精確值的輸入。**

- 搜尋摘要層的讀數：multpl 稱 2026-07 移動 12 個月 EPS 約 **295.36**；S&P DJI「含估計」的 TTM 為 293.58（2026-12 口徑，混入預估）。**兩個都未經官方頁面驗證**（multpl.com、spglobal.com 皆被擋）。
- 模型的 `--now` 用 `--eps` 傳入，並在輸出裡標明來源層級。EPS 只影響「盈餘循環」那一項和「合理價格」換算，**不影響總體→本益比的係數**（那是 1871–2023 精確資料估的）。
- 精確來源：S&P DJI 的 `sp-500-eps-est.xlsx`（每季更新，含 as-reported 與 operating 兩種口徑的季 EPS）。**要在 Mac 上開。** 需要 2023Q3～2026Q2 的 **as-reported** 季 EPS（跟席勒同口徑），八個數字。

## 口徑注意

- 席勒 EPS 是 **as-reported（GAAP）**，不是 operating。兩者在衰退年差可達 30% 以上（2008–09）。「現在」的 EPS 必須用同口徑。
- 席勒價格是**月均**，不是月底。
- 席勒月 EPS 是季資料**線性內插**，所以第 t 月的「移動 EPS」含有最多一季的未來資訊。這對「解釋本益比水準」影響很小，對「用缺口預測未來」有輕微前視；`--backtest` 裡的均值回歸檢定另做了落後 3 個月的版本。

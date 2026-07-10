# tw-funnel — 台股投信×營收動能三層漏斗（v0，上市 TWSE only）

每日盤後掃台股籌碼，跑「資格關卡 → 否決關卡 → 等權評分」漏斗，輸出前 N 檔候選，
並追蹤買訊後 1週/1月/3月/6月/12月前瞻表現，供 monitor 網頁呈現。

設計依據：`topics/business/2026-07-10-us-tw-signal-funnel-design.md` §2（台股漏斗定稿）
＋ `topics/business/2026-07-10-stock-signal-appendix/stock_signal_taiwan.md`（實證底稿）。
架構裁決：負面災難維度用硬關卡（Beneish/Skinner-Sloan 左尾不對稱）、正面訊號等權評分
（Piotroski/AQR/DeMiguel 1/N）——不做權重最適化。

## 唯讀聲明

本專案**純唯讀**：只對 TWSE 公開免金鑰端點發唯讀 GET 查詢。
**絕不**包含任何下單、金鑰、券商連線程式碼；不構成投資建議。

## 三層漏斗（常數全在 config.py）

**第一層｜資格關卡**（全部同時成立才入池——FinLab「投信買超×營收動能」組合條件）：
- 投信當日買賣超 >0 **且** 近 3 日累計買超 ≥ 50 萬股 或 ≥ 5 千萬元（OR）★★
- 月營收 YoY >0 **且** YoY 加速（本月 YoY > 上月 YoY）★★★

**第二層｜否決關卡**（一票否決）：
- 日均成交額 < 3 千萬（20 日均；查無成交額也保守否決）
- 處置股/注意股（公告端點 best-effort，見下方誠實標註）
- 1 月作帳反轉窗：1/1–1/15 不進新倉（config 開關 `JANUARY_NO_NEW_ENTRY`）★★
- 董監質押比 >50%（接得到數據才生效，見下方誠實標註）★★★

**第三層｜等權評分**（每項 0–2 分，等權加總，取前 15）：
- 營收 YoY 加速幅度（≥5pp→1、≥15pp→2）★★★
- 投信買超強度（連買 ≥3 日 +1；3 日買超金額/市值 ≥0.05% +1）★★
- 小型股帶（市值 <300 億→2、<1000 億→1）★★
- 投信「首次」買超（近 60 交易日、本次連買段之前首見）→2 ★★

## 數據源（全部免費、免金鑰）

| 數據 | 端點 | 狀態 |
|---|---|---|
| 投信買賣超（日） | `openapi.twse.com.tw/v1/fund/T86`；備援 `twse.com.tw/rwd/zh/fund/T86` | 已接線 |
| 月營收 | `openapi.twse.com.tw/v1/opendata/t187ap05_L` | 已接線 |
| 全市場收盤/成交額 | `openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` | 已接線 |
| 已發行股數（市值） | `openapi.twse.com.tw/v1/opendata/t187ap03_L` | 已接線（缺欄退化 實收資本額/10） |
| 處置/注意股公告 | `/v1/announcement/punish`、`/v1/announcement/notice` | ⚠ best-effort，未實測 |
| 董監質押比 | `/v1/opendata/t187ap11_L` | ⚠ best-effort，欄位假設未實測 |

### 誠實標註：v0 未接線/未驗證（meta_latest.json 的 `todo_not_wired`/`degradations` 同步標註）

- **董監事申讓申報**：TWSE OpenAPI 查無對應 dataset（申讓申報在 MOPS，無官方 API）——
  否決關卡此項**未接線**（TODO：MOPS AJAX 爬蟲）。
- **處置/注意股、董監質押端點**：dataset 代號為 best-effort 推測，本開發環境 egress
  被擋無法實測；CI 首跑以 `meta_latest.json.endpoint_health` 記錄真實狀態。**失敗＝該
  否決不生效並在 degradations 誠實標註，不假裝有接。**
- **上櫃 TPEx**：v0 只做上市（TWSE）；TPEx OpenAPI 對應端點為 TODO。
- **歷史回測**：Phase 2。組合條件唯一公開回測為 FinLab 樣本內 +33.9%/yr、MDD -45.5%、
  僅 10 檔持股——期望值不可直接引用，須先 walk-forward 樣本外驗證（設計文件 §3）。

## 架構

```
config.py             端點＋全部漏斗常數（門檻、評分分級、視窗、TOP_N）
fetch_twse.py         抓 TWSE 端點 → data/state/ 精簡狀態（防禦性：端點全掛只記 meta 不 crash）
funnel.py             三層漏斗（純函數，可離線測）→ candidates_latest + meta_latest
track_performance.py  買訊事件登記＋滿窗回填 1w/1m/3m/6m/12m 報酬 → performance_tracking
tests/                離線 fixture 自測（不碰網路）
.github/workflows/tw-funnel.yml  平日 UTC 09:45（台北 17:45）＋每月 10/11 加掃＋commit-back
```

資料流：`fetch_twse → funnel → track_performance`，三支各自防禦、`|| true` 保底。
原始端點回應落 `data/tmp/`（.gitignore）；入版控僅 `data/state/` 精簡狀態＋三個輸出
json，總量 <1MB（trust 70 交易日、turnover 25 日、營收 4 個月滾動修剪）。

## 輸出契約（與美股管線完全同 schema，monitor 統一讀取）

`data/candidates_latest.json`：

```json
{"generated_at": "...", "scan_window_days": 3,
 "funnel_stats": {"raw_filings": 0, "qualified_events": 0, "post_veto": 0, "final_candidates": 0},
 "candidates": [{
   "ticker": "1101", "company": "台泥",
   "cluster_size": null, "insiders": null, "total_buy_usd": null,
   "tw_fields": {"trust_net_buy_shares": 300000, "trust_consecutive_days": 3,
                 "revenue_yoy": 12.0, "revenue_yoy_accel": 7.0},
   "score": 7, "score_breakdown": {"revenue_accel": 1, "trust_strength": 2,
                                   "small_cap": 2, "first_time_buy": 2},
   "first_filing_date": "2026-07-08", "entry_price_ref": 50.0}]}
```

美股專屬欄位（cluster_size/insiders/total_buy_usd）在台股一律 `null`；台股專屬欄位
收在 `tw_fields`。台股語意對應：`raw_filings`＝當日投信有動作檔數、
`first_filing_date`＝本次連買段起始日、`entry_price_ref`＝訊號日收盤。

`data/performance_tracking.json`（同美股契約：`positions` 陣列＋
`ticker/signal_date/entry_price_ref/current_price/status/returns` 鍵，monitor 統一讀取）：
事件（ticker×first_filing_date 去重）登記後，訊號日起算滿 7/30/91/182/365 日曆日的
第一個交易日用收盤回填 `returns`（(價/entry)−1）；價格不可得維持 `null` 每日重試；
全窗填滿 `status: "completed"`。

`data/meta_latest.json`：端點健康、漏斗統計、否決原因計數、1 月窗狀態、降級/TODO
誠實標註、漏斗饑餓警告（否決後 <10 檔）/失效警告（>100 檔）。

## 如何在本機跑

```bash
cd projects/tw-funnel
pip install -r requirements.txt      # 只需要 requests

python3 fetch_twse.py                # 需要能連 openapi.twse.com.tw 的網路環境
python3 funnel.py
python3 track_performance.py

python3 tests/test_offline.py        # 離線自測（不碰網路、不需 requests）
```

## 已知限制

- 資格關卡需要**兩期**月營收史料判 YoY 加速：上線首月只有一期 → 通過籌碼關的股票
  以 `accel_unknown` 誠實不入池，滿兩期後自動恢復（不假造上月 YoY）。
- 投信「首次買超」回看視窗同樣隨狀態逐日累積，前 60 交易日內判定偏鬆（史料淺）。
- OpenAPI 多數 dataset 只給最近一期——歷史全靠 CI 逐日累積，斷跑會留缺口。
- 月營收公布集中每月 10 日前後；月中前段 YoY 用的是上月數字（數據本身的節奏，非 bug）。

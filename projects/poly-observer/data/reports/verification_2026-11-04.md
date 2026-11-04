# Polymarket 聰明錢存在性檢驗 — 2026-11-04

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 0 | 2 | status=410 HTTP 410; body={"error":"Data API v1 has been retired","migration":"https://data-api.polymarket.com/v2/","doc |
| `data-api.polymarket.com/positions` | 0 | 2 | status=410 HTTP 410; body={"error":"Data API v1 has been retired","migration":"https://data-api.polymarket.com/v2/","doc |
| `data-api.polymarket.com/v1/leaderboard` | 0 | 3 | status=410 HTTP 410; body={"error":"Data API v1 has been retired","migration":"https://data-api.polymarket.com/v2/","doc |
| `data-api.polymarket.com/value` | 0 | 2 | status=410 HTTP 410; body={"error":"Data API v1 has been retired","migration":"https://data-api.polymarket.com/v2/","doc |
| `lb-api.polymarket.com/leaderboard` | 0 | 3 | status=410 HTTP 410; body={"error":"lb-api.polymarket.com has been retired. Use https://data-api.polymarket.com/v2/leade |
| `user-pnl-api.polymarket.com/user-pnl` | 0 | 4 | status=410 HTTP 410; body={"error":"user-pnl-api.polymarket.com has been retired. Use https://data-api.polymarket.com/v2 |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 0 | 0% |
| degraded | 0 | 0% |
| dormant | 0 | 0% |
| one_hit | 0 | 0% |
| mm_bot_like | 0 | 0% |
| choppy | 0 | 0% |
| insufficient_data | 2 | 100% |
| **合計** | **2** | |

## 3. consistent_winner 明細

（本日無 consistent_winner）

## 4. Ground-truth 校驗

- ❌ **【不符，分類器需檢查】** `0x25e28169faea17421fcd4cc361f6436d1e449a09`：預期 dormant，實際 **insufficient_data**

## 5. 裁決

consistent_winner 數量：**0**

**未發現（本日樣本內沒有符合 consistent_winner 條件的錢包）**

限制與聲明：
- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。
- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。
- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。
- 本工具純唯讀，不執行任何交易。

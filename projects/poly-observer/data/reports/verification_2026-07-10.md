# Polymarket 聰明錢存在性檢驗 — 2026-07-10

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 2 | 0 | — |
| `data-api.polymarket.com/leaderboard` | 0 | 3 | status=404 HTTP 404; body=404 page not found |
| `data-api.polymarket.com/positions` | 1 | 0 | — |
| `data-api.polymarket.com/value` | 1 | 0 | — |
| `lb-api.polymarket.com/leaderboard` | 0 | 3 | status=404 HTTP 404; body=404 page not found |
| `user-pnl-api.polymarket.com/user-pnl` | 1 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 1 | 100% |
| degraded | 0 | 0% |
| one_hit | 0 | 0% |
| mm_bot_like | 0 | 0% |
| choppy | 0 | 0% |
| insufficient_data | 0 | 0% |
| **合計** | **1** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |
|---|---:|---:|---:|---:|---|---|
| `0x25e28169faea17421fcd4cc361f6436d1e449a09` | $176,390 | 83% | 33% | 130.5 | esports (58%) | 否 |

## 4. Ground-truth 校驗

- ❌ **【不符，分類器需檢查】** `0x25e28169faea17421fcd4cc361f6436d1e449a09`：預期 one_hit / degraded，實際 **consistent_winner**

## 5. 裁決

consistent_winner 數量：**1**

**弱存在（樣本內僅少數 consistent_winner，證據不足，需持續觀察）**

限制與聲明：
- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。
- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。
- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。
- 本工具純唯讀，不執行任何交易。

# Polymarket 聰明錢存在性檢驗 — 2026-08-08

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 176 | 0 | — |
| `data-api.polymarket.com/positions` | 60 | 0 | — |
| `data-api.polymarket.com/v1/leaderboard` | 2 | 0 | — |
| `data-api.polymarket.com/value` | 60 | 0 | — |
| `user-pnl-api.polymarket.com/user-pnl` | 60 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 5 | 8% |
| degraded | 0 | 0% |
| dormant | 8 | 13% |
| one_hit | 17 | 28% |
| mm_bot_like | 8 | 13% |
| choppy | 22 | 37% |
| insufficient_data | 0 | 0% |
| **合計** | **60** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |
|---|---:|---:|---:|---:|---|---|
| `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` | $12,687,027 | 100% | 10% | 1,330.0 | other (80%) | 否 |
| `0xbca08c1bc204a34f2fddbe47b438b9bd42ac9705` | $1,359,536 | 100% | 17% | 1,323.0 | sports (100%) | 否 |
| `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` | $1,164,266 | 64% | 9% | 1,475.0 | other (45%) | 否 |
| `0x43372356634781eea88d61bbdd7824cdce958882` | $726,878 | 73% | 39% | 699.0 | other (68%) | 否 |
| `0x25e28169faea17421fcd4cc361f6436d1e449a09` | $176,190 | 71% | 33% | 112.0 | esports (58%) | 否 |

## 4. Ground-truth 校驗

- ❌ **【不符，分類器需檢查】** `0x25e28169faea17421fcd4cc361f6436d1e449a09`：預期 dormant，實際 **consistent_winner**

## 5. 裁決

consistent_winner 數量：**5**

**聰明錢存在（存在性檢驗通過；前瞻持續性需觀察器累積數據驗證）**

限制與聲明：
- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。
- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。
- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。
- 本工具純唯讀，不執行任何交易。

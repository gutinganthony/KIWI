# Polymarket 聰明錢存在性檢驗 — 2026-07-10

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 171 | 0 | — |
| `data-api.polymarket.com/positions` | 60 | 0 | — |
| `data-api.polymarket.com/v1/leaderboard` | 2 | 0 | — |
| `data-api.polymarket.com/value` | 60 | 0 | — |
| `user-pnl-api.polymarket.com/user-pnl` | 60 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 1 | 2% |
| degraded | 0 | 0% |
| dormant | 5 | 8% |
| one_hit | 34 | 57% |
| mm_bot_like | 3 | 5% |
| choppy | 17 | 28% |
| insufficient_data | 0 | 0% |
| **合計** | **60** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |
|---|---:|---:|---:|---:|---|---|
| `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` | $11,011,636 | 100% | 10% | 1,344.0 | sports (81%) | 否 |

## 4. Ground-truth 校驗

- ✅ `0x25e28169faea17421fcd4cc361f6436d1e449a09`：預期 dormant，實際 **dormant** — 符合

## 5. 裁決

consistent_winner 數量：**1**

**弱存在（樣本內僅少數 consistent_winner，證據不足，需持續觀察）**

限制與聲明：
- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。
- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。
- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。
- 本工具純唯讀，不執行任何交易。

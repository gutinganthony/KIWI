# Polymarket 聰明錢存在性檢驗 — 2026-08-25

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 160 | 0 | — |
| `data-api.polymarket.com/positions` | 60 | 0 | — |
| `data-api.polymarket.com/v1/leaderboard` | 2 | 0 | — |
| `data-api.polymarket.com/value` | 60 | 0 | — |
| `user-pnl-api.polymarket.com/user-pnl` | 60 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 4 | 7% |
| degraded | 0 | 0% |
| dormant | 10 | 17% |
| one_hit | 21 | 35% |
| mm_bot_like | 10 | 17% |
| choppy | 15 | 25% |
| insufficient_data | 0 | 0% |
| **合計** | **60** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |
|---|---:|---:|---:|---:|---|---|
| `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` | $12,798,925 | 100% | 10% | 1,316.0 | other (98%) | 否 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | $974,417 | 100% | 17% | 1,413.0 | crypto (100%) | 否 |
| `0x4f1d5ae26fc31472966e951af3183308736d8de2` | $704,348 | 80% | 36% | 554.0 | other (40%) | 否 |
| `0xa3282d3e882501229c75d0caf134e62e3afb4977` | $324,089 | 100% | 34% | 1,275.0 | other (47%) | 否 |

## 4. Ground-truth 校驗

- ✅ `0x25e28169faea17421fcd4cc361f6436d1e449a09`：預期 dormant，實際 **dormant** — 符合

## 5. 裁決

consistent_winner 數量：**4**

**弱存在（樣本內僅少數 consistent_winner，證據不足，需持續觀察）**

限制與聲明：
- 錢包宇宙取自今日排行榜（＋seeds），存在倖存者偏差：只看得到現在還在榜上的贏家。
- 本檢驗證明的是聰明錢的「存在性」，不是「跟得到」——前瞻持續性需觀察器逐日累積數據驗證。
- 標注低信心（low_confidence）的錢包，其 PnL 由 activity 現金流近似，僅供參考。
- 本工具純唯讀，不執行任何交易。

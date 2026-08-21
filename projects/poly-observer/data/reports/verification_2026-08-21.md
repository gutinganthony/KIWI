# Polymarket 聰明錢存在性檢驗 — 2026-08-21

> 純唯讀分析報告。宇宙取自今日排行榜＋seeds，**有倖存者偏差**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `data-api.polymarket.com/activity` | 168 | 0 | — |
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
| one_hit | 20 | 33% |
| mm_bot_like | 10 | 17% |
| choppy | 16 | 27% |
| insufficient_data | 0 | 0% |
| **合計** | **60** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 正月比率 | 峰值回撤 | 頻率(筆/月) | 主類別 | 低信心 |
|---|---:|---:|---:|---:|---|---|
| `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` | $12,607,719 | 100% | 10% | 1,325.0 | other (73%) | 否 |
| `0xb55fa1296e6ec55d0ce53d93b9237389f11764d4` | $946,198 | 100% | 17% | 1,441.0 | crypto (100%) | 否 |
| `0x43372356634781eea88d61bbdd7824cdce958882` | $742,162 | 73% | 39% | 1,342.0 | other (56%) | 否 |
| `0x4f1d5ae26fc31472966e951af3183308736d8de2` | $403,365 | 80% | 36% | 558.0 | other (34%) | 否 |

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

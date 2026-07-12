# Hyperliquid 永續聰明錢存在性檢驗 — 2026-07-12

> 純唯讀分析報告。宇宙取自今日 leaderboard（＋seeds），**有倖存者偏差＋刷量污染**；
> 本檢驗證明的是「存在性」，非「跟得到」。前瞻持續性需觀察器累積數據驗證。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 60 | 0 | — |
| `leaderboard @ stats-data.hyperliquid.xyz/Mainnet/leaderboard` | 1 | 0 | — |
| `portfolio @ api.hyperliquid.xyz/info` | 60 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 60 | 0 | — |
| `userFunding @ api.hyperliquid.xyz/info` | 60 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 1 | 2% |
| blowup_risk | 27 | 45% |
| wash_suspect | 27 | 45% |
| one_hit | 1 | 2% |
| dormant | 0 | 0% |
| choppy | 4 | 7% |
| insufficient_data | 0 | 0% |
| **合計** | **60** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 |
|---|---:|---:|---:|---:|---|---:|
| `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d` | $9,609,116 | 6% | 16.71 | 3x | @166 | 361 |

## 4. Ground-truth 校驗

- ✅ `0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6`：預期 blowup_risk，實際 **blowup_risk** — 符合

## 5. 裁決

consistent_winner 數量：**1**

**弱存在（樣本內僅少數 consistent_winner，證據不足，需持續觀察）**

限制與醒目聲明：
- **倖存者偏差**：宇宙取自今日 leaderboard（＋seeds），只看得到現在還在榜上的贏家。
- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；本檢驗以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。
- **存在性 ≠ 跟得到**：本檢驗證明聰明錢的「存在性」，非「跟得到」——前瞻持續性需觀察器逐日累積數據驗證；跟單模擬器為下一個里程碑。
- **槓桿風險**：永續高槓桿可造高勝率直到一次強平歸零（James Wynn 為活教材）；consistent_winner 已要求槓桿在合理範圍，但過往績效不保證未來不爆倉。
- 標注低信心（low_confidence）的錢包缺 portfolio PnL 曲線，指標可信度較低。
- 本工具**純唯讀**，只查公開 info API，不執行任何下單、簽章或錢包連線。

# Hyperliquid 廣域可跟錢包掃描 — 2026-08-22

> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，
> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；
> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 123 | 0 | — |
| `clearinghouseState@abcd @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@cash @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@flx @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@hyna @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@io @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@km @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@mkts @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@para @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@vntl @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `clearinghouseState@xyz @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `perpDexs @ api.hyperliquid.xyz/info` | 1 | 0 | — |
| `portfolio @ api.hyperliquid.xyz/info` | 123 | 0 | — |
| `spotClearinghouseState @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 123 | 0 | — |
| `userFunding @ api.hyperliquid.xyz/info` | 123 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 3 | 2% |
| blowup_risk | 66 | 54% |
| wash_suspect | 10 | 8% |
| one_hit | 24 | 20% |
| dormant | 0 | 0% |
| choppy | 20 | 16% |
| insufficient_data | 0 | 0% |
| **合計** | **123** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 | 可跟 |
|---|---:|---:|---:|---:|---|---:|---|
| `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d` | $10,921,861 | 6% | 8.31 | 10x | xyz:GOOGL | 402 | ✅（30d 事件 38（截斷外推 50）／fills 2,000）|
| `0x3e9b6020cb47785b9416e83fad561a72d2af4de8` | $917,582 | 5% | 4.95 | —x | @107 | 626 | ✅（30d 事件 0／fills 0）|
| `0x0a0b4d654d967a00407f5329588a258b68a4f615`（⚠️ 曾強平 2 次） | $31,929 | 0% | 1.43 | —x | @107 | 843 | ❌ 持倉過短：平均 6.1h < 12h（30d 事件 0／fills 0）|

## 4. Ground-truth 校驗

- ✅ `0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6`：預期 blowup_risk，實際 **blowup_risk** — 符合

## 5. 裁決

consistent_winner 數量：**3**
其中 followable（可跟）數量：**2**

**consistent_winner 3 個，其中 followable 2 個（僅少數可跟候選，證據不足，需持續觀察）**

限制與醒目聲明：
- **回望偏差**：宇宙來自全量排行榜以歷史窗績效過濾（非僅榜頂，倖存者偏差較輕），但「過去可跟畫像」仍是回望篩選；存在性 ≠ 未來獲利。
- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；本檢驗以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。
- **存在性 ≠ 跟得到**：本檢驗證明聰明錢的「存在性」，非「跟得到」——前瞻持續性需觀察器逐日累積數據驗證；跟單模擬器為下一個里程碑。
- **槓桿風險**：永續高槓桿可造高勝率直到一次強平歸零（James Wynn 為活教材）；consistent_winner 已要求槓桿在合理範圍，但過往績效不保證未來不爆倉。
- 標注低信心（low_confidence）的錢包缺 portfolio PnL 曲線，指標可信度較低。
- 本工具**純唯讀**，只查公開 info API，不執行任何下單、簽章或錢包連線。

# Hyperliquid 廣域可跟錢包掃描 — 2026-07-19

> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，
> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；
> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 32 | 0 | — |
| `portfolio @ api.hyperliquid.xyz/info` | 32 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 32 | 0 | — |
| `userFunding @ api.hyperliquid.xyz/info` | 32 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 6 | 19% |
| blowup_risk | 17 | 53% |
| wash_suspect | 1 | 3% |
| one_hit | 2 | 6% |
| dormant | 0 | 0% |
| choppy | 6 | 19% |
| insufficient_data | 0 | 0% |
| **合計** | **32** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 | 可跟 |
|---|---:|---:|---:|---:|---|---:|---|
| `0x99b1098d9d50aa076f78bd26ab22e6abd3710729` | $26,449,688 | 40% | 5.03 | 10x | xyz:SKHX | 312 | ❌ 頻率過高：30 日推估 232 個部位事件 > 150（fills 截斷窗覆蓋 5.0 天、實測 39 個外推；fills 2000 筆僅參考）（30d 事件 39（截斷外推 232）／fills 2,000）|
| `0x06cecfbac34101ae41c88ebc2450f8602b3d164b` | $14,334,773 | 28% | 0.88 | 20x | @107 | 676 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 19／fills 1,387）|
| `0x84abc08c0ea62e687c370154de1f38ea462f4d37` | $12,605,726 | 22% | — | —x | xyz:DRAM | 361 | ❌ 平均持倉時間估不出（無 Open/Close 成交可配對），保守判不可跟（30d 事件 3（截斷外推 39）／fills 2,000）|
| `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d` | $9,598,888 | 6% | 9.78 | —x | @166 | 368 | ✅（30d 事件 51（截斷外推 84）／fills 2,000）|
| `0xbe19541903f64af97bcf8436f4d15bf3a56b8bd1`（⚠️ 曾強平 1 次） | $9,380,936 | 17% | — | 20x | WLD | 354 | ❌ 平均持倉時間估不出（無 Open/Close 成交可配對），保守判不可跟；槓桿過高：目前 20x > 10x（30d 事件 3（截斷外推 11）／fills 2,000）|
| `0xbe494a5e3a719a78a45a47ab453b7b0199b9d101` | $2,914,768 | 34% | 0.54 | 20x | HYPE | 305 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 28（截斷外推 65）／fills 2,000）|

## 4. Ground-truth 校驗

- ✅ `0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6`：預期 blowup_risk，實際 **blowup_risk** — 符合

## 5. 裁決

consistent_winner 數量：**6**
其中 followable（可跟）數量：**1**

**consistent_winner 6 個，其中 followable 1 個（僅少數可跟候選，證據不足，需持續觀察）**

限制與醒目聲明：
- **回望偏差**：宇宙來自全量排行榜以歷史窗績效過濾（非僅榜頂，倖存者偏差較輕），但「過去可跟畫像」仍是回望篩選；存在性 ≠ 未來獲利。
- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；本檢驗以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。
- **存在性 ≠ 跟得到**：本檢驗證明聰明錢的「存在性」，非「跟得到」——前瞻持續性需觀察器逐日累積數據驗證；跟單模擬器為下一個里程碑。
- **槓桿風險**：永續高槓桿可造高勝率直到一次強平歸零（James Wynn 為活教材）；consistent_winner 已要求槓桿在合理範圍，但過往績效不保證未來不爆倉。
- 標注低信心（low_confidence）的錢包缺 portfolio PnL 曲線，指標可信度較低。
- 本工具**純唯讀**，只查公開 info API，不執行任何下單、簽章或錢包連線。

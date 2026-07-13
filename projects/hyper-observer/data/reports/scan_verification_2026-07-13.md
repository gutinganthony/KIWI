# Hyperliquid 廣域可跟錢包掃描 — 2026-07-13

> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，
> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；
> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 40 | 0 | — |
| `portfolio @ api.hyperliquid.xyz/info` | 40 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 40 | 0 | — |
| `userFunding @ api.hyperliquid.xyz/info` | 40 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 6 | 15% |
| blowup_risk | 24 | 60% |
| wash_suspect | 2 | 5% |
| one_hit | 1 | 2% |
| dormant | 0 | 0% |
| choppy | 7 | 18% |
| insufficient_data | 0 | 0% |
| **合計** | **40** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 | 可跟 |
|---|---:|---:|---:|---:|---|---:|---|
| `0x8e096995c3e4a3f0bc5b3ea1cba94de2aa4d70c9` | $59,393,127 | 35% | 453,866.15 | 20x | xyz:SKHX | 579 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 8（截斷外推 22）／fills 2,000）|
| `0x06cecfbac34101ae41c88ebc2450f8602b3d164b` | $14,017,350 | 28% | 2.22 | 20x | AAVE | 670 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 19／fills 936）|
| `0x84abc08c0ea62e687c370154de1f38ea462f4d37` | $12,227,038 | 21% | 0.32 | —x | xyz:DRAM | 355 | ❌ 頻率過高：30 日推估 627 個部位事件 > 150（fills 截斷窗覆蓋 0.3 天、實測 6 個外推；fills 2000 筆僅參考）；持倉過短：平均 0.0h < 12h（30d 事件 6（截斷外推 627）／fills 2,000）|
| `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d` | $9,577,958 | 6% | 16.71 | 3x | @166 | 362 | ✅（30d 事件 41／fills 1,028）|
| `0xbe19541903f64af97bcf8436f4d15bf3a56b8bd1`（⚠️ 曾強平 1 次） | $9,058,873 | 17% | — | 20x | WLD | 348 | ❌ 平均持倉時間估不出（無 Open/Close 成交可配對），保守判不可跟；槓桿過高：目前 20x > 10x（30d 事件 3（截斷外推 40）／fills 2,000）|
| `0xbe494a5e3a719a78a45a47ab453b7b0199b9d101` | $2,912,041 | 34% | 45.17 | 20x | HYPE | 299 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 20（截斷外推 86）／fills 2,000）|

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

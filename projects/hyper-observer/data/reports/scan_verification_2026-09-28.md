# Hyperliquid 廣域可跟錢包掃描 — 2026-09-28

> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，
> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；
> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 105 | 0 | — |
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
| `portfolio @ api.hyperliquid.xyz/info` | 105 | 0 | — |
| `spotClearinghouseState @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 104 | 1 | status=429 HTTP 429; body=null |
| `userFunding @ api.hyperliquid.xyz/info` | 105 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 6 | 6% |
| blowup_risk | 51 | 49% |
| wash_suspect | 11 | 10% |
| one_hit | 11 | 10% |
| dormant | 0 | 0% |
| choppy | 26 | 25% |
| insufficient_data | 0 | 0% |
| **合計** | **105** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 | 可跟 |
|---|---:|---:|---:|---:|---|---:|---|
| `0x456f1049c0f2ec990091bbd3f30af62aca3fcdf1` | $2,945,285 | 12% | 5,343.11 | 10x | ZEC | 459 | ❌ 頻率過高：30 日推估 412 個部位事件 > 150（fills 截斷窗覆蓋 6.6 天、實測 90 個外推；fills 2000 筆僅參考）（30d 事件 90（截斷外推 412）／fills 2,000）|
| `0x230963164d9637a4c536270a06b4e3636d44a2d9` | $2,395,072 | 31% | 2.45 | 20x | ZEC | 494 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 7／fills 549）|
| `0xb5101614ad71468a041a83e64d8b834aa17a1ed6` | $1,065,713 | 39% | 1.41 | 20x | XRP | 662 | ❌ 槓桿過高：目前 20x > 10x（30d 事件 54／fills 1,583）|
| `0x3e9b6020cb47785b9416e83fad561a72d2af4de8` | $917,582 | 5% | 7.55 | —x | @107 | 662 | ✅（30d 事件 3／fills 577）|
| `0xa237f4cc7bbc930fd531b1a36f31e54f778fc431` | $142,614 | 26% | 0.87 | 20x | CASHCAT | 816 | ❌ 持倉過短：平均 12.0h < 12h；槓桿過高：目前 20x > 10x（30d 事件 34（截斷外推 39）／fills 2,000）|
| `0x0a0b4d654d967a00407f5329588a258b68a4f615`（⚠️ 曾強平 2 次） | $32,330 | 0% | 1.43 | —x | @107 | 879 | ❌ 持倉過短：平均 6.1h < 12h（30d 事件 0／fills 0）|

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

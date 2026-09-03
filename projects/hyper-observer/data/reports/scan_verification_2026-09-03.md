# Hyperliquid 廣域可跟錢包掃描 — 2026-09-03

> 純唯讀掃描報告。宇宙來自**全量排行榜以「可跟畫像」過濾出的候選**（中段與榜外，
> 非僅榜頂），倖存者偏差較 top-N 輕，但過濾以歷史窗績效為準，**仍有回望偏差**；
> 存在性 ≠ 未來獲利、≠ 跟得到。followable 為機械可行性判定，非投資建議。

## 1. 端點健康

| 端點 | 成功 | 失敗 | 失敗樣本 |
|---|---:|---:|---|
| `clearinghouseState @ api.hyperliquid.xyz/info` | 45 | 0 | — |
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
| `portfolio @ api.hyperliquid.xyz/info` | 45 | 0 | — |
| `spotClearinghouseState @ api.hyperliquid.xyz/info` | 3 | 0 | — |
| `userFills @ api.hyperliquid.xyz/info` | 45 | 0 | — |
| `userFunding @ api.hyperliquid.xyz/info` | 45 | 0 | — |

## 2. 分類統計

| 分類 | 錢包數 | 佔比 |
|---|---:|---:|
| consistent_winner | 3 | 7% |
| blowup_risk | 30 | 67% |
| wash_suspect | 2 | 4% |
| one_hit | 2 | 4% |
| dormant | 0 | 0% |
| choppy | 8 | 18% |
| insufficient_data | 0 | 0% |
| **合計** | **45** | |

## 3. consistent_winner 明細

| 地址 | 總 PnL | 峰值回撤 | profit factor | 目前槓桿 | 主力幣 | 活躍天 | 可跟 |
|---|---:|---:|---:|---:|---|---:|---|
| `0x8bae3527e5a33fa0cf184f37bc112d071463ab6d` | $11,295,937 | 6% | 11.15 | 10x | xyz:META | 413 | ✅（30d 事件 28／fills 852）|
| `0xd2a238110d411970efdc9cccfb4110a6fe24206e` | $1,633,535 | 0% | 379.45 | —x | @151 | 525 | ✅（30d 事件 0／fills 0）|
| `0xbd34523189edc7a9e9c202a15e00afe18ba4bc7f` | $64,846 | 31% | 4.23 | 3x | @107 | 214 | ✅（30d 事件 14／fills 1,036）|

## 4. Ground-truth 校驗

- ✅ `0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6`：預期 blowup_risk，實際 **blowup_risk** — 符合

## 5. 裁決

consistent_winner 數量：**3**
其中 followable（可跟）數量：**3**

**consistent_winner 3 個，其中 followable 3 個（僅少數可跟候選，證據不足，需持續觀察）**

限制與醒目聲明：
- **回望偏差**：宇宙來自全量排行榜以歷史窗績效過濾（非僅榜頂，倖存者偏差較輕），但「過去可跟畫像」仍是回望篩選；存在性 ≠ 未來獲利。
- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；本檢驗以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。
- **存在性 ≠ 跟得到**：本檢驗證明聰明錢的「存在性」，非「跟得到」——前瞻持續性需觀察器逐日累積數據驗證；跟單模擬器為下一個里程碑。
- **槓桿風險**：永續高槓桿可造高勝率直到一次強平歸零（James Wynn 為活教材）；consistent_winner 已要求槓桿在合理範圍，但過往績效不保證未來不爆倉。
- 標注低信心（low_confidence）的錢包缺 portfolio PnL 曲線，指標可信度較低。
- 本工具**純唯讀**，只查公開 info API，不執行任何下單、簽章或錢包連線。

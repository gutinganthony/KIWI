# 全維度診斷探測 — 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

> 純唯讀診斷（2026-10-30，探測時間 2026-10-30T02:13:33.557245+00:00）。
> 只用 Hyperliquid 公開 info API 的查詢型 type；不含下單/簽章/金鑰/錢包連線。
> 動機：clearinghouseState（不帶 dex）只看原生永續 dex，對 HIP-3 builder 市場全盲，導致「0 持倉、$0 淨值」與 portfolio 的百萬淨值自相矛盾。

## 0. 探測結果總表

| 查詢 | 成功 |
|---|---|
| perpDexs | ✅ |
| clearinghouseState_native | ✅ |
| clearinghouseState_dex | ✅ |
| spotClearinghouseState | ✅ |
| userNonFundingLedgerUpdates | ✅ |
| portfolio | ✅ |
| userFills | ✅ |

perpDexs 偵測到的 builder dex（查詢上限 10 個）：xyz, flx, vntl, hyna, km, abcd, cash, para, mkts, io

## (a) 資金在哪？

| 場所 | 帳戶淨值(USD) | 未平倉數 | 持倉名目(USD) |
|---|---:|---:|---:|
| 原生永續 dex | $545,791.97 | 2 | $28,675.73 |
| builder dex `abcd` | $0.00 | 0 | $0.00 |
| builder dex `cash` | $0.00 | 0 | $0.00 |
| builder dex `flx` | $0.00 | 0 | $0.00 |
| builder dex `hyna` | $0.00 | 0 | $0.00 |
| builder dex `io` | $0.00 | 0 | $0.00 |
| builder dex `km` | $0.00 | 0 | $0.00 |
| builder dex `mkts` | $0.00 | 0 | $0.00 |
| builder dex `para` | $0.00 | 0 | $0.00 |
| builder dex `vntl` | $0.00 | 0 | $0.00 |
| builder dex `xyz` | $535,866.71 | 3 | $4,689,553.03 |
| 現貨 spot | $4,394,092.53（含估算） | 3 幣 | — |
| **合計** | **$5,475,751.20** | **5** | — |

非原生（builder dex＋現貨）占比：**90.0%**（$4,929,959.24 / $5,475,751.20）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 4,345,877.2695 | $4,345,877.27 |
| USDT0 | 48,215.2509 | $48,215.25（估） |
| USDH | 0.01250805 | $0.01 |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $4,393,843.24 | $5,536,041.61 |
| week | $4,393,843.24 | $5,536,041.61 |
| month | $4,393,843.24 | $12,975,863.80 |
| allTime | $4,393,843.24 | $374,728,419.46 |
| perpDay | $1,081,815.36 | $5,536,041.61 |
| perpWeek | $1,081,815.36 | $5,536,041.61 |
| perpMonth | $1,081,815.36 | $12,975,863.80 |
| perpAllTime | $1,081,815.36 | $366,674,062.40 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| xyz | xyz:SKHY | short | 10x | $2,427,305.51 | $785,965.39 |
| xyz | xyz:SKHX | long | 10x | $2,200,724.86 | $-817,313.39 |
| xyz | xyz:GOOGL | long | 10x | $61,522.66 | $-13,953.96 |
| （原生） | TNSR | long | 3x | $23,174.66 | $-8,308.71 |
| （原生） | BSV | long | 3x | $5,501.07 | $368.33 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：1（回應共 1 筆，json 保留 1 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$900,000.00**
- 外部入金合計：$0.00
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | bridge_out | 1 | $900,000.00 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$900,000.00**，1 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-10-10T05:29:03.127000+00:00 | $900,000.00 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-10-29T16:52:57.646000+00:00**（距今 0.39 天）
- 近 7 天成交：**282** 筆／近 30 天：**676** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1226, 'native': 745, 'builder:para': 29}
- 主力幣：xyz:NVDA×490、DOGE×302、xyz:SKHY×234、xyz:INTC×224、xyz:DRAM×180
- 目前持倉：5 個（原生 2／builder dex 3）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-10-29T16:52:57.646000+00:00 | kNEIRO | Close Long | 0.06932 | 82,931.1 |
| 2026-10-29T16:52:57.594000+00:00 | kNEIRO | Close Long | 0.06932 | 577 |
| 2026-10-29T16:52:57.594000+00:00 | kNEIRO | Close Long | 0.06932 | 577 |
| 2026-10-29T16:52:57.594000+00:00 | kNEIRO | Close Long | 0.06932 | 14,339.4 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.0698 | 180.4 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06979 | 2,658 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06979 | 2,526.5 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06976 | 3,794.6 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06973 | 8,553.2 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06972 | 8,060.4 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.0697 | 8,553.2 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.0697 | 9,149.4 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.0697 | 9,908.8 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06969 | 8,065.6 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06969 | 16,309.5 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06967 | 8,553.2 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06966 | 8,066.8 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06964 | 8,553.2 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06963 | 8,038 |
| 2026-10-29T16:52:57.171000+00:00 | kNEIRO | Close Long | 0.06963 | 28,709 |

## 裁決

- 非原生資金 $4,929,959.24 占總資產 $5,475,751.20 的90%（builder dex $535,866.71／現貨 $4,394,092.53）
- 成交戰場分布：非原生 1255/2000 筆（63%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $900,000.00

**裁決：同地址換戰場（builder dex/現貨）**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

# 全維度診斷探測 — 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

> 純唯讀診斷（2026-10-12，探測時間 2026-10-12T01:52:49.048982+00:00）。
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
| 原生永續 dex | $728,118.99 | 5 | $1,834,500.29 |
| builder dex `abcd` | $0.00 | 0 | $0.00 |
| builder dex `cash` | $0.00 | 0 | $0.00 |
| builder dex `flx` | $0.00 | 0 | $0.00 |
| builder dex `hyna` | $0.00 | 0 | $0.00 |
| builder dex `io` | $0.00 | 0 | $0.00 |
| builder dex `km` | $0.00 | 0 | $0.00 |
| builder dex `mkts` | $0.00 | 0 | $0.00 |
| builder dex `para` | $0.00 | 0 | $0.00 |
| builder dex `vntl` | $0.00 | 0 | $0.00 |
| builder dex `xyz` | $545,110.19 | 3 | $5,417,390.73 |
| 現貨 spot | $4,248,194.76（含估算） | 3 幣 | — |
| **合計** | **$5,521,423.94** | **8** | — |

非原生（builder dex＋現貨）占比：**86.8%**（$4,793,304.95 / $5,521,423.94）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 4,199,979.4922 | $4,199,979.49 |
| USDT0 | 48,215.2509 | $48,215.25（估） |
| USDH | 0.01250805 | $0.01 |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $4,248,477.82 | $0.00 |
| week | $4,248,477.82 | $7,419,940.91 |
| month | $4,248,477.82 | $12,203,394.76 |
| allTime | $4,248,477.82 | $369,172,496.57 |
| perpDay | $1,272,204.84 | $0.00 |
| perpWeek | $1,272,204.84 | $7,419,940.91 |
| perpMonth | $1,272,204.84 | $12,203,394.76 |
| perpAllTime | $1,272,204.84 | $361,118,139.51 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| xyz | xyz:SKHY | short | 10x | $2,757,999.76 | $455,271.14 |
| xyz | xyz:SKHX | long | 10x | $2,581,846.56 | $-436,191.69 |
| （原生） | BTC | short | 40x | $896,937.11 | $3,472.19 |
| （原生） | DOGE | long | 10x | $843,068.17 | $-55,858.29 |
| xyz | xyz:GOOGL | long | 10x | $77,544.41 | $2,067.79 |
| （原生） | TNSR | long | 3x | $32,768.93 | $1,285.56 |
| （原生） | kNEIRO | long | 3x | $31,617.49 | $4,113.38 |
| （原生） | BSV | long | 3x | $30,108.59 | $4,308.81 |

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

- 最後成交時間：**2026-10-10T20:04:08.584000+00:00**（距今 1.24 天）
- 近 7 天成交：**319** 筆／近 30 天：**477** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1582, 'native': 389, 'builder:para': 29}
- 主力幣：xyz:NVDA×490、xyz:DRAM×318、xyz:SKHY×234、xyz:INTC×224、xyz:SKHX×180
- 目前持倉：8 個（原生 5／builder dex 3）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-10-10T20:04:08.584000+00:00 | BSV | Close Long | 19.70 | 31.94 |
| 2026-10-10T05:26:05.612000+00:00 | BSV | Close Long | 19.70 | 82,207.57 |
| 2026-10-07T07:42:17.350000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:17.350000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:17.350000+00:00 | kNEIRO | Close Long | 0.086 | 5,633.2 |
| 2026-10-07T07:42:16.952000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:16.746000+00:00 | kNEIRO | Close Long | 0.086 | 6,009 |
| 2026-10-07T07:42:16.544000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:16.412000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:16.002000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:15.805000+00:00 | kNEIRO | Close Long | 0.086 | 765.1 |
| 2026-10-07T07:42:15.406000+00:00 | kNEIRO | Close Long | 0.086 | 7,265.7 |
| 2026-10-07T07:42:14.721000+00:00 | kNEIRO | Close Long | 0.086 | 7,264 |
| 2026-10-07T07:42:14.243000+00:00 | kNEIRO | Close Long | 0.086 | 6,009 |
| 2026-10-07T07:42:13.795000+00:00 | kNEIRO | Close Long | 0.086 | 1,149 |
| 2026-10-07T07:42:13.464000+00:00 | kNEIRO | Close Long | 0.086 | 11,595.7 |
| 2026-10-07T07:42:13.464000+00:00 | kNEIRO | Close Long | 0.086 | 1,162.8 |
| 2026-10-07T07:42:13.392000+00:00 | kNEIRO | Close Long | 0.086 | 815.9 |
| 2026-10-07T07:42:13.125000+00:00 | kNEIRO | Close Long | 0.086 | 116,004.3 |
| 2026-10-07T07:42:12.989000+00:00 | kNEIRO | Close Long | 0.086 | 1,163 |

## 裁決

- 非原生資金 $4,793,304.95 占總資產 $5,521,423.94 的87%（builder dex $545,110.19／現貨 $4,248,194.76）
- 成交戰場分布：非原生 1611/2000 筆（81%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $900,000.00

**裁決：同地址換戰場（builder dex/現貨）**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

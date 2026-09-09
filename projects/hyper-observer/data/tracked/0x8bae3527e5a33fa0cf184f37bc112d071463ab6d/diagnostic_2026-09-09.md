# 全維度診斷探測 — 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

> 純唯讀診斷（2026-09-09，探測時間 2026-09-09T00:44:51.288571+00:00）。
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
| 原生永續 dex | $0.00 | 0 | $0.00 |
| builder dex `abcd` | $0.00 | 0 | $0.00 |
| builder dex `cash` | $0.00 | 0 | $0.00 |
| builder dex `flx` | $0.00 | 0 | $0.00 |
| builder dex `hyna` | $0.00 | 0 | $0.00 |
| builder dex `io` | $0.00 | 0 | $0.00 |
| builder dex `km` | $0.00 | 0 | $0.00 |
| builder dex `mkts` | $0.00 | 0 | $0.00 |
| builder dex `para` | $0.00 | 0 | $0.00 |
| builder dex `vntl` | $0.00 | 0 | $0.00 |
| builder dex `xyz` | $231,694.13 | 2 | $1,350,269.64 |
| 現貨 spot | $4,454,006.65（含估算） | 3 幣 | — |
| **合計** | **$4,685,700.78** | **2** | — |

非原生（builder dex＋現貨）占比：**100.0%**（$4,685,700.78 / $4,685,700.78）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 4,405,791.3823 | $4,405,791.38 |
| USDT0 | 48,215.2509 | $48,215.25（估） |
| USDH | 0.01250805 | $0.01 |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $4,454,006.65 | $928,136.33 |
| week | $4,454,006.65 | $928,136.33 |
| month | $4,454,006.65 | $30,410,564.76 |
| allTime | $4,454,006.65 | $350,737,799.44 |
| perpDay | $231,691.93 | $928,136.33 |
| perpWeek | $231,691.93 | $928,136.33 |
| perpMonth | $231,691.93 | $30,410,564.76 |
| perpAllTime | $231,691.93 | $342,683,442.38 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| xyz | xyz:NVDA | long | 5x | $1,275,718.44 | $15,989.18 |
| xyz | xyz:GOOGL | long | 10x | $74,551.19 | $-925.43 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：2（回應共 2 筆，json 保留 2 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$1,330,000.00**
- 外部入金合計：$0.00
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | bridge_out | 2 | $1,330,000.00 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$1,330,000.00**，2 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-08-21T03:41:15.443000+00:00 | $500,000.00 | USDC | `0x2000000000000000000000000000000000000000` |
| 2026-07-30T06:41:51.269000+00:00 | $830,000.00 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-09-08T05:25:30.518000+00:00**（距今 0.81 天）
- 近 7 天成交：**268** 筆／近 30 天：**1059** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1791, 'native': 180, 'builder:para': 29}
- 主力幣：xyz:DRAM×318、xyz:GOOGL×281、xyz:INTC×224、xyz:NVDA×222、xyz:SMSN×198
- 目前持倉：2 個（原生 0／builder dex 2）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 10.01 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 1.8 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 6.71 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 10.01 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 6.71 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 8.08 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 10.01 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 39.85 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.91 | 72.71 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 1.8 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 2.59 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 1.8 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 6.19 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 5.99 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 39.85 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.90 | 20.97 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.89 | 1 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.89 | 6.72 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.89 | 2.59 |
| 2026-09-08T05:25:30.518000+00:00 | xyz:INTC | Close Long | 99.89 | 39.85 |

## 裁決

- 非原生資金 $4,685,700.78 占總資產 $4,685,700.78 的100%（builder dex $231,694.13／現貨 $4,454,006.65）
- 成交戰場分布：非原生 1820/2000 筆（91%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $1,330,000.00
- 跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）$1,330,000.00，占「現餘＋跨層轉移」22%（≥ 20% 門檻）→ 資本正離開交易場（跨層/減倉）

**裁決：同地址換戰場（builder dex/現貨）｜⚠️ 資本外移中**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

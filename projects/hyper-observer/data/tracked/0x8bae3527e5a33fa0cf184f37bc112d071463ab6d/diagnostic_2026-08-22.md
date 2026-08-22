# 全維度診斷探測 — 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

> 純唯讀診斷（2026-08-22，探測時間 2026-08-22T23:03:29.286827+00:00）。
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
| 原生永續 dex | $610,429.46 | 2 | $123,880.81 |
| builder dex `abcd` | $0.00 | 0 | $0.00 |
| builder dex `cash` | $0.00 | 0 | $0.00 |
| builder dex `flx` | $0.00 | 0 | $0.00 |
| builder dex `hyna` | $0.00 | 0 | $0.00 |
| builder dex `io` | $0.00 | 0 | $0.00 |
| builder dex `km` | $0.00 | 0 | $0.00 |
| builder dex `mkts` | $0.00 | 0 | $0.00 |
| builder dex `para` | $3,999.77 | 1 | $3,990.24 |
| builder dex `vntl` | $0.00 | 0 | $0.00 |
| builder dex `xyz` | $7,784.52 | 2 | $75,932.24 |
| 現貨 spot | $4,035,573.35（含估算） | 3 幣 | — |
| **合計** | **$4,657,787.10** | **5** | — |

非原生（builder dex＋現貨）占比：**86.9%**（$4,047,357.64 / $4,657,787.10）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 3,987,358.0903 | $3,987,358.09 |
| USDT0 | 48,215.2509 | $48,215.25（估） |
| USDH | 0.01250805 | $0.01 |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $4,035,564.19 | $3,430,172.79 |
| week | $4,035,564.19 | $17,334,271.00 |
| month | $4,035,564.19 | $52,606,214.01 |
| allTime | $4,035,564.19 | $344,534,769.66 |
| perpDay | $622,214.07 | $3,430,172.79 |
| perpWeek | $622,214.07 | $17,334,271.00 |
| perpMonth | $622,214.07 | $52,606,214.01 |
| perpAllTime | $622,214.07 | $336,480,412.60 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| （原生） | RSR | long | 3x | $109,893.00 | $15,622.04 |
| xyz | xyz:GOOGL | long | 10x | $75,778.39 | $301.77 |
| （原生） | kLUNC | long | 3x | $13,987.82 | $330.87 |
| para | para:UNITREE | long | 1x | $3,990.24 | $181.06 |
| xyz | xyz:SKHY | short | 10x | $153.85 | $4.71 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：3（回應共 3 筆，json 保留 3 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$2,130,000.00**
- 外部入金合計：$0.00
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | bridge_out | 3 | $2,130,000.00 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$2,130,000.00**，3 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-08-21T03:41:15.443000+00:00 | $500,000.00 | USDC | `0x2000000000000000000000000000000000000000` |
| 2026-07-30T06:41:51.269000+00:00 | $830,000.00 | USDC | `0x2000000000000000000000000000000000000000` |
| 2026-07-17T02:59:04.334000+00:00 | $800,000.00 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-08-22T07:59:11.569000+00:00**（距今 0.63 天）
- 近 7 天成交：**161** 筆／近 30 天：**2000** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1934, 'native': 64, 'builder:para': 2}
- 主力幣：xyz:GOOGL×459、xyz:META×386、xyz:DRAM×351、xyz:SMSN×320、xyz:SKHY×192
- 目前持倉：5 個（原生 2／builder dex 3）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-08-22T07:59:11.569000+00:00 | kLUNC | Close Long | 0.059832 | 28,900,394 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.63 | 5.34 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.63 | 3.79 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.63 | 0.23 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.64 | 3.66 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.65 | 2.64 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.65 | 143.85 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.65 | 1.32 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 2.65 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 1.32 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 43.74 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 5.87 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 0.36 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 61.11 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.66 | 50 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.67 | 1.14 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.67 | 0.77 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.67 | 2.3 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.67 | 23.16 |
| 2026-08-22T07:57:46.068000+00:00 | xyz:SKHY | Close Short | 163.68 | 2.65 |

## 裁決

- 非原生資金 $4,047,357.64 占總資產 $4,657,787.10 的87%（builder dex $11,784.29／現貨 $4,035,573.35）
- 成交戰場分布：非原生 1936/2000 筆（97%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $2,130,000.00
- 跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）$2,130,000.00，占「現餘＋跨層轉移」31%（≥ 20% 門檻）→ 資本正離開交易場（跨層/減倉）

**裁決：同地址換戰場（builder dex/現貨）｜⚠️ 資本外移中**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

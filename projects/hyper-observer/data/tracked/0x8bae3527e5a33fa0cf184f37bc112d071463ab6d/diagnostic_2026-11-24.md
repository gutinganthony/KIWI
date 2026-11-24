# 全維度診斷探測 — 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

> 純唯讀診斷（2026-11-24，探測時間 2026-11-24T06:30:55.447301+00:00）。
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
| 原生永續 dex | $2,316.83 | 1 | $6,291.33 |
| builder dex `abcd` | $0.00 | 0 | $0.00 |
| builder dex `cash` | $0.00 | 0 | $0.00 |
| builder dex `flx` | $0.00 | 0 | $0.00 |
| builder dex `hyna` | $0.00 | 0 | $0.00 |
| builder dex `io` | $0.00 | 0 | $0.00 |
| builder dex `km` | $0.00 | 0 | $0.00 |
| builder dex `mkts` | $0.00 | 0 | $0.00 |
| builder dex `para` | $0.00 | 0 | $0.00 |
| builder dex `vntl` | $0.00 | 0 | $0.00 |
| builder dex `xyz` | $0.00 | 0 | $0.00 |
| 現貨 spot | $3,199,401.16（含估算） | 3 幣 | — |
| **合計** | **$3,201,717.99** | **1** | — |

非原生（builder dex＋現貨）占比：**99.9%**（$3,199,401.16 / $3,201,717.99）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 3,151,185.9006 | $3,151,185.90 |
| USDT0 | 48,215.2509 | $48,215.25（估） |
| USDH | 0.01250805 | $0.01 |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $3,199,339.66 | $0.00 |
| week | $3,199,339.66 | $2,997,146.13 |
| month | $3,199,339.66 | $20,745,776.60 |
| allTime | $3,199,339.66 | $389,938,154.45 |
| perpDay | $2,310.29 | $0.00 |
| perpWeek | $2,310.29 | $2,997,146.13 |
| perpMonth | $2,310.29 | $20,745,776.60 |
| perpAllTime | $2,310.29 | $381,883,797.39 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| （原生） | APEX | long | 3x | $6,291.33 | $-2,131.07 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：2（回應共 2 筆，json 保留 2 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$1,800,000.00**
- 外部入金合計：$0.00
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | bridge_out | 2 | $1,800,000.00 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$1,800,000.00**，2 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-11-04T18:04:13.740000+00:00 | $900,000.00 | USDC | `0x2000000000000000000000000000000000000000` |
| 2026-11-03T05:12:40.095000+00:00 | $900,000.00 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-11-21T05:09:54.605000+00:00**（距今 3.06 天）
- 近 7 天成交：**478** 筆／近 30 天：**1366** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1402, 'native': 598}
- 主力幣：xyz:NVDA×746、DOGE×302、xyz:SKHY×291、xyz:SKHX×173、xyz:ORCL×123
- 目前持倉：1 個（原生 1／builder dex 0）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-11-21T05:09:54.605000+00:00 | xyz:NVDA | Close Long | 127.80 | 281.328 |
| 2026-11-21T05:09:54.605000+00:00 | xyz:NVDA | Close Long | 127.80 | 782.288 |
| 2026-11-21T05:09:54.605000+00:00 | xyz:NVDA | Close Long | 127.80 | 145.607 |
| 2026-11-21T05:09:54.477000+00:00 | xyz:NVDA | Close Long | 127.80 | 20 |
| 2026-11-21T05:09:54.184000+00:00 | xyz:NVDA | Close Long | 127.80 | 39.093 |
| 2026-11-21T05:09:54.055000+00:00 | xyz:NVDA | Close Long | 127.80 | 0.713 |
| 2026-11-21T05:09:54.055000+00:00 | xyz:NVDA | Close Long | 127.80 | 3.315 |
| 2026-11-21T05:09:53.915000+00:00 | xyz:NVDA | Close Long | 127.80 | 7.73 |
| 2026-11-21T05:09:53.915000+00:00 | xyz:NVDA | Close Long | 127.80 | 30.404 |
| 2026-11-21T05:09:53.915000+00:00 | xyz:NVDA | Close Long | 127.80 | 7.73 |
| 2026-11-21T05:09:53.915000+00:00 | xyz:NVDA | Close Long | 127.80 | 0.109 |
| 2026-11-21T05:09:53.792000+00:00 | xyz:NVDA | Close Long | 127.80 | 2.467 |
| 2026-11-21T05:09:53.725000+00:00 | xyz:NVDA | Close Long | 127.80 | 13.184 |
| 2026-11-21T05:09:53.725000+00:00 | xyz:NVDA | Close Long | 127.80 | 7.825 |
| 2026-11-21T05:09:53.725000+00:00 | xyz:NVDA | Close Long | 127.80 | 7.73 |
| 2026-11-21T05:09:53.725000+00:00 | xyz:NVDA | Close Long | 127.80 | 2.186 |
| 2026-11-21T05:09:53.614000+00:00 | xyz:NVDA | Close Long | 127.80 | 1.988 |
| 2026-11-21T05:09:53.522000+00:00 | xyz:NVDA | Close Long | 127.80 | 2.452 |
| 2026-11-21T05:09:53.433000+00:00 | xyz:NVDA | Close Long | 127.80 | 11.737 |
| 2026-11-21T05:09:53.433000+00:00 | xyz:NVDA | Close Long | 127.80 | 3.91 |

## 裁決

- 非原生資金 $3,199,401.16 占總資產 $3,201,717.99 的100%（builder dex $0.00／現貨 $3,199,401.16）
- 成交戰場分布：非原生 1402/2000 筆（70%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $1,800,000.00
- 跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）$1,800,000.00，占「現餘＋跨層轉移」36%（≥ 20% 門檻）→ 資本正離開交易場（跨層/減倉）

**裁決：同地址換戰場（builder dex/現貨）｜⚠️ 資本外移中**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

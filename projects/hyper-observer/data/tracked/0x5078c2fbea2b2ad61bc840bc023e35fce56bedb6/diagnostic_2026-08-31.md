# 全維度診斷探測 — 0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6

> 純唯讀診斷（2026-08-31，探測時間 2026-08-31T00:55:55.447384+00:00）。
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
| 原生永續 dex | $4,704.12 | 1 | $103,731.61 |
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
| 現貨 spot | $4,732.88（含估算） | 5 幣 | — |
| **合計** | **$9,437.00** | **1** | — |

非原生（builder dex＋現貨）占比：**50.1%**（$4,732.88 / $9,437.00）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 4,724.0697 | $4,724.07 |
| FARM | 0.8 | $4.69（估） |
| VAPOR | 816 | $3.58（估） |
| HYPE | 0.01439447 | $0.54（估） |
| MAX | 2,908.3048 | $0.00（估） |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $4,725.33 | $0.00 |
| week | $4,725.33 | $103,204.61 |
| month | $4,725.33 | $937,937.90 |
| allTime | $4,725.33 | $18,940,102,411.74 |
| perpDay | $4,724.07 | $0.00 |
| perpWeek | $4,724.07 | $103,204.61 |
| perpMonth | $4,724.07 | $937,937.90 |
| perpAllTime | $4,724.07 | $18,932,094,824.37 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| （原生） | BTC | short | 20x | $103,731.61 | $-526.97 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：6（回應共 6 筆，json 保留 6 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$4,457.57**
- 外部入金合計：$10,994.83
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | mixed | 4 | $9,684.36 |
| rewardsClaim | in | 2 | $5,768.03 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$4,457.57**，1 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-08-27T12:35:48.352000+00:00 | $4,457.57 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-08-29T09:13:20.864000+00:00**（距今 1.65 天）
- 近 7 天成交：**6** 筆／近 30 天：**86** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1211, 'native': 784, 'spot': 5}
- 主力幣：xyz:SP500×1118、BTC×770、xyz:GOLD×66、xyz:SPCX×27、SOL×9
- 目前持倉：1 個（原生 1／builder dex 0）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-08-29T09:13:20.864000+00:00 | BTC | Open Short | 77,589.00 | 0.06366 |
| 2026-08-29T09:13:13.401000+00:00 | BTC | Open Short | 77,593.00 | 0.32103 |
| 2026-08-29T09:13:13.401000+00:00 | BTC | Open Short | 77,593.00 | 0.00015 |
| 2026-08-29T09:13:13.401000+00:00 | BTC | Open Short | 77,593.00 | 0.0002 |
| 2026-08-29T09:13:13.401000+00:00 | BTC | Open Short | 77,593.00 | 0.00077 |
| 2026-08-29T09:13:13.401000+00:00 | BTC | Open Short | 77,593.00 | 0.94427 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,692.90 | 3.206 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,692.90 | 0.202 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,692.90 | 0.301 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,692.90 | 3.255 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.00 | 0.649 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.00 | 0.197 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.00 | 0.022 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.00 | 0.619 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.00 | 2 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.10 | 0.006 |
| 2026-08-04T15:13:51.918000+00:00 | xyz:SP500 | Close Short | 7,693.10 | 1.374 |
| 2026-08-04T14:18:06.916000+00:00 | xyz:SP500 | Close Short | 7,673.90 | 2.957 |
| 2026-08-04T14:01:18.982000+00:00 | xyz:SP500 | Close Short | 7,654.70 | 3.696 |
| 2026-08-04T13:30:33.965000+00:00 | xyz:SP500 | Close Short | 7,633.20 | 4.62 |

## 裁決

- 非原生資金 $4,732.88 占總資產 $9,437.00 的50%（builder dex $0.00／現貨 $4,732.88）
- 成交戰場分布：非原生 1216/2000 筆（61%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $4,457.57
- 跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）$4,457.57，占「現餘＋跨層轉移」32%（≥ 20% 門檻）→ 資本正離開交易場（跨層/減倉）

**裁決：同地址換戰場（builder dex/現貨）｜⚠️ 資本外移中**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

# 全維度診斷探測 — 0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6

> 純唯讀診斷（2026-09-04，探測時間 2026-09-04T00:30:37.539476+00:00）。
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
| 原生永續 dex | $1,683.34 | 2 | $51,732.53 |
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
| 現貨 spot | $1,789.30（含估算） | 5 幣 | — |
| **合計** | **$3,472.64** | **2** | — |

非原生（builder dex＋現貨）占比：**51.5%**（$1,789.30 / $3,472.64）

現貨非零餘額（估值：USDC 類 1:1；其他 token 用 entryNtl 成本基礎粗估）：

| 幣 | 數量 | USD |
|---|---:|---:|
| USDC | 1,780.4931 | $1,780.49 |
| FARM | 0.8 | $4.69（估） |
| VAPOR | 816 | $3.58（估） |
| HYPE | 0.01439447 | $0.54（估） |
| MAX | 2,908.3048 | $0.00（估） |

portfolio 各視窗最新帳戶淨值（與 clearinghouseState 對照）：

| 視窗 | accountValue | vlm |
|---|---:|---:|
| day | $1,782.91 | $51,268.76 |
| week | $1,782.91 | $548,705.17 |
| month | $1,782.91 | $548,705.17 |
| allTime | $1,782.91 | $18,940,547,912.30 |
| perpDay | $1,684.40 | $51,268.76 |
| perpWeek | $1,684.40 | $548,705.17 |
| perpMonth | $1,684.40 | $548,705.17 |
| perpAllTime | $1,684.40 | $18,932,540,324.93 |

> portfolio 的 accountValue 含全部場所（原生＋builder＋現貨），perp* 視窗只含永續——兩者差額即「不在原生永續」的部分。

全部未平倉部位（含 builder dex）：

| dex | 幣 | 方向 | 槓桿 | 名目(USD) | 未實現PnL |
|---|---|---|---:|---:|---:|
| （原生） | BTC | long | 40x | $49,782.07 | $501.44 |
| （原生） | CASHCAT | long | 3x | $1,950.45 | $-37.75 |

## (b) 有沒有轉出到其他地址？（近 45 天非資金費帳變動）

- 視窗內帳變動筆數：10（回應共 10 筆，json 保留 10 筆）
- 外轉合計（withdraw／轉他址／進 vault）：**$0.00**
- 跨層轉移合計（HyperCore→HyperEVM，同一地址擁有者，非第三方）：**$4,457.57**
- 外部入金合計：$12,193.57
- 同地址內部轉移（perp↔spot accountClassTransfer）：**$0.00**
- 無法分類的帳變動：**$0.00**

| type | 方向 | 筆數 | USD |
|---|---|---:|---:|
| send | mixed | 4 | $9,684.36 |
| rewardsClaim | in | 6 | $6,966.77 |

查無 withdraw／轉到第三方地址／vault 存入紀錄——但這**不等於沒有資金移動**，見下方跨層轉移／無法分類項。

### 跨層轉移（HyperCore→HyperEVM，同一擁有者）：**$4,457.57**，1 筆

> destination 是 Hyperliquid 的 spot token **系統地址**（第一個 byte 0x20、末端 big-endian 編 token index；HYPE 為 0x2222…2222），款項進入**同一位擁有者在 HyperEVM 上的同一地址**，不是轉給第三方。
> 資金仍屬同一擁有者控制，但**已離開 HyperCore 交易帳戶**（不再作為永續/現貨交易的抵押品）。
> 來源：https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers

| 時間(UTC) | USD | token | destination（系統地址） |
|---|---:|---|---|
| 2026-08-27T12:35:48.352000+00:00 | $4,457.57 | USDC | `0x2000000000000000000000000000000000000000` |

## (c) 是否仍在交易？

- 最後成交時間：**2026-09-03T19:50:10.925000+00:00**（距今 0.19 天）
- 近 7 天成交：**50** 筆／近 30 天：**50** 筆（回應共 2000 筆，已達 API 截斷上限）
- 成交戰場分布：{'builder:xyz': 1211, 'native': 785, 'spot': 4}
- 主力幣：xyz:SP500×1118、BTC×758、xyz:GOLD×66、xyz:SPCX×27、CASHCAT×13
- 目前持倉：2 個（原生 2／builder dex 0）

最後 20 筆成交：

| 時間(UTC) | 幣 | 動作 | px | sz |
|---|---|---|---:|---:|
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30426 | 492 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30427 | 328 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30432 | 65 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30432 | 869 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30434 | 869 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30473 | 370 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30484 | 271 |
| 2026-09-03T19:50:10.925000+00:00 | CASHCAT | Open Long | 0.30485 | 296 |
| 2026-09-03T15:03:57.092000+00:00 | CASHCAT | Open Long | 0.27194 | 460 |
| 2026-09-03T15:03:57.092000+00:00 | CASHCAT | Open Long | 0.27248 | 443 |
| 2026-09-03T15:03:57.092000+00:00 | CASHCAT | Open Long | 0.27248 | 443 |
| 2026-09-03T15:03:57.092000+00:00 | CASHCAT | Open Long | 0.27248 | 1,535 |
| 2026-09-03T14:59:12.511000+00:00 | CASHCAT | Open Long | 0.27439 | 436 |
| 2026-09-03T14:58:30.805000+00:00 | BTC | Open Long | 80,293.00 | 0.02851 |
| 2026-09-03T14:58:30.805000+00:00 | BTC | Open Long | 80,293.00 | 0.115 |
| 2026-09-03T14:58:30.805000+00:00 | BTC | Open Long | 80,293.00 | 0.415 |
| 2026-09-03T14:58:30.805000+00:00 | BTC | Open Long | 80,293.00 | 0.05525 |
| 2026-09-01T18:37:07.474000+00:00 | BTC | Close Long | 76,734.00 | 1.1911 |
| 2026-09-01T18:27:43.925000+00:00 | BTC | Close Long | 76,963.00 | 0.12672 |
| 2026-09-01T18:27:43.925000+00:00 | BTC | Close Long | 76,963.00 | 0.05197 |

## 裁決

- 非原生資金 $1,789.30 占總資產 $3,472.64 的52%（builder dex $0.00／現貨 $1,789.30）
- 成交戰場分布：非原生 1215/2000 筆（61%）
- 近 45 天帳變動離場訊號：跨層轉移（HyperCore→HyperEVM，同一擁有者） $4,457.57
- 跨層轉移（HyperCore→HyperEVM，同一地址擁有者，非第三方）$4,457.57，占「現餘＋跨層轉移」56%（≥ 20% 門檻）→ 資本正離開交易場（跨層/減倉）

**裁決：同地址換戰場（builder dex/現貨）｜⚠️ 資本外移中**

> 純唯讀觀察，不執行任何交易；不構成投資建議。

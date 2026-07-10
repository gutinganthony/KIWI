---
title: 跟單聰明錢觀察器 — Polymarket + Hyperliquid 跨平台實證結論（唯讀）
url: local
date_added: 2026-07-10
last_updated: 2026-07-10
topic: business
tags: [copy-trading, smart-money, polymarket, hyperliquid, prediction-markets, perps, on-chain, wallet-tracking, read-only, due-diligence, quant]
version: 1.0
related: [./2026-07-10-polymarket-copy-trading-guide-verification.md]
---

> 承接〈Polymarket跟單指南查證〉。為回答「聰明錢錢包存不存在、值不值得跟」，建了兩個純唯讀、CI 驅動的鏈上觀察器（`projects/poly-observer/`、`projects/hyper-observer/`），用真實公開 API 掃錢包、分類、模擬跟單成本。本檔記錄跨平台實證結論。**兩個工具皆純唯讀：不含任何下單、簽章、私鑰、錢包連線程式碼。**

---

## 0. 一句話結論

**在兩個平台上，排行榜頂端都找不到「可跟的」聰明錢**——榜首結構性地由三種「你無法複製的東西」組成：高槓桿爆倉賭徒、做市商、刷量戶。排行榜的排序邏輯（比 PnL／比交易量）正好篩選出這些不可跟的特徵。真正可跟的對象（中等規模、中頻、方向性、低槓桿、撐過回撤）不在榜上，需要換一套搜尋方法才找得到。

---

## 1. 工具架構（兩平台共用骨架）

`fetch`（公開 API 抓錢包宇宙＋逐錢包完整數據）→ `classify`（分類器：存在性檢驗）→ `track_wallet`（逐日 dossier＋新建倉偵測）→ `simulate_copy`（跟單成本模擬，僅 Polymarket 版）。跑在 GitHub Actions（雲端 session egress 被擋，但 Actions runner 無限制），每日排程＋push 觸發，結果 commit 回分支。每個錢包用一個「已知結局的反例」做 ground-truth 自我校驗。

## 2. Polymarket 實證（`poly-observer`）

- **API**：leaderboard 已搬到 `data-api.polymarket.com/v1/leaderboard`（舊 lb-api 退役）；逐錢包 activity/positions/value + user-pnl 曲線。
- **存在性**：60 錢包宇宙中僅 1–3 個「持續贏家」，且**全部高頻**（730–1,344 筆/月）。高 PnL 與高頻在 Polymarket 綁在一起。
- **範例錢包 0x2005d16a（+$11M）**：真實頂尖運動博彩戶，但 ~114 筆/小時（每 31 秒一單）→ 散戶延遲下無法跟。
- **模擬器誠實性教訓**（重要資料陷阱）：Polymarket **輸的部位不產生 REDEEM 事件**（只有贏了領獎才有）→ 用交易流重建 PnL 會系統性只看到贏家、造出 300%+ ROI／100% 勝率的假獲利；加上高頻錢包 activity 1500 筆上限只涵蓋約 12 小時、「只結算無買入」的幽靈市場把前期獲利當純利。修正：只算完整 round-trip，截斷+短窗+結算全贏家時**工具明白拒答**（不印假數字）。唯一可信 PnL 來源是 user-pnl 曲線。

## 3. Hyperliquid 實證（`hyper-observer`）

- **API**：`POST api.hyperliquid.xyz/info`（免金鑰），clearinghouseState（持倉/槓桿/強平價/未實現PnL/資金費）＋portfolio（PnL 曲線）＋userFills（含**輸贏皆有** closedPnl，無 Polymarket 的贏家倖存者偏誤）＋userFunding；宇宙來自未文件化 `stats-data.hyperliquid.xyz/Mainnet/leaderboard`（實測可用）。
- **修正後分類分布（top-60 leaderboard）**：blowup_risk 31、wash_suspect 24、one_hit 1、choppy 4、**consistent_winner 0**。裁決：未發現。
- **最接近「贏家」的錢包 0x5b5d5120（+$181M、profit factor 13）**：卻是 20x 槓桿 HFT，曾從 +$32M 一路虧到 −$78M（100% 回撤）再翻回 +$181M → 跟它早被強平／嚇出場，判 choppy 不可跟。
- **分類器誠實化（修了 6 個指標偏誤才可信）**：回撤/崩跌除法爆量（早期小峰值→深負算出 78028% 假回撤）加 min_peak 閘＋封頂；做市商（$4.5B 量、量/PnL 163）用 vlm/PnL 判據攔進 wash；截斷 fills 的 profit_factor 不當硬否決；缺曲線判 insufficient；**強平「次數」取代「有無」**（≥3 次才強制 blowup——Wynn 592 次仍判 blowup，單次強平的大額淨正戶走正常分類並揭露風險）。ground-truth：James Wynn `0x5078c2fb...`（592 次強平、$100M→巨虧）正確判 blowup。

## 4. 跨平台結論：為什麼排行榜找不到可跟的錢包

| 榜上主體 | 為何不可跟 |
|---|---|
| 高槓桿爆倉賭徒（HL blowup 31／Wynn 型） | 高勝率是賣波動率/馬丁格爾假象，一次強平歸零；跟它＝跟到爆倉 |
| 做市商（HL wash 24／Poly $11M 亦近似） | 賺的是價差/做市，你鏡像下單＝站到它的對手方，吃不到 edge |
| 刷量戶（HL 空投對敲） | 巨量、PnL≈0、無淨方向，根本沒有可跟的方向性訊號 |
| 高頻方向戶（Poly 全部贏家、HL HFT） | 每分鐘數單，散戶偵測+執行延遲下永遠買在更差價、拿逆選擇的殘羹 |

**排序即篩選**：leaderboard 比 PnL/量，天然把「規模大、槓桿高、頻率高、做市」推到頂端——這四者全是不可跟的特徵。可跟的錢包（中頻方向性、低槓桿、撐過回撤、仍活躍）在榜單中段甚至榜外。

## 5. 自建即時下單 bot 能否解決延遲？（部分能，關鍵不能）

延遲三段：偵測（得知贏家開倉）／決策簽章／執行。自建 bot 能把後兩段壓到毫秒，但**無法修「你永遠在贏家之後行動」的偵測段**——跟單本質是反應式，你不可能比被跟的人快。是否致命取決於**持倉時間**：低頻方向戶（抱數日）延遲幾分鐘無所謂，bot 可行；高頻/做市（抱秒級）延遲 1–2 秒就 edge 全失。故：**bot 是必要非充分——先有一個「持倉夠長、可跟」的標的，bot 才有意義。**

## 6. 廣域掃描結果（2026-07-10 執行，v1.1 新增）

換獵場實測：從排行榜原始回應的 **40,381 個錢包全量**過濾「可跟畫像」（全期 PnL≥$2M、本月本週仍在賺、量/PnL∈[1,30] 排除做市與 vault、ROI≥1、帳戶 $20k–$20M）→ **120 個候選**深驗（每錢包 4 端點、修正後分類器）：

- 分布：blowup_risk 41、choppy 12、wash_suspect 3、one_hit 3、**consistent_winner 3**
- **可跟性判定（頻率≤150筆/30日、持倉≥12h、槓桿≤10x）：3 個贏家全數不過——followable 0 個**
- 最接近可跟的 `0x8bae3527e5…`：+$9.28M、回撤僅 5.6%、profit factor 14、槓桿 3x、零強平、平均持倉 250 小時（10 天）——唯一不過的是 30 日 1,080 筆 fills。**已知限制**：fills≠決策次數（一張單在薄簿會拆成多筆 fill；持倉 10 天與高 fills 並存暗示分批執行），精細判定需把 fills 聚合成「部位事件」再算真實決策頻率——列為後續複核項。

## 7. 影子跟單 bot 實測（2026-07-10 首班，v1.1 新增）

對 Polymarket $11M 高頻運動錢包實跑 15 分鐘（51 筆、零故障）：偵測延遲 median 17.7s/p90 27s（輪詢上界）；**BUY 進場劣化 median +2.2%、p90 +11.1%**；**第一檔深度 median 僅 $199**（$50 小單 43% 擠不進第一檔）。結論：bot 工程可行；該錢包確定不可跟（劣化＋容量雙殺）。bot 每日三班持續累積，留待對準未來找到的可跟標的。

## 8. 總結與下一步（v1.1 更新）

**兩平台、三種宇宙（Poly 榜首／HL 榜首／HL 全量可跟畫像過濾）全部掃完：至今 0 個通過「持續贏家＋可跟」雙門檻的錢包。** 洞見不變且更強：鏈上頂級獲利者的 edge 形態（高頻、做市、高槓桿）與「可被散戶複製」本質互斥。殘餘待驗：(a) fills 聚合後 0x8bae35 型「分批執行的長持倉戶」是否翻案；(b) 觀察器逐日累積的前瞻數據。**在出現通過全部證據閘門的標的之前，投入真錢跟單無實證基礎——此為本調查的操作性結論。**

## Update Log
- 2026-07-10 v1.0：初版。兩個唯讀觀察器建置＋跨平台實證：兩平台 leaderboard 頂端皆 0 個可跟贏家；記錄模擬器/分類器的誠實化教訓（贏家倖存者偏誤、除法爆量、做市商辨識、強平計數）。

# Polymarket 錢包跟單（Copy Trading）散戶可行性研究

研究日期：2026-07-10 ｜ 方法：WebSearch 多輪交叉檢索（WebFetch 對多數目標站被 gateway 403，全文核對受限，見文末「工具限制」）
每項標註【有實證】＝有公開數據/事件可查；【推理】＝由已知事實推導；【vendor】＝跟單工具商自報數據，有利益衝突。

## 結論（先行）

跟單 Polymarket 在機制上完全可行（API 公開、工具成熟），但在經濟上對小本金散戶是「近零和扣手續費」的遊戲：
未經過濾的天真跟單是明確負期望；最嚴格紀律執行下，可信的上緣約 +2~5%/月。「月賺 $50k」需要 50 萬至 250 萬美元
本金＋持續頂尖 edge＋深度流動性三者同時成立，對 $1k-$10k 本金的散戶實質機率趨近於零。且台灣自 2026 年已被
Polymarket 列為 close-only（只能平倉、不能開新倉），這篇教學的前提對台灣使用者根本不成立。

---

## 1. 機制面：跟單途徑盤點

### 1.1 Polymarket 官方：沒有內建跟單功能【有實證】
- 截至 2026 年中，Polymarket 主站/app 沒有官方 copy trading 功能；所有跟單都是第三方非託管工具讀鏈上交易再用你的錢包鏡像下單。
  - https://www.newspoly.net/blog/does-polymarket-have-an-app （2026-03 時點確認無官方功能）
  - 官方 Substack《The Oracle》曾以 "COPYCAT" 專文報導第三方 Stand.trade 的跟單/反向跟單功能（2 個月內追蹤 1,500+ 錢包、5,000+ 策略）——官方「報導」但非官方「產品」：https://news.polymarket.com/p/copycat 、https://news.polymarket.com/p/copytrade-wars

### 1.2 CLOB API：公開、可程式化下單【有實證】
- CLOB API（clob.polymarket.com，Polygon chain 137）完全公開，官方 Python client `py-clob-client` 開源，支援下單/撤單/市場數據，L1/L2 header 認證。自建跟單 bot 技術上無門檻。
  - https://github.com/Polymarket/py-clob-client ｜ https://docs.polymarket.com/trading/overview ｜ https://pypi.org/project/py-clob-client/

### 1.3 第三方跟單工具（2026 年生態）【有實證】
- Telegram bots：PolyGun（每筆 1% 費）、Kreo（fee-on-trade，同類工具 0.5-1.5%/筆）、PolyBot、PolyDex_bot、Polycule。
  - https://telegramtrading.net/polygun-review-telegram-copy-trading-bot/ ｜ https://coincodecap.com/kreo-review-polymarket-kalshi-copy-trading-bot ｜ https://polymart.app/blog/best-polymarket-telegram-bots
- Web 平台：Stand.trade（跟單＋反向跟單終端）、Polycopy、Poly Syncer（2026-05 上線）、PolyHermes、polycop.fun。
  - https://polymart.app/stand-trade ｜ https://polycopy.app/ ｜ https://www.polysyncer.com/
- **安全事故**：Polycule 2026-01 被駭，約 $230,000 用戶資金失竊（Telegram bot 託管風險）。
  - https://news.dropstab.com/research/polymarket-telegram-bot

### 1.4 開源腳本：GitHub 上大量是惡意軟體誘餌【有實證】
- 合法日本 DeFi 專案 dev-protocol 的 GitHub org 被劫持，散佈假 Polymarket bot（精美 README＋數百星），npm 依賴中藏私鑰竊取器：https://www.stepsecurity.io/blog/malicious-polymarket-bot-hides-in-hijacked-dev-protocol-github-org-and-steals-wallet-keys
- 2026-07-01 SlowMist 揭露假 arbitrage bot repo（53 forks），依賴 `clob-client-math` 於 npm install 時竊取私鑰明文外傳；歸因北韓「Contagious Trader」行動，30+ 惡意 npm 套件：https://safedep.io/defi-infostealer-fake-arbitrage-bot-npm/ ｜ https://www.cryptopolitan.com/defi-polymarket-users-targeted-npm-package/
- 搜尋結果中大量名稱怪異的 "Polymarket-Copy-Trade" repo（隨機人名帳號＋行銷文案 README）符合上述誘餌模式【推理】。**任何要你貼私鑰的開源 bot 都應視為敵意。**

## 2. 結構性風險逐項評估

### (a) 延遲與滑點【有實證】
- 多數長尾市場總成交量 <$10K；$12K 市價單可推動價格 5-10 美分。旗艦市場（大選、超級盃）才能吸收 $50-100K。
  - https://polybacktest.com/limit-order-book-shape-polymarket ｜ https://www.alphascope.app/blog/polymarket-order-book-explained
- Polymarket crypto 訂單簿比 Deribit 單一 BTC strike 薄 20-40 倍；5 分鐘/15 分鐘 crypto 市場，幾美分滑點即殺死跟單策略。
  - https://polybacktest.com/limit-order-book-shape-polymarket ｜ https://startpolymarket.com/strategies/copy-trading/
- 跟單教學文自己承認滑點吃掉每筆 2-3%：https://startpolymarket.com/strategies/copy-trading/ ｜ https://ratio.you/blog/copy-trading-mistakes-draining-polymarket-bankroll

### (b) 逆選擇：你的成交價永遠比原單差【推理，多來源一致】
- 你看到鯨魚下單時，價格已因該單移動；若鯨魚的 edge 是資訊（如 20 分鐘後的民調），價格在你進場前已反映。跟單者結構上買在調整後、賣在調整後。
  - https://startpolymarket.com/strategies/copy-trading/ ｜ https://www.quantvps.com/blog/polymarket-copy-trading-bot

### (c) 成為退出流動性【手法有多來源記載；未找到具名可驗證個案】
- 記載的手法：一個錢包公開建立戰績→吸引跟單者→大單引跟單資金推價→向跟單者需求出貨；或乾脆用第二錢包反向收割。精明交易者知道自己被盯，公開錢包不是完整部位。
  - https://startpolymarket.com/strategies/copy-trading/ ｜ https://www.alphascope.app/blog/polymarket-copy-trading
- **Merge 陷阱**：同時持 YES+NO 合併成 USDC 出場，活動流上不顯示為賣出，多數跟單 app 不標記——你會漏掉離場訊號。
  - https://ratio.you/blog/copy-trading-mistakes-draining-polymarket-bankroll
- Stand.trade 內建「counter trading（反向跟單）」功能，等於生態系公開承認「跟單流本身是可收割的訊號」：https://news.polymarket.com/p/copycat
- 誠實標註：以上是業內公認手法描述（多個獨立來源），但我未能找到「某具名錢包被證實收割跟單者」的可驗證個案——歸類為結構性風險而非已判決事實。

### (d) 高勝率假象【有實證】
- Hubble AI 追蹤 90,000 錢包：排行榜是倖存者偏差，「高勝率」策略統計上注定失血歸零：https://x.com/MeetHubble/status/2010938884289675481
- 實例：某帳號 6,615 筆交易 98% 勝率——全是在 97¢ 附近賣尾部（15 分鐘 BTC/ETH up-down 市場），一次錯誤結算抹掉一個月獲利：https://tradoxvps.com/how-to-win-on-polymarket-in-2026-the-strategic-edge-guide/
- 母體統計：5 萬錢包中 92.4% 不賺錢；99.49% 錢包終生獲利不到 $1,000；80% 參與者長期虧損。
  - https://tradoxvps.com/how-to-win-on-polymarket-in-2026-the-strategic-edge-guide/ ｜ https://praveenax.medium.com/devs-are-making-10k-200k-a-month-on-polymarket-b55d29c32ed1 ｜ https://tradesignal.se/polymarket/strategies/how-polymarket-works
- 推論：用「勝率」選跟單對象，會系統性選到尾部賣家與做市 bot，正是爆倉前最漂亮的那種帳號。做市單的本質是逆選擇——掛單最容易成交的時刻正是價格對你不利的時刻。

### (e) 單一事件內幕錢包不可持續【有實證】
- 2025-10 諾貝爾和平獎案：帳號 "dirtycup"（開戶 <10 天）賽前數小時押 $68,340 於 Machado（賠率 3.6%），結算贖回 $80,000；帳號 "6741" 專為此市場開戶，$29,000 → 獲利 $53,500。挪威諾貝爾研究所啟動調查。
  - https://www.forbes.com/sites/brandonkochkodin/2025/10/10/did-the-nobel-peace-prize-expose-insider-trading-on-prediction-market-polymarket/ ｜ https://decrypt.co/343840/nobel-peace-prize-organizers-intestigating-polymarket-insider-trades ｜ https://protos.com/polymarket-traders-accused-of-insider-trading-nobel-peace-prize/
- 對跟單的含義【推理】：內幕錢包是「新錢包＋單一事件＋一次性」，事後才可辨識，不可能事前跟到；教學文拿這種案例當「可複製收益」是倖存者敘事。

## 3. 實證：公開可驗證的獲利/虧損案例

**正面（皆為 vendor 自報，有利益衝突）：**
- Polycopy 回測 687K+ 筆已結算交易：Copy Score 70+ 過濾後勝率 67.7%、平均每筆 P&L +5.76%；**未過濾的跟單約等於擲硬幣**：https://polycopy.app/polymarket-trading-strategies
- Polyloly「insider tail」策略回測：原始 ROI +46.7%，計入 3¢ 滑點與 10 個百分點勝率回歸後，實際約 +15~25%（回測期，非月報酬）：https://polyloly.com/blog/polymarket-insider-tail-backtest-46-percent-roi
- **未找到任何獨立、可驗證、超過 6 個月的散戶跟單獲利帳戶公開紀錄。**

**反面：**
- Polycule 被駭 $230K（2026-01）；GitHub/npm 假 bot 竊私鑰多起（見 §1.4）。
- 母體統計 92.4% 錢包不賺錢（§2d）。
- Reddit r/Polymarket 具體跟單虧損討論串：多次檢索未命中（搜尋為 US-only 索引，可能是檢索限制而非不存在）——標記為**證據缺口**。

## 4. 現實期望值推導（本題核心）

前提事實：Polymarket 無槓桿、無保證金，現貨 USDC，最大虧損=本金（margin 僅在申請中，2026-07-09 Bloomberg 報導：https://www.bloomberg.com/news/articles/2026-07-09/polymarket-seeks-license-to-offer-margin-trading-legally-in-us）。平台本身零交易費，成本=價差＋滑點＋bot 費。

**每筆成本疊加：** 滑點 2-3% ＋ bot 費 0.5-1.5% ≈ **每筆 3-4.5% 摩擦成本**。

**情境 A：天真跟單（跟排行榜/KOL 推的錢包，不過濾）**
勝率≈擲硬幣（Polycopy 自己的數據），每筆期望 ≈ 0% − 3~4.5% 摩擦 = **明確負期望**。
月交易 20-40 筆、每筆用 10-20% 本金 → 月報酬期望約 **-8% ~ -20%**。

**情境 B：紀律執行（嚴格過濾、只跟深流動性市場、小單、限價）**
取 vendor 回測上緣 +15~25%/回測期，扣 vendor 樂觀偏誤與費用，換算月報酬合理上緣 **+2~5%/月**【推理換算，回測期長度未揭露】。

**具體數字：**
- **$1,000 本金**：合理月區間 **-$200 ~ +$80**；中心值偏零至微負（-$30 ~ +$30）；紀律執行最好 +$20~50/月。
- **$10,000 本金**：合理月區間 **-$2,000 ~ +$800**；紀律執行最好 +$200~500/月。

**「月賺 $50,000」需要什麼前提：**
1. 本金：+5%/月（已是英雄假設）→ 需 **$1,000,000** 部署；+2%/月 → $2.5M；即使奇蹟式 +10%/月 → $500K。無槓桿可用，本金無法用 margin 縮小。
2. 流動性牆：$500K+ 的跟單部位必須塞進「$12K 就推價 5-10¢」的訂單簿；規模越大滑點越高，策略自我毀滅——只有少數旗艦市場容得下，而那些市場最有效率、edge 最薄。
3. 或者：一次性內幕/運氣事件（如諾貝爾案 $29K→+$53.5K）——不可複製、不可事前跟到。
4. 被跟錢包必須持續免費分享 alpha 且永不反向收割。
→ 四個條件同時成立的機率，對散戶而言可視為零。$50k/月敘事的實際功能是行銷漏斗（導流到抽 1%/筆的 bot 或 referral），與「99.49% 錢包終生獲利 <$1,000」的母體數據直接矛盾。

## 5. 台灣使用者面向

- **Taiwan (TW) 在 Polymarket 地理限制名單上，狀態為 close-only**：只能平倉既有部位，不能開新倉；IP geoblock 執行。多來源一致（截至 2026）：
  - https://help.polymarket.com/en/articles/13364163-geographic-restrictions ｜ https://docs.polymarket.com/api-reference/geoblock ｜ https://www.datawallet.com/crypto/polymarket-restricted-countries ｜ https://laikalabs.ai/prediction-markets/polymarket-supported-restricted-countries
- **KYC**：非限制區一般仍可無 KYC 交易；但高額用戶（七位數部位）實質被強制驗證；美國合法通道（QCEX）需完整 KYC。用 VPN 繞 geoblock＝違反 ToS，資金凍結風險，且過不了驗證。
  - https://www.copytradeinsider.com/blog/polymarket-kyc-requirements/ ｜ https://crypto.news/polymarket-says-no-mandatory-kyc-planned-for-main-prediction-market/
- **出入金**：USDC on Polygon；台灣需經交易所購 USDC 再跨鏈，技術可行，但入口已被 geoblock 封死。
- **法律備註（非法律意見）**：台灣無預測市場專法，此類以金錢對賭事件結果的行為可能落入刑法賭博罪章相關條文的灰區；平台本身又明示限制台灣——**雙重灰區**，做任何操作前應自行評估。
- **淨結論**：對台灣散戶，該教學的第一步（開新倉）在 2026 年已不可合規執行。

## 6. 總評

| 問題 | 判定 |
|---|---|
| 機制上可行嗎 | 可行（API 公開、工具多）【有實證】 |
| 天真跟單期望值 | 負（摩擦 3-4.5%/筆 vs 擲硬幣勝率）【實證+推理】 |
| 最好情況月報酬 | +2~5%（vendor 回測上緣換算）【推理】 |
| $1k/$10k 本金月損益 | -$200~+$80 / -$2,000~+$800【推理，依據實證參數】 |
| 月賺 $50k 前提 | $0.5M-$2.5M 本金＋頂尖 edge＋流動性奇蹟，或一次性內幕運氣【推理】 |
| 台灣可用性 | close-only，合規上做不到【有實證】 |
| 散戶照做月賺 $50k 機率 | 趨近於零 |

## 附註：本次研究工具限制（供主對話回寫 mac-manual-homework 待辦）
- WebFetch 被 gateway 403 的站點：startpolymarket.com、news.polymarket.com、docs.polymarket.com、help.polymarket.com、medium.com、datawallet.com、alphascope.app、quantvps.com、ratio.you、polyloly.com、polycopy.app、polymarket101.com、tradoxvps.com；agent proxy 亦拒絕 CONNECT 至 polymarket.com / data-api.polymarket.com。
- 影響：本文引文多來自 WebSearch 的摘要層，未能逐篇全文核對；關鍵數字（92.4%、67.7%、+5.76%、$12K→5-10¢）均有至少一個獨立來源交叉出現，但仍建議 Mac 端人工抽查 2-3 個來源全文。

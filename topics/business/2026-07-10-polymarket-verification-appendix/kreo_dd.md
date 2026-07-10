# 盡職調查：KreoPolyBot（Kreo）＋ polymarketanalytics.com
日期：2026-07-10。方法：僅公開資訊（WebSearch 取證）。**注意**：本 session 的 agent proxy 對 t.me、kreopoly.app、polymarketanalytics.com、polymarket.com、coincodecap.com 等網域的 CONNECT 一律回 403（policy denial），所有直接 WebFetch/curl 皆失敗，證據全部來自搜尋結果引文＋來源 URL。頁面級驗證（t.me 預覽、traders 篩選器截圖、pricing 頁）需在 Mac 手動補做。

---

## 對象 A：KreoPolyBot（Kreo）

### 基本身分
- 產品名 Kreo，Telegram bot 為 @KreoPolyBot，web 版 enter.kreo.app，官方文件 docs.kreo.app，官方 X 帳號 @kreoapp（多個獨立來源一致指認）。
  - https://enter.kreo.app/ ・ https://docs.kreo.app/ ・ https://x.com/kreoapp
  - https://polymart.app/kreo ・ https://www.ai-polymarket.com/kreo/
- **注意生態混亂**：kreopoly.app、polymarketcrypto.us、polymarket-tradingbot.co.uk 等多個「介紹站/docs 站」外觀像官方，實為 SEO/聯盟行銷站（內容互抄、皆導流至 bot）。官方 X 帳號頁面自己也警告「beware of scammers」。

### 誰營運
- **匿名團隊**。多篇評測明言「built by a team that has not published detailed public information about its founders or company structure」。查無公司登記、查無具名創辦人。
  - https://coincodecap.com/kreo-review-polymarket-kalshi-copy-trading-bot ・ https://www.mexc.com/news/1066685
- 是 Polymarket「Builders Program」（2025-11 啟動）生態內的第三方開發者，非 Polymarket 官方產品。
  - https://unchainedcrypto.com/polymarket-audits-builders-program-startups-over-insider-trading-concerns/

### 託管模式
- 自稱「non-custodial」：Privy（MPC＋secure enclaves，Stripe 投資的錢包基建商）管理金鑰，鏈上錢包為 Gnosis Safe 智能合約錢包；宣稱伺服器不持有私鑰、用戶可導出私鑰。
  - https://kreopoly.app/docs/ ・ https://coincodecap.com/kreo-review-polymarket-kalshi-copy-trading-bot
- **實質**：bot 替你開一個新的嵌入式錢包（非連接你既有錢包），你把 USDC 存進去、bot 有代簽權限自動下單——本質是「可代簽的熱錢包」，比要私鑰的舊式 bot 好，但不等於冷錢包級安全。評測原話：「still a hot wallet by design … fund the bot incrementally rather than parking everything inside」。

### 收費
- 交易抽成制（無訂閱）：每筆 `max(0.003, 0.07 × price × (1 − price))`，即 50/50 盤口最高約 1.75%，極端賠率趨近 0.3% 下限；疊加在 Polymarket/Kalshi 本身費用之上。
  - https://kreopoly.app/docs/ ・ https://polymarktbots.com/tools/copy-trading-bots/kreo/

### 推薦返佣（=作者利益）
- **L1 直接推薦：抽被推薦人每筆交易淨手續費的 30–35%（永久，非一次性）；L2 3%、L3 2%**；另有自身交易 5–25% 費用返還、被別人跟單可抽其產生淨費 15%。以 USDC.e（Polygon）發放。
  - https://kreopoly.app/rewards/ ・ https://kreopoly.app/docs/
- → 透過 `ref-waveking` 註冊，「waveking」可長期抽你 30–35% 的交易手續費。**明確利益衝突**。查無「waveking」個人身分資訊（查無）。

### 上線時間與規模
- @kreoapp X 帳號 2025-11 加入；與 Builders Program（2025-11）同期 → 至今約 8 個月。
  - https://x.com/kreoapp ・ https://unchainedcrypto.com/polymarket-audits-builders-program-startups-over-insider-trading-concerns/
- 用戶規模：**查無官方數字**。評測稱「small but active user base」。Builders Program 整體（含 Kreo、Polycool 等）把月交易量從 $100M（2025-11）推到 $600M+（2026-03，佔 Polymarket 16%），非 Kreo 單獨數字。
  - https://www.theinformation.com/articles/polymarket-reverses-course-startups-piggyback-insider-trades（轉引自 Unchained/The Block）

### 負面紀錄與稽核
- 被駭/rug/盜款/drainer 指控：英文（Kreo scam/rug/drainer/stole funds/hack）與中文（Kreo 骗局/跑路/盗、跟单机器人 盗）**均查無**具體受害指控（截至 2026-07-10）。
- 安全稽核：**查無**任何公開第三方智能合約或安全稽核報告；安全性訴求全押在 Privy＋Gnosis Safe 基建上。
- **監管/平台風險**：2026 年 Polymarket 正對 Kreo、Polycool 等 copy-trading 應用啟動稽核——Kreo 行銷語「find insiders before everyone else」被點名，涉協助用戶跟單疑似內線帳戶。若被切斷 API/封殺，跟單功能與存放資金的流動性都有風險。
  - https://unchainedcrypto.com/polymarket-audits-builders-program-startups-over-insider-trading-concerns/
  - https://www.theblock.co/post/397387/polymarket-audits-startups-potentially-helping-users-copy-insider-trading-report
- 周邊風險環境：(1) Polymarket 本體 2026-06 前端供應鏈被駭 $3.1M（官方全額賠付）；(2) GitHub 上有假 Polymarket bot 藏私鑰竊取器的活躍攻擊。與 Kreo 無直接關聯，但說明此領域釣魚/假冒極多。
  - https://techcrunch.com/2026/06/25/polymarket-says-hackers-stole-users-funds/
  - https://www.coindesk.com/markets/2026/06/27/polymarket-hack-updated-to-usd3-1-million-days-after-the-platform-promised-users-full-refunds
  - https://www.stepsecurity.io/blog/malicious-polymarket-bot-hides-in-hijacked-dev-protocol-github-org-and-steals-wallet-keys

### 品類前科（Telegram 交易 bot 歷史事故，3 例）
1. **Maestro**（2023-10-24）：router 合約漏洞，106 名用戶被盜約 280 ETH，團隊賠 610 ETH。https://www.certik.com/resources/blog/1Zh5XbaDstXKteFcRSmOcp-maestro-and-unibot
2. **Unibot**（2023-10-31）：call injection 漏洞，約 355.5 ETH（>$600K）被盜，團隊承諾賠償。https://www.cryptopolitan.com/unibot-suffers-security-breach-600k-lost/
3. **Banana Gun**（2024-09）：Telegram 訊息 oracle 漏洞，11 名用戶被盜約 563 ETH（~$1.9–3M），金庫全額賠付。https://www.bitget.com/news/detail/12560604219665
→ 教訓：即使「大牌」bot 也出過事，差別只在團隊有無能力賠。匿名＋無稽核＋8 個月的新 bot，賠付能力未知。

### 另一個直接相關警訊
- 資安帳號 Kr$na（@krishdotdev）2026 年點名一篇同類型「Polymarket 跟單」X 文章為「本月最精緻的詐騙文章」：內嵌兩個推薦漏斗、錢包連到已知詐騙網路、宣稱 33,950 筆交易 100% 勝率（數學上不可能）。與本次 waveking 文章是否同一作者查無，但**該文體（教學文＋嵌入 ref 連結＋誇張勝率）本身就是已知詐騙/導流模板**。
  - https://x.com/krishdotdev/status/2038238892344979934

### A 判定：**中風險（偏高）**
理由：架構在品類內相對較好（Privy MPC＋Gnosis Safe、可導出私鑰、無需交私鑰），且查無出事紀錄；但團隊匿名、無公開稽核、上線僅約 8 個月、資金實質放在 bot 可代簽的熱錢包、正被 Polymarket 稽核（平台風險）、品類前科累累——**只適合放「全損也無所謂」的小額**，絕不適合大額資金。

---

## 對象 B：polymarketanalytics.com

- **確實存在**，且有 Traders 頁：https://polymarketanalytics.com/traders（頁題即「Top Trader PnL, Positions, Wins & Losses」）。
- 篩選器與文章描述吻合：PnL（總收益）、current holdings value（持倉價值）、active positions（活躍倉位）、wins/losses（勝負場數）、win rate（勝率）、近期報酬率；V2 加入連勝 streak 與 API。
  - https://polymarketanalytics.com/traders ・ https://news.polymarket.com/p/this-tool-finds-polymarket-traders
- 誰營運：**Primo Data（@primo_data）**，具名資料工程師，Dune 上有公開帳號；先以 side project 形式建站，**後來已加入 Polymarket 團隊**，站點獲 Polymarket 官方 newsletter 專文介紹（「carries direct support from Polymarket itself」）。
  - https://x.com/primo_data ・ https://dune.com/primo_data ・ https://news.polymarket.com/p/this-tool-finds-polymarket-traders
- 資料來源：鏈上真數據——用 Goldsky 索引 Polygon 鏈上交易＋Polymarket Gamma API 補足鏈下資料。
  - https://news.polymarket.com/p/this-tool-finds-polymarket-traders
- 免費/付費：瀏覽為免費（第三方描述「free data platform」）；站上有 /pricing 頁，付費部分疑為 Pro/API（一處第三方提及 $25/月，**未能直接開頁驗證**，proxy 擋）。
  - https://polymarketanalytics.com/pricing ・ https://polymart.app/polymarket-analytics
- 社群評價：查無負面指控；被 Polymarket 官方、多個第三方導覽站正面引用。
- 注意：它是**唯讀分析站**，不碰錢包、不需存款——與 A 的風險性質完全不同。

### B 判定：**低風險**
理由：具名作者（已入職 Polymarket）、官方背書、鏈上數據可驗證、唯讀不涉資金；最多只有「數據解讀誤導」風險（歷史勝率≠未來報酬）。

---

## 問題 3 明確回答：作者透過推薦連結拿什麼好處
透過 https://t.me/KreoPolyBot?start=ref-waveking 註冊後，作者（waveking）**永久抽取你每筆交易 Kreo 淨手續費的 30–35%（L1），你再推薦別人他還抽 L2 3%／L3 2%**，以 USDC.e 直接入他帳（https://kreopoly.app/rewards/）。文章本質是有直接金錢動機的導流內容，勝率/獲利敘事應視為行銷而非中立評測。

## 查無清單
- Kreo 具名團隊/公司實體、官方用戶數/交易量、任何第三方安全稽核報告
- 「waveking」的身分、其 X 文章是否為 Kr$na 點名的那批詐騙文
- polymarketanalytics.com 付費方案確切價格（/pricing 被 proxy 擋，無法直開）
- t.me/KreoPolyBot 預覽頁原文（proxy 擋 t.me）——@KreoPolyBot 為官方 bot 係由多來源交叉指認，非直接驗證

## 雲端做不到（供 mac-manual-homework 待辦）
- proxy 對 t.me、kreopoly.app、docs.kreo.app、polymarketanalytics.com、polymarket.com、coincodecap.com 等 CONNECT 一律 403：需在 Mac 手動開 (1) t.me/KreoPolyBot 預覽確認 bot 名與用戶數 (2) polymarketanalytics.com/traders 與 /pricing 確認篩選器與價格 (3) docs.kreo.app 核對費率/返佣原文。

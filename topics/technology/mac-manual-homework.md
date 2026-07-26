---
title: 🖥️ Mac 手動功課清單（雲端做不到、只能在 Jake 電腦上做的事）
url: local
topic: technology
tags: [workflow, convention, manual-homework, cloud-limitations, checklist]
last_updated: 2026-07-06
---

# Mac 手動功課清單

## 這份檔案在幹嘛（慣例說明）

雲端 session（claude.ai/code）跑在隔離容器裡，有些事**做不到**：
- 抓被 403 擋掉的日本財經站（Yahoo!ファイナンス、kabutan、minkabu）、EDINET/TDnet、部分券商頁；
- 觸發需要 `actions:write` 的 GitHub 操作（整合 token 無此權限，Claude 代按會 403）；
- 讀你本機的 broker/下單環境。

**慣例**：每次雲端 session 結束時，把「雲端做不到、需要你在 Mac 上做」的事**集中 append 到本檔的「待辦」區**（而不是散在對話裡）。你在 Mac 開一個 local session（或自己動手）**一次清掉**，做完打勾、移到「已完成」區。這樣把散射的介入合併成單點，也不會漏。

> 為什麼放這裡：CLAUDE.md 的「KIWI 自動載入」清單有指向本檔，所以**每個新 session 開場就會看到有沒有積欠的手動功課**——系統提醒你，而不是你自己記。

---

## 🔴 待辦（依急迫度）

### 站著的（長期）
- [ ] **GitHub Pages deploy 卡住時去按 Re-run failed jobs**（自 2026-07-03 起偶發，Pages 後端暫時性錯誤、非程式問題）。
  - ✅ 現在已有失敗推播（`deploy-pages.yml` → Telegram），收到通知再去按即可，不用自己巡邏網站。
  - 位置：Actions 分頁 → Deploy Dashboard to GitHub Pages → Re-run failed jobs；或等下次自動 deploy。

### 2026-07-06 session 產生的（JEM 第一關收尾，加碼前必做）
> 🔄 **2026-07-26 狀態更新：已改由資料橋自動處理，先別自己做。** 本 session 實測雲端 agent proxy 對 **TDnet／EDINET／irbank／kabutan／minkabu／Yahoo!JP／JEM 官網 全部 CONNECT 403**（curl 與 WebFetch 皆然）→ 新增 `scripts/fetch_jp_disclosures.py` 掛在 dashboard workflow（一天 3 次）的 `fetch_backtest_ext.py` 後面，由 Actions runner 抓 irbank 的 `/ir`（開示一覽）與 `/customers`（有報 相手先別販売実績），落地 `data/ext/jp_disclosures/6855_JEM.md`。**下次 bot 跑完就有檔；若檔內是 403 錯誤訊息（代表 runner 也被擋），才需要你在 Mac 上手動做下面兩項。**
- [ ] **TDnet 7 月適時開示清單**（等橋）：確認 JEM（6855）無再增資/CB/下修。→ 否證 #1。**搜尋層已知：7/11 與 7/24 各有一則開示（PDF 123KB／106KB），標題未取得**——多半是例行的自己株式取得狀況報告，但需確認。
- [ ] **JEM FY3/26 有報「主な相手先別販売実績」**（等橋）：查 NAND 單一客戶占比、**Micron 系是否回到 >10%（＝最強確認）**。→ 否證 #2。**搜尋層已取得部分答案：有報註記「Micron Memory Japan 與 MICRON MEMORY TAIWAN 前事業年度合計未達總銷售 10%」——即 Micron 系在前一年度 <10%；當年度（FY3/26）數字未取得，最強確認訊號尚未成立也尚未推翻。**
- [ ] **Yahoo!ファイナンス 6855 時系列**：核對 7/3 與 7/6 兩日收盤，判別 7/6 單日跌幅是 -10.4% 還是 -14.3%（兩快照矛盾，複核 agent 無法裁決）。
  - 三項全過 → JEM 首批建倉區 ¥6,400–6,800 紀律恢復有效（第二關 8/7 Q1 財報再定第二批）。

### 2026-07-12 session 產生的（LFI 第四錶）
- [ ] **上線驗證 LFI 第四錶**：bot 下次跑 update-dashboard 後，開 https://gutinganthony.github.io/KIWI/ 看第四張紫色錶卡（LFI）有沒有出現真讀數（不是「--」）；失敗會有 Telegram 推播。
- [ ] **上線驗證「連續維持天數」標注**：同一張 LFI 卡片底部應出現「目前水位已連續維持 ≥80 X · ≥90 Y · ≥95 Z 交易日」那一行（bot 下次跑才會帶出 `days_ge_*`，在那之前該行隱藏是正常的）。07-10 讀數已到 84.8，若持續 ≥80，X 應該 ≥1 且逐日遞增。
- [ ] **（可選）真標的驗證節流閥**：資料橋補齊 JEM/Towa/Kokusai 等真股歷史後（~1 週），重跑 `scripts/serenity_throttle_validation.py` 改用真標的，確認「節流閥別硬加」的結論在真標的上也成立。
### 2026-07-12 session 產生的（llm-council-skill 評估）
- [ ] **安裝 gcpdev/llm-council-skill 到 Mac 本機 Claude Code**（雲端跑不了：容器 proxy 會擋 OpenAI/Gemini 的 API 呼叫）。雲端已做背景查證：作者可信（萊比錫大學語意網研究者）、334★、MIT 授權、無安全疑慮紀錄，但程式碼本身**未逐行審查**（`add_repo` 核准流程本 session 沒跑通）。步驟：clone repo → 把 `llm-council/` 資料夾放進 `~/.claude/skills/` → `.env` 填 `OPENAI_API_KEY`/`GEMINI_API_KEY` → 裝之前先看一眼 `scripts/query_llms.py` 確認只打 OpenAI/Google 官方端點、沒有第三方轉發。用法：對話裡打「Consult the council: ＜問題＞」。**⚠️ 只拿它問技術/通用問題，別把 KIWI 持倉、部位、fund 細節餵給它**——內容會送到 OpenAI 和 Google。ChatGPT 本來就是 council 兩席之一，免額外設定。

### 2026-07-16 session 產生的（幫朋友代管資金研究——僅在你決定要做時才需核對）
- [ ] **核對 Bitget 託管子帳戶門檻**（bitget.com/support 被雲端擋）：「>50,000 USDT 或 VIP2 可申請委託交易員、投資人保留出入金權、無建立費」——這是唯一個人可行的正式代管路徑，數字全來自搜尋摘要未直接核對。
- [ ] **核對 Binance/Bybit/Bitget 帶單門檻與台灣可用性**（官網全被雲端擋；OKX 已直接核對免查）：Binance 合約帶單 1,000 USDT＋服務清單含台灣；Bybit 100 USDT＋Pro 版台灣可用性；Bitget 帶單台灣可用性（查無官方證據）。待核頁面清單見 `topics/business/2026-07-16-crypto-managed-trading-research/research_copytrading.md` 附錄。
- [ ] **（決定行動前必做）law.moj.gov.tw 核對法條原文**：銀行法 5-1/29/29-1/125（雲端僅 GitHub 鏡像間接核對）、《虛擬資產服務法》三讀條文與總統公布日、期交法 §3/§112——法規線報告所有判決字號皆為轉述，引用前須 law.judicial.gov.tw 複核。＋諮詢熟悉虛擬資產的執業律師。

### 2026-07-24 session 產生的（物理 AI 研究——低急迫，深掘/建倉前才需核）
- [ ] **日股估值三檔複核**（quote 站被雲端 403，全為搜尋摘要層）：HDS 6324 預估 PER ~152/PBR 8.3、THK 6481 PER ~36.7、IKO 6480 現價 ~¥2,041（7/14）——kabutan/Yahoo!ファイナンス 各花 1 分鐘。
- [ ] **和大 1536 Optimus 拉貨狀態查證**：Yahoo 股市有「Optimus 拉貨喊停」報導，與 Tesla 產線未啟動互相印證——確認和大是否已實際出貨/出貨中斷（月營收＋法說紀錄）。

### 2026-07-26 session 產生的（Serenity 週報 — 只剩「雲端真的做不到」的項）
> ✅ **上一批「補 live 現價」的功課全部由 2026-07-26 週報自動結案**——發現本 runner 可直連交易所級行情 API（見 `agents/LEARNINGS.md` 2026-07-26 條），全名單價格/市值/trailing P/E 已取得精確值，**不需要你在 Mac 上補價了**。以下是剩下真正需要你的：
- [ ] **JEM 6855 兩件建倉前功課（仍未清，唯一擋住執行的東西）**：①TDnet 7 月適時開示清單確認無再增資/CB/下修；②FY3/26 有価証券報告書「主な相手先別販売実績」查 NAND 單一客戶占比與 **Micron 系是否 >10%（＝最強確認）**。現價 ¥6,280 已跌破首批區 ¥6,400–6,800 下緣、朝 <¥5,800 最大加碼區走，**功課清掉才有部位可談**。
- [ ] **群翊 6664 七月營收（~8/10 公布）＝否證線裁判**：查 TWSE/Goodinfo 月營收 YoY。<10% → 5 月(+7.92%)+7 月成立、六月(+19.32%)變孤點、否證壓力回來；≥10% → 買進條件續成立。**本週價格已進 NT$330–360 觸發區、六月營收 ≥10%＝兩條件成立，這是唯一未結的變數。**
- [ ] **Seikoh 6834 中國 SINY 合資的曝險評估（需讀一手 TDnet PDF）**：`https://www.release.tdnet.info/inbs/140120260716595447.pdf`（7/17 公告）——查合資公司出資比例、是否可能推升中國營收占比、有無技術授權條款。**這是 🟢 觸發名單裡首次出現中國曝險**，Serenity 對中國是原則性排除，權益法不立即否決但要定性。
- [ ] **（低優先）Intekplus 064290 券商目標價時效確認**：查到的 TP ₩18,000 遠低於現價 ₩30,500，疑為 2026/3 舊報告。若確為舊件則不構成降評理由，本週報已暫降為觀察待重評。

### 2026-07-11 session 產生的（台股漏斗數據源）
- [ ] **註冊 FinMind 免費帳號取得 API token**（finmindtrade.com）→ 放進 GitHub repo Settings → Secrets → `FINMIND_TOKEN`。無 token 時台股管線走 TWSE 次源可運作；FinMind 主源（更穩、可歷史回補）的全市場查詢需 token 解鎖（匿名層回 400）。
- [ ] （低優先）雲端 WebFetch 被 403 擋的站 +1：`stockanalysis.com`（TSM 估值頁）。雲端已用 WebSearch 摘要繞過，僅在需要精確 P/B 等單一指標時在 Mac 上手動查。

### 2026-07-10 session 產生的（Polymarket 跟單文查證——優先度低：雲端查證結論已足夠明確〔判定為導流文，不建議執行〕，以下僅在你想二次確認時做）
- [ ] 開 t.me/KreoPolyBot 預覽確認 bot 真偽；開 t.me/polymarketsig、t.me/duanlang1000x、t.me/polyalpha1 查群人數與付費層級（t.me 被擋）
- [ ] 開 polymarketanalytics.com/traders 與 /pricing、docs.kreo.app 核對篩選器/價格/費率與返佣原文（站點被擋，僅搜尋摘要層取得）
- [ ] 登入 X 核對 @waveking1314 粉絲數、開號日、歷史貼文主題（搜尋摘要顯示 ~42.8K 粉、2023-03 開號，未直接核對）

### 2026-07-07 session 產生的（AXW/AIR TRF 研究）
- [ ] **AIR TRF 真實利差序列建檔（文獻查證：DataMine 有免費日檔！）**：註冊 CME DataMine → 拉 AIR TRF 免費 CSV（欄位 `DLY_FUND` FID#10335、`ACC_FUND` #10337）→ 建歷史序列存進 `projects/avi-v5/data/ext/air_trf.csv` → 跑與 `lev_stress_proxy` 的相關性（報告 §8 否證 ②）。備用免費儀表板：snippet.finance「S&P 500 Futures Financing」（2012 迄今）。每週順手記一次 CME 產品頁的近月 bps 與分位數。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

- [x] ~~本機 curl Polymarket data-api 複核範例錢包精確數字~~ → **2026-07-10 由 poly-observer CI（GitHub Actions runner 不受雲端封鎖）直查完成**，且推翻了媒體快照的「−$311k 爆倉」說法（實為終身 +$176,445、4/12 後停止交易、持倉 $0）。詳見 topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md v1.1。

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。

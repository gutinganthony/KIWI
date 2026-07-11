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
- [ ] **TDnet 7/3–7/6 適時開示清單**：確認 JEM（6855）這幾天沒有任何未被媒體報導的公告（增資/CB/下修）。→ 排除否證 #1 的殘餘不確定性。
- [ ] **JEM FY3/26 有価証券報告書「主な相手先別販売実績」表**（EDINET 或 JEM 官網 PDF）：查 NAND 單一客戶（Kioxia/Flash Forward 系）占比未失控、**Micron 系是否回到 >10%（=最強確認訊號）**。→ 補齊否證 #2 的資料缺口。
- [ ] **Yahoo!ファイナンス 6855 時系列**：核對 7/3 與 7/6 兩日收盤，判別 7/6 單日跌幅是 -10.4% 還是 -14.3%（兩快照矛盾，複核 agent 無法裁決）。
  - 三項全過 → JEM 首批建倉區 ¥6,400–6,800 紀律恢復有效（第二關 8/7 Q1 財報再定第二批）。

### 2026-07-11 session 產生的（台股漏斗數據源）
- [ ] **註冊 FinMind 免費帳號取得 API token**（finmindtrade.com）→ 放進 GitHub repo Settings → Secrets → `FINMIND_TOKEN`。無 token 時台股管線走 TWSE 次源可運作；FinMind 主源（更穩、可歷史回補）的全市場查詢需 token 解鎖（匿名層回 400）。

### 2026-07-10 session 產生的（Polymarket 跟單文查證——優先度低：雲端查證結論已足夠明確〔判定為導流文，不建議執行〕，以下僅在你想二次確認時做）
- [ ] 開 t.me/KreoPolyBot 預覽確認 bot 真偽；開 t.me/polymarketsig、t.me/duanlang1000x、t.me/polyalpha1 查群人數與付費層級（t.me 被擋）
- [ ] 開 polymarketanalytics.com/traders 與 /pricing、docs.kreo.app 核對篩選器/價格/費率與返佣原文（站點被擋，僅搜尋摘要層取得）
- [ ] 登入 X 核對 @waveking1314 粉絲數、開號日、歷史貼文主題（搜尋摘要顯示 ~42.8K 粉、2023-03 開號，未直接核對）

### 2026-07-11 session 產生的（playground plugin——可選，僅在你看完介紹想採用時做）
- [ ] **在 Mac 的 Claude Code 安裝 playground plugin**：跑 `/plugin` 瀏覽官方 marketplace（anthropics/claude-plugins-official）→ 安裝 `playground`。之後在本機對 Claude 說「幫我做一個 XX 的 playground」即可。雲端 session 不需裝——直接請 session 照同樣模式生 HTML 並以 Artifact 連結交付。

### 2026-07-07 session 產生的（AXW/AIR TRF 研究）
- [ ] **AIR TRF 真實利差序列建檔（文獻查證：DataMine 有免費日檔！）**：註冊 CME DataMine → 拉 AIR TRF 免費 CSV（欄位 `DLY_FUND` FID#10335、`ACC_FUND` #10337）→ 建歷史序列存進 `projects/avi-v5/data/ext/air_trf.csv` → 跑與 `lev_stress_proxy` 的相關性（報告 §8 否證 ②）。備用免費儀表板：snippet.finance「S&P 500 Futures Financing」（2012 迄今）。每週順手記一次 CME 產品頁的近月 bps 與分位數。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

- [x] ~~本機 curl Polymarket data-api 複核範例錢包精確數字~~ → **2026-07-10 由 poly-observer CI（GitHub Actions runner 不受雲端封鎖）直查完成**，且推翻了媒體快照的「−$311k 爆倉」說法（實為終身 +$176,445、4/12 後停止交易、持倉 $0）。詳見 topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md v1.1。

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。

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

### 2026-07-11 session 產生的（Vibe-Trading——目前唯一的主動功課）
- [ ] **若要跑 Vibe-Trading 的 swarm（多空辯論委員會）**：提供一把 DeepSeek 或 OpenRouter API key → GitHub Secrets。純資料層/回測/alpha bench **不需要任何 LLM key**（Claude 本身就是大腦），且雲端 session 已實測可安裝——真正的雲端阻礙是行情源被 proxy 封鎖，解法是走 GitHub Actions（詳見評估文與 2026-07-11 session 對話）。Mac 本機安裝只在你想要「即時互動 TUI」時才需要。評估文：topics/technology/2026-07-11-vibe-trading-hkuds-evaluation.md

### 擱置（AIR TRF——等 Jake 讀完說明決定要不要做；屬 avi-v5 報告 §8 否證②的驗證工作）
- [ ] **AIR TRF 真實利差序列建檔**：AIR TRF = CME「調整利率型 S&P 500 總報酬期貨」，其隱含融資利差是市場槓桿需求的直接量測。此功課=註冊 CME DataMine（有免費日檔）→ 拉 CSV（欄位 `DLY_FUND` FID#10335、`ACC_FUND` #10337）→ 存進 `projects/avi-v5/data/ext/air_trf.csv` → 驗證 AVI 的 `lev_stress_proxy` 代理指標是否真的跟蹤實際融資壓力。備用免費儀表板：snippet.finance「S&P 500 Futures Financing」（2012 迄今）。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

- [x] ~~註冊 FinMind 免費帳號取得 API token → GitHub Secrets `FINMIND_TOKEN`~~ → **2026-07-11 確認已生效**：當日 tw-funnel CI 的 fetch_meta.json 顯示 FinMind 以 register 等級回應（股票清單 200、月營收 43 檔抓到 42）。法人買賣超/全市場股價兩個資料集回 400 是「需付費 sponsor 層」而非 token 缺失——管線已自動 fallback TWSE 且成功，**免費層即可，不需升級**。
- [x] ~~本機 curl Polymarket data-api 複核範例錢包精確數字~~ → **2026-07-10 由 poly-observer CI（GitHub Actions runner 不受雲端封鎖）直查完成**，且推翻了媒體快照的「−$311k 爆倉」說法（實為終身 +$176,445、4/12 後停止交易、持倉 $0）。詳見 topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md v1.1。

## 🗄️ 已取消（2026-07-11 Jake 指示：手動功課只留 Vibe-Trading；以下項目取消，保留紀錄以便日後想撿回）

- ~~JEM 第一關收尾三項（TDnet 7/3–7/6 開示清單、FY3/26 有報「主な相手先別販売実績」表、Yahoo!ファイナンス 6855 時系列核對）~~——原目的：JEM 加碼前排除否證 #1/#2 殘餘不確定性。取消＝若未做就加碼，承擔對應資訊缺口。
- ~~Polymarket 導流文二次確認三項（t.me 群組核對、polymarketanalytics/kreo 原文核對、@waveking1314 X 帳號核對）~~——雲端查證結論已明確（導流文、不建議執行），本就標記為可選。

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。

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

### 2026-07-07 session 產生的（AXW/AIR TRF 研究）
- [ ] **AIR TRF 真實利差數據探路**：在 Mac 上試 yfinance/券商終端有無 ASR（S&P 500 AIR TRF）連續合約價；沒有的話看 CME 每日 settlement 頁能否腳本化抓取（今後累積序列）；評估 DataMine `cme.air` 是否值得買。→ 用途：驗證 `lev_stress_proxy` 與真品的相關性（報告 §8 否證條件 ②）。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

（空）

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。

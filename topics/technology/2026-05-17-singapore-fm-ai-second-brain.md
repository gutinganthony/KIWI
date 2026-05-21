---
title: 新加坡外長的 AI 第二大腦 — NanoClaw + Obsidian + Whisper 實戰外交
url: https://www.facebook.com/story.php?story_fbid=10163322509018318&id=649368317
source: Facebook 文章（AI Engineer Singapore 大會演講紀錄）
date_added: 2026-05-17
last_updated: 2026-05-17
topic: technology
tags: [AI-agent, NanoClaw, Obsidian, second-brain, Claude, Raspberry-Pi, personal-AI, workflow, government, deep-dive]
version: 1.0
---

## Summary

新加坡外交部長 Vivian Balakrishnan（65 歲、眼科醫師出身、不會寫程式）花三個月在一台 8GB Raspberry Pi 上組了一套個人 AI 助理，用於外交工作。核心技術棧：NanoClaw（Claude Agent SDK 上的輕量代理框架）+ Mnemon（圖譜記憶系統）+ Ollama（本機嵌入模型）+ Whisper（語音）+ Obsidian（wiki + iCloud 同步）。他說已經不敢把它關掉了。

---

## 三個核心訊息

### 1. 你的理解無法外包

> 計算、記憶、知識傳播都可以交給機器，但「理解」外包不掉。你可以把工作授權出去，但你沒辦法把問責授權出去。

他堅持自己讀得懂 NanoClaw 的程式碼（只有 ~500 行），每次代理要 bash 權限他都會掃過那段程式碼。「就算你不會寫程式，能看懂發生了什麼事，也已經有差。」

### 2. 真正的價值在地面層

引用劍橋大學 Neil Lawrence 的觀點：AI 的真正回報不在模型層、不在資料中心，而是**一般人開始用這些工具的時候**。老師、律師、醫生、經理、部長——懂自己工作、又被工具加持的人，才是替社會創造真實價值的人。

### 3. 進入門檻已經崩塌

他沒有寫 Claude，沒有寫 Baileys，沒有寫 Mnemon，沒有寫 Whisper。他連 glue code 都沒寫。他做的事情就是**組裝**。「光是坐著讀、看標題、看摘要是不夠的，你對什麼有興趣，就去把手弄濕。」

---

## 他的技術棧

| 層 | 工具 | 用途 |
|---|------|------|
| 代理框架 | **NanoClaw**（基於 Claude Agent SDK，~500 行程式碼） | 底層平台，透過 WhatsApp 跟 AI 對話 |
| 通訊介面 | **Baileys**（WhatsApp 偽終端機） | 讓代理接上 WhatsApp |
| 記憶系統 | **Mnemon**（圖譜結構記憶） | 實體 + 因果/時間/語意關係 |
| 語意搜尋 | **Ollama** + 嵌入模型（本機） | 不被關鍵字綁死，語意搜尋 |
| 語音 | **Whisper** | 語音輸入輸出 |
| 知識庫 | **Obsidian** + iCloud | wiki 生成 + 跨裝置同步 |
| 硬體 | **Raspberry Pi**（8GB，兩三年前買的） | 每天跑代理 |
| LLM | **Claude**（Anthropic） | 分析、抽象、起草 |

### 他的使用場景

- 出差前：AI 整理目標國家的經濟、地理、文化、歷史、戰爭與和平
- 會前：AI 抽出談判對手的背景資料
- 起草：簡報、講稿、國會質詢答覆
- 記憶：把講稿、國會發言、逐字稿餵進 Mnemon，建立長期記憶
- Wiki：用 Karpathy 的 LLM 監督式 wiki 生成法，自動產出知識條目

---

## 他提到的限制

1. **成本**：Token 不便宜，算力有限，電價在漲。不要把每個問題都丟給 LLM。
2. **確定性系統仍有角色**：專家規則系統、神經符號系統。「LLM 很好，但這不是大自然解決問題的方式」（引 Yann LeCun）。
3. **安全**：只放已公開、已發表的東西進系統。安全始終第一位。
4. **記憶是最大未解難題**：「記憶這件事非常人性。」
5. **工具比模型重要**。

---

## 🔗 與我們系統的對應與可應用之處

### 1. 他的 Obsidian + iCloud = 我們的 Second Brain

**他做了什麼**：Obsidian 存 wiki，iCloud 同步，走到哪帶到哪。

**我們已經有什麼**：完整的 Obsidian Second Brain（CLAUDE.md + 6 個 McKinsey Prompt + 7 個模板 + 報告情報管線），已安裝在你的 Mac 上，用 iCloud 同步。

**可以借鑑的**：
- 他用 Mnemon 做**圖譜記憶**，我們的 Obsidian 目前只有 wiki links，可以加入更結構化的實體關係（例如：「NVDA → 供應商 → TSMC → 地緣風險 → 台海」這種因果鏈）
- 他用 Karpathy 的 LLM 監督式 wiki 生成法——我們可以讓 Claude 自動從每日 TSI/CPI 報告中生成 Obsidian wiki 條目

### 2. 他的 NanoClaw + WhatsApp = 我們可以做的 LINE/Telegram 通知

**他做了什麼**：透過 WhatsApp 跟 AI 代理對話，隨時隨地問問題。

**我們可以做的**：
- 把 CPI/TSI 的每日結果自動推送到 LINE 或 Telegram
- 設定 Flash Alert 自動觸發通知（不用每天手動跑 Dashboard）
- 甚至可以像他一樣，用 WhatsApp/LINE 直接問「今天科技股壓力多高？」然後 AI 回答

### 3. 他的「理解無法外包」= 我們的系統化決策 + 人工判斷

**他的原則**：AI 整理資訊，但判斷是人做的。每次 bash 權限他都會親自看。

**對應到我們**：
- CPI/TSI 給你信號，但**你**決定要不要減倉
- 月報是 AI 生成的，但**你**要看過才發給客戶
- 合約是我幫你擬的，但**你**要確認每一條才能用
- **永遠不要讓系統自動交易**——系統給建議，你按按鈕

### 4. 他的「地面層價值」= 你用 AVI/CPI/TSI 做內容行銷

**他的觀點**：真正的價值是一般人開始用工具的時候。

**對你的意義**：
- 你不需要訓練新模型，你需要的是**把投資顧問的工作流程用現有工具重接一遍**（你已經做了！）
- 你的 CPI/TSI Dashboard 就是「地面層」的產物——用現成的 AI 工具解決投資顧問的真實痛點
- 這也是你突破死因 3（募資瓶頸）的核心武器：公開分享你的系統化方法，吸引認同這種方法論的客戶

### 5. 他的「門檻已崩塌」= 你已經是活證據

**他的證據**：65 歲、不會寫程式、用 Raspberry Pi。

**你的證據**：金融投資顧問、用 Claude Code 建了三套量化系統（AVI/CPI/TSI）+ Dashboard + Obsidian Second Brain + 創業評估 Skill。你比他走得更遠。

### 6. 具體可以新增到系統的功能

| 靈感來源 | 我們可以做的 | 優先級 |
|---------|------------|--------|
| Mnemon 圖譜記憶 | 在 Obsidian 中建立「投資因果鏈」（公司→產業→宏觀→地緣）| P2 |
| WhatsApp 代理 | CPI/TSI Flash Alert → LINE 自動推播 | P1 |
| Karpathy wiki 生成 | 每日 TSI/CPI 自動生成 Obsidian 日誌條目 | P2 |
| Whisper 語音 | 用語音問「今天 CPI 多少？」→ AI 回答 | P3 |
| 「不敢關掉」的日常化 | GitHub Pages 部署 → 隨時任何裝置查看 | **P0**（正在做）|

---

## 金句摘錄

> 「我老實講，已經不敢把它關掉了。」

> 「你沒辦法治理一個你只被簡報過的技術。」

> 「你的理解無法外包。你可以把工作授權出去，但你沒辦法把問責授權出去。」

> 「真正的回報，是當一般人開始用這些工具的時候才出現。」

> 「光是坐著讀、看標題、看摘要是不夠的。你對什麼有興趣，就去把手弄濕。」

> 「手裡拿著鎚子的人，看什麼都像釘子。」

---

## Update Log

- 2026-05-17 v1.0: 完整文章摘錄 + 三核心訊息 + 技術棧 + 與我們系統的 6 個對應點。

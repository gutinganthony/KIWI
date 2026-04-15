---
title: 如何用 Claude Code 自動化重複性商業任務 (How to Automate Repetitive Business Tasks Using Claude Code)
url: https://www.geeky-gadgets.com/automate-tasks-with-claude-code/
source: Geeky Gadgets (based on insights by Simon Scrapes)
date_added: 2026-04-15
last_updated: 2026-04-15
topic: technology
tags: [claude-code, ai, automation, business-workflow, claude-md, skills, productivity, no-code, smb]
version: 1.0
---

## Summary

Geeky Gadgets 整理自 Simon Scrapes 的分析文章，介紹 Claude Code 如何成為中小企業主與非技術使用者的「重複性任務自動化引擎」。文章不以寫程式為核心，而是把 Claude Code 重新定位為：用自然語言下指令、可客製化品牌語氣、可安裝 Skills 當作數位 SOP 的自動化平台，串接 Shopify、Slack、CRM 等日常商業系統。

核心主張：Claude Code 的價值不只是寫程式，而是把那些「80% 差不多就好、但人類要反覆修的」工作（內容生成、銷售報告、個人化郵件）交給 AI 一致性執行，讓老闆與團隊把時間留給策略決策。

## Key Takeaways

- **「80% 問題」是重點痛點**：Simon Scrapes 強調一般 AI 工具常因 context drift 與重複性錯誤導致人工修正，反而抵銷掉生產力紅利。Claude Code 透過 `Claude.md` + Skills 解決一致性問題。
- **Claude.md 是品牌記憶體**：使用者可在專案根目錄的 `Claude.md` 裡預先寫入語氣、風格、禁用詞、品牌準則，讓每次輸出自動對齊品牌。
- **Skills = 數位 SOP**：預先定義的任務劇本（playbook），例如「寫 SEO 部落格文章」、「草擬客戶回覆信」，讓 AI agent 能以一致流程反覆執行。
- **自然語言即介面**：非技術人員也能透過 prompt 委派任務，不需要懂 CLI 或程式語法。
- **原生整合商業系統**：文章點名 Shopify、Slack 等平台，並延伸到 CRM、專案管理工具的串接可能性。
- **訂閱制定價**：$20 – $200/月的彈性方案，適合從個人到小型團隊。

---

## 1. 重新定位 Claude Code：從 Dev Tool 到 Business Automation

傳統認知裡，Claude Code 是給工程師寫程式用的終端機工具。本篇文章的觀點翻轉這個框架：

- **使用者是誰**：小企業主、行銷、業務、客服、營運
- **任務是什麼**：不是寫 app，而是每天重複的「內容 / 溝通 / 報表 / 資料搬運」
- **為什麼選 Claude Code**：因為它有檔案系統存取、可執行命令、可安裝 Skills，比一般聊天介面更「會動手」

這是把 Claude Code 當成「有執行力的 AI 員工」來用，而不是 autocomplete。

## 2. Claude.md — 讓 AI 記住你的品牌

文章把 `Claude.md` 描述為客製化的起點。它是一個放在專案根目錄的純文字檔，功能類似於：

| 層面 | 可以寫進 Claude.md 的內容 |
|------|------------------------|
| Tone & Voice | 正式 / 親切 / 專業 / 幽默、句子長短、第幾人稱 |
| 品牌準則 | 禁用詞、必提關鍵字、產品名稱大小寫 |
| 任務預設 | 預設輸出格式（Markdown / 表格 / JSON） |
| 資訊來源 | 要優先查閱的檔案、資料夾、URL |
| 安全邊界 | 不能碰的檔案 / 不能寄出的郵件帳號 |

> Claude 每次啟動工作階段都會讀取 `Claude.md`，因此輸出自動對齊品牌，不用每次都重寫 prompt。

## 3. Skills — 預先封裝的任務劇本

Skills 是 Claude Code 的「任務模板」概念，文章把它類比為數位 SOP。文章提到的典型範例：

- **SEO-friendly 部落格文章生成**：從關鍵字研究 → 大綱 → 內文 → meta description 一條龍
- **客戶郵件草擬**：依對象、目的、歷史紀錄自動生成個人化信件
- **銷售報表**：從原始資料產出視覺化報告
- **內容改寫 / 多平台再利用**：同一份內容改寫成部落格、電子報、社群貼文

Skills 的優勢：**一致性**。人類寫十次同類文件會有十種風格；Skill 可以強制走固定流程。

## 4. 實務應用場景

| 場景 | 例子 | 串接系統 |
|------|------|---------|
| 內容生成 | 每週部落格、週報、產品更新 | Ghost、WordPress、Notion |
| 個人化溝通 | 客戶追蹤信、合作邀約 | Gmail、Outlook、CRM |
| 電商營運 | 商品描述、庫存報表 | **Shopify** |
| 團隊協作 | 會議摘要、任務派發 | **Slack**、Linear |
| 銷售情報 | 每日 / 每週銷售報告 | Google Sheets、HubSpot |

文章特別點名 **Shopify** 與 **Slack** 作為示範整合對象，代表這套方法論對電商店家和遠端團隊最有立即回報。

## 5. 起步流程（文章隱含的四步驟）

1. **訂閱 Claude 方案**：$20 – $200/月，依使用量與團隊規模選
2. **寫 `Claude.md`**：把你的品牌守則、偏好格式、禁用清單寫進去
3. **學習下 prompt**：用自然語言清楚描述任務、交付物、驗收標準
4. **安裝或撰寫 Skills**：把反覆出現的任務封裝成 Skill，團隊共享

## 6. 觀察與延伸思考

- **這篇文章的敘事正在把 Claude Code「去工程師化」**：Anthropic 顯然想把 Claude Code 從 dev tool 擴展成通用自動化層，這與近期 Claude Code 推出 Skills、Computer Use、Scheduled Tasks 等功能方向一致。
- **`Claude.md` 的角色類似 `.cursorrules` / system prompt**，但加上了「品牌一致性」的包裝，這對非技術使用者是更好理解的比喻。
- **和 n8n / Zapier 的差異**：不是 node-based flow，而是 prompt + skill + 檔案系統。優勢是彈性與語言理解，劣勢是可觀測性較弱。
- **「80% 問題」值得記錄**：這個詞點出所有 LLM 自動化實務的真痛點——不是 AI 做不到，而是做不穩。
- **對 KIWI 的啟示**：KIWI 本身就是一個 Claude Code + `Claude.md` + 檔案系統驅動的個人知識庫範例，剛好是文章描述的模式最小可行版本。

---

## 相關延伸閱讀（同系列 Geeky Gadgets 報導）

- [Claude Code Agents: The Feature That Changes Everything](https://www.geeky-gadgets.com/claude-code-agents-task-automation/)
- [Claude Code 2 Feature Update: Automation, Workspace Links, and Skill Scoring](https://www.geeky-gadgets.com/claude-code-automation-workflows/)
- [Claude Code Skills Best Practices: Why 20–30 Beats 1,000](https://www.geeky-gadgets.com/claude-code-skills-best-practices/)
- [How to Automate Development Tasks with Claude Code & GitHub](https://www.geeky-gadgets.com/claude-code-github-workflow-automation/)

---

## Update Log

- 2026-04-15 v1.0: Initial entry. 基於 Geeky Gadgets 報導 + Simon Scrapes 分析整理，重點在於把 Claude Code 重新定位為商業自動化工具，並強調 `Claude.md` 與 Skills 兩大支柱。

---
type: workflow
created: 2026-05-10T00:00
updated: 2026-05-10T00:00
tags: [workflow, report, intelligence, automation]
status: active
---

# Report Intelligence Pipeline

> 每週情報掃描流程：從免費報告來源中萃取投資洞見與創業機會。

---

## Free Report Sources（14 個免費資訊來源）

| # | 來源 | 類型 | 頻率 | URL | 標籤 | 優先級 |
|---|------|------|------|-----|------|--------|
| 1 | McKinsey Insights | 策略/產業趨勢 | 每週 | mckinsey.com/insights | `#source/mckinsey` | 必讀 |
| 2 | BCG Henderson Institute | 策略/創新 | 每週 | bcghendersoninstitute.com | `#source/bcg` | 必讀 |
| 3 | Bain Brief | 策略/營運 | 每月 | bain.com/insights | `#source/bain` | 推薦 |
| 4 | Deloitte Insights | 產業/數位轉型 | 每週 | deloitte.com/insights | `#source/deloitte` | 推薦 |
| 5 | CB Insights Research | 市場數據/新創 | 每週 | cbinsights.com/research | `#source/cbinsights` | 必讀 |
| 6 | a16z Blog | 科技/VC觀點 | 每週 | a16z.com/blog | `#source/a16z` | 必讀 |
| 7 | Sequoia Arc | 創業指南/趨勢 | 不定期 | sequoiacap.com/arc | `#source/sequoia` | 推薦 |
| 8 | Y Combinator Blog | 創業/產品 | 每週 | ycombinator.com/blog | `#source/yc` | 必讀 |
| 9 | IMF Working Papers | 全球總經 | 每月 | imf.org/publications | `#source/imf` | 推薦 |
| 10 | BIS Quarterly Review | 央行/國際金融 | 每季 | bis.org/publ | `#source/bis` | 季度必讀 |
| 11 | FRED Blog | 美國總經數據 | 每週 | fredblog.stlouisfed.org | `#source/fed` | 推薦 |
| 12 | Bridgewater Daily Observations | 總經/投資框架 | 不定期 | bridgewater.com/research | `#source/bridgewater` | 有發就讀 |
| 13 | First Round Review | 營運/管理 | 每週 | review.firstround.com | `#source/firstround` | 推薦 |
| 14 | Stratechery (free tier) | 科技策略 | 每週 | stratechery.com | `#source/stratechery` | 必讀 |

### 補充台灣來源

| # | 來源 | 類型 | 頻率 | URL | 標籤 |
|---|------|------|------|-----|------|
| 15 | 台灣央行 | 貨幣政策 | 每季 | cbc.gov.tw | `#source/cbc` |
| 16 | 主計總處 DGBAS | 台灣經濟數據 | 每月 | dgbas.gov.tw | `#source/dgbas` |
| 17 | 金管會 | 金融法規 | 不定期 | fsc.gov.tw | `#source/fsc` |

---

## Weekly Monday Scan Workflow

### 流程圖

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  RSS Feed   │────▶│  Skim &      │────▶│  Create Note │────▶│  Link to    │
│  Aggregator │     │  Highlight   │     │  RS-{source} │     │  Thesis &   │
│  (Feedly/   │     │  Key Points  │     │  -YYYY-MM-DD │     │  Idea       │
│   Inoreader)│     │  (10 min)    │     │  (15 min)    │     │  Backlog    │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │  Apply Tags  │
                                         │  (Auto-rules)│
                                         └──────────────┘
```

### Step-by-Step Workflow

#### 1. 週一早晨掃描（30 min）— 07:15-07:45

**a) 開啟 RSS Reader（5 min）**
- 瀏覽上週累積的文章標題
- 快速判斷：值得讀 / 跳過 / 稍後讀
- 標記法：star 必讀、pin 稍後、skip 跳過

**b) 快速摘要必讀文章（15 min）**
- 每篇花 3-5 分鐘速讀
- 記錄：核心論點 + 關鍵數據 + 我的初始反應
- 存入 `00-Inbox/web-clips/` 等待週間深讀

**c) 建立本週閱讀清單（10 min）**
- 從標記的文章中選出 Top 5 深讀
- 安排到週間零碎時間
- 如有急迫性高的（影響投資決策），優先處理

#### 2. 每日零碎時間深讀（每天 15-20 min）

- 從本週清單中挑 1 篇深讀
- 使用 `Templates/tpl-report-summary.md` 建立正式筆記
- 命名：`RS-{source}-YYYY-MM-DD.md`
- 存入：`04-Learning/Reports/`

#### 3. 週五回顧連結（15 min，as part of Weekly Review）

- 回顧本週所有報告摘要
- 建立雙向連結：
  - 報告 <-> 相關 Investment Thesis
  - 報告 <-> Startup Idea Backlog
  - 報告 <-> 其他報告（相關主題群組）
- 標記需要追蹤的發展
- 更新 Idea Backlog scoring（如有新資訊）

---

## Auto-Tagging Rules

根據報告內容中出現的關鍵詞自動套用標籤：

```yaml
auto_tag_rules:
  # AI & Technology
  - keywords: [AI, artificial intelligence, LLM, GPT, Claude, machine learning, deep learning]
    tag: "#topic/ai"
  
  # FinTech
  - keywords: [fintech, payment, banking, neobank, insurtech, regtech, wealthtech]
    tag: "#topic/fintech"
  
  # Taiwan Specific
  - keywords: [Taiwan, 台灣, TSMC, semiconductor, 半導體, 金管會]
    tag: "#topic/taiwan"
  
  # Crypto & Web3
  - keywords: [crypto, blockchain, DeFi, web3, Bitcoin, Ethereum, stablecoin]
    tag: "#topic/crypto"
  
  # SaaS & Business Model
  - keywords: [SaaS, subscription, ARR, MRR, churn, retention, B2B]
    tag: "#topic/saas"
  
  # Startup & VC
  - keywords: [startup, founder, seed, Series A, venture capital, accelerator, YC]
    tag: "#topic/startup"
  
  # Macro Economics
  - keywords: [macro, GDP, inflation, interest rate, monetary policy, fiscal, recession]
    tag: "#topic/macro"
  
  # Quantitative
  - keywords: [quantitative, algorithm, backtest, alpha, factor, systematic]
    tag: "#topic/quant"
  
  # Consumer & Creator
  - keywords: [creator economy, influencer, content, social media, consumer]
    tag: "#topic/creator"
  
  # Climate & ESG
  - keywords: [ESG, climate, carbon, sustainability, green energy, clean tech]
    tag: "#topic/esg"
```

### 手動套用方式

在 Obsidian 中建立筆記後：
1. 掃描內容中的關鍵詞
2. 對照上方規則，在 frontmatter `tags` 中加入對應標籤
3. 加入來源標籤：`#source/{source_name}`
4. 加入 action 標籤（如需後續追蹤）：`#action/followup`

---

## Monthly Digest Generation Process

### 每月第一個週一（60 min）

#### 1. 數據彙整（15 min）

用 Dataview 查詢本月所有報告：

```dataview
TABLE source, relevance, tags
FROM "04-Learning/Reports"
WHERE date(created) >= date(today) - dur(30 days)
SORT relevance DESC
```

#### 2. 主題群組分析（20 min）

將本月報告按主題分群：
- 哪些主題出現頻率最高？（趨勢信號）
- 哪些主題的 relevance 分數最高？
- 跨主題的交叉點在哪裡？

#### 3. Monthly Insight Memo（20 min）

建立月度洞見備忘錄（存入 `06-Weekly-Review/`）：

```markdown
## Monthly Intelligence Digest: YYYY-MM

### Top Trends This Month
1. [趨勢] — 出現 N 次，相關報告：[[]]
2. 
3. 

### Investment Implications
- 

### Startup Opportunity Updates
- 新發現的機會：
- 被推翻的假設：
- 需要加速的方向：

### Knowledge Gaps Identified
- 我對什麼了解不足？
- 下個月需要深入的領域：

### Action Items for Next Month
- [ ] 
```

#### 4. Idea Backlog Update（5 min）

- 基於本月情報，更新 Idea Backlog 的評分
- 標記受到新趨勢支持/威脅的 ideas
- 是否有新的 idea 值得建檔？

---

## RSS Reader Setup Recommendations

### Option 1: Feedly (Free Tier)
- 可建立最多 3 個 feed 分類
- 建議分類：`Must Read` / `Finance & Macro` / `Tech & Startup`

### Option 2: Inoreader (Free Tier)
- 更好的搜尋功能
- 支援 keyword highlighting

### Option 3: Obsidian RSS Reader Plugin
- 直接在 vault 中讀取
- 缺點：需要 Obsidian 開啟才能更新

---

## Workflow Automation Ideas (Future)

- [ ] Readwise integration for auto highlight import
- [ ] IFTTT/Zapier: new report notification via Telegram
- [ ] Claude API: auto-generate report summary drafts
- [ ] Dataview: auto-generate monthly digest data section

---

*Related:* [[Templates/tpl-report-summary]]
*Weekly Review Template:* [[Templates/tpl-weekly-review]]

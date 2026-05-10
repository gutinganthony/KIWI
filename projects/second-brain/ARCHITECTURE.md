# Second Brain Architecture

> Obsidian Vault + Claude Code + KIWI 整合架構文件
> 適用對象：Financial Investment Advisor exploring entrepreneurship

---

## 1. Overview

本系統將 **Obsidian** 作為個人知識管理核心，結合 **Claude Code** 的 AI 能力與 **KIWI** 專案管理框架，為一位在台灣從事金融投資顧問、同時探索創業可能性的使用者打造完整的 Second Brain。

### 核心設計原則

| 原則 | 說明 |
|------|------|
| **Single Source of Truth** | 所有筆記、分析、想法集中在 Obsidian Vault |
| **AI-Augmented Thinking** | Claude Code 作為思考夥伴，不取代判斷 |
| **KIWI Integration** | 技術專案透過 symlink 無縫連結 |
| **Progressive Summarization** | 資訊經 Inbox → Processing → Permanent Notes 逐步精煉 |
| **Bilingual by Default** | 技術內容英文、個人反思與工作流程繁中 |

### 使用者背景

- **身份**：金融投資顧問（台灣）
- **社群**：@afternoon.jk（IG）
- **核心能力**：總經分析、投資論述建構、客戶關係管理
- **探索方向**：AI-native 創業、量化交易、個人品牌

---

## 2. Vault Structure

```
~/SecondBrain/
├── CLAUDE.md                          # Claude Code 進入 vault 的指引
├── 00-Inbox/                          # 快速捕捉，未整理的想法與連結
│   ├── fleeting-notes/                # 閃念筆記
│   ├── web-clips/                     # 網頁剪貼
│   └── ig-saved/                      # IG 儲存貼文摘要
├── 01-Daily/                          # 每日日誌
│   ├── 2026-01/
│   ├── 2026-02/
│   └── ...
├── 02-Investment/                     # 投資相關
│   ├── Market-Analysis/               # 市場分析筆記
│   ├── Thesis/                        # 投資論述
│   ├── Macro/                         # 總經觀察
│   ├── Client-Notes/                  # 客戶會議紀錄
│   └── AVI-Log/                       # AVI 系統開發日誌
├── 03-Startup/                        # 創業探索
│   ├── Idea-Backlog/                  # 創業想法庫
│   ├── Evaluations/                   # 想法評估報告
│   ├── Yuni/                          # Yuni 專案筆記
│   └── Competitive-Intel/             # 競爭情報
├── 04-Learning/                       # 學習資源
│   ├── Articles/                      # 文章摘要
│   ├── Books/                         # 讀書筆記
│   ├── Reports/                       # 研究報告
│   └── Courses/                       # 課程筆記
├── 05-AI-Toolkit/                     # AI 工具箱
│   ├── Prompts/                       # 常用 prompt 模板
│   ├── Workflows/                     # 自動化工作流程
│   └── Claude-Skills/                 # Claude Code skills
├── 06-Weekly-Review/                  # 週回顧
│   ├── 2026-W01/
│   └── ...
├── 07-KIWI/                           # → symlink to ~/KIWI
├── Templates/                         # Obsidian 模板
│   ├── tpl-daily-journal.md
│   ├── tpl-market-analysis.md
│   ├── tpl-startup-idea-evaluation.md
│   ├── tpl-client-meeting.md
│   ├── tpl-weekly-review.md
│   ├── tpl-report-summary.md
│   └── tpl-investment-thesis.md
└── Assets/                            # 附件（圖片、PDF）
    ├── images/
    └── pdfs/
```

### 資料夾命名規則

- 使用 `NN-` 前綴排序（00-07）
- 子資料夾用 `PascalCase` 或 `kebab-case`
- 年月子資料夾格式：`YYYY-MM`

---

## 3. CLAUDE.md（Vault Root 指引檔）

以下為放置於 `~/SecondBrain/CLAUDE.md` 的完整內容：

````markdown
# CLAUDE.md — Second Brain Vault

## Who I Am

我是一位在台灣的金融投資顧問（IG: @afternoon.jk），專注於總經分析與投資組合管理。
目前同時探索 AI-native 創業機會。

## Current Projects

| Project | Status | Location |
|---------|--------|----------|
| **AVI V4** | Active development | `07-KIWI/projects/avi-v5/` |
| **Yuni** | Concept exploration | `03-Startup/Yuni/` |
| **Quant** | Research phase | `07-KIWI/projects/quant/` |
| **KIWI** | Infrastructure | `07-KIWI/` |
| **Second Brain** | This system | `07-KIWI/projects/second-brain/` |

## Vault Conventions

### File Naming
- Daily notes: `YYYY-MM-DD.md` (e.g., `2026-05-10.md`)
- Market analysis: `MA-YYYY-MM-DD-{topic}.md`
- Investment thesis: `IT-{ticker-or-theme}.md`
- Client notes: `CN-YYYY-MM-DD-{client-code}.md`
- Startup ideas: `SI-{sequential-id}-{name}.md`
- Weekly reviews: `WR-YYYY-WNN.md`
- Report summaries: `RS-{source}-YYYY-MM-DD.md`

### Frontmatter Requirements
Every note MUST include:
```yaml
---
created: YYYY-MM-DDTHH:mm
modified: YYYY-MM-DDTHH:mm
type: daily | analysis | thesis | client | idea | review | report
tags: []
status: draft | active | archived
---
```

### Tags (Hierarchical)
- `#macro/fed`, `#macro/ecb`, `#macro/boj`, `#macro/pboc`
- `#sector/tech`, `#sector/semicon`, `#sector/energy`
- `#thesis/bull`, `#thesis/bear`, `#thesis/neutral`
- `#startup/idea`, `#startup/evaluation`, `#startup/pivot`
- `#source/mckinsey`, `#source/bcg`, `#source/a16z`
- `#action/todo`, `#action/followup`, `#action/decision`

### Linking Rules
- Use `[[wikilinks]]` for internal vault links
- Use `[[note|display text]]` for readable aliases
- Every note should have at least 2 backlinks
- Use `02-Investment/Thesis/IT-{name}` for thesis cross-references
- Tag client notes with `#client/{code}` for privacy separation

## Goals

### Short-term (1-3 months)
- 建立完整的 Second Brain 工作流程
- AVI V4 → V5 升級完成
- 累積 30+ 份 market analysis notes

### Medium-term (3-12 months)
- Yuni MVP 開發與市場驗證
- 量化交易系統 prototype
- 建立個人品牌內容管線

### Long-term (1-3 years)
- 從投資顧問轉型為 AI-native 創業者
- 打造可規模化的產品或服務
- 建立被動收入來源

## Claude Behavior in This Vault
- 回應以繁體中文為主，技術術語保留英文
- 分析時採用 MECE 架構
- 投資相關內容加上風險警語
- 不主動建立新檔案，除非明確要求
- 遵循上述檔案命名與 frontmatter 規則
````

---

## 4. McKinsey-Level Diagnosis Prompts（麥肯錫等級診斷 Prompts）

以下六個 prompt 為 production-ready，可直接貼入 Claude 使用。

### 4.1 殘酷商業診斷（Brutal Business Diagnosis）

```markdown
# 殘酷商業診斷 Prompt

你是一位擁有 20 年經驗的麥肯錫資深合夥人，專精 TMT（科技、媒體、電信）與金融服務產業。
你的任務是對以下商業構想進行毫不留情、但具建設性的診斷。

## 診斷對象
- 商業名稱：{business_name}
- 一句話描述：{one_liner}
- 目標市場：{target_market}
- 目前階段：{stage}
- 月營收/用戶數：{metrics}

## 診斷框架（請逐項分析）

### 1. 市場規模現實檢驗
- TAM/SAM/SOM 估算（附計算邏輯）
- 這個市場是否大到值得花 3-5 年？
- 市場成長率與驅動因子

### 2. 價值主張強度
- 用 Jobs-to-be-Done 框架分析核心價值
- 替代方案分析：客戶目前如何解決同樣問題？
- 從「nice to have」到「must have」的距離有多遠？

### 3. 商業模式可行性
- 單位經濟學：CAC、LTV、Payback Period 合理性
- 收入模式的可擴展性
- 毛利率結構是否支撐成長

### 4. 護城河評估
- 網路效應 / 規模經濟 / 轉換成本 / 品牌 / 數據優勢
- 誠實評分：1-10（10 = 幾乎不可能被模仿）

### 5. 團隊-市場契合度
- 創辦人的不公平優勢是什麼？
- 哪些關鍵能力缺口需要補？

### 6. 最終判決
- Kill / Pivot / Proceed（擇一）
- 如果 Proceed：最關鍵的 3 件事
- 如果 Pivot：建議方向
- 如果 Kill：為什麼，以及什麼類型的機會更適合這個團隊

## 輸出格式
請用表格、bullet points、與明確的數字佐證。避免模糊的鼓勵性語言。
如果數據不足以做判斷，明確指出需要什麼資訊。
```

### 4.2 創辦人盲點偵測器（Founder Blind Spot Finder）

```markdown
# 創辦人盲點偵測器 Prompt

你是一位經歷過 3 次創業（1 次成功 IPO、1 次被收購、1 次失敗）的連續創業家，
同時擔任 Y Combinator 客座合夥人。你的任務是找出創辦人的認知盲點。

## 創辦人背景
- 職業背景：{background}（例：金融投資顧問，7年經驗）
- 技術能力：{tech_skills}
- 創業經驗：{startup_exp}
- 最大的假設：{assumptions}

## 盲點偵測框架

### 1. 認知偏誤掃描
逐一檢驗以下偏誤是否存在：
- 確認偏誤（只看支持自己想法的證據）
- 沉沒成本謬誤
- 達克效應（高估自身能力）
- 倖存者偏誤（只看成功案例）
- 錨定效應
- 規劃謬誤（低估時間與成本）
- 為每個偏誤提供具體的「你可能正在犯這個錯」的場景

### 2. 經驗缺口分析
- 從你的背景來看，你最可能低估什麼？
- 「投資顧問思維」vs「創業者思維」的關鍵差異
- 你的優勢在哪些情境下反而是弱點？

### 3. 社交網路盲點
- 你的人脈圈是否足夠多元？
- 你缺少哪類人的觀點？（技術、設計、營運、法務）
- Echo Chamber 風險評估

### 4. 時間分配審計
- 你花最多時間在什麼上面？這正確嗎？
- 什麼事情你一直在「準備」但從未開始？
- 完美主義 vs. 速度的平衡點在哪？

### 5. 解毒處方
- 針對每個盲點，提供具體的矯正行動
- 推薦 3 本必讀的書（針對你的盲點）
- 建議 3 個應該定期做的「現實檢驗」儀式

## 語氣
直接、犀利、但帶有善意。像一位嚴格的導師，不是一位討好的顧問。
```

### 4.3 市場機會掃描器（Market Opportunity Scanner）

```markdown
# 市場機會掃描器 Prompt

你是一位專精於 FinTech 與 AI 交叉領域的市場研究分析師，
擁有 CB Insights、PitchBook、Crunchbase 等數據庫的深厚經驗。

## 掃描參數
- 領域：{domain}（例：AI + 個人理財 / 量化交易工具 / 投資教育）
- 地理範圍：{geography}（例：台灣 → 亞太 → 全球）
- 創辦人資源：{resources}（資金、時間、團隊規模）
- 時間範圍：{timeline}（6個月 / 12個月 / 24個月）

## 掃描框架

### 1. 趨勢矩陣
建立 3x3 矩陣：
- X 軸：市場成熟度（新興 / 成長 / 成熟）
- Y 軸：技術可行性（低 / 中 / 高）
- 標注每個機會的位置與市場規模

### 2. 競爭景觀地圖
- 現有玩家分類（Incumbent / Startup / Adjacent）
- 近 18 個月的融資事件與金額
- 哪些領域「過度競爭」、哪些「被忽略」？

### 3. 台灣特有機會
- 台灣法規環境的限制與機會
- 台灣消費者行為的獨特性
- 可以利用的在地優勢（語言、文化、監管套利）

### 4. 進入策略建議
- 對每個值得追的機會，建議：
  - 最小可行切入點
  - 首 100 個用戶從哪來
  - 12 個月里程碑
  - 需要的關鍵資源

### 5. 機會排名
以表格呈現 Top 5 機會：
| 排名 | 機會 | 市場規模 | 競爭程度 | 創辦人契合度 | 啟動難度 | 綜合評分 |

## 輸出要求
- 所有數據標註來源（即使是估算）
- 區分「事實」與「假設」
- 提供 bull case 和 bear case
```

### 4.4 收入模式壓力測試（Revenue Model Stress Test）

```markdown
# 收入模式壓力測試 Prompt

你是一位 SaaS metrics 專家，曾任 Bessemer Venture Partners 營運合夥人，
專門幫助早期團隊驗證商業模式的財務可行性。

## 產品資訊
- 產品名稱：{product}
- 定價模式：{pricing}（例：月訂閱 $X / 按次收費 / Freemium）
- 目標客群：{segment}
- 目前數據：{current_data}（用戶數、轉換率、ARPU 等）

## 壓力測試框架

### 1. 單位經濟學深度分析
- CAC（客戶獲取成本）拆解：各渠道成本
- LTV（客戶終身價值）計算：含 churn rate 敏感度分析
- LTV:CAC ratio 在不同場景下的表現：
  - 樂觀：churn 2%, CAC -20%
  - 基準：churn 5%, CAC as-is
  - 悲觀：churn 10%, CAC +50%

### 2. 定價策略審計
- 你的定價是基於「成本」、「價值」還是「競爭」？
- 價格彈性估算
- 價格分層建議（Good / Better / Best）
- 免費方案是助力還是阻力？

### 3. 規模化情境模擬
建立 24 個月的財務模型：
| 月份 | 新用戶 | 活躍用戶 | MRR | Gross Margin | Burn Rate | Runway |
- 三種情境：Conservative / Base / Aggressive

### 4. 收入多元化
- 核心收入流的脆弱性評估
- 可行的第二收入流建議
- 交叉銷售 / 追加銷售機會

### 5. 致命問題清單
- 這個模式能在沒有外部融資的情況下存活嗎？
- 達到盈虧平衡需要多少用戶？這現實嗎？
- 如果最大客戶/渠道消失，會怎樣？
- 這個定價在台灣市場是否合理？

## 輸出格式
使用表格和圖表描述。所有數字附計算過程。
明確標示哪些是假設（需要驗證）vs 事實（已有數據支持）。
```

### 4.5 競爭護城河分析器（Competitive Moat Analyzer）

```markdown
# 競爭護城河分析器 Prompt

你是一位 Hamilton Helmer（《7 Powers》作者）風格的策略顧問，
專精於分析新創公司的長期競爭優勢。

## 分析對象
- 公司/產品：{company}
- 所在市場：{market}
- 目前規模：{scale}
- 主要競爭者：{competitors}

## 護城河分析框架（7 Powers）

### 1. 規模經濟（Scale Economies）
- 你的成本結構是否隨規模顯著下降？
- 固定成本 vs 變動成本比例
- 規模經濟的「門檻」在哪裡？
- 評分：⬜⬜⬜⬜⬜（0-5）

### 2. 網路效應（Network Effects）
- 是否存在直接網路效應？（用戶越多 → 對每個用戶越有價值）
- 是否存在間接網路效應？（雙邊市場）
- 網路效應的強度與類型
- 評分：⬜⬜⬜⬜⬜（0-5）

### 3. 反向定位（Counter-Positioning）
- 你在做什麼「在位者不願意做」的事？
- 在位者模仿你的成本是什麼？（不只是錢，包括組織慣性）
- 這個窗口會持續多久？
- 評分：⬜⬜⬜⬜⬜（0-5）

### 4. 轉換成本（Switching Costs）
- 用戶遷移到競品的成本（時間、金錢、數據）
- 財務轉換成本 / 程序轉換成本 / 關係轉換成本
- 你能主動提高轉換成本嗎？（不靠鎖定，靠價值）
- 評分：⬜⬜⬜⬜⬜（0-5）

### 5. 品牌（Branding）
- 你的品牌能帶來定價權嗎？
- 品牌認知度 vs 品牌忠誠度
- 建立品牌護城河需要多長時間？
- 評分：⬜⬜⬜⬜⬜（0-5）

### 6. 壟斷性資源（Cornered Resource）
- 你擁有什麼獨特、不可複製的資源？
- 獨家數據 / 專利 / 人才 / 關係
- 評分：⬜⬜⬜⬜⬜（0-5）

### 7. 流程優勢（Process Power）
- 你的組織是否有難以模仿的流程或文化？
- 這需要時間累積，目前的進展如何？
- 評分：⬜⬜⬜⬜⬜（0-5）

### 綜合評估
- 護城河總評分（/35）
- 最強的 2 個維度是什麼？如何加強？
- 最弱的 2 個維度是什麼？是否需要擔心？
- 12 個月護城河建設路線圖

## 語氣
嚴謹的學術風格，但結論要直接可行動。
```

### 4.6 客戶痛點萃取器（Customer Pain Point Extractor）

```markdown
# 客戶痛點萃取器 Prompt

你是一位精通 Design Thinking 與 Jobs-to-be-Done 框架的產品策略顧問，
曾在 IDEO 與 Strategyzer 工作。你的目標是幫助創辦人從模糊的直覺中萃取出精確的客戶痛點。

## 目標客群
- 客群描述：{persona}
- 使用場景：{context}
- 現有替代方案：{alternatives}
- 創辦人的初始假設：{hypothesis}

## 萃取框架

### 1. 痛點層級分析
將痛點分為四個層級：
- **功能層**：具體任務無法完成或太麻煩
- **情緒層**：焦慮、挫折、不安全感
- **社會層**：形象、地位、歸屬感
- **財務層**：金錢損失、機會成本

### 2. 痛點強度量表
對每個痛點評估：
| 痛點 | 頻率 | 強度 | 願付價格 | 現有解法滿意度 | 總分 |
- 頻率：每天/每週/每月/每年
- 強度：1-10
- 願付價格：預估金額
- 現有解法滿意度：1-10（越低 = 機會越大）

### 3. Jobs-to-be-Done 拆解
- 核心 Job：客戶「雇用」你的產品來完成什麼任務？
- 相關 Jobs：順帶完成的次要任務
- 情緒 Jobs：讓客戶「感覺」如何？
- 社會 Jobs：讓別人「看到」客戶如何？

### 4. 反面驗證
- 如果這個痛點明天消失，客戶會注意到嗎？
- 客戶是否已經在花錢/時間解決這個問題？
- 這是「維他命」還是「止痛藥」？
- 哪些信號可以證偽你的痛點假設？

### 5. 痛點優先級矩陣
2x2 矩陣：
- X 軸：解決難度（低 → 高）
- Y 軸：客戶價值（低 → 高）
- 標注每個痛點的位置
- 右上角 = 護城河機會
- 左上角 = Quick Win

### 6. 驗證實驗設計
針對 Top 3 痛點，各設計一個：
- 最小化驗證實驗（< 1 週、< $100）
- 成功/失敗的明確標準
- 需要訪談的人數與對象

## 輸出要求
用客戶的語言描述痛點（不是產品語言）。
區分「創辦人認為的痛點」和「客戶實際的痛點」。
```

---

## 5. Report Intelligence Pipeline

### 5.1 Free Sources（免費資訊來源）

| 來源 | 類型 | 頻率 | RSS/URL | 標籤 |
|------|------|------|---------|------|
| McKinsey Insights | 策略/產業 | 每週 | mckinsey.com/insights | `#source/mckinsey` |
| BCG Henderson Institute | 策略/創新 | 每週 | bcghendersoninstitute.com | `#source/bcg` |
| Bain Brief | 策略/營運 | 每月 | bain.com/insights | `#source/bain` |
| a16z Blog | 科技/VC | 每週 | a16z.com/blog | `#source/a16z` |
| CB Insights Research | 市場數據 | 每週 | cbinsights.com/research | `#source/cbinsights` |
| IMF Working Papers | 總經 | 每月 | imf.org/publications | `#source/imf` |
| BIS Quarterly Review | 央行/金融 | 每季 | bis.org/publ | `#source/bis` |
| Fed FRED Blog | 美國總經 | 每週 | fredblog.stlouisfed.org | `#source/fed` |
| Sequoia Arc | 創業指南 | 不定期 | sequoiacap.com/arc | `#source/sequoia` |
| First Round Review | 營運/管理 | 每週 | review.firstround.com | `#source/firstround` |
| Stratechery (free tier) | 科技策略 | 每週 | stratechery.com | `#source/stratechery` |
| Matt Levine (Bloomberg) | 金融幽默 | 每日 | bloomberg.com/opinion | `#source/levine` |
| Taiwan DGBAS | 台灣經濟數據 | 每月 | dgbas.gov.tw | `#source/dgbas` |
| 台灣央行 | 貨幣政策 | 每季 | cbc.gov.tw | `#source/cbc` |

### 5.2 Weekly Scan Workflow（每週情報掃描流程）

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  RSS Feed   │────▶│  Skim &      │────▶│  Create Note │────▶│  Link to    │
│  Aggregator │     │  Highlight   │     │  RS-{source} │     │  Idea       │
│             │     │  Key Points  │     │  -YYYY-MM-DD │     │  Backlog    │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │  Auto-tag    │
                                         │  by Category │
                                         └──────────────┘
```

**Weekly Scan 步驟：**

1. **週一早晨（30 min）**：瀏覽 RSS feed，標記值得深讀的文章
2. **每日零碎時間**：閱讀標記文章，用 `tpl-report-summary` 建立筆記
3. **週五回顧時**：檢視本週報告，連結到相關 idea 或 thesis

### 5.3 Auto-Tagging Rules

根據報告內容自動套用標籤的規則：

```yaml
auto_tag_rules:
  keywords_to_tags:
    - keywords: [AI, artificial intelligence, LLM, GPT, Claude]
      tag: "#topic/ai"
    - keywords: [fintech, payment, banking, neobank]
      tag: "#topic/fintech"
    - keywords: [Taiwan, 台灣, TSMC, semiconductor]
      tag: "#topic/taiwan"
    - keywords: [crypto, blockchain, DeFi, web3]
      tag: "#topic/crypto"
    - keywords: [SaaS, subscription, ARR, MRR]
      tag: "#topic/saas"
    - keywords: [startup, founder, seed, Series A]
      tag: "#topic/startup"
    - keywords: [macro, GDP, inflation, interest rate]
      tag: "#topic/macro"
    - keywords: [quantitative, algorithm, backtest]
      tag: "#topic/quant"
```

### 5.4 Idea Backlog Linking

每份報告摘要底部包含：

```markdown
## Idea Sparks
- 這篇報告啟發了什麼新想法？
- 連結到現有 idea：[[03-Startup/Idea-Backlog/SI-xxx]]
- 是否需要建立新 idea？→ 用 `tpl-startup-idea-evaluation`
```

---

## 6. Obsidian Templates

### 6.1 tpl-daily-journal

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: daily
tags: [daily]
status: active
mood: 
energy: /10
---

# {{date:YYYY-MM-DD}} {{date:dddd}}

## Morning Check-in
- 今天最重要的 3 件事：
  1. 
  2. 
  3. 
- 身體狀態：
- 心理狀態：

## Market Pulse
- 昨夜美股：
- 亞洲盤勢：
- 關鍵數據/事件：
- 我的觀點：

## Work Log
### 投資顧問
- 

### Side Projects
- [ ] 
- [ ] 

## Idea Capture
> 今天冒出的任何想法，不管多瘋狂

## Learning
- 今天讀了/學了什麼？
- 連結：

## Evening Reflection
- 今天最大的收穫：
- 明天要改進的一件事：
- 感恩清單：
  1. 
  2. 
  3. 

---
*Linked Notes:*
```

### 6.2 tpl-market-analysis

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: analysis
tags: [analysis]
status: draft
market: 
timeframe: 
conviction: /10
---

# Market Analysis: {{title}}

## Executive Summary
> 一段話總結核心觀點

## Macro Context
- 利率環境：
- 通膨趨勢：
- 經濟週期位置：
- 地緣政治風險：

## Sector Analysis
### 驅動因子
1. 
2. 
3. 

### 壓制因子
1. 
2. 
3. 

## Data Points
| 指標 | 數值 | 趨勢 | 意義 |
|------|------|------|------|
|      |      |      |      |

## Technical View
- 關鍵價位：
- 型態觀察：
- 量能分析：

## Investment Implications
### Bull Case
- 

### Bear Case
- 

### Base Case
- 

## Action Items
- [ ] 
- [ ] 

## Risk Factors
1. 
2. 

## Sources
- 

---
*Related Thesis:* [[]]
*Related Notes:* [[]]
```

### 6.3 tpl-startup-idea-evaluation

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: idea
tags: [startup/idea]
status: draft
idea_id: SI-
score: /100
verdict: kill | pivot | explore | build
---

# Startup Idea: {{title}}

## One-Liner
> 

## Problem Statement
- 誰有這個問題？
- 問題有多痛？（1-10）
- 目前怎麼解決？
- 為什麼現有解法不夠好？

## Proposed Solution
- 核心功能：
- 差異化：
- 技術可行性：

## Market Sizing
| 層級 | 規模 | 計算邏輯 |
|------|------|----------|
| TAM  |      |          |
| SAM  |      |          |
| SOM  |      |          |

## Competitive Landscape
| 競爭者 | 優勢 | 劣勢 | 定價 |
|--------|------|------|------|
|        |      |      |      |

## Business Model
- 收入模式：
- 定價策略：
- 預估 CAC：
- 預估 LTV：

## Founder-Market Fit
- 我的不公平優勢：
- 我的能力缺口：
- 需要的團隊成員：

## Quick Scorecard
| 維度 | 分數 (1-10) | 備註 |
|------|-------------|------|
| 問題強度 | | |
| 市場規模 | | |
| 解法獨特性 | | |
| 商業可行性 | | |
| 創辦人契合 | | |
| 時機 | | |
| 護城河潛力 | | |
| 興奮程度 | | |
| **總分** | **/80** | |

## Next Steps
- [ ] 驗證實驗 1：
- [ ] 驗證實驗 2：
- [ ] 找 5 個潛在用戶聊聊

## Decision Log
| 日期 | 決定 | 原因 |
|------|------|------|
|      |      |      |

---
*Inspired by:* [[]]
*Related Ideas:* [[]]
```

### 6.4 tpl-client-meeting

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: client
tags: [client]
status: active
client_code: 
meeting_type: regular | adhoc | review
---

# Client Meeting: {{date:YYYY-MM-DD}}

## Meeting Info
- 客戶代碼：
- 日期時間：{{date:YYYY-MM-DD HH:mm}}
- 地點/形式：
- 參與者：

## Agenda
1. 
2. 
3. 

## Portfolio Review
| 資產類別 | 配置比重 | 報酬率 | 備註 |
|----------|----------|--------|------|
|          |          |        |      |

## Key Discussion Points
### 客戶關注
- 

### 我的建議
- 

### 市場觀點分享
- 

## Action Items
- [ ] 我要做：
- [ ] 客戶要做：

## Risk Flags
- 客戶情緒：穩定 / 焦慮 / 貪婪 / 恐懼
- 合規注意事項：
- 適合度確認：

## Follow-up
- 下次會議：
- 需要準備的資料：

---
*Related Analysis:* [[]]
*Previous Meeting:* [[]]
```

### 6.5 tpl-weekly-review

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: review
tags: [review/weekly]
status: draft
week: {{date:YYYY}}-W{{date:ww}}
---

# Weekly Review: {{date:YYYY}}-W{{date:ww}}

## Wins This Week
1. 
2. 
3. 

## Challenges & Lessons
1. 
2. 

## Key Metrics
| 指標 | 本週 | 上週 | 趨勢 |
|------|------|------|------|
| 客戶會議數 | | | |
| 深度分析篇數 | | | |
| Side Project 進度 | | | |
| 學習時數 | | | |
| 運動次數 | | | |

## Market Recap
- 本週重大事件：
- 市場趨勢變化：
- 對投資組合的影響：

## Project Progress
### AVI
- 

### Yuni
- 

### Quant
- 

### KIWI
- 

## Idea Pipeline
- 新增想法：
- 淘汰想法：
- 正在驗證：

## Content & Learning
- 本週讀了：
- 本週學了：
- 值得分享的：

## Next Week Plan
### Top 3 Priorities
1. 
2. 
3. 

### Meetings & Deadlines
- 

### 要避免的事
- 

## Personal
- 能量水平：/10
- 整體滿意度：/10
- 需要調整的：

---
*Previous Review:* [[]]
```

### 6.6 tpl-report-summary

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: report
tags: [report]
status: draft
source: 
source_url: 
publish_date: 
read_time: min
relevance: /10
---

# Report Summary: {{title}}

## Source Info
- 來源：
- 作者：
- 發布日期：
- 原文連結：

## Key Takeaways
1. 
2. 
3. 

## Summary
> 3-5 句話摘要核心論點

## Important Data Points
| 數據 | 數值 | 含義 |
|------|------|------|
|      |      |      |

## Quotes Worth Keeping
> 

## My Analysis
- 同意的部分：
- 不同意的部分：
- 需要進一步研究的：

## Relevance to My Work
- 對投資觀點的影響：
- 對創業想法的啟發：
- 可以分享給客戶嗎？是 / 否

## Idea Sparks
- 這篇報告啟發了什麼新想法？
- 連結到現有 idea：[[]]
- 是否需要建立新 idea？

## Tags Applied
- 

---
*Related Reports:* [[]]
*Related Thesis:* [[]]
```

### 6.7 tpl-investment-thesis

```markdown
---
created: {{date:YYYY-MM-DDTHH:mm}}
modified: {{date:YYYY-MM-DDTHH:mm}}
type: thesis
tags: [thesis]
status: draft
thesis_type: bull | bear | neutral
asset_class: 
timeframe: 
conviction: /10
last_reviewed: 
---

# Investment Thesis: {{title}}

## Thesis Statement
> 一句話表達核心論述

## Bull / Bear / Neutral Case

### Core Argument
1. 
2. 
3. 

### Supporting Evidence
| 證據 | 來源 | 強度 | 日期 |
|------|------|------|------|
|      |      |      |      |

### Counter-Arguments
1. 
2. 

### Counter-Counter-Arguments
1. 
2. 

## Key Assumptions
- [ ] 假設 1：（已驗證 / 待驗證 / 已推翻）
- [ ] 假設 2：
- [ ] 假設 3：

## Catalyst Timeline
| 事件 | 預期日期 | 影響 | 機率 |
|------|----------|------|------|
|      |          |      |      |

## Position Sizing Framework
- 最大配置比重：
- 進場條件：
- 加碼條件：
- 停損條件：
- 停利條件：

## Monitoring Checklist
- [ ] 每日：檢查價格/關鍵指標
- [ ] 每週：重新評估論述有效性
- [ ] 每月：更新假設驗證狀態
- [ ] 觸發事件：

## Thesis Health Score
| 維度 | 初始評分 | 目前評分 | 趨勢 |
|------|----------|----------|------|
| 證據強度 | | | |
| 市場認同度 | | | |
| 時機正確性 | | | |
| 風險報酬比 | | | |

## Decision Log
| 日期 | 行動 | 原因 | 結果 |
|------|------|------|------|
|      |      |      |      |

---
*Related Analysis:* [[]]
*Related Reports:* [[]]
*Conflicting Thesis:* [[]]
```

---

## 7. Integration Points

### 7.1 Vault ↔ KIWI

```
~/SecondBrain/07-KIWI/ → symlink → ~/KIWI/
```

| 整合點 | 方向 | 說明 |
|--------|------|------|
| 專案筆記 | Vault → KIWI | 在 vault 寫的專案想法可連結到 KIWI 的具體 task |
| 開發日誌 | KIWI → Vault | KIWI 的 commit log 可在 vault 中追蹤 |
| Skills | 雙向 | `05-AI-Toolkit/Claude-Skills/` 與 `KIWI/projects/skills/` 同步 |
| 文件 | KIWI → Vault | KIWI 的 ARCHITECTURE.md 等文件可從 vault 直接讀取 |

### 7.2 Vault ↔ AVI V4/V5

| 整合點 | 說明 |
|--------|------|
| 投資論述 | `02-Investment/Thesis/` 的筆記可作為 AVI prompt context |
| 市場分析 | `02-Investment/Market-Analysis/` 提供 AVI 的背景知識 |
| 開發日誌 | `02-Investment/AVI-Log/` 記錄 AVI 的開發進展 |
| 回測結果 | AVI 的輸出存入 `02-Investment/Market-Analysis/` |

### 7.3 Vault ↔ IG Saved Posts

```
IG Saved Posts → Manual/Semi-auto extraction → 00-Inbox/ig-saved/
```

**流程：**
1. 在 IG 儲存有價值的貼文
2. 定期（每週一次）匯出儲存貼文的重點
3. 使用 `tpl-report-summary` 建立筆記
4. 標籤 `#source/ig` + 主題標籤
5. 連結到相關的 idea 或 thesis

---

## 8. Daily / Weekly Workflow

### 8.1 Morning Routine（早晨流程，30-45 min）

```
06:30  起床、運動
07:15  ☕ 開始 Morning Routine
       │
       ├── [5 min]  建立今日 Daily Note（tpl-daily-journal）
       ├── [10 min] Market Pulse：掃描隔夜市場
       │            - 美股三大指數、VIX
       │            - 亞洲期貨、匯率
       │            - 重大新聞/數據
       ├── [10 min] 設定今日 Top 3 Priorities
       ├── [10 min] 瀏覽 RSS feed，標記值得讀的文章
       └── [5 min]  檢查行事曆、確認今日會議
08:00  開始正式工作
```

### 8.2 Evening Routine（晚間流程，15 min）

```
21:30  Evening Routine
       │
       ├── [5 min]  回顧今日 Daily Note
       │            - 完成了什麼？
       │            - 有什麼遺漏？
       ├── [5 min]  Idea Capture
       │            - 記錄白天冒出的想法
       │            - 不做判斷，只記錄
       └── [5 min]  Evening Reflection
                    - 今天的收穫
                    - 明天要改進的
                    - 感恩清單
22:00  結束螢幕時間
```

### 8.3 Friday Review（週五回顧，60-90 min）

```
Friday 14:00  Weekly Review
              │
              ├── [15 min] 回顧本週所有 Daily Notes
              │            - 統計完成的任務
              │            - 識別模式與趨勢
              ├── [15 min] Market Recap
              │            - 本週重大事件
              │            - 投資組合表現
              │            - 論述更新
              ├── [15 min] Project Progress
              │            - AVI / Yuni / Quant / KIWI 進度
              │            - 是否 on track？
              ├── [15 min] Report & Learning Review
              │            - 本週讀了什麼？
              │            - 新想法 → Idea Backlog
              ├── [10 min] Idea Pipeline Review
              │            - 新增/淘汰/正在驗證
              │            - 用 scoring 排優先級
              └── [10 min] Next Week Planning
                           - Top 3 Priorities
                           - 會議準備
                           - 要避免的事
```

---

## 9. Setup Instructions

### 9.1 Required Obsidian Plugins

| Plugin | 用途 | 優先級 |
|--------|------|--------|
| **Templater** | 模板系統，支援日期變數與腳本 | 必裝 |
| **Dataview** | 將 vault 當資料庫查詢，建立動態表格 | 必裝 |
| **Calendar** | 日曆介面，快速跳到 Daily Notes | 必裝 |
| **Tag Wrangler** | 批量管理、重命名標籤 | 必裝 |
| **Obsidian Git** | 自動 git 備份 vault | 必裝 |
| **Natural Language Dates** | 自然語言輸入日期 | 推薦 |
| **Kanban** | 看板管理 Idea Backlog | 推薦 |
| **Excalidraw** | 手繪圖表、架構圖 | 推薦 |
| **Periodic Notes** | 週/月回顧筆記管理 | 推薦 |

### 9.2 Obsidian Settings

```
Settings > Files & Links:
  - Default location for new notes: 00-Inbox
  - New link format: Relative path to file
  - Use [[Wikilinks]]: ON

Settings > Templates (Core Plugin):
  - Template folder location: Templates

Settings > Templater:
  - Template folder location: Templates
  - Trigger on new file creation: ON

Settings > Dataview:
  - Enable JavaScript Queries: ON
  - Enable Inline Queries: ON

Settings > Obsidian Git:
  - Auto backup interval: 30 minutes
  - Auto pull interval: On startup
  - Commit message: vault backup: {{date}}
```

### 9.3 Symlink Setup

```bash
# 建立 KIWI symlink
ln -s ~/KIWI ~/SecondBrain/07-KIWI

# 驗證
ls -la ~/SecondBrain/07-KIWI
# 應該顯示 -> /home/user/KIWI
```

### 9.4 Git Initialization

```bash
# 初始化 vault 的 git repo
cd ~/SecondBrain
git init
git branch -M main

# 建立 .gitignore
cat > .gitignore << 'EOF'
# Obsidian
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/recent-files-obsidian/data.json
.trash/
.DS_Store

# KIWI symlink (managed separately)
07-KIWI/

# Sensitive data
02-Investment/Client-Notes/

# Large files
Assets/pdfs/*.pdf
EOF

# 初次 commit
git add -A
git commit -m "Initial vault setup"

# 設定 remote（選用）
# git remote add origin git@github.com:username/second-brain.git
# git push -u origin main
```

### 9.5 Folder Creation Script

```bash
#!/bin/bash
# setup-vault.sh — 一鍵建立 Second Brain 資料夾結構

VAULT=~/SecondBrain

mkdir -p "$VAULT"/{00-Inbox/{fleeting-notes,web-clips,ig-saved},01-Daily,02-Investment/{Market-Analysis,Thesis,Macro,Client-Notes,AVI-Log},03-Startup/{Idea-Backlog,Evaluations,Yuni,Competitive-Intel},04-Learning/{Articles,Books,Reports,Courses},05-AI-Toolkit/{Prompts,Workflows,Claude-Skills},06-Weekly-Review,Templates,Assets/{images,pdfs}}

# 建立 KIWI symlink
ln -sf ~/KIWI "$VAULT/07-KIWI"

# 複製模板（假設模板已存在）
echo "Vault structure created at $VAULT"
echo "Next steps:"
echo "  1. Open $VAULT in Obsidian"
echo "  2. Install required plugins"
echo "  3. Copy templates to $VAULT/Templates/"
echo "  4. Create CLAUDE.md in vault root"
```

### 9.6 Dataview 常用查詢

放在任何筆記中即可使用：

**最近 7 天的 Daily Notes：**
````markdown
```dataview
TABLE mood, energy
FROM "01-Daily"
WHERE date(created) >= date(today) - dur(7 days)
SORT created DESC
```
````

**所有進行中的 Startup Ideas：**
````markdown
```dataview
TABLE score, verdict
FROM "03-Startup/Idea-Backlog"
WHERE status = "active"
SORT score DESC
```
````

**本週讀過的報告：**
````markdown
```dataview
TABLE source, relevance
FROM "04-Learning"
WHERE type = "report" AND date(created) >= date(today) - dur(7 days)
SORT relevance DESC
```
````

**待處理的 Inbox 項目：**
````markdown
```dataview
LIST
FROM "00-Inbox"
WHERE status = "draft"
SORT created ASC
```
````

---

## Appendix: Quick Reference

### File Naming Cheat Sheet

| 類型 | 格式 | 範例 |
|------|------|------|
| Daily | `YYYY-MM-DD.md` | `2026-05-10.md` |
| Market Analysis | `MA-YYYY-MM-DD-{topic}.md` | `MA-2026-05-10-fed-rate.md` |
| Investment Thesis | `IT-{ticker-or-theme}.md` | `IT-tsmc-ai-capex.md` |
| Client Notes | `CN-YYYY-MM-DD-{code}.md` | `CN-2026-05-10-A001.md` |
| Startup Idea | `SI-{id}-{name}.md` | `SI-003-ai-advisor.md` |
| Weekly Review | `WR-YYYY-WNN.md` | `WR-2026-W19.md` |
| Report Summary | `RS-{source}-YYYY-MM-DD.md` | `RS-mckinsey-2026-05-10.md` |

### Tag Hierarchy

```
#macro/          → fed, ecb, boj, pboc, cbc
#sector/         → tech, semicon, energy, finance, healthcare
#thesis/         → bull, bear, neutral
#startup/        → idea, evaluation, pivot, kill
#source/         → mckinsey, bcg, a16z, cbinsights, ig
#topic/          → ai, fintech, taiwan, crypto, saas, quant
#action/         → todo, followup, decision, blocked
#client/         → {client-code}
#review/         → weekly, monthly, quarterly
#project/        → avi, yuni, quant, kiwi
```

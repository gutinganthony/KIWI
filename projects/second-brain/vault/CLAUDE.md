# CLAUDE.md — Second Brain Vault

## Who I Am

我是一位在台灣的金融投資顧問（IG: @afternoon.jk / GitHub: gutinganthony），專注於總經分析與投資組合管理。
目前同時探索 AI-native 創業機會，身兼投資顧問與獨立開發者。

## Current Projects

| Project | Status | Score/Stage | Location |
|---------|--------|-------------|----------|
| **AVI V4** | Active development | 6.73 score | `07-KIWI/projects/avi-v5/` |
| **Yuni** | Concept exploration | 命理戀愛平台 | `03-Startup/Yuni/` |
| **Quant Projects** | Research phase | Multiple strategies | `07-KIWI/projects/quant/` |
| **KIWI** | Infrastructure | Active | `07-KIWI/` |
| **Second Brain** | This system | Active | `07-KIWI/projects/second-brain/` |

## Vault Structure

```
~/SecondBrain/
├── CLAUDE.md                    # 本文件 — Claude Code vault 指引
├── 00-Inbox/                    # 快速捕捉（fleeting notes, web clips, IG saved）
├── 01-Daily/                    # 每日日誌（按 YYYY-MM 分月）
├── 02-Investment/               # 投資相關（Market Analysis, Thesis, Macro, Client, AVI）
├── 03-Startup/                  # 創業探索（Idea Backlog, Evaluations, Yuni, Competitive Intel）
├── 04-Learning/                 # 學習資源（Articles, Books, Reports, Courses）
├── 05-AI-Toolkit/               # AI 工具箱（Prompts, Workflows, Claude Skills）
├── 06-Weekly-Review/            # 週回顧（按 YYYY-WNN 命名）
├── 07-KIWI/                     # → symlink to ~/KIWI
├── Templates/                   # Obsidian Templater 模板
└── Assets/                      # 附件（images, pdfs）
```

## File Naming Conventions

| 類型 | 格式 | 範例 |
|------|------|------|
| Daily | `YYYY-MM-DD.md` | `2026-05-10.md` |
| Market Analysis | `MA-YYYY-MM-DD-{topic}.md` | `MA-2026-05-10-fed-rate.md` |
| Investment Thesis | `IT-{ticker-or-theme}.md` | `IT-tsmc-ai-capex.md` |
| Client Notes | `CN-YYYY-MM-DD-{code}.md` | `CN-2026-05-10-A001.md` |
| Startup Idea | `SI-{id}-{name}.md` | `SI-003-ai-advisor.md` |
| Weekly Review | `WR-YYYY-WNN.md` | `WR-2026-W19.md` |
| Report Summary | `RS-{source}-YYYY-MM-DD.md` | `RS-mckinsey-2026-05-10.md` |

## Frontmatter Standard

Every note MUST include the following frontmatter:

```yaml
---
type: daily | analysis | thesis | client | idea | review | report | prompt
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
tags: []
status: draft | active | archived
related: []
---
```

Additional fields by type:
- `analysis`: conviction (/10), timeframe, market
- `thesis`: thesis_type (bull/bear/neutral), asset_class, last_reviewed
- `idea`: idea_id, score (/100), verdict (kill/pivot/explore/build)
- `client`: client_code, meeting_type
- `review`: week (YYYY-WNN)
- `report`: source, source_url, relevance (/10)

## Tag System

```
#macro/          → fed, ecb, boj, pboc, cbc (央行/總經)
#sector/         → tech, semicon, energy, finance, healthcare
#thesis/         → bull, bear, neutral
#startup/        → idea, evaluation, pivot, kill
#source/         → mckinsey, bcg, a16z, cbinsights, ig
#topic/          → ai, fintech, taiwan, crypto, saas, quant
#action/         → todo, followup, decision, blocked
#client/         → {client-code}
#review/         → weekly, monthly, quarterly
#project/        → avi, yuni, quant, kiwi
#investment      → 投資相關通用標籤
#startup         → 創業相關通用標籤
#quant           → 量化交易
#avi-v4          → AVI 系統開發
#yuni            → Yuni 專案
```

## Linking Rules

- Use `[[wikilinks]]` for internal vault links
- Use `[[note|display text]]` for readable aliases
- Every note should have at least 2 backlinks
- Cross-reference KIWI: `[[07-KIWI/projects/avi-v5/README|AVI V5]]`
- Tag client notes with `#client/{code}` for privacy separation
- Use `02-Investment/Thesis/IT-{name}` for thesis cross-references
- Link reports to ideas: every report summary should connect to Idea Backlog if relevant

## Goals

### Short-term (6 months)
- 建立完整的 Second Brain 工作流程，養成每日使用習慣
- AVI V4 → V5 升級完成（目標 score > 7.5）
- 累積 30+ 份 market analysis notes
- Yuni MVP 完成初步市場驗證
- 完成 50+ 份報告摘要，建立情報資料庫

### Medium-term (1-2 years)
- Yuni 正式上線並取得首批付費用戶
- 量化交易系統 live trading 階段
- 建立個人品牌內容管線（IG + Newsletter）
- 客戶 AUM 成長 50%
- Second Brain 累積 500+ 互聯筆記

### Long-term (3-5 years)
- 從投資顧問轉型為 AI-native 創業者
- 打造可規模化的 SaaS 產品（MRR > $10K USD）
- 建立被動收入來源（量化 + 產品）
- 成為台灣 AI × Finance 領域的意見領袖

## Claude Behavior in This Vault

- 回應以繁體中文為主，技術術語保留英文
- 分析時採用 MECE 架構
- 投資相關內容加上風險警語
- 不主動建立新檔案，除非明確要求
- 遵循上述檔案命名與 frontmatter 規則
- 建議連結相關筆記時，使用完整的 vault 路徑
- 對創業想法保持建設性但誠實的態度

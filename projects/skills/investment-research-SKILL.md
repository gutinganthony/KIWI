---
name: investment-research
description: Research and verify investment thesis, market claims, or analyst reports. Use when the user shares an article, chart, social media post, or investment idea and wants it analyzed, verified with data, and stored in KIWI. Also use when user asks to check market conditions using AVI/CPI/TSI systems.
---

# Investment Research & Verification Skill

## When to use
- User shares an article/post and says "幫我驗證" or "加入KIWI"
- User asks about current market conditions or risk levels
- User wants to analyze a stock, sector, or macro thesis
- User asks "這個說法合理嗎" about any investment claim

## Step 1: Understand the claim
Extract the core thesis in one sentence. Identify:
- What is being claimed?
- What timeframe?
- What assets/sectors affected?
- Who is making the claim? (credibility check)

## Step 2: Verify with data
Use WebSearch to find:
1. Supporting evidence (at least 3 data points)
2. Contradicting evidence (at least 2 data points)
3. Historical precedent (has this pattern happened before?)

Present as a table:
| 論點 | 數據 | 來源 |

## Step 3: Cross-reference with KIWI
Check if this connects to existing KIWI entries:
- `topics/business/2026-04-07-photonics-*` (光子投資)
- `topics/business/2026-05-16-ai-memory-*` (記憶體分析)
- `topics/business/2026-05-17-hbm-*` (HBM 光互連)
- `topics/business/2026-05-17-socamm-*` (SoCAMM 供需)
- `topics/business/2026-05-17-h2-investment-*` (投資策略)
- `topics/business/2026-05-17-tsi-backtest-*` (TSI + 歷史信號)

## Step 4: Rate plausibility
Score 1-10 with explanation:
- 8-10: 強烈支持，數據充分
- 6-7: 合理但有保留
- 4-5: 一半一半
- 1-3: 數據不支持

## Step 5: Investment implication
- How does this affect the user's H2 2026 strategy?
- Any changes to AVI/CPI/TSI monitoring?
- Specific tickers to watch or avoid?
- Timeline (when does this matter?)

## Step 6: Store in KIWI
Create a KIWI entry at `topics/business/YYYY-MM-DD-{slug}.md` with:
- YAML frontmatter (title, url, source, date_added, topic, tags)
- Summary
- Evidence tables (pro and con)
- Cross-references to existing KIWI entries
- Investment implications
- Update Log

Always commit and push after creating the entry.

## Output format
Use Traditional Chinese (繁體中文) for the KIWI entry.
Use the user's language for conversation.
Always end with: "要把這份分析存入 KIWI 嗎？" unless user already said to store it.

## Market condition check
When user asks about current market:
```
AVI V5: X.X/10 — [interpretation]
CPI:    XX/100 — [interpretation]  
TSI:    XX/100 — [interpretation]

Combined signal: [action guidance from H2 strategy]
```

Reference: `topics/business/2026-05-17-h2-investment-strategy.md` for decision rules.

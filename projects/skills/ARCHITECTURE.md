# /evaluate-idea Skill Architecture

## What It Does

The `/evaluate-idea` skill is a structured startup and side-business evaluator for Claude Code. It walks through a four-phase process to score an idea across eight dimensions drawn from Paul Graham's essays, YC's vertical AI thesis, a16z's 2026 investment themes, and real niche launch case studies. The output is a single Launch Confidence Score (0-100) with a clear verdict: LAUNCH, BUILD MVP, RESEARCH MORE, or KILL IT.

## Installation

```bash
mkdir -p ~/.claude/skills/evaluate-idea
cp evaluate-idea-SKILL.md ~/.claude/skills/evaluate-idea/SKILL.md
```

Once installed, invoke with `/evaluate-idea` in any Claude Code session.

## Scoring Framework

The skill evaluates ideas across eight dimensions:

| # | Dimension | Type | Weight |
|---|-----------|------|--------|
| 1 | Paul Graham Score | 0-10 (3 sub-tests) | x1.5 |
| 2 | Niche Focus Score | 0-10 | x1.5 |
| 3 | Revenue Model Clarity | 0-10 | x1.5 |
| 4 | Schlep Filter Check | Boolean (PASSES/FAILS) | 10 or 0 |
| 5 | Unsexy Filter Check | Boolean (PASSES/FAILS) | 10 or 0 |
| 6 | Founder-Market Fit | 0-10 | x1.5 |
| 7 | AI Leverage Score | 0-10 | x1.0 |
| 8 | a16z/YC Alignment | FULL/PARTIAL/NONE | 10/5/0 |

**Formula**: `PG*1.5 + Niche*1.5 + Revenue*1.5 + FounderFit*1.5 + AI*1.0 + Schlep + Unsexy + a16z_YC`

Maximum possible score: 100. Verdicts: 75-100 LAUNCH, 55-74 BUILD MVP, 35-54 RESEARCH MORE, 0-34 KILL IT.

## Example: AVI V4 as SaaS for Retail Investors

**Idea**: Turn the personal AVI V4 market risk tool into a subscription SaaS product for retail self-directed equity investors.

### Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Paul Graham Score | 8/10 | Built for personal use (3.33), can build it solo (3.33), non-obvious for retail investors (1.33) |
| Niche Focus | 7/10 | Retail self-directed equity investors — specific but not hyper-niche |
| Revenue Model Clarity | 8/10 | $9.99/mo basic, $29.99/mo pro; 1000 users = ~$15K MRR |
| Founder-Market Fit | 10/10 | Founder IS the target user and has investment advisory background |
| AI Leverage | 6/10 | AI assists data collection and summarization but core value is the quantitative model |

### Filter Checks

| Filter | Result | Reasoning |
|--------|--------|-----------|
| Schlep Filter | PASSES | Financial data pipelines, broker integrations, and regulatory compliance are tedious work most founders avoid |
| Unsexy Filter | PASSES | A monthly risk score dashboard is not viral or cool; tech founders chase flashier fintech ideas |
| a16z/YC Alignment | PARTIAL | Adjacent to "AI-native banking and financial services" but focused on risk analytics, not full banking |

### Launch Confidence Calculation

```
PG:         8  x 1.5 = 12.0
Niche:      7  x 1.5 = 10.5
Revenue:    8  x 1.5 = 12.0
FounderFit: 10 x 1.5 = 15.0
AI:         6  x 1.0 =  6.0
Schlep:     PASSES   = 10.0
Unsexy:     PASSES   = 10.0
a16z/YC:    PARTIAL  =  5.0
                       -----
Total:                 80.5
```

**Launch Confidence: 80.5/100 — LAUNCH**

### Suggested MVP (1 Weekend)

- Static landing page showing AVI composite risk score + radar chart visualization
- Stripe integration at $9.99/mo for basic access
- Email newsletter delivering weekly risk snapshots
- Deploy on Vercel, collect emails, track conversion from visitor to paid subscriber

# Second Brain — Obsidian Vault Starter Kit

A portable Obsidian vault designed for a financial investment advisor exploring AI-native entrepreneurship. Integrates with Claude Code and the KIWI project management framework.

## What This Is

A complete knowledge management system built on Obsidian, including:

- **7 folder structure** (Inbox, Daily, Investment, Startup, Learning, AI-Toolkit, Weekly Review)
- **7 Templater templates** (daily journal, market analysis, startup idea evaluation, client meeting, weekly review, report summary, investment thesis)
- **6 diagnosis prompts** (brutal business diagnosis, founder blind spot finder, market opportunity scanner, revenue model stress test, competitive moat analyzer, customer pain point extractor)
- **Report Intelligence Pipeline** workflow with 14 free sources
- **CLAUDE.md** context file for Claude Code integration

## Quick Start

```bash
# From the KIWI repo
cd projects/second-brain

# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

The script will:
1. Create `~/SecondBrain/` with full folder structure
2. Copy all templates, prompts, and workflows
3. Create a symlink to your KIWI repo
4. Initialize git with appropriate .gitignore
5. Print plugin installation instructions

### Custom paths

```bash
# Use custom vault location
SECOND_BRAIN_PATH=~/Documents/MyVault ./setup.sh

# Use custom KIWI location
KIWI_PATH=/path/to/kiwi ./setup.sh
```

## Required Obsidian Plugins

| Plugin | Purpose | Priority |
|--------|---------|----------|
| Templater | Template system with date variables and scripts | Required |
| Dataview | Query vault as database, dynamic tables | Required |
| Calendar | Calendar UI for daily notes navigation | Required |
| Tag Wrangler | Batch manage and rename tags | Required |
| Obsidian Git | Auto git backup of vault | Required |
| Natural Language Dates | Natural language date input | Recommended |
| Kanban | Kanban board for Idea Backlog | Recommended |
| Excalidraw | Diagrams and architecture sketches | Recommended |
| Periodic Notes | Weekly/monthly note management | Recommended |

## Daily Workflow Overview

### Morning Routine (30 min)

1. Create daily note using `tpl-daily-journal`
2. Fill Market Pulse section (overnight markets, AVI reading)
3. Set Top 3 priorities for the day
4. Quick RSS scan, mark articles for later

### Throughout the Day

- Capture ideas in daily note
- Use `tpl-report-summary` for deep reads
- Use `tpl-client-meeting` before/after meetings

### Evening (15 min)

- Review daily note completeness
- Record learnings and reflections
- Set tomorrow's priorities

### Friday Review (60-90 min)

- Use `tpl-weekly-review` template
- Review all daily notes from the week
- Update investment thesis health scores
- Review startup idea pipeline
- Plan next week

## File Structure

```
vault/
├── CLAUDE.md                              # Claude Code context
├── 00-Inbox/                              # Quick capture
├── 01-Daily/                              # Daily journals
├── 02-Investment/                         # Market analysis, thesis, clients
├── 03-Startup/                            # Ideas, evaluations, Yuni
├── 04-Learning/                           # Reports, articles, books
├── 05-AI-Toolkit/
│   ├── Prompts/                           # 6 diagnosis prompts
│   └── Workflows/                         # Intelligence pipeline
├── 06-Weekly-Review/                      # Weekly reviews
├── Templates/                             # 7 Obsidian templates
└── Assets/                                # Images, PDFs
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system design document.

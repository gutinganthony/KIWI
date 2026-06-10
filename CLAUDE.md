## gstack (REQUIRED — global install)

**Before doing ANY work, verify gstack is installed:**

```bash
test -d ~/.claude/skills/gstack/bin && echo "GSTACK_OK" || echo "GSTACK_MISSING"
```

If GSTACK_MISSING: STOP. Do not proceed. Tell the user:

> gstack is required for all AI-assisted work in this repo.
> Install it:
> ```bash
> git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
> cd ~/.claude/skills/gstack && ./setup --team
> ```
> Then restart your AI coding tool.

Do not skip skills, ignore gstack errors, or work around missing gstack.

Using gstack skills: After install, skills like /qa, /ship, /review, /investigate,
and /browse are available. Use /browse for all web browsing.
Use ~/.claude/skills/gstack/... for gstack file paths (the global path).

## KIWI 自動載入（每個 session 開始時執行）

每次 session 開始，自動讀取以下檔案建立背景知識：

1. `docs/KIWI_INDEX_FRAMEWORK.md` — ACT index（AVI/CRI/TSI）完整定義
2. `skills/serenity/SKILL.md` — Serenity 供應鏈瓶頸選股框架
3. `skills/wavetrend/SKILL.md` — WaveTrend Oscillator 技術分析框架

載入後，使用者可以直接說：
- 「用 Serenity 框架分析 $TICKER」→ 依照 skills/serenity/SKILL.md 執行完整分析
- 「用 WaveTrend 分析 $TICKER」→ 依照 skills/wavetrend/SKILL.md 執行技術分析
- 「用 Serenity + WaveTrend 分析 $TICKER，搭配 ACT index 判讀」→ 三合一分析

新增分析模組時，在 `skills/` 下建新資料夾並寫 SKILL.md，然後在此處加一行載入路徑即可。

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore

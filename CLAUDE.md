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

## Data Accuracy（摸魚記文章鐵律）

- 所有市場數據（指數、個股價、VIX、報價）發佈前必須對公開來源查證；WebFetch 失敗就明講並請 Jake 確認，絕不憑記憶填數字。
- **事件日期必須對官方行事曆查證**：財報日（去公司 IR 頁確認，注意會計年度：美光 FQ 結束於 2/5/8/11 月底、財報約在其後一個月）、台積電除息（季配息：3/6/9/12 月中旬；2026/7 曾在已發佈文章寫「下週台積電除息」，實際下次為 9/16）、FOMC（約六週一次）、CPI（隔月中旬）。不要從新聞標題反推事件——2026/7 曾因誤讀「Micron could fall after July 10」把 SKHY 掛牌日錯寫成美光財報日，錯誤進了兩篇已發佈文章。
- 範圍限定詞不可省略：說「唯一」「第一」前先窮舉反例（例：美股記憶體標的除美光還有 SanDisk/威騰；HSBC 35% 溢價統計限定「DRAM 純標的」）。
- 查不到的數字標〔待補〕留白，寧可晚發不編數字。
- **每次動筆前先確認「今天是幾號」**（看系統 currentDate，不要用對話流推算）：長 session 跨多天，事件的過去式/未來式必須對齊真實日期。2026/7 曾把已踢完兩天的世界盃決賽（7/19）當成「這週日才要踢」規劃前瞻文。

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

# Codex handoff: <task title>

- Task ID: `<YYYY-MM-DD-task-slug>`
- Codex branch: `codex/<task-slug>`
- Base commit: `<sha>`
- Codex head commit: `<sha>`
- Status: draft | ready-for-Claude-review
- User request: <short statement>

## Outcome

<What was produced and why>

## Proposed changes

- `path/to/file`: <change and reason>

## Validation

- <command/check>: pass | fail | not run
- Reason for anything not run: <reason>

## Decisions and assumptions

- <decision or assumption>

## Risks and open questions

- <risk, tradeoff, or question>

## Claude integration instructions

Inspect the branch diff. Do not merge this branch and do not cherry-pick its commits. Re-apply only accepted changes on a `claude/**` branch, validate them, and open the user-reviewed PR to `main`.

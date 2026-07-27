# Codex collaboration policy

This repository uses Claude Code as the final integration gate for changes that may reach `main`.

## Branch boundary

- Work only on branches named `codex/**`.
- Never push directly to `main`.
- Never open a pull request whose base branch is `main`.
- Never merge, approve, or enable auto-merge for a pull request.
- Do not rename a `codex/**` branch to bypass these rules.

## Ownership boundary

- Treat `memory/claude/**`, `handoffs/claude/**`, `CLAUDE.md`, `agents/**`, and Claude-authored work as read-only unless the user explicitly approves a specific change.
- Do not delete, revert, overwrite, rename, or broadly reformat Claude-owned or user-owned content.
- Preserve unrelated changes.

## Codex output

- Codex may implement and test work on a `codex/**` branch.
- Final output must include a handoff under `handoffs/codex/<task-id>/HANDOFF.md`.
- Use `handoffs/codex/_template/HANDOFF.md` as the format.
- Store durable Codex-only notes under `memory/codex/**`.
- Suggestions about Claude-owned content belong in the handoff, not as direct edits.

## Integration gate

Claude Code must inspect the Codex branch or diff, selectively re-apply accepted work on a `claude/**` branch, and create the user-reviewed pull request to `main`. Codex commits must not be merged or cherry-picked into `main`.

These rules may be changed only with explicit user approval.

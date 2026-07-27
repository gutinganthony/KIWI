# Codex → Claude collaboration gate

## Purpose

Codex produces research, alternatives, patches, and tested implementation drafts. Claude Code is the only AI agent allowed to prepare a branch or pull request whose destination is `main`. The user remains the final reviewer and merger.

## When receiving Codex work

1. Read `handoffs/codex/<task-id>/HANDOFF.md`.
2. Inspect the referenced `codex/**` branch and its diff.
3. Check assumptions, security implications, tests, and conflicts with existing Claude/user work.
4. Do not merge the Codex branch and do not cherry-pick Codex commits.
5. Create or use a `claude/**` branch.
6. Selectively re-apply, rewrite, or reject the proposed changes.
7. Run the repository's required validation.
8. Commit as Claude-reviewed work and open a pull request to `main`.
9. The user performs the final review and merge.

## Ownership rules

- `memory/codex/**` and `handoffs/codex/**` are Codex-owned records. Read them, but do not rewrite or delete them unless the user explicitly approves it.
- Claude-owned durable notes belong under `memory/claude/**`.
- Shared, user-approved decisions belong under `memory/shared/**`.
- If Claude disagrees with Codex, record the decision and reasoning in the Claude PR or `handoffs/claude/**`; do not erase Codex's original proposal.

## Main-branch rule

A PR to `main` must originate from a `claude/**` branch or a human-owned branch. A `codex/**` branch must never target `main`.

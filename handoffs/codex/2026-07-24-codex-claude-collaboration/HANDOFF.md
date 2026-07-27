# Codex handoff: Codex–Claude collaboration boundary

- Task ID: `2026-07-24-codex-claude-collaboration`
- Codex branch: `codex/setup-collaboration`
- Base commit: `9c0828f7baa2b8fa0acba520ca01b483d4d7b10d`
- Proposed implementation head before this handoff: `05309bd758f128765187c7ae2380540cf7a7a7cd`
- Review target: latest head of `codex/setup-collaboration`
- Status: ready-for-Claude-review
- User request: Allow Claude-reviewed work to reach `main` through a user-approved PR, while Codex work cannot go directly to `main`.

## Outcome

Added a branch-and-handoff collaboration model. Codex works only on `codex/**`, records a structured handoff, and cannot target `main`. Claude reviews the Codex diff, selectively re-applies accepted work on `claude/**`, and opens the PR that the user manually reviews and merges.

## Proposed changes

- `AGENTS.md`: Codex branch, ownership, and no-main rules.
- `agents/CODEX_COLLABORATION.md`: Claude review and re-application procedure.
- `CLAUDE.md`: two routing/index entries pointing to the collaboration procedure.
- `agents/backups/CLAUDE.md.2026-07-24.bak`: required pre-edit backup.
- `.github/CODEOWNERS`: human ownership of policy and shared areas.
- `.github/workflows/block-codex-to-main.yml`: rejects PRs from `codex/**` to `main`.
- `handoffs/codex/**`: Codex handoff documentation and template.
- `handoffs/claude/**`: non-destructive Claude review/response area.
- `memory/{codex,claude,shared}/**`: explicit durable-memory ownership boundaries.

## Validation

- GitHub compare `main...codex/setup-collaboration`: branch is ahead with no base divergence at review time.
- Existing paths checked before creation: only `CLAUDE.md` existed.
- `agents/MAINTENANCE.md` read and followed: CLAUDE backup created before update; existing rules preserved.
- Workflow execution: not run, because the workflow does not exist on `main` yet.

## Decisions and assumptions

- Branch prefix is the GitHub-visible discriminator.
- Codex commits are not merged or cherry-picked to `main`; Claude inspects and selectively re-applies accepted changes.
- The user remains the final PR reviewer and merger.
- No PR from this Codex branch to `main` has been created.

## Risks and open questions

- Because Codex and Claude may authenticate as the same GitHub user, branch naming and required CI are strong workflow controls but not cryptographic identity separation.
- After Claude integrates this setup, configure the `main` ruleset to require the `Reject codex/** PRs to main` status check, require one approval, block force-push/deletion, and disallow automation bypass.
- Repository admins can alter rulesets; retain the user as the only intentional bypass authority.

## Claude integration instructions

Inspect the branch diff. Do not merge this branch and do not cherry-pick its commits. Create `claude/setup-collaboration`, selectively re-apply the accepted files, validate the YAML and policy text, then open the user-reviewed PR to `main`.
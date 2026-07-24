# Codex handoffs

Each Codex task that may influence repository work gets its own directory:

```text
handoffs/codex/<YYYY-MM-DD-task-slug>/
└── HANDOFF.md
```

Codex owns this area. Claude Code reads the handoff, reviews the referenced `codex/**` diff, and selectively re-applies accepted changes on a `claude/**` branch. Codex branches and commits do not go directly to `main`.

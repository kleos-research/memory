# Kaleidoscope agent instructions

These are the exact locally verified manager-candidate workflows. No public
package or production account endpoint is available yet.

The manager installs the canonical skill into
`.agents/skills/use-kaleidoscope/SKILL.md` and can add an owner-marked pointer
for each harness without overwriting unrelated instructions.

```bash
kaleidoscope instructions install skill --project "$PWD"
kaleidoscope instructions install agents --project "$PWD" --dry-run
kaleidoscope instructions install agents --project "$PWD"
kaleidoscope instructions install claude --project "$PWD"
kaleidoscope instructions install cursor --project "$PWD"

kaleidoscope instructions remove cursor --project "$PWD" --dry-run
kaleidoscope instructions remove cursor --project "$PWD"
```

Published byte-identical sources:

- [SKILL.md](/SKILL.md)
- [AGENTS.md snippet](/snippets/AGENTS.md)
- [CLAUDE.md snippet](/snippets/CLAUDE.md)
- [Cursor rule](/snippets/cursor-kaleidoscope.mdc)

Use the manager for installation and removal so ownership receipts, bounded
backups, tamper refusal, and concurrent-edit checks stay intact.

The canonical skill SHA-256 for this staging build is
`c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad`.
It exposes only agent use of `search` and `remember`; it does not advertise
account, feedback, lifecycle, maintenance, ontology, or diagnostic operations
as model tools.

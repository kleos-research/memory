# Kaleidoscope agent instructions

The manager installs the canonical skill into
`.agents/skills/use-kaleidoscope/SKILL.md` and can add an owner-marked pointer
for each harness without overwriting unrelated instructions.

```bash
kaleidoscope instructions install skill --project "$PWD"
kaleidoscope instructions install agents --project "$PWD" --dry-run
kaleidoscope instructions install agents --project "$PWD"
kaleidoscope instructions install claude --project "$PWD"
kaleidoscope instructions install cursor --project "$PWD"
```

Published byte-identical sources:

- [SKILL.md](/SKILL.md)
- [AGENTS.md snippet](/snippets/AGENTS.md)
- [CLAUDE.md snippet](/snippets/CLAUDE.md)
- [Cursor rule](/snippets/cursor-kaleidoscope.mdc)

Use the manager for installation and removal so ownership receipts, bounded
backups, tamper refusal, and concurrent-edit checks stay intact.

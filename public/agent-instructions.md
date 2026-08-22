# Kaleidoscope agent instructions

These are the commands that tell your agent Kaleidoscope is there. They work on
a build you already have; there is no package to install and no account to sign
in to yet.

Kaleidoscope installs the shared skill into
`.agents/skills/use-kaleidoscope/SKILL.md`, and can add a short pointer to the
instructions file your editor already reads, marked as its own, without
touching anything else in that file.

```bash
kaleidoscope instructions install skill --project "$PWD"
kaleidoscope instructions install agents --project "$PWD" --dry-run
kaleidoscope instructions install agents --project "$PWD"
kaleidoscope instructions install claude --project "$PWD"
kaleidoscope instructions install cursor --project "$PWD"

kaleidoscope instructions remove cursor --project "$PWD" --dry-run
kaleidoscope instructions remove cursor --project "$PWD"
```

The files it installs are published here, byte for byte:

- [SKILL.md](/SKILL.md)
- [AGENTS.md snippet](/snippets/AGENTS.md)
- [CLAUDE.md snippet](/snippets/CLAUDE.md)
- [Cursor rule](/snippets/cursor-kaleidoscope.mdc)

Install and remove them with `kaleidoscope` rather than by hand. That is what
keeps the dry run, the backup, the record of what Kaleidoscope owns, the
refusal to overwrite something you edited yourself, and the check for a file
that changed underneath it.

The skill tells an agent how to use `search` and `remember`, and nothing else.
It does not offer an agent any account, maintenance or diagnostic command as a
tool, because a model never sees one.

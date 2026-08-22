# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The canonical skill and three harness snippets under `public/` are
byte-for-byte mirrors of the frozen SDK-BOOT manager sources at commit
`3b1ec66d4fc96ff2e77bf7c382b107502ccc7b8d` and remain byte-identical in the
local DX-05B auth-manager candidate `048bf90854a1e38a1b88d14de88b681a206e5790`.
The canonical skill SHA-256 is
`c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad`.
`public/agent-instructions.md` is the docs index for those exact files. The
build copies all five without rendering or rewriting them and binds their exact
digests in `site-manifest.json`.

The staging artifact also emits source-free, machine-readable evidence and
candidate reference snapshots:

- engine candidate SHA-256
  `988192ac9677d5dd55a3642b2da493a0806bb860b5b3c0f509b37ddadee08825`;
- public-contract SHA-256
  `a2357ed6c00e3e143d08581590571447e31d24fd0e7d2466d28a211a0515c75e`;
- the exact local DX-05B manager help under
  `reference/kaleidoscope-cli.candidate.txt`;
- a bounded MCP schema projection under
  `reference/kaleidoscope-mcp.candidate.json`; and
- all verified-local milestones and protected gates under
  `staging-evidence.json`.

These bindings do not provide a final auth-merged manager hash. The current
DX-06 package evidence uses the pre-auth manager, so distribution and
conformance must be regenerated before promotion.

```sh
python3 build_site.py --output dist
python3 verify_site.py dist --mode staging
python3 -m unittest discover -s tests -v
```

A production build requires immutable release metadata containing exactly
`release_version`, `public_contract_sha256`, `availability`, and `updated_at`.
The verifier additionally refuses staging language, stale tool contracts,
private paths, and private core repository links. Building a production
artifact is not permission to publish it. This repository intentionally has no
`LICENSE`; documentation licensing and Pages promotion remain unapproved.

# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The canonical skill and three harness snippets under `public/` are
byte-for-byte mirrors of the consolidated SDK manager at source commit
`05948a3acfbf0a325f06ecfe6057db484f02e5a1`. The deterministic local manager
candidate SHA-256 is
`4fecd84584ed50dacde0677a9aba18c8a44ce6a58ea499e701e2c6dcd1c05b3e`.
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
- the exact consolidated local manager help under
  `reference/kaleidoscope-cli.candidate.txt`;
- a bounded MCP schema projection under
  `reference/kaleidoscope-mcp.candidate.json`; and
- all verified-local milestones and protected gates under
  `staging-evidence.json`.

The final local rebind uses distribution commit
`42ffba4e3976810f91f2adcf53bd4393e5330d72`, DX-06 verification-summary
SHA-256 `98d36d4ce6a7b99c273f6c216a0b351fced7860c76edfc1429f499c0ba63bbed`,
DX-10A evidence SHA-256
`cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e`,
DX-09 deterministic fixture evidence SHA-256
`f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504`,
and DX-10B real-Codex host evidence SHA-256
`74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840`.
All remain local and unpublished. Production signing, live OIDC, additional
native platforms and hosts, licenses/EULA, registry publication, and Pages
promotion remain held.

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

# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The canonical skill and three harness snippets under `public/` remain
byte-for-byte mirrors of the consolidated manager sources. The converged SDK
facades are bound to commit
`67e351d9210756153338825b1d2aab7bb8f1dcb7`; the deterministic local manager
candidate remains
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

The converged local RC uses distribution assembler
`af892d180fe01729450e03917f33ac56698e90e1` and final evidence commit
`53ff63960e660becba3624bd83a17dff5b1caf6b`. The public npm and Python facades
contain the full SDK and both `kaleidoscope`/`kscope` launchers; the macOS arm64
native companions contain the manager and proprietary object-code engine.
Exact RC evidence is:

- release archive `dc7d54bf894966b935c8e2d44868c5caa4571b3fdfabd6765672486a95eb9d9a`;
- manifest `a997d4679f54125bc618c412bca5b877afc83273730cca5a0c9553a29da88e04`;
- package proof `9f9258988e2f7dd5c1cf380405eee9081bc6de33f038a4bdb4d54600b7f6b1aa`;
- npm facade/native `24774b0c455136aff861b643121feec755d03d5d01bf7a9f318082083ec2b8f5` / `d60be804252af0d1abe8207a00816cfce33903afae1770f0674a1c7deb1d9d81`;
- Python facade/native `596dcff8043a94d19ff47f60db27f7d183b4dda3fc084274e7e79ea06e5f1ccf` / `f9d9ad0ec7b3d2ecb99e06a92e68c1c3ba24026c78d460741597d0b32bcf7920`;
- DX-10A evidence `cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e`;
- DX-09 fixture evidence `f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504`;
- DX-10B real-Codex host evidence `74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840`.
All remain local, test-signed and unpublished. The RC has native evidence only
for macOS arm64. Production signing, live OIDC, additional
native platforms and hosts, licenses/EULA, registry publication, and Pages
promotion remain held.

```sh
python3 build_site.py --output docs
python3 verify_site.py docs --mode staging
python3 -m unittest discover -s tests -v
```

`docs/` is the checked-in, deterministic Pages artifact. The repository is
currently still configured to serve legacy GitHub Pages from `main:/`, so
merging this staging work does not promote the new artifact. During the
separately approved Pages promotion, switch the publishing source to
`main:/docs` only after the reviewed artifact and its release content are ready.
The generated artifact carries both `.nojekyll` and the canonical `CNAME` so
the supported branch-folder deployment shape preserves the static route and
custom-domain contract.

A production build requires immutable release metadata containing exactly
`release_version`, `public_contract_sha256`, `availability`, and `updated_at`.
The verifier additionally refuses staging language, stale tool contracts,
private paths, and private core repository links. Building a production
artifact is not permission to publish it. This repository intentionally has no
`LICENSE`; documentation licensing and Pages promotion remain unapproved.

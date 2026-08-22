# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The canonical skill and three harness snippets under `public/` remain
byte-for-byte mirrors of the consolidated manager sources. The converged SDK
facades are bound to commit
`fc15e1ec7d98a9d37983cea87ab23bfc0b7fd317`; the deterministic local manager
candidate is
`fc6afb3606fcd312a7a7188e6f9ec2e72c6885f3f4a87e11b5eeb9b291bf336b`.
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
`d9409ebacf63bcf2b32fde56a31a6350cfdfd491`. The public npm and Python facades
contain the full SDK and both `kaleidoscope`/`kscope` launchers; the macOS arm64
native companions contain the manager and proprietary object-code engine.
Exact RC evidence is:

- release archive `fc37a2caa00f038bf7c260e53b62c9bee6d5e78df1cc3568a180816a3d9b2abf`;
- manifest `39c8738cd938e79b10a20d429ace1fb6a4eda73b1f25a99681a8104dd2e0ef2f`;
- build proof `eb23e9f490179e6d84f4933de5ea5b2ff390030798727ba1ddd90628106b4d94`;
- package proof `095f91ca73faf811a888771dc1298a200193458df63ae5cb890a16f632bc1d3c`;
- final facade evidence `f23c4a0fea5aa260ec41f10f2da23c3bab5147a942aa3e3ea09a3d7473918be0`;
- npm facade/native `c30d45d9ccc61b36ede7b6df87f6728aa9307445a08446a7de5de5bafe9c0605` / `a2cd8924c89a74204fcb9ee8790daf6a53d4ce4bec6fdf6329e127ff9b5b5d12`;
- Python facade/native `7208468413a44412959e0426cf7fb508ca7f32861fcd0ee79ec0f6bedb88e68c` / `24eb29ac7ec70a2a9d36832994d5a17cba2b42f6a12fd6557f541bd2890f89d3`;
- SBOM/provenance/test-only signature `a236f913fa83bf02e99605ba573203ba7cb48f7798ad8728c2aa4d590fd191f3` / `a177d3537d87bfba08e77fe4171e41dff69a757499a742c8a5501ed5777b1d56` / `7fc485f638bcf3327804009bf2890afb96b106fd3171e6f8a013dadac90510d2`;
- DX-10A evidence `cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e`;
- DX-09 fixture evidence `f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504`;
- historic pre-final DX-10B real-Codex host evidence `74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840`.
All remain local, test-signed and unpublished. The RC has native evidence only
for macOS arm64. The final package evidence covers fresh npm/Python facade
invocation, `connect codex --dry-run`, and MCP discovery; it does not establish
real host/IDE acceptance. Production signing, live OIDC, additional native
platforms and hosts, licenses/EULA, registry publication, and Pages promotion
remain held.

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

# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The canonical skill and three harness snippets under `public/` remain
byte-for-byte mirrors of the consolidated manager sources. The converged SDK
facades are bound to commit
`9ed39bddd7bf14e68e1c363074f6921288b9e94b`; the deterministic local manager
candidate is
`a1eb37ab61f8f5681b654f7e25f06c3e3188720ad4cf61aaecc1ecf265e8f6c1`.
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
`0c42ff35b789a0406aaabf6634bdb2988db36b0a`. The public npm and Python facades
contain the full SDK and both `kaleidoscope`/`kscope` launchers; the macOS arm64
native companions contain the manager and proprietary object-code engine.
Exact RC evidence is:

- release archive `2342d12e0010e983db9cfd9c32079bddcc96e8045299c97d878f94200ef6ac8a`;
- manifest `efc41f32bea0deb4180cca85d2996c39d4793cdea78888fc6216a2dcd8ba22f8`;
- build proof `ff363dc752e19979e44b71cc2fdfe6b7f0bf136ba3c29b5cd1bc8b08aa24d053`;
- package proof `62afa5714352615f6c2303ed6427842a70168cbfb0bb6bea0ca2753ba0d551b7`;
- final facade evidence `7d4b49919d9d7607542e27979b64a5f071c58418096ec2a8c74b3c211738307c`;
- npm facade/native `0980c1aef2d94960e7b3384bdc932da024a9534d123d3521f05c66a1b600b4bd` / `ec38717398a623fcca6043b37438ab3f6e2bcfa5790e391bb8747b63ab3f340b`;
- Python facade/native `72099296676ef38b146018ae4ffac6cfb082bc8a537f178443acd351cf7bf6d7` / `d265493d6ca583f2ecd9e69257c8ed604174636e1c5f3b29dc08eafe01c51d8b`;
- SBOM/provenance/test-only signature `5058f2170630cb70ac14252162245f3ae94cc9d02f9b58c74d36694355094f4c` / `498c60561520e57834a807c2e17443b0a7eefe1c3901c67450e0506135babfb8` / `9bce859379b24683cff7e6069835aa9f8d8ac4f1d07ff353f050ea1b9df60e0c`;
- DX-10A evidence `cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e`;
- DX-09 fixture evidence `f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504`;
- historic pre-final DX-10B real-Codex host evidence `74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840`.
All remain local, test-signed and unpublished. The RC has native evidence only
for macOS arm64. The final package evidence covers fresh npm/Python facade
invocation, `connect codex --dry-run`, and MCP discovery; it does not establish
real host/IDE acceptance. Apache-2.0 public software licensing, CC BY 4.0
original documentation licensing, and review-draft product terms are
source-staged. Production signing, live OIDC, additional native platforms and
hosts, final legal review, and registry publication remain held; the separately
authorized Pages release is prepared from a verified public documentation
artifact.

```sh
python3 build_site.py --output docs --public-docs --release-metadata public-docs-release.json
python3 verify_site.py docs --mode public_docs
python3 -m unittest discover -s tests -v
```

`docs/` is the checked-in, deterministic public documentation-preview artifact.
It is intentionally indexable because it documents the public developer
contract, but it does not make the private package artifacts or production OIDC
available. `public-docs-release.json` binds the immutable preview version and
public-contract digest. GitHub Pages serves `main:/docs`; the generated artifact
carries both `.nojekyll` and the canonical `CNAME` so that branch-folder
deployment preserves the static route and custom-domain contract.

The public preview and a production build both require immutable release
metadata containing exactly `release_version`, `public_contract_sha256`,
`availability`, and `updated_at`. The production verifier additionally refuses
staging language, stale tool contracts, private paths, and private core
repository links. Building a production artifact is not permission to publish
it. The [documentation license](LICENSE) applies CC BY 4.0 to original
documentation while excluding software, proprietary engine material,
trademarks, third-party content, and the product terms themselves.

# Kaleidoscope documentation

This repository builds the public documentation site served at
`memory.kleosresearch.xyz`. It contains no product source. Building it performs
no network access, no login, no publication and no deployment.

## What the site says, and the rule that governs it

Kaleidoscope is not released. Every page states status as **what a reader can
and cannot do** — not as what an internal check verified. Concretely:

- Never claim something works that has not been run. `/docs/status/` is the
  single place that says what has been run, on what, and what has not.
- The five status words (`Tested`, `Partly tested`, `Compiler-checked only`,
  `Untested`, `Not available`) are defined once, on `/docs/compatibility/`, and
  every other page defers to that definition. A `Partly tested` row must say
  which part.
- A compiler check is not a build. Four platforms have had a compiler check for
  the memory engine and nothing else: nothing was assembled into a program for
  them and nothing has ever run there. Calling that "builds for this target"
  reads as a working build and is the one claim this repository has already
  had to retract.
- Pre-release honesty is required, not optional. Say plainly that nothing
  installs from a registry, nothing is signed, sign-in does not work, the
  product terms are unreviewed drafts, and no benchmark score is published.
- Our internal release process does not appear anywhere. `verify_site.py`
  enforces this with a vocabulary scan over every published file; see
  `BANNED_VOCABULARY` and the exemptions beside it.

## Page content lives in `build_site.py`

`docs/` is generated. Never hand-edit it. Page copy lives in `PAGES`,
`INTEGRATION_PAGES` and `LEGAL_PAGES`; the machine-readable records published
alongside the pages are `STATUS_RECORD`, `PLATFORM_SUPPORT`, `HOST_SUPPORT` and
`MCP_REFERENCE`. Those records carry capability and status only — no commit, no
build digest, no internal identifier.

The four product terms under `docs/legal/` and the agent skill at `public/`
are republished verbatim from their sources and are not edited from here.

## Build, verify, regenerate

```sh
python3 -m unittest discover -s tests -v
python3 build_site.py --output .site --public-docs --release-metadata public-docs-release.json
python3 verify_site.py .site --mode public_docs
diff --brief --recursive .site docs
```

To regenerate the checked-in artifact after changing `build_site.py`:

```sh
rm -rf .site && python3 build_site.py --output .site --public-docs \
  --release-metadata public-docs-release.json && rm -rf docs && cp -R .site docs
```

`docs/` is the checked-in, deterministic artifact GitHub Pages serves from
`main:/docs`. It carries `.nojekyll` and the canonical `CNAME` so that
branch-folder deployment preserves the route and custom-domain contract.

Both `--public-docs` and `--production` refuse to build without immutable
release metadata containing exactly `release_version`,
`public_contract_sha256`, `availability` and `updated_at`.
`public-docs-release.json` supplies it for the preview. The production verifier
additionally refuses pre-release language, retired tool contracts, private
paths and private repository links. Building a production artifact is not
permission to publish it.

The [documentation license](LICENSE) applies CC BY 4.0 to original
documentation while excluding software, proprietary engine material,
trademarks, third-party content, and the product terms themselves.

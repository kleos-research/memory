# Kaleidoscope documentation

This repository builds the public, source-free documentation surface for
`memory.kleosresearch.xyz`. The default artifact is an explicitly non-indexable
staging build and performs no network, login, publication, or deployment.

The public policy files under `public/` are byte-for-byte mirrors of the
frozen SDK-BOOT manager sources at commit
`3b1ec66d4fc96ff2e77bf7c382b107502ccc7b8d`. The canonical skill SHA-256 is
`c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad`.
The build copies these files without rendering or rewriting them and binds
their exact digests in `site-manifest.json`.

```sh
python3 build_site.py --output dist
python3 verify_site.py dist --mode staging
```

A production build requires immutable release metadata containing exactly
`release_version`, `public_contract_sha256`, `availability`, and `updated_at`.
The verifier additionally refuses staging language, stale tool contracts,
private paths, and private core repository links. Building a production
artifact is not permission to publish it.

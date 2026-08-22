#!/usr/bin/env python3
"""Build the source-free Kaleidoscope public documentation surface.

The default build is an explicitly non-indexable staging artifact. A production
artifact requires immutable release metadata and refuses placeholder values.
This script performs no network, authentication, publication, or deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

DOMAIN = "https://memory.kleosresearch.xyz"
SOCIAL_IMAGE = f"{DOMAIN}/assets/kaleidoscope-og.png"
ROOT = Path(__file__).resolve().parent
TODAY = date(2026, 8, 22)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_FILES = {
    "SKILL.md": ROOT / "public" / "SKILL.md",
    "agent-instructions.md": ROOT / "public" / "agent-instructions.md",
    "snippets/AGENTS.md": ROOT / "public" / "snippets" / "AGENTS.md",
    "snippets/CLAUDE.md": ROOT / "public" / "snippets" / "CLAUDE.md",
    "snippets/cursor-kaleidoscope.mdc": ROOT
    / "public"
    / "snippets"
    / "cursor-kaleidoscope.mdc",
    "documentation-license.txt": ROOT / "LICENSE",
    "legal/CC-BY-4.0.txt": ROOT / "legal" / "CC-BY-4.0.txt",
    "legal/ENGINE-EULA.txt": ROOT / "legal" / "ENGINE-EULA.txt",
    "legal/PRIVACY-NOTICE.txt": ROOT / "legal" / "PRIVACY-NOTICE.txt",
    "legal/SECURITY-POLICY.txt": ROOT / "legal" / "SECURITY-POLICY.txt",
    "legal/SUPPORT-POLICY.txt": ROOT / "legal" / "SUPPORT-POLICY.txt",
}

ENGINE_SOURCE_COMMIT = "d96355632cc52816472106d0776ce63d73631fef"
ENGINE_CANDIDATE_SHA256 = (
    "988192ac9677d5dd55a3642b2da493a0806bb860b5b3c0f509b37ddadee08825"
)
PUBLIC_CONTRACT_SHA256 = (
    "a2357ed6c00e3e143d08581590571447e31d24fd0e7d2466d28a211a0515c75e"
)
PUBLIC_SKILL_SHA256 = (
    "c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad"
)
MANAGER_SOURCE_COMMIT = "fc15e1ec7d98a9d37983cea87ab23bfc0b7fd317"
MANAGER_SHA256 = (
    "fc6afb3606fcd312a7a7188e6f9ec2e72c6885f3f4a87e11b5eeb9b291bf336b"
)
DISTRIBUTION_COMMIT = "42ffba4e3976810f91f2adcf53bd4393e5330d72"
SDK_FACADE_COMMIT = "fc15e1ec7d98a9d37983cea87ab23bfc0b7fd317"
DISTRIBUTION_ASSEMBLER_COMMIT = "af892d180fe01729450e03917f33ac56698e90e1"
FINAL_EVIDENCE_COMMIT = "d9409ebacf63bcf2b32fde56a31a6350cfdfd491"
FINAL_PACKAGE_EVIDENCE_SHA256 = (
    "f23c4a0fea5aa260ec41f10f2da23c3bab5147a942aa3e3ea09a3d7473918be0"
)
FINAL_BUILD_PROOF_SHA256 = (
    "eb23e9f490179e6d84f4933de5ea5b2ff390030798727ba1ddd90628106b4d94"
)
DX10A_EVIDENCE_SHA256 = (
    "cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e"
)
SDK_HOST_CONFORMANCE_COMMIT = "9cd4b5837e887a0bb3dcc13209134c002aad08f5"
PACKAGE_PROOF_SHA256 = "095f91ca73faf811a888771dc1298a200193458df63ae5cb890a16f632bc1d3c"
NPM_FACADE_SHA256 = "c30d45d9ccc61b36ede7b6df87f6728aa9307445a08446a7de5de5bafe9c0605"
NPM_NATIVE_SHA256 = "a2cd8924c89a74204fcb9ee8790daf6a53d4ce4bec6fdf6329e127ff9b5b5d12"
PYTHON_FACADE_SHA256 = (
    "7208468413a44412959e0426cf7fb508ca7f32861fcd0ee79ec0f6bedb88e68c"
)
PYTHON_NATIVE_SHA256 = (
    "24eb29ac7ec70a2a9d36832994d5a17cba2b42f6a12fd6557f541bd2890f89d3"
)
DX10B_HOST_EVIDENCE_SHA256 = (
    "74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840"
)
BENCHMARK_COMMIT = "ef89d05f09435afc9790fcdf5df3e01d34c7115b"
DX09_FIXTURE_EVIDENCE_SHA256 = (
    "f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504"
)
LOCAL_ARCHIVE_SHA256 = (
    "fc37a2caa00f038bf7c260e53b62c9bee6d5e78df1cc3568a180816a3d9b2abf"
)
LOCAL_MANIFEST_SHA256 = (
    "39c8738cd938e79b10a20d429ace1fb6a4eda73b1f25a99681a8104dd2e0ef2f"
)
LOCAL_SBOM_SHA256 = (
    "a236f913fa83bf02e99605ba573203ba7cb48f7798ad8728c2aa4d590fd191f3"
)
LOCAL_PROVENANCE_SHA256 = (
    "a177d3537d87bfba08e77fe4171e41dff69a757499a742c8a5501ed5777b1d56"
)
LOCAL_TEST_SIGNATURE_SHA256 = (
    "7fc485f638bcf3327804009bf2890afb96b106fd3171e6f8a013dadac90510d2"
)

MANAGER_HELP = """Kaleidoscope public local manager

Usage:
  kaleidoscope [--engine PATH] init [--root PATH] [--profile NAME]
                                      [--durability process-local|durable-local]
  kaleidoscope [--engine PATH] profile list
  kaleidoscope [--engine PATH] profile show NAME
  kaleidoscope [--engine PATH] profile use NAME
  kaleidoscope [--engine PATH] profile remove NAME
  kaleidoscope profile account show [NAME]
  kaleidoscope profile account bind ACCOUNT_UUID [NAME]
  kaleidoscope profile account unbind [NAME]
  kaleidoscope [--engine PATH] config [--profile NAME] [--json]
  kaleidoscope [--engine PATH] connect HOST [--scope user|project]
                                      [--profile NAME] [--project PATH]
                                      [--opencode-version stable-v1|beta-v2]
                                      [--dry-run] [--yes]
  kaleidoscope [--engine PATH] disconnect HOST [--scope user|project]
                                      [--project PATH] [--dry-run] [--yes]
  kaleidoscope instructions install TARGET [--project PATH] [--dry-run] [--yes]
  kaleidoscope instructions remove TARGET [--project PATH] [--dry-run] [--yes]
  kaleidoscope [--engine PATH] doctor [--project PATH]
  kaleidoscope login [--device]
  kaleidoscope status [--json]
  kaleidoscope logout [--all-devices] [--local-only]
  kaleidoscope account link PROVIDER
  kaleidoscope account identities
  kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
  kaleidoscope account revoke-session
  kaleidoscope devices list
  kaleidoscope devices revoke DEVICE_UUID
  kaleidoscope --version

Instruction TARGET is skill, agents, claude, or cursor.
The manager edits host configuration only after preview and confirmation.
Project scope is the default. Use --dry-run for an effect-free plan.
"""

MCP_REFERENCE = {
    "schema_version": "kaleidoscope.docs-mcp-reference.v1",
    "status": "verified_local_candidate_only",
    "manager": {
        "source_commit": MANAGER_SOURCE_COMMIT,
        "sha256": MANAGER_SHA256,
        "version": "0.1.0",
    },
    "engine": {
        "source_commit": ENGINE_SOURCE_COMMIT,
        "sha256": ENGINE_CANDIDATE_SHA256,
        "target": "aarch64-apple-darwin",
        "version": "0.0.0-proposal",
    },
    "public_contract_sha256": PUBLIC_CONTRACT_SHA256,
    "protocol_revision": "2025-11-25",
    "model_tools": [
        {
            "name": "remember",
            "required": ["mode"],
            "fields": [
                "content_md",
                "expected_version_id",
                "items",
                "memory_id",
                "mode",
                "semantic_delta",
            ],
            "modes": ["create", "update", "delete"],
            "maximum_batch_items": 20,
        },
        {
            "name": "search",
            "required": [],
            "fields": [
                "as_of",
                "bfs_depth",
                "candidate_pool",
                "channels",
                "ledger",
                "max_facts",
                "maximum_context_bytes",
                "memory_id",
                "query",
                "scope",
                "top_k",
            ],
            "addressing": "exactly_one_of_query_or_memory_id",
            "ledger_values": [True],
        },
    ],
    "operator_commands_are_model_tools": False,
    "local_conformance": {
        "dx10a_evidence_sha256": DX10A_EVIDENCE_SHA256,
        "final_package_evidence_sha256": FINAL_PACKAGE_EVIDENCE_SHA256,
        "historical_codex_host_evidence": {
            "commit": SDK_HOST_CONFORMANCE_COMMIT,
            "sha256": DX10B_HOST_EVIDENCE_SHA256,
            "applies_to": "pre-final manager candidate only",
        },
    },
    "package_contract": {
        "version": "0.1.0-rc.1",
        "sdk_facade_commit": SDK_FACADE_COMMIT,
        "native_target": "darwin-arm64",
        "facade_launchers": ["kaleidoscope", "kscope"],
        "publicly_available": False,
    },
    "release_readiness_claimed": False,
}

STAGING_EVIDENCE = {
    "schema_version": "kaleidoscope.docs-staging-evidence.v1",
    "as_of": TODAY.isoformat(),
    "status": "local_staging_only",
    "engine": {
        "source_commit": ENGINE_SOURCE_COMMIT,
        "candidate_sha256": ENGINE_CANDIDATE_SHA256,
        "public_contract_sha256": PUBLIC_CONTRACT_SHA256,
        "production_signature_verified": False,
    },
    "manager": {
        "source_commit": MANAGER_SOURCE_COMMIT,
        "candidate_sha256": MANAGER_SHA256,
        "version": "0.1.0",
        "production_signature_verified": False,
    },
    "local_distribution": {
        "commit": FINAL_EVIDENCE_COMMIT,
        "assembler_commit": DISTRIBUTION_ASSEMBLER_COMMIT,
        "sdk_facade_commit": SDK_FACADE_COMMIT,
        "version": "0.1.0-rc.1",
        "native_target": "darwin-arm64",
        "archive_sha256": LOCAL_ARCHIVE_SHA256,
        "manifest_sha256": LOCAL_MANIFEST_SHA256,
        "sbom_sha256": LOCAL_SBOM_SHA256,
        "provenance_sha256": LOCAL_PROVENANCE_SHA256,
        "signature_envelope_sha256": LOCAL_TEST_SIGNATURE_SHA256,
        "build_proof_sha256": FINAL_BUILD_PROOF_SHA256,
        "package_proof_sha256": PACKAGE_PROOF_SHA256,
        "final_facade_happy_path_evidence_sha256": FINAL_PACKAGE_EVIDENCE_SHA256,
        "facades": {
            "contains": "full public SDK plus kaleidoscope and kscope launchers",
            "npm": {
                "name": "@kleos-research/kaleidoscope",
                "sha256": NPM_FACADE_SHA256,
            },
            "python": {
                "name": "kaleidoscope-memory",
                "sha256": PYTHON_FACADE_SHA256,
            },
        },
        "native_companions": {
            "contains": "manager plus proprietary object-code engine",
            "npm": {
                "name": "@kleos-research/kaleidoscope-darwin-arm64",
                "sha256": NPM_NATIVE_SHA256,
            },
            "python": {
                "name": "kaleidoscope-memory-native-darwin-arm64",
                "sha256": PYTHON_NATIVE_SHA256,
            },
        },
        "test_signature_only": True,
        "production_release": False,
    },
    "milestones": [
        {
            "id": "DX-04",
            "commit": MANAGER_SOURCE_COMMIT,
            "status": "verified_local",
            "scope": "consolidated manager init, profiles, reversible host configuration, doctor, instructions",
            "verification": f"deterministic candidate manager SHA-256 {MANAGER_SHA256}",
        },
        {
            "id": "DX-05B",
            "commit": MANAGER_SOURCE_COMMIT,
            "status": "verified_local_provider_unconfigured",
            "scope": "consolidated manager OIDC, device login, credential storage, account and device commands",
            "verification": "12 account/device commands passed the offline provider-not-configured and no-engine-resolution lane",
        },
        {
            "id": "DX-06A/B",
            "commit": DISTRIBUTION_ASSEMBLER_COMMIT,
            "status": "verified_local_test_signature_only",
            "scope": "source-only distribution tooling, full SDK facades, native object-code companions and lifecycle rehearsal",
            "verification": f"reassembled source-bound archive and package proof SHA-256 {PACKAGE_PROOF_SHA256}; build proof SHA-256 {FINAL_BUILD_PROOF_SHA256}",
        },
        {
            "id": "DX-07",
            "commit": SDK_FACADE_COMMIT,
            "status": "verified_local",
            "scope": "full Python and TypeScript SDK facades, agent/framework integrations, installed-payload resolvers and both launchers",
            "verification": "37 TypeScript tests and the Python suite passed with one intentional native-profile skip each, plus installed-payload resolver checks",
        },
        {
            "id": "DX-09",
            "commit": BENCHMARK_COMMIT,
            "status": "merged_deterministic_fixture_only",
            "scope": "candidate-bound native smoke and credential-free deterministic fixture pipeline; no benchmark score",
            "verification": f"24 tests passed with 1 live skip; stable fixture evidence SHA-256 {DX09_FIXTURE_EVIDENCE_SHA256}",
        },
        {
            "id": "DX-10B",
            "commit": FINAL_EVIDENCE_COMMIT,
            "status": "verified_local_package_facades",
            "scope": "fresh npm and Python facade invocation: init, doctor, Codex dry-run configuration, and stdio MCP discovery",
            "verification": f"final package evidence SHA-256 {FINAL_PACKAGE_EVIDENCE_SHA256}; no real host acceptance claim",
        },
        {
            "id": "DX-10A",
            "commit": DISTRIBUTION_COMMIT,
            "status": "verified_local_macos_arm64",
            "scope": "clean install, package binding, friendly profile MCP, account refusal, update, rollback, uninstall and vault canary",
            "verification": f"DX-10A evidence SHA-256 {DX10A_EVIDENCE_SHA256}",
        },
    ],
    "historical_host_conformance": {
        "commit": SDK_HOST_CONFORMANCE_COMMIT,
        "evidence_sha256": DX10B_HOST_EVIDENCE_SHA256,
        "scope": "isolated real Codex CLI configuration and generic stdio MCP",
        "status": "pre-final manager candidate only; not final package acceptance",
    },
    "release_holds": {
        "production_oidc_issuer": None,
        "production_signing_identity": None,
        "engine_eula_product_authorized": True,
        "production_engine_eula_finalized": False,
        "public_software_license_product_authorized": True,
        "original_documentation_license_product_authorized": True,
        "external_legal_review_complete": False,
        "registry_publication_authorized": False,
        "pages_promotion_authorized": False,
        "non_macos_arm64_native_support_verified": False,
        "claude_cursor_opencode_live_host_verified": False,
        "live_model_or_ide_acceptance_verified": False,
    },
    "production_release": False,
    "public_availability": False,
}


@dataclass(frozen=True)
class Page:
    route: str
    title: str
    description: str
    body: str
    section: str = "docs"
    noindex: bool = False


def legal_document_body(filename: str, summary: str) -> str:
    source = PUBLIC_FILES[f"legal/{filename}"].read_text(encoding="utf-8")
    return (
        f'<p class="lede">{html.escape(summary)}</p>'
        '<div class="callout"><strong>Review status.</strong> This is a '
        "source-controlled review draft, not a production legal notice, "
        "support commitment, or claim of external legal approval.</div>"
        f'<p><a href="/legal/{html.escape(filename, quote=True)}">'
        "Download the plain-text source</a>.</p>"
        f'<pre class="legal-document"><code>{html.escape(source)}</code></pre>'
    )


DOC_NAV = (
    ("/docs/", "Overview"),
    ("/docs/getting-started/", "Getting started"),
    ("/docs/packages/", "Packages"),
    ("/docs/concepts/", "Concepts"),
    ("/docs/cli/", "CLI"),
    ("/docs/mcp/", "MCP"),
    ("/docs/integrations/", "Integrations"),
    ("/docs/operations/", "Operations"),
    ("/docs/security/", "Security"),
    ("/docs/privacy/", "Privacy"),
    ("/docs/account/", "Account"),
    ("/docs/compatibility/", "Compatibility"),
    ("/docs/benchmarks/", "Benchmarks"),
    ("/docs/evidence/", "Release evidence"),
    ("/docs/release-notes/", "Release notes"),
    ("/docs/troubleshooting/", "Troubleshooting"),
    ("/docs/migration/", "Migration"),
    ("/docs/legal/", "Legal"),
)


PAGES = (
    Page(
        route="/docs/",
        title="Kaleidoscope documentation",
        description="Developer documentation for the local Kaleidoscope CLI, stdio MCP server, profiles, integrations, security, and account boundary.",
        body="""
<p class="lede">Kaleidoscope is local memory for agents: a native CLI and persistent stdio MCP server with one profile shared across configured harnesses.</p>
<div class="callout"><strong>Release status.</strong> This is a non-indexable documentation staging build. Local implementation and conformance evidence exists, but no package, registry, production login, public SDK repository, or Pages promotion is authorized.</div>
<div class="grid">
  <article class="card"><h2><a href="/docs/getting-started/">Preview the workflow</a></h2><p>Inspect the verified manager interface for one profile, reversible host setup, and local diagnostics.</p></article>
  <article class="card"><h2><a href="/docs/packages/">Prepare a package install</a></h2><p>See the final npm and Python names, platform rules, and source-free release gates.</p></article>
  <article class="card"><h2><a href="/docs/mcp/">Build against MCP</a></h2><p>Use the candidate-bound two-tool contract over one long-lived stdio process.</p></article>
  <article class="card"><h2><a href="/docs/evidence/">Check what passed</a></h2><p>Separate locally verified milestones from platform holds and protected production gates.</p></article>
</div>
<h2>Choose a path</h2>
<ul><li>Agent user: read <a href="/docs/getting-started/">Getting started</a>; the commands are an interface preview until a protected release is approved.</li><li>Application developer: begin with <a href="/docs/integrations/">Integrations</a>, then use the persistent <a href="/docs/mcp/">MCP contract</a>.</li><li>Operator: use <a href="/docs/operations/">Operations</a> for separate configuration, credential, package, and vault lifecycles.</li><li>Security or privacy reviewer: read <a href="/docs/security/">Security</a>, <a href="/docs/privacy/">Privacy</a>, and the machine-readable <a href="/staging-evidence.json">staging evidence</a>.</li><li>Agent crawler: start at <a href="/llms.txt">llms.txt</a> or the expanded <a href="/llms-full.txt">llms-full.txt</a>.</li></ul>
""",
    ),
    Page(
        route="/docs/getting-started/",
        title="Getting started",
        description="The release-gated Kaleidoscope quickstart: initialize a local profile, safely connect an agent harness, and verify search and remember.",
        body="""
<p class="lede">The verified manager creates or imports one local profile, previews an owner-marked host change, applies it with confirmation, and can remove exactly what it owns.</p>
<div class="callout"><strong>Release-candidate quickstart, not a live registry command.</strong> The converged <code>0.1.0-rc.1</code> package contract passed locally for macOS arm64, but the packages remain private, test-signed, noindex, and unpublished.</div>
<h2>1. Install after protected promotion</h2>
<p>Choose one public SDK facade after publication. Each facade installs its exact macOS arm64 native companion; do not install both and do not omit the native dependency.</p>
<pre><code># npm / Node.js 22+
npm install -g @kleos-research/kaleidoscope@0.1.0-rc.1

# or Python 3.11+
python -m pip install kaleidoscope-memory==0.1.0rc1

kaleidoscope --version
kscope --version</code></pre>
<p>The facade contains the full public SDK, installed-payload resolver, and both launchers. Its native companion contains the manager and proprietary object-code engine without engine source. There is no install hook, runtime download, compiler, or source-build fallback.</p>
<h2>2. Initialize a profile</h2>
<pre><code>kaleidoscope init \
  --profile default \
  --root /absolute/path/to/user-owned/kaleidoscope-memory
kaleidoscope config --profile default --json</code></pre>
<p>The launcher resolves the manager and engine from the installed native companion. A profile is selected through the manager and native profile registry; agent configuration receives <code>mcp --profile NAME</code>, not credentials or raw vault coordinates.</p>
<h2>3. Preview and connect a host</h2>
<pre><code>kaleidoscope connect codex --profile default --project "$PWD" --dry-run
kaleidoscope connect codex --profile default --project "$PWD"
kaleidoscope doctor --project "$PWD"</code></pre>
<p>Local tests cover <code>codex</code>, <code>claude</code>, <code>cursor</code>, and <code>opencode</code> transforms. That is configuration evidence, not live acceptance by a released host version. Existing unrelated configuration is preserved; ambiguous, symlinked, tampered, or concurrently edited files are refused.</p>
<h2>4. Verify the contract</h2>
<p>The local candidate contract is bound to engine SHA-256 <code>988192ac9677…</code> and public-contract SHA-256 <code>a2357ed6c00e…</code>. It publishes exactly <code>remember</code> and <code>search</code>; the launch descriptor presents the agent-facing order <code>search</code>, <code>remember</code>. Ranked search returns <code>selected_hits</code>; addressed search returns the memory at top level.</p>
<h2>5. Disconnect safely</h2>
<pre><code>kaleidoscope disconnect codex --project "$PWD" --dry-run
kaleidoscope disconnect codex --project "$PWD"</code></pre>
<p>Disconnect removes only Kaleidoscope-owned material and leaves other host settings and vault bytes unchanged.</p>
""",
    ),
    Page(
        route="/docs/packages/",
        title="Package installation",
        description="Kaleidoscope npm and Python package names, platform selection, source-free payload rules, and protected release gates.",
        body=f"""
<p class="lede">The converged contract separates public SDK facades from native companions. Facades contain the full language SDK and both command launchers; native companions contain the manager plus proprietary object-code engine.</p>
<div class="callout"><strong>Local RC evidence only.</strong> Version <code>0.1.0-rc.1</code> (Python <code>0.1.0rc1</code>) is verified only for macOS arm64. Every artifact remains private, test-signed, unpublished, and outside a support claim.</div>
<h2>npm: full TypeScript SDK facade</h2>
<pre><code>npm install -g @kleos-research/kaleidoscope@0.1.0-rc.1
kaleidoscope --version
kscope --version</code></pre>
<p><code>@kleos-research/kaleidoscope</code> contains the full public TypeScript client, type declarations, typed installed-payload resolver, and the <code>kaleidoscope</code>/<code>kscope</code> launchers. It requires Node.js 22 or newer and pins <code>@kleos-research/kaleidoscope-darwin-arm64@0.1.0-rc.1</code> as its exact optional native companion. Do not use <code>--omit=optional</code>.</p>
<p>The macOS arm64 native companion contains the manager, proprietary object-code engine, bound public contract, manifest, and trust material. It contains neither the public SDK implementation nor engine source.</p>
<h2>Python: full Python SDK facade</h2>
<pre><code>python -m pip install kaleidoscope-memory==0.1.0rc1
kaleidoscope --version
kscope --version</code></pre>
<p><code>kaleidoscope-memory</code> contains the full public Python client, installed-payload resolver, and both console scripts. It requires Python 3.11 or newer and selects <code>kaleidoscope-memory-native-darwin-arm64==0.1.0rc1</code> only on macOS arm64.</p>
<p>The native wheel contains the same manager and proprietary object-code engine payload as the npm native companion. Neither ecosystem uses an install hook, runtime download, compiler, source distribution fallback, or embedded private engine source.</p>
<h2>Exact local RC artifacts</h2>
<table><thead><tr><th>Artifact</th><th>SHA-256</th></tr></thead><tbody>
<tr><td>Source-free release archive</td><td><code>{LOCAL_ARCHIVE_SHA256}</code></td></tr>
<tr><td>Signed distribution manifest</td><td><code>{LOCAL_MANIFEST_SHA256}</code></td></tr>
<tr><td>npm SDK facade</td><td><code>{NPM_FACADE_SHA256}</code></td></tr>
<tr><td>npm macOS arm64 native companion</td><td><code>{NPM_NATIVE_SHA256}</code></td></tr>
<tr><td>Python SDK facade</td><td><code>{PYTHON_FACADE_SHA256}</code></td></tr>
<tr><td>Python macOS arm64 native companion</td><td><code>{PYTHON_NATIVE_SHA256}</code></td></tr>
<tr><td>Combined package proof</td><td><code>{PACKAGE_PROOF_SHA256}</code></td></tr>
</tbody></table>
<h2>What the package checks</h2>
<ul><li>Exact SDK commit, manager, engine, public-contract, manifest, package, SBOM, provenance, and signature bindings.</li><li>Facade names, versions, native dependency pins, required client modules, resolvers, both launchers, and allowlisted archive inventories.</li><li>Private-source and build-path scans plus isolated npm/Python installs and both version commands.</li><li>Unsupported targets fail clearly; the five non-macOS-arm64 entries remain refusal-only scaffolds.</li></ul>
<h2>Current availability</h2>
<p>SDK commit <code>{SDK_FACADE_COMMIT}</code>, assembler commit <code>{DISTRIBUTION_ASSEMBLER_COMMIT}</code>, and final evidence commit <code>{FINAL_EVIDENCE_COMMIT}</code> define this local RC contract. The package proof records <code>facade_mode: sdk_artifacts</code>; the final package evidence records fresh npm/Python facade invocation. Apache-2.0 metadata and the proprietary EULA review draft are source-staged and a legally-bound refresh of this local proof is in progress. Final legal review, trusted signing identities, registry credentials, other native platforms, and protected publication approval remain required.</p>
""",
    ),
    Page(
        route="/docs/concepts/",
        title="Concepts and boundaries",
        description="How Kaleidoscope separates local memory, profiles, harness identity, account identity, and a future hosted service.",
        body="""
<p class="lede">The important boundary is local memory versus account metadata—not merely “logged in versus logged out.”</p>
<h2>Local engine</h2>
<p>The proprietary native engine owns the memory algorithm, canonical vault, graph, ranking, and stdio MCP behavior. Its source is not part of the public manager, client, integration, or skill surfaces.</p>
<h2>Manager and profile</h2>
<p>The consolidated manager initializes profiles, validates the engine launch descriptor, edits harness configuration safely, runs offline diagnostics, installs agent guidance, and exposes account/device commands. A profile may carry one explicit, manager-local account UUID reference; this changes neither its vault identity nor its credentials. The local distribution is bound to manager source commit <code>fc15e1e…</code> and its candidate binary digest.</p>
<h2>SDK facade and native companion</h2>
<p>The npm and Python facades at SDK commit <code>fc15e1e…</code> contain the full public clients, typed installed-payload resolvers, and <code>kaleidoscope</code>/<code>kscope</code> launchers. Their exact macOS arm64 native companions contain the manager and proprietary engine object code. This keeps the public developer API in the facade without placing engine source in either layer.</p>
<h2>Harness identity</h2>
<p>Codex, Claude, Cursor, OpenCode, framework clients, and generic MCP clients are consumers of the same profile. They do not become separate memory stores merely because their configuration formats differ.</p>
<h2>Account identity</h2>
<p>Login is designed to link a product account and device. The account protocol rejects memory fields and absolute local paths before transport. Logout or unlinking is not a vault operation and must not be interpreted as consent to upload memory.</p>
<h2>Hosted memory</h2>
<p>A hosted service is a later product requiring separate authorization, tenant isolation, retention, residency, deletion, sync, billing, and incident-response contracts. It is not available; login does not opt a user into it.</p>
""",
    ),
    Page(
        route="/docs/cli/",
        title="CLI reference",
        description="Candidate-generated reference for the Kaleidoscope manager CLI, profiles, host connection, diagnostics, and account commands.",
        body="""
<p class="lede">The developer-facing CLI is <code>kaleidoscope</code>. The engine executable <code>kscope</code> remains a native runtime/operator surface and is not the manager quickstart.</p>
<div class="callout"><strong>Candidate-generated reference.</strong> The exact help snapshot comes from consolidated manager source commit <code>fc15e1e…</code> and the bound candidate SHA-256. It is not a public-installation claim.</div>
<p><a href="/reference/kaleidoscope-cli.candidate.txt">Download the exact candidate help text</a>.</p>
<h2>Local memory and host commands</h2>
<pre><code>kaleidoscope [--engine PATH] init [--root PATH] [--profile NAME] [--durability process-local|durable-local]
kaleidoscope [--engine PATH] profile list|show|use|remove
kaleidoscope profile account show [NAME]
kaleidoscope profile account bind ACCOUNT_UUID [NAME]
kaleidoscope profile account unbind [NAME]
kaleidoscope [--engine PATH] config [--profile NAME] [--json]
kaleidoscope [--engine PATH] connect HOST [--scope user|project] [--profile NAME] [--project PATH] [--opencode-version stable-v1|beta-v2] [--dry-run] [--yes]
kaleidoscope [--engine PATH] disconnect HOST [--scope user|project] [--project PATH] [--dry-run] [--yes]
kaleidoscope instructions install|remove skill|agents|claude|cursor [--project PATH] [--dry-run] [--yes]
kaleidoscope [--engine PATH] doctor [--project PATH]</code></pre>
<h2>Account and device commands</h2>
<pre><code>kaleidoscope login [--device]
kaleidoscope status [--json]
kaleidoscope logout [--all-devices] [--local-only]
kaleidoscope account link PROVIDER
kaleidoscope account identities
kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
kaleidoscope account revoke-session
kaleidoscope devices list
kaleidoscope devices revoke DEVICE_UUID</code></pre>
<p><code>account identities</code> lists only opaque IDs usable by <code>account unlink</code>. <code>account revoke-session</code> revokes the current token family; it is not an account-deactivation command. The local profile-account commands hold a non-secret UUID reference only. All remote account commands intentionally fail with <code>provider not configured</code> without approved issuer, audience, client, and account-origin configuration. No production issuer is published.</p>
<h2>Safety invariants</h2>
<ul><li>Mutating host and instruction commands support an effect-free dry run and explicit confirmation.</li><li>Unknown, conflicting, symlinked, tampered, or concurrently changed targets fail closed.</li><li>Backups are bounded and owner receipts make removal idempotent.</li><li>Agent launch configuration contains no tokens, provider keys, or raw vault coordinates.</li><li>Account traffic is closed to an exact account-only route inventory; it is separate from engine MCP traffic.</li></ul>
""",
    ),
    Page(
        route="/docs/mcp/",
        title="MCP reference",
        description="The Kaleidoscope stdio MCP contract: exactly search and remember for agents, with persistent sessions and operator-tool exclusion.",
        body="""
<p class="lede">The candidate public contract publishes exactly two model-callable MCP tools over stdio revision <code>2025-11-25</code>. Everything else remains outside the agent tool list.</p>
<div class="callout"><strong>Exact local binding.</strong> Engine <code>988192ac9677…</code>, public contract <code>a2357ed6c00e…</code>, macOS arm64 only. This is contract and functional evidence, not a production signature or availability claim.</div>
<p><a href="/reference/kaleidoscope-mcp.candidate.json">Download the machine-readable candidate MCP reference</a>.</p>
<h2><code>search</code></h2>
<p>Supply exactly one of <code>query</code> or <code>memory_id</code>. A query performs ranked retrieval and records an exposure; <code>ledger</code> accepts only <code>true</code>. Use a small protocol-defining <code>top_k</code> (normally about 5) and a bounded <code>maximum_context_bytes</code>. Ranked results appear under <code>selected_hits</code>. An addressed read returns the memory at top level and refuses ranking controls.</p>
<pre><code>{"query":"What constraints govern the release?","top_k":5,"ledger":true}</code></pre>
<h2><code>remember</code></h2>
<p><code>mode</code> is required and is <code>create</code>, <code>update</code>, or <code>delete</code>. Create/update content begins with an H1 and carries a semantic delta with a required title and at least one fact. Every fact endpoint is declared with <code>n</code>, <code>kind</code>, and the required <code>is</code> gloss. Predicates are snake_case. Update/delete use <code>memory_id</code> and <code>expected_version_id</code>. Batching accepts at most 20 creates and does not share semantic fields between items.</p>
<h2>Lifecycle</h2>
<p>Clients keep one stdio process alive across calls, negotiate MCP once, enforce a startup deadline, cancel cleanly, bound stderr, and tear down without an orphan. DX-07 locally verifies persistent Python and TypeScript sessions; framework integrations do not run a second hidden retrieval.</p>
<h2>Not agent tools</h2>
<p>Feedback, lifecycle/import, maintenance, ontology, and diagnostics are controller/operator operations. Public search does not return the handle required for feedback, so there is no supported public agent-attribution path. Historical names are documented only on the <a href="/docs/migration/">migration page</a>.</p>
""",
    ),
    Page(
        route="/docs/integrations/",
        title="Agent and framework integrations",
        description="How Kaleidoscope integrates with Codex, Claude, Cursor, OpenCode, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, and generic MCP.",
        body="""
<p class="lede">Every integration consumes the same closed profile-first launch descriptor and persistent stdio MCP contract. The wrapper candidates do not contain or reimplement the proprietary memory algorithm.</p>
<table><thead><tr><th>Integration</th><th>Pinned local evidence</th><th>Public status</th></tr></thead><tbody>
<tr><td><a href="/docs/integrations/codex/">Codex</a></td><td>Real <code>codex-cli 0.149.0-alpha.4</code> add/list/get/remove passed in isolated config with byte-exact rollback; generic stdio MCP exposed exactly two tools.</td><td>Verified local CLI configuration; model/TUI acceptance held</td></tr>
<tr><td><a href="/docs/integrations/claude-code/">Claude Code</a></td><td>Managed <code>.mcp.json</code> render, dry run, idempotence, and exact rollback passed.</td><td>Not live-host accepted</td></tr>
<tr><td><a href="/docs/integrations/cursor/">Cursor</a></td><td>Managed <code>mcp.json</code> plus owner-marked rule passed local configuration tests.</td><td>Not live-host accepted</td></tr>
<tr><td><a href="/docs/integrations/opencode/">OpenCode</a></td><td>Stable v1 direct entry is default; beta v2 is explicit and never silently selected.</td><td>Not live-host accepted</td></tr>
<tr><td><a href="/docs/integrations/generic-mcp/">Python and TypeScript generic MCP</a></td><td><code>mcp==1.29.0</code>, <code>mcp==2.0.0</code>, and <code>@modelcontextprotocol/client==2.0.0</code>; persistent and real-profile lanes passed.</td><td>Verified local, unpublished</td></tr>
<tr><td><a href="/docs/integrations/langchain/">LangChain</a> / <a href="/docs/integrations/langgraph/">LangGraph</a></td><td><code>langchain==1.3.16</code>, <code>langgraph==1.2.11</code>; one persistent session and no shadow store.</td><td>Verified with fake provider</td></tr>
<tr><td><a href="/docs/integrations/claude-agent-sdk/">Claude Agent SDK</a></td><td><code>claude-agent-sdk==0.2.143</code>; strict MCP names and lifecycle passed.</td><td>Verified without live provider</td></tr>
<tr><td><a href="/docs/integrations/openai-agents-sdk/">OpenAI Agents SDK</a></td><td>Python <code>0.22.0</code> and TypeScript <code>0.17.0</code>; scripted-model routing passed.</td><td>Verified with adapter caveat</td></tr>
<tr><td><a href="/docs/integrations/crewai/">CrewAI</a></td><td><code>crewai==1.15.17</code>; long-lived MCP adapter passed.</td><td>Verified with fake server</td></tr>
</tbody></table>
<div class="callout"><strong>What DX-07 and final package evidence prove.</strong> SDK commit <code>fc15e1e…</code> converges the tested Python/TypeScript clients and both command launchers into the registry facades; the local suites and installed-payload resolvers passed. Final evidence <code>{FINAL_PACKAGE_EVIDENCE_SHA256[:10]}…</code> proves fresh npm/Python facade <code>init</code>, <code>doctor</code>, <code>connect codex --dry-run</code>, and stdio MCP discovery. Historic commit <code>9cd4b58…</code> covered real Codex CLI configuration for a pre-final manager candidate only. Claude Code, Cursor, and OpenCode live acceptance remains unverified; no live provider, model/TUI/IDE, publication, or support claim follows.</div>
<h2>Agent guidance</h2>
<p>Install the <a href="/SKILL.md">public skill</a>, then add only the compact owner-marked pointer appropriate to <a href="/snippets/AGENTS.md">AGENTS.md</a>, <a href="/snippets/CLAUDE.md">CLAUDE.md</a>, or <a href="/snippets/cursor-kaleidoscope.mdc">Cursor</a>. Use the manager so dry runs, backups, receipts, tamper checks, and exact removal remain intact.</p>
""",
    ),
    Page(
        route="/docs/operations/",
        title="Local operations",
        description="Operate Kaleidoscope safely: locations, backup and restore, migration, disconnect, uninstall, and exact vault deletion.",
        body="""
<p class="lede">Configuration, agent instructions, account credentials, installed executables, and canonical vault data have separate lifecycles.</p>
<h2>Locate before changing</h2><p>Use the manager profile and doctor views to identify the active package and profile without printing tokens or raw memory content. Never assume a worktree carries gitignored vault data.</p>
<h2>Back up and restore</h2><p>Back up the canonical vault from the main checkout or another explicit data location, not a disposable worktree. Restore only through the verified export/import path for the same supported vault format.</p>
<h2>Disconnect and uninstall</h2><p>Disconnect removes only manager-owned host configuration. Instruction removal is separate. A future installer uninstall removes package artifacts according to its scope; account logout/revocation is also separate. None of these operations implicitly deletes a vault.</p>
<h2>Delete a vault</h2><p>Vault deletion is a separate preview-and-confirm operation tied to one exact resolved root. Logical memory deletion and physical vault deletion are different operations. A broad path, unresolved variable, or ambiguous target must be refused.</p>
<h2>Update and rollback</h2><p>DX-10A locally exercised clean install, update, exact rollback, and uninstall under an explicitly marked staging root using the final local manager and engine candidate. It verified only a TEST-ONLY Ed25519 trust root and reused the same binaries for the simulated update. This is not a production installer, notarization result, or supported update channel. The separate vault canary remained byte-identical.</p>
<h2>Package shapes</h2><p>Local macOS arm64 staging produced full TypeScript/Python SDK facades and exact npm/wheel native companions. Both facades expose <code>kaleidoscope</code> and <code>kscope</code>; both companions carry the manager and proprietary object-code engine. Nothing was published, and the other five platform entries remain refusal-only scaffolds.</p>
""",
    ),
    Page(
        route="/docs/security/",
        title="Security",
        description="Kaleidoscope security model, package integrity, account isolation, vulnerability reporting, and native-binary limits.",
        body="""
<p class="lede">Kaleidoscope protects source distribution and establishes verifiable boundaries. A native binary remains inspectable and may be reverse engineered; object-code distribution is not a claim of impossibility.</p>
<h2>Local engine boundary</h2><p>The generated candidate contract declares a local vault, stdio MCP, no required network, and no external model calls. The manager launches the engine with a closed non-secret environment instead of inheriting provider keys, account tokens, cloud credentials, or direct vault-coordinate variables.</p>
<h2>Account boundary</h2><p>The consolidated manager constructs only 11 declared account routes. Its request privacy guard rejects memory/profile field families and absolute local paths before transport. DX-10A exercised all 11 without an engine argument against a deliberately missing engine and observed provider-not-configured refusals before engine resolution. No production account endpoint is available.</p>
<h2>Package integrity</h2><p>DX-06 binds the SDK facade commit, manager, engine, bundled model, public contract, package digests, CycloneDX SBOM, provenance, target, and prior-manifest rollback identity. It validates facade client modules, resolvers, both launchers, exact native dependency pins, archive safety, and the public/private source boundary. Its signature is from a checked-in test fixture and the native code is only ad hoc/linker signed. Authorized license selections and an EULA review draft are now source-staged; the older exact package proof does not contain them. Production trust roots, role keys, Apple signing/notarization, final notices, and final legal review remain absent.</p>
<h2>Verified privacy checks</h2><p>The manager and engine candidates contain no bounded private builder-path hits and no Mach-O debug sections. Local conformance used canary values for environment, outputs, profiles, host configuration, and MCP traffic. The Codex lane used isolated HOME, CODEX_HOME, XDG, project, profile, and vault roots and restored its non-empty baseline byte-for-byte. These are scoped test results, not a universal absence claim.</p>
<h2>Report a vulnerability</h2><p>Do not publish an exploit or sensitive report in a public issue. The production security contact and supported-version policy are release blockers and will be published here and in <code>/.well-known/security.txt</code> before promotion.</p>
""",
    ),
    Page(
        route="/docs/privacy/",
        title="Privacy and data boundary",
        description="What Kaleidoscope keeps local, what the account manager may send, credential storage, telemetry status, and hosted-memory separation.",
        body="""
<p class="lede">Local memory and account identity are separate systems. Logging in does not authorize memory upload, sync, analysis, training, or deletion.</p>
<h2>Local memory data</h2><p>Memory content, queries, selected results, memory IDs, graph data, local paths, vault coordinates, workspace/principal/journal identity, and local provider credentials remain engine-side fields. They are excluded from the account protocol.</p>
<h2>Account data</h2><p>The local auth candidate sends bounded account and device fields needed for OIDC login, refresh, account status, external-identity linking, logout/revocation, and device management. Device display fields reject absolute-path forms. The exact production provider, policy, retention, recovery, and account-deletion terms are not configured.</p>
<h2>Credential storage</h2><p>The native implementation uses macOS Keychain on the only natively tested platform. Windows Credential Manager and Linux Secret Service implementations exist but still need native runners. There is no plaintext credential fallback. Agent configuration and profiles do not contain refresh tokens.</p>
<h2>Network and telemetry</h2><p>The local engine contract declares no required network and no external model calls. Non-auth manager operations are offline. Account commands are the only planned account-network surface. No production telemetry inventory, destination list, consent policy, or privacy terms have been approved, so production login remains disabled.</p>
<h2>Hosted service</h2><p>Hosted memory is a future, separately authorized product. It requires explicit contracts for tenant isolation, retention, residency, deletion, sync, training use, billing, and incidents. It is not implied by these local docs.</p>
""",
    ),
    Page(
        route="/docs/account/",
        title="Account and devices",
        description="What Kaleidoscope login does, how credentials are stored, and why account operations never upload or delete local memory.",
        body="""
<p class="lede">Login is intended for product-account and device workflows. It is not a hosted-memory connection and is not usable against a production issuer today.</p>
<h2>Locally verified manager flows</h2><p>Consolidated manager commit <code>fc15e1e…</code> implements authorization code with PKCE and a loopback callback plus device authorization for headless environments. It validates OIDC discovery, JWKS and RSA ID tokens; rotates refresh-token families; and fails closed on reuse. The local control plane also completes a one-time external-identity link after fresh provider authentication, returning only opaque identity IDs for unlinking. The package candidate has only credential-free account-provider refusal evidence until an approved OIDC deployment exists.</p>
<h2>Commands</h2><pre><code>kaleidoscope login
kaleidoscope login --device
kaleidoscope status --json
kaleidoscope logout
kaleidoscope logout --all-devices
kaleidoscope logout --local-only
kaleidoscope account link PROVIDER
kaleidoscope account identities
kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
kaleidoscope account revoke-session
kaleidoscope devices list
kaleidoscope devices revoke DEVICE_UUID
kaleidoscope profile account show [NAME]
kaleidoscope profile account bind ACCOUNT_UUID [NAME]
kaleidoscope profile account unbind [NAME]</code></pre>
<p><code>account identities</code> supplies the opaque UUID required by <code>account unlink</code>. <code>account revoke-session</code> has the deliberately narrow meaning of revoking the current session family. <code>--local-only</code> warns that it does not revoke a remote session. The profile-account commands write a local, non-secret account UUID reference only; they do not resolve the engine, contact the account service, alter a vault, or store a credential. Without approved provider configuration, remote account commands return <code>provider not configured</code>; the docs do not provide substitute endpoints.</p>
<h2>What logout changes</h2><p>Logout removes or revokes account credentials according to scope. It does not change local profile identity or vault bytes. Vault deletion is a separate explicit local operation.</p>
<h2>Control plane status</h2><p>The client contract is closed and account-only, but production identity-provider metadata, service deployment, credentials, domains, privacy terms, recovery, and deletion procedures remain gated. No production-login claim is made.</p>
""",
    ),
    Page(
        route="/docs/compatibility/",
        title="Compatibility",
        description="Kaleidoscope platform and harness compatibility policy, including the difference between build evidence and native release support.",
        body="""
<p class="lede">A platform or harness is supported only after the packaged artifact passes the canonical end-to-end proof on the named native runner and pinned host version.</p>
<table><thead><tr><th>Surface</th><th>Verified local evidence</th><th>Held before support</th></tr></thead><tbody>
<tr><td>macOS arm64</td><td>Full npm/Python SDK facades, exact native companions, auth-enabled manager and engine candidate, real stdio MCP, account refusal, clean install/update/rollback/uninstall, vault canary, and real Codex CLI configuration.</td><td>Production signature/notarization, approved terms, live OIDC/keychain, model/TUI/IDE acceptance, and protected publication.</td></tr>
<tr><td>macOS x64</td><td>Target metadata/refusal only.</td><td>Native binaries, package, runner, signing/notarization.</td></tr>
<tr><td>Linux x86_64/arm64</td><td>Source implementation and target metadata only; libc policy not frozen.</td><td>Native credential store, binaries, packages, runners, installer evidence.</td></tr>
<tr><td>Windows x86_64/arm64</td><td>Source implementation and target metadata only.</td><td>Native credential store, binaries, packages, runners, installer evidence.</td></tr>
<tr><td>Codex</td><td>Config transforms plus real pinned CLI add/list/get/remove and exact isolated rollback.</td><td>Model/TUI acceptance and a protected published install.</td></tr>
<tr><td>Claude Code / Cursor / OpenCode</td><td>Config render, dry run, idempotence, and exact rollback.</td><td>Installed CLIs/IDE and pinned live-host acceptance.</td></tr>
<tr><td>Framework clients</td><td>Generic MCP and adapter lifecycle suites passed with pinned versions and final-candidate non-auth conformance.</td><td>Live-provider lanes where required and protected published packages.</td></tr>
</tbody></table>
<p>Cross-compiling, extracting a foreign package, parsing configuration, or running a fake provider is useful evidence but not native support. Nothing in this table is a public availability claim.</p>
""",
    ),
    Page(
        route="/docs/benchmarks/",
        title="Benchmarks and evidence",
        description="How Kaleidoscope publishes clean, reproducible memory benchmarks without private-source dependencies or stale tool contracts.",
        body="""
<p class="lede">Benchmark results are meaningful only when the candidate, public contract, dataset, evaluator, and retrieval path are immutable and auditable.</p>
<div class="callout"><strong>Current result: functional smoke, no score.</strong> Benchmark PRs 3 and 4 are merged. The ordinary suite passed 20 tests with the live lane skipped; the opt-in macOS arm64 lane then passed against engine <code>988192ac9677…</code> and contract <code>a2357ed6c00e…</code>. It deliberately records <code>signature_verified: false</code>.</div>
<h2>What the live smoke proves</h2><p>Before vault work it checks both digests, loads the bundled model contract, creates a fresh isolated profile and vault, discovers runtime memory types, writes one explicit semantic delta, performs ranked and addressed search, and validates the closed launch descriptor.</p>
<h2>What it does not prove</h2><p>It records no BEAM score, runs no LLM evaluator, verifies no production signature, and makes no release-readiness claim. Full ingest, answer, judge, and report phases still require the dataset, evaluator credentials, preregistered procedure, and a signed packaged candidate.</p>
<h2>Protocol rules</h2><p>The harness performs one model-facing <code>search</code>, records explicit <code>top_k</code> and <code>maximum_context_bytes</code>, obtains vocabulary from the runtime, isolates conversations and candidate-bound caches, and refuses stale cross-candidate phase artifacts.</p>
<h2>Public repository</h2><p>The benchmark harness is the only milestone here already merged into its public repository. That does not make the private engine, unpublished clients, staged packages, or these docs public.</p>
""",
    ),
    Page(
        route="/docs/evidence/",
        title="Local evidence and production gates",
        description="Exact Kaleidoscope candidate digests, verified local DX milestones, remaining platform holds, and protected release approvals.",
        body=f"""
<p class="lede">Evidence is split into local functional proof, package/signature proof, native platform support, and protected production promotion. Passing one does not imply the others.</p>
<div class="callout"><strong>Machine-readable record.</strong> <a href="/staging-evidence.json">staging-evidence.json</a> carries the same public, source-free status. It contains no local paths, credentials, vault coordinates, or private engine source.</div>
<h2>Exact local candidate</h2>
<table><tbody><tr><th>SDK facade commit</th><td><code>{SDK_FACADE_COMMIT}</code></td></tr><tr><th>Distribution assembler commit</th><td><code>{DISTRIBUTION_ASSEMBLER_COMMIT}</code></td></tr><tr><th>Final evidence commit</th><td><code>{FINAL_EVIDENCE_COMMIT}</code></td></tr><tr><th>Final package evidence SHA-256</th><td><code>{FINAL_PACKAGE_EVIDENCE_SHA256}</code></td></tr><tr><th>Manager source commit</th><td><code>{MANAGER_SOURCE_COMMIT}</code></td></tr><tr><th>Manager candidate SHA-256</th><td><code>{MANAGER_SHA256}</code></td></tr><tr><th>Engine source commit</th><td><code>{ENGINE_SOURCE_COMMIT}</code></td></tr><tr><th>Engine candidate SHA-256</th><td><code>{ENGINE_CANDIDATE_SHA256}</code></td></tr><tr><th>Public contract SHA-256</th><td><code>{PUBLIC_CONTRACT_SHA256}</code></td></tr><tr><th>RC package version</th><td><code>0.1.0-rc.1</code> / Python <code>0.1.0rc1</code></td></tr><tr><th>Native target tested</th><td>macOS arm64 only</td></tr><tr><th>Production signature</th><td>Not verified</td></tr></tbody></table>
<h2>Milestones</h2>
<table><thead><tr><th>Slice</th><th>Exact evidence</th><th>What is true now</th></tr></thead><tbody>
<tr><td>DX-04 / DX-05B</td><td><code>{MANAGER_SOURCE_COMMIT}</code>, manager <code>{MANAGER_SHA256}</code></td><td>Consolidated friendly and auth/device manager surfaces passed locally; production provider is unconfigured.</td></tr>
<tr><td>DX-06A/B</td><td><code>{DISTRIBUTION_ASSEMBLER_COMMIT}</code>, proof <code>{PACKAGE_PROOF_SHA256}</code></td><td>The final source-bound archive and package set was reassembled with a test-only signature; a legally-bound refresh is in progress and no publication occurred.</td></tr>
<tr><td>DX-07</td><td><code>{SDK_FACADE_COMMIT}</code></td><td>Full Python/TypeScript clients, installed-payload resolvers, integrations, and both launchers passed locally; Apache-2.0 licensing is source-staged and no public remote is configured.</td></tr>
<tr><td>DX-09</td><td><code>{BENCHMARK_COMMIT}</code>, merged PRs 5/6; evidence <code>{DX09_FIXTURE_EVIDENCE_SHA256}</code></td><td>Two clean exact-candidate fixture runs produced byte-identical artifacts; no score, signature, performance, or production-comparability claim.</td></tr>
<tr><td>DX-10A</td><td><code>{DX10A_EVIDENCE_SHA256}</code></td><td>Final local package install, real MCP, account refusal, update, rollback, uninstall, and vault canary passed on macOS arm64; five non-native cells held.</td></tr>
<tr><td>DX-10B</td><td><code>{FINAL_EVIDENCE_COMMIT}</code>, evidence <code>{FINAL_PACKAGE_EVIDENCE_SHA256}</code></td><td>Fresh npm/Python facade <code>init</code>, <code>doctor</code>, Codex dry-run configuration, and MCP discovery passed. This is not real Codex/Claude/Cursor/OpenCode host acceptance.</td></tr>
</tbody></table>
<h2>Converged RC package proof</h2><p>The local archive <code>{LOCAL_ARCHIVE_SHA256}</code>, manifest <code>{LOCAL_MANIFEST_SHA256}</code>, build proof <code>{FINAL_BUILD_PROOF_SHA256}</code>, and combined package proof <code>{PACKAGE_PROOF_SHA256}</code> bind the full npm/Python SDK facades to their exact macOS arm64 native companions. The facades carry public client code, installed-payload resolution and both launchers; the companions carry manager <code>{MANAGER_SHA256}</code> and engine <code>{ENGINE_CANDIDATE_SHA256}</code> plus contract <code>{PUBLIC_CONTRACT_SHA256}</code>. The SBOM <code>{LOCAL_SBOM_SHA256}</code>, provenance <code>{LOCAL_PROVENANCE_SHA256}</code>, and signature envelope <code>{LOCAL_TEST_SIGNATURE_SHA256}</code> are all test-only local evidence. This closes local package-shape convergence, not protected production gates.</p>
<h2>Approval and credential gates</h2><ul><li>Apache-2.0 for the public manager, wrappers, integrations, and skill and CC BY 4.0 for original documentation are product-authorized and source-staged.</li><li>The engine object-code EULA, privacy, security, and support policies remain review drafts pending exact entity, jurisdiction, contacts, operational commitments, and external legal review.</li><li>Staging/production OIDC configuration and private control-plane deployment evidence.</li><li>Production signing/notarization identities, registry/CDN credentials, and native platform runners.</li><li>Package publication and production login remain separate deferred approvals.</li></ul>
""",
    ),
    Page(
        route="/docs/release-notes/",
        title="Release notes",
        description="Versioned Kaleidoscope release notes bound to immutable package and public-contract digests.",
        body="""
<p class="lede">Release notes become authoritative only when they name the exact signed package, final manager, engine, and public-contract digests.</p>
<h2>Unreleased local staging — 2026-08-22</h2><ul><li>The consolidated auth-enabled manager is deterministically bound at <code>fc6afb3606fc…</code>.</li><li>SDK commit <code>fc15e1e…</code> places the full public TypeScript/Python clients, installed-payload resolvers, account identity lifecycle, profile-account binding, and both launchers in the facade packages.</li><li>Distribution assembler <code>af892d1…</code> pairs those facades with macOS arm64 native companions containing the manager and proprietary object-code engine; the exact package proof is <code>095f91ca…</code>.</li><li>DX-09 native smoke plus the credential-free deterministic fixture pipeline merged in PRs 5/6; no benchmark score was produced.</li><li>DX-10A historic local macOS arm64 lifecycle evidence remains recorded for its then-current candidate.</li><li>Final DX-10B package evidence passed fresh npm/Python facade init, doctor, Codex dry-run configuration, and stdio MCP discovery; other platforms and live host/model/IDE acceptance remain held.</li></ul>
<h2>Promotion rule</h2><p>A release entry must record public availability, supported targets and pinned host versions, known limitations, migration requirements, security fixes, all package checksums, SBOM/provenance, exact rollback identity, license/EULA links, and production account/privacy terms. Publication and documentation promotion are separate protected actions.</p>
""",
    ),
    Page(
        route="/docs/troubleshooting/",
        title="Troubleshooting",
        description="Diagnose Kaleidoscope profile, descriptor, host-configuration, MCP startup, and account problems without leaking local memory or credentials.",
        body="""
<p class="lede">Start with <code>kaleidoscope doctor</code> for local profile/engine/host issues. Account commands have a separate error boundary.</p>
<h2>The host cannot find the tools</h2><ol><li>Confirm the active profile and exact candidate/package digest are valid.</li><li>Preview the host connection and inspect only the manager-owned block.</li><li>Restart the host after a successful connect.</li><li>Confirm the discovered tools are exactly <code>search</code> and <code>remember</code>.</li></ol>
<h2>OpenCode configuration is refused</h2><p>Stable and beta-v2 shapes differ. The manager adopts an unambiguous existing shape or an explicit version selection; it never silently migrates stable configuration to beta. Remove conflicting duplicate Kaleidoscope entries and retry the dry run.</p>
<h2>A profile points to the wrong place</h2><p>Do not edit the profile by hand. Import the intended existing vault or initialize an explicit new root. A missing or invalid root is refused rather than created implicitly.</p>
<h2>Login says provider not configured</h2><p>That is the expected staging result: no production account origin, issuer, audience, or client ID is published. Do not invent endpoints or delete/recreate the local vault. Account status and local memory are separate.</p>
<h2>I cannot install the package</h2><p>No public installation channel exists. The local archive, npm tarballs, and wheels are evidence artifacts created with a test-only signature, not downloadable releases.</p>
<h2>Before sharing diagnostics</h2><p>Remove local paths, account identifiers, provider keys, tokens, memory content, queries, results, and vault coordinates. Use the redacted doctor artifact intended for support.</p>
""",
    ),
    Page(
        route="/docs/migration/",
        title="Migration from historical tool contracts",
        description="How to migrate historical Kaleidoscope agent integrations to the public search and remember MCP contract.",
        body="""
<p class="lede">Current agents discover exactly <code>search</code> and <code>remember</code>. Historical names are not aliases and must be removed from host allowlists and prompts.</p>
<h2>Retrieval</h2><p>Replace <code>recall</code>, <code>compile</code>, and <code>read_memory</code> with <code>search</code>. Send <code>query</code> for ranked retrieval and <code>memory_id</code> for an addressed read. Ranked results are under <code>selected_hits</code>. Use <code>top_k</code>, not <code>limit</code>.</p>
<h2>Writing</h2><p>Replace <code>ingest_memory</code> or prose-inference paths with explicit <code>remember</code> semantic deltas. The runtime does not infer entities, facts, relationships, or dates from prose.</p>
<h2>Other retired names</h2><p>Remove <code>merge_verdict</code>, <code>ontology_proposal</code>, <code>policy</code>, <code>policy_patch</code>, <code>ope</code>, and <code>replay</code> from agent definitions. The generated candidate contract marks them retired.</p>
<h2>Operator feedback</h2><p><code>feedback</code> is an operator command, not an MCP tool. Public search does not return its required decision handle, so a model has no supported public path to call it. Do not reconstruct private state or advertise a fake attribution workflow.</p>
""",
    ),
)


INTEGRATION_PAGES = (
    Page(
        route="/docs/integrations/codex/",
        title="Codex integration",
        description="Connect Kaleidoscope to Codex through the local manager and a two-tool stdio MCP configuration.",
        body="""
<p class="lede">Codex uses the same profile-first stdio descriptor as every other harness. The manager owns configuration changes so they can be previewed, backed up, and removed exactly.</p>
<h2>Connect a project</h2><pre><code>kaleidoscope connect codex --profile default --project "$PWD" --dry-run
kaleidoscope connect codex --profile default --project "$PWD"
kaleidoscope instructions install agents --project "$PWD"</code></pre>
<p>The generated configuration names an absolute local engine command, <code>mcp --profile default</code>, and exactly <code>search</code> and <code>remember</code>. It does not add vault coordinates, provider keys, or account credentials.</p>
<h2>Evidence boundary</h2><p>The local candidate passed isolated <code>codex mcp add/list/get/remove</code>, byte-exact rollback, and real stdio discovery. That proves the CLI configuration lane on macOS arm64; it does not make a model, TUI, IDE, package, or production account claim.</p>
""",
    ),
    Page(
        route="/docs/integrations/claude-code/",
        title="Claude Code integration",
        description="Configure Claude Code with the Kaleidoscope local stdio MCP descriptor and concise project guidance.",
        body="""
<p class="lede">Claude Code receives one local stdio MCP server definition and an optional owner-marked project pointer to the public skill.</p>
<h2>Preview first</h2><pre><code>kaleidoscope connect claude --profile default --project "$PWD" --dry-run
kaleidoscope connect claude --profile default --project "$PWD"
kaleidoscope instructions install claude --project "$PWD"</code></pre>
<p>The manager writes only its owned entry in <code>.mcp.json</code>, retains unrelated configuration, and refuses ambiguous or modified ownership boundaries. The descriptor publishes only <code>search</code> and <code>remember</code>.</p>
<h2>Evidence boundary</h2><p>Renderer, dry-run, idempotence, and rollback tests passed locally. Live Claude Code acceptance remains held until an installed, pinned host lane is run against a released package.</p>
""",
    ),
    Page(
        route="/docs/integrations/claude-agent-sdk/",
        title="Claude Agent SDK integration",
        description="Use one Claude Agent SDK client and a strict Kaleidoscope MCP allowlist for an agent run.",
        body="""
<p class="lede">The Python recipe creates one Claude Agent SDK client for the intended run and passes a strict stdio MCP configuration with explicit Kaleidoscope tool names.</p>
<h2>Allowed tools</h2><pre><code>mcp__kaleidoscope__search
mcp__kaleidoscope__remember</code></pre>
<p>Provider credentials remain the application’s concern. The descriptor has an empty override environment, so account tokens, vault coordinates, and provider keys do not enter the MCP child process.</p>
<h2>Evidence boundary</h2><p>The local lifecycle test uses a deterministic client double to prove one client and the exact allowlist. It is not a live-provider acceptance claim.</p>
""",
    ),
    Page(
        route="/docs/integrations/cursor/",
        title="Cursor integration",
        description="Safely configure Cursor with Kaleidoscope’s profile-first local MCP descriptor and project rule pointer.",
        body="""
<p class="lede">Cursor uses the same local MCP command and only the two public memory tools. The manager makes the JSON mutation reversible and adds a small project rule only when requested.</p>
<h2>Connect and guide</h2><pre><code>kaleidoscope connect cursor --profile default --project "$PWD" --dry-run
kaleidoscope connect cursor --profile default --project "$PWD"
kaleidoscope instructions install cursor --project "$PWD"</code></pre>
<p>Existing unrelated entries stay untouched. Tampered receipts, conflicting names, malformed configuration, symlinked files, and concurrent edits are refused for manual review.</p>
<h2>Evidence boundary</h2><p>Local renderer and rollback coverage passed. A pinned Cursor build and installed-package acceptance remain held.</p>
""",
    ),
    Page(
        route="/docs/integrations/opencode/",
        title="OpenCode integration",
        description="Configure the stable or explicitly selected beta OpenCode MCP format for Kaleidoscope.",
        body="""
<p class="lede">OpenCode stable v1 and beta v2 use different configuration shapes. Kaleidoscope never guesses or silently migrates between them.</p>
<h2>Stable v1 by default</h2><pre><code>kaleidoscope connect opencode --profile default --project "$PWD" --dry-run
kaleidoscope connect opencode --profile default --project "$PWD"</code></pre>
<h2>Explicit beta v2</h2><pre><code>kaleidoscope connect opencode --profile default --project "$PWD" --opencode-version beta-v2 --dry-run</code></pre>
<p>The stable entry is a direct local command; beta v2 uses the explicit server shape with code mode disabled so <code>search</code> and <code>remember</code> remain visible. Ambiguous dual shapes are refused.</p>
<h2>Evidence boundary</h2><p>Both renderers and safe mutation paths passed locally. Installed OpenCode acceptance remains held.</p>
""",
    ),
    Page(
        route="/docs/integrations/generic-mcp/",
        title="Generic MCP integration",
        description="Launch Kaleidoscope as a persistent local stdio MCP server from the manager-generated descriptor.",
        body="""
<p class="lede">Any standard MCP host can obtain the canonical child-process descriptor from the manager and retain one initialized session for its run.</p>
<h2>Get the descriptor</h2><pre><code>kaleidoscope config --profile default --json</code></pre>
<p>The result is intentionally closed: an absolute command, <code>mcp --profile NAME</code>, <code>stdio</code>, exactly two tools, and an empty environment. Do not add vault coordinates or tokens.</p>
<h2>Persistent session rule</h2><p>Initialize once, discover exactly <code>search</code> and <code>remember</code>, then reuse the session through the agent or application run. A controller-owned raw search replaces a model-facing MCP search for that turn; it does not duplicate it.</p>
<h2>Evidence boundary</h2><p>Python MCP 1.x/2.x and TypeScript MCP client suites exercised persistent process, restart, teardown, malformed discovery, structured output, and tool-refusal behavior against the local candidate.</p>
""",
    ),
    Page(
        route="/docs/integrations/langchain/",
        title="LangChain integration",
        description="Use LangChain’s MCP adapter with one Kaleidoscope session and no shadow memory store.",
        body="""
<p class="lede">Use the official LangChain MCP adapter to load the two Kaleidoscope tools inside one adapter session. Kaleidoscope is not a <code>BaseStore</code> implementation.</p>
<h2>Lifecycle</h2><p>Open the stdio adapter once around the application’s intended agent run, load and filter the two tools, then close the adapter after the run. The application supplies its model-provider credentials separately.</p>
<h2>Boundary</h2><p>Do not implement a parallel LangChain memory or summarize messages into a second store. The MCP server remains the one canonical memory owner.</p>
<h2>Evidence boundary</h2><p>The pinned local LangChain adapter suite verified remembered and searched values share one MCP process. It uses a deterministic provider double and does not claim live provider behavior.</p>
""",
    ),
    Page(
        route="/docs/integrations/langgraph/",
        title="LangGraph integration",
        description="Use the LangChain MCP adapter inside a LangGraph tool node without making Kaleidoscope a graph store.",
        body="""
<p class="lede">LangGraph uses the same one-session MCP adapter as LangChain, placed in the graph’s tool node for the run.</p>
<h2>Boundary</h2><p>Kaleidoscope is not a LangGraph checkpointer or <code>BaseStore</code>. Graph state and local durable memory remain distinct so the integration does not create a second canonical owner.</p>
<h2>Lifecycle</h2><p>Open the adapter before executing the graph, pass the filtered MCP tools into the tool node, and close it once execution is complete. Reuse the session across node calls.</p>
<h2>Evidence boundary</h2><p>The pinned local graph test exercised a tool node calling <code>remember</code> then <code>search</code> through the same MCP process.</p>
""",
    ),
    Page(
        route="/docs/integrations/openai-agents-sdk/",
        title="OpenAI Agents SDK integration",
        description="Attach a persistent Kaleidoscope stdio MCP server to an OpenAI Agents SDK agent with a strict two-tool contract.",
        body="""
<p class="lede">Use the official stdio MCP server lifecycle supplied by the OpenAI Agents SDK, keeping one server alive for the agent run and filtering the model-facing tools to Kaleidoscope’s two public operations.</p>
<h2>Tool boundary</h2><p>The agent may call <code>search</code> and <code>remember</code>. Controller, account, and operator commands stay outside the model tool set. Provider credentials are supplied by the application, never through the Kaleidoscope descriptor.</p>
<h2>Lifecycle</h2><p>Create the MCP server as a managed resource around the run, then close it deterministically. Do not reopen a separate engine process for each tool call.</p>
<h2>Evidence boundary</h2><p>Pinned Python and TypeScript adapters passed scripted-model lifecycle tests with one persistent server. This is not a live-model or account claim.</p>
""",
    ),
    Page(
        route="/docs/integrations/crewai/",
        title="CrewAI integration",
        description="Use the CrewAI MCP adapter as one persistent context with Kaleidoscope’s two-tool local contract.",
        body="""
<p class="lede">CrewAI uses one stdio MCP adapter context for the crew run. The adapter exposes only the Kaleidoscope tools that are appropriate for the model.</p>
<h2>Lifecycle</h2><p>Construct the adapter with the manager-generated local descriptor, enter it once, select <code>search</code> and <code>remember</code>, run the crew, then close the context. Do not recreate the server for each task.</p>
<h2>Boundary</h2><p>The framework owns provider configuration and crew state. Kaleidoscope owns only its local memory and does not receive model-provider credentials or account tokens.</p>
<h2>Evidence boundary</h2><p>The pinned adapter was exercised against the local MCP fixture with one persistent process and explicit tool filtering.</p>
""",
    ),
)


LEGAL_PAGES = (
    Page(
        route="/docs/legal/",
        title="Licenses and product terms",
        description="Kaleidoscope public software and documentation licenses, proprietary engine EULA, privacy notice, security policy, and support policy.",
        body="""
<p class="lede">The public software, original documentation, and proprietary
engine have deliberately separate license boundaries.</p>
<div class="callout"><strong>Review status.</strong> Apache-2.0 and CC BY 4.0
are the authorized public license selections. The EULA, privacy, security, and
support text remains a source-controlled review draft until the production
entity, jurisdiction, contacts, operational commitments, and external legal
review are complete.</div>
<ul>
<li><a href="/documentation-license.txt">Documentation license scope</a> and
<a href="/legal/CC-BY-4.0.txt">CC BY 4.0 legal code</a>.</li>
<li><a href="/docs/legal/engine-eula/">Proprietary engine EULA</a>.</li>
<li><a href="/docs/legal/privacy-notice/">Privacy notice</a>.</li>
<li><a href="/docs/legal/security-policy/">Security policy</a>.</li>
<li><a href="/docs/legal/support-policy/">Support policy</a>.</li>
</ul>
<p>The Apache-2.0 license for the public manager, SDKs, wrappers,
integrations, and skill is carried in those source and package repositories.
It does not license the native engine, model weights, trademarks, or
third-party material.</p>
""",
    ),
    Page(
        route="/docs/legal/engine-eula/",
        title="Proprietary engine EULA",
        description="Review draft of the Kaleidoscope proprietary native engine object-code end user license agreement.",
        body=legal_document_body(
            "ENGINE-EULA.txt",
            "Terms proposed for proprietary Kaleidoscope engine object code; public Apache-2.0 components and CC BY 4.0 documentation remain separate.",
        ),
    ),
    Page(
        route="/docs/legal/privacy-notice/",
        title="Privacy notice",
        description="Review draft of the Kaleidoscope local-product privacy notice and local-memory/account data boundary.",
        body=legal_document_body(
            "PRIVACY-NOTICE.txt",
            "The local engine does not imply memory upload; optional account, site, purchase, and support processing require explicit production disclosures.",
        ),
    ),
    Page(
        route="/docs/legal/security-policy/",
        title="Security policy",
        description="Review draft of supported-version, vulnerability reporting, safe-harbor, and incident communication terms.",
        body=legal_document_body(
            "SECURITY-POLICY.txt",
            "A proposed coordinated-disclosure policy; no production intake exists until a monitored private channel and supported-version table are published.",
        ),
    ),
    Page(
        route="/docs/legal/support-policy/",
        title="Support policy",
        description="Review draft of Kaleidoscope standard product support scope, exclusions, severity guidance, and response targets.",
        body=legal_document_body(
            "SUPPORT-POLICY.txt",
            "Proposed standard support terms; prereleases and test-signed packages remain unsupported and no SLA exists without a separate written plan.",
        ),
    ),
)


PAGES += INTEGRATION_PAGES + LEGAL_PAGES + (
    Page(
        route="/docs/hosted/",
        title="Hosted memory (future)",
        description="The boundary between Kaleidoscope’s local memory product and a future hosted-memory service.",
        noindex=True,
        body="""
<p class="lede">Hosted memory is not available. This page exists to make that boundary explicit, not to advertise an endpoint, API, waitlist, or implicit sync path.</p>
<h2>What local Kaleidoscope does today</h2><p>The local CLI, manager, and stdio MCP server keep canonical memory in a user-owned local vault. Login and device management are separate account workflows; they do not upload or host local memory.</p>
<h2>What a future hosted service would require</h2><p>A separate product decision must define tenant authorization, consent, data residency, retention, deletion, export/import, synchronization, billing, incident handling, and model-training policy. None is implied by a local profile or account login.</p>
<p>This future-facing route is intentionally excluded from search indexing and the documentation sitemap.</p>
""",
    ),
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "p", "li", "tr", "pre"}:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")
        if tag == "a":
            self.href = dict(attrs).get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href:
            self.parts.append(f" ({self.href})")
            self.href = None
        if tag in {"h1", "h2", "h3", "p", "li", "tr", "pre"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts))
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n[ \t]+", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def load_metadata(path: Path | None, production: bool) -> dict[str, str]:
    if path is None:
        if production:
            raise SystemExit("production build requires --release-metadata")
        return {
            "release_version": "unreleased",
            "public_contract_sha256": "not-yet-bound",
            "availability": "staging",
            "updated_at": TODAY.isoformat(),
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    allowed = {
        "release_version",
        "public_contract_sha256",
        "availability",
        "updated_at",
    }
    if set(data) != allowed or not all(isinstance(data[key], str) for key in allowed):
        raise SystemExit("release metadata must contain exactly four string fields")
    if production:
        if data["availability"] not in {"release_candidate", "released"}:
            raise SystemExit(
                "production build requires release_candidate or released metadata"
            )
        if data["release_version"] in {"", "unreleased", "latest"}:
            raise SystemExit("production build requires an immutable release version")
        if not HEX64.fullmatch(data["public_contract_sha256"]):
            raise SystemExit(
                "production build requires a lowercase 64-hex public contract digest"
            )
        try:
            date.fromisoformat(data["updated_at"])
        except ValueError as error:
            raise SystemExit("updated_at must be YYYY-MM-DD") from error
    return data


def nav_link(route: str, label: str, current: str) -> str:
    active = (
        ' aria-current="page"'
        if route == current
        or (route == "/docs/integrations/" and current.startswith(route))
        else ""
    )
    return f'<a href="{route}"{active}>{html.escape(label)}</a>'


def structured_data(page: Page | None, canonical: str) -> str:
    if page is None:
        data = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Organization",
                    "@id": f"{DOMAIN}/#organization",
                    "name": "Kleos Research",
                    "url": "https://kleosresearch.xyz/",
                },
                {
                    "@type": "SoftwareApplication",
                    "@id": f"{DOMAIN}/#software",
                    "name": "Kaleidoscope",
                    "applicationCategory": "DeveloperApplication",
                    "operatingSystem": "macOS",
                    "softwareVersion": "unreleased",
                    "description": "Local native memory for AI agents, exposed through a staged manager CLI and stdio MCP contract.",
                    "publisher": {"@id": f"{DOMAIN}/#organization"},
                    "url": DOMAIN,
                },
            ],
        }
    else:
        crumbs = [
            {"@type": "ListItem", "position": 1, "name": "Kaleidoscope", "item": f"{DOMAIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Docs", "item": f"{DOMAIN}/docs/"},
        ]
        if page.route != "/docs/":
            route_name = page.title
            crumbs.append(
                {
                    "@type": "ListItem",
                    "position": len(crumbs) + 1,
                    "name": route_name,
                    "item": canonical,
                }
            )
        data = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "TechArticle",
                    "headline": page.title,
                    "description": page.description,
                    "dateModified": TODAY.isoformat(),
                    "mainEntityOfPage": canonical,
                    "publisher": {"@id": f"{DOMAIN}/#organization"},
                },
                {
                    "@type": "BreadcrumbList",
                    "itemListElement": crumbs,
                },
            ],
        }
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace(
        "</", "<\\/"
    )


def head(
    title: str,
    description: str,
    canonical: str,
    production: bool,
    page: Page | None,
    *,
    noindex: bool = False,
) -> str:
    robots = "index,follow" if production and not noindex else "noindex,nofollow"
    full_title = (
        "Kaleidoscope — local memory for agents"
        if page is None
        else f"{title} | Kaleidoscope"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(full_title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="stylesheet" href="/assets/site.css">
  <meta name="theme-color" content="#0b0b0c">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Kaleidoscope">
  <meta property="og:title" content="{html.escape(full_title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Kaleidoscope — local memory for agents">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(full_title, quote=True)}">
  <meta name="twitter:description" content="{html.escape(description, quote=True)}">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <meta name="twitter:image:alt" content="Kaleidoscope — local memory for agents">
  <script type="application/ld+json">{structured_data(page, canonical)}</script>
</head>"""


def header(current: str, metadata: dict[str, str]) -> str:
    return f"""<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell">
  <a class="brand" href="/"><span>K</span> Kaleidoscope</a>
  <nav class="site-nav" aria-label="Primary">
    {nav_link("/docs/", "Docs", current)}
    {nav_link("/docs/integrations/", "Integrations", current)}
    {nav_link("/docs/security/", "Security", current)}
    <a href="https://github.com/kleos-research">GitHub</a>
  </nav>
</div></header>
<div class="status"><div class="shell"><span class="status-dot" aria-hidden="true"></span><strong>{html.escape(metadata["availability"])}</strong><span>Release {html.escape(metadata["release_version"])} · contract {html.escape(metadata["public_contract_sha256"][:12])}</span></div></div>"""


def footer() -> str:
    return """<footer class="site-footer"><div class="shell">
  <span>Kaleidoscope by <a href="https://kleosresearch.xyz/">Kleos Research</a></span>
  <nav aria-label="Footer"><a href="/docs/legal/">Licenses &amp; terms</a><a href="/docs/legal/privacy-notice/">Privacy notice</a><a href="/docs/legal/security-policy/">Security policy</a><a href="/docs/legal/support-policy/">Support</a><a href="/llms.txt">llms.txt</a></nav>
</div></footer></body></html>"""


def render_home(metadata: dict[str, str], production: bool) -> str:
    description = "Local native memory for AI agents: one CLI and stdio MCP profile across Codex, Claude, Cursor, OpenCode, and agent frameworks."
    return (
        head("Kaleidoscope", description, f"{DOMAIN}/", production, None)
        + header("/", metadata)
        + """
<main id="main">
  <section class="hero shell">
    <p class="eyebrow">Local memory for agents</p>
    <h1>Carry the work forward.</h1>
    <p class="lede">Kaleidoscope gives agents one local memory across harnesses. The native engine stays on your machine; the manager candidate connects it safely through a CLI and exactly two MCP tools.</p>
    <div class="actions"><a class="button" href="/docs/getting-started/">Preview the workflow</a><a class="button secondary" href="/docs/evidence/">Inspect the evidence</a></div>
  </section>
  <section class="shell grid" aria-label="Product principles">
    <article class="card"><h2>Local by construction</h2><p>Memory content, queries, results, identities, and vault paths are not account-service data.</p></article>
    <article class="card"><h2>Harness neutral</h2><p>Codex, Claude, Cursor, OpenCode, and framework clients consume the same profile and MCP contract.</p></article>
    <article class="card"><h2>Inspectable boundary</h2><p>The staged bundle binds object code, manager, model, contract, SBOM, and provenance; license source is staged separately while production signing, final terms, and publication remain gated.</p></article>
  </section>
  <section class="shell hero"><p class="eyebrow">Developer contract</p><h2>Two tools, one persistent process.</h2><p class="lede"><code>search</code> retrieves ranked or addressed memory. <code>remember</code> writes explicit durable semantic deltas. Operator commands never enter the agent tool list.</p></section>
</main>"""
        + footer()
    )


def render_page(page: Page, metadata: dict[str, str], production: bool) -> str:
    canonical = f"{DOMAIN}{page.route}"
    sidebar = "".join(
        f"<li>{nav_link(route, label, page.route)}</li>" for route, label in DOC_NAV
    )
    return (
        head(
            page.title,
            page.description,
            canonical,
            production,
            page,
            noindex=page.noindex,
        )
        + header(page.route, metadata)
        + f"""
<main id="main" class="shell layout">
  <nav class="sidebar" aria-label="Documentation"><strong>Documentation</strong><ul>{sidebar}</ul></nav>
  <article class="content"><span class="release-tag">{html.escape(metadata["release_version"])} · {html.escape(metadata["public_contract_sha256"][:12])}</span><h1>{html.escape(page.title)}</h1>{page.body}</article>
</main>"""
        + footer()
    )


def route_path(output: Path, route: str) -> Path:
    if route == "/":
        return output / "index.html"
    return output / route.strip("/") / "index.html"


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def plain_text(body: str) -> str:
    parser = TextExtractor()
    parser.feed(body)
    return parser.text()


def prepare_output(output: Path) -> None:
    """Replace only an empty directory or a prior generated artifact."""
    if output == ROOT or output in ROOT.parents or output.is_symlink():
        raise SystemExit(f"refusing unsafe output directory: {output}")
    if output.exists():
        if not output.is_dir():
            raise SystemExit(f"output exists and is not a directory: {output}")
        entries = list(output.iterdir())
        if entries:
            manifest_path = output / "site-manifest.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                raise SystemExit(
                    f"refusing to replace non-generated output directory: {output}"
                ) from exc
            if manifest.get("schema_version") != "kaleidoscope.docs-artifact.v1":
                raise SystemExit(f"refusing output with an unknown manifest: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)


def build(output: Path, metadata: dict[str, str], production: bool) -> None:
    prepare_output(output)
    shutil.copyfile(ROOT / "CNAME", output / "CNAME")
    for asset in (
        "favicon.svg",
        "favicon-32.png",
        "favicon.ico",
        "apple-touch-icon.png",
    ):
        shutil.copyfile(ROOT / asset, output / asset)
    (output / "assets").mkdir(exist_ok=True)
    for asset in ("site.css", "kaleidoscope-og.png"):
        shutil.copyfile(ROOT / "assets" / asset, output / "assets" / asset)
    write_text(output / ".nojekyll", "")
    write_text(route_path(output, "/"), render_home(metadata, production))
    for page in PAGES:
        write_text(
            route_path(output, page.route), render_page(page, metadata, production)
        )

    not_found = head(
        "Page not found",
        "The requested Kaleidoscope documentation page was not found.",
        f"{DOMAIN}/404.html",
        False,
        None,
    )
    not_found += (
        header("", metadata)
        + """<main id="main" class="shell hero"><p class="eyebrow">404</p><h1>That page is not in this release.</h1><p class="lede">Use the documentation index, getting-started guide, or security boundary instead.</p><div class="actions"><a class="button" href="/docs/">Documentation</a><a class="button secondary" href="/docs/getting-started/">Getting started</a></div></main>"""
        + footer()
    )
    write_text(output / "404.html", not_found)

    urls = [
        f"{DOMAIN}/",
        *(f"{DOMAIN}{page.route}" for page in PAGES if not page.noindex),
    ]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(
            f"  <url><loc>{html.escape(url)}</loc><lastmod>{metadata['updated_at']}</lastmod></url>\n"
            for url in urls
        )
        + "</urlset>"
    )
    write_text(output / "sitemap.xml", sitemap)
    robots = (
        "User-agent: *\nAllow: /\nSitemap: https://memory.kleosresearch.xyz/sitemap.xml"
        if production
        else "User-agent: *\nDisallow: /"
    )
    write_text(output / "robots.txt", robots)

    security = f"""# STAGING ONLY — no production security intake is published.
Contact: {DOMAIN}/docs/security/
Canonical: {DOMAIN}/.well-known/security.txt
Expires: 2026-09-30T23:59:59Z
Preferred-Languages: en
Policy: {DOMAIN}/docs/security/
"""
    write_text(output / ".well-known" / "security.txt", security)

    llms = f"""# Kaleidoscope

> Local native memory for agents, exposed through a manager CLI and persistent stdio MCP. Release status: {metadata["availability"]} ({metadata["release_version"]}); no package or production login is public.

- [Documentation]({DOMAIN}/docs/): product and developer overview
- [Getting started]({DOMAIN}/docs/getting-started/): protected RC install, profile and reversible host workflow
- [Packages]({DOMAIN}/docs/packages/): full SDK facades, native companions, exact macOS arm64 RC hashes and gates
- [CLI reference]({DOMAIN}/docs/cli/): exact local manager-candidate commands
- [MCP reference]({DOMAIN}/docs/mcp/): candidate-bound `search` and `remember` contract
- [Integrations]({DOMAIN}/docs/integrations/): Codex, Claude, Cursor, OpenCode, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, and generic MCP
- [Security]({DOMAIN}/docs/security/): package, process, and account isolation evidence
- [Privacy]({DOMAIN}/docs/privacy/): local/account data boundary, credential storage, and telemetry status
- [Licenses and terms]({DOMAIN}/docs/legal/): Apache-2.0 public software boundary, CC BY 4.0 documentation, and proprietary engine EULA
- [Privacy notice]({DOMAIN}/docs/legal/privacy-notice/): review draft of production privacy terms
- [Security policy]({DOMAIN}/docs/legal/security-policy/): review draft of disclosure, safe-harbor, and supported-version policy
- [Support policy]({DOMAIN}/docs/legal/support-policy/): review draft of scope, exclusions, severity, and response targets
- [Account]({DOMAIN}/docs/account/): login manages account/device state and does not upload local memory
- [Operations]({DOMAIN}/docs/operations/): backup, restore, uninstall, update, and exact vault deletion
- [Compatibility]({DOMAIN}/docs/compatibility/): verified local cells versus native/support holds
- [Benchmarks]({DOMAIN}/docs/benchmarks/): merged candidate-bound smoke, with no score or release claim
- [Release evidence]({DOMAIN}/docs/evidence/): exact digests, converged package proof, milestone commits, and protected gates
- [Public agent skill]({DOMAIN}/SKILL.md): bounded retrieval and verified durable writes
- [Agent instructions]({DOMAIN}/agent-instructions.md): safe manager-installed AGENTS, CLAUDE, and Cursor pointers
- [Machine-readable staging evidence]({DOMAIN}/staging-evidence.json): source-free milestone and gate record
- [Candidate CLI help]({DOMAIN}/reference/kaleidoscope-cli.candidate.txt): exact consolidated manager help snapshot
- [Candidate MCP reference]({DOMAIN}/reference/kaleidoscope-mcp.candidate.json): exact engine and public-contract binding plus tool fields

The `0.1.0-rc.1` package contract is verified only for macOS arm64. SDK commit {SDK_FACADE_COMMIT} puts the full public TypeScript/Python clients, installed-payload resolvers and both `kaleidoscope`/`kscope` launchers in the facade packages. Assembler commit {DISTRIBUTION_ASSEMBLER_COMMIT} pairs them with native companions containing manager object code and the proprietary object code engine; final evidence commit {FINAL_EVIDENCE_COMMIT} freezes the result. Exact hashes: release archive {LOCAL_ARCHIVE_SHA256}; manifest {LOCAL_MANIFEST_SHA256}; build proof {FINAL_BUILD_PROOF_SHA256}; package proof {PACKAGE_PROOF_SHA256}; npm facade {NPM_FACADE_SHA256}; npm native companion {NPM_NATIVE_SHA256}; Python facade {PYTHON_FACADE_SHA256}; Python native companion {PYTHON_NATIVE_SHA256}; SBOM {LOCAL_SBOM_SHA256}; provenance {LOCAL_PROVENANCE_SHA256}; test-only signature envelope {LOCAL_TEST_SIGNATURE_SHA256}. The engine source is not in any public surface. Manager SHA-256 {MANAGER_SHA256}; engine SHA-256 {ENGINE_CANDIDATE_SHA256}; public contract SHA-256 {PUBLIC_CONTRACT_SHA256}; final package evidence SHA-256 {FINAL_PACKAGE_EVIDENCE_SHA256}; DX-09 fixture evidence SHA-256 {DX09_FIXTURE_EVIDENCE_SHA256}; historic DX-10A evidence SHA-256 {DX10A_EVIDENCE_SHA256}; historic pre-final Codex-host evidence SHA-256 {DX10B_HOST_EVIDENCE_SHA256}. Final package evidence proves fresh npm/Python facade init, doctor, Codex dry-run configuration, and MCP discovery—not real host/IDE acceptance. All packages remain private, test-signed, unpublished and outside a support claim. Hosted memory is planned, not available. Apache-2.0 and CC BY 4.0 source licensing and review-draft product terms are staged; production signing, final legal review, registry publication, and login remain separately gated.
"""
    write_text(output / "llms.txt", llms)

    chunks = [llms.strip()]
    for page in PAGES:
        if page.noindex:
            continue
        chunks.append(
            f"# {page.title}\n\nURL: {DOMAIN}{page.route}\nRelease: {metadata['release_version']}\nUpdated: {metadata['updated_at']}\n\n{plain_text(page.body)}"
        )
    chunks.extend(
        [
            f"# Public agent skill\n\nURL: {DOMAIN}/SKILL.md\nSHA-256: {PUBLIC_SKILL_SHA256}\n\n{PUBLIC_FILES['SKILL.md'].read_text(encoding='utf-8').strip()}",
            f"# Candidate CLI help\n\nURL: {DOMAIN}/reference/kaleidoscope-cli.candidate.txt\nSource: consolidated manager commit {MANAGER_SOURCE_COMMIT}\nSHA-256: {MANAGER_SHA256}\n\n{MANAGER_HELP.strip()}",
            f"# Candidate MCP reference\n\nURL: {DOMAIN}/reference/kaleidoscope-mcp.candidate.json\n\n{json.dumps(MCP_REFERENCE, indent=2, sort_keys=True)}",
            f"# Machine-readable staging evidence\n\nURL: {DOMAIN}/staging-evidence.json\n\n{json.dumps(STAGING_EVIDENCE, indent=2, sort_keys=True)}",
        ]
    )
    write_text(output / "llms-full.txt", "\n\n---\n\n".join(chunks))

    write_text(
        output / "staging-evidence.json",
        json.dumps(STAGING_EVIDENCE, indent=2, sort_keys=True),
    )
    write_text(
        output / "reference" / "kaleidoscope-cli.candidate.txt", MANAGER_HELP
    )
    write_text(
        output / "reference" / "kaleidoscope-mcp.candidate.json",
        json.dumps(MCP_REFERENCE, indent=2, sort_keys=True),
    )

    public_source_digests = {}
    for relative, source in PUBLIC_FILES.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        public_source_digests[relative] = hashlib.sha256(
            source.read_bytes()
        ).hexdigest()

    manifest_items = []
    for path in sorted(file for file in output.rglob("*") if file.is_file()):
        relative = path.relative_to(output).as_posix()
        if relative == "site-manifest.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_items.append(
            {"path": relative, "sha256": digest, "size_bytes": path.stat().st_size}
        )
    manifest = {
        "schema_version": "kaleidoscope.docs-artifact.v1",
        "mode": "production" if production else "staging",
        "release": metadata,
        "public_source_sha256": public_source_digests,
        "files": manifest_items,
    }
    write_text(
        output / "site-manifest.json", json.dumps(manifest, indent=2, sort_keys=True)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs")
    parser.add_argument("--release-metadata", type=Path)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    metadata = load_metadata(args.release_metadata, args.production)
    build(args.output.expanduser().absolute(), metadata, args.production)


if __name__ == "__main__":
    main()

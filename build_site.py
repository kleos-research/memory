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
MANAGER_SOURCE_COMMIT = "05948a3acfbf0a325f06ecfe6057db484f02e5a1"
MANAGER_SHA256 = (
    "4fecd84584ed50dacde0677a9aba18c8a44ce6a58ea499e701e2c6dcd1c05b3e"
)
DISTRIBUTION_COMMIT = "42ffba4e3976810f91f2adcf53bd4393e5330d72"
DX06_VERIFICATION_SHA256 = (
    "98d36d4ce6a7b99c273f6c216a0b351fced7860c76edfc1429f499c0ba63bbed"
)
DX10A_EVIDENCE_SHA256 = (
    "cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e"
)
SDK_HOST_CONFORMANCE_COMMIT = "9cd4b5837e887a0bb3dcc13209134c002aad08f5"
DX10B_HOST_EVIDENCE_SHA256 = (
    "74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840"
)
BENCHMARK_COMMIT = "ef89d05f09435afc9790fcdf5df3e01d34c7115b"
DX09_FIXTURE_EVIDENCE_SHA256 = (
    "f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504"
)
LOCAL_ARCHIVE_SHA256 = (
    "48e34b1126d4b29b103cb913ddd71ffe2fd39ad141228346afccb8eaa504c658"
)
LOCAL_MANIFEST_SHA256 = (
    "e1f19abbfcf088e0121c135a623f2aa86fd68ba412b640084324bdf125a0eb6c"
)
LOCAL_SBOM_SHA256 = (
    "50444804bb2d29561b9b3f9f85afdb5133d06afb92886683ab9e4f7339ec2a15"
)
LOCAL_PROVENANCE_SHA256 = (
    "7b08171edaf1aac81f81c78d5bd704674db3f2a8c3e44f122cccf456ee3ff82e"
)
LOCAL_TEST_SIGNATURE_SHA256 = (
    "6dd03a82e4688413c438a8ca8682b20e3a8886895ba2059a22881458127f843e"
)

MANAGER_HELP = """Kaleidoscope public local manager

Usage:
  kaleidoscope [--engine PATH] init [--root PATH] [--profile NAME]
                                      [--durability process-local|durable-local]
  kaleidoscope [--engine PATH] profile list
  kaleidoscope [--engine PATH] profile show NAME
  kaleidoscope [--engine PATH] profile use NAME
  kaleidoscope [--engine PATH] profile remove NAME
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
  kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
  kaleidoscope account revoke
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
        "dx10b_host_evidence_sha256": DX10B_HOST_EVIDENCE_SHA256,
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
        "commit": DISTRIBUTION_COMMIT,
        "archive_sha256": LOCAL_ARCHIVE_SHA256,
        "manifest_sha256": LOCAL_MANIFEST_SHA256,
        "sbom_sha256": LOCAL_SBOM_SHA256,
        "provenance_sha256": LOCAL_PROVENANCE_SHA256,
        "signature_envelope_sha256": LOCAL_TEST_SIGNATURE_SHA256,
        "verification_summary_sha256": DX06_VERIFICATION_SHA256,
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
            "verification": "11 account commands passed the offline provider-not-configured and no-engine-resolution lane",
        },
        {
            "id": "DX-06A/B",
            "commit": DISTRIBUTION_COMMIT,
            "status": "verified_local_test_signature_only",
            "scope": "source-only distribution tooling, object-code bundle, npm and wheel shapes, lifecycle rehearsal",
            "verification": f"18 tests passed; verification summary SHA-256 {DX06_VERIFICATION_SHA256}",
        },
        {
            "id": "DX-07",
            "commit": "fd0b1877f70b1bb57e1b67c4c559e8b2e1d44290",
            "status": "verified_local",
            "scope": "Python and TypeScript clients plus agent and framework integrations",
            "verification": "Python dependency matrices, TypeScript 32-pass/1-skip and 33-of-33 real-profile lanes, and poison scan passed",
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
            "commit": SDK_HOST_CONFORMANCE_COMMIT,
            "status": "verified_local_codex_cli",
            "scope": "isolated real Codex CLI configuration plus generic persistent stdio MCP conformance",
            "verification": f"host evidence SHA-256 {DX10B_HOST_EVIDENCE_SHA256}",
        },
        {
            "id": "DX-10A",
            "commit": DISTRIBUTION_COMMIT,
            "status": "verified_local_macos_arm64",
            "scope": "clean install, package binding, friendly profile MCP, account refusal, update, rollback, uninstall and vault canary",
            "verification": f"DX-10A evidence SHA-256 {DX10A_EVIDENCE_SHA256}",
        },
    ],
    "release_holds": {
        "production_oidc_issuer": None,
        "production_signing_identity": None,
        "production_engine_eula_approved": False,
        "public_manager_license_approved": False,
        "original_documentation_license_approved": False,
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


DOC_NAV = (
    ("/docs/", "Overview"),
    ("/docs/getting-started/", "Getting started"),
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
<div class="callout"><strong>Interface preview, not an install command.</strong> No package is public. The final local DX-06 archive is bound to the auth-enabled manager but still uses a test-only signature; it is evidence, not a downloadable release.</div>
<h2>1. Install after protected promotion</h2>
<p>The intended package contains the public manager and proprietary engine object code without engine source. License grants, an engine EULA, production signing, registry credentials, supported-target evidence, and a separate publication approval are still required.</p>
<h2>2. Initialize a profile</h2>
<pre><code>kaleidoscope --engine /absolute/path/to/kscope init \
  --profile default \
  --root /absolute/path/to/user-owned/kaleidoscope-memory
kaleidoscope --engine /absolute/path/to/kscope config --json</code></pre>
<p>The no-argument friendly path is also implemented locally. A profile is selected through the manager and native profile registry; agent configuration receives <code>mcp --profile NAME</code>, not credentials or raw vault coordinates.</p>
<h2>3. Preview and connect a host</h2>
<pre><code>kaleidoscope connect codex --profile default --project "$PWD" --dry-run
kaleidoscope connect codex --profile default --project "$PWD"
kaleidoscope --engine /absolute/path/to/kscope doctor --project "$PWD"</code></pre>
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
        route="/docs/concepts/",
        title="Concepts and boundaries",
        description="How Kaleidoscope separates local memory, profiles, harness identity, account identity, and a future hosted service.",
        body="""
<p class="lede">The important boundary is local memory versus account metadata—not merely “logged in versus logged out.”</p>
<h2>Local engine</h2>
<p>The proprietary native engine owns the memory algorithm, canonical vault, graph, ranking, and stdio MCP behavior. Its source is not part of the public manager, client, integration, or skill surfaces.</p>
<h2>Manager and profile</h2>
<p>The consolidated manager initializes profiles, validates the engine launch descriptor, edits harness configuration safely, runs offline diagnostics, installs agent guidance, and exposes the account/device commands. The local distribution is bound to manager source commit <code>05948a3…</code> and binary SHA-256 <code>4fecd84584ed…</code>.</p>
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
<div class="callout"><strong>Candidate-generated reference.</strong> The exact help snapshot comes from consolidated manager source commit <code>05948a3…</code> and candidate SHA-256 <code>4fecd84584ed…</code>. It is not a public-installation claim.</div>
<p><a href="/reference/kaleidoscope-cli.candidate.txt">Download the exact candidate help text</a>.</p>
<h2>Local memory and host commands</h2>
<pre><code>kaleidoscope [--engine PATH] init [--root PATH] [--profile NAME] [--durability process-local|durable-local]
kaleidoscope [--engine PATH] profile list|show|use|remove
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
kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
kaleidoscope account revoke
kaleidoscope devices list
kaleidoscope devices revoke DEVICE_UUID</code></pre>
<p>These account commands are locally implemented and tested but intentionally fail with <code>provider not configured</code> without approved issuer, audience, client, and account-origin configuration. No production issuer is published.</p>
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
<tr><td>Codex</td><td>Real <code>codex-cli 0.149.0-alpha.4</code> add/list/get/remove passed in isolated config with byte-exact rollback; generic stdio MCP exposed exactly two tools.</td><td>Verified local CLI configuration; model/TUI acceptance held</td></tr>
<tr><td>Claude Code</td><td>Managed <code>.mcp.json</code> render, dry run, idempotence, and exact rollback passed.</td><td>Not live-host accepted</td></tr>
<tr><td>Cursor</td><td>Managed <code>mcp.json</code> plus owner-marked rule passed local configuration tests.</td><td>Not live-host accepted</td></tr>
<tr><td>OpenCode</td><td>Stable v1 direct entry is default; beta v2 is explicit and never silently selected.</td><td>Not live-host accepted</td></tr>
<tr><td>Python generic MCP</td><td><code>mcp==1.29.0</code> and <code>mcp==2.0.0</code>; persistent and real-profile lanes passed.</td><td>Verified local, unpublished</td></tr>
<tr><td>TypeScript generic MCP</td><td><code>@modelcontextprotocol/client==2.0.0</code>; explicit revision negotiation and real-profile lane passed.</td><td>Verified local, unpublished</td></tr>
<tr><td>LangChain / LangGraph</td><td><code>langchain==1.3.16</code>, <code>langgraph==1.2.11</code>; one persistent session and no shadow store.</td><td>Verified with fake provider</td></tr>
<tr><td>Claude Agent SDK</td><td><code>claude-agent-sdk==0.2.143</code>; strict MCP names and lifecycle passed.</td><td>Verified without live provider</td></tr>
<tr><td>OpenAI Agents SDK</td><td>Python <code>0.22.0</code> and TypeScript <code>0.17.0</code>; scripted-model routing passed.</td><td>Verified with adapter caveat</td></tr>
<tr><td>CrewAI</td><td><code>crewai==1.15.17</code>; long-lived MCP adapter passed.</td><td>Verified with fake server</td></tr>
</tbody></table>
<div class="callout"><strong>What DX-07 and DX-10B prove.</strong> The Python/TypeScript matrices and real-profile lanes passed, and host conformance commit <code>9cd4b58…</code> bound the final manager and engine to isolated real Codex CLI configuration plus dependency-free generic MCP. Claude Code, Cursor, and OpenCode CLIs were absent; no live provider, model/TUI/IDE, publication, or support claim follows.</div>
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
<h2>Package shapes</h2><p>Local macOS arm64 staging produced an object-code archive, npm meta/platform tarballs, and Python facade/native wheels, plus aggregate SBOM and provenance. Nothing was published; other platform entries are refusal-only scaffolds.</p>
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
<h2>Package integrity</h2><p>DX-06 binds object-code digests, source commits, bundled model, CycloneDX SBOM, provenance, candidate public contract, target, and prior-manifest rollback identity. Its signature is from a checked-in test fixture and the native code is only ad hoc/linker signed. Production trust roots, role keys, Apple signing/notarization, EULA, notices, and approved licenses are absent.</p>
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
<h2>Locally verified manager flows</h2><p>Consolidated manager commit <code>05948a3…</code> implements authorization code with PKCE and a loopback callback plus device authorization for headless environments. It validates OIDC discovery, JWKS and RSA ID tokens; rotates refresh-token families; and fails closed on reuse. The final packaged candidate exposes all 11 closed account/device commands, but only the offline provider-not-configured lane has run against that package.</p>
<h2>Commands</h2><pre><code>kaleidoscope login
kaleidoscope login --device
kaleidoscope status --json
kaleidoscope logout
kaleidoscope logout --all-devices
kaleidoscope logout --local-only
kaleidoscope account link PROVIDER
kaleidoscope account unlink EXTERNAL_IDENTITY_UUID
kaleidoscope account revoke
kaleidoscope devices list
kaleidoscope devices revoke DEVICE_UUID</code></pre>
<p><code>--local-only</code> deliberately warns that it does not revoke the remote session. Without approved provider configuration, account commands return <code>provider not configured</code>; the docs do not provide substitute endpoints.</p>
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
<tr><td>macOS arm64</td><td>Final auth-enabled manager and engine candidate, object-code packaging, real stdio MCP, account refusal, clean install/update/rollback/uninstall, vault canary, and real Codex CLI configuration.</td><td>Production signature/notarization, approved terms, live OIDC/keychain, model/TUI/IDE acceptance, and protected publication.</td></tr>
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
<table><tbody><tr><th>Manager source commit</th><td><code>{MANAGER_SOURCE_COMMIT}</code></td></tr><tr><th>Manager candidate SHA-256</th><td><code>{MANAGER_SHA256}</code></td></tr><tr><th>Engine source commit</th><td><code>{ENGINE_SOURCE_COMMIT}</code></td></tr><tr><th>Engine candidate SHA-256</th><td><code>{ENGINE_CANDIDATE_SHA256}</code></td></tr><tr><th>Public contract SHA-256</th><td><code>{PUBLIC_CONTRACT_SHA256}</code></td></tr><tr><th>Native target tested</th><td>macOS arm64</td></tr><tr><th>Production signature</th><td>Not verified</td></tr></tbody></table>
<h2>Milestones</h2>
<table><thead><tr><th>Slice</th><th>Exact evidence</th><th>What is true now</th></tr></thead><tbody>
<tr><td>DX-04 / DX-05B</td><td><code>{MANAGER_SOURCE_COMMIT}</code>, manager <code>{MANAGER_SHA256}</code></td><td>Consolidated friendly and auth/device manager surfaces passed locally; production provider is unconfigured.</td></tr>
<tr><td>DX-06A/B</td><td><code>{DISTRIBUTION_COMMIT}</code>, summary <code>{DX06_VERIFICATION_SHA256}</code></td><td>18 tests passed over source-only tooling and final object-code package shapes with a test-only signature; no publication.</td></tr>
<tr><td>DX-07</td><td><code>fd0b187…</code></td><td>Pinned Python/TypeScript client and integration matrices passed locally; no license or remote.</td></tr>
<tr><td>DX-09</td><td><code>{BENCHMARK_COMMIT}</code>, merged PRs 5/6; evidence <code>{DX09_FIXTURE_EVIDENCE_SHA256}</code></td><td>Two clean exact-candidate fixture runs produced byte-identical artifacts; no score, signature, performance, or production-comparability claim.</td></tr>
<tr><td>DX-10A</td><td><code>{DX10A_EVIDENCE_SHA256}</code></td><td>Final local package install, real MCP, account refusal, update, rollback, uninstall, and vault canary passed on macOS arm64; five non-native cells held.</td></tr>
<tr><td>DX-10B</td><td><code>{SDK_HOST_CONFORMANCE_COMMIT}</code>, evidence <code>{DX10B_HOST_EVIDENCE_SHA256}</code></td><td>Real isolated Codex CLI configuration and generic MCP passed; model/TUI/IDE and absent-host cells held.</td></tr>
</tbody></table>
<h2>Local rebind complete, production promotion held</h2><p>The local DX-06 archive, manifest, SBOM, provenance, package shapes, and DX-10A lane are now bound to manager <code>{MANAGER_SHA256}</code>, engine <code>{ENGINE_CANDIDATE_SHA256}</code>, and contract <code>{PUBLIC_CONTRACT_SHA256}</code>. The archive digest is <code>{LOCAL_ARCHIVE_SHA256}</code>. Its signature envelope <code>{LOCAL_TEST_SIGNATURE_SHA256}</code> uses only a checked-in TEST-ONLY trust root. These bindings close the local rebind; they do not satisfy licenses, EULA, production OIDC, production signing/notarization, other native platforms, live model/IDE acceptance, registry publication, or Pages promotion.</p>
<h2>Approval and credential gates</h2><ul><li>Approval of a license for the public manager, wrappers, integrations, and skill.</li><li>Approval of terms for original documentation and an engine object-code EULA.</li><li>Staging/production OIDC configuration and private control-plane deployment evidence.</li><li>Production signing/notarization identities, registry/CDN credentials, and native platform runners.</li><li>A separate final approval for package publication, production login, and Pages promotion.</li></ul>
""",
    ),
    Page(
        route="/docs/release-notes/",
        title="Release notes",
        description="Versioned Kaleidoscope release notes bound to immutable package and public-contract digests.",
        body="""
<p class="lede">Release notes become authoritative only when they name the exact signed package, final manager, engine, and public-contract digests.</p>
<h2>Unreleased local staging — 2026-08-22</h2><ul><li>The consolidated auth-enabled manager is deterministically bound at <code>4fecd84584ed…</code>.</li><li>DX-06 object-code archive, npm/wheel shapes, SBOM/provenance, and lifecycle rehearsal passed with a test-only signature and final local manager.</li><li>DX-07 Python/TypeScript and harness integration matrices passed locally.</li><li>DX-09 native smoke plus the credential-free deterministic fixture pipeline merged in PRs 5/6; no benchmark score was produced.</li><li>DX-10A final local macOS arm64 clean install, MCP, offline account refusal, update/rollback/uninstall, and vault-canary lane passed.</li><li>DX-10B isolated real Codex CLI configuration and generic stdio MCP passed; other hosts and model/IDE acceptance remain held.</li></ul>
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
    active = ' aria-current="page"' if route == current else ""
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
        data = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": page.title,
            "description": page.description,
            "dateModified": TODAY.isoformat(),
            "mainEntityOfPage": canonical,
            "publisher": {"@id": f"{DOMAIN}/#organization"},
        }
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace(
        "</", "<\\/"
    )


def head(
    title: str, description: str, canonical: str, production: bool, page: Page | None
) -> str:
    robots = "index,follow" if production else "noindex,nofollow"
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
  <meta name="twitter:card" content="summary">
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
  <nav aria-label="Footer"><a href="/llms.txt">llms.txt</a><a href="/.well-known/security.txt">security.txt</a><a href="/docs/account/">Account boundary</a></nav>
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
    <article class="card"><h2>Inspectable boundary</h2><p>The staged bundle binds object code, manager, model, contract, SBOM, and provenance; production signing and licenses are still gated.</p></article>
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
        head(page.title, page.description, canonical, production, page)
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
    for asset in (
        "favicon.svg",
        "favicon-32.png",
        "favicon.ico",
        "apple-touch-icon.png",
    ):
        shutil.copyfile(ROOT / asset, output / asset)
    (output / "assets").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "assets/site.css", output / "assets/site.css")
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

    urls = [f"{DOMAIN}/", *(f"{DOMAIN}{page.route}" for page in PAGES)]
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
- [Getting started]({DOMAIN}/docs/getting-started/): release-gated profile and reversible host workflow
- [CLI reference]({DOMAIN}/docs/cli/): exact local manager-candidate commands
- [MCP reference]({DOMAIN}/docs/mcp/): candidate-bound `search` and `remember` contract
- [Integrations]({DOMAIN}/docs/integrations/): Codex, Claude, Cursor, OpenCode, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, and generic MCP
- [Security]({DOMAIN}/docs/security/): package, process, and account isolation evidence
- [Privacy]({DOMAIN}/docs/privacy/): local/account data boundary, credential storage, and telemetry status
- [Account]({DOMAIN}/docs/account/): login manages account/device state and does not upload local memory
- [Operations]({DOMAIN}/docs/operations/): backup, restore, uninstall, update, and exact vault deletion
- [Compatibility]({DOMAIN}/docs/compatibility/): verified local cells versus native/support holds
- [Benchmarks]({DOMAIN}/docs/benchmarks/): merged candidate-bound smoke, with no score or release claim
- [Release evidence]({DOMAIN}/docs/evidence/): exact digests, milestone commits, rebind requirement, and protected gates
- [Public agent skill]({DOMAIN}/SKILL.md): bounded retrieval and verified durable writes
- [Agent instructions]({DOMAIN}/agent-instructions.md): safe manager-installed AGENTS, CLAUDE, and Cursor pointers
- [Machine-readable staging evidence]({DOMAIN}/staging-evidence.json): source-free milestone and gate record
- [Candidate CLI help]({DOMAIN}/reference/kaleidoscope-cli.candidate.txt): exact consolidated manager help snapshot
- [Candidate MCP reference]({DOMAIN}/reference/kaleidoscope-mcp.candidate.json): exact engine and public-contract binding plus tool fields

The engine remains proprietary object code and its source is not in the public surfaces. The manager, wrappers, integrations, skill, and original documentation have no approved public license grant yet. Exact locally verified bindings: manager SHA-256 {MANAGER_SHA256}; engine SHA-256 {ENGINE_CANDIDATE_SHA256}; public contract SHA-256 {PUBLIC_CONTRACT_SHA256}; DX-06 summary SHA-256 {DX06_VERIFICATION_SHA256}; DX-09 deterministic fixture evidence SHA-256 {DX09_FIXTURE_EVIDENCE_SHA256}; DX-10A evidence SHA-256 {DX10A_EVIDENCE_SHA256}; DX-10B Codex-host evidence SHA-256 {DX10B_HOST_EVIDENCE_SHA256}. The local distribution is test-signed only and supports no production-release claim. Hosted memory is planned, not available. Production publication, login, and Pages promotion require separate approval.
"""
    write_text(output / "llms.txt", llms)

    chunks = [llms.strip()]
    for page in PAGES:
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
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--release-metadata", type=Path)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    metadata = load_metadata(args.release_metadata, args.production)
    build(args.output.expanduser().absolute(), metadata, args.production)


if __name__ == "__main__":
    main()

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
    ("/docs/security/", "Security & privacy"),
    ("/docs/account/", "Account"),
    ("/docs/compatibility/", "Compatibility"),
    ("/docs/benchmarks/", "Benchmarks"),
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
<p class="lede">Kaleidoscope is local memory for agents: a native CLI and persistent stdio MCP server with one profile shared across supported harnesses.</p>
<div class="callout"><strong>Release status.</strong> This documentation is a staging candidate. Installation artifacts and production login are not public until the signed release and protected promotion gates pass.</div>
<div class="grid">
  <article class="card"><h2><a href="/docs/getting-started/">Start locally</a></h2><p>Install, initialize one profile, connect a harness, and verify the two agent tools.</p></article>
  <article class="card"><h2><a href="/docs/mcp/">Use MCP</a></h2><p>Discover exactly <code>search</code> and <code>remember</code> over one long-lived stdio process.</p></article>
  <article class="card"><h2><a href="/docs/security/">Understand the boundary</a></h2><p>Memory and vault coordinates stay on the device; account login is a separate control-plane concern.</p></article>
</div>
<h2>Choose a path</h2>
<ul>
  <li>Agent user: follow <a href="/docs/getting-started/">Getting started</a> and let the manager make a reversible host configuration.</li>
  <li>Application developer: begin with <a href="/docs/integrations/">Integrations</a> and the persistent MCP client contract.</li>
  <li>Operator: use <a href="/docs/operations/">Operations</a> for backup, restore, uninstall, and exact vault deletion.</li>
  <li>Security reviewer: read <a href="/docs/security/">Security &amp; privacy</a> and verify the signed public contract, SBOM, and package provenance.</li>
</ul>
""",
    ),
    Page(
        route="/docs/getting-started/",
        title="Getting started",
        description="The release-gated Kaleidoscope quickstart: initialize a local profile, safely connect an agent harness, and verify search and remember.",
        body="""
<p class="lede">One manager command creates or imports a local profile. A second command previews and applies an owner-marked, reversible host configuration.</p>
<div class="callout"><strong>Not installable yet.</strong> The commands below describe the SDK-BOOT release-candidate interface. This page becomes a public copy/paste quickstart only after it passes against the exact signed package.</div>
<h2>1. Install the signed package</h2>
<p>Use one supported package channel. The final installer contains the public manager and proprietary engine object code, plus the composite license, notices, aggregate SBOM, and signed public contract. It does not contain the private engine source.</p>
<h2>2. Initialize a profile</h2>
<pre><code>kaleidoscope init</code></pre>
<p>The interactive path chooses an existing vault or creates one explicitly. A profile is a non-secret local pointer; it never embeds account credentials in agent configuration.</p>
<h2>3. Preview and connect a host</h2>
<pre><code>kaleidoscope connect codex --dry-run
kaleidoscope connect codex
kaleidoscope doctor</code></pre>
<p>Use <code>claude</code>, <code>cursor</code>, or <code>opencode</code> only when the <a href="/docs/compatibility/">compatibility page</a> marks that exact version supported. Existing unrelated configuration is preserved. Ambiguous or concurrently edited files are refused.</p>
<h2>4. Verify the contract</h2>
<p>Restart the host and confirm it discovers exactly two agent tools: <code>search</code> and <code>remember</code>. A ranked search returns hits under <code>selected_hits</code>; an addressed search with <code>memory_id</code> returns the selected memory at top level.</p>
<h2>5. Disconnect safely</h2>
<pre><code>kaleidoscope disconnect codex --dry-run
kaleidoscope disconnect codex</code></pre>
<p>Disconnect removes only Kaleidoscope-owned material and leaves other host settings and vault bytes unchanged.</p>
""",
    ),
    Page(
        route="/docs/concepts/",
        title="Concepts and boundaries",
        description="How Kaleidoscope separates local memory, profiles, harness identity, account identity, and a future hosted service.",
        body="""
<p class="lede">The important boundary is not “logged in versus logged out.” It is local memory versus account metadata.</p>
<h2>Local engine</h2>
<p>The proprietary native engine owns the memory algorithm, canonical vault, graph, ranking, and stdio MCP behavior. Local memory content, queries, results, memory IDs, vault coordinates, and local paths are not account-service fields.</p>
<h2>Manager and profile</h2>
<p>The public manager initializes profiles, validates the engine launch descriptor, edits harness configuration safely, runs offline diagnostics, and manages account credentials through the operating-system credential store. A profile names one local vault identity without revealing those coordinates to agent configuration.</p>
<h2>Harness identity</h2>
<p>Codex, Claude, Cursor, OpenCode, framework clients, and generic MCP clients are consumers of the same profile. They do not become separate memory stores merely because their configuration formats differ.</p>
<h2>Account identity</h2>
<p>Login links a product account and device. Logout or account unlinking does not delete, relocate, or rewrite the local vault. Account state must not be interpreted as consent to upload memory.</p>
<h2>Hosted memory</h2>
<p>A hosted service is a future product requiring its own authorization, tenant-isolation, retention, residency, deletion, sync, billing, and incident-response contract. It is not available and login does not opt a user into it.</p>
""",
    ),
    Page(
        route="/docs/cli/",
        title="CLI reference",
        description="Generated-reference boundary for the public Kaleidoscope manager CLI, profiles, host connection, diagnostics, and account commands.",
        body="""
<p class="lede">The supported public CLI is <code>kaleidoscope</code>. Direct <code>kscope</code> operator commands are an engine/operator surface and are not a replacement for the manager quickstart.</p>
<div class="callout"><strong>Generation pending release binding.</strong> The final command table is generated from the immutable manager artifact and signed public contract. This staging page intentionally does not invent flags that the candidate has not exposed.</div>
<h2>Public command groups</h2>
<table><thead><tr><th>Group</th><th>Purpose</th><th>Network</th></tr></thead><tbody>
<tr><td><code>init</code> / profile</td><td>Create or import one validated local profile.</td><td>None</td></tr>
<tr><td><code>connect</code> / <code>disconnect</code></td><td>Preview and apply reversible owner-marked host configuration.</td><td>None</td></tr>
<tr><td><code>doctor</code></td><td>Validate package, descriptor, profile, host configuration, and local MCP startup without printing secrets.</td><td>None</td></tr>
<tr><td>instructions</td><td>Install or remove the public skill and compact AGENTS/CLAUDE/Cursor guidance.</td><td>None</td></tr>
<tr><td>account</td><td>Login, status, logout, link, revoke, and device management.</td><td>Account endpoints only</td></tr>
</tbody></table>
<h2>Safety invariants</h2>
<ul><li>Mutating host commands support a dry run and explicit confirmation.</li><li>Unknown, conflicting, symlinked, or concurrently changed targets fail closed.</li><li>Backups are bounded and owner receipts make removal idempotent.</li><li>Agent launch configuration contains no tokens, provider keys, or raw vault coordinates.</li></ul>
""",
    ),
    Page(
        route="/docs/mcp/",
        title="MCP reference",
        description="The Kaleidoscope stdio MCP contract: exactly search and remember for agents, with persistent sessions and operator-tool exclusion.",
        body="""
<p class="lede">Kaleidoscope publishes exactly two model-callable MCP tools. Everything else is an operator command outside the agent tool list.</p>
<h2><code>search</code></h2>
<p>Use a query for ranked retrieval or <code>memory_id</code> for an addressed read. Ranked results appear under <code>selected_hits</code>. The ranking knobs are <code>top_k</code>, <code>candidate_pool</code>, <code>bfs_depth</code>, and <code>max_facts</code>; clients should omit defaults rather than hand-copy them.</p>
<pre><code>{"query":"What constraints govern the release?","top_k":5,"ledger":true}</code></pre>
<h2><code>remember</code></h2>
<p>Create, update, or logically delete a durable semantic delta. A create or update includes Markdown beginning with an H1 plus declared entities and subject–predicate–object facts. Every fact endpoint must be declared with <code>n</code>, <code>kind</code>, and a required <code>is</code> gloss. Predicates are snake_case.</p>
<h2>Lifecycle</h2>
<p>Clients should keep one stdio process alive across calls, negotiate MCP once, enforce a startup deadline, cancel cleanly, bound stderr, and tear down without leaving an orphan or locked update target. Model-facing integrations do not run a second hidden retrieval.</p>
<h2>Not agent tools</h2>
<p>Feedback, lifecycle/import, maintenance, ontology, and doctor operations are controller/operator commands. Historical tool names and shapes are documented only on the <a href="/docs/migration/">migration page</a>; they must not appear in a model tool list.</p>
""",
    ),
    Page(
        route="/docs/integrations/",
        title="Agent and framework integrations",
        description="How Kaleidoscope integrates with Codex, Claude, Cursor, OpenCode, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, and generic MCP.",
        body="""
<p class="lede">Every integration consumes the same validated launch descriptor and persistent stdio MCP contract; none reimplements the memory algorithm.</p>
<table><thead><tr><th>Integration</th><th>Candidate path</th><th>Release status</th></tr></thead><tbody>
<tr><td>Codex</td><td>User or trusted-project MCP configuration with an exact <code>search</code>/<code>remember</code> allowlist.</td><td>Under conformance</td></tr>
<tr><td>Claude Code / Agent SDK</td><td>Managed <code>.mcp.json</code> or SDK MCP server configuration.</td><td>Under conformance</td></tr>
<tr><td>Cursor</td><td>User or project <code>mcp.json</code> plus an owner-marked rule.</td><td>Under conformance</td></tr>
<tr><td>OpenCode</td><td>Stable direct <code>mcp.&lt;name&gt;</code> by default; explicit beta-v2 support without silent migration.</td><td>Under conformance</td></tr>
<tr><td>LangChain / LangGraph</td><td>Python persistent MCP client and framework-native tool binding.</td><td>Under conformance</td></tr>
<tr><td>OpenAI Agents SDK</td><td>TypeScript or Python MCP stdio server integration.</td><td>Under conformance</td></tr>
<tr><td>CrewAI</td><td>Python MCP adapter using the same long-lived session.</td><td>Under conformance</td></tr>
<tr><td>Generic MCP</td><td>Standards-conforming stdio initialization and tool calls.</td><td>Under conformance</td></tr>
</tbody></table>
<div class="callout"><strong>No support claim yet.</strong> A row changes from “under conformance” only when its pinned version passes the packaged release matrix. Cross-compilation or a configuration snapshot is not sufficient.</div>
""",
    ),
    Page(
        route="/docs/operations/",
        title="Local operations",
        description="Operate Kaleidoscope safely: locations, backup and restore, migration, disconnect, uninstall, and exact vault deletion.",
        body="""
<p class="lede">Configuration, account credentials, installed executables, and canonical vault data have separate lifecycles.</p>
<h2>Locate before changing</h2><p>Use the manager profile and doctor views to identify the active package and profile without printing tokens or raw memory content. Never assume a worktree carries gitignored vault data.</p>
<h2>Back up and restore</h2><p>Back up the canonical vault from the main checkout or another explicit data location, not a disposable worktree. Restore only through the verified export/import path for the same supported vault format.</p>
<h2>Disconnect and uninstall</h2><p>Disconnect removes only manager-owned host configuration. Uninstall removes package artifacts and account credentials according to the selected scope. Neither operation implicitly deletes a vault.</p>
<h2>Delete a vault</h2><p>Vault deletion is a separate preview-and-confirm operation tied to one exact resolved root. Logical memory deletion and physical vault deletion are different operations. A broad path, unresolved variable, or ambiguous target must be refused.</p>
<h2>Update and rollback</h2><p>The installer stages, verifies, atomically activates, health-checks, and finalizes a signed package. A failed update returns to the exact prior manifest. Update and rollback do not migrate or alter canonical memory implicitly.</p>
""",
    ),
    Page(
        route="/docs/security/",
        title="Security and privacy",
        description="Kaleidoscope security model, local data boundary, package integrity, telemetry status, vulnerability reporting, and native-binary limits.",
        body="""
<p class="lede">Kaleidoscope protects source distribution and establishes verifiable package boundaries. It does not claim that a native executable is impossible to inspect or reverse engineer.</p>
<h2>Local data boundary</h2><p>The engine is local and makes no account-service request. Login traffic is limited to allowlisted account and device fields. Memory content, queries, results, memory IDs, vault coordinates, local paths, workspace/principal/journal identity, and provider credentials are excluded.</p>
<h2>Package integrity</h2><p>A release binds the manager and engine digests, source commits, bundled model, aggregate CycloneDX SBOM, public contract, licenses, target, channel, compatibility, and rollback identity. Installers start from an embedded rotating trust root and refuse altered, expired, replayed, downgraded, wrong-target, or cross-channel metadata.</p>
<h2>Environment and logs</h2><p>The engine receives a closed non-secret bootstrap environment rather than the full ambient process environment. Diagnostics and receipts are bounded and redacted. Release conformance scans argv, environment, profiles, logs, crash data, MCP traffic, and public artifacts with canary values.</p>
<h2>Telemetry</h2><p>The staging candidate makes no telemetry claim beyond the tested release evidence. The production page must enumerate every network destination and field before login is enabled.</p>
<h2>Report a vulnerability</h2><p>Do not publish an exploit or sensitive report in a public issue. The production security contact and supported-version policy are release blockers and will be published here and in <code>/.well-known/security.txt</code> before promotion.</p>
""",
    ),
    Page(
        route="/docs/account/",
        title="Account and devices",
        description="What Kaleidoscope login does, how credentials are stored, and why account operations never upload or delete local memory.",
        body="""
<p class="lede">Login is for product account and device workflows. It is not a hosted-memory connection.</p>
<h2>Authentication flows</h2><p>The native manager uses authorization code with PKCE and a loopback callback where available, with a device authorization flow for headless environments. Tokens are stored in the operating-system credential store, never in agent configuration or a profile.</p>
<h2>Account commands</h2><p>The release-candidate surface covers login, status, logout, link, revoke, and device listing/revocation. Refresh tokens rotate by family; reuse revokes the family. Denied, expired, cancelled, offline, and credential-store-failure states are explicit.</p>
<h2>What logout changes</h2><p>Logout removes or revokes account credentials according to the requested scope. It does not change the local principal, workspace, journal, or vault bytes. Vault deletion remains a separate local operation.</p>
<h2>Control plane boundary</h2><p>The private control plane is account-only. It has no memory/profile routes and stores no memory content or local vault identity. Production identity-provider metadata, keys, domains, privacy terms, and recovery procedures remain gated until launch.</p>
""",
    ),
    Page(
        route="/docs/compatibility/",
        title="Compatibility",
        description="Kaleidoscope platform and harness compatibility policy, including the difference between build evidence and native release support.",
        body="""
<p class="lede">A platform or harness is supported only after the packaged artifact passes the canonical end-to-end proof on the named native runner and pinned host version.</p>
<table><thead><tr><th>Surface</th><th>Candidate target</th><th>Current public claim</th></tr></thead><tbody>
<tr><td>macOS</td><td>arm64, x64</td><td>Not released</td></tr><tr><td>Linux</td><td>x86_64, arm64; libc policy must be explicit</td><td>Not released</td></tr><tr><td>Windows</td><td>x86_64, arm64</td><td>Not released</td></tr>
<tr><td>Agent hosts</td><td>Codex, Claude Code, Cursor, OpenCode</td><td>Under conformance</td></tr><tr><td>Frameworks</td><td>Claude Agent SDK, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, generic MCP</td><td>Under conformance</td></tr>
</tbody></table>
<p>Cross-compiling, extracting a foreign package, or parsing a configuration file is useful evidence but never a native support claim. Any matrix cell that does not pass is removed from the release before promotion.</p>
""",
    ),
    Page(
        route="/docs/benchmarks/",
        title="Benchmarks and evidence",
        description="How Kaleidoscope publishes clean, reproducible memory benchmarks without private-source dependencies or stale tool contracts.",
        body="""
<p class="lede">Benchmark results are useful only when the evaluated candidate, public contract, dataset, evaluator, and retrieval path are immutable and auditable.</p>
<h2>Candidate binding</h2><p>A public run names the signed engine candidate, package digest, public-contract digest, dataset and evaluator versions. Missing or mismatched inputs fail before acquisition. A local unsigned binary cannot be relabelled as release evidence.</p>
<h2>One retrieval path</h2><p>The harness performs one model-facing <code>search</code>. It does not hide a second acquisition search or depend on a legacy acquisition command.</p>
<h2>Runtime vocabulary</h2><p>Accepted memory types and relationship vocabulary come from the runtime contract, not a hand-copied list in benchmark code or prompts.</p>
<h2>Published evidence</h2><p>Reports include protocol persistence, restart behavior, exact candidate and contract digests, raw aggregate metrics, limitations, evaluator procedure, and proof that public configuration contains no private repository or vault coordinates.</p>
""",
    ),
    Page(
        route="/docs/release-notes/",
        title="Release notes",
        description="Versioned Kaleidoscope release notes bound to immutable package and public-contract digests.",
        body="""
<p class="lede">Release notes become authoritative only when they name the exact signed package and public-contract digest.</p>
<h2>Unreleased</h2><p>The local manager, account boundary, confidential bundle, integrations, documentation, benchmark cleanup, and cross-platform conformance are being staged as separately reviewable changes. No production package or login endpoint is public.</p>
<h2>Promotion rule</h2><p>A release entry records availability, supported targets and pinned host versions, known limitations, migration requirements, security fixes, checksums, SBOM and provenance links, and exact rollback identity. Publication and documentation promotion remain a separate protected action.</p>
""",
    ),
    Page(
        route="/docs/troubleshooting/",
        title="Troubleshooting",
        description="Diagnose Kaleidoscope profile, descriptor, host-configuration, MCP startup, and account problems without leaking local memory or credentials.",
        body="""
<p class="lede">Start with <code>kaleidoscope doctor</code>. Its output is designed to identify the failing boundary without printing secrets or memory content.</p>
<h2>The host cannot find the tools</h2><ol><li>Confirm the active profile and signed package are valid.</li><li>Preview the host connection and inspect only the manager-owned block.</li><li>Restart the host after a successful connect.</li><li>Confirm the discovered tools are exactly <code>search</code> and <code>remember</code>.</li></ol>
<h2>OpenCode configuration is refused</h2><p>Stable and beta-v2 shapes differ. The manager adopts an unambiguous existing shape or an explicit version selection; it never silently migrates stable configuration to beta. Remove conflicting duplicate Kaleidoscope entries and retry the dry run.</p>
<h2>A profile points to the wrong place</h2><p>Do not edit the profile by hand. Import the intended existing vault or initialize an explicit new root. A missing or invalid root is refused rather than created implicitly.</p>
<h2>Login fails but memory still works</h2><p>That separation is intentional for documented offline-existing-user paths. Account status and the local vault are separate. Do not delete or recreate the vault to repair an account problem.</p>
<h2>Before sharing diagnostics</h2><p>Remove local paths, account identifiers, provider keys, tokens, memory content, queries, results, and vault coordinates. Use the redacted doctor artifact intended for support.</p>
""",
    ),
    Page(
        route="/docs/migration/",
        title="Migration from historical tool contracts",
        description="How to migrate historical Kaleidoscope agent integrations to the public search and remember MCP contract.",
        body="""
<p class="lede">Current agents discover exactly <code>search</code> and <code>remember</code>. Historical tool names are not aliases and must be removed from host allowlists and prompts.</p>
<h2>Retrieval</h2><p>Replace <code>recall</code>, <code>compile</code>, and <code>read_memory</code> with <code>search</code>. Send <code>query</code> for ranked retrieval and <code>memory_id</code> for an addressed read. Ranked results are under <code>selected_hits</code>. Use <code>top_k</code>, not <code>limit</code>.</p>
<h2>Writing</h2><p>Replace prose-inference or <code>ingest_memory</code> paths with explicit <code>remember</code> semantic deltas. The runtime does not infer entities, facts, relationships, or dates from prose.</p>
<h2>Operator feedback</h2><p><code>feedback</code> remains an authenticated controller/operator command because its decision token does not reach a model. Do not advertise it as an MCP tool.</p>
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
                    "operatingSystem": "macOS, Linux, Windows",
                    "description": "Local native memory for AI agents, exposed through a CLI and stdio MCP.",
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
    <p class="lede">Kaleidoscope gives agents one local memory across harnesses. The native engine stays on your machine; the public manager connects it safely through a CLI and exactly two MCP tools.</p>
    <div class="actions"><a class="button" href="/docs/getting-started/">Read the quickstart</a><a class="button secondary" href="/docs/security/">Inspect the boundary</a></div>
  </section>
  <section class="shell grid" aria-label="Product principles">
    <article class="card"><h2>Local by construction</h2><p>Memory content, queries, results, identities, and vault paths are not account-service data.</p></article>
    <article class="card"><h2>Harness neutral</h2><p>Codex, Claude, Cursor, OpenCode, and framework clients consume the same profile and MCP contract.</p></article>
    <article class="card"><h2>Inspectable boundary</h2><p>Signed packages bind the proprietary object code, public manager, model, contract, licenses, SBOM, and provenance.</p></article>
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

    security = f"""Contact: {DOMAIN}/docs/security/
Canonical: {DOMAIN}/.well-known/security.txt
Expires: 2026-09-30T23:59:59Z
Preferred-Languages: en
Policy: {DOMAIN}/docs/security/
"""
    write_text(output / ".well-known" / "security.txt", security)

    llms = f"""# Kaleidoscope

> Local native memory for agents, exposed through a public manager CLI and persistent stdio MCP. Release status: {metadata["availability"]} ({metadata["release_version"]}).

- [Documentation]({DOMAIN}/docs/): product and developer overview
- [Getting started]({DOMAIN}/docs/getting-started/): profile and reversible host setup
- [MCP reference]({DOMAIN}/docs/mcp/): exactly `search` and `remember`
- [Integrations]({DOMAIN}/docs/integrations/): Codex, Claude, Cursor, OpenCode, LangChain, LangGraph, OpenAI Agents SDK, CrewAI, and generic MCP
- [Security and privacy]({DOMAIN}/docs/security/): local/account/data boundary and release integrity
- [Account]({DOMAIN}/docs/account/): login manages account/device state and does not upload local memory
- [Operations]({DOMAIN}/docs/operations/): backup, restore, uninstall, update, and exact vault deletion

The engine is proprietary object code. The manager, wrappers, integrations, and public skill are intended to be public after licensing approval. Hosted memory is planned, not available. Public contract SHA-256: {metadata["public_contract_sha256"]}.
"""
    write_text(output / "llms.txt", llms)

    chunks = [llms.strip()]
    for page in PAGES:
        chunks.append(
            f"# {page.title}\n\nURL: {DOMAIN}{page.route}\nRelease: {metadata['release_version']}\nUpdated: {metadata['updated_at']}\n\n{plain_text(page.body)}"
        )
    write_text(output / "llms-full.txt", "\n\n---\n\n".join(chunks))

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

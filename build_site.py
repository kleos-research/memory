#!/usr/bin/env python3
"""Build the source-free Kaleidoscope public documentation surface.

The default build is an explicitly non-indexable staging artifact. A public
documentation preview is indexable but does not claim package availability or
production login. A production artifact requires immutable release metadata and
refuses placeholder values. This script performs no network, authentication,
publication, or deployment.
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

PUBLIC_SKILL_SHA256 = (
    "c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad"
)

# The records below are published so an agent or a crawler can read the same
# status the pages state in prose. They describe what a reader can and cannot
# do. They deliberately carry no commit, no build digest and no internal
# work-item identifier: those describe how we got here, which is not something
# a reader of this site has any way to use, and publishing them once put the
# internal release process on the public site.

TESTED_PLATFORM = "macOS, Apple Silicon"
PACKAGE_VERSION = "0.1.0-rc.1"

HOST_SUPPORT = {
    "schema_version": "kaleidoscope.docs-host-support.v1",
    "run_on": TESTED_PLATFORM,
    "tools_a_model_sees": ["remember", "search"],
    "hosts": [
        {
            "name": "Codex",
            "version": "0.149.0",
            "status": "partly tested",
            "confirmed": "Kaleidoscope's entry is added to Codex's configuration, listed, read back and removed exactly, leaving the file byte for byte as it was",
            "not confirmed": "that Codex then starts the server and sees the two tools; Codex's command line offers no way to check",
        },
        {
            "name": "Claude Code",
            "version": "2.1.239",
            "status": "tested",
            "confirmed": "connected from the command line, not duplicated on a second run, removed cleanly, and both tools discovered",
            "not confirmed": "any run through a model turn, and anything done through the graphical interface",
        },
        {
            "name": "OpenCode",
            "version": "1.18.21",
            "status": "tested",
            "confirmed": "both configuration shapes written, applied twice without duplicating, removed cleanly, and both tools discovered",
            "not confirmed": "any run through a model turn, and anything done through the graphical interface",
        },
        {
            "name": "Cursor",
            "status": "partly tested",
            "confirmed": "its configuration and its project rule are written and removed exactly",
            "not confirmed": "everything after that; Cursor has never been launched against them",
        },
    ],
    "not tested at all": [
        "any run against a live model provider",
        "any editor's graphical interface",
        "any platform other than macOS on Apple Silicon",
        "any package installed from a registry",
    ],
}

PLATFORM_SUPPORT = {
    "schema_version": "kaleidoscope.docs-platform-support.v1",
    "what this is": "Which machines Kaleidoscope has been run on, and which ones have only had a compiler check.",
    "run on": [TESTED_PLATFORM],
    "compiler checked only": {
        "meaning": "The compiler accepts the memory engine's source for this platform when it is asked from a Mac. Nothing was ever assembled into a program for it, nothing was linked, and nothing has been run there.",
        "checked from": TESTED_PLATFORM,
        "covers": "the memory engine only, not the command-line tool you would run and not the client libraries",
        "platforms": [
            {"platform": "macOS", "architecture": "x86_64", "result": "passed"},
            {"platform": "Linux", "architecture": "x86_64", "result": "passed"},
            {"platform": "Linux", "architecture": "arm64", "result": "passed"},
            {"platform": "Windows", "architecture": "x86_64", "result": "passed"},
        ],
    },
    "not checked at all": [{"platform": "Windows", "architecture": "arm64"}],
    "does not establish": [
        "that a program was ever built for these platforms",
        "that anything runs there",
        "that an installer, a credential store or an editor works there",
        "that any build is available for them",
    ],
}

STATUS_RECORD = {
    "schema_version": "kaleidoscope.docs-status.v1",
    "as of": TODAY.isoformat(),
    "summary": "Kaleidoscope is not released. Nothing here installs from a package registry, nothing is signed for release, and signing in does not work.",
    "released": False,
    "publicly available": False,
    "what you can do today": [
        "Read the documentation, the command reference and the two-tool agent contract.",
        "On a Mac with Apple Silicon, run a build you already have and connect an editor to it.",
    ],
    "what you cannot do today": [
        "Install Kaleidoscope from npm or PyPI: neither package is published.",
        "Download a build: none is offered, for any platform.",
        "Sign in or create an account: every account command answers 'provider not configured'.",
        "Use hosted memory: there is no service, endpoint, API or waitlist.",
        "Read a benchmark score: none is published.",
        "Rely on any support commitment: none is offered.",
    ],
    "packages": {
        "published to a registry": False,
        "signed for release": False,
        "version": PACKAGE_VERSION,
        "npm": {
            "client": "@kleos-research/kaleidoscope",
            "platform package": "@kleos-research/kaleidoscope-darwin-arm64",
        },
        "python": {
            "client": "kaleidoscope-memory",
            "platform package": "kaleidoscope-memory-native-darwin-arm64",
        },
        "the client package contains": "the public SDK and the kaleidoscope and kscope commands",
        "the platform package contains": "the local manager and the memory engine, as proprietary object code",
        "the platform package is built for": [TESTED_PLATFORM],
    },
    "platforms": PLATFORM_SUPPORT,
    "hosts": HOST_SUPPORT,
    "licences": {
        "this documentation": "CC BY 4.0, in force",
        "the public code": "Apache-2.0, in force",
        "the product terms": "unreviewed drafts, not in force; no counsel has read them",
    },
    "still true before any release": {
        "packages published to a registry": False,
        "builds signed for release": False,
        "product terms reviewed by legal counsel": False,
        "sign-in service configured": False,
        "support offered": False,
        "security contact published": False,
        "any platform other than macOS on Apple Silicon verified": False,
        "any editor run against a live model provider": False,
        "benchmark score published": False,
        "hosted memory built": False,
    },
}

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
    "schema_version": "kaleidoscope.docs-mcp-reference.v2",
    "what this is": "The two tools an agent sees when it connects to Kaleidoscope, and the fields each one takes.",
    "released": False,
    "publicly available": False,
    "transport": "stdio",
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
    "release_readiness_claimed": False,
}


@dataclass(frozen=True)
class Page:
    route: str
    title: str
    description: str
    body: str
    section: str = "docs"
    noindex: bool = False
    release_bound: bool = False
    notice: str = ""


def legal_document_body(filename: str, summary: str) -> str:
    source = PUBLIC_FILES[f"legal/{filename}"].read_text(encoding="utf-8")
    return (
        f'<p class="lede">{html.escape(summary)}</p>'
        f'<p><a href="/legal/{html.escape(filename, quote=True)}">'
        "Download the plain-text source</a>.</p>"
        f'<pre class="legal-document"><code>{html.escape(source)}</code></pre>'
    )


# The documentation nav is grouped into named areas. Each entry is
# (route, sidebar label, one-line blurb used by the documentation index).
DOC_SECTIONS = (
    (
        "Start",
        (
            ("/docs/", "Overview", "what Kaleidoscope is, and which page you need"),
            (
                "/docs/getting-started/",
                "Getting started",
                "the five commands you will run, in order",
            ),
            (
                "/docs/packages/",
                "Install",
                "the two package names, what is inside them, and why you cannot get them yet",
            ),
            (
                "/docs/concepts/",
                "Concepts",
                "what a profile, a vault, and an account are",
            ),
        ),
    ),
    (
        "Reference",
        (
            ("/docs/cli/", "CLI", "every kaleidoscope command and flag"),
            ("/docs/mcp/", "MCP", "how to write a correct search or remember call"),
            (
                "/docs/integrations/",
                "Integrations",
                "find your editor, agent, or framework and connect it",
            ),
        ),
    ),
    (
        "Operate",
        (
            (
                "/docs/operations/",
                "Operations",
                "back up your memory, move it, uninstall, delete a vault",
            ),
            (
                "/docs/account/",
                "Account",
                "what signing in would do, and what it never touches",
            ),
            (
                "/docs/troubleshooting/",
                "Troubleshooting",
                "the six things that go wrong, and what causes each",
            ),
        ),
    ),
    (
        "Boundaries",
        (
            (
                "/docs/security/",
                "Security",
                "what is isolated from what, and how to report a vulnerability",
            ),
            (
                "/docs/privacy/",
                "Privacy",
                "what stays on your machine, and what this website itself does",
            ),
            (
                "/docs/legal/",
                "Legal (drafts)",
                "which licences are in force, and which terms are unreviewed drafts",
            ),
        ),
    ),
    (
        "Status",
        (
            (
                "/docs/status/",
                "What works today",
                "the platforms and editors that have actually been run",
            ),
            (
                "/docs/compatibility/",
                "Platform support",
                "does this run on my machine",
            ),
            (
                "/docs/benchmarks/",
                "Benchmarks",
                "why there is no published score yet",
            ),
            (
                "/docs/release-notes/",
                "Release notes",
                "there have been no releases; this is where they will appear",
            ),
        ),
    ),
)

DOC_NAV = tuple(
    (route, label)
    for _section, entries in DOC_SECTIONS
    for route, label, _blurb in entries
)

NAV_LABELS = dict(DOC_NAV)

# Routes whose breadcrumb names the area they belong to. The "Start" area and
# the first entry of every other area are self-evident from the title and are
# left unlabelled.
SECTION_CRUMB_ROUTES = frozenset(
    route
    for section, entries in DOC_SECTIONS
    if section != "Start"
    for route, _label, _blurb in entries[1:]
)

# Routes that own a nested route family; a child page names its parent.
PARENT_ROUTES = ("/docs/integrations/", "/docs/legal/")


def section_of(route: str) -> str:
    for section, entries in DOC_SECTIONS:
        if any(entry[0] == route for entry in entries):
            return section
    return ""


def parent_route(route: str) -> str:
    for parent in PARENT_ROUTES:
        if route != parent and route.startswith(parent):
            return parent
    return ""


def doc_area_rows() -> str:
    rows = []
    for section, entries in DOC_SECTIONS:
        cells = "".join(
            f'<span class="entry"><a href="{route}">{html.escape(label)}</a>'
            f" — {html.escape(blurb)}</span>"
            for route, label, blurb in entries
        )
        rows.append(
            f'<li><span class="k">{html.escape(section)}</span>'
            f'<span class="v">{cells}</span></li>'
        )
    return f'<ul class="rows">{"".join(rows)}</ul>'


DRAFT_NOTICES = {
    "legal-index": (
        '<span class="tag">Review drafts — not in force</span>'
        "<p><strong>The product terms below have not been reviewed by legal "
        "counsel.</strong> Apache-2.0 and CC BY 4.0 are authorized license "
        "selections and are in force for the material they cover. The engine "
        "EULA, privacy notice, security policy, and support policy are "
        "source-controlled drafts: not in force, not offers or contracts, and "
        "not a description of terms that govern anything today. The production "
        "entity, jurisdiction, contacts, operational commitments, and external "
        "legal review are all outstanding.</p>"
    ),
    "legal-draft": (
        '<span class="tag">Review draft — not in force</span>'
        "<p><strong>This document has not been reviewed by legal "
        "counsel.</strong> It is a source-controlled draft published for "
        "inspection and comment. It is not in force, is not an offer or a "
        "contract, does not create any obligation or commitment, and does not "
        "describe terms that currently govern any product, service, or "
        "relationship. Kaleidoscope is not publicly released; the governing "
        "terms will be published separately with a production release. Do not "
        "rely on this text.</p>"
    ),
}


def draft_notice_html(page: Page) -> str:
    if not page.notice:
        return ""
    return (
        '<div class="notice-band"><div class="shell">'
        f'<div class="draft-notice" role="note">{DRAFT_NOTICES[page.notice]}</div>'
        "</div></div>"
    )


def heading_slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")


def annotate_body(body: str) -> tuple[str, str]:
    """Add heading anchors, wrap tables, make scrollers focusable.

    Returns the rewritten body and the on-this-page table of contents.
    """
    headings: list[tuple[str, str]] = []

    def anchor(match: re.Match[str]) -> str:
        markup = match.group(1)
        text = re.sub(r"<[^>]+>", "", markup)
        slug = heading_slug(text)
        headings.append((slug, text))
        return f'<h2 id="{slug}">{markup}</h2>'

    body = re.sub(r"<h2>(.*?)</h2>", anchor, body, flags=re.S)

    def wrap_table(match: re.Match[str]) -> str:
        before = body[: match.start()]
        titles = re.findall(r'<h2 id="[^"]*">(.*?)</h2>', before, flags=re.S)
        label = (
            f'{re.sub(r"<[^>]+>", "", titles[-1])} table' if titles else "Table"
        )
        return (
            f'<div class="table-scroll" tabindex="0" role="region" '
            f'aria-label="{html.escape(label, quote=True)}">{match.group(0)}</div>'
        )

    body = re.sub(r"<table>.*?</table>", wrap_table, body, flags=re.S)
    body = re.sub(r"<pre(?=[ >])", '<pre tabindex="0"', body)

    toc = ""
    if len(headings) >= 3:
        items = "".join(
            f'<li><a href="#{slug}">{text}</a></li>' for slug, text in headings
        )
        toc = f'<ul class="toc" aria-label="On this page">{items}</ul>'
    return body, toc


PAGES = (
    Page(
        route="/docs/",
        title="Kaleidoscope documentation",
        description="Documentation for Kaleidoscope: the local CLI, the two MCP tools, profiles, integrations, security and privacy boundaries, and what works today.",
        body=f"""
<p class="lede">Kaleidoscope is local memory for agents. Your memory lives in a vault on your machine, and every editor or agent you connect shares one profile through a CLI and a long-lived MCP server.</p>
<div class="callout"><strong>Kaleidoscope is not released.</strong> You cannot install it from npm or PyPI, you cannot sign in, and there is no public source repository for the clients yet. <a href="/docs/status/">What works today</a> lists what has actually been run, and on what.</div>
<section>
  <h2>Start here</h2>
  <div class="cards">
    <article><h3><a href="/docs/getting-started/">Getting started</a></h3><p>The five commands you will run, in order, from creating a profile to disconnecting cleanly.</p><p class="s">Five commands</p></article>
    <article><h3><a href="/docs/packages/">Install</a></h3><p>What the two packages will be called, what is inside them, and why you cannot get them yet.</p><p class="s">Not available</p></article>
    <article><h3><a href="/docs/mcp/">MCP</a></h3><p>Write a correct <code>search</code> or <code>remember</code> call against the two-tool contract.</p><p class="s">Two tools</p></article>
  </div>
</section>
<section>
  <h2>By area</h2>
  {doc_area_rows()}
</section>
<section>
  <h2>Choose a path</h2>
  <ul class="rows">
    <li><span class="k">Using an agent</span><span class="v">Start at <a href="/docs/getting-started/">Getting started</a>, then <a href="/docs/concepts/">Concepts</a> for what a profile and a vault actually are.</span></li>
    <li><span class="k">Building on it</span><span class="v">Find your editor or framework in <a href="/docs/integrations/">Integrations</a>, then write calls against the <a href="/docs/mcp/">MCP</a> contract.</span></li>
    <li><span class="k">Running it day to day</span><span class="v">Use <a href="/docs/operations/">Operations</a> to back up, move, or delete a vault, and <a href="/docs/troubleshooting/">Troubleshooting</a> when a host cannot see the tools.</span></li>
    <li><span class="k">Reviewing it</span><span class="v">Read <a href="/docs/security/">Security</a> for what is isolated from what, and <a href="/docs/privacy/">Privacy</a> for what leaves your machine and what this website itself does.</span></li>
    <li><span class="k">An agent or crawler</span><span class="v">Read <a href="/llms.txt">llms.txt</a>, or the expanded <a href="/llms-full.txt">llms-full.txt</a>.</span></li>
  </ul>
</section>
""",
    ),
    Page(
        route="/docs/getting-started/",
        release_bound=True,
        title="Getting started",
        description="Create a local Kaleidoscope profile, connect your editor or agent, check that search and remember appear, and disconnect cleanly — plus why you cannot install it yet.",
        body="""
<p class="lede">These are the five commands you will run, in order. You cannot run the first one, because nothing installs from a registry yet; the four below it are real, and they are the ones we run.</p>
<div class="callout"><strong>You cannot install Kaleidoscope yet.</strong> Neither package has been published, so step 1 is blocked for everyone. Steps 2 to 5 have each been run on a Mac with Apple Silicon, which is the only kind of machine anything has ever been run on.</div>
<h2>1. Install — not possible yet</h2>
<p>There is no way to install Kaleidoscope today. Neither package exists in a registry, and both names return 404. When they publish, the npm package will be <code>@kleos-research/kaleidoscope</code> and will need Node.js 22 or newer; the Python package will be <code>kaleidoscope-memory</code> and will need Python 3.11 or newer. You install one of them, not both. Either one gives you the <code>kaleidoscope</code> and <code>kscope</code> commands and brings in a second package built for your platform, which carries the engine.</p>
<h2>2. Create a profile</h2>
<pre><code>kaleidoscope init --profile default --root /absolute/path/to/your/kaleidoscope-memory
kaleidoscope config --profile default --json</code></pre>
<p>A profile is one memory store on your machine, at a path you choose and own. A missing or invalid root is refused rather than created for you. What gets written into your editor's configuration later is <code>mcp --profile NAME</code> — never a credential, never the raw location of your vault.</p>
<h2>3. Preview the change, then connect</h2>
<pre><code>kaleidoscope connect codex --profile default --project "$PWD" --dry-run
kaleidoscope connect codex --profile default --project "$PWD"
kaleidoscope doctor --project "$PWD"</code></pre>
<p>The first command shows you the exact change and writes nothing. Applying it touches only the block Kaleidoscope owns, so your existing settings survive; an ambiguous, symlinked, tampered, or concurrently edited file is refused rather than overwritten. The hosts the command knows are <code>codex</code>, <code>claude</code>, <code>cursor</code>, and <code>opencode</code>.</p>
<p>Codex, Claude Code, and OpenCode have each been connected this way for real, on a Mac with Apple Silicon. Cursor's configuration is written and removed correctly, but nobody has ever launched Cursor against it.</p>
<h2>4. Check that both tools appeared</h2>
<p>Restart your editor after connecting, then look at the tools it lists for Kaleidoscope. You should see exactly two, <code>search</code> and <code>remember</code>. If you see none, or more than two, go to <a href="/docs/troubleshooting/">Troubleshooting</a>. Operator commands are never offered to a model, so two is the correct number in every host.</p>
<h2>5. Disconnect safely</h2>
<pre><code>kaleidoscope disconnect codex --project "$PWD" --dry-run
kaleidoscope disconnect codex --project "$PWD"</code></pre>
<p>Disconnect removes only what Kaleidoscope wrote and leaves the rest of the host's settings, and every byte of your vault, alone. Disconnecting, uninstalling, signing out, and deleting a vault are four separate operations, and the first three never delete memory. <a href="/docs/operations/">Operations</a> covers the other three.</p>
""",
    ),
    Page(
        route="/docs/packages/",
        release_bound=True,
        title="Install",
        description="The npm and Python package names for Kaleidoscope, what each one installs, what your machine needs, and why neither is available yet.",
        body="""
<p class="lede">You cannot install Kaleidoscope today. Neither package exists in a registry, so both names on this page return 404. What follows is what you will install once they publish, what is inside, and what your machine will need.</p>
<h2>The two packages</h2>
<table><thead><tr><th>Ecosystem</th><th>Package</th><th>Requires</th><th>Status</th></tr></thead><tbody>
<tr><td>npm</td><td><code>@kleos-research/kaleidoscope</code></td><td>Node.js 22 or newer</td><td>Not available</td></tr>
<tr><td>PyPI</td><td><code>kaleidoscope-memory</code></td><td>Python 3.11 or newer</td><td>Not available</td></tr>
</tbody></table>
<p>These names are final. You only need one of them: both install the same two commands, <code>kaleidoscope</code> and <code>kscope</code>, and both give you the same local memory. Pick whichever ecosystem your project already uses.</p>
<h2>What is inside</h2>
<p>Installing one of these gets you two things. The first is the package for your language: the full client library for TypeScript or Python, and the <code>kaleidoscope</code> and <code>kscope</code> commands. The second is a package built for your platform, which carries the engine that stores and ranks your memory.</p>
<p>That engine is proprietary object code. Its source is not in either package, and a native binary is still inspectable — shipping object code is not a claim that it cannot be read. Everything around the engine is open: the command-line tool, both SDKs, every integration, and the agent skill are Apache-2.0.</p>
<p>Today the only platform package that exists is for macOS on Apple Silicon. Neither ecosystem uses an install hook, a download at install time, a compiler, or a source-build fallback — installing puts files on your disk, and that is all it does.</p>
<h2>Why you cannot install it yet</h2>
<p>There is no public installation channel. <code>@kleos-research/kaleidoscope</code> is not on npm and <code>kaleidoscope-memory</code> is not on PyPI. Archives, tarballs, and wheels do exist, but they are private test builds, not downloads, and there is nowhere to fetch them from.</p>
<p>Nothing is signed for production either. There is no Apple signing and no notarisation; the only signature that exists is a test fixture checked into the source tree, and the native code is ad-hoc signed only. None of that is a supply-chain guarantee, and it has to be real before either package can publish.</p>
""",
    ),
    Page(
        route="/docs/concepts/",
        title="Concepts and boundaries",
        description="What a profile, a vault, and an account are in Kaleidoscope, and the boundary that matters: your local memory versus your account metadata.",
        body="""
<p class="lede">The boundary that matters is your local memory versus your account metadata — not merely whether you are signed in.</p>
<h2>Local engine</h2>
<p>The proprietary native engine owns the memory algorithm, the canonical vault on your machine, the graph, ranking, and the stdio MCP behavior. Its source is not part of the public CLI, client, integration, or skill surfaces.</p>
<h2>Manager and profile</h2>
<p>The <code>kaleidoscope</code> command creates profiles, validates the engine launch descriptor, edits host configuration safely, runs offline diagnostics, installs agent guidance, and carries the account and device commands. A profile may hold one explicit account UUID reference locally; that changes neither its vault identity nor its credentials.</p>
<h2>What gets installed</h2>
<p>You install one package for your language — the npm package or the Python package — and it brings in a second package built for your platform. The language package holds the full public client, the typed resolver that finds the installed payload, and the <code>kaleidoscope</code> and <code>kscope</code> commands. The platform package holds the manager and the proprietary engine as object code. Neither one contains engine source, and neither downloads anything at install time.</p>
<h2>One profile, every tool</h2>
<p>Codex, Claude Code, Cursor, OpenCode, framework clients, and generic MCP clients are consumers of the same profile. They do not become separate memory stores merely because their configuration formats differ.</p>
<h2>Account identity</h2>
<p>Signing in is designed to link a product account and a device. The account protocol rejects memory fields and absolute local paths before transport. Signing out or unlinking is not a vault operation, and must not be read as consent to upload memory.</p>
<h2>Hosted memory</h2>
<p>A hosted service is a later product requiring separate authorization, tenant isolation, retention, residency, deletion, sync, billing, and incident-response contracts. It does not exist, and signing in does not opt you into it.</p>
""",
    ),
    Page(
        route="/docs/cli/",
        title="CLI reference",
        description="Every kaleidoscope command and flag: set up a local profile, connect your editor or agent, run diagnostics, and manage an account.",
        body="""
<p class="lede">The command you will run is <code>kaleidoscope</code>. It sets up your local memory, connects your editor or agent to it, and tells you what is wrong when something does not work. You cannot install it yet, so read this as the reference for the command surface rather than a set of steps to follow now.</p>
<p><code>kscope</code> is the engine executable. It is installed alongside <code>kaleidoscope</code> and you do not normally run it yourself.</p>
<p><a href="/reference/kaleidoscope-cli.txt">Read the full <code>kaleidoscope</code> help text</a>.</p>
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
<p><code>init</code> creates a profile and a vault. <code>connect</code> writes the entry your editor or agent needs and <code>disconnect</code> takes it back out; both touch only what Kaleidoscope owns. <code>instructions</code> installs or removes the agent guidance files for a project. <code>doctor</code> reports on your profile, engine, and host configuration without printing memory content or credentials.</p>
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
<p>None of these work today. All remote account commands intentionally fail with <code>provider not configured</code>, because no production sign-in service is published. You do not need an account to use your local memory.</p>
<p>When they do work: <code>account identities</code> lists the opaque IDs that <code>account unlink</code> takes, and nothing else. <code>account revoke-session</code> revokes the session you are in — it does not deactivate an account. The <code>profile account</code> commands write a non-secret account ID into your local profile and nothing more: they do not start the engine, contact any service, touch a vault, or store a credential.</p>
<h2>Safety invariants</h2>
<ul><li>Any command that changes a host file can be previewed with <code>--dry-run</code>, which changes nothing, and asks you to confirm before it writes.</li><li>An unknown, conflicting, symlinked, tampered, or concurrently edited target is refused rather than overwritten.</li><li>Changes are backed up, and removal is recorded so that running it twice is safe.</li><li>The configuration written for your editor or agent contains no tokens, no provider keys, and no vault location.</li><li>Account traffic goes to a closed list of account-only routes. It is separate from the local memory connection.</li></ul>
""",
    ),
    Page(
        route="/docs/mcp/",
        release_bound=True,
        title="MCP reference",
        description="Write a correct search or remember call: the two tools Kaleidoscope gives an agent, their fields, worked examples, and how the session works.",
        body="""
<p class="lede">Your editor or agent sees exactly two tools from Kaleidoscope: <code>search</code> and <code>remember</code>. Nothing else is callable by a model. This page is what you need to write a correct call to either one.</p>
<p>There is no way to install Kaleidoscope yet, so you cannot connect a host of your own today — see <a href="/docs/packages/">Install</a>. The contract below is the one that runs locally.</p>
<p><a href="/reference/kaleidoscope-mcp.json">Read the machine-readable tool reference</a>.</p>
<h2><code>search</code></h2>
<p>Send exactly one of <code>query</code> or <code>memory_id</code>. A <code>query</code> ranks your memories and returns them under <code>selected_hits</code>. A <code>memory_id</code> is an addressed read: it returns that one memory at the top level and refuses ranking controls. Keep <code>top_k</code> small — about 5 is normal — and set a bounded <code>maximum_context_bytes</code>. <code>ledger</code> accepts only <code>true</code>.</p>
<pre><code>{"query":"how do we handle database migrations","top_k":5,"ledger":true}</code></pre>
<p>A query also writes down what it returned. That record goes into your vault on your machine, next to the memories themselves, and it stays there — it is what a later authenticated tool would use to tell which memories actually helped.</p>
<h2><code>remember</code></h2>
<p><code>mode</code> is required and is <code>create</code>, <code>update</code>, or <code>delete</code>. For a create or an update, <code>content_md</code> is the memory as you want to read it back and must begin with an H1, and <code>semantic_delta</code> carries the structure: a title and at least one fact. Every endpoint a fact names is declared with <code>n</code>, the surface the fact refers to it by; <code>kind</code>; and <code>is</code>, a short gloss. Predicates are snake_case. An update or a delete needs <code>memory_id</code> and <code>expected_version_id</code>. Batching through <code>items</code> accepts at most 20 creates, and items do not share structure with each other.</p>
<pre><code>{"mode":"create",
 "content_md":"# Ana owns the billing service\\n\\nAna took it over after the payments team split.",
 "semantic_delta":{
   "memory_type":"decision",
   "title":"Ana owns the billing service",
   "entities":[
     {"n":"Ana","kind":"person","is":"backend engineer on my team"},
     {"n":"billing service","kind":"service","is":"the service that issues invoices"}],
   "facts":[{"subject":"Ana","predicate":"owns","object":"billing service"}]}}</code></pre>
<p>Write the <code>is</code> gloss properly. It is not documentation — it is what the engine matches on when it decides whether two mentions of a name are the same thing, so <code>Ana | person | backend engineer on my team</code> finds far more than <code>Ana</code> alone does.</p>
<p><code>remember</code> infers nothing from what you wrote. The entities, facts, relationships, and dates it stores are the ones you state explicitly. Treat the tool schema your host discovered as the authority for which memory types and fields a build accepts, rather than copying a vocabulary out of prose.</p>
<h2>Lifecycle</h2>
<p>Your host keeps one long-lived process alive across calls and talks to it over stdio at MCP protocol revision <code>2025-11-25</code>. It negotiates once, enforces a startup deadline, cancels cleanly, bounds what it reads from stderr, and shuts the process down without leaving an orphan behind. A framework integration will not run a second retrieval behind your back.</p>
<h2>What a model never sees</h2>
<p>Feedback, lifecycle and import, maintenance, ontology, and diagnostics are operator commands, not tools. They are absent from the list your agent discovers. Search results do not carry the handle those commands need either, so there is no path from a model to them and nothing to reconstruct.</p>
""",
    ),
    Page(
        route="/docs/integrations/",
        title="Agent and framework integrations",
        description="Find your editor, agent, or framework, see how far it has been tested, and get the exact command that connects it.",
        body="""
<p class="lede">Find your editor or framework below, then follow its page for the exact commands. Whatever you connect, it talks to the one engine on your machine and sees exactly two tools, <code>search</code> and <code>remember</code> — so every tool you connect shares the same memory instead of starting a store of its own.</p>
<p>“Tested” means we have run it ourselves on a Mac with Apple Silicon and it worked. “Partly tested” means part of it has been run and part has not; the limitation column says which part. Neither word means released or supported — the full definitions are on <a href="/docs/compatibility/">Platform support</a>.</p>
<table><thead><tr><th>Integration</th><th>Status</th><th>Limitation</th><th>How you connect</th></tr></thead><tbody>
<tr><td><a href="/docs/integrations/codex/">Codex</a></td><td>Partly tested</td><td>Its configuration is written and removed exactly, but Codex gives no way to confirm it then started the server</td><td><code>kaleidoscope connect codex</code></td></tr>
<tr><td><a href="/docs/integrations/claude-code/">Claude Code</a></td><td>Tested</td><td>—</td><td><code>kaleidoscope connect claude</code></td></tr>
<tr><td><a href="/docs/integrations/opencode/">OpenCode</a></td><td>Tested</td><td>Stable v1 by default; beta v2 only if you ask for it</td><td><code>kaleidoscope connect opencode</code></td></tr>
<tr><td><a href="/docs/integrations/cursor/">Cursor</a></td><td>Partly tested</td><td>Its configuration is written and removed correctly, but Cursor has never been launched against it</td><td><code>kaleidoscope connect cursor</code></td></tr>
<tr><td><a href="/docs/integrations/generic-mcp/">Generic MCP, Python and TypeScript</a></td><td>Tested</td><td>—</td><td>Read the descriptor with <code>kaleidoscope config --profile default --json</code></td></tr>
<tr><td><a href="/docs/integrations/langchain/">LangChain</a> and <a href="/docs/integrations/langgraph/">LangGraph</a></td><td>Partly tested</td><td>Run against a stand-in model, never against a live provider</td><td>The LangChain MCP adapter</td></tr>
<tr><td><a href="/docs/integrations/claude-agent-sdk/">Claude Agent SDK</a></td><td>Partly tested</td><td>Run against a stand-in model, never against a live provider</td><td>The SDK’s own stdio MCP configuration</td></tr>
<tr><td><a href="/docs/integrations/openai-agents-sdk/">OpenAI Agents SDK</a></td><td>Partly tested</td><td>Run against a scripted model, never against a live provider</td><td>The SDK’s stdio MCP server lifecycle</td></tr>
<tr><td><a href="/docs/integrations/crewai/">CrewAI</a></td><td>Partly tested</td><td>Run against a local test server, never against a live provider</td><td>The CrewAI MCP adapter context</td></tr>
</tbody></table>
<p>The editor versions we tested against were Codex 0.149.0, Claude Code 2.1.239, and OpenCode 1.18.21. None of this installs from a registry yet, so connecting an editor means pointing it at a build you already have on your machine.</p>
<h2>Integration pages</h2>
<ul class="rows">
<li><span class="k">Editors and CLIs</span><span class="v"><a href="/docs/integrations/codex/">Codex</a> — one entry in Codex’s own configuration, removable byte for byte; <a href="/docs/integrations/claude-code/">Claude Code</a> — one entry in <code>.mcp.json</code>; <a href="/docs/integrations/cursor/">Cursor</a> — one entry in <code>mcp.json</code> plus an optional project rule; <a href="/docs/integrations/opencode/">OpenCode</a> — stable v1 by default, beta v2 only when you ask.</span></li>
<li><span class="k">Direct MCP</span><span class="v"><a href="/docs/integrations/generic-mcp/">Python and TypeScript generic MCP</a> — the launch descriptor any standard MCP client can read, over one long-lived process.</span></li>
<li><span class="k">Agent frameworks</span><span class="v"><a href="/docs/integrations/claude-agent-sdk/">Claude Agent SDK</a> — one client, two allowed tool names; <a href="/docs/integrations/langchain/">LangChain</a> and <a href="/docs/integrations/langgraph/">LangGraph</a> — one session, no second memory store; <a href="/docs/integrations/openai-agents-sdk/">OpenAI Agents SDK</a> — Python and TypeScript; <a href="/docs/integrations/crewai/">CrewAI</a> — one adapter context for the crew run.</span></li>
</ul>
<h2>Telling your agent about it</h2>
<p>Install the <a href="/SKILL.md">public skill</a>, then add the short pointer that fits your project — <a href="/snippets/AGENTS.md">AGENTS.md</a>, <a href="/snippets/CLAUDE.md">CLAUDE.md</a>, or the <a href="/snippets/cursor-kaleidoscope.mdc">Cursor rule</a>. Make the change with <code>kaleidoscope</code> rather than by hand, so you keep the dry run, the backup, and exact removal.</p>
""",
    ),
    Page(
        route="/docs/operations/",
        title="Operations",
        description="Where your memory lives, how to back it up and restore it, and how disconnecting, uninstalling, logging out and deleting a vault differ.",
        body="""
<p class="lede">Your memory lives in one place on your machine — a vault directory you chose. Everything else Kaleidoscope touches (editor configuration, agent instructions, account credentials, the installed executables) has its own lifecycle, and removing any of them does not remove your memory.</p>
<h2>Find your profile first</h2><p>You named a vault root when you initialized a profile. To see which profile is active and where it points, without printing credentials or any memory content:</p>
<pre><code>kaleidoscope profile list
kaleidoscope config --profile default --json
kaleidoscope doctor --project "$PWD"</code></pre>
<h2>Back up and restore</h2><p>Back up by copying the whole vault directory while nothing is connected to it — close the editors and agents you have connected first, so nothing is writing to it mid-copy. Copy the directory as a whole; a partial copy is not a vault. To restore, or to move your memory to another machine or another path, put the directory back and point a profile at it:</p>
<pre><code>kaleidoscope init --profile default --root /absolute/path/to/the/vault</code></pre>
<h2>Disconnect and uninstall</h2><p>These are four separate operations, and it matters that you know which one you are doing.</p>
<ul>
<li><code>kaleidoscope disconnect HOST</code> removes only the configuration Kaleidoscope itself wrote into that editor. Other settings in the same file are left alone.</li>
<li><code>kaleidoscope instructions remove</code> removes the agent guidance pointer, which is a separate thing from the connection.</li>
<li>Uninstalling the package removes the executables.</li>
<li><code>kaleidoscope logout</code> removes or revokes account credentials.</li>
</ul>
<p>None of the four deletes a vault. Your memory survives all of them.</p>
<h2>Delete a vault</h2><p>Deleting a vault is deliberately its own operation: it previews what it will delete, asks you to confirm, and acts on exactly one fully resolved path. A broad path, an unresolved variable, or an ambiguous target is refused rather than guessed at. Deleting a memory and deleting the vault that holds it are different acts — the first is something you ask the engine to do, the second removes the files.</p>
<h2>Install, update, and roll back</h2><p>Installing, updating, rolling back to the previous version, and uninstalling have each been run on a Mac with Apple Silicon and behaved correctly, and a vault kept alongside was byte-for-byte identical afterwards. That is the whole of what has been established. Nothing is signed for production, and there is no channel to update from yet, so this is not a supported update path — it is a mechanism we have run once, on one machine.</p>
<h2>What gets installed</h2><p>Two things: a language package for npm or Python, and a second package built for your platform. The language package holds the client library and the <code>kaleidoscope</code> and <code>kscope</code> commands; the platform package holds the manager and the engine, as object code. There is no install hook, runtime download, compiler, or source-build fallback — nothing is fetched or built on your machine after the download. The engine source is in neither package.</p>
""",
    ),
    Page(
        route="/docs/security/",
        title="Security",
        description="What Kaleidoscope keeps on your machine, what account commands can send, what is not signed, and how to report a vulnerability.",
        body="""
<p class="lede">Kaleidoscope’s engine is distributed as object code rather than source. That is a distribution choice, not a security guarantee: a native binary on your machine is still inspectable and may be reverse engineered, and shipping object code is not a claim of impossibility. What this page describes is the boundaries you can check — what the engine can reach, what account commands can send, and what is not signed.</p>
<h2>What the engine can reach</h2><p>The engine keeps your memory in a local vault, speaks stdio to your editor, declares no required network access, and makes no external model calls. When the manager launches it, it hands over a closed, non-secret environment rather than passing along whatever is in yours — your model-provider keys, account tokens, cloud credentials and the vault’s location are not part of what the engine process receives.</p>
<h2>What account commands can send</h2><p>Account commands never touch the memory engine. The manager can reach exactly eleven account routes and no others, and a guard rejects memory and profile fields, and absolute local paths, before anything is sent. With the engine deliberately removed from the machine, all eleven still refused cleanly with <code>provider not configured</code> — they fail before anything local is opened. There is no production account service to reach in any case.</p>
<h2>Nothing is signed for production</h2><p>There is no Apple signing and no notarisation. The only signature that exists anywhere in the build is a test fixture checked into the source, and the native code is ad-hoc signed only. Do not read any of this as a supply-chain guarantee: nothing here lets you verify that a file you received is the file we built. Production trust roots, signing identities and the final notices that go with them do not exist yet.</p>
<h2>What we have checked for leaks</h2><p>We put distinctive marker values into the environment, the profiles, the editor configuration and the MCP traffic, then check that none of them turn up in output. That is a scoped test on one platform, not a proof that nothing ever leaks — it can only find the kinds of leak it was written to look for.</p>
<h2>Report a vulnerability</h2><p>Do not publish an exploit or a sensitive report in a public issue. There is no security contact to send it to yet; publishing one, along with a policy saying which versions get fixes, is something that has to happen before release. It will appear on this page and at <code>/.well-known/security.txt</code>.</p>
""",
    ),
    Page(
        route="/docs/privacy/",
        title="Privacy and data boundary",
        description="What stays on your machine, what signing in can send, how credentials are stored, what is not yet approved, and what this website itself does.",
        body="""
<p class="lede">Your memory and your account identity are separate systems. Signing in does not authorize upload, sync, analysis, training on, or deletion of your memory.</p>
<h2>Your memory stays local</h2><p>Signing in never carries your memory with it. Memory content, the queries you ran, the results you got back, memory IDs, graph data, local paths, vault locations, the internal identifiers Kaleidoscope uses to organise a vault, and any credentials you have stored locally are all excluded from the account protocol. The account client rejects those fields — and any absolute local path — before anything would leave your machine.</p>
<h2>What signing in would send</h2><p>Signing in would send a narrow set of account and device fields — enough to log in, keep you logged in, show your account status, link or unlink another sign-in provider, log out, and manage the devices attached to your account. Nothing else. You cannot sign in today, and the terms that would govern it — who runs the sign-in service, how long anything is kept, how you recover an account, and how you delete one — are not settled. That is one of the reasons sign-in is switched off.</p>
<h2>Where credentials would be kept</h2><p>On a Mac — the only platform Kaleidoscope has been run on — credentials go into the macOS Keychain. Code for the Windows and Linux equivalents exists, but neither has ever been run on those platforms, so treat both as untested. There is no fallback that writes a credential to a plain file, and no sign-in token is ever written into an editor’s configuration or into a profile.</p>
<h2>Network use</h2><p>The engine needs no network access and makes no calls to any model provider. Everything except the account commands works with your machine offline, and the account commands are the only part of Kaleidoscope that is ever meant to talk to a server at all. Nothing has been settled about what a released version would report back, where that would go, or what you would be asked to agree to — and until it is settled and written into terms someone has actually reviewed, sign-in stays switched off.</p>
<h2>This documentation site</h2><p>These pages are static files served by GitHub Pages. They set no cookies, use no local storage, and run no analytics or behavioural script; the only script on any page is an inline JSON-LD block, which does not execute. They do make one third-party request: the three typefaces are fetched from Google Fonts (<code>fonts.googleapis.com</code> and <code>fonts.gstatic.com</code>), so Google receives the request metadata a font fetch carries, including your IP address. Blocking it costs only the typefaces. Nothing on this site reads a vault, a profile, or any local memory.</p>
<h2>Hosted memory</h2><p>There is no hosted service. Kaleidoscope does not sync your memory anywhere, there is no endpoint or API to send it to, and there is no waitlist for one. If that ever changes it will be a separate product with its own terms, and it will not be something a local profile or a sign-in quietly opts you into.</p>
""",
    ),
    Page(
        route="/docs/account/",
        title="Account and devices",
        description="Why you do not need an account, what signing in would manage, and why it never touches your local memory.",
        body="""
<p class="lede">You do not need an account to use Kaleidoscope — your memory lives on your machine and works without one. You also could not sign in today if you wanted to: every command here that reaches the account service answers <code>provider not configured</code>, because no production sign-in service is configured or published.</p>
<h2>What signing in would be for</h2><p>Signing in is designed as an ordinary browser sign-in, with a code-based path for machines that have no browser. It manages your product account and the devices attached to it. It is not a connection to hosted memory: no hosted service, endpoint, API, waitlist, or sync path exists, and signing in would not opt you into one.</p>
<h2>What it never does to your memory</h2><p>Signing in never uploads, syncs, analyses, trains on, or deletes your memory. Memory content, your queries, the results you got back, memory IDs, graph data, local paths, and vault locations are all excluded from the account protocol, and the account client rejects those fields — and any absolute local path — before anything would leave your machine. Credentials go into the macOS Keychain, the only platform this has been run on; there is no plaintext fallback, and no refresh token is ever written into an editor’s configuration or into a profile.</p>
<h2>Commands</h2><p>None of these work yet. They are listed so you can see the shape of what signing in will and will not do.</p><pre><code>kaleidoscope login
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
<p><code>account identities</code> is where you get the opaque UUID that <code>account unlink</code> needs. <code>account revoke-session</code> has the deliberately narrow meaning of revoking the session you are currently using; <code>--local-only</code> warns you that it does not revoke a remote one. The <code>profile account</code> commands write a local, non-secret account reference and nothing else — they do not start the engine, contact any service, change a vault, or store a credential.</p>
<h2>What logging out changes</h2><p>Logging out removes or revokes your credentials, according to the scope you chose. It does not change which profile you are on and it does not alter a single byte of your vault. Deleting a vault is a separate, explicit operation with its own confirmation — see <a href="/docs/operations/">Operations</a>.</p>
""",
    ),
    Page(
        route="/docs/compatibility/",
        title="Platform support",
        description="Which machines Kaleidoscope has actually been run on, which ones have only had a compiler check, and what you need installed.",
        body="""
<p class="lede">Kaleidoscope has only ever been run on a Mac with Apple Silicon. If you are on an Intel Mac, on Linux, or on Windows, it will not run for you today — and there is nothing to download on any platform, including that Mac.</p>
<h2>What the status words mean</h2>
<p>The same five words are used on every page of this site. They describe what you can obtain, not what a test did.</p>
<ul class="rows">
<li><span class="k">Tested</span><span class="v">We have run this ourselves and it worked. It is not released, supported, or signed — but it is not theoretical.</span></li>
<li><span class="k">Partly tested</span><span class="v">Some of this has been run and some has not. Every “Partly tested” row says which part.</span></li>
<li><span class="k">Compiler-checked only</span><span class="v">The compiler accepts the source for this target when it is checked from a Mac. It has never been built into a program for that platform, and nobody has ever run it there. It may or may not work, and there is nothing available for it.</span></li>
<li><span class="k">Untested</span><span class="v">Nobody has run this and nothing has been built for it. Assume it does not work.</span></li>
<li><span class="k">Not available</span><span class="v">This does not exist yet. There is nothing to install, sign up for, or try.</span></li>
</ul>
<h2>Platforms</h2>
<table><thead><tr><th>Platform</th><th>Status</th><th>What you need</th></tr></thead><tbody>
<tr><td>macOS, Apple Silicon</td><td>Tested</td><td>macOS; Node.js 22 or newer, or Python 3.11 or newer</td></tr>
<tr><td>macOS, Intel</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Linux, x86_64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Linux, arm64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Windows, x86_64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Windows, arm64</td><td>Untested</td><td>—</td></tr>
</tbody></table>
<h2>Hosts and frameworks</h2>
<table><thead><tr><th>Host</th><th>Status</th><th>Limitation</th></tr></thead><tbody>
<tr><td>Codex</td><td>Partly tested</td><td>Its configuration is written and removed exactly, but Codex gives no way to confirm it then started the server</td></tr>
<tr><td>Claude Code</td><td>Tested</td><td>—</td></tr>
<tr><td>OpenCode</td><td>Tested</td><td>Stable v1 by default; beta v2 only if you ask for it</td></tr>
<tr><td>Cursor</td><td>Partly tested</td><td>Its configuration is written and removed correctly, but Cursor has never been launched against it</td></tr>
<tr><td>Generic MCP clients, Python and TypeScript</td><td>Tested</td><td>—</td></tr>
<tr><td>Agent frameworks — LangChain, LangGraph, Claude Agent SDK, OpenAI Agents SDK, CrewAI</td><td>Partly tested</td><td>Run against a stand-in model, never against a live model provider</td></tr>
</tbody></table>
<h2>A compiler check is not a working build</h2>
<p>Every row above marked “Compiler-checked only” means one narrow thing, and it is narrower than it sounds. From a Mac, we asked the compiler whether it accepts the source of one part of Kaleidoscope — the memory engine — for that platform, and it said yes. Nothing was ever assembled into a program for that platform, and the step where a program is stitched together from its parts and its system libraries is exactly the step where building for another platform usually fails first. That step has not happened, on any of these rows. The rest of Kaleidoscope — the command-line tool you would actually run, and the client libraries — was not part of the check at all.</p>
<p>So nobody has executed a program, run an installer, touched a credential store, or driven an editor on any platform except a Mac with Apple Silicon. Windows on arm64 is weaker still — it has not even had the compiler check, so do not read it as a quieter version of Windows on x86_64.</p>
<p>Nothing in these tables is an availability claim. There is no build you can download for any platform, and no package in any registry.</p>
""",
    ),
    Page(
        route="/docs/benchmarks/",
        release_bound=True,
        title="Benchmarks",
        description="Why Kaleidoscope publishes no benchmark score, and the three things that would have to be true before one appears here.",
        body="""
<p class="lede">There is no published benchmark score for Kaleidoscope, and nothing on this site claims anything about how well it retrieves or how fast it is. This page explains why, and what would have to be true before you saw a number here.</p>
<h2>Why there is no number here</h2><p>A score a vendor runs on a workload the vendor chose measures what that vendor is good at. If you cannot reproduce it on your own data, on your own machine, it is not information you can act on — it is a claim you have to take on trust. We would rather publish nothing than publish that.</p>
<h2>What would have to be true first</h2><p>Three things, together. The workload has to be described in full: the data, the queries, and how an answer is judged right or wrong. You have to be able to run it yourself, against a build you can actually get, and arrive at the same numbers. And the result has to be reported against a named alternative, so the number means something relative to a choice you might otherwise make.</p><p>None of those hold today, and the first one cannot hold while there is no build to give you.</p>
<h2>What you can check instead</h2><p>The parts of Kaleidoscope that do not need a score are the ones you can read now: the exact two tools an agent gets and the shape of a valid call, on <a href="/docs/mcp/">MCP</a>; where memory lives and what never leaves your machine, on <a href="/docs/privacy/">Privacy</a>; and what has and has not been run, on <a href="/docs/status/">What works today</a>.</p>
""",
    ),
    Page(
        route="/docs/status/",
        release_bound=True,
        title="What works today",
        description="Which platforms Kaleidoscope has actually been run on, which editors and agents connect to it, and everything that has never been tested.",
        body="""
<p class="lede">You cannot install Kaleidoscope today: neither package exists in a registry, there is nothing to sign up for, and no build is offered for download. This page is the plain answer to “can I use this?” — what has been run, on what, and what has never been run at all.</p>
<h2>Platforms</h2>
<p>Kaleidoscope has only ever been run on a Mac with Apple Silicon. Every other row below has had a compiler check and nothing more — nobody has built a program for it or run anything on it. The status words are defined once, on <a href="/docs/compatibility/">Platform support</a>.</p>
<table><thead><tr><th>Platform</th><th>Status</th><th>What you need</th></tr></thead><tbody>
<tr><td>macOS, Apple Silicon</td><td>Tested</td><td>macOS; Node.js 22+ or Python 3.11+</td></tr>
<tr><td>macOS, Intel</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Linux, x86_64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Linux, arm64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Windows, x86_64</td><td>Compiler-checked only</td><td>—</td></tr>
<tr><td>Windows, arm64</td><td>Untested</td><td>—</td></tr>
</tbody></table>
<h2>Hosts you can connect</h2>
<p>Each of these talks to the same local engine over one long-lived stdio MCP process, and each sees exactly two tools: <code>search</code> and <code>remember</code>. No operator command is ever exposed to a model.</p>
<table><thead><tr><th>Host</th><th>Status</th><th>How you connect</th></tr></thead><tbody>
<tr><td>Codex</td><td>Partly tested</td><td><code>kaleidoscope connect codex</code></td></tr>
<tr><td>Claude Code</td><td>Tested</td><td><code>kaleidoscope connect claude</code></td></tr>
<tr><td>OpenCode</td><td>Tested</td><td><code>kaleidoscope connect opencode</code></td></tr>
<tr><td>Cursor</td><td>Partly tested</td><td><code>kaleidoscope connect cursor</code></td></tr>
<tr><td>Agent frameworks</td><td>Partly tested</td><td>their own MCP adapter, given the descriptor from <code>kaleidoscope config --json</code></td></tr>
</tbody></table>
<p>Three of those rows carry a limit. With Codex, Kaleidoscope’s entry is written, read back and removed exactly, but Codex offers no way to confirm it then started the server and saw the two tools — with Claude Code and OpenCode that step was confirmed. Cursor’s configuration and project rule are written and removed correctly, but nobody has launched Cursor against them. The agent frameworks — LangChain, LangGraph, the Claude Agent SDK, the OpenAI Agents SDK and CrewAI — were run against stand-in models, never a live provider. Any other MCP client can use the same descriptor; the Python and TypeScript MCP clients have been tested directly.</p>
<p>The versions we tested against were Codex 0.149.0, Claude Code 2.1.239, and OpenCode 1.18.21. OpenCode’s stable v1 shape is the default; beta v2 has to be asked for explicitly.</p>
<h2>What has not been tested</h2>
<ul>
<li>Any platform other than a Mac with Apple Silicon. No binary has been executed, no installer run, no credential store touched and no editor driven anywhere else.</li>
<li>Windows on arm64. It has not even had the compiler check that the other platforms have had.</li>
<li>Cursor itself. Only its configuration has been written and removed.</li>
<li>Whether Codex actually starts the server after being configured. Its configuration entry is written, read back and removed exactly, and that is as far as Codex’s command line lets us check.</li>
<li>Any editor’s graphical interface. The connections above were made and checked from the command line.</li>
<li>Any run against a live model provider.</li>
<li>Signing in. Every account command refuses with <code>provider not configured</code>.</li>
<li>Any signed build. Nothing is signed for production — no Apple signing, no notarisation.</li>
<li>Any published package. Everything that exists is a private test build.</li>
</ul>
<p>Some things do not exist yet, so there is nothing to test. There is no hosted service, no API and no waitlist. No benchmark score has been published, and nothing on this site claims anything about retrieval quality or speed. No security contact is published yet; it will appear on <a href="/docs/security/">Security</a> and at <code>/.well-known/security.txt</code> before release. There is no public source repository for the clients or SDKs.</p>
""",
    ),
    Page(
        route="/docs/release-notes/",
        release_bound=True,
        title="Release notes",
        description="Kaleidoscope has not been released. This is where release notes will be published, and what each entry will contain.",
        body="""
<p class="lede">Kaleidoscope has not been released, so there are no release notes yet. When it is released, every version will be listed here, newest first.</p>
<p>Each entry will say which platforms that version runs on, which editor and agent versions it was tested against, what changed, what broke or was removed, whether anything you already have needs to be moved or reconfigured, and any security fixes it carries.</p>
<p>Until then, <a href="/docs/status/">What works today</a> is the current picture: what has been run, on what, and what has never been tested.</p>
""",
    ),
    Page(
        route="/docs/troubleshooting/",
        title="Troubleshooting",
        description="Fix the six things that go wrong with Kaleidoscope: tool discovery, OpenCode configuration, a misplaced profile, sign-in, installation, and safe diagnostics.",
        body="""
<p class="lede">Start with <code>kaleidoscope doctor</code> when your profile, engine, or host configuration is misbehaving. Account commands fail on their own separate boundary, so read that section before you conclude that anything local is broken.</p>
<h2>The host cannot find the tools</h2><ol><li>Confirm the active profile is the one you expect.</li><li>Preview the connection with <code>--dry-run</code> and read only the block Kaleidoscope owns.</li><li>Restart the host after a successful connect — most hosts read their configuration once, at startup.</li><li>Confirm the tools it discovered are exactly <code>search</code> and <code>remember</code>.</li></ol>
<h2>OpenCode configuration is refused</h2><p>The stable and beta-v2 configuration shapes differ. Kaleidoscope adopts an existing shape when it is unambiguous, or the version you named explicitly; it never quietly rewrites stable configuration into beta. Remove any duplicate Kaleidoscope entry and run the dry run again.</p>
<h2>A profile points to the wrong place</h2><p>Do not edit the profile by hand. Import the vault you meant to use, or initialise a new one at an explicit path. A missing or invalid root is refused rather than created for you, so nothing is silently written to the wrong place.</p>
<h2>Login says provider not configured</h2><p>That is expected today. No production sign-in service is published, so every remote account command refuses. Do not invent an endpoint, and do not delete or recreate your vault to try to fix it — your account status and your local memory are separate, and you do not need an account to use your memory.</p>
<h2>I cannot install the package</h2><p>No public installation channel exists. The archives, tarballs, and wheels that exist are private test builds signed with a test-only key; they are not downloadable releases, and there is nowhere to fetch them from.</p>
<h2>Before sharing diagnostics</h2><p>Strip local paths, account identifiers, provider keys, tokens, memory content, queries, results, and vault locations before you send anything to anyone. Use the redacted <code>doctor</code> output, which is the artifact meant for that.</p>
""",
    ),
)


INTEGRATION_PAGES = (
    Page(
        route="/docs/integrations/codex/",
        title="Codex integration",
        description="Connect Codex to your local Kaleidoscope profile, with a dry run first and exact removal afterwards.",
        body="""
<p class="lede">Codex reads the same local launch descriptor and the same profile as every other editor you connect. Kaleidoscope owns the change it makes to Codex’s configuration, so you can preview it, and take it back out exactly.</p>
<h2>Connect a project</h2><pre><code>kaleidoscope connect codex --profile default --project "$PWD" --dry-run
kaleidoscope connect codex --profile default --project "$PWD"
kaleidoscope instructions install agents --project "$PWD"</code></pre>
<p>What gets written names an absolute path to the local engine, <code>mcp --profile default</code>, and exactly <code>search</code> and <code>remember</code>. It does not carry your vault location, a provider key, or an account credential.</p>
<h2>What is tested</h2><p>On a Mac with Apple Silicon, Kaleidoscope added its entry to Codex 0.149.0’s configuration, Codex listed and read that entry back, and removing it restored the file byte for byte. That is the part we can vouch for. Codex’s own command line offers no way to confirm that it then launched the server and saw the two tools, so for Codex that step is unconfirmed — it has been confirmed with Claude Code and OpenCode. Codex has also not been driven through a model turn or its terminal interface, and there is no package to install it from yet.</p>
""",
    ),
    Page(
        route="/docs/integrations/claude-code/",
        title="Claude Code integration",
        description="Add Kaleidoscope to Claude Code as one local MCP server entry, plus an optional project pointer.",
        body="""
<p class="lede">Claude Code gets one local MCP server definition from you, and optionally a short project pointer to the public skill. Everything Kaleidoscope writes is marked as its own, so it can take it back out.</p>
<h2>Preview first</h2><pre><code>kaleidoscope connect claude --profile default --project "$PWD" --dry-run
kaleidoscope connect claude --profile default --project "$PWD"
kaleidoscope instructions install claude --project "$PWD"</code></pre>
<p>Only the entry Kaleidoscope owns is written to <code>.mcp.json</code>; the rest of your file is left alone. If the ownership markers have been edited or the file is ambiguous, the change is refused rather than guessed at. The entry publishes only <code>search</code> and <code>remember</code>.</p>
<h2>What is tested</h2><p>Claude Code 2.1.239 has been connected for real on a Mac with Apple Silicon. The entry was written, running the command again did not duplicate it, removing it left the file clean, and Claude Code discovered the two tools. It has not been run through a model turn against an installed package, because there is no package to install yet.</p>
""",
    ),
    Page(
        route="/docs/integrations/claude-agent-sdk/",
        title="Claude Agent SDK integration",
        description="Give a Claude Agent SDK run one Kaleidoscope MCP client and a strict two-name tool allowlist.",
        body="""
<p class="lede">Create one Claude Agent SDK client for the run you intend, and hand it a stdio MCP configuration that names the Kaleidoscope tools explicitly. One client, one process, for the whole run.</p>
<h2>Allowed tools</h2><pre><code>mcp__kaleidoscope__search
mcp__kaleidoscope__remember</code></pre>
<p>Your model-provider credentials stay yours. The descriptor sets an empty environment for the child process, so account tokens, vault locations, and provider keys never reach it.</p>
<h2>What is tested</h2><p>This has been run against a stand-in model, never against a live provider. The test confirms one client and exactly the two tool names above.</p>
""",
    ),
    Page(
        route="/docs/integrations/cursor/",
        title="Cursor integration",
        description="What Kaleidoscope writes for Cursor, how to take it back out, and the honest limit of what has been tried.",
        body="""
<p class="lede">Cursor uses the same local command and the same two tools as every other editor. Kaleidoscope makes the change to Cursor’s JSON reversible, and adds a small project rule only if you ask for one.</p>
<h2>Connect and guide</h2><pre><code>kaleidoscope connect cursor --profile default --project "$PWD" --dry-run
kaleidoscope connect cursor --profile default --project "$PWD"
kaleidoscope instructions install cursor --project "$PWD"</code></pre>
<p>Entries you added yourself are left untouched. A tampered marker, a name that conflicts, a malformed file, a symlink, or a file being edited at the same time is refused and handed back to you rather than overwritten.</p>
<h2>What is tested</h2><p>Kaleidoscope writes Cursor’s configuration and the project rule correctly and removes both exactly — on a Mac with Apple Silicon, and only that far. Nobody has ever launched Cursor against them. Everything past the configuration step is unknown.</p>
""",
    ),
    Page(
        route="/docs/integrations/opencode/",
        title="OpenCode integration",
        description="Connect OpenCode using its stable v1 configuration, or ask explicitly for the beta v2 shape.",
        body="""
<p class="lede">OpenCode stable v1 and beta v2 want different configuration shapes. Kaleidoscope never guesses which one you are on and never quietly moves you between them.</p>
<h2>Stable v1 by default</h2><pre><code>kaleidoscope connect opencode --profile default --project "$PWD" --dry-run
kaleidoscope connect opencode --profile default --project "$PWD"</code></pre>
<h2>Explicit beta v2</h2><pre><code>kaleidoscope connect opencode --profile default --project "$PWD" --opencode-version beta-v2 --dry-run</code></pre>
<p>The stable entry is a direct local command. Beta v2 uses the explicit server shape with code mode turned off, so <code>search</code> and <code>remember</code> stay visible to the model. If your file already contains both shapes, the change is refused rather than resolved for you.</p>
<h2>What is tested</h2><p>OpenCode 1.18.21 has been connected for real on a Mac with Apple Silicon: both shapes were written, applied again without duplicating, removed cleanly, and the two tools were discovered. It has not been run through a model turn, and there is no package to install it from yet.</p>
""",
    ),
    Page(
        route="/docs/integrations/generic-mcp/",
        title="Generic MCP integration",
        description="Read Kaleidoscope's launch descriptor and run it as one long-lived stdio MCP server from any standard client.",
        body="""
<p class="lede">Any standard MCP client can ask Kaleidoscope for its launch descriptor and keep one initialized session open for the whole run. You do not have to hand-write the command.</p>
<h2>Get the descriptor</h2><pre><code>kaleidoscope config --profile default --json</code></pre>
<p>What comes back is deliberately closed: an absolute command, <code>mcp --profile NAME</code>, <code>stdio</code>, exactly two tools, and an empty environment. Do not add your vault location or a token to it.</p>
<h2>Keep one session</h2><p>Initialize once, check that you see exactly <code>search</code> and <code>remember</code>, then reuse that session for the rest of the run. Starting a new process per tool call is slower and gains you nothing.</p>
<h2>What is tested</h2><p>The Python <code>mcp</code> client at 1.29.0 and 2.0.0, and the TypeScript <code>@modelcontextprotocol/client</code> at 2.0.0, have both driven this server on a Mac with Apple Silicon: one long-lived process, restart, shutdown, structured results, a malformed discovery response, and refusal of anything outside the two tools.</p>
""",
    ),
    Page(
        route="/docs/integrations/langchain/",
        title="LangChain integration",
        description="Use LangChain's MCP adapter to load Kaleidoscope's two tools into one session, without a second memory store.",
        body="""
<p class="lede">Use the official LangChain MCP adapter to load the two Kaleidoscope tools inside a single adapter session. Kaleidoscope is not a <code>BaseStore</code> implementation, and you should not wrap it as one.</p>
<h2>Lifecycle</h2><p>Open the stdio adapter once around the agent run you intend, load the two tools, then close the adapter when the run is over. Your model-provider credentials are supplied by your own application and never pass through Kaleidoscope.</p>
<h2>Boundary</h2><p>Do not add a parallel LangChain memory or summarize messages into a second store. If two things can answer “what do I know”, they will disagree. The MCP server stays the one owner.</p>
<h2>What is tested</h2><p>Tested with langchain 1.3.16 against a stand-in model, never against a live provider: what one step remembered, a later step found again through the same single process.</p>
""",
    ),
    Page(
        route="/docs/integrations/langgraph/",
        title="LangGraph integration",
        description="Put Kaleidoscope's two tools in a LangGraph tool node without turning it into a graph store.",
        body="""
<p class="lede">LangGraph uses the same one-session MCP adapter as LangChain, placed in your graph’s tool node for the length of the run.</p>
<h2>Boundary</h2><p>Kaleidoscope is not a LangGraph checkpointer and not a <code>BaseStore</code>. Keep graph state and durable memory separate, so you never end up with two things that both claim to be the record.</p>
<h2>Lifecycle</h2><p>Open the adapter before you execute the graph, pass the two tools into the tool node, and close it once execution finishes. The same session is reused across node calls.</p>
<h2>What is tested</h2><p>Tested with langgraph 1.2.11 against a stand-in model, never against a live provider: a tool node wrote a memory and then found it again through the same process.</p>
""",
    ),
    Page(
        route="/docs/integrations/openai-agents-sdk/",
        title="OpenAI Agents SDK integration",
        description="Attach Kaleidoscope to an OpenAI Agents SDK run as one long-lived stdio MCP server with two tools.",
        body="""
<p class="lede">Use the stdio MCP server lifecycle the OpenAI Agents SDK already gives you. Keep one server alive for the agent run, and filter the model-facing tools down to Kaleidoscope’s two.</p>
<h2>Tool boundary</h2><p>Your agent may call <code>search</code> and <code>remember</code>. Nothing else is ever exposed to a model — the operator commands are yours, from the terminal. Provider credentials come from your application and are never placed in the Kaleidoscope descriptor.</p>
<h2>Lifecycle</h2><p>Create the MCP server as a managed resource around the run and close it deterministically at the end. Do not open a fresh engine process for every tool call.</p>
<h2>What is tested</h2><p>Tested with the Python 0.22.0 and TypeScript 0.17.0 SDKs against a scripted model, never against a live provider: one server stayed alive for the whole run.</p>
""",
    ),
    Page(
        route="/docs/integrations/crewai/",
        title="CrewAI integration",
        description="Run Kaleidoscope as one persistent MCP adapter context for a CrewAI crew, exposing only two tools.",
        body="""
<p class="lede">CrewAI uses one stdio MCP adapter context for the whole crew run, and exposes only the Kaleidoscope tools you choose to give the model.</p>
<h2>Lifecycle</h2><p>Build the adapter from the descriptor <code>kaleidoscope config --profile default --json</code> gives you, enter it once, select <code>search</code> and <code>remember</code>, run the crew, then close the context. Do not recreate the server for each task.</p>
<h2>Boundary</h2><p>CrewAI owns your provider configuration and your crew state. Kaleidoscope owns only the local memory, and never receives a model-provider credential or an account token.</p>
<h2>What is tested</h2><p>Tested with crewai 1.15.17 against a local test server, never against a live model provider: one long-lived process for the crew run, with only the two tools exposed.</p>
""",
    ),
)


LEGAL_PAGES = (
    Page(
        route="/docs/legal/",
        title="Licenses and product terms",
        description="Kaleidoscope public software and documentation licenses, proprietary engine EULA, privacy notice, security policy, and support policy.",
        notice="legal-index",
        body="""
<p class="lede">The public software, original documentation, and proprietary
engine have deliberately separate license boundaries. Two of them are settled;
the rest are drafts.</p>
<h2>Authorized public licenses</h2>
<ul class="rows">
<li><span class="k">Apache-2.0 <span class="chip is-authorized">In force</span></span><span class="v">Covers the public manager, SDKs, wrappers, integrations, and skill, and is carried in those source and package repositories. It does not license the native engine, model weights, trademarks, or third-party material.</span></li>
<li><span class="k">CC BY 4.0 <span class="chip is-authorized">In force</span></span><span class="v">Covers original documentation. Read the <a href="/documentation-license.txt">documentation license scope</a> and the <a href="/legal/CC-BY-4.0.txt">CC BY 4.0 legal code</a>.</span></li>
</ul>
<h2>Product terms — review drafts</h2>
<table><thead><tr><th>Document</th><th>Status</th><th>Plain text</th></tr></thead><tbody>
<tr><td><a href="/docs/legal/engine-eula/">Proprietary engine EULA</a></td><td><span class="chip is-draft">Review draft</span></td><td><a href="/legal/ENGINE-EULA.txt"><code>ENGINE-EULA.txt</code></a></td></tr>
<tr><td><a href="/docs/legal/privacy-notice/">Privacy notice</a></td><td><span class="chip is-draft">Review draft</span></td><td><a href="/legal/PRIVACY-NOTICE.txt"><code>PRIVACY-NOTICE.txt</code></a></td></tr>
<tr><td><a href="/docs/legal/security-policy/">Security policy</a></td><td><span class="chip is-draft">Review draft</span></td><td><a href="/legal/SECURITY-POLICY.txt"><code>SECURITY-POLICY.txt</code></a></td></tr>
<tr><td><a href="/docs/legal/support-policy/">Support policy</a></td><td><span class="chip is-draft">Review draft</span></td><td><a href="/legal/SUPPORT-POLICY.txt"><code>SUPPORT-POLICY.txt</code></a></td></tr>
</tbody></table>
<h2>What is still outstanding</h2>
<ul class="rows">
<li><span class="k">Production entity</span><span class="v">The contracting entity named in the drafts is a placeholder and has not been settled.</span></li>
<li><span class="k">Jurisdiction</span><span class="v">Governing law and venue are unresolved, so no dispute clause in the drafts is operative.</span></li>
<li><span class="k">Contacts</span><span class="v">No monitored legal, privacy, or security intake address is published; the addresses in the drafts do not accept mail.</span></li>
<li><span class="k">Commitments</span><span class="v">Support scope, severity definitions, and response targets are proposals, not obligations, and no service level exists.</span></li>
<li><span class="k">External legal review</span><span class="v">No counsel has reviewed any of these documents. This is the gate that keeps every draft above out of force.</span></li>
</ul>
""",
    ),
    Page(
        route="/docs/legal/engine-eula/",
        title="Proprietary engine EULA (review draft)",
        description="Review draft of the Kaleidoscope proprietary native engine object-code end user license agreement.",
        noindex=True,
        notice="legal-draft",
        body=legal_document_body(
            "ENGINE-EULA.txt",
            "Terms proposed for proprietary Kaleidoscope engine object code; public Apache-2.0 components and CC BY 4.0 documentation remain separate.",
        ),
    ),
    Page(
        route="/docs/legal/privacy-notice/",
        title="Privacy notice (review draft)",
        description="Review draft of the Kaleidoscope local-product privacy notice and local-memory/account data boundary.",
        noindex=True,
        notice="legal-draft",
        body=legal_document_body(
            "PRIVACY-NOTICE.txt",
            "The local engine does not imply memory upload; optional account, site, purchase, and support processing require explicit production disclosures.",
        ),
    ),
    Page(
        route="/docs/legal/security-policy/",
        title="Security policy (review draft)",
        description="Review draft of supported-version, vulnerability reporting, safe-harbor, and incident communication terms.",
        noindex=True,
        notice="legal-draft",
        body=legal_document_body(
            "SECURITY-POLICY.txt",
            "A proposed coordinated-disclosure policy; no production intake exists until a monitored private channel and supported-version table are published.",
        ),
    ),
    Page(
        route="/docs/legal/support-policy/",
        title="Support policy (review draft)",
        description="Review draft of Kaleidoscope standard product support scope, exclusions, severity guidance, and response targets.",
        noindex=True,
        notice="legal-draft",
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
<p class="lede">Hosted memory does not exist. There is no service, no endpoint, no API and no waitlist. This page exists only so that the answer is written down somewhere.</p>
<h2>Where your memory is today</h2><p>Kaleidoscope keeps your memory in a vault on your own machine, and that vault is the only copy. Nothing uploads it, nothing syncs it, and signing in — which does not work yet either — would not change that. See <a href="/docs/privacy/">Privacy</a> for exactly what is and is not excluded from the account protocol.</p>
<h2>If that ever changes</h2><p>A hosted service would be a separate product with its own terms, and you would have to choose it deliberately. It is not something a local profile or a sign-in would quietly opt you into. Nothing on this site should be read as a promise that it is coming.</p>
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


def load_metadata(path: Path | None, mode: str = "staging") -> dict[str, str]:
    if mode not in {"staging", "public_docs", "production"}:
        raise ValueError(f"unknown documentation build mode: {mode}")
    if path is None:
        if mode != "staging":
            raise SystemExit(f"{mode} build requires --release-metadata")
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
    if mode != "staging":
        allowed_availability = (
            {"documentation_preview"}
            if mode == "public_docs"
            else {"release_candidate", "released"}
        )
        if data["availability"] not in allowed_availability:
            raise SystemExit(
                f"{mode} build has an invalid availability value"
            )
        if data["release_version"] in {"", "unreleased", "latest"}:
            raise SystemExit(f"{mode} build requires an immutable release version")
        if not HEX64.fullmatch(data["public_contract_sha256"]):
            raise SystemExit(
                f"{mode} build requires a lowercase 64-hex public contract digest"
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
            parent = parent_route(page.route)
            if parent:
                crumbs.append(
                    {
                        "@type": "ListItem",
                        "position": len(crumbs) + 1,
                        "name": NAV_LABELS[parent],
                        "item": f"{DOMAIN}{parent}",
                    }
                )
            crumbs.append(
                {
                    "@type": "ListItem",
                    "position": len(crumbs) + 1,
                    "name": page.title,
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
    indexable: bool,
    page: Page | None,
    *,
    noindex: bool = False,
) -> str:
    robots = "index,follow" if indexable and not noindex else "noindex,nofollow"
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
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta name="theme-color" content="#0B0B0C">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/site.css">
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


BRAND_MARK = (
    '<svg viewBox="0 0 64 64" width="18" height="18" aria-hidden="true">'
    '<g fill="currentColor">'
    '<rect x="4" y="16" width="28" height="7"/>'
    '<rect x="4" y="16" width="28" height="7" transform="rotate(90 32 32)" opacity="0.78"/>'
    '<rect x="4" y="16" width="28" height="7" transform="rotate(180 32 32)" opacity="0.56"/>'
    '<rect x="4" y="16" width="28" height="7" transform="rotate(270 32 32)" opacity="0.34"/>'
    '<rect x="28.5" y="28.5" width="7" height="7"/>'
    '</g></svg>'
)


def header(current: str, metadata: dict[str, str]) -> str:
    return f"""<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell">
  <a class="brand" href="/">{BRAND_MARK}<span class="wordmark">Kaleidoscope</span></a>
  <nav class="site-nav" aria-label="Primary">
    {nav_link("/docs/", "Docs", current)}
    {nav_link("/docs/integrations/", "Integrations", current)}
    {nav_link("/docs/security/", "Security", current)}
    {nav_link("/docs/status/", "Status", current)}
    <a href="https://github.com/kleos-research">GitHub</a>
  </nav>
</div></header>
<div class="strip"><div class="shell">
  <span class="dot" aria-hidden="true"></span>
  <span class="t">In development</span>
  <span class="d">Kaleidoscope is not publicly released. Nothing here installs from a registry yet — <a href="/docs/status/">see what has been verified locally</a>.</span>
</div></div>"""


def footer() -> str:
    return """<footer class="site-footer"><div class="shell">
  <span>Kaleidoscope by <a href="https://kleosresearch.xyz/">Kleos Research</a></span>
  <nav aria-label="Footer"><a href="/docs/legal/">Licenses &amp; terms</a><a href="/docs/legal/privacy-notice/">Privacy notice (draft)</a><a href="/docs/legal/security-policy/">Security policy (draft)</a><a href="/docs/legal/support-policy/">Support (draft)</a><a href="/docs/status/">What works today</a><a href="/llms.txt">llms.txt</a></nav>
</div></footer></body></html>"""


def render_home(metadata: dict[str, str], indexable: bool) -> str:
    description = "Local memory for AI agents. Your memory stays in a vault on your machine, and every editor or agent you connect shares one profile through exactly two tools."
    return (
        head("Kaleidoscope", description, f"{DOMAIN}/", indexable, None)
        + header("/", metadata)
        + """
<main id="main">
  <section class="hero shell">
    <p class="eyebrow mono">Local memory for agents</p>
    <h1>Carry the work forward.</h1>
    <p class="sub">one memory · every tool · on your machine</p>
    <p class="lede">Kaleidoscope gives your agents one memory on your machine that every editor and agent you connect shares. The engine that stores and ranks it runs locally; the <code>kaleidoscope</code> command wires it into your editor or agent, which sees exactly two tools: <code>search</code> and <code>remember</code>. Kaleidoscope is not released, and there is nothing you can install today.</p>
    <div class="actions"><a class="button" href="/docs/getting-started/">Get started</a><a class="button secondary" href="/docs/status/">What works today</a></div>
  </section>
  <section class="shell band">
    <p class="eyebrow mono">Principles</p>
    <h2>Three properties, not three features.</h2>
    <div class="cards">
      <article><h3>Local by construction</h3><p>Your memory lives in a vault on your machine. The engine needs no network and makes no external model calls, and memory content, queries, results, identifiers, and vault paths are never account data.</p><p class="s">On your machine</p></article>
      <article><h3>Works with your tools</h3><p>Codex, Claude Code, Cursor, OpenCode, and agent frameworks all read the same profile. They do not become separate memory stores merely because their configuration formats differ.</p><p class="s">One profile</p></article>
      <article><h3>Open around a closed core</h3><p>The engine that stores and ranks your memory is proprietary object code. Everything around it is Apache-2.0: the CLI, both SDKs, every integration, and the agent skill.</p><p class="s">Apache-2.0 around it</p></article>
    </div>
  </section>
  <section class="shell hero"><p class="eyebrow mono">Developer contract</p><h2>Two tools, one long-lived process.</h2><p class="lede">Your agent gets <code>search</code>, which brings back what you stored, ranked or by identifier, and <code>remember</code>, which writes exactly what you tell it to write. Every host runs one long-lived process, and no operator command ever enters a model’s tool list.</p></section>
</main>"""
        + footer()
    )


def sidebar_html(current: str) -> str:
    groups = []
    for section, entries in DOC_SECTIONS:
        items = "".join(
            f"<li>{nav_link(route, label, current)}</li>"
            for route, label, _blurb in entries
        )
        groups.append(
            f'<div class="group"><strong class="mono">{html.escape(section)}</strong>'
            f"<ul>{items}</ul></div>"
        )
    return (
        '<nav class="sidebar" aria-label="Documentation">'
        + "".join(groups)
        + "</nav>"
    )


def crumbs_html(page: Page) -> str:
    separator = '<span aria-hidden="true">/</span>'
    parts = ['<a href="/">Kaleidoscope</a>']
    if page.route == "/docs/":
        parts.append('<span aria-current="page">Docs</span>')
    else:
        parts.append('<a href="/docs/">Docs</a>')
        parent = parent_route(page.route)
        if parent:
            parts.append(
                f'<a href="{parent}">{html.escape(NAV_LABELS[parent])}</a>'
            )
        elif page.route in SECTION_CRUMB_ROUTES:
            parts.append(
                f'<span class="group">{html.escape(section_of(page.route))}</span>'
            )
        parts.append(
            f'<span aria-current="page">{html.escape(page.title)}</span>'
        )
    return (
        '<nav class="crumbs" aria-label="Breadcrumb">'
        + separator.join(parts)
        + "</nav>"
    )


def render_docs_index(page: Page, metadata: dict[str, str], indexable: bool) -> str:
    canonical = f"{DOMAIN}{page.route}"
    return (
        head(
            page.title,
            page.description,
            canonical,
            indexable,
            page,
            noindex=page.noindex,
        )
        + header(page.route, metadata)
        + f"""
<main id="main" class="shell docs-index">
  {crumbs_html(page)}
  <div class="masthead">
    <p class="eyebrow mono">Documentation</p>
    <h1>{html.escape(page.title)}</h1>
    <p class="sub">Local memory for agents · CLI and stdio MCP · macOS on Apple Silicon</p>
  </div>{page.body}
</main>"""
        + footer()
    )


def render_page(page: Page, metadata: dict[str, str], indexable: bool) -> str:
    if page.route == "/docs/":
        return render_docs_index(page, metadata, indexable)
    canonical = f"{DOMAIN}{page.route}"
    body, toc = annotate_body(page.body)
    notice = draft_notice_html(page)
    return (
        head(
            page.title,
            page.description,
            canonical,
            indexable,
            page,
            noindex=page.noindex,
        )
        + header(page.route, metadata)
        + f"""
<main id="main">{notice}
  <div class="shell layout">
    {sidebar_html(page.route)}
    <article class="content">{crumbs_html(page)}<h1>{html.escape(page.title)}</h1>{toc}{body}</article>
  </div>
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


def build(output: Path, metadata: dict[str, str], mode: str = "staging") -> None:
    if mode not in {"staging", "public_docs", "production"}:
        raise ValueError(f"unknown documentation build mode: {mode}")
    indexable = mode in {"public_docs", "production"}
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
    write_text(route_path(output, "/"), render_home(metadata, indexable))
    for page in PAGES:
        write_text(
            route_path(output, page.route), render_page(page, metadata, indexable)
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
        + """<main id="main" class="shell hero"><p class="eyebrow mono">404</p><h1>That page doesn’t exist.</h1><p class="lede">Try the documentation index or the getting-started guide instead.</p><div class="actions"><a class="button" href="/docs/">Documentation</a><a class="button secondary" href="/docs/getting-started/">Getting started</a></div></main>"""
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
        if indexable
        else "User-agent: *\nDisallow: /"
    )
    write_text(output / "robots.txt", robots)

    security_heading = (
        "# LOCAL BUILD ONLY — no production security intake is published."
        if mode == "staging"
        else "# DOCUMENTATION PREVIEW — no production security intake is published."
        if mode == "public_docs"
        else "# No production security intake is published."
    )
    security = f"""{security_heading}
Contact: {DOMAIN}/docs/security/
Canonical: {DOMAIN}/.well-known/security.txt
Expires: 2026-09-30T23:59:59Z
Preferred-Languages: en
Policy: {DOMAIN}/docs/security/
"""
    write_text(output / ".well-known" / "security.txt", security)

    llms = f"""# Kaleidoscope

> Local native memory for agents. Your memory lives in a vault on your machine, and every editor or agent you connect shares one profile through a command-line tool and a long-lived stdio MCP server. Kaleidoscope is not released: nothing installs from a registry, and signing in does not work.

- [Documentation]({DOMAIN}/docs/): what Kaleidoscope is, and which page answers your question
- [Getting started]({DOMAIN}/docs/getting-started/): the five commands you will run, in order
- [Install]({DOMAIN}/docs/packages/): the two package names, what is inside them, and why you cannot install them yet
- [CLI reference]({DOMAIN}/docs/cli/): every `kaleidoscope` command and flag
- [MCP reference]({DOMAIN}/docs/mcp/): the two tools an agent sees, `search` and `remember`, and how to call them
- [Integrations]({DOMAIN}/docs/integrations/): Codex, Claude Code, Cursor, OpenCode, LangChain, LangGraph, Claude Agent SDK, OpenAI Agents SDK, CrewAI, and any standard MCP client
- [Security]({DOMAIN}/docs/security/): what is isolated from what, what is not signed, and how to report a vulnerability
- [Privacy]({DOMAIN}/docs/privacy/): what stays on your machine, how credentials are stored, and what this website itself does
- [Licenses and terms]({DOMAIN}/docs/legal/): Apache-2.0 and CC BY 4.0 are in force; the product terms are unreviewed drafts
- [Privacy notice]({DOMAIN}/docs/legal/privacy-notice/): an unreviewed draft of the production privacy terms, not in force
- [Security policy]({DOMAIN}/docs/legal/security-policy/): an unreviewed draft of the disclosure and supported-version policy, not in force
- [Support policy]({DOMAIN}/docs/legal/support-policy/): an unreviewed draft of the support scope and response targets, not in force
- [Account]({DOMAIN}/docs/account/): you do not need an account, and you cannot create one yet
- [Operations]({DOMAIN}/docs/operations/): back up your memory, move it, uninstall, and delete a vault safely
- [Platform support]({DOMAIN}/docs/compatibility/): which machines this has been run on, and which have only had a compiler check
- [Benchmarks]({DOMAIN}/docs/benchmarks/): why no score is published, and what would have to be true first
- [What works today]({DOMAIN}/docs/status/): the platforms and editors that have actually been run, and what never has
- [Public agent skill]({DOMAIN}/SKILL.md): how an agent should retrieve and write memory
- [Agent instructions]({DOMAIN}/agent-instructions.md): the short pointers Kaleidoscope installs into AGENTS.md, CLAUDE.md, or a Cursor rule
- [Status record]({DOMAIN}/status.json): the same status these pages state, in machine-readable form
- [Platform support record]({DOMAIN}/platform-support.json): which platforms have been run on and which have only had a compiler check
- [Full CLI help text]({DOMAIN}/reference/kaleidoscope-cli.txt): the complete `kaleidoscope` help output
- [Tool reference]({DOMAIN}/reference/kaleidoscope-mcp.json): the fields of the two tools an agent sees

Kaleidoscope has only ever been run on one kind of machine: a Mac with Apple Silicon. On that machine you can run a build you already have, connect Claude Code, Codex, OpenCode, Cursor, a standard MCP client or an agent framework to it, and have them all share one local memory. You cannot install it from npm or PyPI, because neither package is published; you cannot download a build for any platform; and you cannot sign in, because no sign-in service is configured and every account command answers `provider not configured`. macOS on Intel, Linux on x86_64 and arm64, and Windows on x86_64 have had a compiler check for the memory engine and nothing more — nothing was ever assembled into a program for them and nothing has been run there. Windows on arm64 has not had even that. Three connections carry a limit: Codex's configuration entry is written, read back and removed exactly, but Codex offers no way to confirm it then starts the server; Cursor's configuration and project rule are written and removed exactly, but Cursor has never been launched against them; and the agent frameworks were run against stand-in models rather than a live provider. Nothing has been driven through an editor's graphical interface. Nothing is signed for release. Apache-2.0 covers the public code and CC BY 4.0 covers this documentation, and both are in force; the product terms — the engine licence, the privacy notice, the security policy and the support policy — are unreviewed drafts that no counsel has read, and none of them is in force. There is no support commitment and no published security contact yet. Hosted memory does not exist: there is no service, endpoint, API or waitlist, and nothing syncs your memory anywhere. No benchmark score is published, and nothing here claims anything about retrieval quality or speed. The memory engine ships as proprietary object code, and its source is not in any public surface.
"""
    write_text(output / "llms.txt", llms)

    chunks = [llms.strip()]
    for page in PAGES:
        if page.noindex:
            continue
        release_line = (
            f"Release: {metadata['release_version']}\n" if page.release_bound else ""
        )
        chunks.append(
            f"# {page.title}\n\nURL: {DOMAIN}{page.route}\n{release_line}Updated: {metadata['updated_at']}\n\n{plain_text(draft_notice_html(page) + page.body)}"
        )
    chunks.extend(
        [
            f"# Public agent skill\n\nURL: {DOMAIN}/SKILL.md\n\n{PUBLIC_FILES['SKILL.md'].read_text(encoding='utf-8').strip()}",
            f"# Full CLI help text\n\nURL: {DOMAIN}/reference/kaleidoscope-cli.txt\n\n{MANAGER_HELP.strip()}",
            f"# Tool reference\n\nURL: {DOMAIN}/reference/kaleidoscope-mcp.json\n\n{json.dumps(MCP_REFERENCE, indent=2, sort_keys=True)}",
            f"# Status record\n\nURL: {DOMAIN}/status.json\n\n{json.dumps(STATUS_RECORD, indent=2, sort_keys=True)}",
            f"# Platform support record\n\nURL: {DOMAIN}/platform-support.json\n\n{json.dumps(PLATFORM_SUPPORT, indent=2, sort_keys=True)}",
        ]
    )
    write_text(output / "llms-full.txt", "\n\n---\n\n".join(chunks))

    write_text(
        output / "status.json",
        json.dumps(STATUS_RECORD, indent=2, sort_keys=True),
    )
    write_text(
        output / "platform-support.json",
        json.dumps(PLATFORM_SUPPORT, indent=2, sort_keys=True),
    )
    write_text(output / "reference" / "kaleidoscope-cli.txt", MANAGER_HELP)
    write_text(
        output / "reference" / "kaleidoscope-mcp.json",
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
        "mode": mode,
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--production", action="store_true")
    mode.add_argument("--public-docs", action="store_true")
    args = parser.parse_args()
    build_mode = (
        "production"
        if args.production
        else "public_docs"
        if args.public_docs
        else "staging"
    )
    metadata = load_metadata(args.release_metadata, build_mode)
    build(args.output.expanduser().absolute(), metadata, build_mode)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify a generated Kaleidoscope documentation artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

DOMAIN = "https://memory.kleosresearch.xyz"
SOCIAL_IMAGE = f"{DOMAIN}/assets/kaleidoscope-og.png"
# The social card is the product's identity on every share surface, and a PNG
# magic-byte test cannot see that it is the wrong drawing in the wrong colour.
# Pin the composed brand card itself: ink ground, the real swept mark in brass,
# the wordmark in Newsreader. Regenerate the card, then update this digest.
SOCIAL_IMAGE_SHA256 = (
    "d84723af1329236dc663243909771784a4a056a6359f1f0cbd3243390c27ebf5"
)
EXPECTED_CNAME = "memory.kleosresearch.xyz"
PUBLIC_SKILL_SHA256 = (
    "c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad"
)
PRIVATE_MARKERS = (
    "/Users/",
    "\\Users\\",
    ".codex/worktrees",
    ".claude/worktrees",
    'github.com/kleos-research/kaleidoscope"',
    "KSCOPE_ROOT",
    "KSCOPE_WORKSPACE",
    "KSCOPE_PRINCIPAL",
    "KSCOPE_JOURNAL",
)
LEGACY_TOOLS = ("compile", "recall", "read_memory", "ingest_memory")
# Words that state our internal release process instead of what a reader can
# and cannot do. Every one of them was published on this site at least once,
# and the owner rejected the copy that carried them. The scan runs over the
# whole lowercased text of every published file, so it also sees class names,
# JSON keys, SVG ids and aria labels, and "-" is a word boundary.
BANNED_VOCABULARY = (
    r"dx-\d",
    r"facades?",
    r"harnesse?s?",
    r"conformance",
    r"signature_verified",
    r"milestones",
    r"\bslices?\b",
    r"\bsmoke\b",
    r"\blanes?\b",
    r"\bstaging\b",
    r"\bcandidates?\b",
    r"\bpromotion\b",
    r"\bcanary\b",
    r"\bexercised\b",
    # A commit or a build digest is our coordinate, not the reader's. Twelve
    # characters is the shortest form that was ever published in prose.
    r"\b[0-9a-f]{12,}\b",
)
# Files the site republishes verbatim rather than writes. The four product
# terms are unreviewed draft source under a mandatory not-in-force notice, and
# SKILL.md is the agent skill exactly as the product installs it — its
# "candidates" and "milestone" are ordinary English about memories, not about
# this release. Editing either from this repository would make the published
# copy differ from the source it claims to reproduce byte for byte.
VOCABULARY_EXEMPT = {
    "SKILL.md",
    "legal/ENGINE-EULA.txt",
    "legal/PRIVACY-NOTICE.txt",
    "legal/SECURITY-POLICY.txt",
    "legal/SUPPORT-POLICY.txt",
    "docs/legal/engine-eula/index.html",
    "docs/legal/privacy-notice/index.html",
    "docs/legal/security-policy/index.html",
    "docs/legal/support-policy/index.html",
    # every file digest in the build manifest is a 64-character hex string
    "site-manifest.json",
}
# llms-full.txt inlines the exempt skill; scan the chunks the site wrote.
VOCABULARY_EXEMPT_CHUNKS = ("# Public agent skill",)
PRODUCTION_BLOCKERS = (
    "unreleased",
    "not-yet-bound",
    "under conformance",
    "not released",
    "staging candidate",
    "not installable yet",
    "generation pending release binding",
    "no support claim yet",
    "will be published here",
    "local staging",
    "local-only",
    "test-only",
    "not public",
    "unapproved",
    "provider not configured",
    "production login remains disabled",
    "review draft",
    "not for production",
    "not live-host accepted",
    "verified local, unpublished",
    "verified without live provider",
    "no package or production login is public",
)

EXPECTED_HTML = {
    "404.html",
    "index.html",
    "docs/index.html",
    "docs/getting-started/index.html",
    "docs/packages/index.html",
    "docs/concepts/index.html",
    "docs/cli/index.html",
    "docs/mcp/index.html",
    "docs/integrations/index.html",
    "docs/integrations/codex/index.html",
    "docs/integrations/claude-code/index.html",
    "docs/integrations/claude-agent-sdk/index.html",
    "docs/integrations/cursor/index.html",
    "docs/integrations/opencode/index.html",
    "docs/integrations/generic-mcp/index.html",
    "docs/integrations/langchain/index.html",
    "docs/integrations/langgraph/index.html",
    "docs/integrations/openai-agents-sdk/index.html",
    "docs/integrations/crewai/index.html",
    "docs/operations/index.html",
    "docs/security/index.html",
    "docs/privacy/index.html",
    "docs/account/index.html",
    "docs/compatibility/index.html",
    "docs/benchmarks/index.html",
    "docs/status/index.html",
    "docs/release-notes/index.html",
    "docs/troubleshooting/index.html",
    "docs/hosted/index.html",
    "docs/legal/index.html",
    "docs/legal/engine-eula/index.html",
    "docs/legal/privacy-notice/index.html",
    "docs/legal/security-policy/index.html",
    "docs/legal/support-policy/index.html",
}
NOINDEX_HTML = {
    "404.html",
    "docs/hosted/index.html",
    "docs/legal/engine-eula/index.html",
    "docs/legal/privacy-notice/index.html",
    "docs/legal/security-policy/index.html",
    "docs/legal/support-policy/index.html",
}
# Routes where a developer has asked for technical provenance. Global chrome
# must not carry a release version, availability value, or contract digest.
PROVENANCE_ROUTES = {
    "docs/status/index.html",
    "docs/packages/index.html",
    "docs/release-notes/index.html",
    "docs/mcp/index.html",
    "docs/getting-started/index.html",
    "docs/benchmarks/index.html",
}
LEGAL_DRAFT_ROUTES = {
    "docs/legal/index.html",
    "docs/legal/engine-eula/index.html",
    "docs/legal/privacy-notice/index.html",
    "docs/legal/security-policy/index.html",
    "docs/legal/support-policy/index.html",
}
# "has not" on a document page, "have not" on the section index — match both.
LEGAL_DRAFT_SENTINELS = ("not been reviewed by legal counsel", "not in force")
LEGAL_OVERCLAIMS = (
    "reviewed by counsel",
    "legally binding",
    "counsel-approved",
    "legally effective",
    # the affirmative that mirrors the sentinel: a page may carry the sentinel
    # and this at the same time, and neither of the other checks would speak.
    "has been reviewed by legal counsel",
    "have been reviewed by legal counsel",
    "reviewed by outside counsel",
    "counsel-reviewed",
    "approved by counsel",
)
# kaleidoscope-dark, brand/tokens/tokens.json.
REQUIRED_TOKENS = ("#0B0B0C", "#131315", "#232325", "#8C887F", "#EAE7E0", "#CFA757")
# Values that must not reappear: the five drifted ones from the rejected design,
# plus #605D57, which was a rebuild extension token used for real text at
# 9.5-12px and measures 3.00:1 on --bg and 2.83:1 on --raised.
DRIFTED_TOKENS = (
    "#2c2c30",
    "#ece8df",
    "#918b80",
    "#d2aa5b",
    "#e0be7b",
    "#9bc6a4",
    "#605d57",
)
class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.h1_count = 0
        self.headings: list[int] = []
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.descriptions: list[str] = []
        self.meta: dict[str, list[str]] = {}
        self.structured_data: list[str] = []
        self._structured_buffer: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag in {"img", "script", "link"} and values.get("src"):
            self.links.append(values["src"] or "")
        if tag == "link" and values.get("href"):
            self.links.append(values["href"] or "")
            if values.get("rel") == "canonical":
                self.canonicals.append(values["href"] or "")
        if tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta.setdefault(key, []).append(values.get("content") or "")
            if values.get("name") == "robots":
                self.robots.append(values.get("content") or "")
            if values.get("name") == "description":
                self.descriptions.append(values.get("content") or "")
        if tag == "script" and values.get("type") == "application/ld+json":
            self._structured_buffer = []
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(int(tag[1]))
            if tag == "h1":
                self.h1_count += 1

    def handle_data(self, data: str) -> None:
        if self._structured_buffer is not None:
            self._structured_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._structured_buffer is not None:
            self.structured_data.append("".join(self._structured_buffer))
            self._structured_buffer = None


def local_target(root: Path, link: str) -> Path | None:
    parsed = urlparse(link)
    if parsed.scheme or parsed.netloc or link.startswith(("mailto:", "#")):
        return None
    path = parsed.path
    if not path.startswith("/"):
        return None
    if path == "/":
        return root / "index.html"
    candidate = root / path.lstrip("/")
    if path.endswith("/"):
        return candidate / "index.html"
    return candidate


def verify(root: Path, expected_mode: str) -> list[str]:
    failures: list[str] = []
    manifest_path = root / "site-manifest.json"
    if not manifest_path.is_file():
        return ["missing site-manifest.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "kaleidoscope.docs-artifact.v1":
        failures.append("wrong manifest schema")
    if manifest.get("mode") != expected_mode:
        failures.append(
            f"manifest mode is {manifest.get('mode')!r}, expected {expected_mode!r}"
        )

    cname_path = root / "CNAME"
    if not cname_path.is_file():
        failures.append("missing CNAME")
    elif cname_path.read_text(encoding="utf-8").strip() != EXPECTED_CNAME:
        failures.append("CNAME does not match the canonical documentation domain")

    social_image = root / "assets" / "kaleidoscope-og.png"
    if not social_image.is_file():
        failures.append("missing or invalid Kaleidoscope social image")
    else:
        social_bytes = social_image.read_bytes()
        if not social_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            failures.append("missing or invalid Kaleidoscope social image")
        else:
            width, height = struct.unpack(">II", social_bytes[16:24])
            if (width, height) != (1200, 630):
                failures.append(
                    f"social image is {width}x{height}, expected 1200x630"
                )
            digest = hashlib.sha256(social_bytes).hexdigest()
            if digest != SOCIAL_IMAGE_SHA256:
                failures.append(
                    "social image is not the composed Kaleidoscope brand card "
                    f"(sha256 {digest}); it must carry the swept mark in brass "
                    "on ink, not a second palette or a substitute drawing"
                )

    declared = {entry["path"]: entry for entry in manifest.get("files", [])}
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if set(declared) != set(actual):
        failures.append(
            f"manifest inventory mismatch: declared-only={sorted(set(declared) - set(actual))}, actual-only={sorted(set(actual) - set(declared))}"
        )
    for relative, entry in declared.items():
        path = actual.get(relative)
        if path is None:
            continue
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry.get("sha256"):
            failures.append(f"manifest digest mismatch: {relative}")
        if len(content) != entry.get("size_bytes"):
            failures.append(f"manifest size mismatch: {relative}")

    public_sources = manifest.get("public_source_sha256")
    if not isinstance(public_sources, dict) or not public_sources:
        failures.append("missing public source bindings")
    else:
        for relative, digest in public_sources.items():
            path = actual.get(relative)
            if path is None:
                failures.append(f"missing bound public source: {relative}")
            elif not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                failures.append(f"invalid public source digest: {relative}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append(f"public source binding mismatch: {relative}")
    skill_path = actual.get("SKILL.md")
    if skill_path is None:
        failures.append("missing canonical public skill")
    elif hashlib.sha256(skill_path.read_bytes()).hexdigest() != PUBLIC_SKILL_SHA256:
        failures.append("canonical public skill digest changed")

    status_path = actual.get("status.json")
    if status_path is None:
        failures.append("missing status.json")
    else:
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("status.json is not valid JSON")
        else:
            if status.get("schema_version") != "kaleidoscope.docs-status.v1":
                failures.append("status.json has the wrong schema")
            # Every one of these is a claim a reader would act on. A build that
            # flips one has said the product is available, and must not pass
            # until someone changes this file on purpose.
            for field in ("released", "publicly available"):
                if status.get(field) is not False:
                    failures.append(f"status.json must keep {field!r} false")
            packages = status.get("packages", {})
            for field in ("published to a registry", "signed for release"):
                if packages.get(field) is not False:
                    failures.append(f"status.json must keep packages {field!r} false")
            if packages.get("the platform package is built for") != [
                "macOS, Apple Silicon"
            ]:
                failures.append("status.json has the wrong built-for platform")
            licences = status.get("licences", {})
            if "not in force" not in licences.get("the product terms", ""):
                failures.append("status.json must keep the product terms not in force")
            if "no counsel has read them" not in licences.get("the product terms", ""):
                failures.append("status.json must say no counsel has read the drafts")
            holds = status.get("still true before any release", {})
            for field in (
                "packages published to a registry",
                "builds signed for release",
                "product terms reviewed by legal counsel",
                "sign-in service configured",
                "support offered",
                "security contact published",
                "any platform other than macOS on Apple Silicon verified",
                "any editor run against a live model provider",
                "benchmark score published",
                "hosted memory built",
            ):
                if holds.get(field) is not False:
                    failures.append(f"status.json must keep {field!r} false")
            hosts = {
                (host.get("name"), host.get("status"))
                for host in status.get("hosts", {}).get("hosts", [])
            }
            expected_hosts = {
                ("Codex", "partly tested"),
                ("Claude Code", "tested"),
                ("OpenCode", "tested"),
                ("Cursor", "partly tested"),
            }
            if hosts != expected_hosts:
                failures.append("status.json has the wrong host inventory")
            # A "partly tested" row that does not say which part is the exact
            # thing the status words were introduced to stop.
            for host in status.get("hosts", {}).get("hosts", []):
                if host.get("status") == "partly tested" and not host.get(
                    "not confirmed"
                ):
                    failures.append(
                        f"status.json marks {host.get('name')!r} partly tested without saying which part"
                    )
            if status.get("hosts", {}).get("tools_a_model_sees") != [
                "remember",
                "search",
            ]:
                failures.append("status.json exposes the wrong tools to a model")

    platform_path = actual.get("platform-support.json")
    if platform_path is None:
        failures.append("missing platform-support.json")
    else:
        try:
            platforms = json.loads(platform_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("platform-support.json is not valid JSON")
        else:
            if (
                platforms.get("schema_version")
                != "kaleidoscope.docs-platform-support.v1"
            ):
                failures.append("platform-support.json has the wrong schema")
            if platforms.get("run on") != ["macOS, Apple Silicon"]:
                failures.append("platform-support.json has the wrong run-on list")
            checked = platforms.get("compiler checked only", {})
            # The claim these four rows carry is a compiler check and nothing
            # more. Published once as "the code builds for this target", it read
            # as a working build for platforms nothing has ever been built for.
            meaning = checked.get("meaning", "")
            for phrase in (
                "The compiler accepts",
                "Nothing was ever assembled",
                "nothing has been run there",
            ):
                if phrase not in meaning:
                    failures.append(
                        f"platform-support.json must keep {phrase!r} in the compiler-check meaning"
                    )
            checked_platforms = {
                (row.get("platform"), row.get("architecture"), row.get("result"))
                for row in checked.get("platforms", [])
            }
            expected_checked = {
                ("macOS", "x86_64", "passed"),
                ("Linux", "x86_64", "passed"),
                ("Linux", "arm64", "passed"),
                ("Windows", "x86_64", "passed"),
            }
            if checked_platforms != expected_checked:
                failures.append("platform-support.json has the wrong checked inventory")
            if platforms.get("not checked at all") != [
                {"platform": "Windows", "architecture": "arm64"}
            ]:
                failures.append("platform-support.json has the wrong unchecked list")
            if not platforms.get("does not establish"):
                failures.append(
                    "platform-support.json must keep the limits of a compiler check"
                )

    cli_reference = actual.get("reference/kaleidoscope-cli.txt")
    if cli_reference is None:
        failures.append("missing CLI reference")
    else:
        cli_text = cli_reference.read_text(encoding="utf-8")
        for command in (
            "kaleidoscope [--engine PATH] init",
            "connect HOST",
            "disconnect HOST",
            "instructions install TARGET",
            "doctor",
        ):
            if command not in cli_text:
                failures.append(f"CLI reference missing {command!r}")

    mcp_reference = actual.get("reference/kaleidoscope-mcp.json")
    if mcp_reference is None:
        failures.append("missing MCP tool reference")
    else:
        try:
            mcp = json.loads(mcp_reference.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("MCP tool reference is not valid JSON")
        else:
            if mcp.get("schema_version") != "kaleidoscope.docs-mcp-reference.v2":
                failures.append("MCP tool reference has the wrong schema")
            if mcp.get("protocol_revision") != "2025-11-25":
                failures.append("MCP tool reference has the wrong protocol revision")
            tools = {tool.get("name") for tool in mcp.get("model_tools", [])}
            if tools != {"remember", "search"}:
                failures.append(
                    "MCP tool reference must expose exactly remember and search"
                )
            for tool in mcp.get("model_tools", []):
                if tool.get("name") == "remember" and tool.get(
                    "maximum_batch_items"
                ) != 20:
                    failures.append("MCP tool reference has the wrong batch bound")
                if tool.get("name") == "search" and tool.get("ledger_values") != [True]:
                    failures.append(
                        "MCP tool reference must keep ranked search ledgered"
                    )
            if mcp.get("operator_commands_are_model_tools") is not False:
                failures.append("MCP tool reference exposes operator commands")
            if mcp.get("release_readiness_claimed") is not False:
                failures.append("MCP tool reference claims release readiness")
            for field in ("released", "publicly available"):
                if mcp.get(field) is not False:
                    failures.append(f"MCP tool reference must keep {field!r} false")

    for relative, path in actual.items():
        if path.suffix not in {".html", ".txt", ".md", ".xml", ".json", ".css"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in PRIVATE_MARKERS:
            if marker in text:
                failures.append(f"private marker {marker!r} in {relative}")
        if relative not in VOCABULARY_EXEMPT:
            scanned = text
            if relative == "llms-full.txt":
                scanned = "\n\n---\n\n".join(
                    chunk
                    for chunk in text.split("\n\n---\n\n")
                    if not chunk.lstrip().startswith(VOCABULARY_EXEMPT_CHUNKS)
                )
            lowered_text = scanned.lower()
            for pattern in BANNED_VOCABULARY:
                found = re.search(pattern, lowered_text)
                if found:
                    failures.append(
                        f"internal vocabulary {found.group(0)!r} in {relative}"
                    )
        for placeholder in ("{FINAL_PACKAGE_EVIDENCE_SHA256", "{PLATFORM_HARNESS_COMMIT"):
            if placeholder in text:
                failures.append(f"unexpanded placeholder {placeholder!r} in {relative}")
        if expected_mode == "production":
            lowered = text.lower()
            for blocker in PRODUCTION_BLOCKERS:
                if blocker in lowered:
                    failures.append(f"production blocker {blocker!r} in {relative}")

    html_files = sorted(path for path in actual.values() if path.suffix == ".html")
    html_relatives = {path.relative_to(root).as_posix() for path in html_files}
    if html_relatives != EXPECTED_HTML:
        failures.append(
            f"HTML route inventory mismatch: expected-only={sorted(EXPECTED_HTML - html_relatives)}, actual-only={sorted(html_relatives - EXPECTED_HTML)}"
        )
    for path in html_files:
        relative = path.relative_to(root).as_posix()
        document = path.read_text(encoding="utf-8")
        parser = DocumentParser()
        parser.feed(document)
        if parser.h1_count != 1:
            failures.append(
                f"{relative}: expected exactly one h1, found {parser.h1_count}"
            )
        if parser.headings:
            if parser.headings[0] != 1:
                failures.append(
                    f"{relative}: the first heading is h{parser.headings[0]}, not h1"
                )
            for previous, level in zip(parser.headings, parser.headings[1:]):
                if level > previous + 1:
                    failures.append(
                        f"{relative}: heading order skips h{previous} -> h{level}"
                    )
                    break
        if len(parser.canonicals) != 1 or not parser.canonicals[0].startswith(
            f"{DOMAIN}/"
        ):
            failures.append(f"{relative}: missing or invalid canonical")
        expected_robots = (
            "index,follow"
            if expected_mode in {"public_docs", "production"}
            and relative not in NOINDEX_HTML
            else "noindex,nofollow"
        )
        if parser.robots != [expected_robots]:
            failures.append(
                f"{relative}: robots is {parser.robots!r}, expected {[expected_robots]!r}"
            )
        if len(parser.descriptions) != 1 or not parser.descriptions[0].strip():
            failures.append(f"{relative}: expected one non-empty meta description")
        for name, expected in (
            ("og:image", SOCIAL_IMAGE),
            ("og:image:width", "1200"),
            ("og:image:height", "630"),
            ("og:image:alt", "Kaleidoscope — local memory for agents"),
            ("twitter:card", "summary_large_image"),
            ("twitter:image", SOCIAL_IMAGE),
            ("twitter:image:alt", "Kaleidoscope — local memory for agents"),
        ):
            if parser.meta.get(name) != [expected]:
                failures.append(
                    f"{relative}: {name} is {parser.meta.get(name)!r}, expected {[expected]!r}"
                )
        if len(parser.structured_data) != 1:
            failures.append(
                f"{relative}: expected one JSON-LD block, found {len(parser.structured_data)}"
            )
        else:
            try:
                structured = json.loads(parser.structured_data[0])
            except json.JSONDecodeError:
                failures.append(f"{relative}: JSON-LD is invalid")
            else:
                if structured.get("@context") != "https://schema.org":
                    failures.append(f"{relative}: JSON-LD has wrong schema context")
                if relative.startswith("docs/"):
                    graph = structured.get("@graph")
                    if not isinstance(graph, list) or {
                        item.get("@type")
                        for item in graph
                        if isinstance(item, dict)
                    } != {"TechArticle", "BreadcrumbList"}:
                        failures.append(
                            f"{relative}: JSON-LD must contain TechArticle and BreadcrumbList"
                        )
        lowered = document.lower()
        for tool in LEGACY_TOOLS:
            if re.search(rf"\b{re.escape(tool)}\b", lowered):
                failures.append(f"retired tool name {tool!r} in {relative}")
        stylesheet = actual.get("assets/site.css")
        css_text = (
            stylesheet.read_text(encoding="utf-8") if stylesheet is not None else ""
        )
        if (
            "fonts.googleapis.com/css2" not in document
            and not ("@font-face" in css_text and "as=\"font\"" in document)
        ):
            failures.append(
                f"{relative}: no webfont is loaded; the type system falls back silently"
            )
        mark = re.search(r"<svg\b.*?</svg>", document, flags=re.S)
        if mark is None:
            failures.append(f"{relative}: the Kaleidoscope mark is missing")
        else:
            mark_text = mark.group(0)
            bars = mark_text.count('width="28" height="7"')
            if bars != 4:
                failures.append(
                    f"{relative}: the mark is one bar swept four times — "
                    f"found {bars} bars"
                )
            for angle in ("rotate(90 32 32)", "rotate(180 32 32)", "rotate(270 32 32)"):
                if angle not in mark_text:
                    failures.append(f"{relative}: the mark is missing {angle}")
            for step in ("0.78", "0.56", "0.34"):
                if f'opacity="{step}"' not in mark_text:
                    failures.append(
                        f"{relative}: the mark has no opacity cascade at {step} — "
                        "flat sweeps are prohibited"
                    )
            if 'x="28.5" y="28.5" width="7" height="7"' not in mark_text:
                failures.append(
                    f"{relative}: the inline mark has no centre square"
                )
            if "rx=" in mark_text or "ry=" in mark_text:
                failures.append(
                    f"{relative}: the mark has rounded corners — nothing in the "
                    "system is rounded except the app-icon tile"
                )
        for opening in re.findall(r"<pre\b[^>]*>", document):
            if "tabindex=" not in opening:
                failures.append(
                    f"{relative}: a <pre> scrolls horizontally with no tab stop — "
                    "its clipped content is unreachable by keyboard"
                )
                break
        for opening in re.findall(r'<div class="table-scroll"[^>]*>', document):
            if "tabindex=" not in opening:
                failures.append(
                    f"{relative}: a table scroll container has no tab stop"
                )
                break
        if '<link rel="icon" href="/favicon.ico"' not in document:
            failures.append(f"{relative}: favicon.ico is shipped but not linked")
        if expected_mode in {"public_docs", "production"} and relative not in PROVENANCE_ROUTES:
            release = manifest.get("release", {})
            for label, value in (
                ("availability", release.get("availability", "")),
                ("release version", release.get("release_version", "")),
                ("contract digest", release.get("public_contract_sha256", "")[:12]),
            ):
                if value and value in document:
                    failures.append(
                        f"{relative}: {label} {value!r} appears outside the provenance pages"
                    )
        if expected_mode in {"staging", "public_docs"}:
            lowered_document = document.lower()
            if relative in LEGAL_DRAFT_ROUTES:
                for sentinel in LEGAL_DRAFT_SENTINELS:
                    if sentinel not in lowered_document:
                        failures.append(
                            f"{relative}: review-draft boundary is missing {sentinel!r}"
                        )
                if 'class="draft-notice"' not in document:
                    failures.append(
                        f"{relative}: the review-draft notice component is absent"
                    )
                if 'class="notice-band"' not in document:
                    failures.append(
                        f"{relative}: the review-draft notice is not a page-level "
                        "band — inside the article it falls below the navigation "
                        "on a narrow viewport"
                    )
                elif document.index('class="notice-band"') > document.index(
                    'class="sidebar"'
                ):
                    failures.append(
                        f"{relative}: the review-draft band renders after the "
                        "documentation navigation"
                    )
            for overclaim in LEGAL_OVERCLAIMS:
                if overclaim in lowered_document:
                    failures.append(
                        f"{relative}: legal overclaim {overclaim!r} — nothing has had counsel review"
                    )
        for link in parser.links:
            target = local_target(root, link)
            if target is not None and not target.exists():
                failures.append(f"{relative}: broken internal link {link}")

    stylesheet = actual.get("assets/site.css")
    if stylesheet is None:
        failures.append("missing assets/site.css")
    else:
        css = stylesheet.read_text(encoding="utf-8")
        lowered_css = css.lower()
        for required in REQUIRED_TOKENS:
            if required.lower() not in lowered_css:
                failures.append(
                    f"assets/site.css: canonical kaleidoscope-dark token {required} is absent"
                )
        for drifted in DRIFTED_TOKENS:
            if drifted in lowered_css:
                failures.append(
                    f"assets/site.css: drifted token {drifted} — use the kaleidoscope-dark value"
                )
        rounded = [
            value
            for value in re.findall(r"border-radius\s*:\s*([^;}]+)", css)
            if value.strip().rstrip(";").strip() != "0"
        ]
        if rounded:
            failures.append(
                "assets/site.css: rounded corners "
                f"{rounded!r} — nothing in the system is rounded except the "
                "app-icon tile, which this stylesheet does not draw"
            )
        prose_code = re.search(
            r"\.content p code[^{]*\{([^}]*)\}", css, flags=re.S
        )
        if prose_code is None or "overflow-wrap" not in prose_code.group(1):
            failures.append(
                "assets/site.css: inline prose code has no overflow-wrap — a "
                "64-character digest then scrolls the whole page sideways"
            )

    robots = (root / "robots.txt").read_text(encoding="utf-8")
    if expected_mode in {"public_docs", "production"} and "Allow: /" not in robots:
        failures.append(f"{expected_mode} robots does not allow root")
    if expected_mode == "staging" and "Disallow: /" not in robots:
        failures.append("staging robots does not disallow root")

    try:
        sitemap = ElementTree.parse(root / "sitemap.xml")
    except ElementTree.ParseError:
        failures.append("sitemap.xml is invalid")
    else:
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = {
            element.text
            for element in sitemap.findall("s:url/s:loc", namespace)
            if element.text
        }
        expected_urls = {f"{DOMAIN}/"}
        expected_urls.update(
            f"{DOMAIN}/" + relative.removesuffix("index.html")
            for relative in EXPECTED_HTML - NOINDEX_HTML - {"index.html"}
        )
        if sitemap_urls != expected_urls:
            failures.append(
                f"sitemap URL inventory mismatch: expected-only={sorted(expected_urls - sitemap_urls)}, actual-only={sorted(sitemap_urls - expected_urls)}"
            )

    security = (root / ".well-known" / "security.txt").read_text(encoding="utf-8")
    if expected_mode == "staging" and "LOCAL BUILD ONLY" not in security:
        failures.append("staging security.txt is not marked as staging")
    if expected_mode == "public_docs" and "DOCUMENTATION PREVIEW" not in security:
        failures.append("public documentation security.txt is not marked as preview")
    if expected_mode == "production" and "LOCAL BUILD ONLY" in security:
        failures.append("production security.txt still carries the staging marker")

    llms = (root / "llms.txt").read_text(encoding="utf-8")
    llms_lower = llms.lower()
    # llms.txt is linked from the footer of every page, so it is reader-facing
    # copy and not a machine record. It used to close with a paragraph of
    # internal work-item identifiers and build digests; these are the honest
    # claims that replaced it, and each one is load-bearing.
    for required in (
        "local native",
        "`search` and `remember`",
        "proprietary object code",
        "kaleidoscope is not released",
        "neither package is published",
        "you cannot download a build for any platform",
        "provider not configured",
        "a compiler check for the memory engine and nothing more",
        "nothing is signed for release",
        "unreviewed drafts that no counsel has read",
        "hosted memory does not exist",
        "no benchmark score is published",
        "/docs/privacy/",
        "/docs/status/",
        "/skill.md",
        "/status.json",
        "/platform-support.json",
        "/reference/kaleidoscope-cli.txt",
        "/reference/kaleidoscope-mcp.json",
    ):
        if required.lower() not in llms_lower:
            failures.append(f"llms.txt missing {required!r}")

    llms_full = (root / "llms-full.txt").read_text(encoding="utf-8")
    for relative in sorted(EXPECTED_HTML - NOINDEX_HTML - {"index.html"}):
        route = "/" + relative.removesuffix("index.html")
        if f"URL: {DOMAIN}{route}" not in llms_full:
            failures.append(f"llms-full.txt missing canonical section for {route}")
    for required in (
        "# Public agent skill",
        "# Full CLI help text",
        "# Tool reference",
        "# Status record",
        "# Platform support record",
    ):
        if required not in llms_full:
            failures.append(f"llms-full.txt missing {required!r}")

    # The text mirror carries the same chrome the HTML does. Scanning only the
    # HTML let a per-page release tag survive here after it was removed there.
    provenance_paths = {
        "/" + relative.removesuffix("index.html") for relative in PROVENANCE_ROUTES
    }
    release = manifest.get("release", {})
    identifiers = [
        ("availability", release.get("availability", "")),
        ("release version", release.get("release_version", "")),
        ("contract digest", release.get("public_contract_sha256", "")[:12]),
    ]
    for chunk in llms_full.split("\n\n---\n\n"):
        url = re.search(rf"^URL: {re.escape(DOMAIN)}(\S*/)$", chunk, flags=re.M)
        if url is None:
            continue
        route = url.group(1)
        if expected_mode in {"public_docs", "production"} and (
            route not in provenance_paths
        ):
            for label, value in identifiers:
                if value and value in chunk:
                    failures.append(
                        f"llms-full.txt {route}: {label} {value!r} appears "
                        "outside the provenance pages"
                    )
        page_path = route.lstrip("/") + "index.html"
        if expected_mode in {"staging", "public_docs"} and (
            page_path in LEGAL_DRAFT_ROUTES
        ):
            for sentinel in LEGAL_DRAFT_SENTINELS:
                if sentinel not in chunk.lower():
                    failures.append(
                        f"llms-full.txt {route}: review-draft boundary is "
                        f"missing {sentinel!r}"
                    )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--mode", choices=("staging", "public_docs", "production"), required=True
    )
    args = parser.parse_args()
    failures = verify(args.root.resolve(), args.mode)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print(f"verified {args.mode} documentation artifact at {args.root}")


if __name__ == "__main__":
    main()

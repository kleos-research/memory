#!/usr/bin/env python3
"""Verify a generated Kaleidoscope documentation artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

DOMAIN = "https://memory.kleosresearch.xyz"
ENGINE_CANDIDATE_SHA256 = (
    "988192ac9677d5dd55a3642b2da493a0806bb860b5b3c0f509b37ddadee08825"
)
PUBLIC_CONTRACT_SHA256 = (
    "a2357ed6c00e3e143d08581590571447e31d24fd0e7d2466d28a211a0515c75e"
)
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
    "docs/concepts/index.html",
    "docs/cli/index.html",
    "docs/mcp/index.html",
    "docs/integrations/index.html",
    "docs/operations/index.html",
    "docs/security/index.html",
    "docs/privacy/index.html",
    "docs/account/index.html",
    "docs/compatibility/index.html",
    "docs/benchmarks/index.html",
    "docs/evidence/index.html",
    "docs/release-notes/index.html",
    "docs/troubleshooting/index.html",
    "docs/migration/index.html",
}
EXPECTED_MILESTONES = {
    "DX-04": "3b1ec66d4fc96ff2e77bf7c382b107502ccc7b8d",
    "DX-05B": "048bf90854a1e38a1b88d14de88b681a206e5790",
    "DX-06A/B": "4a195d548036aa5bccd61d1bc0025d126a4d71ad",
    "DX-07": "fd0b1877f70b1bb57e1b67c4c559e8b2e1d44290",
    "DX-09": "ceac8311f819437ace54813d2b4ba0731a5981a1",
    "DX-10B": "ee01e26baaa0df28331795b918c7f1633dafc6f8",
}


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.h1_count = 0
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.descriptions: list[str] = []
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
        if tag == "meta" and values.get("name") == "robots":
            self.robots.append(values.get("content") or "")
        if tag == "meta" and values.get("name") == "description":
            self.descriptions.append(values.get("content") or "")
        if tag == "script" and values.get("type") == "application/ld+json":
            self._structured_buffer = []
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

    evidence_path = actual.get("staging-evidence.json")
    if evidence_path is None:
        failures.append("missing staging-evidence.json")
    else:
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("staging-evidence.json is not valid JSON")
        else:
            if evidence.get("schema_version") != "kaleidoscope.docs-staging-evidence.v1":
                failures.append("wrong staging evidence schema")
            engine = evidence.get("engine", {})
            if engine.get("candidate_sha256") != ENGINE_CANDIDATE_SHA256:
                failures.append("staging evidence has wrong engine candidate")
            if engine.get("public_contract_sha256") != PUBLIC_CONTRACT_SHA256:
                failures.append("staging evidence has wrong public contract")
            if engine.get("production_signature_verified") is not False:
                failures.append("staging evidence must not claim a production signature")
            if evidence.get("production_release") is not False:
                failures.append("staging evidence must not claim production release")
            if evidence.get("public_availability") is not False:
                failures.append("staging evidence must not claim public availability")
            holds = evidence.get("release_holds", {})
            for field in (
                "final_auth_merged_manager_sha256",
                "final_auth_merged_distribution_sha256",
                "production_oidc_issuer",
                "production_signing_identity",
            ):
                if holds.get(field, "missing") is not None:
                    failures.append(f"staging evidence must leave {field} unresolved")
            for field in (
                "public_manager_license_approved",
                "original_documentation_license_approved",
                "registry_publication_authorized",
                "pages_promotion_authorized",
            ):
                if holds.get(field) is not False:
                    failures.append(f"staging evidence must leave {field} false")
            milestones = {item.get("id"): item for item in evidence.get("milestones", [])}
            if set(milestones) != set(EXPECTED_MILESTONES):
                failures.append("staging evidence milestone inventory changed")
            else:
                for milestone, commit in EXPECTED_MILESTONES.items():
                    if milestones[milestone].get("commit") != commit:
                        failures.append(
                            f"staging evidence has wrong commit for {milestone}"
                        )

    cli_reference = actual.get("reference/kaleidoscope-cli.candidate.txt")
    if cli_reference is None:
        failures.append("missing candidate CLI reference")
    else:
        cli_text = cli_reference.read_text(encoding="utf-8")
        for command in (
            "kaleidoscope [--engine PATH] init",
            "kaleidoscope [--engine PATH] connect HOST",
            "kaleidoscope instructions install TARGET",
            "kaleidoscope login [--device]",
            "kaleidoscope status [--json]",
            "kaleidoscope account unlink EXTERNAL_IDENTITY_UUID",
            "kaleidoscope devices revoke DEVICE_UUID",
        ):
            if command not in cli_text:
                failures.append(f"candidate CLI reference missing {command!r}")

    mcp_reference = actual.get("reference/kaleidoscope-mcp.candidate.json")
    if mcp_reference is None:
        failures.append("missing candidate MCP reference")
    else:
        try:
            mcp = json.loads(mcp_reference.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("candidate MCP reference is not valid JSON")
        else:
            if mcp.get("schema_version") != "kaleidoscope.docs-mcp-reference.v1":
                failures.append("wrong candidate MCP reference schema")
            if mcp.get("engine", {}).get("sha256") != ENGINE_CANDIDATE_SHA256:
                failures.append("candidate MCP reference has wrong engine digest")
            if mcp.get("public_contract_sha256") != PUBLIC_CONTRACT_SHA256:
                failures.append("candidate MCP reference has wrong contract digest")
            if mcp.get("protocol_revision") != "2025-11-25":
                failures.append("candidate MCP reference has wrong protocol revision")
            tools = {tool.get("name"): tool for tool in mcp.get("model_tools", [])}
            if set(tools) != {"remember", "search"}:
                failures.append("candidate MCP reference must expose exactly remember/search")
            if tools.get("remember", {}).get("maximum_batch_items") != 20:
                failures.append("candidate MCP reference has wrong remember batch bound")
            if tools.get("search", {}).get("ledger_values") != [True]:
                failures.append("candidate MCP reference must keep ranked search ledgered")
            if mcp.get("operator_commands_are_model_tools") is not False:
                failures.append("candidate MCP reference exposes operator commands")
            if mcp.get("release_readiness_claimed") is not False:
                failures.append("candidate MCP reference claims release readiness")

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
        if len(parser.canonicals) != 1 or not parser.canonicals[0].startswith(
            f"{DOMAIN}/"
        ):
            failures.append(f"{relative}: missing or invalid canonical")
        expected_robots = (
            "index,follow"
            if expected_mode == "production" and relative != "404.html"
            else "noindex,nofollow"
        )
        if parser.robots != [expected_robots]:
            failures.append(
                f"{relative}: robots is {parser.robots!r}, expected {[expected_robots]!r}"
            )
        if len(parser.descriptions) != 1 or not parser.descriptions[0].strip():
            failures.append(f"{relative}: expected one non-empty meta description")
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
        if not relative.startswith("docs/migration/"):
            lowered = document.lower()
            for tool in LEGACY_TOOLS:
                if re.search(rf"\b{re.escape(tool)}\b", lowered):
                    failures.append(
                        f"legacy tool {tool!r} outside migration page: {relative}"
                    )
        for link in parser.links:
            target = local_target(root, link)
            if target is not None and not target.exists():
                failures.append(f"{relative}: broken internal link {link}")

    robots = (root / "robots.txt").read_text(encoding="utf-8")
    if expected_mode == "production" and "Allow: /" not in robots:
        failures.append("production robots does not allow root")
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
            for relative in EXPECTED_HTML - {"404.html", "index.html"}
        )
        if sitemap_urls != expected_urls:
            failures.append(
                f"sitemap URL inventory mismatch: expected-only={sorted(expected_urls - sitemap_urls)}, actual-only={sorted(sitemap_urls - expected_urls)}"
            )

    security = (root / ".well-known" / "security.txt").read_text(encoding="utf-8")
    if expected_mode == "staging" and "STAGING ONLY" not in security:
        failures.append("staging security.txt is not marked as staging")
    if expected_mode == "production" and "STAGING ONLY" in security:
        failures.append("production security.txt still carries the staging marker")

    llms = (root / "llms.txt").read_text(encoding="utf-8")
    llms_lower = llms.lower()
    for required in (
        "local native",
        "`search` and `remember`",
        "proprietary object code",
        "hosted memory is planned",
        "/docs/privacy/",
        "/docs/evidence/",
        "/skill.md",
        "/staging-evidence.json",
        "/reference/kaleidoscope-cli.candidate.txt",
        "/reference/kaleidoscope-mcp.candidate.json",
        ENGINE_CANDIDATE_SHA256,
        PUBLIC_CONTRACT_SHA256,
    ):
        if required.lower() not in llms_lower:
            failures.append(f"llms.txt missing {required!r}")

    llms_full = (root / "llms-full.txt").read_text(encoding="utf-8")
    for relative in sorted(EXPECTED_HTML - {"404.html", "index.html"}):
        route = "/" + relative.removesuffix("index.html")
        if f"URL: {DOMAIN}{route}" not in llms_full:
            failures.append(f"llms-full.txt missing canonical section for {route}")
    for required in (
        "# Public agent skill",
        PUBLIC_SKILL_SHA256,
        "# Candidate CLI help",
        "# Candidate MCP reference",
        "# Machine-readable staging evidence",
    ):
        if required not in llms_full:
            failures.append(f"llms-full.txt missing {required!r}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--mode", choices=("staging", "production"), required=True)
    args = parser.parse_args()
    failures = verify(args.root.resolve(), args.mode)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print(f"verified {args.mode} documentation artifact at {args.root}")


if __name__ == "__main__":
    main()

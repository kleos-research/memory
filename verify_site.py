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
SOCIAL_IMAGE = f"{DOMAIN}/assets/kaleidoscope-og.png"
EXPECTED_CNAME = "memory.kleosresearch.xyz"
ENGINE_CANDIDATE_SHA256 = (
    "988192ac9677d5dd55a3642b2da493a0806bb860b5b3c0f509b37ddadee08825"
)
PUBLIC_CONTRACT_SHA256 = (
    "a2357ed6c00e3e143d08581590571447e31d24fd0e7d2466d28a211a0515c75e"
)
PUBLIC_SKILL_SHA256 = (
    "c688db1b84ee20b6786d6109c68fbf8a21fd87486b9fe37e525d85170b77c9ad"
)
MANAGER_SOURCE_COMMIT = "9ed39bddd7bf14e68e1c363074f6921288b9e94b"
MANAGER_SHA256 = (
    "a1eb37ab61f8f5681b654f7e25f06c3e3188720ad4cf61aaecc1ecf265e8f6c1"
)
DISTRIBUTION_COMMIT = "42ffba4e3976810f91f2adcf53bd4393e5330d72"
SDK_FACADE_COMMIT = "9ed39bddd7bf14e68e1c363074f6921288b9e94b"
DISTRIBUTION_ASSEMBLER_COMMIT = "af892d180fe01729450e03917f33ac56698e90e1"
FINAL_EVIDENCE_COMMIT = "0c42ff35b789a0406aaabf6634bdb2988db36b0a"
FINAL_PACKAGE_EVIDENCE_SHA256 = (
    "7d4b49919d9d7607542e27979b64a5f071c58418096ec2a8c74b3c211738307c"
)
FINAL_BUILD_PROOF_SHA256 = (
    "ff363dc752e19979e44b71cc2fdfe6b7f0bf136ba3c29b5cd1bc8b08aa24d053"
)
LOCAL_ARCHIVE_SHA256 = (
    "2342d12e0010e983db9cfd9c32079bddcc96e8045299c97d878f94200ef6ac8a"
)
LOCAL_MANIFEST_SHA256 = (
    "efc41f32bea0deb4180cca85d2996c39d4793cdea78888fc6216a2dcd8ba22f8"
)
PACKAGE_PROOF_SHA256 = "62afa5714352615f6c2303ed6427842a70168cbfb0bb6bea0ca2753ba0d551b7"
NPM_FACADE_SHA256 = "0980c1aef2d94960e7b3384bdc932da024a9534d123d3521f05c66a1b600b4bd"
NPM_NATIVE_SHA256 = "ec38717398a623fcca6043b37438ab3f6e2bcfa5790e391bb8747b63ab3f340b"
PYTHON_FACADE_SHA256 = (
    "72099296676ef38b146018ae4ffac6cfb082bc8a537f178443acd351cf7bf6d7"
)
PYTHON_NATIVE_SHA256 = (
    "d265493d6ca583f2ecd9e69257c8ed604174636e1c5f3b29dc08eafe01c51d8b"
)
LOCAL_SBOM_SHA256 = (
    "5058f2170630cb70ac14252162245f3ae94cc9d02f9b58c74d36694355094f4c"
)
LOCAL_PROVENANCE_SHA256 = (
    "498c60561520e57834a807c2e17443b0a7eefe1c3901c67450e0506135babfb8"
)
LOCAL_TEST_SIGNATURE_SHA256 = (
    "9bce859379b24683cff7e6069835aa9f8d8ac4f1d07ff353f050ea1b9df60e0c"
)
DX10A_EVIDENCE_SHA256 = (
    "cfb0c09eccc2dffeca67fb324927b602f6f1158a9d6e85682cc3112fd696b12e"
)
SDK_HOST_CONFORMANCE_COMMIT = "9cd4b5837e887a0bb3dcc13209134c002aad08f5"
PLATFORM_HARNESS_COMMIT = "52ad4d243966c5a5c9f65b35909d8f029ae74afd"
CROSS_TARGET_COMPILE_SOURCE_COMMIT = "be5112911125a31bcf2efa766791d044cadab5ed"
CROSS_TARGET_COMPILE_EVIDENCE_SHA256 = (
    "67ec1ad295ce912799c883b661e3f2f0ad6e19139a887ea190613ef4a806c55f"
)
DX10B_HOST_EVIDENCE_SHA256 = (
    "74ab8ac26bbb0a3d6093c8d4db467de8d998882801a815495ada0ad0fc1ec840"
)
BENCHMARK_COMMIT = "ef89d05f09435afc9790fcdf5df3e01d34c7115b"
DX09_FIXTURE_EVIDENCE_SHA256 = (
    "f2d2a43bd8ee137f980c83398ec7197e26eedd2395d019926e38ea7531a2a504"
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
    "docs/evidence/index.html",
    "docs/release-notes/index.html",
    "docs/troubleshooting/index.html",
    "docs/migration/index.html",
    "docs/hosted/index.html",
    "docs/legal/index.html",
    "docs/legal/engine-eula/index.html",
    "docs/legal/privacy-notice/index.html",
    "docs/legal/security-policy/index.html",
    "docs/legal/support-policy/index.html",
}
NOINDEX_HTML = {"404.html", "docs/hosted/index.html"}
EXPECTED_MILESTONES = {
    "DX-04": MANAGER_SOURCE_COMMIT,
    "DX-05B": MANAGER_SOURCE_COMMIT,
    "DX-06A/B": DISTRIBUTION_ASSEMBLER_COMMIT,
    "DX-07": SDK_FACADE_COMMIT,
    "DX-09": BENCHMARK_COMMIT,
    "DX-10A": DISTRIBUTION_COMMIT,
    "DX-10B": FINAL_EVIDENCE_COMMIT,
}


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.h1_count = 0
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
    if not social_image.is_file() or not social_image.read_bytes().startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        failures.append("missing or invalid Kaleidoscope social image")

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
            manager = evidence.get("manager", {})
            if manager.get("source_commit") != MANAGER_SOURCE_COMMIT:
                failures.append("staging evidence has wrong manager source commit")
            if manager.get("candidate_sha256") != MANAGER_SHA256:
                failures.append("staging evidence has wrong manager digest")
            if manager.get("production_signature_verified") is not False:
                failures.append("staging evidence must not claim a signed manager")
            distribution = evidence.get("local_distribution", {})
            if distribution.get("commit") != FINAL_EVIDENCE_COMMIT:
                failures.append("staging evidence has wrong final evidence commit")
            if distribution.get("assembler_commit") != DISTRIBUTION_ASSEMBLER_COMMIT:
                failures.append("staging evidence has wrong assembler commit")
            if distribution.get("sdk_facade_commit") != SDK_FACADE_COMMIT:
                failures.append("staging evidence has wrong SDK facade commit")
            if distribution.get("version") != "0.1.0-rc.1":
                failures.append("staging evidence has wrong RC version")
            if distribution.get("native_target") != "darwin-arm64":
                failures.append("staging evidence has wrong native RC target")
            for field, expected in (
                ("archive_sha256", LOCAL_ARCHIVE_SHA256),
                ("manifest_sha256", LOCAL_MANIFEST_SHA256),
                ("sbom_sha256", LOCAL_SBOM_SHA256),
                ("provenance_sha256", LOCAL_PROVENANCE_SHA256),
                ("signature_envelope_sha256", LOCAL_TEST_SIGNATURE_SHA256),
                ("build_proof_sha256", FINAL_BUILD_PROOF_SHA256),
                ("package_proof_sha256", PACKAGE_PROOF_SHA256),
                (
                    "final_facade_happy_path_evidence_sha256",
                    FINAL_PACKAGE_EVIDENCE_SHA256,
                ),
            ):
                if distribution.get(field) != expected:
                    failures.append(f"staging evidence has wrong {field}")
            facades = distribution.get("facades", {})
            if facades.get("contains") != (
                "full public SDK plus kaleidoscope and kscope launchers"
            ):
                failures.append("staging evidence has wrong facade contents")
            if facades.get("npm", {}).get("sha256") != NPM_FACADE_SHA256:
                failures.append("staging evidence has wrong npm facade digest")
            if facades.get("python", {}).get("sha256") != PYTHON_FACADE_SHA256:
                failures.append("staging evidence has wrong Python facade digest")
            native = distribution.get("native_companions", {})
            if native.get("contains") != "manager plus proprietary object-code engine":
                failures.append("staging evidence has wrong native companion contents")
            if native.get("npm", {}).get("sha256") != NPM_NATIVE_SHA256:
                failures.append("staging evidence has wrong npm native digest")
            if native.get("python", {}).get("sha256") != PYTHON_NATIVE_SHA256:
                failures.append("staging evidence has wrong Python native digest")
            if distribution.get("test_signature_only") is not True:
                failures.append("staging evidence must mark its signature test-only")
            if distribution.get("production_release") is not False:
                failures.append("staging distribution must not claim production release")
            if evidence.get("production_release") is not False:
                failures.append("staging evidence must not claim production release")
            if evidence.get("public_availability") is not False:
                failures.append("staging evidence must not claim public availability")
            host_conformance = evidence.get("local_host_cli_conformance", {})
            if host_conformance.get("commit") != PLATFORM_HARNESS_COMMIT:
                failures.append("staging evidence has wrong platform harness commit")
            if host_conformance.get("status") != "verified_local_bundled_candidate":
                failures.append("staging evidence has wrong local host status")
            if host_conformance.get("platform") != "macOS arm64":
                failures.append("staging evidence has wrong local host platform")
            if host_conformance.get("candidate") != "private verified bundled engine candidate":
                failures.append("staging evidence has wrong local host candidate")
            if host_conformance.get("candidate_version") != "0.0.0-proposal":
                failures.append("staging evidence has wrong bundled candidate version")
            if host_conformance.get("candidate_size_bytes") != 21122544:
                failures.append("staging evidence has wrong bundled candidate size")
            if host_conformance.get("candidate_sha256") != ENGINE_CANDIDATE_SHA256:
                failures.append("staging evidence has wrong bundled candidate digest")
            if host_conformance.get("candidate_model_status") != "bundled":
                failures.append("staging evidence must record the bundled model")
            if host_conformance.get("mcp_tools") != ["remember", "search"]:
                failures.append("staging evidence has wrong local host MCP tools")
            hosts = {
                (host.get("name"), host.get("version"), host.get("status"))
                for host in host_conformance.get("hosts", [])
            }
            expected_hosts = {
                ("Codex", "0.149.0", "configuration_verified"),
                ("Claude Code", "2.1.239", "connected"),
                ("OpenCode", "1.18.21", "connected"),
            }
            if hosts != expected_hosts:
                failures.append("staging evidence has wrong local host inventory")
            compile_evidence = evidence.get("cross_target_compile", {})
            if compile_evidence.get("schema_version") != "kaleidoscope.docs-cross-target-compile.v1":
                failures.append("staging evidence has wrong cross-target compile schema")
            if compile_evidence.get("status") != "compile_only":
                failures.append("staging evidence must mark cross-target checks compile-only")
            if compile_evidence.get("source_commit") != CROSS_TARGET_COMPILE_SOURCE_COMMIT:
                failures.append("staging evidence has wrong cross-target source commit")
            if compile_evidence.get("rust_toolchain") != "1.97.1":
                failures.append("staging evidence has wrong cross-target toolchain")
            if compile_evidence.get("host_environment") != "macOS arm64":
                failures.append("staging evidence has wrong cross-target host environment")
            if compile_evidence.get("evidence_sha256") != CROSS_TARGET_COMPILE_EVIDENCE_SHA256:
                failures.append("staging evidence has wrong cross-target evidence digest")
            compile_targets = {
                (target.get("triple"), target.get("platform"), target.get("architecture"), target.get("status"))
                for target in compile_evidence.get("targets", [])
            }
            expected_compile_targets = {
                ("x86_64-unknown-linux-gnu", "Linux", "x86_64", "passed"),
                ("aarch64-unknown-linux-gnu", "Linux", "arm64", "passed"),
                ("x86_64-pc-windows-gnu", "Windows", "x86_64", "passed"),
                ("x86_64-apple-darwin", "macOS", "x86_64", "passed"),
            }
            if compile_targets != expected_compile_targets:
                failures.append("staging evidence has wrong cross-target inventory")
            holds = evidence.get("release_holds", {})
            if holds.get("local_host_cli_configuration_verified") is not True:
                failures.append("staging evidence must record local host wiring")
            for field in ("production_oidc_issuer", "production_signing_identity"):
                if holds.get(field, "missing") is not None:
                    failures.append(f"staging evidence must leave {field} unresolved")
            for field in (
                "production_engine_eula_finalized",
                "external_legal_review_complete",
                "registry_publication_authorized",
                "pages_promotion_authorized",
                "non_macos_arm64_native_support_verified",
                "claude_cursor_opencode_live_host_verified",
                "live_model_or_ide_acceptance_verified",
            ):
                if holds.get(field) is not False:
                    failures.append(f"staging evidence must leave {field} false")
            for field in (
                "engine_eula_product_authorized",
                "public_software_license_product_authorized",
                "original_documentation_license_product_authorized",
            ):
                if holds.get(field) is not True:
                    failures.append(f"staging evidence must record {field}")
            milestones = {item.get("id"): item for item in evidence.get("milestones", [])}
            if set(milestones) != set(EXPECTED_MILESTONES):
                failures.append("staging evidence milestone inventory changed")
            else:
                for milestone, commit in EXPECTED_MILESTONES.items():
                    if milestones[milestone].get("commit") != commit:
                        failures.append(
                            f"staging evidence has wrong commit for {milestone}"
                        )
                if DX10A_EVIDENCE_SHA256 not in milestones["DX-10A"].get(
                    "verification", ""
                ):
                    failures.append("staging evidence has wrong DX-10A digest")
                if DX09_FIXTURE_EVIDENCE_SHA256 not in milestones["DX-09"].get(
                    "verification", ""
                ):
                    failures.append("staging evidence has wrong DX-09 digest")
                if FINAL_PACKAGE_EVIDENCE_SHA256 not in milestones["DX-10B"].get(
                    "verification", ""
                ):
                    failures.append("staging evidence has wrong final DX-10B digest")
            historical = evidence.get("historical_host_conformance", {})
            if historical.get("commit") != SDK_HOST_CONFORMANCE_COMMIT:
                failures.append("staging evidence has wrong historic host commit")
            if historical.get("evidence_sha256") != DX10B_HOST_EVIDENCE_SHA256:
                failures.append("staging evidence has wrong historic host digest")
            if "pre-final manager candidate" not in historical.get("status", ""):
                failures.append("staging evidence must qualify historic host evidence")

    compile_path = actual.get("cross-target-checks.json")
    if compile_path is None:
        failures.append("missing cross-target-checks.json")
    else:
        try:
            compile_record = json.loads(compile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append("cross-target-checks.json is not valid JSON")
        else:
            if compile_record.get("schema_version") != "kaleidoscope.docs-cross-target-compile.v1":
                failures.append("wrong cross-target compile evidence schema")
            if compile_record.get("source_commit") != CROSS_TARGET_COMPILE_SOURCE_COMMIT:
                failures.append("cross-target compile evidence has wrong source commit")
            if compile_record.get("evidence_sha256") != CROSS_TARGET_COMPILE_EVIDENCE_SHA256:
                failures.append("cross-target compile evidence has wrong digest")

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
            "kaleidoscope profile account bind ACCOUNT_UUID [NAME]",
            "kaleidoscope account identities",
            "kaleidoscope account unlink EXTERNAL_IDENTITY_UUID",
            "kaleidoscope account revoke-session",
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
            if mcp.get("manager", {}).get("source_commit") != MANAGER_SOURCE_COMMIT:
                failures.append("candidate MCP reference has wrong manager source")
            if mcp.get("manager", {}).get("sha256") != MANAGER_SHA256:
                failures.append("candidate MCP reference has wrong manager digest")
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
            conformance = mcp.get("local_conformance", {})
            if conformance.get("dx10a_evidence_sha256") != DX10A_EVIDENCE_SHA256:
                failures.append("candidate MCP reference has wrong DX-10A digest")
            if (
                conformance.get("final_package_evidence_sha256")
                != FINAL_PACKAGE_EVIDENCE_SHA256
            ):
                failures.append("candidate MCP reference has wrong final DX-10B digest")
            if conformance.get("platform_harness_commit") != PLATFORM_HARNESS_COMMIT:
                failures.append("candidate MCP reference has wrong platform harness commit")
            host_conformance = conformance.get("local_host_cli_conformance", {})
            if host_conformance.get("commit") != PLATFORM_HARNESS_COMMIT:
                failures.append("candidate MCP reference has wrong local host commit")
            if host_conformance.get("mcp_tools") != ["remember", "search"]:
                failures.append("candidate MCP reference has wrong local host MCP tools")
            historical = conformance.get("historical_codex_host_evidence", {})
            if historical.get("commit") != SDK_HOST_CONFORMANCE_COMMIT:
                failures.append("candidate MCP reference has wrong historic host commit")
            if historical.get("sha256") != DX10B_HOST_EVIDENCE_SHA256:
                failures.append("candidate MCP reference has wrong historic host digest")
            if historical.get("applies_to") != "pre-final manager candidate only":
                failures.append("candidate MCP reference must qualify historic host evidence")
            packages = mcp.get("package_contract", {})
            if packages.get("version") != "0.1.0-rc.1":
                failures.append("candidate MCP reference has wrong RC version")
            if packages.get("sdk_facade_commit") != SDK_FACADE_COMMIT:
                failures.append("candidate MCP reference has wrong SDK facade commit")
            if packages.get("native_target") != "darwin-arm64":
                failures.append("candidate MCP reference has wrong native target")
            if packages.get("facade_launchers") != ["kaleidoscope", "kscope"]:
                failures.append("candidate MCP reference has wrong facade launchers")
            if packages.get("publicly_available") is not False:
                failures.append("candidate MCP reference claims package availability")
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
    if expected_mode == "staging" and "STAGING ONLY" not in security:
        failures.append("staging security.txt is not marked as staging")
    if expected_mode == "public_docs" and "DOCUMENTATION PREVIEW" not in security:
        failures.append("public documentation security.txt is not marked as preview")
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
        "/cross-target-checks.json",
        "/reference/kaleidoscope-cli.candidate.txt",
        "/reference/kaleidoscope-mcp.candidate.json",
        ENGINE_CANDIDATE_SHA256,
        PUBLIC_CONTRACT_SHA256,
        MANAGER_SHA256,
        FINAL_PACKAGE_EVIDENCE_SHA256,
        FINAL_BUILD_PROOF_SHA256,
        DX09_FIXTURE_EVIDENCE_SHA256,
        DX10A_EVIDENCE_SHA256,
        DX10B_HOST_EVIDENCE_SHA256,
        PLATFORM_HARNESS_COMMIT,
        CROSS_TARGET_COMPILE_EVIDENCE_SHA256,
        SDK_FACADE_COMMIT,
        DISTRIBUTION_ASSEMBLER_COMMIT,
        FINAL_EVIDENCE_COMMIT,
        LOCAL_ARCHIVE_SHA256,
        LOCAL_MANIFEST_SHA256,
        PACKAGE_PROOF_SHA256,
        NPM_FACADE_SHA256,
        NPM_NATIVE_SHA256,
        PYTHON_FACADE_SHA256,
        PYTHON_NATIVE_SHA256,
        LOCAL_SBOM_SHA256,
        LOCAL_PROVENANCE_SHA256,
        LOCAL_TEST_SIGNATURE_SHA256,
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

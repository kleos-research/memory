from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

import build_site
import verify_site


ROOT = Path(__file__).parents[1]


class DocumentationArtifactTest(unittest.TestCase):
    def test_staging_build_passes_full_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            metadata = build_site.load_metadata(None)
            build_site.build(output, metadata)
            self.assertEqual(verify_site.verify(output, "staging"), [])

    def test_checked_in_pages_artifact_matches_the_deterministic_public_docs_build(self) -> None:
        checked_in = ROOT / "docs"
        self.assertEqual(verify_site.verify(checked_in, "public_docs"), [])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            metadata = build_site.load_metadata(
                ROOT / "public-docs-release.json", "public_docs"
            )
            build_site.build(output, metadata, "public_docs")
            self.assertEqual(
                json.loads((checked_in / "site-manifest.json").read_text()),
                json.loads((output / "site-manifest.json").read_text()),
            )
        image = ROOT / "assets" / "kaleidoscope-og.png"
        self.assertTrue(image.is_file())
        self.assertTrue(image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_public_docs_requires_immutable_preview_metadata(self) -> None:
        with self.assertRaises(SystemExit):
            build_site.load_metadata(None, "public_docs")
        metadata = build_site.load_metadata(
            ROOT / "public-docs-release.json", "public_docs"
        )
        self.assertEqual(metadata["availability"], "documentation_preview")

    def test_route_inventory_matches_navigation(self) -> None:
        page_routes = [page.route for page in build_site.PAGES]
        nav_routes = [route for route, _label in build_site.DOC_NAV]
        self.assertEqual(len(page_routes), len(set(page_routes)))
        self.assertEqual(len(nav_routes), len(set(nav_routes)))
        self.assertTrue(set(nav_routes).issubset(page_routes))
        self.assertIn("/docs/hosted/", page_routes)
        self.assertTrue(
            next(page for page in build_site.PAGES if page.route == "/docs/hosted/").noindex
        )

    def test_public_skill_and_tool_contract_are_exact(self) -> None:
        skill = build_site.PUBLIC_FILES["SKILL.md"]
        self.assertEqual(
            hashlib.sha256(skill.read_bytes()).hexdigest(),
            build_site.PUBLIC_SKILL_SHA256,
        )
        self.assertEqual(
            {tool["name"] for tool in build_site.MCP_REFERENCE["model_tools"]},
            {"search", "remember"},
        )
        self.assertFalse(build_site.MCP_REFERENCE["operator_commands_are_model_tools"])
        self.assertEqual(
            build_site.STATUS_RECORD["hosts"]["tools_a_model_sees"],
            ["remember", "search"],
        )
        self.assertEqual(
            {
                (row["platform"], row["architecture"])
                for row in build_site.PLATFORM_SUPPORT["compiler checked only"][
                    "platforms"
                ]
            },
            {
                ("macOS", "x86_64"),
                ("Linux", "x86_64"),
                ("Linux", "arm64"),
                ("Windows", "x86_64"),
            },
        )

    def test_every_partly_tested_host_says_which_part(self) -> None:
        for host in build_site.HOST_SUPPORT["hosts"]:
            if host["status"] == "partly tested":
                self.assertTrue(
                    host["not confirmed"],
                    f"{host['name']} is partly tested without saying which part",
                )

    def test_the_compiler_check_is_never_described_as_a_build(self) -> None:
        # Published once as "the code builds for this target", four platforms
        # nothing has ever been built for read as working builds.
        meaning = build_site.PLATFORM_SUPPORT["compiler checked only"]["meaning"]
        self.assertIn("The compiler accepts", meaning)
        self.assertIn("Nothing was ever assembled", meaning)
        self.assertIn("nothing has been run there", meaning)
        for page in build_site.PAGES:
            if page.route in {"/docs/compatibility/", "/docs/status/"}:
                self.assertNotIn("Builds only", page.body)

    def test_public_machine_records_have_no_private_coordinates(self) -> None:
        values = "\n".join(
            (
                build_site.MANAGER_HELP,
                json.dumps(build_site.MCP_REFERENCE, sort_keys=True),
                json.dumps(build_site.STATUS_RECORD, sort_keys=True),
                json.dumps(build_site.PLATFORM_SUPPORT, sort_keys=True),
            )
        )
        for marker in verify_site.PRIVATE_MARKERS:
            self.assertNotIn(marker, values)
        for pattern in verify_site.BANNED_VOCABULARY:
            self.assertIsNone(
                re.search(pattern, values.lower()),
                f"internal vocabulary matching {pattern} in a public machine record",
            )
        status = build_site.STATUS_RECORD
        self.assertFalse(status["released"])
        self.assertFalse(status["publicly available"])
        self.assertFalse(status["packages"]["published to a registry"])
        self.assertFalse(status["packages"]["signed for release"])
        self.assertIn("not in force", status["licences"]["the product terms"])
        for value in status["still true before any release"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()

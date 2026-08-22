from __future__ import annotations

import hashlib
import json
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

    def test_public_skill_and_candidate_bindings_are_exact(self) -> None:
        skill = build_site.PUBLIC_FILES["SKILL.md"]
        self.assertEqual(
            hashlib.sha256(skill.read_bytes()).hexdigest(),
            build_site.PUBLIC_SKILL_SHA256,
        )
        self.assertEqual(
            build_site.MCP_REFERENCE["engine"]["sha256"],
            build_site.ENGINE_CANDIDATE_SHA256,
        )
        self.assertEqual(
            build_site.MCP_REFERENCE["public_contract_sha256"],
            build_site.PUBLIC_CONTRACT_SHA256,
        )
        self.assertEqual(
            {tool["name"] for tool in build_site.MCP_REFERENCE["model_tools"]},
            {"search", "remember"},
        )
        self.assertEqual(
            build_site.MCP_REFERENCE["local_conformance"]["platform_harness_commit"],
            build_site.PLATFORM_HARNESS_COMMIT,
        )
        self.assertEqual(
            build_site.STAGING_EVIDENCE["local_host_cli_conformance"]["mcp_tools"],
            ["remember", "search"],
        )

    def test_public_machine_records_have_no_private_coordinates(self) -> None:
        values = "\n".join(
            (
                build_site.MANAGER_HELP,
                json.dumps(build_site.MCP_REFERENCE, sort_keys=True),
                json.dumps(build_site.STAGING_EVIDENCE, sort_keys=True),
            )
        )
        for marker in verify_site.PRIVATE_MARKERS:
            self.assertNotIn(marker, values)
        holds = build_site.STAGING_EVIDENCE["release_holds"]
        self.assertEqual(
            build_site.STAGING_EVIDENCE["manager"]["candidate_sha256"],
            build_site.MANAGER_SHA256,
        )
        self.assertEqual(
            build_site.STAGING_EVIDENCE["local_distribution"][
                "package_proof_sha256"
            ],
            build_site.PACKAGE_PROOF_SHA256,
        )
        distribution = build_site.STAGING_EVIDENCE["local_distribution"]
        self.assertEqual(distribution["sdk_facade_commit"], build_site.SDK_FACADE_COMMIT)
        self.assertEqual(distribution["native_target"], "darwin-arm64")
        self.assertEqual(
            distribution["facades"]["contains"],
            "full public SDK plus kaleidoscope and kscope launchers",
        )
        self.assertEqual(
            distribution["native_companions"]["contains"],
            "manager plus proprietary object-code engine",
        )
        self.assertTrue(
            build_site.STAGING_EVIDENCE["local_distribution"][
                "test_signature_only"
            ]
        )
        self.assertTrue(holds["engine_eula_product_authorized"])
        self.assertTrue(holds["public_software_license_product_authorized"])
        self.assertTrue(
            holds["original_documentation_license_product_authorized"]
        )
        self.assertFalse(holds["production_engine_eula_finalized"])
        self.assertFalse(holds["external_legal_review_complete"])
        self.assertFalse(holds["non_macos_arm64_native_support_verified"])
        self.assertFalse(holds["claude_cursor_opencode_live_host_verified"])
        self.assertTrue(holds["local_host_cli_configuration_verified"])
        self.assertFalse(build_site.STAGING_EVIDENCE["production_release"])
        self.assertFalse(build_site.STAGING_EVIDENCE["public_availability"])


if __name__ == "__main__":
    unittest.main()

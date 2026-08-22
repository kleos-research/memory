from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import build_site
import verify_site


class DocumentationArtifactTest(unittest.TestCase):
    def test_staging_build_passes_full_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            metadata = build_site.load_metadata(None, production=False)
            build_site.build(output, metadata, production=False)
            self.assertEqual(verify_site.verify(output, "staging"), [])

    def test_route_inventory_matches_navigation(self) -> None:
        page_routes = [page.route for page in build_site.PAGES]
        nav_routes = [route for route, _label in build_site.DOC_NAV]
        self.assertEqual(len(page_routes), len(set(page_routes)))
        self.assertEqual(page_routes, nav_routes)

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
                "verification_summary_sha256"
            ],
            build_site.DX06_VERIFICATION_SHA256,
        )
        self.assertTrue(
            build_site.STAGING_EVIDENCE["local_distribution"][
                "test_signature_only"
            ]
        )
        self.assertFalse(holds["production_engine_eula_approved"])
        self.assertFalse(holds["non_macos_arm64_native_support_verified"])
        self.assertFalse(holds["claude_cursor_opencode_live_host_verified"])
        self.assertFalse(build_site.STAGING_EVIDENCE["production_release"])
        self.assertFalse(build_site.STAGING_EVIDENCE["public_availability"])


if __name__ == "__main__":
    unittest.main()

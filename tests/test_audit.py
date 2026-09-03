from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_audit.core import (
    audit_directory,
    classify_asset_type,
    classify_lifecycle,
    classify_project,
    write_audit_outputs,
)
from knowledge_audit.generator import generate_synthetic_dataset, synthetic_files


class ClassificationTests(unittest.TestCase):
    def test_project_rules_are_explainable(self) -> None:
        self.assertEqual(
            classify_project("01_self_injection_return_model/analysis/scenarios.csv"),
            "Self-injectable medicine return model",
        )
        self.assertEqual(
            classify_project("02_medical_waste_vehicle/operations/routes.csv"),
            "Medical-waste vehicle operations",
        )
        self.assertEqual(
            classify_project("03_drone_systems/coverage_model.py"), "Drone systems"
        )
        self.assertEqual(
            classify_project("misc/notes.txt"), "Cross-project / General"
        )

    def test_type_and_lifecycle_rules(self) -> None:
        self.assertEqual(classify_asset_type("data/assumptions.csv"), "Structured data")
        self.assertEqual(classify_asset_type("tools/check.py"), "Source code")
        self.assertEqual(
            classify_lifecycle("archive/model_backup.csv"), "Archive/backup hint"
        )
        self.assertEqual(classify_lifecycle("brief_final.md"), "Final/release hint")
        self.assertEqual(classify_lifecycle("notes.md"), "No status hint")


class AuditWorkflowTests(unittest.TestCase):
    def test_generation_refuses_collision_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generate_synthetic_dataset(root)
            with self.assertRaises(FileExistsError):
                generate_synthetic_dataset(root)

    def test_overwrite_preserves_unrelated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generate_synthetic_dataset(root)
            unrelated = root / "KEEP_ME.txt"
            unrelated.write_text("user-owned file\n", encoding="utf-8")

            generate_synthetic_dataset(root, overwrite=True)

            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user-owned file\n")

    def test_synthetic_audit_finds_expected_exact_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "input"
            generate_synthetic_dataset(root)
            result = audit_directory(root)

            self.assertEqual(result.summary["files_discovered"], len(synthetic_files()))
            self.assertEqual(result.summary["files_with_errors"], 0)
            self.assertEqual(result.summary["exact_duplicate_groups"], 3)
            self.assertEqual(result.summary["redundant_exact_copies"], 3)
            self.assertEqual(
                result.summary["unique_content_hashes"], len(synthetic_files()) - 3
            )

            duplicate_paths = {
                record.relative_path: record.duplicate_of
                for record in result.records
                if record.duplicate_of
            }
            self.assertEqual(
                duplicate_paths[
                    "01_self_injection_return_model/research/landscape_notes - Copy.md"
                ],
                "01_self_injection_return_model/research/landscape_notes.md",
            )
            self.assertEqual(
                duplicate_paths[
                    "01_self_injection_return_model/analysis/collection_scenarios_backup.csv"
                ],
                "01_self_injection_return_model/analysis/collection_scenarios.csv",
            )

    def test_all_outputs_are_written_and_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "input"
            output = base / "output"
            generate_synthetic_dataset(source)
            result = audit_directory(source)
            paths = write_audit_outputs(
                result,
                output,
                title="Test audit",
                provenance="Synthetic unit-test data.",
                generated_at_utc="2026-01-15T00:00:00+00:00",
            )

            self.assertEqual(
                set(paths),
                {"inventory", "duplicates", "review_queue", "summary", "report"},
            )
            self.assertTrue(all(path.is_file() for path in paths.values()))

            summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
            self.assertEqual(summary["summary"]["exact_duplicate_groups"], 3)
            self.assertIn("Synthetic unit-test data.", summary["provenance"])

            with paths["inventory"].open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), len(synthetic_files()))

            report = paths["report"].read_text(encoding="utf-8")
            self.assertIn("# Test audit", report)
            self.assertIn("## Interpretation boundaries", report)
            self.assertIn(
                "do not auto-delete",
                paths["review_queue"].read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()


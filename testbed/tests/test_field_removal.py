"""Reject unrelated failures rather than reporting them as removal evidence."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("field_removal", ROOT / "run_field_removal.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class FailureEvidenceTests(unittest.TestCase):
    def test_expected_missing_field_diagnostics(self):
        diagnostics = {
            "python": 'AttributeError: Protocol message Entity has no "name" field.',
            "typescript": "main.ts(10,20): error TS2339: Property 'name' does not exist on type 'Entity'.",
            "csharp": "main.cs(10,20): error CS1061: 'Entity' does not contain a definition for 'Name'",
        }
        for language, diagnostic in diagnostics.items():
            with self.subTest(language=language):
                demo.require_field_failure(language, subprocess.CompletedProcess([], 1, diagnostic))

    def test_unrelated_build_errors_do_not_count(self):
        for language in ("python", "typescript", "csharp"):
            with self.subTest(language=language):
                with self.assertRaises(RuntimeError):
                    demo.require_field_failure(language, subprocess.CompletedProcess([], 1, "missing dependency"))

    def test_success_cannot_count_as_expected_failure(self):
        with self.assertRaises(RuntimeError):
            demo.require_field_failure("python", subprocess.CompletedProcess([], 0, 'AttributeError: name'))


if __name__ == "__main__":
    unittest.main()

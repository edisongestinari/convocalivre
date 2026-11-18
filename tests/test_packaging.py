"""Portable Windows launcher smoke test without requiring a GUI display."""

from pathlib import Path
import runpy
import unittest


class PackagingTests(unittest.TestCase):
    def test_launcher_smoke_test_has_no_window(self):
        launcher = (
            Path(__file__).resolve().parents[1] / "packaging" / "windows_launcher.py"
        )
        namespace = runpy.run_path(str(launcher))
        self.assertEqual(namespace["main"](["--smoke-test"]), 0)
        self.assertEqual(namespace["main"](["unknown"]), 2)


if __name__ == "__main__":
    unittest.main()

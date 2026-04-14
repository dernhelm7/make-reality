from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .fixture_support import ET_BOOK_ROMAN, EXAMPLES_ROOT, REPO_ROOT


class CommandSmokeTests(unittest.TestCase):
    def test_cli_build_command(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "labyrinth",
                "build",
                str(EXAMPLES_ROOT / "minimal-markdown"),
                str(publish_root),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((publish_root / "index.html").exists())
        self.assertTrue((publish_root / ET_BOOK_ROMAN).exists())

    def test_build_script_works_outside_repo_root(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        outside_cwd = Path(self.enterContext(tempfile.TemporaryDirectory()))
        result = subprocess.run(
            [
                str(REPO_ROOT / "build-site"),
                str(EXAMPLES_ROOT / "minimal-markdown"),
                str(publish_root),
            ],
            cwd=outside_cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((publish_root / "index.html").exists())
        self.assertTrue((publish_root / ET_BOOK_ROMAN).exists())

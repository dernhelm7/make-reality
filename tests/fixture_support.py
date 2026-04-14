from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from labyrinth.builder import build_site


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "agent_docs" / "examples"
ET_BOOK_ROMAN = "fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff"
ET_BOOK_ITALIC = (
    "fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff"
)
ET_BOOK_BOLD = "fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff"
ET_BOOK_LICENSE = "fonts/et-book/LICENSE.txt"


class FixtureSiteTestCase(unittest.TestCase):
    def make_fixture(self, fixture_name: str) -> tuple[Path, Path]:
        temp_dir = self.enterContext(tempfile.TemporaryDirectory())
        site_root = Path(temp_dir) / "site"
        publish_root = Path(temp_dir) / "publish"
        shutil.copytree(EXAMPLES_ROOT / fixture_name, site_root)
        return site_root, publish_root

    def build_fixture(self, fixture_name: str) -> tuple[Path, Path]:
        site_root, publish_root = self.make_fixture(fixture_name)
        build_site(site_root, publish_root)
        return site_root, publish_root

    def page_text(self, publish_root: Path, public_path: str) -> str:
        return read_text(self.public_page_path(publish_root, public_path))

    def public_page_path(self, publish_root: Path, public_path: str) -> Path:
        if public_path == "/":
            return publish_root / "index.html"
        candidate = publish_root / public_path.lstrip("/")
        if candidate.is_dir():
            return candidate / "index.html"
        if candidate.exists():
            return candidate
        html_candidate = candidate.with_suffix(".html")
        if html_candidate.exists():
            return html_candidate
        return candidate

    def assert_common_public_layout(self, publish_root: Path, expected_pages: list[str]) -> None:
        self.assertTrue((publish_root / "index.html").is_file())
        self.assertFalse((publish_root / "works").exists())
        self.assertTrue((publish_root / "feed.xml").is_file())
        self.assertTrue((publish_root / "site.css").is_file())
        self.assertTrue((publish_root / ET_BOOK_ROMAN).is_file())
        self.assertTrue((publish_root / ET_BOOK_ITALIC).is_file())
        self.assertTrue((publish_root / ET_BOOK_BOLD).is_file())
        self.assertTrue((publish_root / ET_BOOK_LICENSE).is_file())
        self.assertEqual([], list(publish_root.rglob("*.js")))
        for public_path in expected_pages:
            self.assertTrue(self.public_page_path(publish_root, public_path).exists(), public_path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()

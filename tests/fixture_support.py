from __future__ import annotations

import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

from labyrinth.builder import build_site


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "agent_docs" / "examples"


class FixtureSiteTestCase(unittest.TestCase):
    def make_site(self, works: dict[str, dict[str, str]]) -> Path:
        site_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (site_root / "site.toml").write_text(
            textwrap.dedent(
                """\
                url = "https://labyrinth.example"
                lang = "en"
                title = "Labyrinth"
                statement = "A room for poems, projects, and notes."
                author_name = "Labyrinth Author"
                updated = "2024-02-14T00:00:00Z"
                """
            ),
            encoding="utf-8",
        )
        (site_root / "home.md").write_text(
            textwrap.dedent(
                """\
                # Labyrinth

                A room for poems, projects, and notes.

                [First](https://first.example/labyrinth)
                [Second](https://second.example/labyrinth)
                [Feed](/feed.xml)

                ## Index
                """
            ),
            encoding="utf-8",
        )
        (site_root / "feed.md").write_text(
            "Web feed\n\nCopy [the feed URL]({feed_url}) into a feed reader.",
            encoding="utf-8",
        )
        works_root = site_root / "works"
        works_root.mkdir()

        for name, files in works.items():
            work_root = works_root / name
            work_root.mkdir(parents=True)
            for filename, content in files.items():
                (work_root / filename).write_text(content, encoding="utf-8")
        return site_root

    def set_home_sections(self, site_root: Path, headings: str) -> None:
        home_md = site_root / "home.md"
        home_md.write_text(
            home_md.read_text(encoding="utf-8").replace("## Index", f"## Index\n\n{headings}"),
            encoding="utf-8",
        )

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
        return self.public_page_path(publish_root, public_path).read_text(encoding="utf-8")

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
        self.assertTrue((publish_root / "feed.css").is_file())
        self.assertTrue((publish_root / "site.css").is_file())
        self.assertTrue(any(path.suffix == ".woff" for path in (publish_root / "fonts").rglob("*")))
        self.assertEqual([], list(publish_root.rglob("*.js")))
        for public_path in ["/", *expected_pages]:
            page = self.page_text(publish_root, public_path)
            self.assertIn('id="site-theme-toggle"', page)
        for public_path in expected_pages:
            self.assertTrue(self.public_page_path(publish_root, public_path).exists(), public_path)

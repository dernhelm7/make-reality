from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from labyrinth.builder import BuildError, RenderedPage, build_site, validate_rendered_pages


class ValidationTests(unittest.TestCase):
    def test_missing_required_field_case(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": "",
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "missing-required-field")
        self.assertIn("meta.toml", str(error.exception.source_path))

    def test_missing_site_feed_fields_fail_build(self) -> None:
        for field in ("author_name", "updated"):
            site_root = self.make_site(
                {
                    "alpha": {
                        "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                        "index.md": "# Opening\n\nA first note.",
                    }
                }
            )
            site_toml = site_root / "site.toml"
            site_toml.write_text(
                "\n".join(
                    line
                    for line in site_toml.read_text(encoding="utf-8").splitlines()
                    if not line.startswith(f"{field} = ")
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(BuildError) as error:
                build_site(site_root, site_root / "public")

            self.assertEqual(error.exception.rule, "missing-required-field")
            self.assertIn("site.toml", str(error.exception.source_path))

    def test_missing_home_markdown_fails_build(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )
        (site_root / "home.md").unlink()

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "missing-required-field")
        self.assertIn("home.md", str(error.exception.source_path))

    def test_missing_feed_markdown_fails_build(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )
        (site_root / "feed.md").unlink()

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "missing-required-field")
        self.assertIn("feed.md", str(error.exception.source_path))

    def test_missing_work_feed_fields_fail_build(self) -> None:
        for field in ("updated", "atom_id"):
            site_root = self.make_site(
                {
                    "alpha": {
                        "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                        "index.md": "# Opening\n\nA first note.",
                    }
                }
            )
            meta_toml = site_root / "works" / "alpha" / "meta.toml"
            meta_toml.write_text(
                "\n".join(
                    line
                    for line in meta_toml.read_text(encoding="utf-8").splitlines()
                    if not line.startswith(f"{field} = ")
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(BuildError) as error:
                build_site(site_root, site_root / "public")

            self.assertEqual(error.exception.rule, "missing-required-field")
            self.assertIn("meta.toml", str(error.exception.source_path))

    def test_duplicate_published_path_case(self) -> None:
        site_root = self.make_site(
            {
                "feed.xml": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/feed-xml"\n',
                    "index.md": "# Reserved\n\nPath collision.",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "duplicate-published-path")

    def test_broken_internal_link_case(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "[Broken](/missing-path)",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "broken-internal-link")

    def test_missing_canonical_link_case(self) -> None:
        page = RenderedPage(
            public_path="/",
            output_path=Path("index.html"),
            html="<!DOCTYPE html><html><head><title>Missing</title></head><body></body></html>",
            source_path=Path("synthetic.html"),
        )

        with self.assertRaises(BuildError) as error:
            validate_rendered_pages([page])

        self.assertEqual(error.exception.rule, "missing-canonical-link")

    def test_invalid_build_url_case(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public", build_url="/preview")

        self.assertEqual(error.exception.rule, "missing-required-field")
        self.assertEqual(Path("<command-line>"), error.exception.source_path)

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
            work_root.mkdir()
            for filename, content in files.items():
                (work_root / filename).write_text(content, encoding="utf-8")
        return site_root


if __name__ == "__main__":
    unittest.main()

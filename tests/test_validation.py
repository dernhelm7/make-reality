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
            self.assertIn(field, error.exception.message)

    def test_missing_cover_line_fails_build(self) -> None:
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
                if not line.startswith("cover_line = ")
            )
            + "\n",
            encoding="utf-8",
        )

        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(error.exception.rule, "missing-required-field")
        self.assertIn("site.toml", str(error.exception.source_path))
        self.assertIn("cover_line", error.exception.message)

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
            self.assertIn(field, error.exception.message)

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
        self.assertIn("/missing-path", error.exception.message)

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
        self.assertIn("build-url", error.exception.message)

    def make_site(self, works: dict[str, dict[str, str]]) -> Path:
        site_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (site_root / "site.toml").write_text(
            textwrap.dedent(
                """\
                url = "https://labyrinth.example"
                lang = "en"
                title = "Labyrinth"
                cover_line = "A room for poems, projects, and notes."
                statement = "A room for poems, projects, and notes."
                author_name = "Labyrinth Author"
                updated = "2024-02-14T00:00:00Z"

                [[contact_links]]
                label = "Email"
                href = "mailto:hello@labyrinth.example"

                [[gift_links]]
                label = "Gift"
                href = "https://gifts.example/labyrinth"

                sections = []
                """
            ),
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

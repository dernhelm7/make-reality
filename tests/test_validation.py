from __future__ import annotations

from pathlib import Path
import textwrap

from labyrinth.builder import BuildError, RenderedPage, build_site, validate_rendered_pages
from labyrinth.theme import render_theme_tokens

from .fixture_support import FixtureSiteTestCase


class ValidationTests(FixtureSiteTestCase):
    def assert_build_error(self, site_root: Path, *, rule: str, source_name: str) -> None:
        with self.assertRaises(BuildError) as error:
            build_site(site_root, site_root / "public")

        self.assertEqual(rule, error.exception.rule)
        self.assertIn(source_name, str(error.exception.source_path))

    def test_missing_work_body_case(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'atom_id = "https://labyrinth.example/id/alpha"\n',
                }
            }
        )

        self.assert_build_error(site_root, rule="missing-required-field", source_name="alpha")

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

            self.assert_build_error(site_root, rule="missing-required-field", source_name="site.toml")

    def test_missing_required_source_files_fail_build(self) -> None:
        for filename in ("home.md", "feed.md"):
            site_root = self.make_site(
                {
                    "alpha": {
                        "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                        "index.md": "# Opening\n\nA first note.",
                    }
                }
            )
            (site_root / filename).unlink()

            self.assert_build_error(site_root, rule="missing-required-field", source_name=filename)

    def test_malformed_work_metadata_fails_build(self) -> None:
        for field, replacement in (
            ("created", 'created = ""'),
            ("atom_id", 'atom_id = "/alpha"'),
        ):
            site_root = self.make_site(
                {
                    "alpha": {
                        "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                        "index.md": "# Opening\n\nA first note.",
                    }
                }
            )
            meta_toml = site_root / "works" / "alpha" / "meta.toml"
            lines = [
                replacement if line.startswith(f"{field} = ") else line
                for line in meta_toml.read_text(encoding="utf-8").splitlines()
            ]
            meta_toml.write_text("\n".join(lines) + "\n", encoding="utf-8")

            self.assert_build_error(site_root, rule="missing-required-field", source_name="meta.toml")

    def test_duplicate_front_matter_and_meta_toml_fails_build(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'atom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": '+++\ncreated = "2024-02-14T00:00:00Z"\n+++\n# Opening\n\nA first note.',
                }
            }
        )

        self.assert_build_error(site_root, rule="duplicate-metadata", source_name="index.md")

    def test_work_section_field_fails_build(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": (
                        'created = "2024-02-14T00:00:00Z"\n'
                        'updated = "2024-02-14T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/alpha"\n'
                        'section = "Notes"\n'
                    ),
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )

        self.assert_build_error(site_root, rule="unsupported-field", source_name="meta.toml")

    def test_duplicate_published_path_case(self) -> None:
        site_root = self.make_site(
            {
                "feed.xml": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/feed-xml"\n',
                    "index.md": "# Reserved\n\nPath collision.",
                }
            }
        )

        self.assert_build_error(site_root, rule="duplicate-published-path", source_name="meta.toml")

    def test_file_and_folder_work_with_same_slug_fail_build(self) -> None:
        site_root = self.make_site(
            {
                "notes/alpha": {
                    "index.md": "# Folder Alpha\n\nA folder work.",
                }
            }
        )
        (site_root / "works" / "notes" / "alpha.md").write_text("# File Alpha\n\nA file work.", encoding="utf-8")

        self.assert_build_error(site_root, rule="duplicate-published-path", source_name="alpha")

    def test_multiple_body_files_fail_build(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "index.md": "# Opening\n\nA first note.",
                    "other.md": "# Other\n\nA second body.",
                }
            }
        )

        self.assert_build_error(site_root, rule="missing-required-field", source_name="alpha")

    def test_broken_internal_link_case(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "[Broken](/missing-path)",
                }
            }
        )

        self.assert_build_error(site_root, rule="broken-internal-link", source_name="index.md")

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

    def test_stylesheets_include_author_palette_and_derived_theme_tokens(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\nA first note.",
                }
            }
        )
        publish_root = site_root / "public"

        build_site(site_root, publish_root)

        for stylesheet_name in ("site.css", "feed.css"):
            stylesheet = (publish_root / stylesheet_name).read_text(encoding="utf-8")
            self.assertRegex(stylesheet, r"--theme-light-page: #[0-9a-fA-F]{6};")
            self.assertRegex(stylesheet, r"--theme-dark-page: #[0-9a-fA-F]{6};")
            self.assertRegex(stylesheet, r"rgba\(\d+,\d+,\d+,0\.38\)")
            self.assertRegex(stylesheet, r"rgba\(\d+,\d+,\d+,0\.48\)")
            self.assertNotIn("__THEME_", stylesheet)

    def test_cursor_colors_follow_changed_author_palette_during_build(self) -> None:
        source = textwrap.dedent(
            """\
            :root {
              --theme-light-page: #faf0e6;
              --theme-dark-page: #690000;
              --cursor-light: rgba(__THEME_DARK_PAGE_RGB__,0.38);
              --cursor-dark: rgba(__THEME_LIGHT_PAGE_RGB__,0.48);
            }
            """
        )

        rendered = render_theme_tokens(source, Path("tokens.css"))

        self.assertIn("--theme-dark-page: #690000;", rendered)
        self.assertIn("--cursor-light: rgba(105,0,0,0.38);", rendered)
        self.assertIn("--cursor-dark: rgba(250,240,230,0.48);", rendered)
        self.assertNotIn("__THEME_", rendered)

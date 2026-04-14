from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from labyrinth.markup import ResolvedWorkLink, render_html_body, render_markdown_body
from labyrinth.model import BuildError, build_site_graph, load_site_config, load_work_inputs

from .fixture_support import EXAMPLES_ROOT


class MarkupAndGraphTests(unittest.TestCase):
    def test_markdown_body_tracks_structured_links(self) -> None:
        body = render_markdown_body(
            "Read [[Garden Path]]. Compare [Turn](./garden-path#turn). Visit [Archive](https://archive.example). Stay [Here](#opening).",
            current_public_path="/field-notes",
            work_lookup={"garden path": ResolvedWorkLink(title="Garden Path", public_path="/garden-path")},
            work_paths={"/field-notes", "/garden-path"},
        )

        links = [(link.href, link.resolved_path, link.fragment, link.kind) for link in body.links]
        self.assertEqual(
            [
                ("/garden-path", "/garden-path", None, "work"),
                ("./garden-path#turn", "/garden-path", "turn", "work"),
                ("https://archive.example", None, None, "external"),
                ("#opening", "/field-notes", "opening", "internal"),
            ],
            links,
        )

    def test_html_body_tracks_structured_links(self) -> None:
        body = render_html_body(
            '<p><a href="./garden-path#turn">Turn</a> <a href="#note">Note</a> <a href="https://archive.example">Archive</a></p>',
            current_public_path="/field-notes",
            work_paths={"/field-notes", "/garden-path"},
        )

        links = [(link.href, link.resolved_path, link.fragment, link.kind) for link in body.links]
        self.assertEqual(
            [
                ("./garden-path#turn", "/garden-path", "turn", "work"),
                ("#note", "/field-notes", "note", "internal"),
                ("https://archive.example", None, None, "external"),
            ],
            links,
        )
        self.assertIn('class="internal-link work-link"', body.html)

    def test_rendered_internal_links_are_relative_to_the_current_page(self) -> None:
        markdown = render_markdown_body(
            "Read [[Garden Path]]. Compare [Turn](./garden-path#turn). Stay [Here](#opening).",
            current_public_path="/field-notes",
            work_lookup={"garden path": ResolvedWorkLink(title="Garden Path", public_path="/garden-path")},
            work_paths={"/field-notes", "/garden-path"},
        )
        html = render_html_body(
            '<p><a href="/garden-path#turn">Turn</a> <a href="#note">Note</a></p>',
            current_public_path="/field-notes",
            work_paths={"/field-notes", "/garden-path"},
        )

        self.assertIn('href="../garden-path"', markdown.html)
        self.assertIn('href="../garden-path#turn"', markdown.html)
        self.assertIn('href="#opening"', markdown.html)
        self.assertIn('href="../garden-path#turn"', html.html)
        self.assertIn('href="#note"', html.html)

    def test_site_graph_derives_sections_backlinks_and_lookup_maps(self) -> None:
        site = load_site_config(EXAMPLES_ROOT / "reading-microfeatures")
        graph = build_site_graph(site, load_work_inputs(EXAMPLES_ROOT / "reading-microfeatures"))

        self.assertEqual("Other works", graph.work_by_path["/field-notes"].resolved_section)
        self.assertEqual("materials", graph.work_by_path["/field-notes"].top_level_headings[0].anchor_id)
        self.assertIs(graph.contents_sections[0], graph.contents_section_by_name["Other works"])
        self.assertEqual(("/field-notes",), tuple(work.public_path for work in graph.backlinks["/garden-path"]))

    def test_site_graph_rejects_missing_heading_fragment(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\n',
                    "index.md": "# Opening\n\n[Broken](#missing)",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site_graph(load_site_config(site_root), load_work_inputs(site_root))

        self.assertEqual("broken-internal-link", error.exception.rule)
        self.assertIn("missing heading id", error.exception.message)

    def make_site(self, works: dict[str, dict[str, str]]) -> Path:
        site_root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (site_root / "site.toml").write_text(
            textwrap.dedent(
                """\
                url = "https://labyrinth.example"
                lang = "en"
                title = "Labyrinth"
                statement = "A room for poems, projects, and notes."

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

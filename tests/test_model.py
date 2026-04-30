from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from labyrinth.markup import BodyContext, ResolvedWorkLink, render_html_body, render_markdown_body
from labyrinth.model import BuildError, build_site_graph, load_site_config, load_work_inputs
from labyrinth.urls import PageUrls

from .fixture_support import EXAMPLES_ROOT


class MarkupAndGraphTests(unittest.TestCase):
    def test_markdown_body_tracks_structured_links(self) -> None:
        body = render_markdown_body(
            "Read [[Garden Path]]. Compare [Turn](./garden-path#turn). Visit [Archive](https://archive.example). Stay [Here](#opening).",
            context=self.body_context(),
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
            context=self.body_context(),
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
            context=self.body_context(),
        )
        html = render_html_body(
            '<p><a href="/garden-path#turn">Turn</a> <a href="#note">Note</a></p>',
            context=self.body_context(),
        )

        self.assertIn('href="../garden-path"', markdown.html)
        self.assertIn('href="../garden-path#turn"', markdown.html)
        self.assertIn('href="#opening"', markdown.html)
        self.assertIn('href="../garden-path#turn"', html.html)
        self.assertIn('href="#note"', html.html)

    def test_page_urls_derives_page_relative_and_feed_absolute_urls(self) -> None:
        urls = PageUrls(
            site_url="https://labyrinth.example/journal",
            build_url="http://localhost:8000/preview",
            public_path="/field-notes",
        )

        self.assertEqual("https://labyrinth.example/journal/field-notes", urls.canonical_url)
        self.assertEqual("http://localhost:8000/preview/field-notes", urls.output_url)
        self.assertEqual("http://localhost:8000/preview/field-notes/", urls.base_href)
        self.assertEqual("../garden-path", urls.relative_href("/garden-path"))
        self.assertEqual("../#contents", urls.relative_href("/", fragment="contents"))
        self.assertEqual("../feed.xml", urls.root_relative_href("/feed.xml"))
        self.assertEqual(
            "http://localhost:8000/preview/garden-path#turn",
            urls.absolute_href("../garden-path#turn"),
        )

    def test_site_graph_derives_sections_backlinks_and_lookup_maps(self) -> None:
        site = load_site_config(EXAMPLES_ROOT / "reading-microfeatures")
        graph = build_site_graph(site, load_work_inputs(EXAMPLES_ROOT / "reading-microfeatures"))

        self.assertEqual("Other works", graph.work_by_path["/field-notes"].resolved_section)
        self.assertEqual("materials", graph.work_by_path["/field-notes"].top_level_headings[0].anchor_id)
        self.assertIs(graph.contents_sections[0], graph.contents_section_by_name["Other works"])
        self.assertEqual(("/field-notes",), tuple(work.public_path for work in graph.backlinks["/garden-path"]))

    def test_site_graph_treats_fixed_public_files_as_known_paths(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\n[Styles](/site.css) and [Feed styles](/feed.css).",
                }
            }
        )

        graph = build_site_graph(load_site_config(site_root), load_work_inputs(site_root))

        self.assertIn("/site.css", graph.known_paths)
        self.assertIn("/feed.css", graph.known_paths)
        self.assertIn('href="../site.css"', graph.work_by_path["/alpha"].body.html)
        self.assertIn('href="../feed.css"', graph.work_by_path["/alpha"].body.html)

    def test_home_markdown_defines_links_and_sections(self) -> None:
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
        (site_root / "home.md").write_text(
            textwrap.dedent(
                """\
                # Labyrinth Home

                Visible cover line.

                [Email](mailto:hello@labyrinth.example)
                [Gift](https://gifts.example/labyrinth)
                [RSS](/feed.xml)

                ## Read

                ### Notes

                ### Guides
                Reusable methods.
                """
            ),
            encoding="utf-8",
        )

        site = load_site_config(site_root)
        graph = build_site_graph(site, load_work_inputs(site_root))

        self.assertEqual("Labyrinth Home", site.home.title)
        self.assertEqual(("Email", "Gift", "RSS"), tuple(link.label for link in site.home.links))
        self.assertEqual(("", "Reusable methods."), tuple(section.description for section in site.home.sections))
        self.assertEqual(("Notes", "Guides"), tuple(section.name for section in graph.contents_sections))
        self.assertEqual("", graph.contents_sections[0].description)
        self.assertEqual("Reusable methods.", graph.contents_sections[1].description)
        self.assertEqual((), graph.contents_sections[1].works)

    def test_site_graph_groups_contents_sections_in_one_configured_order(self) -> None:
        site_root = self.make_site(
            {
                "alpha-note": {
                    "meta.toml": (
                        'created = "2024-02-16T00:00:00Z"\n'
                        'updated = "2024-02-16T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/alpha-note"\n'
                        'section = "Notes"\n'
                    ),
                    "index.md": "# Alpha\n\nA note.",
                },
                "beta-essay": {
                    "meta.toml": (
                        'created = "2024-02-15T00:00:00Z"\n'
                        'updated = "2024-02-15T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/beta-essay"\n'
                        'section = "Essays"\n'
                    ),
                    "index.md": "# Beta\n\nAn essay.",
                },
                "loose-map": {
                    "meta.toml": (
                        'created = "2024-02-14T00:00:00Z"\n'
                        'updated = "2024-02-14T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/loose-map"\n'
                    ),
                    "index.md": "# Loose\n\nA fallback work.",
                },
            }
        )
        home_md = site_root / "home.md"
        home_md.write_text(
            home_md.read_text(encoding="utf-8").replace(
                "## Read",
                "## Read\n\n### Essays\n\n### Notes\n\n### Empty",
            ),
            encoding="utf-8",
        )

        graph = build_site_graph(load_site_config(site_root), load_work_inputs(site_root))

        self.assertEqual(
            ("Essays", "Notes", "Empty", "Other works"),
            tuple(section.name for section in graph.contents_sections),
        )
        self.assertEqual(
            ("Beta Essay",),
            tuple(work.title for work in graph.contents_section_by_name["Essays"].works),
        )
        self.assertEqual(
            ("Alpha Note",),
            tuple(work.title for work in graph.contents_section_by_name["Notes"].works),
        )
        self.assertEqual((), graph.contents_section_by_name["Empty"].works)
        self.assertEqual(
            ("Loose Map",),
            tuple(work.title for work in graph.contents_section_by_name["Other works"].works),
        )

    def test_site_graph_rejects_missing_heading_fragment(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\n[Broken](#missing)",
                }
            }
        )

        with self.assertRaises(BuildError) as error:
            build_site_graph(load_site_config(site_root), load_work_inputs(site_root))

        self.assertEqual("broken-internal-link", error.exception.rule)
        self.assertIn("missing heading id", error.exception.message)

    def body_context(self) -> BodyContext:
        return BodyContext(
            current_public_path="/field-notes",
            work_lookup={
                "garden path": ResolvedWorkLink(
                    title="Garden Path",
                    public_path="/garden-path",
                ),
            },
            work_paths=frozenset({"/field-notes", "/garden-path"}),
        )

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

                [Email](mailto:hello@labyrinth.example)
                [Gift](https://gifts.example/labyrinth)
                [RSS](/feed.xml)

                ## Read
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

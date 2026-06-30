from __future__ import annotations

from datetime import UTC, datetime
import os
import textwrap

from labyrinth.markup import BodyContext, ResolvedWorkLink, render_html_body, render_markdown_body
from labyrinth.model import BuildError, build_site_graph, load_site_config, load_work_inputs
from labyrinth.urls import PageUrls

from .fixture_support import FixtureSiteTestCase


class MarkupAndGraphTests(FixtureSiteTestCase):
    def build_graph(self, site_root):
        site = load_site_config(site_root)
        return build_site_graph(site, load_work_inputs(site_root, site.home.sections))

    def test_markdown_body_tracks_structured_links(self) -> None:
        body = render_markdown_body(
            "See [[Garden Path]]. Compare [Turn](./garden-path#turn). Visit [Archive](https://archive.example). Stay [Here](#opening).",
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

    def test_rendered_internal_links_are_relative_to_the_current_page(self) -> None:
        markdown = render_markdown_body(
            "See [[Garden Path]]. Compare [Turn](./garden-path#turn). Stay [Here](#opening).",
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
        site_root = self.make_site(
            {
                "source-work": {
                    "meta.toml": 'created = "2024-02-15T00:00:00Z"\nupdated = "2024-02-15T00:00:00Z"\natom_id = "https://labyrinth.example/id/source-work"\n',
                    "index.md": "# Source Heading\n\nSee [[target-work]].",
                },
                "target-work": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/target-work"\n',
                    "index.md": "# Target Heading\n\nA destination.",
                },
            }
        )

        graph = self.build_graph(site_root)
        source = graph.work_by_path["/source-work"]
        target = graph.work_by_path["/target-work"]

        self.assertEqual(graph.contents_sections[0].name, source.resolved_section)
        self.assertEqual("source-heading", source.top_level_headings[0].anchor_id)
        self.assertIs(graph.contents_sections[0], graph.contents_section_by_name[source.resolved_section])
        self.assertEqual((source.public_path,), tuple(work.public_path for work in graph.backlinks[target.public_path]))

    def test_site_graph_resolves_fixed_public_file_links(self) -> None:
        site_root = self.make_site(
            {
                "alpha": {
                    "meta.toml": 'created = "2024-02-14T00:00:00Z"\nupdated = "2024-02-14T00:00:00Z"\natom_id = "https://labyrinth.example/id/alpha"\n',
                    "index.md": "# Opening\n\n[Styles](/site.css) and [Feed styles](/feed.css).",
                }
            }
        )

        graph = self.build_graph(site_root)

        self.assertIn('href="../site.css"', graph.work_by_path["/alpha"].body.html)
        self.assertIn('href="../feed.css"', graph.work_by_path["/alpha"].body.html)

    def test_direct_markdown_file_derives_work_defaults(self) -> None:
        site_root = self.make_site({})
        self.set_home_sections(site_root, "### Poems")
        poems_root = site_root / "works" / "poems"
        poems_root.mkdir()
        body_path = poems_root / "know.md"
        body_path.write_text("# Opening\n\nA poem.", encoding="utf-8")
        os.utime(body_path, (1_700_000_000, 1_700_000_000))

        graph = self.build_graph(site_root)
        work = graph.work_by_path["/know"]

        self.assertEqual("Know", work.title)
        self.assertEqual("Poems", work.resolved_section)
        self.assertEqual("https://labyrinth.example/id/know", work.atom_id)
        self.assertEqual(datetime.fromtimestamp(1_700_000_000, tz=UTC), work.created)
        self.assertIn("<p>A poem.</p>", work.body.html)

    def test_toml_front_matter_overrides_work_metadata(self) -> None:
        site_root = self.make_site(
            {
                "notes/source-note": {
                    "index.md": (
                        "+++\n"
                        'created = "2024-02-16T00:00:00Z"\n'
                        'updated = "2024-02-17T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/custom-source"\n'
                        'aliases = ["Origin"]\n'
                        "+++\n"
                        "# Source\n\nSee [[Origin]]."
                    ),
                }
            }
        )
        self.set_home_sections(site_root, "### Notes")

        graph = self.build_graph(site_root)
        work = graph.work_by_path["/source-note"]

        self.assertEqual(datetime(2024, 2, 16, tzinfo=UTC), work.created)
        self.assertEqual(datetime(2024, 2, 17, tzinfo=UTC), work.updated)
        self.assertEqual("https://labyrinth.example/id/custom-source", work.atom_id)
        self.assertEqual("/source-note", graph.work_lookup["origin"].public_path)
        self.assertNotIn("created =", work.body.html)

    def test_direct_html_file_uses_toml_front_matter(self) -> None:
        site_root = self.make_site({})
        html_path = site_root / "works" / "artifact.html"
        html_path.write_text(
            '+++\ncreated = "2024-02-16T00:00:00Z"\n+++\n<p>Authored HTML.</p>',
            encoding="utf-8",
        )

        graph = self.build_graph(site_root)
        work = graph.work_by_path["/artifact"]

        self.assertEqual(datetime(2024, 2, 16, tzinfo=UTC), work.created)
        self.assertEqual("<p>Authored HTML.</p>", work.body.html)

    def test_folder_work_accepts_one_arbitrary_markdown_body(self) -> None:
        site_root = self.make_site(
            {
                "poems/know": {
                    "know.md": "# Opening\n\nA poem.",
                }
            }
        )
        self.set_home_sections(site_root, "### Poems")

        graph = self.build_graph(site_root)

        self.assertEqual("Poems", graph.work_by_path["/know"].resolved_section)
        self.assertIn("<p>A poem.</p>", graph.work_by_path["/know"].body.html)

    def test_direct_folder_work_accepts_one_arbitrary_markdown_body(self) -> None:
        site_root = self.make_site(
            {
                "field-notes": {
                    "notes.md": "# Opening\n\nA direct folder work.",
                }
            }
        )

        graph = self.build_graph(site_root)

        self.assertIn("<p>A direct folder work.</p>", graph.work_by_path["/field-notes"].body.html)

    def test_home_markdown_defines_links_and_sections(self) -> None:
        site_root = self.make_site(
            {
                "notes/alpha": {
                    "meta.toml": (
                        'created = "2024-02-14T00:00:00Z"\n'
                        'updated = "2024-02-14T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/alpha"\n'
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

                [First](https://first.example/labyrinth)
                [Second](https://second.example/labyrinth)
                [Feed](/feed.xml)

                ## Library

                ### Notes

                ### Guides
                Reusable methods.
                """
            ),
            encoding="utf-8",
        )

        site = load_site_config(site_root)
        graph = build_site_graph(site, load_work_inputs(site_root, site.home.sections))

        self.assertEqual("Labyrinth Home", site.home.title)
        self.assertEqual("Library", site.home.read_label)
        self.assertEqual(("First", "Second", "Feed"), tuple(link.label for link in site.home.links))
        self.assertEqual(("", "Reusable methods."), tuple(section.description for section in site.home.sections))
        self.assertEqual(("Notes", "Guides"), tuple(section.name for section in graph.contents_sections))
        self.assertEqual("", graph.contents_sections[0].description)
        self.assertEqual("Reusable methods.", graph.contents_sections[1].description)
        self.assertEqual((), graph.contents_sections[1].works)

    def test_site_graph_groups_contents_sections_in_one_configured_order(self) -> None:
        site_root = self.make_site(
            {
                "shelf-one/alpha-note": {
                    "meta.toml": (
                        'created = "2024-02-16T00:00:00Z"\n'
                        'updated = "2024-02-16T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/alpha-note"\n'
                    ),
                    "index.md": "# Alpha\n\nA note.",
                },
                "shelf-two/beta-essay": {
                    "meta.toml": (
                        'created = "2024-02-15T00:00:00Z"\n'
                        'updated = "2024-02-15T00:00:00Z"\n'
                        'atom_id = "https://labyrinth.example/id/beta-essay"\n'
                    ),
                    "index.md": "# Beta\n\nAn essay.",
                },
                "maps/loose-map": {
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
                "## Index",
                "## Library\n\n### Shelf Two\n\n### Shelf One\n\n### Empty Shelf",
            ),
            encoding="utf-8",
        )

        graph = self.build_graph(site_root)

        self.assertEqual(
            ("Shelf Two", "Shelf One", "Empty Shelf"),
            tuple(section.name for section in graph.contents_sections[:3]),
        )
        self.assertEqual(
            ("Beta Essay",),
            tuple(work.title for work in graph.contents_section_by_name["Shelf Two"].works),
        )
        self.assertEqual(
            ("Alpha Note",),
            tuple(work.title for work in graph.contents_section_by_name["Shelf One"].works),
        )
        self.assertEqual((), graph.contents_section_by_name["Empty Shelf"].works)
        fallback_sections = [
            section
            for section in graph.contents_sections
            if tuple(work.public_path for work in section.works) == ("/loose-map",)
        ]
        self.assertEqual(1, len(fallback_sections))

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
            self.build_graph(site_root)

        self.assertEqual("broken-internal-link", error.exception.rule)

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

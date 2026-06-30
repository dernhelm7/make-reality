from __future__ import annotations

from html import escape
import tempfile
from pathlib import Path

from labyrinth.builder import build_site
from labyrinth.model import SiteGraph, WorkDocument, build_site_graph, load_site_config, load_work_inputs
from labyrinth.urls import PageUrls

from .fixture_support import (
    FixtureSiteTestCase,
    REPO_ROOT,
)


GRAPH_FIXTURES = (
    "minimal-markdown",
    "named-sections",
    "section-fallback",
    "html-work",
    "reading-microfeatures",
    "wikilinks-and-assets",
)


class AcceptanceTests(FixtureSiteTestCase):
    def build_fixture_graph(self, fixture_name: str) -> tuple[Path, Path, SiteGraph]:
        site_root, publish_root = self.build_fixture(fixture_name)
        site = load_site_config(site_root)
        graph = build_site_graph(site, load_work_inputs(site_root, site.home.sections))
        return site_root, publish_root, graph

    def assert_all_in(self, text: str, needles: list[str]) -> None:
        for needle in needles:
            self.assertIn(needle, text)

    def assert_home_is_functional(self, publish_root: Path, graph: SiteGraph) -> None:
        home_page = self.page_text(publish_root, "/")
        self.assert_all_in(
            home_page,
            [
                "<!DOCTYPE html>",
                f'<base href="{escape(graph.site.site_url)}/">',
                'rel="alternate" type="application/atom+xml"',
                'href="./#contents"',
                'id="contents"',
                escape(graph.site.home.title),
                escape(graph.site.home.read_label),
            ],
        )

        for link in graph.site.home.links:
            self.assertIn(escape(link.label), home_page)
        for section in graph.contents_sections:
            self.assertIn(escape(section.name), home_page)
            for work in section.works:
                self.assertIn(f'href="{escape(work.public_path.strip("/"))}"', home_page)
                self.assertIn(escape(work.title), home_page)

    def assert_work_page_is_functional(
        self,
        publish_root: Path,
        graph: SiteGraph,
        work: WorkDocument,
    ) -> None:
        work_page = self.page_text(publish_root, work.public_path)
        urls = PageUrls(site_url=graph.site.site_url, build_url=graph.site.build_url, public_path=work.public_path)

        self.assert_all_in(
            work_page,
            [
                "<!DOCTYPE html>",
                f'<base href="{escape(urls.base_href)}">',
                f'<link rel="canonical" href="{escape(urls.canonical_url)}">',
                'id="work-top"',
                escape(work.title),
                escape(work.created.isoformat()),
                escape(work.resolved_section),
            ],
        )

        current_section = graph.contents_section_by_name.get(work.resolved_section)
        if current_section is not None:
            self.assertIn(
                f'href="{escape(urls.relative_href("/", fragment=current_section.anchor_id))}"',
                work_page,
            )

        if work.body.html:
            first_rendered_line = next(line for line in work.body.html.splitlines() if line.strip())
            self.assertIn(first_rendered_line, work_page)
        for heading in work.top_level_headings:
            self.assertIn(f'id="{escape(heading.anchor_id)}"', work_page)
            self.assertIn(f'href="#{escape(heading.anchor_id)}"', work_page)
        for target_path in work.outbound_work_paths:
            target = graph.work_by_path[target_path]
            self.assertIn(f'href="{escape(urls.relative_href(target.public_path))}"', work_page)
        for source in graph.backlinks.get(work.public_path, ()):
            self.assertIn(f'href="{escape(urls.relative_href(source.public_path))}"', work_page)

    def assert_feed_is_functional(self, publish_root: Path, graph: SiteGraph) -> None:
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")
        self.assert_all_in(
            feed,
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?xml-stylesheet type="text/css" href="feed.css"?>',
                '<feed xmlns="http://www.w3.org/2005/Atom">',
                f"<id>{escape(graph.site.site_url)}/feed.xml</id>",
                f'<link rel="self" type="application/atom+xml" href="{escape(graph.site.build_url)}/feed.xml"/>',
                f'<link rel="alternate" type="text/html" href="{escape(graph.site.build_url)}"/>',
            ],
        )
        self.assertNotIn("<rss", feed)
        self.assertNotIn('type="text/xsl"', feed)
        self.assertFalse((publish_root / "feed.xsl").exists())

        for work in graph.works:
            self.assertIn(f"<id>{escape(work.atom_id)}</id>", feed)
            self.assertIn(f'href="{escape(graph.site.build_url + work.public_path)}"', feed)

    def test_example_fixtures_build_functional_public_sites(self) -> None:
        for fixture_name in GRAPH_FIXTURES:
            with self.subTest(fixture=fixture_name):
                _, publish_root, graph = self.build_fixture_graph(fixture_name)
                self.assert_common_public_layout(publish_root, [work.public_path for work in graph.works])
                self.assert_home_is_functional(publish_root, graph)
                for work in graph.works:
                    self.assert_work_page_is_functional(publish_root, graph, work)
                self.assert_feed_is_functional(publish_root, graph)

    def test_starter_site_builds_functional_public_site(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        build_site(REPO_ROOT / "site", publish_root)

        self.assertTrue((publish_root / "index.html").is_file())
        self.assertTrue((publish_root / "write" / "index.html").is_file())
        self.assertTrue((publish_root / "feed.xml").is_file())
        self.assertTrue((publish_root / "feed.css").is_file())
        self.assertTrue((publish_root / "site.css").is_file())
        self.assertEqual([], list(publish_root.rglob("*.js")))

        home_page = (publish_root / "index.html").read_text(encoding="utf-8")
        write_page = (publish_root / "write" / "index.html").read_text(encoding="utf-8")
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")

        self.assert_all_in(home_page, ["Lay the Land", "Read", "Follow", "Write"])
        self.assert_all_in(
            write_page,
            [
                'id="write"',
                "https://tally.so/embed/7RJ6Z2",
                "https://tally.so/widgets/embed.js",
                ">Write</a>",
            ],
        )
        self.assertIn('href="https://dernhelm7.github.io/make-reality/write">Write</xhtml:a>', feed)

    def test_markdown_work_assets_are_published(self) -> None:
        site_root, publish_root = self.make_fixture("minimal-markdown")
        home_path = site_root / "home.md"
        home_path.write_text(
            home_path.read_text(encoding="utf-8").replace("## Read", "## Read\n\n### Notes\nsleep notes"),
            encoding="utf-8",
        )
        work_dir = site_root / "works" / "notes" / "hypnosis"
        work_dir.mkdir(parents=True)
        (work_dir / "Hypnosis.md").write_text(
            (
                "+++\n"
                'created = "2024-02-14T00:00:00Z"\n'
                'updated = "2024-02-14T00:00:00Z"\n'
                "+++\n"
                "# Opening\n\n"
                "- First\n"
                "- Second\n\n"
                "![](./out_of_the_dark_world_32.png)\n"
            ),
            encoding="utf-8",
        )
        (work_dir / "out_of_the_dark_world_32.png").write_bytes(b"image bytes")

        build_site(site_root, publish_root)
        work_page = self.page_text(publish_root, "/hypnosis")

        self.assertIn("<ul>", work_page)
        self.assertIn("<li>Second</li>", work_page)
        self.assertIn('<img src="out_of_the_dark_world_32.png" alt=""', work_page)
        self.assertEqual(b"image bytes", (publish_root / "hypnosis" / "out_of_the_dark_world_32.png").read_bytes())

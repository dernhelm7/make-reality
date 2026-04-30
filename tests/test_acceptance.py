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
    tree_digest,
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
        graph = build_site_graph(load_site_config(site_root), load_work_inputs(site_root))
        return site_root, publish_root, graph

    def assert_all_in(self, text: str, needles: list[str]) -> None:
        for needle in needles:
            self.assertIn(needle, text)

    def assert_ordered(self, text: str, needles: list[str]) -> None:
        cursor = -1
        for needle in needles:
            index = text.index(needle)
            self.assertGreater(index, cursor)
            cursor = index

    def assert_home_reflects_graph(self, publish_root: Path, graph: SiteGraph) -> None:
        home_page = self.page_text(publish_root, "/")
        self.assert_all_in(
            home_page,
            [
                f'<base href="{escape(graph.site.site_url)}/">',
                'rel="alternate" type="application/atom+xml"',
                escape(graph.site.home.title),
                escape(graph.site.home.read_label),
            ],
        )
        for link in graph.site.home.links:
            self.assertIn(escape(link.label), home_page)
        self.assert_ordered(home_page, [escape(section.name) for section in graph.contents_sections])
        for section in graph.contents_sections:
            self.assertIn(escape(section.name), home_page)
            if section.description:
                self.assertIn(escape(section.description), home_page)
            for work in section.works:
                self.assertLess(
                    home_page.index(escape(section.name)),
                    home_page.index(escape(work.title)),
                )
        for work in graph.works:
            self.assertIn(f'href="{escape(work.public_path.strip("/"))}"', home_page)
            self.assertIn(escape(work.title), home_page)

    def assert_work_reflects_graph(self, publish_root: Path, graph: SiteGraph, work: WorkDocument) -> None:
        work_page = self.page_text(publish_root, work.public_path)
        urls = PageUrls(site_url=graph.site.site_url, build_url=graph.site.build_url, public_path=work.public_path)
        self.assert_all_in(
            work_page,
            [
                f'<base href="{escape(urls.base_href)}">',
                escape(work.title),
                escape(work.created.isoformat()),
                f'href="{escape(urls.relative_href("/", fragment="contents"))}"',
            ],
        )
        if work.body.html:
            self.assertIn(work.body.html.splitlines()[0], work_page)
        for heading in work.top_level_headings:
            self.assertIn(f'id="{escape(heading.anchor_id)}"', work_page)
            self.assertIn(f'href="#{escape(heading.anchor_id)}"', work_page)
        self.assertIn(escape(work.resolved_section), work_page)
        self.assert_work_links_reflect_graph(work_page, graph, work)
        self.assert_backlinks_reflect_graph(publish_root, graph, work)

    def assert_feed_reflects_graph(self, publish_root: Path, graph: SiteGraph) -> None:
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")
        self.assert_all_in(
            feed,
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<?xml-stylesheet type="text/xsl" href="feed.xsl"?>',
                '<feed xmlns="http://www.w3.org/2005/Atom">',
                f"<id>{escape(graph.site.site_url)}/feed.xml</id>",
                f'<link rel="self" type="application/atom+xml" href="{escape(graph.site.build_url)}/feed.xml"/>',
                f'<link rel="alternate" type="text/html" href="{escape(graph.site.build_url)}"/>',
            ],
        )
        self.assertNotIn("<rss", feed)
        feed_transform = (publish_root / "feed.xsl").read_text(encoding="utf-8")
        self.assert_all_in(feed_transform, ['<meta name="viewport"', 'href="feed.css"'])
        for work in graph.works:
            self.assert_all_in(
                feed,
                [
                    f"<id>{escape(work.atom_id)}</id>",
                    f"<published>{work.created.strftime('%Y-%m-%dT%H:%M:%SZ')}</published>",
                    f"<updated>{work.updated.strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>",
                    f'href="{escape(graph.site.build_url + work.public_path)}"',
                ],
            )
            for link in work.body.links:
                if link.kind == "work" and link.resolved_path:
                    target = graph.work_by_path[link.resolved_path]
                    self.assertIn(escape(f'href="{graph.site.build_url + target.public_path}"', quote=True), feed)
                if link.kind == "external":
                    self.assertIn(escape(f'href="{link.href}"', quote=True), feed)

    def assert_work_links_reflect_graph(self, work_page: str, graph: SiteGraph, work: WorkDocument) -> None:
        urls = PageUrls(graph.site.site_url, graph.site.build_url, work.public_path)
        for target_path in work.outbound_work_paths:
            target = graph.work_by_path[target_path]
            self.assertIn(f'href="{escape(urls.relative_href(target.public_path))}"', work_page)
            self.assertIn(escape(target.title), work_page)

    def assert_backlinks_reflect_graph(self, publish_root: Path, graph: SiteGraph, work: WorkDocument) -> None:
        target_urls = PageUrls(graph.site.site_url, graph.site.build_url, work.public_path)
        work_page = self.page_text(publish_root, work.public_path)
        for source in graph.backlinks.get(work.public_path, ()):
            self.assertIn(f'href="{escape(target_urls.relative_href(source.public_path))}"', work_page)
            self.assertIn(escape(source.title), work_page)

    def test_build_url_override_keeps_canonical_urls_and_rewrites_preview_targets(self) -> None:
        site_root, publish_root = self.make_fixture("minimal-markdown")
        build_url = "http://localhost:8009/preview"

        build_site(site_root, publish_root, build_url=build_url)
        graph = build_site_graph(load_site_config(site_root, build_url=build_url), load_work_inputs(site_root))
        work = graph.works[0]
        heading = work.top_level_headings[0]
        work_page = self.page_text(publish_root, work.public_path)
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")

        self.assert_all_in(
            work_page,
            [
                f'<base href="{escape(build_url + work.public_path)}/">',
                f'<link rel="canonical" href="{escape(graph.site.site_url + work.public_path)}">',
            ],
        )
        self.assert_all_in(
            feed,
            [
                f"<id>{escape(graph.site.site_url)}/feed.xml</id>",
                f'<link rel="self" type="application/atom+xml" href="{escape(build_url)}/feed.xml"/>',
                f'<link rel="alternate" type="text/html" href="{escape(build_url)}"/>',
                f"<id>{escape(work.atom_id)}</id>",
                f'<link rel="alternate" type="text/html" href="{escape(build_url + work.public_path)}"/>',
                f"{escape(build_url + work.public_path)}#{escape(heading.anchor_id)}",
            ],
        )

    def test_rendered_public_urls_are_relative_to_the_current_page(self) -> None:
        site_root, publish_root = self.make_fixture("reading-microfeatures")
        site_toml = site_root / "site.toml"
        site_toml.write_text(
            site_toml.read_text(encoding="utf-8").replace(
                'url = "https://labyrinth.example"',
                'url = "https://labyrinth.example/journal"',
                1,
            ),
            encoding="utf-8",
        )

        build_site(site_root, publish_root)
        graph = build_site_graph(load_site_config(site_root), load_work_inputs(site_root))
        source_work = next(work for work in graph.works if work.outbound_work_paths)
        target_path = sorted(source_work.outbound_work_paths)[0]
        urls = PageUrls(graph.site.site_url, graph.site.build_url, source_work.public_path)
        home_page = self.page_text(publish_root, "/")
        work_page = self.page_text(publish_root, source_work.public_path)

        self.assert_all_in(
            home_page,
            [
                f'<base href="{escape(graph.site.site_url)}/">',
                'href="site.css"',
                'href="feed.xml"',
                f'href="{escape(source_work.public_path.strip("/"))}"',
                'rel="alternate" type="application/atom+xml"',
            ],
        )
        self.assert_all_in(
            work_page,
            [
                f'<base href="{escape(urls.base_href)}">',
                f'href="{escape(urls.relative_href("/", fragment="contents"))}"',
                f'href="{escape(urls.relative_href(target_path))}"',
                f'<link rel="canonical" href="{escape(urls.canonical_url)}">',
            ],
        )

    def test_example_fixtures_reflect_their_source_graphs(self) -> None:
        for fixture_name in GRAPH_FIXTURES:
            with self.subTest(fixture=fixture_name):
                _, publish_root, graph = self.build_fixture_graph(fixture_name)
                self.assert_common_public_layout(publish_root, [work.public_path for work in graph.works])
                self.assert_home_reflects_graph(publish_root, graph)
                for work in graph.works:
                    self.assert_work_reflects_graph(publish_root, graph, work)
                self.assert_feed_reflects_graph(publish_root, graph)

    def test_starter_site_builds_without_snapshotting_author_copy(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        build_site(REPO_ROOT / "site", publish_root)

        self.assertTrue((publish_root / "index.html").is_file())
        self.assertTrue((publish_root / "feed.xml").is_file())
        self.assertTrue((publish_root / "feed.xsl").is_file())
        self.assertTrue((publish_root / "feed.css").is_file())
        self.assertTrue((publish_root / "site.css").is_file())
        self.assertEqual([], list(publish_root.rglob("*.js")))

    def test_publish_root_is_deterministic(self) -> None:
        first_root = self.build_fixture("minimal-markdown")[1]
        second_root = self.build_fixture("minimal-markdown")[1]

        self.assertEqual(tree_digest(first_root), tree_digest(second_root))
        self.assertEqual((first_root / "site.css").read_bytes(), (second_root / "site.css").read_bytes())

    def test_rebuild_removes_stale_files(self) -> None:
        site_root, publish_root = self.build_fixture("minimal-markdown")
        stale = publish_root / "stale.txt"
        stale.write_text("leftover", encoding="utf-8")

        build_site(site_root, publish_root)

        self.assertFalse(stale.exists())

    def test_publish_root_contains_only_public_files(self) -> None:
        _, publish_root = self.build_fixture("reading-microfeatures")
        files = sorted(path.relative_to(publish_root).as_posix() for path in publish_root.rglob("*") if path.is_file())
        self.assertIn("feed.xml", files)
        self.assertIn("feed.xsl", files)
        self.assertIn("feed.css", files)
        self.assertIn("site.css", files)
        self.assertTrue(any(path.startswith("fonts/") and path.endswith(".woff") for path in files))
        self.assertNotIn("site.js", files)
        for path in files:
            self.assertTrue(
                path == "feed.xml"
                or path == "feed.xsl"
                or path == "feed.css"
                or path == "site.css"
                or path.startswith("fonts/")
                or path.endswith("/index.html")
                or path == "index.html"
            )

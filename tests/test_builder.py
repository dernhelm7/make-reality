from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import labyrinth.builder as builder
from labyrinth.builder import BuildError


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "agent_docs" / "examples"
ET_BOOK_ROMAN = "fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff"
ET_BOOK_ITALIC = (
    "fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff"
)
ET_BOOK_BOLD = "fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff"
ET_BOOK_LICENSE = "fonts/et-book/LICENSE.txt"


class BuilderTests(unittest.TestCase):
    def make_fixture(self, fixture_name: str) -> tuple[Path, Path, tempfile.TemporaryDirectory]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        site_root = Path(temp_dir.name) / "site"
        publish_root = Path(temp_dir.name) / "publish"
        shutil.copytree(EXAMPLES_ROOT / fixture_name, site_root)
        return site_root, publish_root, temp_dir

    def build_fixture(self, fixture_name: str) -> tuple[Path, Path, builder.BuildResult]:
        site_root, publish_root, _ = self.make_fixture(fixture_name)
        result = builder.build_site(site_root, publish_root)
        return site_root, publish_root, result

    def page_text(self, publish_root: Path, public_path: str) -> str:
        if public_path == "/":
            candidate = publish_root / "index.html"
        else:
            candidate = publish_root / public_path.lstrip("/")
            if candidate.is_dir():
                candidate = candidate / "index.html"
            elif not candidate.exists():
                html_candidate = candidate.with_suffix(".html")
                if html_candidate.exists():
                    candidate = html_candidate
        return candidate.read_text()

    def snapshot(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

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

    def test_minimal_markdown_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("minimal-markdown")
        self.assert_common_public_layout(publish_root, ["/first-room"])

        home_html = self.page_text(publish_root, "/")
        work_html = self.page_text(publish_root, "/first-room")
        styles = (publish_root / "site.css").read_text()

        self.assertIn('page-head', home_html)
        self.assertNotIn('page-rule', home_html)
        self.assertIn('page-deck', home_html)
        self.assertIn('class="site-sidebar"', home_html)
        self.assertIn('class="site-bar"', home_html)
        self.assertIn('site-nav--primary', home_html)
        self.assertIn('href="#contents">Content</a>', home_html)
        self.assertIn('href="#contents">Enter the content</a>', home_html)
        self.assertIn('id="contents"', home_html)
        self.assertIn('>Contents</h2>', home_html)
        self.assertIn('href="/first-room"', home_html)
        self.assertNotIn('href="/works">Content</a>', home_html)
        self.assertIn('site-nav--global', home_html)
        self.assertIn('site-bar-section--global', home_html)
        self.assertIn('class="site-global-label visually-hidden"', home_html)
        self.assertIn('site-title-link--placeholder', home_html)
        self.assertNotIn('<a class="site-title-link"', home_html)
        self.assertNotIn('site-header', home_html)
        self.assertNotIn('site-footer', home_html)
        self.assertNotIn('<p class="site-global-label">Links</p>', home_html)
        self.assertNotIn('<p class="page-kicker">Table of contents</p>', home_html)
        self.assertIn(">Other works</h2>", home_html)
        self.assertIn('<h1 class="page-title work-title p-name">First Room</h1>', work_html)
        self.assertIn("Other works", work_html)
        self.assertNotIn('page-kicker work-meta', work_html)
        self.assertIn('<aside class="work-date-note" aria-label="Published">', work_html)
        self.assertIn('<time class="work-date dt-published" datetime="2024-02-14T00:00:00+00:00">14 February 2024</time>', work_html)
        self.assertLess(work_html.index('<aside class="work-date-note" aria-label="Published">'), work_html.index('<div class="page-body">'))
        self.assertIn('<a class="site-back-link" href="/#contents">Back to contents</a>', work_html)
        self.assertIn('site-bar-section--contents', work_html)
        self.assertIn('<section class="site-contents-group site-contents-group--current">', work_html)
        self.assertIn('<p class="site-contents-summary">Other works</p>', work_html)
        self.assertNotIn("<details", work_html)
        self.assertNotIn("<summary", work_html)
        self.assertIn('<span class="site-contents-current" aria-current="page">First Room</span>', work_html)
        self.assertNotIn('class="site-contents-link"', work_html)
        self.assertNotIn('site-work-headings-list', work_html)
        self.assertNotIn('site-nav--primary', work_html)
        self.assertIn('reading-prose', work_html)
        self.assertIn('id="opening"', work_html)
        self.assertIn('href="#opening">Opening</a>', work_html)
        self.assertNotIn('aria-label="On this page"', work_html)
        self.assertNotIn('page-rule', work_html)
        self.assertIn('class="works-entry"', home_html)
        self.assertIn("Other works", home_html)
        self.assertIn('href="/first-room"', home_html)
        self.assertIn(">First Room<", home_html)
        self.assertIn('<link rel="alternate" type="application/rss+xml"', home_html)
        self.assertIn('@font-face {', styles)
        self.assertIn(
            'src: url("/fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff") format("woff");',
            styles,
        )
        self.assertIn('font-display: swap;', styles)

    def test_named_sections_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("named-sections")
        self.assert_common_public_layout(publish_root, ["/essay-fragment", "/folded-map"])

        home_html = self.page_text(publish_root, "/")
        work_html = self.page_text(publish_root, "/folded-map")
        self.assertIn('class="works-entry"', home_html)
        self.assertIn('>Essays</h2>', home_html)
        self.assertIn('>Projects</h2>', home_html)
        self.assertIn('href="/essay-fragment"', home_html)
        self.assertIn(">Essay Fragment<", home_html)
        self.assertIn('href="/folded-map"', home_html)
        self.assertIn(">Folded Map<", home_html)
        self.assertNotIn('Other works', home_html)
        self.assertIn(
            '<section class="site-contents-group site-contents-group--current"><p class="site-contents-summary">Projects</p>',
            work_html,
        )
        self.assertIn('<span class="site-contents-current" aria-current="page">Folded Map</span>', work_html)
        self.assertNotIn("<details", work_html)
        self.assertNotIn("<summary", work_html)
        self.assertNotIn('<p class="site-contents-summary">Essays</p>', work_html)
        self.assertNotIn('class="site-link site-contents-link" href="/essay-fragment">Essay Fragment</a>', work_html)

    def test_section_fallback_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("section-fallback")
        self.assert_common_public_layout(publish_root, ["/night-walk"])

        home_html = self.page_text(publish_root, "/")
        self.assertIn('>Other works</h2>', home_html)
        self.assertIn('href="/night-walk"', home_html)
        self.assertIn(">Night Walk<", home_html)

    def test_html_work_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("html-work")
        self.assert_common_public_layout(publish_root, ["/studio-note"])

        work_html = self.page_text(publish_root, "/studio-note")
        header_index = work_html.index('<header class="page-head work-header">')
        body_index = work_html.index('<div class="work-body e-content">')

        self.assertLess(header_index, body_index)
        self.assertIn('<div class="work-body e-content">', work_html)
        self.assertIn("<section>", work_html)
        self.assertIn('<script>', work_html)
        self.assertIn('document.documentElement.dataset.work = "studio-note";', work_html)
        self.assertIn('<p>A room built by hand.</p>', work_html)

    def test_reading_microfeatures_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("reading-microfeatures")
        self.assert_common_public_layout(publish_root, ["/field-notes", "/garden-path"])

        field_html = self.page_text(publish_root, "/field-notes")
        garden_html = self.page_text(publish_root, "/garden-path")
        home_html = self.page_text(publish_root, "/")
        styles = (publish_root / "site.css").read_text()

        self.assertIn('id="materials"', field_html)
        self.assertIn('<span class="site-contents-current" aria-current="page">Field Notes</span>', field_html)
        self.assertIn('<ol class="site-work-headings-list">', field_html)
        self.assertIn('data-anchor-id="materials"', field_html)
        self.assertIn('class="site-link site-link--work-index" href="#materials">Materials</a>', field_html)
        self.assertIn('id="turn"', field_html)
        self.assertIn('data-anchor-id="turn"', field_html)
        self.assertIn('class="site-link site-link--work-index" href="#turn">Turn</a>', field_html)
        self.assertIn('id="turn-2"', field_html)
        self.assertIn('data-anchor-id="turn-2"', field_html)
        self.assertIn('class="site-link site-link--work-index" href="#turn-2">Turn</a>', field_html)
        self.assertIn('id="marks"', field_html)
        self.assertNotIn('class="site-link site-link--work-index" href="#marks">Marks</a>', field_html)
        self.assertIn('<style class="site-work-index-targets">', field_html)
        self.assertIn('.site-page--work:has(.work-body [id="materials"]:target)', field_html)
        self.assertNotIn('font-weight:', field_html)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Garden Path</a>', field_html)
        self.assertIn('<a class="external-link" href="https://archive.example/atlas">Archive Atlas</a>', field_html)
        self.assertIn('class="site-sidebar"', field_html)
        self.assertNotIn('page-kicker work-meta', field_html)
        self.assertIn('<aside class="work-date-note" aria-label="Published">', field_html)
        self.assertIn(
            '<time class="work-date dt-published" datetime="2024-08-04T10:00:00+00:00">04 August 2024</time>',
            field_html,
        )
        self.assertLess(field_html.index('<aside class="work-date-note" aria-label="Published">'), field_html.index('<div class="page-body">'))
        self.assertIn('<a class="site-back-link" href="/#contents">Back to contents</a>', field_html)
        self.assertIn('site-bar-section--contents', field_html)
        self.assertIn(
            '<section class="site-contents-group site-contents-group--current"><p class="site-contents-summary">Other works</p>',
            field_html,
        )
        self.assertIn('class="site-link site-contents-link" href="/garden-path">Garden Path</a>', field_html)
        self.assertNotIn("<details", field_html)
        self.assertNotIn("<summary", field_html)
        self.assertNotIn('site-nav--primary', field_html)
        self.assertIn('page-head work-header', field_html)
        self.assertNotIn('page-rule', field_html)
        self.assertIn('reading-prose', field_html)
        self.assertIn('site-bar-section--global', field_html)
        self.assertIn('class="site-global-label visually-hidden"', field_html)
        self.assertNotIn('<p class="site-global-label">Links</p>', field_html)
        self.assertIn('id="contents"', home_html)
        self.assertIn('>Contents</h2>', home_html)
        self.assertIn('href="/garden-path"', home_html)
        self.assertIn('@media (max-width: 62rem)', styles)
        self.assertIn('.site-sidebar', styles)
        self.assertIn('.site-layout', styles)
        self.assertIn('.page-head', styles)
        self.assertNotIn('.page-rule', styles)
        self.assertIn('.page-deck', styles)
        self.assertIn('.works-entry', styles)
        self.assertIn('.page--home', styles)
        self.assertIn('.home-contents', styles)
        self.assertIn('.work-page', styles)
        self.assertIn('min-height: 100svh;', styles)
        self.assertIn('--scale-base: 1rem;', styles)
        self.assertIn('--scale-ratio: 1.18;', styles)
        self.assertIn('--step-n3: calc(var(--scale-base) * pow(var(--scale-ratio), -3));', styles)
        self.assertIn('--step-p9: calc(var(--scale-base) * pow(var(--scale-ratio), 9));', styles)
        self.assertIn('--text-base: clamp(var(--step-0), calc(var(--step-0) + 0.42vw), var(--step-p1));', styles)
        self.assertIn('--page-title-display-size: clamp(var(--step-p6), calc(var(--step-p5) + 3.2vw), var(--step-p9));', styles)
        self.assertIn('--reading-h1-size: clamp(var(--step-p2), calc(var(--step-p2) + 0.85vw), var(--step-p4));', styles)
        self.assertIn('--rail-group-gap: 1.5rem;', styles)
        self.assertIn('--rail-section-gap: 0.58rem;', styles)
        self.assertIn('--rail-item-gap: 0.34rem;', styles)
        self.assertIn('--rail-inline-gap: 0.1rem;', styles)
        self.assertIn('--rail-inline-indent: 0.72rem;', styles)
        self.assertIn('--rail-guide-left: 0.16rem;', styles)
        self.assertIn('--rail-guide-width: 0.085rem;', styles)
        self.assertIn('--rail-guide-dot-size: 0.44rem;', styles)
        self.assertIn('--rail-guide-dot-gap: 0.15rem;', styles)
        self.assertIn('--rail-guide-center-adjust: 0.03ex;', styles)
        self.assertIn('--measure: clamp(38rem, calc(34rem + 8vw), 42rem);', styles)
        self.assertIn('--sidebar-width: 11rem;', styles)
        self.assertIn('--note-width: 11rem;', styles)
        self.assertIn('--date-width: clamp(12rem, calc(11rem + 1.5vw), 13rem);', styles)
        self.assertIn('--margin-width: max(var(--note-width), var(--date-width));', styles)
        self.assertIn('--page-column-gap: clamp(var(--step-p5), 5vw, var(--step-p9));', styles)
        self.assertIn('--reading-span: calc(var(--measure) + var(--page-column-gap) + var(--margin-width));', styles)
        self.assertIn('--rail-corner-space: var(--site-side-space);', styles)
        self.assertIn('--rail-link-size: var(--text-2xs);', styles)
        self.assertIn('--site-top-space: clamp(var(--step-p3), 5vh, var(--step-p6));', styles)
        self.assertIn('--site-side-space: clamp(var(--step-0), 3.2vw, var(--step-p3));', styles)
        self.assertIn('--site-bottom-space: clamp(var(--step-p6), 8vw, var(--step-p9));', styles)
        self.assertIn('--page-stack-gap: clamp(var(--step-p3), 4vw, var(--step-p5));', styles)
        self.assertIn('--home-stack-gap: clamp(var(--step-p7), 8vh, var(--step-p9));', styles)
        self.assertIn('--cover-top-space: clamp(var(--step-p5), 10vh, var(--step-p9));', styles)
        self.assertIn('--prose-flow-space: var(--step-0);', styles)
        self.assertIn('--prose-heading-space: clamp(var(--step-p4), 4vw, var(--step-p6));', styles)
        self.assertIn('--note-stack-gap: var(--step-0);', styles)
        self.assertIn('--rail-marker-center: calc(0.5lh + var(--rail-guide-center-adjust));', styles)
        self.assertIn(
            '--rail-marker-track-inset: calc(var(--rail-marker-center) - (var(--rail-guide-dot-size) / 2));',
            styles,
        )
        self.assertIn('padding: var(--site-top-space) var(--site-side-space) var(--site-bottom-space);', styles)
        self.assertIn('min-height: calc(100vh - var(--site-top-space) - var(--rail-corner-space));', styles)
        self.assertIn('gap: var(--page-stack-gap);', styles)
        self.assertIn('row-gap: var(--page-stack-gap);', styles)
        self.assertIn('padding-top: var(--cover-top-space);', styles)
        self.assertRegex(styles, r"\.site-frame\s*\{[^}]*width:\s*100%")
        self.assertNotIn('margin: 0 auto;', styles)
        self.assertRegex(
            styles,
            r"\.site-layout\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width\) minmax\(0, var\(--reading-span\)\)",
        )
        self.assertIn('.site-bar', styles)
        self.assertIn('.site-nav--primary', styles)
        self.assertIn('.site-link--work-index', styles)
        self.assertIn('.site-back-link', styles)
        self.assertIn('.site-bar-section--contents', styles)
        self.assertIn('.site-contents-groups', styles)
        self.assertIn('.site-contents-group', styles)
        self.assertIn('.site-contents-summary', styles)
        self.assertIn('.site-contents-link', styles)
        self.assertIn('.site-contents-current', styles)
        self.assertIn('.site-work-headings-list', styles)
        self.assertIn('.site-work-headings-item', styles)
        self.assertIn('.site-bar-section--global', styles)
        self.assertIn('.site-title-link--placeholder', styles)
        self.assertIn('.site-nav--global', styles)
        self.assertIn('.link-row', styles)
        self.assertIn('.reading-prose', styles)
        self.assertIn('.work-date-note', styles)
        self.assertIn('.work-date-note .work-date', styles)
        self.assertIn('color: var(--meta-muted);', styles)
        self.assertIn('font-variant-numeric: tabular-nums;', styles)
        self.assertIn('gap: var(--page-column-gap);', styles)
        self.assertIn('margin-left: var(--page-column-gap);', styles)
        self.assertIn('width: min(var(--note-width), 36%);', styles)
        self.assertIn('grid-template-columns: minmax(0, var(--measure)) minmax(var(--date-width), var(--margin-width));', styles)
        self.assertIn('max-width: var(--margin-width);', styles)
        self.assertIn('grid-column: 2;', styles)
        self.assertIn('grid-row: 1;', styles)
        self.assertEqual(3, styles.count('@media '))
        self.assertIn(
            'url("/fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff")',
            styles,
        )
        self.assertIn(
            'url("/fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff")',
            styles,
        )
        self.assertIn('.external-link::after', styles)
        self.assertRegex(styles, r"\.site-sidebar\s*\{[^}]*position:\s*sticky")
        self.assertRegex(styles, r"\.site-sidebar\s*\{[^}]*top:\s*var\(--site-top-space\)")
        self.assertNotRegex(styles, r"\.site-nav--primary a\[aria-current=\"page\"\]\s*\{[^}]*border-left-color")
        self.assertNotIn('.feed-link::after', styles)
        self.assertNotIn('a[href="/feed.xml"]::after', styles)
        self.assertNotIn('.internal-link::after', styles)
        self.assertNotIn('.heading-anchor::before', styles)
        self.assertNotIn('content: "#";', styles)
        self.assertNotIn('.contents-sidebar {', styles)
        self.assertNotIn('.site-nav--toc', styles)
        self.assertNotIn('.site-link--section', styles)
        self.assertRegex(
            styles,
            r"\.heading-anchor:hover,\s*\.heading-anchor:focus-visible\s*\{[^}]*text-decoration:\s*none",
        )
        self.assertRegex(
            styles,
            r"\.site-contents-link,\s*\.site-contents-current,\s*\.site-link--work-index\s*\{[^}]*font-family:\s*var\(--sans\)[^}]*font-size:\s*var\(--rail-link-size\)",
        )
        self.assertRegex(
            styles,
            r"\.site-link--work-index\s*\{[^}]*line-height:\s*1\.1[^}]*text-decoration:\s*none",
        )
        self.assertRegex(
            styles,
            r"\.site-contents-groups\s*\{[^}]*gap:\s*var\(--rail-group-gap\)",
        )
        self.assertRegex(
            styles,
            r"\.site-contents-group\s*\{[^}]*gap:\s*var\(--rail-section-gap\)",
        )
        self.assertRegex(
            styles,
            r"\.site-contents-list\s*\{[^}]*gap:\s*var\(--rail-item-gap\)",
        )
        self.assertRegex(
            styles,
            r"\.site-contents-item\.is-current\s*\{[^}]*gap:\s*calc\(var\(--rail-inline-gap\) \+ 0\.04rem\)",
        )
        self.assertRegex(
            styles,
            r"\.site-work-headings-list\s*\{[^}]*padding:\s*0 0 0 var\(--rail-inline-indent\)[^}]*gap:\s*var\(--rail-inline-gap\)",
        )
        self.assertRegex(
            styles,
            r"\.site-work-headings-list::before\s*\{[^}]*top:\s*var\(--rail-marker-track-inset\)[^}]*bottom:\s*var\(--rail-marker-track-inset\)[^}]*width:\s*var\(--rail-guide-width\)[^}]*background:\s*var\(--line\)",
        )
        self.assertRegex(
            styles,
            r"\.site-work-headings-item::before\s*\{[^}]*top:\s*var\(--rail-marker-center\)[^}]*background:\s*var\(--accent\)[^}]*box-shadow:\s*0 0 0 var\(--rail-guide-dot-gap\) var\(--page\)[^}]*opacity:\s*0",
        )
        self.assertRegex(
            styles,
            r"\.site-work-headings-item:first-child::before\s*\{[^}]*opacity:\s*1",
        )
        self.assertRegex(
            styles,
            r"\.reading-layout,\s*\.reading-column\s*\{[^}]*max-width:\s*var\(--reading-span\)",
        )
        self.assertRegex(
            styles,
            r"\.site-title-link\s*\{[^}]*font-size:\s*var\(--rail-link-size\)",
        )
        self.assertRegex(
            styles,
            r"\.site-link--work-index:hover,\s*\.site-link--work-index:focus-visible\s*\{[^}]*color:\s*inherit",
        )
        self.assertIn('<section class="backlinks" aria-labelledby="backlinks-title">', garden_html)
        self.assertLess(
            garden_html.index('<div class="work-body e-content">'),
            garden_html.index('<section class="backlinks"'),
        )
        self.assertIn('<li><a href="/field-notes">Field Notes</a></li>', garden_html)

    def test_wikilinks_and_assets_fixture(self) -> None:
        _, publish_root, _ = self.build_fixture("wikilinks-and-assets")
        self.assert_common_public_layout(publish_root, ["/garden-path", "/orchard-note"])

        orchard_html = self.page_text(publish_root, "/orchard-note")

        self.assertEqual(2, orchard_html.count('class="internal-link work-link" href="/garden-path"'))
        self.assertIn('class="site-link site-contents-link" href="/garden-path">Garden Path</a>', orchard_html)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Garden Path</a>', orchard_html)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Mapped</a>', orchard_html)
        self.assertIn('Cafe, and Elsewhere.', orchard_html)

    def test_build_is_deterministic_for_minimal_markdown(self) -> None:
        _, publish_root_a, _ = self.build_fixture("minimal-markdown")
        _, publish_root_b, _ = self.build_fixture("minimal-markdown")

        self.assertEqual(self.snapshot(publish_root_a), self.snapshot(publish_root_b))

    def test_missing_required_field_validation(self) -> None:
        site_root, _, _ = self.make_fixture("minimal-markdown")
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        publish_root = Path(temp_dir.name) / "publish"
        meta_path = site_root / "works" / "first-room" / "meta.toml"
        meta_path.write_text('section = "Other works"\n')
        with self.assertRaises(BuildError) as cm:
            builder.build_site(site_root, publish_root)

        self.assertEqual("missing-required-field", cm.exception.rule)
        self.assertEqual("meta.toml", cm.exception.source_path.name)

    def test_duplicate_published_path_validation(self) -> None:
        site_root, _, _ = self.make_fixture("minimal-markdown")
        collision = site_root / "works" / "feed.xml"
        collision.mkdir()
        (collision / "meta.toml").write_text('created = "2024-04-01T00:00:00Z"\n')
        (collision / "index.md").write_text('# Collision\n')
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        publish_root = Path(temp_dir.name) / "publish"

        with self.assertRaises(BuildError) as cm:
            builder.build_site(site_root, publish_root)

        self.assertEqual("duplicate-published-path", cm.exception.rule)
        self.assertEqual("meta.toml", cm.exception.source_path.name)

    def test_broken_internal_link_validation(self) -> None:
        site_root, _, _ = self.make_fixture("minimal-markdown")
        work_body = site_root / "works" / "first-room" / "index.md"
        work_body.write_text('# Opening\n\nA first note in the maze.\n\n[Broken](/missing)\n')
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        publish_root = Path(temp_dir.name) / "publish"

        with self.assertRaises(BuildError) as cm:
            builder.build_site(site_root, publish_root)

        self.assertEqual("broken-internal-link", cm.exception.rule)
        self.assertEqual("index.md", cm.exception.source_path.name)

    def test_missing_canonical_link_validation(self) -> None:
        site_root, publish_root, _ = self.make_fixture("minimal-markdown")
        original_render_pages = builder.render_pages

        def broken_render_pages(*args, **kwargs):
            pages = original_render_pages(*args, **kwargs)
            return [
                builder.RenderedPage(
                    public_path=page.public_path,
                    output_path=page.output_path,
                    html=page.html.replace('<link rel="canonical"', '<link rel="not-canonical"', 1),
                    source_path=page.source_path,
                )
                for page in pages
            ]

        with patch.object(builder, "render_pages", side_effect=broken_render_pages):
            with self.assertRaises(BuildError) as cm:
                builder.build_site(site_root, publish_root)

        self.assertEqual("missing-canonical-link", cm.exception.rule)
        self.assertIn(cm.exception.source_path.name, {"site.toml", "index.html"})


if __name__ == "__main__":
    unittest.main()

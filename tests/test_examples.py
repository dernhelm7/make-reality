from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from labyrinth.builder import build_site


REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_ROOT = REPO_ROOT / "agent_docs" / "examples"
ET_BOOK_ROMAN = "fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff"
ET_BOOK_ITALIC = (
    "fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff"
)
ET_BOOK_BOLD = "fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff"
ET_BOOK_LICENSE = "fonts/et-book/LICENSE.txt"


class ExampleBuildTests(unittest.TestCase):
    def build_fixture(self, fixture_name: str) -> Path:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        build_site(EXAMPLES_ROOT / fixture_name, publish_root)
        return publish_root

    def test_cli_build_command(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "labyrinth",
                "build",
                str(EXAMPLES_ROOT / "minimal-markdown"),
                str(publish_root),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((publish_root / "index.html").exists())
        self.assertTrue((publish_root / ET_BOOK_ROMAN).exists())

    def test_build_script_works_outside_repo_root(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        outside_cwd = Path(self.enterContext(tempfile.TemporaryDirectory()))
        result = subprocess.run(
            [
                str(REPO_ROOT / "build-site"),
                str(EXAMPLES_ROOT / "minimal-markdown"),
                str(publish_root),
            ],
            cwd=outside_cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((publish_root / "index.html").exists())
        self.assertTrue((publish_root / ET_BOOK_ROMAN).exists())

    def test_minimal_markdown_fixture(self) -> None:
        publish_root = self.build_fixture("minimal-markdown")
        first_room = read_text(publish_root / "first-room" / "index.html")
        home_page = read_text(publish_root / "index.html")
        stylesheet = read_text(publish_root / "site.css")

        self.assertIn("First Room", home_page)
        self.assertIn("Other works", home_page)
        self.assertIn('class="works-entry"', home_page)
        self.assertIn('<h1 class="page-title work-title p-name">First Room</h1>', first_room)
        self.assertNotIn('page-kicker work-meta', first_room)
        self.assertIn('<aside class="work-date-note" aria-label="Published">', first_room)
        self.assertIn('<time class="work-date dt-published" datetime="2024-02-14T00:00:00+00:00">14 February 2024</time>', first_room)
        self.assertLess(first_room.index('<aside class="work-date-note" aria-label="Published">'), first_room.index('<div class="page-body">'))
        self.assertIn('<a class="site-back-link" href="/#contents">Back to contents</a>', first_room)
        self.assertIn('site-bar-section--contents', first_room)
        self.assertIn('<section class="site-contents-group site-contents-group--current">', first_room)
        self.assertIn('<p class="site-contents-summary">Other works</p>', first_room)
        self.assertNotIn("<details", first_room)
        self.assertNotIn("<summary", first_room)
        self.assertIn('<span class="site-contents-current" aria-current="page">First Room</span>', first_room)
        self.assertNotIn('class="site-contents-link"', first_room)
        self.assertNotIn('site-work-headings-list', first_room)
        self.assertNotIn('site-nav--primary', first_room)
        self.assertIn('page-head work-header', first_room)
        self.assertNotIn('page-rule', first_room)
        self.assertIn('reading-prose', first_room)
        self.assertIn('id="opening"', first_room)
        self.assertIn('href="#opening">Opening</a>', first_room)
        self.assertNotIn('aria-label="On this page"', first_room)
        self.assertEqual(first_room.count("<h1"), 1)
        self.assertIn('rel="alternate" type="application/rss+xml"', home_page)
        self.assertIn('page-head', home_page)
        self.assertNotIn('page-rule', home_page)
        self.assertIn('page-deck', home_page)
        self.assertIn('class="site-sidebar"', home_page)
        self.assertIn('class="site-bar"', home_page)
        self.assertIn('site-nav--primary', home_page)
        self.assertIn('href="#contents">Content</a>', home_page)
        self.assertIn('href="#contents">Enter the content</a>', home_page)
        self.assertIn('id="contents"', home_page)
        self.assertIn('>Contents</h2>', home_page)
        self.assertIn('href="/first-room"', home_page)
        self.assertNotIn('href="/works">Content</a>', home_page)
        self.assertIn('site-nav--global', home_page)
        self.assertIn('site-bar-section--global', home_page)
        self.assertIn('class="site-global-label visually-hidden"', home_page)
        self.assertIn('site-title-link--placeholder', home_page)
        self.assertNotIn('<a class="site-title-link"', home_page)
        self.assertNotIn('site-header', home_page)
        self.assertNotIn('site-footer', home_page)
        self.assertNotIn('<p class="site-global-label">Links</p>', home_page)
        self.assertNotIn('<p class="page-kicker">Table of contents</p>', home_page)
        self.assertIn('@font-face {', stylesheet)
        self.assertIn(
            'src: url("/fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff") format("woff");',
            stylesheet,
        )
        self.assertIn('font-display: swap;', stylesheet)
        self.assertIn("#fffff8", stylesheet)
        self.assertIn("#1c1a17", stylesheet)
        self.assertIn("#0a7c80", stylesheet)
        self.assertIn("line-height: 1.5;", stylesheet)
        self.assertIn("cursor: url(", stylesheet)
        self.assertIn(".site-sidebar", stylesheet)
        self.assertIn(".site-layout", stylesheet)
        self.assertIn(".page-head", stylesheet)
        self.assertNotIn(".page-rule", stylesheet)
        self.assertIn(".page-deck", stylesheet)
        self.assertIn(".works-entry", stylesheet)
        self.assertIn(".page--home", stylesheet)
        self.assertIn(".home-contents", stylesheet)
        self.assertIn("min-height: 100svh;", stylesheet)
        self.assertIn(".site-bar", stylesheet)
        self.assertIn(".site-nav--primary", stylesheet)
        self.assertIn(".site-nav--global", stylesheet)
        self.assertIn(".link-row", stylesheet)
        self.assertIn(".reading-prose", stylesheet)
        self.assertIn(
            'url("/fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff")',
            stylesheet,
        )
        self.assertIn(
            'url("/fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff")',
            stylesheet,
        )

    def test_named_sections_fixture(self) -> None:
        publish_root = self.build_fixture("named-sections")
        home_page = read_text(publish_root / "index.html")
        folded_map = read_text(publish_root / "folded-map" / "index.html")

        self.assertIn('class="works-entry"', home_page)
        self.assertIn(">Essays</h2>", home_page)
        self.assertIn(">Projects</h2>", home_page)
        essays_index = home_page.index(">Essays</h2>")
        projects_index = home_page.index(">Projects</h2>")
        essay_fragment_index = home_page.index(">Essay Fragment<")
        folded_map_index = home_page.index(">Folded Map<")
        self.assertLess(essays_index, projects_index)
        self.assertLess(essays_index, essay_fragment_index)
        self.assertLess(projects_index, folded_map_index)
        self.assertIn(
            '<section class="site-contents-group site-contents-group--current"><p class="site-contents-summary">Projects</p>',
            folded_map,
        )
        self.assertIn('<span class="site-contents-current" aria-current="page">Folded Map</span>', folded_map)
        self.assertNotIn("<details", folded_map)
        self.assertNotIn("<summary", folded_map)
        self.assertNotIn('<p class="site-contents-summary">Essays</p>', folded_map)
        self.assertNotIn('class="site-link site-contents-link" href="/essay-fragment">Essay Fragment</a>', folded_map)

    def test_section_fallback_fixture(self) -> None:
        publish_root = self.build_fixture("section-fallback")
        home_page = read_text(publish_root / "index.html")

        self.assertIn(">Other works</h2>", home_page)
        self.assertIn(">Night Walk<", home_page)

    def test_html_work_fixture(self) -> None:
        publish_root = self.build_fixture("html-work")
        studio_note = read_text(publish_root / "studio-note" / "index.html")

        self.assertIn('<h1 class="page-title work-title p-name">Studio Note</h1>', studio_note)
        self.assertIn("<section>", studio_note)
        self.assertIn('document.documentElement.dataset.work = "studio-note";', studio_note)
        self.assertLess(
            studio_note.index('<h1 class="page-title work-title p-name">Studio Note</h1>'),
            studio_note.index("document.documentElement.dataset.work"),
        )
        self.assertEqual(list(publish_root.rglob("*.js")), [])

    def test_reading_microfeatures_fixture(self) -> None:
        publish_root = self.build_fixture("reading-microfeatures")
        field_notes = read_text(publish_root / "field-notes" / "index.html")
        garden_path = read_text(publish_root / "garden-path" / "index.html")
        stylesheet = read_text(publish_root / "site.css")

        self.assertIn('page-head work-header', field_notes)
        self.assertNotIn('page-rule', field_notes)
        self.assertIn('reading-prose', field_notes)
        self.assertNotIn('page-kicker work-meta', field_notes)
        self.assertIn('<aside class="work-date-note" aria-label="Published">', field_notes)
        self.assertIn(
            '<time class="work-date dt-published" datetime="2024-08-04T10:00:00+00:00">04 August 2024</time>',
            field_notes,
        )
        self.assertLess(field_notes.index('<aside class="work-date-note" aria-label="Published">'), field_notes.index('<div class="page-body">'))
        self.assertIn('id="materials"', field_notes)
        self.assertIn('id="turn"', field_notes)
        self.assertIn('id="turn-2"', field_notes)
        self.assertIn('id="marks"', field_notes)
        self.assertIn('<span class="site-contents-current" aria-current="page">Field Notes</span>', field_notes)
        self.assertIn('<ol class="site-work-headings-list">', field_notes)
        self.assertIn('data-anchor-id="materials"', field_notes)
        self.assertIn('class="site-link site-link--work-index" href="#materials">Materials</a>', field_notes)
        self.assertIn('data-anchor-id="turn"', field_notes)
        self.assertIn('class="site-link site-link--work-index" href="#turn">Turn</a>', field_notes)
        self.assertIn('data-anchor-id="turn-2"', field_notes)
        self.assertIn('class="site-link site-link--work-index" href="#turn-2">Turn</a>', field_notes)
        self.assertNotIn('class="site-link site-link--work-index" href="#marks">Marks</a>', field_notes)
        self.assertIn('<style class="site-work-index-targets">', field_notes)
        self.assertIn('.site-page--work:has(.work-body [id="materials"]:target)', field_notes)
        self.assertNotIn('font-weight:', field_notes)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Garden Path</a>', field_notes)
        self.assertIn('<a class="external-link" href="https://archive.example/atlas">Archive Atlas</a>', field_notes)
        self.assertIn('class="site-sidebar"', field_notes)
        self.assertIn('<a class="site-back-link" href="/#contents">Back to contents</a>', field_notes)
        self.assertIn('class="site-bar"', field_notes)
        self.assertIn('site-bar-section--contents', field_notes)
        self.assertIn(
            '<section class="site-contents-group site-contents-group--current"><p class="site-contents-summary">Other works</p>',
            field_notes,
        )
        self.assertIn('class="site-link site-contents-link" href="/garden-path">Garden Path</a>', field_notes)
        self.assertNotIn("<details", field_notes)
        self.assertNotIn("<summary", field_notes)
        self.assertNotIn('site-nav--primary', field_notes)
        self.assertIn('site-nav--global', field_notes)
        self.assertIn('site-bar-section--contents', field_notes)
        self.assertIn('site-bar-section--global', field_notes)
        self.assertIn('class="site-global-label visually-hidden"', field_notes)
        self.assertNotIn('site-header', field_notes)
        self.assertNotIn('site-footer', field_notes)
        self.assertNotIn('<p class="site-global-label">Links</p>', field_notes)
        home_page = read_text(publish_root / "index.html")
        self.assertIn('id="contents"', home_page)
        self.assertIn('>Contents</h2>', home_page)
        self.assertIn('href="/garden-path"', home_page)
        self.assertIn(".external-link::after", stylesheet)
        self.assertIn(".site-sidebar", stylesheet)
        self.assertIn(".site-layout", stylesheet)
        self.assertIn(".page-head", stylesheet)
        self.assertNotIn(".page-rule", stylesheet)
        self.assertIn(".page-deck", stylesheet)
        self.assertIn(".works-entry", stylesheet)
        self.assertIn(".site-bar", stylesheet)
        self.assertIn(".work-date-note", stylesheet)
        self.assertIn(".work-date-note .work-date", stylesheet)
        self.assertIn(".work-page", stylesheet)
        self.assertIn("color: var(--meta-muted);", stylesheet)
        self.assertIn("font-variant-numeric: tabular-nums;", stylesheet)
        self.assertIn("gap: var(--page-column-gap);", stylesheet)
        self.assertIn("margin-left: var(--page-column-gap);", stylesheet)
        self.assertIn("width: min(var(--note-width), 36%);", stylesheet)
        self.assertIn("grid-template-columns: minmax(0, var(--measure)) minmax(var(--date-width), var(--margin-width));", stylesheet)
        self.assertIn("max-width: var(--margin-width);", stylesheet)
        self.assertIn("grid-column: 2;", stylesheet)
        self.assertIn("grid-row: 1;", stylesheet)
        self.assertIn(".site-nav--primary", stylesheet)
        self.assertIn(".site-link--work-index", stylesheet)
        self.assertIn(".site-back-link", stylesheet)
        self.assertIn(".site-bar-section--contents", stylesheet)
        self.assertIn(".site-contents-groups", stylesheet)
        self.assertIn(".site-contents-group", stylesheet)
        self.assertIn(".site-contents-summary", stylesheet)
        self.assertIn(".site-contents-link", stylesheet)
        self.assertIn(".site-contents-current", stylesheet)
        self.assertIn(".site-work-headings-list", stylesheet)
        self.assertIn(".site-work-headings-item", stylesheet)
        self.assertIn(".site-bar-section--global", stylesheet)
        self.assertIn(".site-title-link--placeholder", stylesheet)
        self.assertIn(".site-nav--global", stylesheet)
        self.assertIn(".link-row", stylesheet)
        self.assertIn(".reading-prose", stylesheet)
        self.assertIn("--scale-base: 1rem;", stylesheet)
        self.assertIn("--scale-ratio: 1.18;", stylesheet)
        self.assertIn("--step-n3: calc(var(--scale-base) * pow(var(--scale-ratio), -3));", stylesheet)
        self.assertIn("--step-p9: calc(var(--scale-base) * pow(var(--scale-ratio), 9));", stylesheet)
        self.assertIn("--text-base: clamp(var(--step-0), calc(var(--step-0) + 0.42vw), var(--step-p1));", stylesheet)
        self.assertIn("--page-title-display-size: clamp(var(--step-p6), calc(var(--step-p5) + 3.2vw), var(--step-p9));", stylesheet)
        self.assertIn("--reading-h1-size: clamp(var(--step-p2), calc(var(--step-p2) + 0.85vw), var(--step-p4));", stylesheet)
        self.assertIn("--rail-group-gap: 1.5rem;", stylesheet)
        self.assertIn("--rail-section-gap: 0.58rem;", stylesheet)
        self.assertIn("--rail-item-gap: 0.34rem;", stylesheet)
        self.assertIn("--rail-inline-gap: 0.1rem;", stylesheet)
        self.assertIn("--rail-inline-indent: 0.72rem;", stylesheet)
        self.assertIn("--rail-guide-left: 0.16rem;", stylesheet)
        self.assertIn("--rail-guide-width: 0.085rem;", stylesheet)
        self.assertIn("--rail-guide-dot-size: 0.44rem;", stylesheet)
        self.assertIn("--rail-guide-dot-gap: 0.15rem;", stylesheet)
        self.assertIn("--rail-guide-center-adjust: 0.03ex;", stylesheet)
        self.assertIn("--measure: clamp(38rem, calc(34rem + 8vw), 42rem);", stylesheet)
        self.assertIn("--sidebar-width: 11rem;", stylesheet)
        self.assertIn("--note-width: 11rem;", stylesheet)
        self.assertIn("--date-width: clamp(12rem, calc(11rem + 1.5vw), 13rem);", stylesheet)
        self.assertIn("--margin-width: max(var(--note-width), var(--date-width));", stylesheet)
        self.assertIn("--page-column-gap: clamp(var(--step-p5), 5vw, var(--step-p9));", stylesheet)
        self.assertIn("--reading-span: calc(var(--measure) + var(--page-column-gap) + var(--margin-width));", stylesheet)
        self.assertIn("--rail-corner-space: var(--site-side-space);", stylesheet)
        self.assertIn("--rail-link-size: var(--text-2xs);", stylesheet)
        self.assertIn("--site-top-space: clamp(var(--step-p3), 5vh, var(--step-p6));", stylesheet)
        self.assertIn("--site-side-space: clamp(var(--step-0), 3.2vw, var(--step-p3));", stylesheet)
        self.assertIn("--site-bottom-space: clamp(var(--step-p6), 8vw, var(--step-p9));", stylesheet)
        self.assertIn("--page-stack-gap: clamp(var(--step-p3), 4vw, var(--step-p5));", stylesheet)
        self.assertIn("--home-stack-gap: clamp(var(--step-p7), 8vh, var(--step-p9));", stylesheet)
        self.assertIn("--cover-top-space: clamp(var(--step-p5), 10vh, var(--step-p9));", stylesheet)
        self.assertIn("--prose-flow-space: var(--step-0);", stylesheet)
        self.assertIn("--prose-heading-space: clamp(var(--step-p4), 4vw, var(--step-p6));", stylesheet)
        self.assertIn("--note-stack-gap: var(--step-0);", stylesheet)
        self.assertIn("--rail-marker-center: calc(0.5lh + var(--rail-guide-center-adjust));", stylesheet)
        self.assertIn(
            "--rail-marker-track-inset: calc(var(--rail-marker-center) - (var(--rail-guide-dot-size) / 2));",
            stylesheet,
        )
        self.assertIn("padding: var(--site-top-space) var(--site-side-space) var(--site-bottom-space);", stylesheet)
        self.assertIn("min-height: calc(100vh - var(--site-top-space) - var(--rail-corner-space));", stylesheet)
        self.assertIn("@media (max-width: 62rem)", stylesheet)
        self.assertEqual(3, stylesheet.count("@media "))
        self.assertRegex(stylesheet, r"\.site-frame\s*\{[^}]*width:\s*100%")
        self.assertNotIn("margin: 0 auto;", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.site-layout\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width\) minmax\(0, var\(--reading-span\)\)",
        )
        self.assertRegex(stylesheet, r"\.site-sidebar\s*\{[^}]*position:\s*sticky")
        self.assertRegex(stylesheet, r"\.site-sidebar\s*\{[^}]*top:\s*var\(--site-top-space\)")
        self.assertNotRegex(stylesheet, r"\.site-nav--primary a\[aria-current=\"page\"\]\s*\{[^}]*border-left-color")
        self.assertNotIn(".feed-link::after", stylesheet)
        self.assertNotIn('a[href="/feed.xml"]::after', stylesheet)
        self.assertNotIn(".internal-link::after", stylesheet)
        self.assertNotIn(".heading-anchor::before", stylesheet)
        self.assertNotIn('content: "#";', stylesheet)
        self.assertNotIn(".contents-sidebar", stylesheet)
        self.assertNotIn(".site-nav--toc", stylesheet)
        self.assertNotIn(".site-link--section", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.heading-anchor:hover,\s*\.heading-anchor:focus-visible\s*\{[^}]*text-decoration:\s*none",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-link,\s*\.site-contents-current,\s*\.site-link--work-index\s*\{[^}]*font-family:\s*var\(--sans\)[^}]*font-size:\s*var\(--rail-link-size\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-link--work-index\s*\{[^}]*line-height:\s*1\.1[^}]*text-decoration:\s*none",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-groups\s*\{[^}]*gap:\s*var\(--rail-group-gap\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-group\s*\{[^}]*gap:\s*var\(--rail-section-gap\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-list\s*\{[^}]*gap:\s*var\(--rail-item-gap\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-item\.is-current\s*\{[^}]*gap:\s*calc\(var\(--rail-inline-gap\) \+ 0\.04rem\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-work-headings-list\s*\{[^}]*padding:\s*0 0 0 var\(--rail-inline-indent\)[^}]*gap:\s*var\(--rail-inline-gap\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-work-headings-list::before\s*\{[^}]*top:\s*var\(--rail-marker-track-inset\)[^}]*bottom:\s*var\(--rail-marker-track-inset\)[^}]*width:\s*var\(--rail-guide-width\)[^}]*background:\s*var\(--line\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-work-headings-item::before\s*\{[^}]*top:\s*var\(--rail-marker-center\)[^}]*background:\s*var\(--accent\)[^}]*box-shadow:\s*0 0 0 var\(--rail-guide-dot-gap\) var\(--page\)[^}]*opacity:\s*0",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-work-headings-item:first-child::before\s*\{[^}]*opacity:\s*1",
        )
        self.assertRegex(
            stylesheet,
            r"\.reading-layout,\s*\.reading-column\s*\{[^}]*max-width:\s*var\(--reading-span\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-title-link\s*\{[^}]*font-size:\s*var\(--rail-link-size\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-link--work-index:hover,\s*\.site-link--work-index:focus-visible\s*\{[^}]*color:\s*inherit",
        )
        self.assertIn('<h2 class="backlinks-title" id="backlinks-title">Backlinks</h2>', garden_path)
        self.assertIn('<a href="/field-notes">Field Notes</a>', garden_path)
        self.assertLess(
            garden_path.index("A hedge note for the return path."),
            garden_path.index("Backlinks"),
        )

    def test_wikilinks_and_assets_fixture(self) -> None:
        publish_root = self.build_fixture("wikilinks-and-assets")
        orchard_note = read_text(publish_root / "orchard-note" / "index.html")

        self.assertEqual(2, orchard_note.count('class="internal-link work-link" href="/garden-path"'))
        self.assertIn('class="site-link site-contents-link" href="/garden-path">Garden Path</a>', orchard_note)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Garden Path</a>', orchard_note)
        self.assertIn('<a class="internal-link work-link" href="/garden-path">Mapped</a>', orchard_note)
        self.assertIn("Cafe", orchard_note)
        self.assertIn("Elsewhere", orchard_note)
        self.assertNotIn('href="Cafe"', orchard_note)
        self.assertNotIn(">Cafe</a>", orchard_note)
        self.assertNotIn(">Elsewhere</a>", orchard_note)

    def test_publish_root_is_deterministic(self) -> None:
        first_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "first"
        second_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "second"

        build_site(EXAMPLES_ROOT / "minimal-markdown", first_root)
        build_site(EXAMPLES_ROOT / "minimal-markdown", second_root)

        self.assertEqual(tree_digest(first_root), tree_digest(second_root))

    def test_stylesheet_output_is_deterministic(self) -> None:
        first_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "first"
        second_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "second"

        build_site(EXAMPLES_ROOT / "minimal-markdown", first_root)
        build_site(EXAMPLES_ROOT / "minimal-markdown", second_root)

        self.assertEqual((first_root / "site.css").read_bytes(), (second_root / "site.css").read_bytes())

    def test_rebuild_removes_stale_files(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        build_site(EXAMPLES_ROOT / "minimal-markdown", publish_root)
        stale = publish_root / "stale.txt"
        stale.write_text("leftover", encoding="utf-8")

        build_site(EXAMPLES_ROOT / "minimal-markdown", publish_root)

        self.assertFalse(stale.exists())

    def test_publish_root_contains_only_public_files(self) -> None:
        publish_root = self.build_fixture("reading-microfeatures")
        files = sorted(path.relative_to(publish_root).as_posix() for path in publish_root.rglob("*") if path.is_file())
        self.assertIn("feed.xml", files)
        self.assertIn("site.css", files)
        self.assertIn(ET_BOOK_ROMAN, files)
        self.assertIn(ET_BOOK_ITALIC, files)
        self.assertIn(ET_BOOK_BOLD, files)
        self.assertIn(ET_BOOK_LICENSE, files)
        self.assertNotIn("site.js", files)
        for path in files:
            self.assertTrue(
                path == "feed.xml"
                or path == "site.css"
                or path.startswith("fonts/et-book/")
                or path.endswith("/index.html")
                or path == "index.html"
            )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


if __name__ == "__main__":
    unittest.main()

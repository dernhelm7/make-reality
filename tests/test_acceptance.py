from __future__ import annotations

import tempfile
from pathlib import Path

from labyrinth.builder import build_site

from .fixture_support import (
    ET_BOOK_BOLD,
    ET_BOOK_ITALIC,
    ET_BOOK_LICENSE,
    ET_BOOK_ROMAN,
    FixtureSiteTestCase,
    REPO_ROOT,
    tree_digest,
)


class AcceptanceTests(FixtureSiteTestCase):
    def test_build_url_override_keeps_canonical_urls_and_rewrites_preview_targets(self) -> None:
        site_root, publish_root = self.make_fixture("minimal-markdown")

        build_site(
            site_root,
            publish_root,
            build_url="http://localhost:8009/preview",
        )

        first_room = self.page_text(publish_root, "/first-room")
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")

        self.assertIn('<base href="http://localhost:8009/preview/first-room/">', first_room)
        self.assertIn('<link rel="canonical" href="https://labyrinth.example/first-room">', first_room)
        self.assertIn('<a class="visually-hidden u-url" href="https://labyrinth.example/first-room">Permalink</a>', first_room)
        self.assertIn('<id>https://labyrinth.example/feed.xml</id>', feed)
        self.assertIn('<link rel="self" type="application/atom+xml" href="http://localhost:8009/preview/feed.xml"/>', feed)
        self.assertIn('<link rel="alternate" type="text/html" href="http://localhost:8009/preview"/>', feed)
        self.assertIn('Copy <xhtml:a href="http://localhost:8009/preview/feed.xml">the feed URL</xhtml:a> into a feed reader to follow new work.', feed)
        self.assertIn('<id>https://labyrinth.example/id/first-room</id>', feed)
        self.assertIn(
            '<link rel="alternate" type="text/html" href="http://localhost:8009/preview/first-room"/>',
            feed,
        )
        self.assertIn(
            '&lt;a class=&quot;heading-anchor&quot; href=&quot;http://localhost:8009/preview/first-room#opening&quot;&gt;Opening&lt;/a&gt;',
            feed,
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

        home_page = self.page_text(publish_root, "/")
        field_notes = self.page_text(publish_root, "/field-notes")

        self.assertIn('<base href="https://labyrinth.example/journal/">', home_page)
        self.assertIn('<base href="https://labyrinth.example/journal/field-notes/">', field_notes)
        self.assertIn('href="site.css"', home_page)
        self.assertIn('href="feed.xml"', home_page)
        self.assertIn('href="field-notes"', home_page)
        self.assertIn('<a class="site-back-link" href="../#contents">Back to contents</a>', field_notes)
        self.assertIn('class="site-link site-contents-link" href="../garden-path">Garden Path</a>', field_notes)
        self.assertIn('<a class="internal-link work-link" href="../garden-path">Garden Path</a>', field_notes)
        self.assertIn('<link rel="canonical" href="https://labyrinth.example/journal/field-notes">', field_notes)
        self.assertIn('rel="alternate" type="application/atom+xml"', home_page)

    def test_minimal_markdown_fixture(self) -> None:
        _, publish_root = self.build_fixture("minimal-markdown")
        self.assert_common_public_layout(publish_root, ["/first-room"])

        first_room = self.page_text(publish_root, "/first-room")
        home_page = self.page_text(publish_root, "/")
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")
        feed_stylesheet = (publish_root / "feed.css").read_text(encoding="utf-8")
        stylesheet = (publish_root / "site.css").read_text(encoding="utf-8")

        self.assertIn("<!DOCTYPE html>\n<html", home_page)
        self.assertIn("</head>\n<body", home_page)
        self.assertIn("<main class=\"site-main\">\n", first_room)
        self.assertIn("First Room", home_page)
        self.assertIn("Other works", home_page)
        self.assertIn('class="works-entry"', home_page)
        self.assertNotIn('class="works-entry-date works-date"', home_page)
        self.assertIn('<h1 class="page-title work-title p-name">First Room</h1>', first_room)
        self.assertIn('<base href="https://labyrinth.example/first-room/">', first_room)
        self.assertNotIn('page-kicker work-meta', first_room)
        self.assertIn('<aside class="work-date-note" aria-label="Published">', first_room)
        self.assertIn('<time class="work-date dt-published" datetime="2024-02-14T00:00:00+00:00">14 February 2024</time>', first_room)
        self.assertLess(first_room.index('<aside class="work-date-note" aria-label="Published">'), first_room.index('<div class="page-body">'))
        self.assertIn('<a class="site-back-link" href="../#contents">Back to contents</a>', first_room)
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
        self.assertIn('rel="alternate" type="application/atom+xml"', home_page)
        self.assertIn('page-head', home_page)
        self.assertIn('<base href="https://labyrinth.example/">', home_page)
        self.assertIn('<p class="page-deck cover-statement">Visible cover line for the fixture.</p>', home_page)
        self.assertIn('<meta name="description" content="Metadata summary for the fixture.">', home_page)
        self.assertNotIn('page-rule', home_page)
        self.assertIn('page-deck', home_page)
        self.assertNotIn('class="site-sidebar"', home_page)
        self.assertNotIn('class="site-bar"', home_page)
        self.assertIn('class="home-cover-meta"', home_page)
        self.assertNotIn('site-nav--primary', home_page)
        self.assertNotIn('href="#contents">Content</a>', home_page)
        self.assertNotIn('Enter the content', home_page)
        self.assertIn('id="contents"', home_page)
        self.assertIn('<h2 class="page-title page-title--section" id="contents-heading"><a class="home-contents-heading-link" href="#contents">Read</a></h2>', home_page)
        self.assertIn('href="first-room"', home_page)
        self.assertIn('site-nav--global', home_page)
        self.assertIn('site-bar-section--global', home_page)
        self.assertIn('class="site-global-label visually-hidden"', home_page)
        self.assertNotIn('site-title-link--placeholder', home_page)
        self.assertNotIn('<a class="site-title-link"', home_page)
        self.assertNotIn('site-header', home_page)
        self.assertNotIn('site-footer', home_page)
        self.assertNotIn('<p class="site-global-label">Links</p>', home_page)
        self.assertNotIn('<p class="page-kicker">Table of contents</p>', home_page)
        self.assertIn("@font-face {", stylesheet)
        self.assertIn(
            'src: url("fonts/et-book/et-book-roman-line-figures/et-book-roman-line-figures.woff") format("woff");',
            stylesheet,
        )
        self.assertIn("font-display: swap;", stylesheet)
        self.assertIn("#ffffff", stylesheet)
        self.assertIn("#202020", stylesheet)
        self.assertIn("#3a3a3a", stylesheet)
        self.assertIn("#0a7c80", stylesheet)
        self.assertNotIn("line-height: 1.5;", stylesheet)
        self.assertIn("cursor: url(", stylesheet)
        self.assertIn(".site-sidebar", stylesheet)
        self.assertIn(".site-layout", stylesheet)
        self.assertIn(".page-head", stylesheet)
        self.assertNotIn(".page-rule", stylesheet)
        self.assertIn(".page-deck", stylesheet)
        self.assertIn(".works-entry", stylesheet)
        self.assertNotIn(".works-entry-date", stylesheet)
        self.assertIn("--leader-dot-size: var(--text-xs);", stylesheet)
        self.assertIn("--leader-dot-step: 0.18em;", stylesheet)
        self.assertIn("white-space: nowrap;", stylesheet)
        self.assertIn("letter-spacing: var(--leader-dot-step);", stylesheet)
        self.assertIn(".page--home", stylesheet)
        self.assertIn(".home-contents", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.page--home\s*\{[^}]*grid-template-columns:\s*minmax\(0, var\(--home-contents-measure\)\)[^}]*justify-content:\s*center",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-page--home \.page--cover\s*\{[^}]*grid-column:\s*1[^}]*grid-template-columns:\s*minmax\(0, var\(--home-column-measure\)\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-page--home \.page-head--cover\s*\{[^}]*grid-column:\s*1",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-page--home \.page-head--cover\s*\{[^}]*max-width:\s*var\(--home-column-measure\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.home-cover-meta\s*\{[^}]*grid-column:\s*1",
        )
        self.assertRegex(
            stylesheet,
            r"\.home-cover-meta\s*\{[^}]*max-width:\s*var\(--home-column-measure\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.home-contents\s*\{[^}]*grid-column:\s*1[^}]*max-width:\s*var\(--home-contents-measure\)",
        )
        self.assertIn("min-height: 100svh;", stylesheet)
        self.assertIn(".site-bar", stylesheet)
        self.assertIn(".site-nav--global", stylesheet)
        self.assertIn(".home-cover-meta", stylesheet)
        self.assertNotIn(".link-row", stylesheet)
        self.assertIn(".reading-prose", stylesheet)
        self.assertIn(".section-description", stylesheet)
        self.assertIn('@namespace url("http://www.w3.org/2005/Atom");', feed_stylesheet)
        self.assertIn('@namespace xhtml url("http://www.w3.org/1999/xhtml");', feed_stylesheet)
        self.assertIn("feed > title", feed_stylesheet)
        self.assertIn('xhtml|section[class~="feed-guide"]', feed_stylesheet)
        self.assertIn("--feed-bg: #073638;", feed_stylesheet)
        self.assertIn("--feed-guide-bg: #dcefed;", feed_stylesheet)
        self.assertIn("--home-main-indent: max(var(--site-side-space), calc((100vw - var(--home-contents-measure)) / 2));", feed_stylesheet)
        self.assertIn("--feed-content-indent: var(--home-main-indent);", feed_stylesheet)
        self.assertIn("--feed-gutter: calc(var(--feed-content-indent) - var(--feed-cell-inline));", feed_stylesheet)
        self.assertIn("margin: 0 calc(var(--feed-gutter) * -1) var(--feed-gutter);", feed_stylesheet)
        self.assertIn("padding: 2.5rem var(--feed-content-indent) 1.75rem;", feed_stylesheet)
        self.assertIn("--feed-guide-measure: clamp(48ch, 66vw, 86ch);", feed_stylesheet)
        self.assertIn("max-width: var(--feed-guide-measure);", feed_stylesheet)
        self.assertIn("text-wrap: balance;", feed_stylesheet)
        self.assertNotIn('xhtml|span[class~="feed-trademark"]', feed_stylesheet)
        self.assertNotIn('xhtml|span[class~="feed-twitter-x"]', feed_stylesheet)
        self.assertIn("grid-template-columns: minmax(16ch, 18ch) 20ch 20ch max-content;", feed_stylesheet)
        self.assertIn("--feed-cell-inline: 0.5rem;", feed_stylesheet)
        self.assertIn("--feed-cell-padding: var(--feed-cell-block) var(--feed-cell-inline);", feed_stylesheet)
        self.assertIn("padding-left: var(--feed-cell-inline);", feed_stylesheet)
        self.assertIn("text-decoration: underline;", feed_stylesheet)
        self.assertNotIn("display: contents;", feed_stylesheet)
        self.assertIn("white-space: nowrap;", feed_stylesheet)
        self.assertNotIn("border-top:", feed_stylesheet)
        self.assertNotIn("border-bottom:", feed_stylesheet)
        self.assertNotIn('content: "<feed', feed_stylesheet)
        self.assertNotIn('content: "<entry', feed_stylesheet)
        self.assertNotIn('content: "href=', feed_stylesheet)
        self.assertIn('entry > xhtml|a[class~="feed-entry-url"]', feed_stylesheet)
        self.assertNotIn('entry > link[rel="alternate"]::before', feed_stylesheet)
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', feed)
        self.assertIn('<?xml-stylesheet type="text/css" href="feed.css"?>', feed)
        self.assertIn('<feed xmlns="http://www.w3.org/2005/Atom">', feed)
        self.assertIn('<id>https://labyrinth.example/feed.xml</id>', feed)
        self.assertIn('<name>Labyrinth Author</name>', feed)
        self.assertIn('<link rel="self" type="application/atom+xml" href="https://labyrinth.example/feed.xml"/>', feed)
        self.assertIn('<link rel="alternate" type="text/html" href="https://labyrinth.example"/>', feed)
        self.assertIn('<xhtml:section xmlns:xhtml="http://www.w3.org/1999/xhtml" class="feed-guide" aria-label="How to use this feed">', feed)
        self.assertIn('This is my feed; you can use it to follow my site. Feeds work in any reader;', feed)
        self.assertIn('you don&#x27;t need a Facebook™ or Twitter (𝕏) to access them.', feed)
        self.assertIn('Copy <xhtml:a href="https://labyrinth.example/feed.xml">the feed URL</xhtml:a> into a feed reader to follow new work.', feed)
        self.assertIn("Better readers could make this as good as any social network", feed)
        self.assertIn('The first step is to make feeds easy to use. More to come: in the meantime I recommend you start with <xhtml:a href="https://aboutfeeds.com/"><xhtml:em>About Feeds.</xhtml:em></xhtml:a>', feed)
        self.assertIn('Human readable feed layout inspired by <xhtml:a href="https://justinjackson.ca/xslt"><xhtml:em>Don&#x27;t kill my pretty RSS feed.</xhtml:em></xhtml:a>', feed)
        self.assertIn('<subtitle>Metadata summary for the fixture.</subtitle>', feed)
        self.assertIn('<id>https://labyrinth.example/id/first-room</id>', feed)
        self.assertIn('<published>2024-02-14T00:00:00Z</published>', feed)
        self.assertIn('<updated>2024-02-14T00:00:00Z</updated>', feed)
        self.assertIn('<xhtml:a xmlns:xhtml="http://www.w3.org/1999/xhtml" class="feed-entry-url" href="https://labyrinth.example/first-room">https://labyrinth.example/first-room</xhtml:a>', feed)
        self.assertIn('<content type="html">&lt;h2 id=&quot;opening&quot;&gt;&lt;a class=&quot;heading-anchor&quot; href=&quot;https://labyrinth.example/first-room#opening&quot;&gt;Opening&lt;/a&gt;&lt;/h2&gt;', feed)
        self.assertNotIn("<rss", feed)
        self.assertIn(
            'url("fonts/et-book/et-book-display-italic-old-style-figures/et-book-display-italic-old-style-figures.woff")',
            stylesheet,
        )
        self.assertIn(
            'url("fonts/et-book/et-book-bold-line-figures/et-book-bold-line-figures.woff")',
            stylesheet,
        )

    def test_named_sections_fixture(self) -> None:
        _, publish_root = self.build_fixture("named-sections")
        self.assert_common_public_layout(publish_root, ["/essay-fragment", "/folded-map"])

        home_page = self.page_text(publish_root, "/")
        folded_map = self.page_text(publish_root, "/folded-map")

        self.assertIn('class="works-entry"', home_page)
        self.assertNotIn('class="works-entry-date works-date"', home_page)
        self.assertIn(">Essays</h3>", home_page)
        self.assertIn(">Projects</h3>", home_page)
        self.assertIn(">Cabinet</h3>", home_page)
        self.assertIn("Reflective prose and finished arguments.", home_page)
        self.assertIn("Built things and working artifacts.", home_page)
        self.assertIn("References and adjacent material.", home_page)
        essays_index = home_page.index(">Essays</h3>")
        projects_index = home_page.index(">Projects</h3>")
        cabinet_index = home_page.index(">Cabinet</h3>")
        essay_fragment_index = home_page.index(">Essay Fragment<")
        folded_map_index = home_page.index(">Folded Map<")
        self.assertLess(essays_index, projects_index)
        self.assertLess(projects_index, cabinet_index)
        self.assertLess(essays_index, essay_fragment_index)
        self.assertLess(projects_index, folded_map_index)
        self.assertEqual(2, home_page.count('class="works-entry"'))
        self.assertIn('<section class="site-contents-group site-contents-group--current">', folded_map)
        self.assertIn('<p class="site-contents-summary">Projects</p>', folded_map)
        self.assertIn('<span class="site-contents-current" aria-current="page">Folded Map</span>', folded_map)
        self.assertNotIn("<details", folded_map)
        self.assertNotIn("<summary", folded_map)
        self.assertNotIn('<p class="site-contents-summary">Essays</p>', folded_map)
        self.assertNotIn("Built things and working artifacts.", folded_map)
        self.assertNotIn('class="site-link site-contents-link" href="../essay-fragment">Essay Fragment</a>', folded_map)

    def test_section_fallback_fixture(self) -> None:
        _, publish_root = self.build_fixture("section-fallback")
        self.assert_common_public_layout(publish_root, ["/night-walk"])

        home_page = self.page_text(publish_root, "/")
        self.assertIn(">Other works</h3>", home_page)
        self.assertIn(">Night Walk<", home_page)

    def test_html_work_fixture(self) -> None:
        _, publish_root = self.build_fixture("html-work")
        self.assert_common_public_layout(publish_root, ["/studio-note"])

        studio_note = self.page_text(publish_root, "/studio-note")

        self.assertIn('<h1 class="page-title work-title p-name">Studio Note</h1>', studio_note)
        self.assertIn('<div class="work-body e-content">', studio_note)
        self.assertIn("<section>", studio_note)
        self.assertIn('document.documentElement.dataset.work = "studio-note";', studio_note)
        self.assertLess(
            studio_note.index('<h1 class="page-title work-title p-name">Studio Note</h1>'),
            studio_note.index("document.documentElement.dataset.work"),
        )

    def test_reading_microfeatures_fixture(self) -> None:
        _, publish_root = self.build_fixture("reading-microfeatures")
        self.assert_common_public_layout(publish_root, ["/field-notes", "/garden-path"])

        field_notes = self.page_text(publish_root, "/field-notes")
        garden_path = self.page_text(publish_root, "/garden-path")
        home_page = self.page_text(publish_root, "/")
        feed = (publish_root / "feed.xml").read_text(encoding="utf-8")
        stylesheet = (publish_root / "site.css").read_text(encoding="utf-8")

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
        self.assertIn('<a class="internal-link work-link" href="../garden-path">Garden Path</a>', field_notes)
        self.assertIn('<a class="external-link" href="https://archive.example/atlas">Archive Atlas</a>', field_notes)
        self.assertIn('class="site-sidebar"', field_notes)
        self.assertIn('<a class="site-back-link" href="../#contents">Back to contents</a>', field_notes)
        self.assertIn('class="site-bar"', field_notes)
        self.assertIn('site-bar-section--contents', field_notes)
        self.assertIn('<section class="site-contents-group site-contents-group--current">', field_notes)
        self.assertIn('<p class="site-contents-summary">Other works</p>', field_notes)
        self.assertIn('class="site-link site-contents-link" href="../garden-path">Garden Path</a>', field_notes)
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
        self.assertIn('id="contents"', home_page)
        self.assertIn('<h2 class="page-title page-title--section" id="contents-heading"><a class="home-contents-heading-link" href="#contents">Read</a></h2>', home_page)
        self.assertIn('href="garden-path"', home_page)
        self.assertIn('<id>https://labyrinth.example/id/field-notes</id>', feed)
        self.assertIn('<updated>2024-08-04T10:00:00Z</updated>', feed)
        self.assertIn(
            '&lt;a class=&quot;internal-link work-link&quot; href=&quot;https://labyrinth.example/garden-path&quot;&gt;Garden Path&lt;/a&gt;',
            feed,
        )
        self.assertIn(
            '&lt;a class=&quot;external-link&quot; href=&quot;https://archive.example/atlas&quot;&gt;Archive Atlas&lt;/a&gt;',
            feed,
        )
        self.assertNotIn('class="works-entry-date works-date"', home_page)
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
        self.assertIn("width: var(--margin-width);", stylesheet)
        self.assertIn("margin-right: calc(var(--margin-track-span) * -1);", stylesheet)
        self.assertIn("grid-template-columns: minmax(0, var(--measure)) var(--margin-width);", stylesheet)
        self.assertIn("max-width: var(--margin-width);", stylesheet)
        self.assertIn("grid-column: 2;", stylesheet)
        self.assertIn("grid-row: 1;", stylesheet)
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
        self.assertIn(".site-nav--global", stylesheet)
        self.assertNotIn(".link-row", stylesheet)
        self.assertIn(".reading-prose", stylesheet)
        self.assertIn("--scale-base: 1rem;", stylesheet)
        self.assertIn("--scale-ratio: calc(7 / 6);", stylesheet)
        self.assertIn("--step-n4: calc(var(--scale-base) * pow(var(--scale-ratio), -4));", stylesheet)
        self.assertIn("--step-p16: calc(var(--scale-base) * pow(var(--scale-ratio), 16));", stylesheet)
        self.assertIn("--text-2xs: clamp(var(--step-n2), calc(var(--step-n2) + 0.18vw), var(--step-n1));", stylesheet)
        self.assertIn("--text-xs: clamp(var(--step-n1), calc(var(--step-n1) + 0.22vw), var(--step-0));", stylesheet)
        self.assertIn("--text-sm: clamp(var(--step-0), calc(var(--step-0) + 0.24vw), var(--step-p1));", stylesheet)
        self.assertIn("--text-base: clamp(var(--step-0), calc(var(--step-0) + 0.32vw), var(--step-p1));", stylesheet)
        self.assertIn("--page-title-display-size: clamp(var(--step-p6), calc(var(--step-p5) + 2.8vw), var(--step-p10));", stylesheet)
        self.assertIn("--page-title-section-size: clamp(var(--step-p3), calc(var(--step-p3) + 0.6vw), var(--step-p5));", stylesheet)
        self.assertIn("--page-title-work-size: clamp(var(--step-p5), calc(var(--step-p4) + 1.45vw), var(--step-p8));", stylesheet)
        self.assertIn("--reading-h1-size: clamp(var(--step-p2), calc(var(--step-p1) + 0.75vw), var(--step-p4));", stylesheet)
        self.assertIn("--reading-h2-size: clamp(var(--step-p1), calc(var(--step-p1) + 0.4vw), var(--step-p3));", stylesheet)
        self.assertIn("--reading-h3-size: clamp(var(--step-0), calc(var(--step-0) + 0.18vw), var(--step-p1));", stylesheet)
        self.assertIn("--leading-running: calc(var(--scale-ratio) * var(--scale-ratio));", stylesheet)
        self.assertIn("--leading-tight: var(--scale-ratio);", stylesheet)
        self.assertNotIn("--scale-ratio: 1.18;", stylesheet)
        self.assertIn("--rail-guide-left: 0.16rem;", stylesheet)
        self.assertIn("--rail-guide-width: 0.085rem;", stylesheet)
        self.assertIn("--rail-guide-dot-size: 0.44rem;", stylesheet)
        self.assertIn("--rail-guide-dot-gap: 0.15rem;", stylesheet)
        self.assertIn("--rail-guide-center-adjust: 0.03ex;", stylesheet)
        self.assertIn("--rail-guide-dot-offset: calc(var(--step-n4) / 18);", stylesheet)
        self.assertIn("--measure: clamp(66ch, calc(58ch + 4vw), 78ch);", stylesheet)
        self.assertIn("--home-column-measure: clamp(52ch, calc(46ch + 5vw), 60ch);", stylesheet)
        self.assertIn("--work-title-measure: 18ch;", stylesheet)
        self.assertIn("--sidebar-width: 11rem;", stylesheet)
        self.assertNotIn("--page-deck-measure:", stylesheet)
        self.assertIn("--home-contents-measure: min(var(--reading-span), 70rem);", stylesheet)
        self.assertIn("--home-main-indent: max(var(--site-side-space), calc((100vw - var(--home-contents-measure)) / 2));", stylesheet)
        self.assertIn("--home-contents-label-width: clamp(6.75rem, 8vw, 7.5rem);", stylesheet)
        self.assertIn("--date-width: clamp(12rem, calc(11rem + 1.5vw), 13rem);", stylesheet)
        self.assertIn("--margin-width: var(--date-width);", stylesheet)
        self.assertIn("--page-column-gap: clamp(var(--step-p5), 5vw, var(--step-p10));", stylesheet)
        self.assertIn("--margin-track-span: calc(var(--page-column-gap) + var(--margin-width));", stylesheet)
        self.assertIn("--reading-span: calc(var(--measure) + var(--margin-track-span));", stylesheet)
        self.assertIn("--rail-corner-space: var(--site-side-space);", stylesheet)
        self.assertIn("--rail-link-size: var(--text-2xs);", stylesheet)
        self.assertIn("--site-top-space: clamp(var(--step-p3), 5vh, var(--step-p7));", stylesheet)
        self.assertIn("--site-side-space: clamp(var(--step-0), 3.2vw, var(--step-p3));", stylesheet)
        self.assertIn("--site-side-space-narrow: clamp(var(--step-0), 4vw, var(--step-p2));", stylesheet)
        self.assertIn("--site-bottom-space: clamp(var(--step-p6), 8vw, var(--step-p10));", stylesheet)
        self.assertIn("--page-stack-gap: clamp(var(--step-p3), 4vw, var(--step-p5));", stylesheet)
        self.assertIn("--home-stack-gap: clamp(var(--step-p7), 8vh, var(--step-p10));", stylesheet)
        self.assertIn("--cover-top-space: clamp(var(--step-p5), 10vh, var(--step-p10));", stylesheet)
        self.assertIn("--prose-flow-space: var(--step-0);", stylesheet)
        self.assertIn("--prose-heading-space: clamp(var(--step-p4), 4vw, var(--step-p7));", stylesheet)
        self.assertIn("--note-stack-gap: var(--step-0);", stylesheet)
        self.assertIn("--rail-bar-gap: clamp(var(--step-p2), 2.2vw, var(--step-p4));", stylesheet)
        self.assertIn("--rail-section-stack-gap: calc(var(--step-n1) - var(--rail-item-gap));", stylesheet)
        self.assertIn("--rail-contents-gap: calc(var(--step-0) - var(--step-n3));", stylesheet)
        self.assertIn("--rail-group-gap: clamp(var(--step-p2), 2vw, var(--step-p4));", stylesheet)
        self.assertIn("--rail-section-gap: clamp(var(--step-n4), 0.6vw, var(--step-n2));", stylesheet)
        self.assertIn("--rail-item-gap: calc(var(--step-n3) / 2);", stylesheet)
        self.assertIn("--rail-inline-gap: calc(var(--step-n4) / 5);", stylesheet)
        self.assertIn("--rail-inline-group-gap: calc(var(--step-n4) / 4);", stylesheet)
        self.assertIn("--rail-inline-indent: calc(var(--step-n1) - var(--rail-inline-gap));", stylesheet)
        self.assertIn("--rail-nav-gap: var(--step-n4);", stylesheet)
        self.assertIn("--rail-summary-gap: calc(var(--step-0) - var(--rail-item-gap));", stylesheet)
        self.assertIn("--works-section-stack-gap: clamp(var(--step-p3), 5vh, var(--step-p6));", stylesheet)
        self.assertIn("--works-list-gap: calc(var(--step-n4) / 2);", stylesheet)
        self.assertIn("--works-entry-min-height: var(--step-p2);", stylesheet)
        self.assertIn("--works-entry-pad-block: calc(var(--step-n2) / 2);", stylesheet)
        self.assertIn("--leader-dot-offset: 0.02em;", stylesheet)
        self.assertIn("--blockquote-pad-inline: var(--step-p1);", stylesheet)
        self.assertIn("--list-indent: var(--step-p2);", stylesheet)
        self.assertIn("--code-block-pad-inline: var(--step-0);", stylesheet)
        self.assertIn("--sidenote-pad-inline: var(--step-n1);", stylesheet)
        self.assertIn("--mobile-nav-gap: calc(var(--step-n1) - var(--rail-item-gap));", stylesheet)
        self.assertIn("--mobile-contents-gap: var(--step-n1);", stylesheet)
        self.assertIn("--rail-marker-center: calc(0.5lh + var(--rail-guide-center-adjust));", stylesheet)
        self.assertIn(
            "--rail-marker-track-inset: calc(var(--rail-marker-center) - (var(--rail-guide-dot-size) / 2));",
            stylesheet,
        )
        self.assertRegex(stylesheet, r"body\s*\{[^}]*line-height:\s*var\(--leading-running\)")
        self.assertRegex(stylesheet, r"\.page-title\s*\{[^}]*line-height:\s*var\(--leading-tight\)")
        self.assertIn("padding: var(--site-top-space) var(--site-side-space) var(--site-bottom-space);", stylesheet)
        self.assertIn("min-height: calc(100vh - var(--site-top-space) - var(--rail-corner-space));", stylesheet)
        self.assertIn("@media (max-width: 62rem)", stylesheet)
        self.assertIn("@media (max-width: 50rem)", stylesheet)
        self.assertEqual(4, stylesheet.count("@media "))
        self.assertRegex(
            stylesheet,
            r"\.site-page--home \.page--home,\s*\.site-page--home \.page--cover\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)",
        )
        self.assertRegex(
            stylesheet,
            r"@media \(max-width: 50rem\)\s*\{[^}]*\.work-page\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)",
        )
        self.assertRegex(stylesheet, r"\.site-frame\s*\{[^}]*width:\s*100%")
        self.assertNotIn("margin: 0 auto;", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.site-layout\s*\{[^}]*grid-template-columns:\s*var\(--sidebar-width\) minmax\(0, var\(--reading-span\)\)",
        )
        self.assertRegex(stylesheet, r"\.site-sidebar\s*\{[^}]*position:\s*sticky")
        self.assertRegex(stylesheet, r"\.site-sidebar\s*\{[^}]*top:\s*var\(--site-top-space\)")
        self.assertNotIn(".feed-link::after", stylesheet)
        self.assertNotIn('a[href="feed.xml"]::after', stylesheet)
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
            r"\.reading-prose \.internal-link,\s*\.external-link\s*\{[^}]*color:\s*var\(--accent\)[^}]*text-decoration:\s*none",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-contents-link,\s*\.site-contents-current,\s*\.site-link--work-index\s*\{[^}]*font-family:\s*var\(--sans\)[^}]*font-size:\s*var\(--rail-link-size\)",
        )
        self.assertRegex(
            stylesheet,
            r"\.site-link--work-index\s*\{[^}]*line-height:\s*var\(--leading-running\)[^}]*text-decoration:\s*none",
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
            r"\.site-contents-item\.is-current\s*\{[^}]*gap:\s*var\(--rail-inline-group-gap\)",
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
        self.assertNotIn("gap: 1.6rem;", stylesheet)
        self.assertNotIn("gap: 0.75rem;", stylesheet)
        self.assertNotIn("gap: 0.6rem;", stylesheet)
        self.assertNotIn("gap: 0.55rem;", stylesheet)
        self.assertNotIn("gap: 0.8rem;", stylesheet)
        self.assertNotIn("padding: 0.4rem 0;", stylesheet)
        self.assertNotIn("margin-top: 0.7rem;", stylesheet)
        self.assertNotIn("margin-top: 0.45rem;", stylesheet)
        self.assertNotIn("--measure: clamp(38rem, calc(34rem + 8vw), 42rem);", stylesheet)
        self.assertRegex(
            stylesheet,
            r"\.site-link--work-index:hover,\s*\.site-link--work-index:focus-visible\s*\{[^}]*color:\s*inherit",
        )
        self.assertIn('<h2 class="backlinks-title" id="backlinks-title">Backlinks</h2>', garden_path)
        self.assertIn('<a href="../field-notes">Field Notes</a>', garden_path)
        self.assertLess(
            garden_path.index("A hedge note for the return path."),
            garden_path.index("Backlinks"),
        )

    def test_wikilinks_and_assets_fixture(self) -> None:
        _, publish_root = self.build_fixture("wikilinks-and-assets")
        self.assert_common_public_layout(publish_root, ["/garden-path", "/orchard-note"])

        orchard_note = self.page_text(publish_root, "/orchard-note")

        self.assertEqual(2, orchard_note.count('class="internal-link work-link" href="../garden-path"'))
        self.assertIn('class="site-link site-contents-link" href="../garden-path">Garden Path</a>', orchard_note)
        self.assertIn('<a class="internal-link work-link" href="../garden-path">Garden Path</a>', orchard_note)
        self.assertIn('<a class="internal-link work-link" href="../garden-path">Mapped</a>', orchard_note)
        self.assertIn("Cafe", orchard_note)
        self.assertIn("Elsewhere", orchard_note)
        self.assertNotIn('href="Cafe"', orchard_note)
        self.assertNotIn(">Cafe</a>", orchard_note)
        self.assertNotIn(">Elsewhere</a>", orchard_note)

    def test_starter_site_uses_make_reality_sections_and_write_link(self) -> None:
        publish_root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "public"
        build_site(REPO_ROOT / "site", publish_root)

        home_page = self.page_text(publish_root, "/")
        bibliography = self.page_text(publish_root, "/bibliography")

        self.assertIn('<h1 class="page-title page-title--display cover-title">Make Reality</h1>', home_page)
        self.assertIn("Wanting to know one another<br>", home_page)
        self.assertIn("they made the Universe.", home_page)
        self.assertIn('href="#contents">Read</a></h2>', home_page)
        self.assertIn(">Poems</h3>", home_page)
        self.assertIn(">Notes</h3>", home_page)
        self.assertIn(">Studies</h3>", home_page)
        self.assertIn(">Guides</h3>", home_page)
        self.assertIn(">Projects</h3>", home_page)
        self.assertIn(">Cabinet</h3>", home_page)
        self.assertIn("nothing here is real, but it is the stuff of reality", home_page)
        self.assertIn("how I&#x27;ve solved problems", home_page)
        self.assertIn('href="https://tally.so/r/PLACEHOLDER">Write</a>', home_page)
        self.assertIn("Mechanical Watch", bibliography)

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
        self.assertIn("feed.css", files)
        self.assertIn("site.css", files)
        self.assertIn(ET_BOOK_ROMAN, files)
        self.assertIn(ET_BOOK_ITALIC, files)
        self.assertIn(ET_BOOK_BOLD, files)
        self.assertIn(ET_BOOK_LICENSE, files)
        self.assertNotIn("site.js", files)
        for path in files:
            self.assertTrue(
                path == "feed.xml"
                or path == "feed.css"
                or path == "site.css"
                or path.startswith("fonts/et-book/")
                or path.endswith("/index.html")
                or path == "index.html"
            )

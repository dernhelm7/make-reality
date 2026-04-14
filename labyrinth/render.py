from __future__ import annotations

from dataclasses import dataclass
from email.utils import format_datetime
from html import escape
from pathlib import Path

from .markup import Heading
from .model import BuildError, ContentsSection, SiteGraph, WorkDocument
from .urls import canonical_url, page_base_href, relative_public_href, rewrite_root_relative_url

TOC_LEADER_DOTS = "&middot;&nbsp;" * 48


@dataclass(frozen=True)
class RenderedPage:
    public_path: str
    output_path: Path
    html: str
    source_path: Path


def join_html_lines(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


def indent_html(html: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in html.splitlines())


def render_pages(graph: SiteGraph) -> list[RenderedPage]:
    rendered = [
        RenderedPage(
            public_path="/",
            output_path=Path("index.html"),
            html=render_home_page(graph),
            source_path=graph.site.source_path,
        ),
    ]
    for work in graph.works:
        rendered.append(
            RenderedPage(
                public_path=work.public_path,
                output_path=Path(work.public_path.lstrip("/")) / "index.html",
                html=render_work_page(graph, work),
                source_path=work.body_path,
            )
        )
    return rendered


def render_home_page(graph: SiteGraph) -> str:
    content = join_html_lines(
        '<div class="page page--home">',
        '  <section class="page page--cover cover">',
        '    <header class="page-head page-head--cover">',
        f'      <h1 class="page-title page-title--display cover-title">{escape(graph.site.title)}</h1>',
        f'      <p class="page-deck cover-statement">{escape(graph.site.statement)}</p>',
        "    </header>",
        '    <div class="home-cover-meta">',
        indent_html(render_global_links_section(graph, current_public_path="/"), 6),
        "    </div>",
        "  </section>",
        '  <section class="page home-contents" id="contents" aria-labelledby="contents-heading">',
        '    <header class="page-head">',
        '      <h2 class="page-title page-title--section" id="contents-heading">Contents</h2>',
        "    </header>",
        '    <div class="page-body works-body">',
        indent_html(render_contents_sections(graph, current_public_path="/"), 6),
        "    </div>",
        "  </section>",
        "</div>",
    )
    return render_page(
        graph=graph,
        public_path="/",
        page_title=graph.site.title,
        page_kind="home",
        sidebar_html="",
        main_content=content,
        head_extra_html="",
    )


def render_work_page(graph: SiteGraph, work: WorkDocument) -> str:
    backlinks_html = render_backlinks(graph, work)
    date_note_html = (
        '<aside class="work-date-note" aria-label="Published">'
        f'<time class="work-date dt-published" datetime="{escape(work.created.isoformat())}">{escape(format_long_date(work.created))}</time>'
        "</aside>"
    )
    content = join_html_lines(
        '<article class="page page--work work-page h-entry">',
        '  <header class="page-head work-header">',
        f'    <h1 class="page-title work-title p-name">{escape(work.title)}</h1>',
        f'    <a class="visually-hidden u-url" href="{escape(work.canonical_url)}">Permalink</a>',
        "  </header>",
        f"  {date_note_html}",
        '  <div class="page-body">',
        '    <div class="reading-layout">',
        '      <div class="reading-column">',
        '        <div class="work-body e-content">',
        '          <div class="work-body-inner reading-prose e-content">',
        indent_html(work.body.html, 12),
        "          </div>",
        "        </div>",
        indent_html(backlinks_html, 8),
        "      </div>",
        "    </div>",
        "  </div>",
        "</article>",
    )
    return render_page(
        graph=graph,
        public_path=work.public_path,
        page_title=f"{work.title} - {graph.site.title}",
        page_kind="work",
        sidebar_html=render_site_sidebar(graph, current_work=work),
        main_content=content,
        head_extra_html=render_work_heading_target_styles(work.top_level_headings),
    )


def render_backlinks(graph: SiteGraph, work: WorkDocument) -> str:
    backlinks = graph.backlinks.get(work.public_path, ())
    if not backlinks:
        return ""

    items = join_html_lines(
        *(
            join_html_lines(
                "<li>",
                f'  <a href="{escape(relative_public_href(work.public_path, item.public_path))}">{escape(item.title)}</a>',
                "</li>",
            )
            for item in backlinks
        )
    )
    return join_html_lines(
        '<section class="backlinks" aria-labelledby="backlinks-title">',
        '  <h2 class="backlinks-title" id="backlinks-title">Backlinks</h2>',
        '  <ul class="backlinks-list">',
        indent_html(items, 4),
        "  </ul>",
        "</section>",
    )


def render_contents_sections(graph: SiteGraph, *, current_public_path: str) -> str:
    return join_html_lines(
        *(render_contents_section(section, current_public_path=current_public_path) for section in graph.contents_sections)
    )


def render_contents_section(section: ContentsSection, *, current_public_path: str) -> str:
    items = join_html_lines(
        *(render_works_entry(work, current_public_path=current_public_path) for work in section.works)
    )
    return join_html_lines(
        '<section class="works-section">',
        f'  <h2 class="section-heading" id="{escape(section.anchor_id)}">{escape(section.name)}</h2>',
        '  <ol class="works-list">',
        indent_html(items, 4),
        "  </ol>",
        "</section>",
    )


def render_works_entry(work: WorkDocument, *, current_public_path: str) -> str:
    return join_html_lines(
        '<li class="works-entry">',
        f'  <a class="works-entry-link" href="{escape(relative_public_href(current_public_path, work.public_path))}">{escape(work.title)}</a>',
        f'  <span class="works-entry-leader toc-leader" aria-hidden="true">{TOC_LEADER_DOTS}</span>',
        "</li>",
    )


def render_page(
    *,
    graph: SiteGraph,
    public_path: str,
    page_title: str,
    page_kind: str,
    sidebar_html: str,
    main_content: str,
    head_extra_html: str,
) -> str:
    canonical = canonical_url(graph.site.base_url, public_path)
    base_href = page_base_href(graph.site.base_url, public_path)
    return join_html_lines(
        "<!DOCTYPE html>",
        f'<html lang="{escape(graph.site.lang)}">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{escape(page_title)}</title>",
        f'  <meta name="description" content="{escape(graph.site.statement)}">',
        '  <meta name="theme-color" content="#0a7c80">',
        f'  <base href="{escape(base_href)}">',
        f'  <link rel="canonical" href="{escape(canonical)}">',
        f'  <link rel="stylesheet" href="{escape(relative_public_href(public_path, "/site.css"))}">',
        f'  <link rel="alternate" type="application/rss+xml" title="{escape(graph.site.title)} feed" href="{escape(relative_public_href(public_path, "/feed.xml"))}">',
        indent_html(head_extra_html, 2),
        "</head>",
        f'<body class="site-page site-page--{escape(page_kind)}">',
        '  <div class="site-shell">',
        '    <div class="page-surface">',
        '      <div class="site-frame">',
        '        <div class="site-layout">',
        indent_html(sidebar_html, 10),
        '          <main class="site-main">',
        indent_html(main_content, 12),
        "          </main>",
        "        </div>",
        "      </div>",
        "    </div>",
        "  </div>",
        "</body>",
        "</html>",
    )


def render_site_sidebar(graph: SiteGraph, current_work: WorkDocument | None = None) -> str:
    current_public_path = current_work.public_path if current_work else "/"
    return join_html_lines(
        '<aside class="site-sidebar">',
        '  <div class="site-bar">',
        indent_html(render_sidebar_primary(graph, current_work), 4),
        indent_html(render_global_links_section(graph, current_public_path=current_public_path), 4),
        "  </div>",
        "</aside>",
    )


def normalize_sidebar_items(items: list[object]) -> list[tuple[str, str]]:
    normalized: list[tuple[str, str]] = []
    for item in items:
        if isinstance(item, tuple):
            normalized.append(item)
            continue
        normalized.append((item.label, item.href))
    return normalized


def render_sidebar_primary(graph: SiteGraph, current_work: WorkDocument | None) -> str:
    if current_work is None:
        return ""

    contents_groups_html = render_sidebar_contents_groups(graph, current_work)
    return join_html_lines(
        '<div class="site-bar-section site-bar-section--primary">',
        f'  <a class="site-back-link" href="{escape(relative_public_href(current_work.public_path, "/", fragment="contents"))}">Back to contents</a>',
        "</div>",
        '<section class="site-bar-section site-bar-section--contents" aria-labelledby="site-contents-label">',
        '  <h2 class="site-contents-label visually-hidden" id="site-contents-label">Site contents</h2>',
        '  <div class="site-contents-groups">',
        indent_html(contents_groups_html, 4),
        "  </div>",
        "</section>",
    )


def render_global_links_section(graph: SiteGraph, *, current_public_path: str) -> str:
    items = graph.site.contact_links + graph.site.gift_links + [("RSS", "/feed.xml")]
    links_html = join_html_lines(
        *(
            f'<a class="site-link{" feed-link" if href == "/feed.xml" else ""}" href="{escape(rewrite_root_relative_url(current_public_path, href))}">{escape(label)}</a>'
            for label, href in normalize_sidebar_items(items)
        )
    )
    return join_html_lines(
        '<div class="site-bar-section site-bar-section--global">',
        '  <p class="site-global-label visually-hidden">Links</p>',
        '  <nav class="site-nav site-nav--global" aria-label="Global links">',
        indent_html(links_html, 4),
        "  </nav>",
        "</div>",
    )


def render_sidebar_contents_groups(graph: SiteGraph, current_work: WorkDocument) -> str:
    current_section = graph.contents_section_by_name.get(current_work.resolved_section)
    if current_section is None:
        return ""

    items = join_html_lines(
        *(render_sidebar_contents_item(work, current_work) for work in current_section.works)
    )
    return join_html_lines(
        '<section class="site-contents-group site-contents-group--current">',
        f'  <p class="site-contents-summary">{escape(current_section.name)}</p>',
        '  <ol class="site-contents-list">',
        indent_html(items, 4),
        "  </ol>",
        "</section>",
    )


def render_sidebar_contents_item(work: WorkDocument, current_work: WorkDocument) -> str:
    if work.public_path == current_work.public_path:
        inline_headings_html = ""
        if len(current_work.top_level_headings) >= 2:
            heading_links = join_html_lines(
                *(
                    join_html_lines(
                        f'<li class="site-work-headings-item" data-anchor-id="{escape(heading.anchor_id)}">',
                        f'  <a class="site-link site-link--work-index" href="#{escape(heading.anchor_id)}">{escape(heading.text)}</a>',
                        "</li>",
                    )
                    for heading in current_work.top_level_headings
                )
            )
            inline_headings_html = join_html_lines(
                '<ol class="site-work-headings-list">',
                indent_html(heading_links, 2),
                "</ol>",
            )
        return join_html_lines(
            '<li class="site-contents-item is-current">',
            f'  <span class="site-contents-current" aria-current="page">{escape(work.title)}</span>',
            indent_html(inline_headings_html, 2),
            "</li>",
        )

    return join_html_lines(
        '<li class="site-contents-item">',
        f'  <a class="site-link site-contents-link" href="{escape(relative_public_href(current_work.public_path, work.public_path))}">{escape(work.title)}</a>',
        "</li>",
    )


def render_work_heading_target_styles(headings: tuple[Heading, ...]) -> str:
    if len(headings) < 2:
        return ""

    rules = [
        ".site-page--work:has(.work-body :target) .site-work-headings-item:first-child::before { opacity: 0; }",
        ".site-page--work:has(.work-body :target) .site-work-headings-item:first-child .site-link--work-index {"
        " color: color-mix(in srgb, var(--ink) 72%, var(--page)); }",
    ]
    for heading in headings:
        anchor = css_string_literal(heading.anchor_id)
        rules.append(
            '.site-page--work:has(.work-body [id="'
            + anchor
            + '"]:target) .site-work-headings-item[data-anchor-id="'
            + anchor
            + '"]::before { opacity: 1; }'
        )
        rules.append(
            '.site-page--work:has(.work-body [id="'
            + anchor
            + '"]:target) .site-work-headings-item[data-anchor-id="'
            + anchor
            + '"] .site-link--work-index { color: var(--ink); }'
        )
    return join_html_lines(
        '<style class="site-work-index-targets">',
        *rules,
        "</style>",
    )


def render_feed(graph: SiteGraph) -> str:
    items = []
    for work in graph.works:
        items.append(
            "<item>"
            f"<title>{xml_escape(work.title)}</title>"
            f"<link>{xml_escape(work.canonical_url)}</link>"
            f"<guid>{xml_escape(work.canonical_url)}</guid>"
            f"<pubDate>{xml_escape(format_datetime(work.created))}</pubDate>"
            f"<description>{xml_escape(work.title)}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0">'
        "<channel>"
        f"<title>{xml_escape(graph.site.title)}</title>"
        f"<link>{xml_escape(graph.site.base_url + '/')}</link>"
        f"<description>{xml_escape(graph.site.statement)}</description>"
        f"<language>{xml_escape(graph.site.lang)}</language>"
        f"{''.join(items)}"
        "</channel>"
        "</rss>"
    )


def validate_rendered_pages(rendered_pages: list[RenderedPage]) -> None:
    for page in rendered_pages:
        if '<link rel="canonical"' not in page.html:
            raise BuildError(page.source_path, "missing-canonical-link", f"{page.public_path} is missing a canonical link")


def format_long_date(value) -> str:
    return value.strftime("%d %B %Y")


def css_string_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

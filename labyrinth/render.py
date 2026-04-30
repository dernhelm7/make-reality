from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

from .markup import BodyContext, Heading, render_markdown_paragraphs
from .model import BuildError, ContentsSection, LinkItem, SiteGraph, WorkDocument
from .urls import (
    FEED_PUBLIC_PATH,
    FEED_STYLESHEET_PUBLIC_PATH,
    HOME_PUBLIC_PATH,
    PageUrls,
    SITE_STYLESHEET_PUBLIC_PATH,
)

TOC_LEADER_DOTS = "&middot;&nbsp;" * 48
TALLY_EMBED_QUERY = "alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1&formEventsForwarding=1"


@dataclass(frozen=True)
class RenderedPage:
    public_path: str
    output_path: Path
    html: str
    source_path: Path


@dataclass(frozen=True)
class LinkPreview:
    key: str
    panel_class: str
    label: str
    html: str


def join_html_lines(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


def indent_html(html: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in html.splitlines())


def page_urls(graph: SiteGraph, public_path: str) -> PageUrls:
    return PageUrls(
        site_url=graph.site.site_url,
        build_url=graph.site.build_url,
        public_path=public_path,
    )


def render_pages(graph: SiteGraph) -> list[RenderedPage]:
    rendered = [
        RenderedPage(
            public_path=HOME_PUBLIC_PATH,
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
    urls = page_urls(graph, HOME_PUBLIC_PATH)
    content = join_html_lines(
        '<div class="page page--home">',
        '  <section class="page page--cover cover">',
        '    <header class="page-head page-head--cover">',
        f'      <h1 class="page-title page-title--display cover-title">{escape(graph.site.home.title)}</h1>',
        indent_html(render_home_cover_text(graph), 6),
        "    </header>",
        '    <div class="home-cover-meta">',
        indent_html(render_global_links_section(graph, urls=urls, enable_previews=True), 6),
        "    </div>",
        "  </section>",
        '  <section class="page home-contents" id="contents" aria-labelledby="contents-heading">',
        '    <header class="page-head">',
        f'      <h2 class="page-title page-title--section" id="contents-heading"><a class="home-contents-heading-link" href="#read-index"><span>{escape(graph.site.home.read_label)}</span><span class="home-contents-heading-arrow" aria-hidden="true">&rarr;</span></a></h2>',
        "    </header>",
        '    <div class="page-body works-body" id="read-index">',
        indent_html(render_contents_sections(graph, urls=urls), 6),
        "    </div>",
        "  </section>",
        "</div>",
    )
    return render_page(
        graph=graph,
        urls=urls,
        page_title=graph.site.title,
        page_kind="home",
        sidebar_html="",
        main_content=content,
        head_extra_html="",
    )


def render_work_page(graph: SiteGraph, work: WorkDocument) -> str:
    urls = page_urls(graph, work.public_path)
    backlinks_html = render_backlinks(graph, work, urls=urls)
    date_note_html = (
        '<aside class="work-date-note" aria-label="Published">'
        f'<time class="work-date dt-published" datetime="{escape(work.created.isoformat())}">{escape(format_long_date(work.created))}</time>'
        "</aside>"
    )
    content = join_html_lines(
        '<article class="page page--work work-page h-entry">',
        '  <header class="page-head work-header">',
        f'    <h1 class="page-title work-title p-name">{escape(work.title)}</h1>',
        f'    <a class="visually-hidden u-url" href="{escape(urls.canonical_url)}">Permalink</a>',
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
        urls=urls,
        page_title=f"{work.title} - {graph.site.title}",
        page_kind="work",
        sidebar_html=render_site_sidebar(graph, current_work=work, urls=urls),
        main_content=content,
        head_extra_html=render_work_heading_target_styles(work.top_level_headings),
    )


def render_backlinks(graph: SiteGraph, work: WorkDocument, *, urls: PageUrls) -> str:
    backlinks = graph.backlinks.get(work.public_path, ())
    if not backlinks:
        return ""

    items = join_html_lines(
        *(
            join_html_lines(
                "<li>",
                f'  <a href="{escape(urls.relative_href(item.public_path))}">{escape(item.title)}</a>',
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


def render_contents_sections(graph: SiteGraph, *, urls: PageUrls) -> str:
    section_columns = split_contents_sections(graph.contents_sections)
    return join_html_lines(
        *(render_contents_column(column, urls=urls) for column in section_columns if column)
    )


def split_contents_sections(sections: tuple[ContentsSection, ...]) -> tuple[tuple[ContentsSection, ...], ...]:
    midpoint = (len(sections) + 1) // 2
    return (sections[:midpoint], sections[midpoint:])


def render_contents_column(sections: tuple[ContentsSection, ...], *, urls: PageUrls) -> str:
    return join_html_lines(
        '<div class="works-column">',
        indent_html(
            join_html_lines(*(render_contents_section(section, urls=urls) for section in sections)),
            2,
        ),
        "</div>",
    )


def render_contents_section(section: ContentsSection, *, urls: PageUrls) -> str:
    items = join_html_lines(
        *(render_works_entry(work, urls=urls) for work in section.works)
    )
    description_html = (
        f'      <p class="section-description">{escape(section.description)}</p>' if section.description else ""
    )
    works_list_html = ""
    if items:
        works_list_html = join_html_lines(
            '  <ol class="works-list">',
            indent_html(items, 4),
            "  </ol>",
        )
    return join_html_lines(
        f'<section class="works-section" aria-labelledby="{escape(section.anchor_id)}">',
        '  <header class="works-section-head">',
        '    <div class="works-section-line">',
        f'      <h3 class="section-heading" id="{escape(section.anchor_id)}">{escape(section.name)}</h3>',
        description_html,
        "    </div>",
        "  </header>",
        works_list_html,
        "</section>",
    )


def render_works_entry(work: WorkDocument, *, urls: PageUrls) -> str:
    work_href = escape(urls.relative_href(work.public_path))
    title = escape(work.title)
    reference = escape(work_path_reference(work.public_path))
    return join_html_lines(
        '<li class="works-entry">',
        f'  <a class="works-entry-link" href="{work_href}" aria-label="{title}">',
        f'    <span class="works-entry-reference">{reference}</span>',
        f'    <span class="works-entry-title">{title}</span>',
        f'    <span class="works-entry-leader toc-leader" aria-hidden="true">{TOC_LEADER_DOTS}</span>',
        '    <span class="works-entry-mark" aria-hidden="true">&gt;</span>',
        "  </a>",
        "</li>",
    )


def work_path_reference(public_path: str) -> str:
    return public_path.strip("/") or "/"


def render_page(
    *,
    graph: SiteGraph,
    urls: PageUrls,
    page_title: str,
    page_kind: str,
    sidebar_html: str,
    main_content: str,
    head_extra_html: str,
) -> str:
    return join_html_lines(
        "<!DOCTYPE html>",
        f'<html lang="{escape(graph.site.lang)}">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{escape(page_title)}</title>",
        f'  <meta name="description" content="{escape(graph.site.statement)}">',
        '  <meta name="theme-color" content="#0a7c80">',
        f'  <base href="{escape(urls.base_href)}">',
        f'  <link rel="canonical" href="{escape(urls.canonical_url)}">',
        f'  <link rel="stylesheet" href="{escape(urls.relative_href(SITE_STYLESHEET_PUBLIC_PATH))}">',
        f'  <link rel="alternate" type="application/atom+xml" title="{escape(graph.site.title)} feed" href="{escape(urls.relative_href(FEED_PUBLIC_PATH))}">',
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


def render_site_sidebar(graph: SiteGraph, current_work: WorkDocument | None = None, *, urls: PageUrls) -> str:
    return join_html_lines(
        '<aside class="site-sidebar">',
        '  <div class="site-bar">',
        indent_html(render_sidebar_primary(graph, current_work, urls), 4),
        indent_html(render_global_links_section(graph, urls=urls), 4),
        "  </div>",
        "</aside>",
    )


def render_sidebar_primary(graph: SiteGraph, current_work: WorkDocument | None, urls: PageUrls) -> str:
    if current_work is None:
        return ""

    contents_groups_html = render_sidebar_contents_groups(graph, current_work, urls)
    return join_html_lines(
        '<div class="site-bar-section site-bar-section--primary">',
        f'  <a class="site-back-link" href="{escape(urls.relative_href(HOME_PUBLIC_PATH, fragment="contents"))}">Back to contents</a>',
        "</div>",
        '<section class="site-bar-section site-bar-section--contents" aria-labelledby="site-contents-label">',
        '  <h2 class="site-contents-label visually-hidden" id="site-contents-label">Site contents</h2>',
        '  <div class="site-contents-groups">',
        indent_html(contents_groups_html, 4),
        "  </div>",
        "</section>",
    )


def render_global_links_section(graph: SiteGraph, *, urls: PageUrls, enable_previews: bool = False) -> str:
    items = graph.site.home.links
    previews = tuple(link_preview_for_item(item, graph=graph, urls=urls) for item in items)
    links_html = join_html_lines(
        *(
            render_global_link(
                item,
                preview=preview if enable_previews else None,
                urls=urls,
            )
            for item, preview in zip(items, previews, strict=True)
        )
    )
    preview_html = render_global_link_previews(tuple(preview for preview in previews if preview), urls=urls) if enable_previews else ""
    return join_html_lines(
        '<div class="site-bar-section site-bar-section--global">',
        '  <p class="site-global-label visually-hidden">Links</p>',
        '  <nav class="site-nav site-nav--global" aria-label="Global links">',
        indent_html(links_html, 4),
        "  </nav>",
        indent_html(preview_html, 2),
        "</div>",
    )


def render_global_link(item: LinkItem, *, preview: LinkPreview | None, urls: PageUrls) -> str:
    classes = ["site-link"]
    if item.href == FEED_PUBLIC_PATH:
        classes.append("feed-link")
    if preview:
        classes.append("site-link--preview")

    href = escape(urls.root_relative_href(item.href))
    label = escape(item.label)
    if preview:
        return (
            f'<a class="{" ".join(classes)}" href="{href}" '
            f'data-site-preview-trigger="{escape(preview.key)}" '
            f'aria-controls="site-link-preview-{escape(preview.key)}">{label}</a>'
        )
    return f'<a class="{" ".join(classes)}" href="{href}" data-site-preview-clear>{label}</a>'


def link_preview_for_item(item: LinkItem, *, graph: SiteGraph, urls: PageUrls) -> LinkPreview | None:
    form_src = tally_embed_src(item.href)
    if form_src:
        return LinkPreview(
            key="write",
            panel_class="site-link-preview-panel--embed",
            label=f"{item.label} form",
            html=(
                f'<iframe class="site-link-preview-frame" src="{escape(form_src)}" '
                'loading="lazy" title="Send me a message"></iframe>'
            ),
        )

    if item.href == FEED_PUBLIC_PATH:
        return LinkPreview(
            key="follow",
            panel_class="site-link-preview-panel--text",
            label=f"{item.label} preview",
            html=render_feed_link_preview(graph, urls=urls),
        )

    return None


def render_global_link_previews(previews: tuple[LinkPreview, ...], *, urls: PageUrls) -> str:
    if not previews:
        return ""
    panels = join_html_lines(
        *(
            join_html_lines(
                f'<div class="site-link-preview-panel {preview.panel_class}" id="site-link-preview-{escape(preview.key)}" aria-label="{escape(preview.label)}" hidden>',
                indent_html(preview.html, 2),
                "</div>",
            )
            for preview in previews
        )
    )
    return join_html_lines(
        '<div class="site-link-preview-region" data-site-preview-region>',
        indent_html(panels, 2),
        "  </div>",
        render_global_link_preview_script(),
    )


def render_global_link_preview_script() -> str:
    return join_html_lines(
        '<script>',
        "(() => {",
        "  const root = document.currentScript.closest('.site-bar-section--global');",
        "  const panels = new Map([...root.querySelectorAll('.site-link-preview-panel')].map((panel) => [panel.id.replace('site-link-preview-', ''), panel]));",
        "  const show = (key) => panels.forEach((panel, panelKey) => { panel.hidden = panelKey !== key; });",
        "  const clear = () => panels.forEach((panel) => { panel.hidden = true; });",
        "  root.querySelectorAll('[data-site-preview-trigger]').forEach((link) => {",
        "    const key = link.dataset.sitePreviewTrigger;",
        "    link.addEventListener('pointerenter', () => show(key));",
        "    link.addEventListener('focus', () => show(key));",
        "  });",
        "  root.querySelectorAll('[data-site-preview-clear]').forEach((link) => {",
        "    link.addEventListener('pointerenter', clear);",
        "    link.addEventListener('focus', clear);",
        "  });",
        "})();",
        "</script>",
    )


def render_feed_link_preview(graph: SiteGraph, *, urls: PageUrls) -> str:
    feed_href = urls.relative_href(FEED_PUBLIC_PATH)
    preview_text = feed_link_preview_text(graph.site.feed_guide_text).replace(
        "{feed_url}",
        feed_href,
    )
    paragraphs = render_markdown_paragraphs(
        preview_text,
        context=body_context(graph, HOME_PUBLIC_PATH),
    )
    action = (
        f'<p class="site-link-preview-action"><a class="internal-link" href="{escape(feed_href)}">'
        'Follow <span class="site-link-preview-arrow" aria-hidden="true">&rarr;</span></a></p>'
    )
    return join_html_lines(
        *(f'<p class="site-link-preview-copy">{paragraph.html}</p>' for paragraph in paragraphs),
        action,
    )


def feed_link_preview_text(feed_guide_text: str) -> str:
    paragraphs = tuple(part.strip() for part in feed_guide_text.split("\n\n") if part.strip())
    if not paragraphs:
        return ""
    body_paragraphs = paragraphs[1:] if len(paragraphs) > 1 else paragraphs
    return "\n\n".join(body_paragraphs)


def tally_embed_src(href: str) -> str | None:
    parsed = urlsplit(href)
    host = parsed.netloc.lower()
    if parsed.scheme != "https" or host not in {"tally.so", "www.tally.so"}:
        return None

    path_parts = tuple(part for part in parsed.path.split("/") if part)
    if len(path_parts) != 2 or path_parts[0] not in {"r", "embed"}:
        return None

    form_id = quote(path_parts[1], safe="")
    return f"https://tally.so/embed/{form_id}?{TALLY_EMBED_QUERY}"


def render_sidebar_contents_groups(graph: SiteGraph, current_work: WorkDocument, urls: PageUrls) -> str:
    current_section = graph.contents_section_by_name.get(current_work.resolved_section)
    if current_section is None:
        return ""

    items = join_html_lines(
        *(render_sidebar_contents_item(work, current_work, urls) for work in current_section.works)
    )
    return join_html_lines(
        '<section class="site-contents-group site-contents-group--current">',
        f'  <p class="site-contents-summary">{escape(current_section.name)}</p>',
        '  <ol class="site-contents-list">',
        indent_html(items, 4),
        "  </ol>",
        "</section>",
    )


def render_sidebar_contents_item(work: WorkDocument, current_work: WorkDocument, urls: PageUrls) -> str:
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
        f'  <a class="site-link site-contents-link" href="{escape(urls.relative_href(work.public_path))}">{escape(work.title)}</a>',
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
    feed_urls = page_urls(graph, FEED_PUBLIC_PATH)
    home_urls = page_urls(graph, HOME_PUBLIC_PATH)
    feed_updated = max([graph.site.updated, *(work.updated for work in graph.works)])
    entries = join_html_lines(*(render_feed_entry(graph, work) for work in graph.works))
    return join_html_lines(
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<?xml-stylesheet type="text/css" href="{FEED_STYLESHEET_PUBLIC_PATH.lstrip("/")}"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        indent_html(render_feed_guide(graph, feed_url=feed_urls.output_url), 2),
        f"  <title>{xml_escape(graph.site.title)}</title>",
        f"  <subtitle>{xml_escape(graph.site.statement)}</subtitle>",
        f"  <id>{xml_escape(feed_urls.canonical_url)}</id>",
        f"  <updated>{xml_escape(format_atom_datetime(feed_updated))}</updated>",
        '  <author>',
        f"    <name>{xml_escape(graph.site.author_name)}</name>",
        "  </author>",
        f'  <link rel="self" type="application/atom+xml" href="{xml_escape(feed_urls.output_url)}"/>',
        f'  <link rel="alternate" type="text/html" href="{xml_escape(home_urls.output_url)}"/>',
        indent_html(entries, 2),
        "</feed>",
    )


def render_feed_guide(graph: SiteGraph, *, feed_url: str) -> str:
    guide_text = graph.site.feed_guide_text.replace("{feed_url}", feed_url)
    paragraphs = render_markdown_paragraphs(
        guide_text,
        context=body_context(graph, FEED_PUBLIC_PATH),
        tag_prefix="xhtml:",
        include_link_class=False,
    )
    paragraph_html = []
    for index, paragraph in enumerate(paragraphs):
        class_name = ""
        if index == 0:
            class_name = ' class="feed-guide-label"'
        elif index == len(paragraphs) - 1:
            class_name = ' class="feed-guide-inspiration"'
        paragraph_html.append(f"  <xhtml:p{class_name}>{paragraph.html}</xhtml:p>")
    return join_html_lines(
        '<xhtml:section xmlns:xhtml="http://www.w3.org/1999/xhtml" class="feed-guide" aria-label="How to use this feed">',
        *paragraph_html,
        "</xhtml:section>",
    )


def render_home_cover_text(graph: SiteGraph) -> str:
    paragraphs = render_markdown_paragraphs(
        graph.site.home.cover_text,
        context=body_context(graph, HOME_PUBLIC_PATH),
    )
    return join_html_lines(
        *(f'<p class="page-deck cover-statement">{paragraph.html}</p>' for paragraph in paragraphs)
    )


def body_context(graph: SiteGraph, current_public_path: str) -> BodyContext:
    return BodyContext(
        current_public_path=current_public_path,
        work_lookup=graph.work_lookup,
        work_paths=frozenset(graph.work_by_path),
    )


def validate_rendered_pages(rendered_pages: list[RenderedPage]) -> None:
    for page in rendered_pages:
        if '<link rel="canonical"' not in page.html:
            raise BuildError(page.source_path, "missing-canonical-link", f"{page.public_path} is missing a canonical link")


def format_long_date(value) -> str:
    return value.strftime("%d %B %Y")


def format_atom_datetime(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


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


def render_feed_entry(graph: SiteGraph, work: WorkDocument) -> str:
    urls = page_urls(graph, work.public_path)
    body_html = absolutize_feed_content(work, urls=urls)
    output_url = xml_escape(urls.output_url)
    return join_html_lines(
        "  <entry>",
        f"    <title>{xml_escape(work.title)}</title>",
        f"    <id>{xml_escape(work.atom_id)}</id>",
        f"    <published>{xml_escape(format_atom_datetime(work.created))}</published>",
        f"    <updated>{xml_escape(format_atom_datetime(work.updated))}</updated>",
        f'    <link rel="alternate" type="text/html" href="{output_url}"/>',
        f'    <xhtml:a xmlns:xhtml="http://www.w3.org/1999/xhtml" class="feed-entry-url" href="{output_url}">{output_url}</xhtml:a>',
        f'    <content type="html">{xml_escape(body_html)}</content>',
        "  </entry>",
    )


def absolutize_feed_content(work: WorkDocument, *, urls: PageUrls) -> str:
    parser = FeedContentRewriter(urls)
    parser.feed(work.body.html)
    parser.close()
    return parser.render()


class FeedContentRewriter(HTMLParser):
    def __init__(self, urls: PageUrls) -> None:
        super().__init__(convert_charrefs=False)
        self.urls = urls
        self.output: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.output.append(render_html_start_tag(tag, self.rewrite_attrs(attrs), self_closing=False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.output.append(render_html_start_tag(tag, self.rewrite_attrs(attrs), self_closing=True))

    def handle_endtag(self, tag: str) -> None:
        self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.output.append(data)

    def handle_comment(self, data: str) -> None:
        self.output.append(f"<!--{data}-->")

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&#{name};")

    def rewrite_attrs(self, attrs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
        rewritten: list[tuple[str, str | None]] = []
        for name, value in attrs:
            if value is None or name not in {"href", "src", "poster"}:
                rewritten.append((name, value))
                continue
            rewritten.append((name, self.urls.absolute_href(value)))
        return rewritten

    def render(self) -> str:
        return "".join(self.output)


def render_html_start_tag(tag: str, attrs: list[tuple[str, str | None]], *, self_closing: bool) -> str:
    rendered_attrs = "".join(
        f' {name}' if value is None else f' {name}="{escape(value, quote=True)}"' for name, value in attrs
    )
    closing = " />" if self_closing else ">"
    return f"<{tag}{rendered_attrs}{closing}"

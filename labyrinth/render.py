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
    WRITE_PUBLIC_PATH,
)

TOC_LEADER_DOTS = ".&nbsp;" * 64
TALLY_EMBED_QUERY = "alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1"
TALLY_WIDGET_SCRIPT = (
    'var d=document,w="https://tally.so/widgets/embed.js",v=function(){'
    '"undefined"!=typeof Tally?Tally.loadEmbeds():'
    'd.querySelectorAll("iframe[data-tally-src]:not([src])").forEach((function(e){'
    "e.src=e.dataset.tallySrc"
    '}))};if("undefined"!=typeof Tally)v();else if(d.querySelector(\'script[src="\'+w+\'"]\')==null){'
    'var s=d.createElement("script");s.src=w,s.onload=v,s.onerror=v,d.body.appendChild(s);}'
)


@dataclass(frozen=True)
class RenderedPage:
    public_path: str
    output_path: Path
    html: str
    source_path: Path
    assets: tuple[tuple[Path, Path], ...] = ()


def join_html_lines(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


def indent_html(html: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in html.splitlines())


def render_theme_boot_script() -> str:
    return join_html_lines(
        "<script>",
        "(function () {",
        '  var key = "labyrinth-theme";',
        "  try {",
        "    var theme = sessionStorage.getItem(key);",
        '    if (theme === "dark" || theme === "light") {',
        "      document.documentElement.dataset.theme = theme;",
        "    }",
        "  } catch (error) {}",
        "}());",
        "</script>",
    )


def render_theme_control_script() -> str:
    return join_html_lines(
        "<script>",
        "(function () {",
        '  var key = "labyrinth-theme";',
        "  var root = document.documentElement;",
        '  var toggle = document.getElementById("site-theme-toggle");',
        "  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;",
        "  if (!toggle) {",
        "    return;",
        "  }",
        "  function systemTheme() {",
        '    return media && media.matches ? "dark" : "light";',
        "  }",
        "  function storedTheme() {",
        "    try {",
        "      var theme = sessionStorage.getItem(key);",
        '      if (theme === "dark" || theme === "light") {',
        "        return theme;",
        "      }",
        "    } catch (error) {}",
        '    return "";',
        "  }",
        "  function saveTheme(theme) {",
        "    try {",
        "      if (theme) {",
        "        sessionStorage.setItem(key, theme);",
        "      } else {",
        "        sessionStorage.removeItem(key);",
        "      }",
        "      return true;",
        "    } catch (error) {",
        "      return false;",
        "    }",
        "  }",
        "  function applyTheme(theme) {",
        '    if (theme === "dark" || theme === "light") {',
        "      root.dataset.theme = theme;",
        "    } else {",
        "      delete root.dataset.theme;",
        "    }",
        "  }",
        "  function syncToggle() {",
        "    var system = systemTheme();",
        "    var stored = storedTheme();",
        "    var selected = stored || system;",
        "    applyTheme(stored);",
        "    toggle.checked = selected !== system;",
        "  }",
        "  toggle.addEventListener('change', function () {",
        "    if (toggle.checked) {",
        '      var theme = systemTheme() === "dark" ? "light" : "dark";',
        "      var saved = saveTheme(theme);",
        "      applyTheme(theme);",
        "      if (saved) {",
        "        syncToggle();",
        "      }",
        "    } else {",
        '      var reset = saveTheme("");',
        '      applyTheme("");',
        "      if (reset) {",
        "        syncToggle();",
        "      }",
        "    }",
        "  });",
        "  if (media) {",
        "    if (media.addEventListener) {",
        "      media.addEventListener('change', syncToggle);",
        "    } else if (media.addListener) {",
        "      media.addListener(syncToggle);",
        "    }",
        "  }",
        "  syncToggle();",
        "}());",
        "</script>",
    )


def page_urls(graph: SiteGraph, public_path: str) -> PageUrls:
    return PageUrls(
        site_url=graph.site.site_url,
        build_url=graph.site.build_url,
        public_path=public_path,
    )


def render_pages(graph: SiteGraph) -> list[RenderedPage]:
    write_item = write_link_item(graph.site.home.links)
    rendered = [
        RenderedPage(
            public_path=HOME_PUBLIC_PATH,
            output_path=Path("index.html"),
            html=render_home_page(graph),
            source_path=graph.site.source_path,
        ),
    ]
    if write_item is not None:
        rendered.append(
            RenderedPage(
                public_path=WRITE_PUBLIC_PATH,
                output_path=Path(WRITE_PUBLIC_PATH.lstrip("/")) / "index.html",
                html=render_write_page(graph, write_item),
                source_path=graph.site.home_path,
            )
        )
    for work in graph.works:
        rendered.append(
            RenderedPage(
                public_path=work.public_path,
                output_path=Path(work.public_path.lstrip("/")) / "index.html",
                html=render_work_page(graph, work),
                source_path=work.body_path,
                assets=tuple(
                    (asset.source_path, Path(work.public_path.lstrip("/")) / asset.relative_path)
                    for asset in work.assets
                ),
            )
        )
    return rendered


def render_home_page(graph: SiteGraph) -> str:
    urls = page_urls(graph, HOME_PUBLIC_PATH)
    content = join_html_lines(
        '<div class="page page--home">',
        '  <section class="page page--cover cover" aria-label="Home cover">',
        indent_html(render_home_cover_nav(graph, urls=urls), 4),
        "  </section>",
        f'  <section class="page home-contents" id="contents" aria-label="{escape(graph.site.home.read_label)}">',
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


def render_write_page(graph: SiteGraph, item: LinkItem) -> str:
    form_src = tally_embed_src(item.href)
    if form_src is None:
        raise BuildError(graph.site.home_path, "missing-required-field", "write page requires a Tally link")

    urls = page_urls(graph, WRITE_PUBLIC_PATH)
    content = join_html_lines(
        '<article class="page utility-page write-page" id="write">',
        '  <header class="page-head utility-header">',
        f'    <h1 class="page-title page-title--section">{escape(item.label)}</h1>',
        "  </header>",
        '  <div class="page-body utility-body write-body">',
        indent_html(render_tally_embed(form_src), 4),
        "  </div>",
        "</article>",
    )
    return render_page(
        graph=graph,
        urls=urls,
        page_title=f"{item.label} - {graph.site.title}",
        page_kind="utility",
        sidebar_html="",
        main_content=content,
        head_extra_html=render_tally_head_links(),
    )


def render_tally_head_links() -> str:
    return '<link rel="preconnect" href="https://tally.so">'


def render_tally_embed(form_src: str) -> str:
    return join_html_lines(
        f'<iframe src="{escape(form_src)}" data-tally-src="{escape(form_src)}" loading="eager" width="100%" height="330" frameborder="0" marginheight="0" marginwidth="0" title="Send me a message"></iframe>',
        f"<script>{TALLY_WIDGET_SCRIPT}</script>",
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
        '<article class="page page--work work-page h-entry" id="work-top">',
        '  <header class="page-head work-header">',
        f'    <h1 class="page-title work-title p-name">{escape(work.title)}</h1>',
        f'    <a class="visually-hidden u-url" href="{escape(urls.canonical_url)}">Permalink</a>',
        "  </header>",
        f"  {date_note_html}",
        '  <div class="page-body">',
        indent_html(render_mobile_work_contents(work), 4),
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
        indent_html(render_mobile_work_end_matter(graph, work, urls=urls), 2),
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
    return join_html_lines(
        *(render_contents_section(section, urls=urls) for section in graph.contents_sections)
    )


def render_contents_section(section: ContentsSection, *, urls: PageUrls) -> str:
    items = join_html_lines(
        *(
            render_works_entry(
                work,
                urls=urls,
                anchor_id=section.anchor_id if index == 0 else None,
            )
            for index, work in enumerate(section.works)
        )
    )
    description_html = (
        f'      <p class="section-description">{escape(section.description)}</p>' if section.description else ""
    )
    heading_id = f"{section.anchor_id}-heading" if items else section.anchor_id
    works_list_html = ""
    if items:
        works_list_html = join_html_lines(
            '  <ol class="works-list">',
            indent_html(items, 4),
            "  </ol>",
        )
    return join_html_lines(
        f'<section class="works-section" aria-labelledby="{escape(heading_id)}">',
        '  <header class="works-section-head">',
        '    <div class="works-section-line">',
        f'      <h3 class="section-heading" id="{escape(heading_id)}">{escape(section.name)}</h3>',
        description_html,
        "    </div>",
        "  </header>",
        works_list_html,
        "</section>",
    )


def render_works_entry(work: WorkDocument, *, urls: PageUrls, anchor_id: str | None = None) -> str:
    work_href = escape(urls.relative_href(work.public_path))
    title = escape(work.title)
    reference = escape(work_path_reference(work.public_path))
    id_attr = f' id="{escape(anchor_id)}"' if anchor_id else ""
    return join_html_lines(
        f'<li class="works-entry"{id_attr}>',
        f'  <a class="works-entry-link" href="{work_href}" aria-label="{title}">',
        f'    <span class="works-entry-title">{title}</span>',
        f'    <span class="works-entry-leader toc-leader" aria-hidden="true">{TOC_LEADER_DOTS}</span>',
        f'    <span class="works-entry-reference">{reference}</span>',
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
    description_html = (
        f'  <meta name="description" content="{escape(graph.site.statement)}">' if graph.site.statement else ""
    )
    return join_html_lines(
        "<!DOCTYPE html>",
        f'<html lang="{escape(graph.site.lang)}">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{escape(page_title)}</title>",
        description_html,
        f'  <meta name="theme-color" content="{escape(graph.site.primary_color)}">',
        f'  <base href="{escape(urls.base_href)}">',
        f'  <link rel="canonical" href="{escape(urls.canonical_url)}">',
        indent_html(render_theme_boot_script(), 2),
        f'  <link rel="stylesheet" href="{escape(urls.relative_href(SITE_STYLESHEET_PUBLIC_PATH))}">',
        f'  <link rel="alternate" type="application/atom+xml" title="{escape(graph.site.title)} feed" href="{escape(urls.relative_href(FEED_PUBLIC_PATH))}">',
        indent_html(head_extra_html, 2),
        "</head>",
        f'<body class="site-page site-page--{escape(page_kind)}">',
        '  <input class="theme-toggle-input visually-hidden" type="checkbox" id="site-theme-toggle" autocomplete="off">',
        '  <label class="theme-toggle" for="site-theme-toggle">',
        '    <span class="visually-hidden">Use alternate color theme</span>',
        "  </label>",
        indent_html(render_theme_control_script(), 2),
        '  <div class="site-shell">',
        indent_html(render_site_header_nav(graph, urls=urls, page_kind=page_kind), 4),
        '    <div class="page-surface">',
        '      <div class="site-frame">',
        '        <div class="site-layout">',
        '          <main class="site-main">',
        indent_html(main_content, 12),
        "          </main>",
        indent_html(sidebar_html, 10),
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
        "  </div>",
        "</aside>",
    )


def render_sidebar_primary(graph: SiteGraph, current_work: WorkDocument | None, urls: PageUrls) -> str:
    if current_work is None:
        return ""

    contents_groups_html = render_sidebar_contents_groups(graph, current_work, urls)
    return join_html_lines(
        '<section class="site-bar-section site-bar-section--contents" aria-labelledby="site-contents-label">',
        '  <h2 class="site-contents-label visually-hidden" id="site-contents-label">Site contents</h2>',
        '  <div class="site-contents-groups">',
        indent_html(contents_groups_html, 4),
        "  </div>",
        "</section>",
    )


def render_site_header_nav(graph: SiteGraph, *, urls: PageUrls, page_kind: str) -> str:
    title_html = (
        f'<h1 class="site-header-title"><a class="site-header-title-link" href="{escape(urls.relative_href(HOME_PUBLIC_PATH))}">{escape(graph.site.home.title)}</a></h1>'
        if page_kind == "home"
        else f'<a class="site-header-title" href="{escape(urls.relative_href(HOME_PUBLIC_PATH))}">{escape(graph.site.title)}</a>'
    )
    subtitle_html = render_home_subtitle(graph) if page_kind == "home" else ""
    nav_html = (
        ""
        if page_kind == "home"
        else join_html_lines(
            '  <p class="site-global-label visually-hidden">Site links</p>',
            '  <nav class="site-nav site-header-nav" aria-label="Site navigation">',
            indent_html(render_site_header_nav_items(site_header_link_parts(graph, urls=urls)), 4),
            "  </nav>",
        )
    )
    return join_html_lines(
        '<header class="site-header-actions" aria-label="Site">',
        f"  {title_html}",
        indent_html(subtitle_html, 2),
        nav_html,
        "</header>",
    )


def render_home_cover_nav(graph: SiteGraph, *, urls: PageUrls) -> str:
    return join_html_lines(
        '<nav class="site-nav site-header-nav home-cover-nav" aria-label="Site navigation">',
        indent_html(render_site_header_nav_items(site_header_link_parts(graph, urls=urls)), 2),
        "</nav>",
    )


def site_header_link_parts(graph: SiteGraph, *, urls: PageUrls) -> tuple[str, ...]:
    read_link = (
        f'<a class="site-link site-header-link site-header-link--read" '
        f'href="{escape(urls.relative_href(HOME_PUBLIC_PATH, fragment="contents"))}">'
        f"{escape(graph.site.home.read_label)}</a>"
    )
    return (
        read_link,
        *(
            render_global_link(
                item,
                urls=urls,
            )
            for item in ordered_site_header_links(graph.site.home.links)
        ),
    )


def render_home_subtitle(graph: SiteGraph) -> str:
    paragraphs = render_markdown_paragraphs(
        graph.site.home.cover_text,
        context=body_context(graph, HOME_PUBLIC_PATH),
    )
    if not paragraphs:
        return ""

    return join_html_lines(
        '<div class="site-header-subtitle">',
        *(
            f'  <p class="site-header-subtitle-line">{paragraph.html}</p>'
            for paragraph in paragraphs
        ),
        "</div>",
    )


def render_site_header_nav_items(items: tuple[str, ...]) -> str:
    parts: list[str] = []
    for index, item in enumerate(items):
        if index:
            parts.append('<span class="site-header-separator" aria-hidden="true">&bull;</span>')
        parts.append(item)
    return join_html_lines(*parts)


def ordered_site_header_links(items: tuple[LinkItem, ...]) -> tuple[LinkItem, ...]:
    feed_links = tuple(item for item in items if item.href == FEED_PUBLIC_PATH)
    other_links = tuple(item for item in items if item.href != FEED_PUBLIC_PATH)
    return (*feed_links, *other_links)


def render_global_link(item: LinkItem, *, urls: PageUrls) -> str:
    classes = ["site-link", "site-header-link"]
    if item.href == FEED_PUBLIC_PATH:
        classes.append("feed-link")

    href = escape(site_header_link_href(item, urls))
    label = escape(item.label)
    return f'<a class="{" ".join(classes)}" href="{href}">{label}</a>'


def site_header_link_href(item: LinkItem, urls: PageUrls) -> str:
    if tally_embed_src(item.href):
        return urls.relative_href(WRITE_PUBLIC_PATH)
    return urls.root_relative_href(item.href)


def write_link_item(items: tuple[LinkItem, ...]) -> LinkItem | None:
    for item in items:
        if tally_embed_src(item.href):
            return item
    return None


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

    section_href = escape(urls.relative_href(HOME_PUBLIC_PATH, fragment=current_section.anchor_id))
    items = join_html_lines(
        *(render_sidebar_contents_item(work, current_work, urls) for work in current_section.works)
    )
    return join_html_lines(
        '<section class="site-contents-group site-contents-group--current">',
        '  <p class="site-contents-summary">',
        f'    <a class="site-contents-summary-link" href="{section_href}">{escape(current_section.name)}</a>',
        "  </p>",
        '  <ol class="site-contents-list">',
        indent_html(items, 4),
        "  </ol>",
        "</section>",
    )


def render_sidebar_contents_item(work: WorkDocument, current_work: WorkDocument, urls: PageUrls) -> str:
    if work.public_path == current_work.public_path:
        inline_headings_html = ""
        if len(current_work.top_level_headings) >= 2:
            inline_headings_html = join_html_lines(
                '<ol class="site-work-headings-list">',
                indent_html(render_work_heading_links(current_work.top_level_headings), 2),
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


def render_mobile_work_end_matter(graph: SiteGraph, work: WorkDocument, *, urls: PageUrls) -> str:
    date_html = (
        '<p class="mobile-work-date"><span class="visually-hidden">Published </span>'
        f'<time datetime="{escape(work.created.isoformat())}">{escape(format_long_date(work.created))}</time></p>'
    )
    return join_html_lines(
        '<footer class="mobile-work-end" aria-label="Work links">',
        '  <div class="mobile-work-actions">',
        '    <a class="site-link mobile-work-top-link" href="#work-top" aria-label="Top of page">'
        '<span class="mobile-work-top-icon" aria-hidden="true">&uarr;</span></a>',
        f"    {date_html}",
        "  </div>",
        indent_html(render_mobile_work_section_links(graph, work, urls=urls), 2),
        "</footer>",
    )


def render_mobile_work_section_links(graph: SiteGraph, work: WorkDocument, *, urls: PageUrls) -> str:
    current_section = graph.contents_section_by_name.get(work.resolved_section)
    if current_section is None:
        return ""

    items = join_html_lines(
        *(
            render_mobile_work_section_item(section_work, urls=urls)
            for section_work in current_section.works
            if section_work.public_path != work.public_path
        )
    )
    if not items:
        return ""

    title_id = "mobile-work-section-title"
    return join_html_lines(
        f'<section class="works-section mobile-work-section" aria-labelledby="{title_id}">',
        '  <header class="works-section-head mobile-work-section-head">',
        '    <div class="works-section-line mobile-work-section-line">',
        f'      <h2 class="section-heading mobile-work-section-title" id="{title_id}">'
        f"More in {escape(current_section.name)}</h2>",
        "    </div>",
        "  </header>",
        '  <ol class="works-list mobile-work-section-list">',
        indent_html(items, 4),
        "  </ol>",
        "</section>",
    )


def render_mobile_work_section_item(work: WorkDocument, *, urls: PageUrls) -> str:
    return render_works_entry(work, urls=urls)


def render_mobile_work_contents(work: WorkDocument) -> str:
    if len(work.top_level_headings) < 2:
        return ""

    return join_html_lines(
        '<details class="mobile-work-contents">',
        '  <summary class="mobile-work-contents-summary">',
        '    <span>Contents</span>',
        '    <span class="mobile-work-contents-arrow" aria-hidden="true">&rarr;</span>',
        "  </summary>",
        '  <ol class="site-work-headings-list mobile-work-headings-list">',
        indent_html(render_work_heading_links(work.top_level_headings), 4),
        "  </ol>",
        "</details>",
    )


def render_work_heading_links(headings: tuple[Heading, ...]) -> str:
    return join_html_lines(
        *(
            join_html_lines(
                f'<li class="site-work-headings-item" data-anchor-id="{escape(heading.anchor_id)}">',
                f'  <a class="site-link site-link--work-index" href="#{escape(heading.anchor_id)}">{escape(heading.text)}</a>',
                "</li>",
            )
            for heading in headings
        )
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
    subtitle_html = f"  <subtitle>{xml_escape(graph.site.statement)}</subtitle>" if graph.site.statement else ""
    return join_html_lines(
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<?xml-stylesheet type="text/css" href="{FEED_STYLESHEET_PUBLIC_PATH.lstrip("/")}"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        indent_html(render_feed_guide(graph, feed_url=feed_urls.output_url), 2),
        f"  <title>{xml_escape(graph.site.title)}</title>",
        subtitle_html,
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
    )
    paragraph_html = []
    for index, paragraph in enumerate(paragraphs):
        class_name = ""
        if index == len(paragraphs) - 1:
            class_name = ' class="feed-guide-inspiration"'
        paragraph_html.append(f"  <xhtml:p{class_name}>{paragraph.html}</xhtml:p>")
    return join_html_lines(
        '<xhtml:section xmlns:xhtml="http://www.w3.org/1999/xhtml" class="feed-guide" aria-label="How to use this feed">',
        indent_html(render_feed_heading(graph), 2),
        *paragraph_html,
        "</xhtml:section>",
    )


def render_feed_heading(graph: SiteGraph) -> str:
    home_urls = page_urls(graph, HOME_PUBLIC_PATH)
    return join_html_lines(
        '<xhtml:header class="site-header-actions feed-heading" aria-label="Site">',
        f'  <xhtml:a class="site-header-title" href="{xml_escape(home_urls.output_url)}">{xml_escape(graph.site.title)}</xhtml:a>',
        indent_html(render_feed_heading_links(graph), 2),
        "</xhtml:header>",
    )


def render_feed_heading_links(graph: SiteGraph) -> str:
    feed_urls = page_urls(graph, FEED_PUBLIC_PATH)
    home_urls = page_urls(graph, HOME_PUBLIC_PATH)
    links = [
        (graph.site.home.read_label, f"{home_urls.output_url}#contents"),
        *(
            (item.label, feed_heading_link_href(item, graph=graph, urls=feed_urls))
            for item in ordered_site_header_links(graph.site.home.links)
        ),
    ]
    parts = []
    for index, (label, href) in enumerate(links):
        if index:
            parts.append('<xhtml:span class="site-header-separator" aria-hidden="true">&#8226;</xhtml:span>')
        parts.append(f'<xhtml:a class="site-link site-header-link" href="{xml_escape(href)}">{xml_escape(label)}</xhtml:a>')
    return join_html_lines(
        '<xhtml:nav class="site-nav site-header-nav" aria-label="Site navigation">',
        indent_html(join_html_lines(*parts), 2),
        "</xhtml:nav>",
    )


def feed_heading_link_href(item: LinkItem, *, graph: SiteGraph, urls: PageUrls) -> str:
    if tally_embed_src(item.href):
        return page_urls(graph, WRITE_PUBLIC_PATH).output_url
    return urls.absolute_href(item.href)


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

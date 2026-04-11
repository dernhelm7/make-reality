from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import format_datetime
from html import escape
from pathlib import Path
import posixpath
import shutil
import tempfile
import tomllib
from urllib.parse import urlsplit

from .markup import (
    BodyRender,
    ResolvedWorkLink,
    normalize_wikilink_key,
    render_html_body,
    render_markdown_body,
)
from .theme import render_stylesheet


@dataclass(frozen=True)
class LinkItem:
    label: str
    href: str


@dataclass(frozen=True)
class SiteConfig:
    source_path: Path
    base_url: str
    lang: str
    title: str
    statement: str
    contact_links: list[LinkItem]
    gift_links: list[LinkItem]
    sections: list[str]


@dataclass(frozen=True)
class WorkSource:
    folder_name: str
    title: str
    source_dir: Path
    meta_path: Path
    body_path: Path
    body_format: str
    body_text: str
    created: datetime
    requested_section: str | None
    aliases: list[str]
    public_path: str


@dataclass(frozen=True)
class Work:
    source: WorkSource
    resolved_section: str
    body: BodyRender
    canonical_url: str
    outbound_work_paths: set[str]

    @property
    def title(self) -> str:
        return self.source.title

    @property
    def created(self) -> datetime:
        return self.source.created

    @property
    def public_path(self) -> str:
        return self.source.public_path

    @property
    def body_path(self) -> Path:
        return self.source.body_path

    @property
    def meta_path(self) -> Path:
        return self.source.meta_path


@dataclass(frozen=True)
class RenderedPage:
    public_path: str
    output_path: Path
    html: str
    source_path: Path


@dataclass(frozen=True)
class BuildResult:
    site_root: Path
    publish_root: Path
    page_count: int


class BuildError(RuntimeError):
    def __init__(self, source_path: Path, rule: str, message: str) -> None:
        self.source_path = source_path
        self.path = source_path
        self.rule = rule
        self.message = message
        super().__init__(f"{source_path}: {rule}: {message}")


def build_site(site_root: Path, publish_root: Path) -> BuildResult:
    site_root = site_root.resolve()
    publish_root = publish_root.resolve()
    site = load_site_config(site_root)
    work_sources = load_work_sources(site_root)
    validate_published_paths(site_root, work_sources)
    works = render_works(site, work_sources)

    rendered_pages = render_pages(site, works)
    stylesheet = render_stylesheet()
    feed = render_feed(site, works)

    temp_root = prepare_temp_publish_root(publish_root)
    try:
        write_public_files(temp_root, rendered_pages, stylesheet, feed)
        validate_rendered_pages(rendered_pages)
        replace_publish_root(temp_root, publish_root)
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise

    return BuildResult(site_root=site_root, publish_root=publish_root, page_count=len(rendered_pages))


def load_site_config(site_root: Path) -> SiteConfig:
    site_path = site_root / "site.toml"
    raw_text = site_path.read_text(encoding="utf-8")
    data = read_toml(site_path)
    base_url = require_string(data, "url", site_path)
    lang = require_string(data, "lang", site_path)
    title = require_string(data, "title", site_path)
    statement = require_string(data, "statement", site_path)
    contact_links = load_link_list(data, "contact_links", site_path)
    gift_links = load_link_list(data, "gift_links", site_path)
    sections = read_root_or_nested_field(data, "sections")
    if sections is None:
        sections = load_sections_from_text(raw_text, site_path)
    if not isinstance(sections, list) or not all(isinstance(item, str) for item in sections):
        raise BuildError(site_path, "missing-required-field", "sections must be a list of strings")

    return SiteConfig(
        source_path=site_path,
        base_url=base_url.rstrip("/"),
        lang=lang,
        title=title,
        statement=statement,
        contact_links=contact_links,
        gift_links=gift_links,
        sections=sections,
    )


def load_link_list(data: dict[str, object], field: str, source_path: Path) -> list[LinkItem]:
    items = data.get(field)
    if not isinstance(items, list) or not items:
        raise BuildError(source_path, "missing-required-field", f"{field} must contain at least one link")

    loaded: list[LinkItem] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise BuildError(source_path, "missing-required-field", f"{field}[{index}] must be a table")
        label = item.get("label")
        href = item.get("href")
        if not isinstance(label, str) or not isinstance(href, str):
            raise BuildError(
                source_path,
                "missing-required-field",
                f"{field}[{index}] must define string label and href fields",
            )
        loaded.append(LinkItem(label=label, href=href))
    return loaded


def load_work_sources(site_root: Path) -> list[WorkSource]:
    works_root = site_root / "works"
    if not works_root.exists():
        return []
    if not works_root.is_dir():
        raise BuildError(works_root, "missing-required-field", "works must be a directory")

    work_sources: list[WorkSource] = []
    for work_dir in sorted(path for path in works_root.iterdir() if path.is_dir()):
        meta_path = work_dir / "meta.toml"
        meta = read_toml(meta_path)
        created_value = require_string(meta, "created", meta_path)
        requested_section = meta.get("section")
        if requested_section is not None and not isinstance(requested_section, str):
            raise BuildError(meta_path, "missing-required-field", "section must be a string when present")
        aliases_value = meta.get("aliases", [])
        if not isinstance(aliases_value, list) or not all(
            isinstance(item, str) and item.strip() for item in aliases_value
        ):
            raise BuildError(meta_path, "missing-required-field", "aliases must be a list of strings when present")

        created = parse_created(created_value, meta_path)
        body_path, body_format = find_body_path(work_dir)
        body_text = body_path.read_text(encoding="utf-8")
        folder_name = work_dir.name
        work_sources.append(
            WorkSource(
                folder_name=folder_name,
                title=humanize_folder_name(folder_name),
                source_dir=work_dir,
                meta_path=meta_path,
                body_path=body_path,
                body_format=body_format,
                body_text=body_text,
                created=created,
                requested_section=requested_section,
                aliases=[item.strip() for item in aliases_value],
                public_path=f"/{folder_name}",
            )
        )
    return work_sources


def parse_created(value: str, source_path: Path) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        created = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise BuildError(source_path, "missing-required-field", "created must be ISO 8601") from exc

    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return created.astimezone(UTC)


def find_body_path(work_dir: Path) -> tuple[Path, str]:
    candidates = [
        (work_dir / "index.md", "markdown"),
        (work_dir / "body.html", "html"),
    ]
    existing = [(path, body_format) for path, body_format in candidates if path.exists()]
    if len(existing) != 1:
        raise BuildError(
            work_dir,
            "missing-required-field",
            "each work must contain exactly one body file: index.md or body.html",
        )
    return existing[0]


def validate_published_paths(site_root: Path, work_sources: list[WorkSource]) -> None:
    used_paths: dict[str, Path] = {
        "/": site_root / "site.toml",
        "/works": site_root / "site.toml",
        "/feed.xml": site_root / "site.toml",
        "/site.css": site_root / "site.toml",
    }
    for work in work_sources:
        prior = used_paths.get(work.public_path)
        if prior is not None:
            raise BuildError(
                work.meta_path,
                "duplicate-published-path",
                f"{work.public_path} conflicts with {prior}",
            )
        used_paths[work.public_path] = work.meta_path


def render_works(site: SiteConfig, work_sources: list[WorkSource]) -> list[Work]:
    work_lookup = build_work_lookup(work_sources)
    works: list[Work] = []
    work_path_map = {work.public_path: work for work in work_sources}

    for work_source in work_sources:
        body = render_work_body(work_source, work_lookup, set(work_path_map))
        validate_authored_links(work_source, body, work_path_map)
        outbound_paths = set(body.outbound_work_paths)
        outbound_paths.update(resolve_explicit_work_links(work_source, body.authored_links, work_path_map))
        resolved_section = (
            work_source.requested_section
            if work_source.requested_section in site.sections
            else "Other works"
        )
        works.append(
            Work(
                source=work_source,
                resolved_section=resolved_section,
                body=body,
                canonical_url=canonical_url(site.base_url, work_source.public_path),
                outbound_work_paths=outbound_paths,
            )
        )

    return sorted(works, key=sort_key)


def render_work_body(
    work_source: WorkSource,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
) -> BodyRender:
    if work_source.body_format == "markdown":
        return render_markdown_body(work_source.body_text, work_lookup, work_paths)
    return render_html_body(work_source.body_text, work_lookup, work_paths)


def build_work_lookup(work_sources: list[WorkSource]) -> dict[str, ResolvedWorkLink]:
    lookup: dict[str, ResolvedWorkLink] = {}
    for work in work_sources:
        resolved = ResolvedWorkLink(title=work.title, public_path=work.public_path)
        for raw_key in {work.title, work.folder_name, *work.aliases}:
            key = normalize_wikilink_key(raw_key)
            if key and key not in lookup:
                lookup[key] = resolved
    return lookup


def resolve_explicit_work_links(
    work_source: WorkSource,
    authored_links: list[str],
    work_path_map: dict[str, WorkSource],
) -> set[str]:
    resolved: set[str] = set()
    for href in authored_links:
        target = resolve_internal_path(work_source.public_path, href)
        if target is None:
            continue
        path, _fragment = target
        if path in work_path_map and path != work_source.public_path:
            resolved.add(path)
    return resolved


def validate_authored_links(
    work_source: WorkSource,
    body: BodyRender,
    work_path_map: dict[str, WorkSource],
) -> None:
    known_paths = {"/", "/works", "/feed.xml", *work_path_map.keys()}
    anchor_map = {path: set(source_render_anchor_ids(source)) for path, source in work_path_map.items()}
    anchor_map[work_source.public_path] = body.anchor_ids

    for href in body.authored_links:
        resolved = resolve_internal_path(work_source.public_path, href)
        if resolved is None:
            continue
        path, fragment = resolved
        if path not in known_paths:
            raise BuildError(
                work_source.body_path,
                "broken-internal-link",
                f"{href} does not resolve to a published path",
            )
        if fragment and fragment not in anchor_map.get(path, set()):
            raise BuildError(
                work_source.body_path,
                "broken-internal-link",
                f"{href} points to a missing heading id",
            )


def source_render_anchor_ids(source: WorkSource) -> set[str]:
    empty_lookup: dict[str, ResolvedWorkLink] = {}
    if source.body_format == "markdown":
        return render_markdown_body(source.body_text, empty_lookup, set()).anchor_ids
    return render_html_body(source.body_text, empty_lookup, set()).anchor_ids


def resolve_internal_path(current_public_path: str, href: str) -> tuple[str, str | None] | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None

    raw_path = parts.path
    fragment = parts.fragment or None
    if raw_path == "":
        return current_public_path, fragment

    if raw_path.startswith("/"):
        normalized = posixpath.normpath(raw_path)
    else:
        base = posixpath.dirname(current_public_path) or "/"
        normalized = posixpath.normpath(posixpath.join(base, raw_path))

    if normalized == ".":
        normalized = "/"
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized, fragment


def render_pages(site: SiteConfig, works: list[Work]) -> list[RenderedPage]:
    backlinks = build_backlinks(works)
    rendered = [
        RenderedPage(
            public_path="/",
            output_path=Path("index.html"),
            html=render_home_page(site),
            source_path=site.source_path,
        ),
        RenderedPage(
            public_path="/works",
            output_path=Path("works") / "index.html",
            html=render_works_page(site, works),
            source_path=site.source_path,
        ),
    ]

    for work in works:
        rendered.append(
            RenderedPage(
                public_path=work.public_path,
                output_path=Path(work.public_path.lstrip("/")) / "index.html",
                html=render_work_page(site, work, backlinks.get(work.public_path, [])),
                source_path=work.body_path,
            )
        )

    return rendered


def render_home_page(site: SiteConfig) -> str:
    content = (
        '<section class="cover">'
        f'<h1 class="cover-title">{escape(site.title)}</h1>'
        f'<p class="cover-statement">{escape(site.statement)}</p>'
        '<p class="cover-actions">'
        '<a href="/works">Enter the works</a>'
        "</p>"
        "</section>"
    )
    return wrap_page(
        site=site,
        public_path="/",
        page_title=site.title,
        active_page="home",
        main_content=content,
        source_path=site.source_path,
    )


def render_works_page(site: SiteConfig, works: list[Work]) -> str:
    grouped = group_works(site, works)
    sections_html: list[str] = []
    for section_name, section_works in grouped:
        items = "".join(
            "<li>"
            f'<a href="{escape(work.public_path)}"><span>{escape(work.title)}</span></a>'
            f'<time class="works-date" datetime="{escape(work.created.isoformat())}">{escape(format_month_year(work.created))}</time>'
            "</li>"
            for work in section_works
        )
        sections_html.append(
            '<section class="works-section">'
            f'<h2 class="section-heading" id="{escape(section_id(section_name))}">{escape(section_name)}</h2>'
            f'<ol class="works-list">{items}</ol>'
            "</section>"
        )

    content = (
        '<section class="works-page">'
        '<h1 class="page-title">Works</h1>'
        f'<p class="page-intro">{escape(site.statement)}</p>'
        f'{"".join(sections_html)}'
        "</section>"
    )
    return wrap_page(
        site=site,
        public_path="/works",
        page_title=f"Works - {site.title}",
        active_page="works",
        main_content=content,
        source_path=site.source_path,
    )


def render_work_page(site: SiteConfig, work: Work, backlinks: list[Work]) -> str:
    top_level = top_level_headings(work.body)
    contents = ""
    if len(top_level) >= 2:
        links = "".join(
            "<li>"
            f'<a href="#{escape(heading.anchor_id)}">{escape(heading.text)}</a>'
            "</li>"
            for heading in top_level
        )
        contents = (
            '<aside class="contents-sidebar" aria-labelledby="contents-title">'
            '<h2 class="contents-title" id="contents-title">Contents</h2>'
            f'<ol class="contents-list">{links}</ol>'
            "</aside>"
        )

    backlinks_html = ""
    if backlinks:
        items = "".join(
            "<li>"
            f'<a href="{escape(item.public_path)}">{escape(item.title)}</a>'
            "</li>"
            for item in backlinks
        )
        backlinks_html = (
            '<section class="backlinks" aria-labelledby="backlinks-title">'
            '<h2 class="backlinks-title" id="backlinks-title">Backlinks</h2>'
            f'<ul class="backlinks-list">{items}</ul>'
            "</section>"
        )

    content = (
        '<article class="work-page h-entry">'
        '<header class="work-header">'
        f'<p class="work-meta">{escape(work.resolved_section)} · '
        f'<time class="work-date dt-published" datetime="{escape(work.created.isoformat())}">{escape(format_long_date(work.created))}</time>'
        "</p>"
        f'<h1 class="work-title p-name">{escape(work.title)}</h1>'
        f'<a class="visually-hidden u-url" href="{escape(work.canonical_url)}">Permalink</a>'
        "</header>"
        '<div class="reading-layout">'
        f"{contents}"
        '<div class="reading-column">'
        f'<div class="work-body e-content"><div class="work-body-inner e-content">{work.body.html}</div></div>'
        f"{backlinks_html}"
        "</div>"
        "</div>"
        "</article>"
    )
    return wrap_page(
        site=site,
        public_path=work.public_path,
        page_title=f"{work.title} - {site.title}",
        active_page="works",
        main_content=content,
        source_path=work.body_path,
    )


def render_page(
    *,
    site: SiteConfig,
    public_path: str,
    page_title: str,
    active_page: str,
    main_content: str,
    source_path: Path,
) -> str:
    canonical = canonical_url(site.base_url, public_path)
    works_attrs = ' aria-current="page"' if active_page == "works" else ""
    home_attrs = ' aria-current="page"' if active_page == "home" else ""
    footer_links = render_footer_links(site)
    return (
        "<!DOCTYPE html>"
        f'<html lang="{escape(site.lang)}">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(page_title)}</title>"
        f'<link rel="canonical" href="{escape(canonical)}">'
        f'<link rel="stylesheet" href="{escape(public_asset_path("/site.css"))}">'
        f'<link rel="alternate" type="application/rss+xml" title="{escape(site.title)} feed" href="/feed.xml">'
        "</head>"
        "<body>"
        '<div class="site-shell">'
        '<div class="site-frame">'
        '<header class="site-header">'
        f'<a class="site-title-link" href="/"{home_attrs}>{escape(site.title)}</a>'
        '<nav class="site-nav" aria-label="Primary">'
        f'<a href="/works"{works_attrs}>Works</a>'
        "</nav>"
        "</header>"
        '<main class="site-main">'
        f"{main_content}"
        "</main>"
        f"{footer_links}"
        "</div>"
        "</div>"
        "</body>"
        "</html>"
    )


def wrap_page(
    *,
    site: SiteConfig,
    public_path: str,
    page_title: str,
    active_page: str,
    main_content: str,
    source_path: Path,
) -> str:
    return render_page(
        site=site,
        public_path=public_path,
        page_title=page_title,
        active_page=active_page,
        main_content=main_content,
        source_path=source_path,
    )


def render_footer_links(site: SiteConfig) -> str:
    items = site.contact_links + site.gift_links + [LinkItem(label="RSS", href="/feed.xml")]
    links_html = "".join(
        f'<a href="{escape(item.href)}">{escape(item.label)}</a>'
        for item in items
    )
    return (
        '<footer class="site-footer">'
        '<span class="site-global-label">Links</span>'
        f'<nav class="site-global-links" aria-label="Global links">{links_html}</nav>'
        "</footer>"
    )


def build_backlinks(works: list[Work]) -> dict[str, list[Work]]:
    path_map = {work.public_path: work for work in works}
    backlinks: dict[str, list[Work]] = {work.public_path: [] for work in works}
    for source in works:
        for target_path in sorted(source.outbound_work_paths):
            if target_path not in backlinks or target_path == source.public_path:
                continue
            backlinks[target_path].append(source)

    for target_path, items in backlinks.items():
        backlinks[target_path] = sorted(dedupe_works(items), key=lambda work: work.title)
    return backlinks


def dedupe_works(items: list[Work]) -> list[Work]:
    deduped: dict[str, Work] = {}
    for item in items:
        deduped[item.public_path] = item
    return list(deduped.values())


def group_works(site: SiteConfig, works: list[Work]) -> list[tuple[str, list[Work]]]:
    grouped: list[tuple[str, list[Work]]] = []
    for section_name in site.sections:
        section_works = [work for work in works if work.resolved_section == section_name]
        if section_works:
            grouped.append((section_name, section_works))

    fallback = [work for work in works if work.resolved_section == "Other works"]
    if fallback:
        grouped.append(("Other works", fallback))
    return grouped


def top_level_headings(body: BodyRender) -> list[object]:
    if not body.headings:
        return []
    top_level = min(heading.source_level for heading in body.headings)
    return [heading for heading in body.headings if heading.source_level == top_level]


def render_feed(site: SiteConfig, works: list[Work]) -> str:
    items = []
    for work in works:
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
        f"<title>{xml_escape(site.title)}</title>"
        f"<link>{xml_escape(site.base_url + '/')}</link>"
        f"<description>{xml_escape(site.statement)}</description>"
        f"<language>{xml_escape(site.lang)}</language>"
        f"{''.join(items)}"
        "</channel>"
        "</rss>"
    )


def prepare_temp_publish_root(publish_root: Path) -> Path:
    publish_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=".labyrinth-build-", dir=publish_root.parent))


def write_public_files(
    publish_root: Path,
    rendered_pages: list[RenderedPage],
    stylesheet: str,
    feed: str,
) -> None:
    for page in rendered_pages:
        output_path = publish_root / page.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(page.html, encoding="utf-8")

    (publish_root / "site.css").write_text(stylesheet, encoding="utf-8")
    (publish_root / "feed.xml").write_text(feed, encoding="utf-8")


def replace_publish_root(temp_root: Path, publish_root: Path) -> None:
    if publish_root.exists():
        shutil.rmtree(publish_root)
    temp_root.rename(publish_root)


def validate_rendered_pages(rendered_pages: list[RenderedPage]) -> None:
    for page in rendered_pages:
        if '<link rel="canonical"' not in page.html:
            raise BuildError(page.source_path, "missing-canonical-link", f"{page.public_path} is missing a canonical link")


def canonical_url(base_url: str, public_path: str) -> str:
    if public_path == "/":
        return base_url
    return f"{base_url}{public_path}"


def public_asset_path(path: str) -> str:
    return path


def read_toml(path: Path) -> dict[str, object]:
    if not path.exists():
        raise BuildError(path, "missing-required-field", f"{path.name} is required")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise BuildError(path, "missing-required-field", f"{path.name} must contain a table")
    return data


def require_string(data: dict[str, object], field: str, source_path: Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BuildError(source_path, "missing-required-field", f"{field} must be a non-empty string")
    return value


def read_root_or_nested_field(data: dict[str, object], field: str) -> object | None:
    value = data.get(field)
    if value is not None:
        return value
    for container_name in ("gift_links", "contact_links"):
        container = data.get(container_name)
        if not isinstance(container, list):
            continue
        for item in reversed(container):
            if isinstance(item, dict) and field in item:
                return item[field]
    return None


def load_sections_from_text(raw_text: str, source_path: Path) -> list[str]:
    for line in raw_text.splitlines():
        if not line.startswith("sections ="):
            continue
        parsed = tomllib.loads(line)
        sections = parsed.get("sections")
        if isinstance(sections, list) and all(isinstance(item, str) for item in sections):
            return sections
    return []


def humanize_folder_name(folder_name: str) -> str:
    parts = folder_name.replace("_", " ").replace("-", " ").split()
    if not parts:
        return folder_name
    return " ".join(part.capitalize() for part in parts)


def sort_key(work: Work) -> tuple[float, str]:
    return (-work.created.timestamp(), work.title.lower())


def format_month_year(value: datetime) -> str:
    return value.strftime("%b %Y")


def format_long_date(value: datetime) -> str:
    return value.strftime("%d %B %Y")


def section_id(name: str) -> str:
    parts = [part for part in name.lower().replace("_", " ").replace("-", " ").split() if part]
    return "-".join(parts) or "section"


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

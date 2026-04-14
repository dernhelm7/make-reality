from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import tomllib

from .markup import (
    BodyRender,
    Heading,
    ResolvedWorkLink,
    normalize_wikilink_key,
    render_html_body,
    render_markdown_body,
)
from .urls import canonical_url


@dataclass(frozen=True)
class BuildError(RuntimeError):
    source_path: Path
    rule: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", self.source_path)
        RuntimeError.__init__(self, f"{self.source_path}: {self.rule}: {self.message}")


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
class WorkInput:
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
class WorkDocument:
    folder_name: str
    title: str
    source_dir: Path
    meta_path: Path
    body_path: Path
    body_format: str
    created: datetime
    public_path: str
    canonical_url: str
    resolved_section: str
    body: BodyRender
    top_level_headings: tuple[Heading, ...]
    outbound_work_paths: frozenset[str]


@dataclass(frozen=True)
class ContentsSection:
    name: str
    anchor_id: str
    works: tuple[WorkDocument, ...]


@dataclass(frozen=True)
class SiteGraph:
    site: SiteConfig
    works: tuple[WorkDocument, ...]
    contents_sections: tuple[ContentsSection, ...]
    contents_section_by_name: dict[str, ContentsSection]
    backlinks: dict[str, tuple[WorkDocument, ...]]
    known_paths: frozenset[str]
    work_lookup: dict[str, ResolvedWorkLink]
    work_by_path: dict[str, WorkDocument]


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
        sections = load_sections_from_text(raw_text)
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


def load_work_inputs(site_root: Path) -> list[WorkInput]:
    works_root = site_root / "works"
    if not works_root.exists():
        return []
    if not works_root.is_dir():
        raise BuildError(works_root, "missing-required-field", "works must be a directory")

    work_inputs: list[WorkInput] = []
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

        body_path, body_format = find_body_path(work_dir)
        folder_name = work_dir.name
        work_inputs.append(
            WorkInput(
                folder_name=folder_name,
                title=humanize_folder_name(folder_name),
                source_dir=work_dir,
                meta_path=meta_path,
                body_path=body_path,
                body_format=body_format,
                body_text=body_path.read_text(encoding="utf-8"),
                created=parse_created(created_value, meta_path),
                requested_section=requested_section,
                aliases=[item.strip() for item in aliases_value],
                public_path=f"/{folder_name}",
            )
        )
    return work_inputs


def build_site_graph(site: SiteConfig, work_inputs: list[WorkInput]) -> SiteGraph:
    validate_published_paths(site.source_path.parent, work_inputs)
    work_lookup = build_work_lookup(work_inputs)
    work_paths = {work.public_path for work in work_inputs}
    known_paths = frozenset({"/", "/feed.xml", *work_paths})
    works = tuple(sorted(render_work_documents(site, work_inputs, work_lookup, work_paths), key=sort_key))
    work_by_path = {work.public_path: work for work in works}
    validate_work_links(works, known_paths, work_by_path)
    contents_sections = build_contents_sections(site.sections, works)
    contents_section_by_name = {section.name: section for section in contents_sections}
    backlinks = build_backlinks(works)
    return SiteGraph(
        site=site,
        works=works,
        contents_sections=contents_sections,
        contents_section_by_name=contents_section_by_name,
        backlinks=backlinks,
        known_paths=known_paths,
        work_lookup=work_lookup,
        work_by_path=work_by_path,
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


def validate_published_paths(site_root: Path, work_inputs: list[WorkInput]) -> None:
    used_paths: dict[str, Path] = {
        "/": site_root / "site.toml",
        "/feed.xml": site_root / "site.toml",
        "/site.css": site_root / "site.toml",
    }
    for work in work_inputs:
        prior = used_paths.get(work.public_path)
        if prior is not None:
            raise BuildError(
                work.meta_path,
                "duplicate-published-path",
                f"{work.public_path} conflicts with {prior}",
            )
        used_paths[work.public_path] = work.meta_path


def build_work_lookup(work_inputs: list[WorkInput]) -> dict[str, ResolvedWorkLink]:
    lookup: dict[str, ResolvedWorkLink] = {}
    for work in work_inputs:
        resolved = ResolvedWorkLink(title=work.title, public_path=work.public_path)
        for raw_key in {work.title, work.folder_name, *work.aliases}:
            key = normalize_wikilink_key(raw_key)
            if key and key not in lookup:
                lookup[key] = resolved
    return lookup


def render_work_documents(
    site: SiteConfig,
    work_inputs: list[WorkInput],
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
) -> list[WorkDocument]:
    documents: list[WorkDocument] = []
    for work in work_inputs:
        body = render_work_body(work, work_lookup, work_paths)
        documents.append(
            WorkDocument(
                folder_name=work.folder_name,
                title=work.title,
                source_dir=work.source_dir,
                meta_path=work.meta_path,
                body_path=work.body_path,
                body_format=work.body_format,
                created=work.created,
                public_path=work.public_path,
                canonical_url=canonical_url(site.base_url, work.public_path),
                resolved_section=resolve_section(work.requested_section, site.sections),
                body=body,
                top_level_headings=top_level_headings(body),
                outbound_work_paths=extract_outbound_work_paths(work.public_path, body),
            )
        )
    return documents


def render_work_body(
    work: WorkInput,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
) -> BodyRender:
    if work.body_format == "markdown":
        return render_markdown_body(
            work.body_text,
            current_public_path=work.public_path,
            work_lookup=work_lookup,
            work_paths=work_paths,
        )
    return render_html_body(
        work.body_text,
        current_public_path=work.public_path,
        work_paths=work_paths,
    )


def resolve_section(requested_section: str | None, site_sections: list[str]) -> str:
    if requested_section in site_sections:
        return requested_section
    return "Other works"


def top_level_headings(body: BodyRender) -> tuple[Heading, ...]:
    if not body.headings:
        return ()
    top_level = min(heading.source_level for heading in body.headings)
    return tuple(heading for heading in body.headings if heading.source_level == top_level)


def extract_outbound_work_paths(current_public_path: str, body: BodyRender) -> frozenset[str]:
    outbound_paths = {
        link.resolved_path
        for link in body.links
        if link.kind == "work" and link.resolved_path and link.resolved_path != current_public_path
    }
    return frozenset(outbound_paths)


def validate_work_links(
    works: tuple[WorkDocument, ...],
    known_paths: frozenset[str],
    work_by_path: dict[str, WorkDocument],
) -> None:
    anchor_map = {path: set(work.body.anchor_ids) for path, work in work_by_path.items()}
    for work in works:
        for link in work.body.links:
            if link.kind == "external" or link.resolved_path is None:
                continue
            if link.resolved_path not in known_paths:
                raise BuildError(
                    work.body_path,
                    "broken-internal-link",
                    f"{link.href} does not resolve to a published path",
                )
            if link.fragment and link.fragment not in anchor_map.get(link.resolved_path, set()):
                raise BuildError(
                    work.body_path,
                    "broken-internal-link",
                    f"{link.href} points to a missing heading id",
                )


def build_contents_sections(site_sections: list[str], works: tuple[WorkDocument, ...]) -> tuple[ContentsSection, ...]:
    sections: list[ContentsSection] = []
    for section_name in site_sections:
        section_works = tuple(work for work in works if work.resolved_section == section_name)
        if section_works:
            sections.append(
                ContentsSection(
                    name=section_name,
                    anchor_id=section_id(section_name),
                    works=section_works,
                )
            )

    fallback = tuple(work for work in works if work.resolved_section == "Other works")
    if fallback:
        sections.append(
            ContentsSection(
                name="Other works",
                anchor_id=section_id("Other works"),
                works=fallback,
            )
        )
    return tuple(sections)


def build_backlinks(works: tuple[WorkDocument, ...]) -> dict[str, tuple[WorkDocument, ...]]:
    backlinks: dict[str, list[WorkDocument]] = {work.public_path: [] for work in works}
    for source in works:
        for target_path in sorted(source.outbound_work_paths):
            if target_path not in backlinks or target_path == source.public_path:
                continue
            backlinks[target_path].append(source)

    return {
        target_path: tuple(sort_and_dedupe_works(items))
        for target_path, items in backlinks.items()
    }


def sort_and_dedupe_works(items: list[WorkDocument]) -> list[WorkDocument]:
    deduped: dict[str, WorkDocument] = {}
    for item in items:
        deduped[item.public_path] = item
    return sorted(deduped.values(), key=lambda work: work.title)

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


def load_sections_from_text(raw_text: str) -> list[str]:
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


def sort_key(work: WorkDocument) -> tuple[float, str]:
    return (-work.created.timestamp(), work.title.lower())


def section_id(name: str) -> str:
    parts = [part for part in name.lower().replace("_", " ").replace("-", " ").split() if part]
    return "-".join(parts) or "section"

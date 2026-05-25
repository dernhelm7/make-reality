from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re
import subprocess
import tomllib
from urllib.parse import urlsplit

from .markup import (
    BodyContext,
    BodyRender,
    Heading,
    ResolvedWorkLink,
    normalize_wikilink_key,
    render_html_body,
    render_markdown_body,
)
from .urls import FIXED_PUBLIC_PATHS

HOME_LINK_RE = re.compile(r"^\[(?P<label>[^\]]+)\]\((?P<href>[^)]+)\)$")
WORK_METADATA_KEYS = frozenset({"aliases", "atom_id", "created", "updated"})
WORK_FILE_FORMATS = {
    ".html": "html",
    ".md": "markdown",
}
DEFAULT_PRIMARY_COLOR = "#110411"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


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
class SectionDefinition:
    name: str
    description: str


@dataclass(frozen=True)
class HomeDocument:
    title: str
    cover_text: str
    links: tuple[LinkItem, ...]
    read_label: str
    sections: tuple[SectionDefinition, ...]


@dataclass(frozen=True)
class SiteConfig:
    source_path: Path
    home_path: Path
    feed_guide_path: Path
    site_url: str
    build_url: str
    lang: str
    title: str
    home: HomeDocument
    feed_guide_text: str
    statement: str
    author_name: str
    updated: datetime
    primary_color: str


@dataclass(frozen=True)
class WorkInput:
    section_folder: str | None
    folder_name: str
    title: str
    source_dir: Path
    metadata_path: Path
    body_path: Path
    body_format: str
    body_text: str
    created: datetime | None
    updated: datetime | None
    atom_id: str | None
    aliases: tuple[str, ...]
    public_path: str
    assets: tuple[WorkAsset, ...]


@dataclass(frozen=True)
class WorkDocument:
    folder_name: str
    title: str
    source_dir: Path
    metadata_path: Path
    body_path: Path
    body_format: str
    created: datetime
    updated: datetime
    atom_id: str
    public_path: str
    resolved_section: str
    body: BodyRender
    top_level_headings: tuple[Heading, ...]
    outbound_work_paths: frozenset[str]
    assets: tuple[WorkAsset, ...]


@dataclass(frozen=True)
class WorkAsset:
    source_path: Path
    relative_path: Path
    public_path: str


@dataclass(frozen=True)
class ContentsSection:
    name: str
    description: str
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


def load_site_config(site_root: Path, build_url: str | None = None) -> SiteConfig:
    site_path = site_root / "site.toml"
    data = read_toml(site_path)
    home_path = site_root / "home.md"
    feed_guide_path = site_root / "feed.md"
    site_url = require_absolute_url(data, "url", site_path).rstrip("/")
    lang = require_string(data, "lang", site_path)
    title = require_string(data, "title", site_path)
    home = parse_home_markdown(home_path)
    feed_guide_text = read_required_markdown(feed_guide_path)
    statement = optional_string(data, "statement", site_path) or ""
    author_name = require_string(data, "author_name", site_path)
    updated = parse_timestamp(require_string(data, "updated", site_path), site_path, "updated")
    primary_color = parse_hex_color(
        optional_string(data, "primary_color", site_path) or DEFAULT_PRIMARY_COLOR,
        site_path,
    )

    return SiteConfig(
        source_path=site_path,
        home_path=home_path,
        feed_guide_path=feed_guide_path,
        site_url=site_url,
        build_url=normalize_absolute_url(build_url or site_url, Path("<command-line>"), "build-url").rstrip("/"),
        lang=lang,
        title=title,
        home=home,
        feed_guide_text=feed_guide_text,
        statement=statement,
        author_name=author_name,
        updated=updated,
        primary_color=primary_color,
    )


def load_work_inputs(site_root: Path) -> list[WorkInput]:
    works_root = site_root / "works"
    if not works_root.exists():
        return []
    if not works_root.is_dir():
        raise BuildError(works_root, "missing-required-field", "works must be a directory")

    work_inputs: list[WorkInput] = []

    def append_work(
        *,
        source_dir: Path,
        folder_name: str,
        body_path: Path,
        body_format: str,
        section_folder: str | None,
        meta_path: Path | None = None,
        assets: tuple[WorkAsset, ...] = (),
    ) -> None:
        body_text = body_path.read_text(encoding="utf-8")
        front_matter, body_text, has_front_matter = split_toml_front_matter(body_text, body_path)
        metadata = front_matter
        metadata_path = body_path
        if meta_path is not None:
            if has_front_matter:
                raise BuildError(
                    body_path,
                    "duplicate-metadata",
                    "work metadata must live in either TOML front matter or meta.toml, not both",
                )
            metadata = read_toml(meta_path)
            metadata_path = meta_path
        created, updated, atom_id, aliases = parse_work_metadata(metadata, metadata_path)
        work_inputs.append(
            WorkInput(
                section_folder=section_folder,
                folder_name=folder_name,
                title=humanize_folder_name(folder_name),
                source_dir=source_dir,
                metadata_path=metadata_path,
                body_path=body_path,
                body_format=body_format,
                body_text=body_text,
                created=created,
                updated=updated,
                atom_id=atom_id,
                aliases=aliases,
                public_path=work_public_path(folder_name),
                assets=assets,
            )
        )

    def append_file_work(body_path: Path, *, section_folder: str | None) -> None:
        body_format = body_format_for_file(body_path)
        if body_format is None:
            return
        append_work(
            source_dir=body_path.parent,
            folder_name=body_path.stem,
            body_path=body_path,
            body_format=body_format,
            section_folder=section_folder,
        )

    def append_folder_work(work_dir: Path, *, section_folder: str | None) -> None:
        meta_path = work_dir / "meta.toml"
        body_path, body_format = find_body_path(work_dir)
        append_work(
            source_dir=work_dir,
            folder_name=work_dir.name,
            body_path=body_path,
            body_format=body_format,
            section_folder=section_folder,
            meta_path=meta_path if meta_path.is_file() else None,
            assets=collect_work_assets(work_dir, body_path=body_path, public_path=work_public_path(work_dir.name)),
        )

    for source_dir in sorted(path for path in works_root.iterdir() if path.is_dir()):
        if source_dir.name.startswith("."):
            continue
        if is_direct_work_folder(source_dir):
            append_folder_work(source_dir, section_folder=None)
            continue
        for source_path in sorted(source_dir.iterdir()):
            if source_path.name.startswith("."):
                continue
            if source_path.is_file():
                append_file_work(source_path, section_folder=source_dir.name)
            elif source_path.is_dir():
                append_folder_work(source_path, section_folder=source_dir.name)
    for source_path in sorted(path for path in works_root.iterdir() if path.is_file()):
        if source_path.name.startswith("."):
            continue
        append_file_work(source_path, section_folder=None)
    return work_inputs


def build_site_graph(site: SiteConfig, work_inputs: list[WorkInput]) -> SiteGraph:
    validate_published_paths(site.source_path.parent, work_inputs)
    work_lookup = build_work_lookup(work_inputs)
    work_paths = frozenset(work.public_path for work in work_inputs)
    asset_paths = frozenset(asset.public_path for work in work_inputs for asset in work.assets)
    known_paths = frozenset({*FIXED_PUBLIC_PATHS, *work_paths, *asset_paths})
    works = tuple(sorted(render_work_documents(site, work_inputs, work_lookup, work_paths), key=sort_key))
    work_by_path = {work.public_path: work for work in works}
    validate_link_items(site.home.links, site.home_path, known_paths)
    validate_work_links(works, known_paths, work_by_path)
    contents_sections = build_contents_sections(site.home.sections, works)
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


def read_required_markdown(path: Path) -> str:
    if not path.is_file():
        raise BuildError(path, "missing-required-field", f"{path.name} is required")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise BuildError(path, "missing-required-field", f"{path.name} must not be empty")
    return text


def parse_home_markdown(path: Path) -> HomeDocument:
    lines = read_required_markdown(path).splitlines()
    if not lines or not lines[0].startswith("# "):
        raise BuildError(path, "missing-required-field", "home.md must start with a # title")

    title = lines[0][2:].strip()
    if not title:
        raise BuildError(path, "missing-required-field", "home.md title must not be empty")

    cover_lines: list[str] = []
    links: list[LinkItem] = []
    read_label: str | None = None
    section_name: str | None = None
    section_lines: list[str] = []
    sections: list[SectionDefinition] = []

    def flush_section() -> None:
        nonlocal section_name, section_lines
        if section_name is None:
            return
        sections.append(
            SectionDefinition(
                name=section_name,
                description=collapse_plain_text(section_lines),
            )
        )
        section_name = None
        section_lines = []

    for line in lines[1:]:
        stripped = line.strip()
        if stripped.startswith("# "):
            raise BuildError(path, "missing-required-field", "home.md must contain one # title")
        if stripped.startswith("## "):
            flush_section()
            if read_label is not None:
                raise BuildError(path, "missing-required-field", "home.md heading structure is invalid")
            read_label = stripped[3:].strip()
            if not read_label:
                raise BuildError(path, "missing-required-field", "home.md heading structure is invalid")
            continue
        if stripped.startswith("### "):
            if read_label is None:
                raise BuildError(path, "missing-required-field", "home.md heading structure is invalid")
            flush_section()
            section_name = stripped[4:].strip()
            if not section_name:
                raise BuildError(path, "missing-required-field", "home.md section headings must not be empty")
            continue

        if read_label is None:
            link_match = HOME_LINK_RE.match(stripped)
            if link_match:
                label = link_match.group("label").strip()
                href = link_match.group("href").strip()
                if not label or not href:
                    raise BuildError(path, "missing-required-field", "home.md links must define label and href")
                links.append(
                    LinkItem(
                        label=label,
                        href=href,
                    )
                )
                continue
            cover_lines.append(line)
            continue

        if section_name is not None:
            section_lines.append(line)
        elif stripped:
            raise BuildError(path, "missing-required-field", "home.md heading structure is invalid")

    flush_section()
    cover_text = trim_blank_lines(cover_lines)
    if not cover_text.strip():
        raise BuildError(path, "missing-required-field", "home.md cover text must not be empty")
    if not links:
        raise BuildError(path, "missing-required-field", "home.md must define at least one homepage link")
    if read_label is None:
        raise BuildError(path, "missing-required-field", "home.md heading structure is invalid")
    return HomeDocument(
        title=title,
        cover_text=cover_text,
        links=tuple(links),
        read_label=read_label,
        sections=tuple(sections),
    )


def trim_blank_lines(lines: list[str]) -> str:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def collapse_plain_text(lines: list[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip())


def parse_timestamp(value: str, source_path: Path, field: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise BuildError(source_path, "missing-required-field", f"{field} must be ISO 8601") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def split_toml_front_matter(text: str, source_path: Path) -> tuple[dict[str, object], str, bool]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        return {}, text, False
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            front_matter_text = "".join(lines[1:index])
            body_text = "".join(lines[index + 1 :])
            return parse_toml_text(front_matter_text, source_path), body_text, True
    raise BuildError(source_path, "missing-required-field", "TOML front matter must close with +++")


def parse_toml_text(text: str, source_path: Path) -> dict[str, object]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise BuildError(source_path, "missing-required-field", "TOML metadata must be valid") from exc
    if not isinstance(data, dict):
        raise BuildError(source_path, "missing-required-field", "TOML metadata must contain a table")
    return data


def parse_work_metadata(
    data: dict[str, object],
    source_path: Path,
) -> tuple[datetime | None, datetime | None, str | None, tuple[str, ...]]:
    validate_work_metadata_keys(data, source_path)
    created_value = optional_string(data, "created", source_path)
    updated_value = optional_string(data, "updated", source_path)
    atom_id_value = optional_string(data, "atom_id", source_path)
    aliases_value = data.get("aliases", [])
    if not isinstance(aliases_value, list) or not all(
        isinstance(item, str) and item.strip() for item in aliases_value
    ):
        raise BuildError(source_path, "missing-required-field", "aliases must be a list of strings when present")
    return (
        parse_timestamp(created_value, source_path, "created") if created_value is not None else None,
        parse_timestamp(updated_value, source_path, "updated") if updated_value is not None else None,
        normalize_absolute_url(atom_id_value, source_path, "atom_id") if atom_id_value is not None else None,
        tuple(item.strip() for item in aliases_value),
    )


def validate_work_metadata_keys(data: dict[str, object], source_path: Path) -> None:
    unknown_fields = sorted(set(data) - WORK_METADATA_KEYS)
    if not unknown_fields:
        return
    field = unknown_fields[0]
    if field == "section":
        message = "section is set by the parent folder under works; remove section from work metadata"
    else:
        message = f"{field} is not supported in work metadata"
    raise BuildError(source_path, "unsupported-field", message)


def optional_string(data: dict[str, object], field: str, source_path: Path) -> str | None:
    if field not in data:
        return None
    return require_string(data, field, source_path)


def find_body_path(work_dir: Path) -> tuple[Path, str]:
    candidates = [
        path
        for path in sorted(work_dir.iterdir())
        if path.is_file() and (path.name in {"body.html", "index.md"} or path.suffix.lower() == ".md")
    ]
    existing = [(path, body_format_for_file(path)) for path in candidates]
    if len(existing) != 1:
        raise BuildError(
            work_dir,
            "missing-required-field",
            "each work must contain exactly one body file: index.md, body.html, or one *.md file",
        )
    body_path, body_format = existing[0]
    if body_format is None:
        raise BuildError(
            work_dir,
            "missing-required-field",
            "each work must contain exactly one body file: index.md, body.html, or one *.md file",
        )
    return body_path, body_format


def body_format_for_file(path: Path) -> str | None:
    return WORK_FILE_FORMATS.get(path.suffix.lower())


def is_direct_work_folder(path: Path) -> bool:
    return any(
        candidate.is_file()
        for candidate in (
            path / "body.html",
            path / "index.md",
            path / "meta.toml",
            path / f"{path.name}.md",
        )
    )


def collect_work_assets(work_dir: Path, *, body_path: Path, public_path: str) -> tuple[WorkAsset, ...]:
    ignored = {body_path.resolve(), (work_dir / "meta.toml").resolve()}
    assets: list[WorkAsset] = []
    for source_path in sorted(path for path in work_dir.rglob("*") if path.is_file()):
        if source_path.resolve() in ignored:
            continue
        relative_path = source_path.relative_to(work_dir)
        if any(part.startswith(".") for part in relative_path.parts):
            continue
        assets.append(
            WorkAsset(
                source_path=source_path,
                relative_path=relative_path,
                public_path=f"{public_path}/{relative_path.as_posix()}",
            )
        )
    return tuple(assets)


def validate_published_paths(site_root: Path, work_inputs: list[WorkInput]) -> None:
    used_paths: dict[str, Path] = {path: site_root / "site.toml" for path in FIXED_PUBLIC_PATHS}
    for work in work_inputs:
        prior = used_paths.get(work.public_path)
        if prior is not None:
            raise BuildError(
                work.metadata_path,
                "duplicate-published-path",
                f"{work.public_path} conflicts with {prior}",
            )
        used_paths[work.public_path] = work.metadata_path
        work_index_path = f"{work.public_path}/index.html"
        for asset in work.assets:
            prior = used_paths.get(asset.public_path)
            if prior is not None or asset.public_path == work_index_path:
                raise BuildError(
                    asset.source_path,
                    "duplicate-published-path",
                    f"{asset.public_path} conflicts with {prior or work.body_path}",
                )
            used_paths[asset.public_path] = asset.source_path


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
    work_paths: frozenset[str],
) -> list[WorkDocument]:
    documents: list[WorkDocument] = []
    section_names = {section_folder_key(section.name): section.name for section in site.home.sections}
    for work in work_inputs:
        body = render_work_body(work, work_lookup, work_paths)
        created, updated = resolve_work_dates(work)
        documents.append(
            WorkDocument(
                folder_name=work.folder_name,
                title=work.title,
                source_dir=work.source_dir,
                metadata_path=work.metadata_path,
                body_path=work.body_path,
                body_format=work.body_format,
                created=created,
                updated=updated,
                atom_id=work.atom_id or f"{site.site_url}/id/{work.folder_name}",
                public_path=work.public_path,
                resolved_section=resolve_section(work.section_folder, section_names),
                body=body,
                top_level_headings=top_level_headings(body),
                outbound_work_paths=extract_outbound_work_paths(work.public_path, body),
                assets=work.assets,
            )
        )
    return documents


def resolve_work_dates(work: WorkInput) -> tuple[datetime, datetime]:
    derived_created, derived_updated = derive_work_dates(work.body_path)
    created = work.created or derived_created
    updated = work.updated or derived_updated
    if updated < created:
        updated = created
    return created, updated


def derive_work_dates(path: Path) -> tuple[datetime, datetime]:
    commit_times = git_commit_times(path)
    if commit_times:
        return commit_times[-1], commit_times[0]
    fallback = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(microsecond=0)
    return fallback, fallback


def git_commit_times(path: Path) -> tuple[datetime, ...]:
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "log", "--follow", "--format=%cI", "--", path.name],
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        return ()
    if result.returncode != 0:
        return ()
    times: list[datetime] = []
    for line in result.stdout.splitlines():
        if line.strip():
            times.append(parse_timestamp(line.strip(), path, "git history"))
    return tuple(times)


def render_work_body(
    work: WorkInput,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: frozenset[str],
) -> BodyRender:
    context = BodyContext(
        current_public_path=work.public_path,
        work_lookup=work_lookup,
        work_paths=work_paths,
        asset_paths=frozenset(asset.public_path for asset in work.assets),
    )
    if work.body_format == "markdown":
        return render_markdown_body(
            work.body_text,
            context=context,
        )
    return render_html_body(
        work.body_text,
        context=context,
    )


def resolve_section(section_folder: str | None, section_names: dict[str, str]) -> str:
    if section_folder is not None:
        section_name = section_names.get(section_folder_key(section_folder))
        if section_name is not None:
            return section_name
    return "Other works"


def section_folder_key(name: str) -> str:
    return normalize_wikilink_key(name)


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
            if (
                link.kind != "asset"
                and link.fragment
                and link.fragment not in anchor_map.get(link.resolved_path, set())
            ):
                raise BuildError(
                    work.body_path,
                    "broken-internal-link",
                    f"{link.href} points to a missing heading id",
                )


def validate_link_items(items: tuple[LinkItem, ...], source_path: Path, known_paths: frozenset[str]) -> None:
    for item in items:
        parts = urlsplit(item.href)
        if parts.scheme or parts.netloc or not parts.path.startswith("/"):
            continue
        if parts.path not in known_paths:
            raise BuildError(
                source_path,
                "broken-internal-link",
                f"{item.href} does not resolve to a published path",
            )


def build_contents_sections(
    site_sections: tuple[SectionDefinition, ...],
    works: tuple[WorkDocument, ...],
) -> tuple[ContentsSection, ...]:
    grouped_works: dict[str, list[WorkDocument]] = {section.name: [] for section in site_sections}
    fallback_works: list[WorkDocument] = []
    for work in works:
        if work.resolved_section in grouped_works:
            grouped_works[work.resolved_section].append(work)
        else:
            fallback_works.append(work)

    sections: list[ContentsSection] = []
    for section in site_sections:
        sections.append(
            ContentsSection(
                name=section.name,
                description=section.description,
                anchor_id=section_id(section.name),
                works=tuple(grouped_works[section.name]),
            )
        )

    if fallback_works:
        sections.append(
            ContentsSection(
                name="Other works",
                description="",
                anchor_id=section_id("Other works"),
                works=tuple(fallback_works),
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


def require_absolute_url(data: dict[str, object], field: str, source_path: Path) -> str:
    value = require_string(data, field, source_path)
    return normalize_absolute_url(value, source_path, field)


def parse_hex_color(value: str, source_path: Path) -> str:
    if not HEX_COLOR_RE.fullmatch(value):
        raise BuildError(source_path, "missing-required-field", "primary_color must be a six-digit hex color")
    return value.lower()


def normalize_absolute_url(value: str, source_path: Path, field: str) -> str:
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        raise BuildError(source_path, "missing-required-field", f"{field} must be an absolute URL")
    return value


def work_public_path(folder_name: str) -> str:
    return f"/{folder_name}"


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

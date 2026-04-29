from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import posixpath
import re
import unicodedata
from urllib.parse import urlsplit

from .urls import relative_public_href


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
STANDARD_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<href>[^)]+)\)")


@dataclass(frozen=True)
class ResolvedWorkLink:
    title: str
    public_path: str


@dataclass(frozen=True)
class Heading:
    text: str
    anchor_id: str
    source_level: int
    rendered_level: int


@dataclass(frozen=True)
class BodyLink:
    href: str
    resolved_path: str | None
    fragment: str | None
    kind: str


@dataclass(frozen=True)
class BodyContext:
    current_public_path: str
    work_lookup: dict[str, ResolvedWorkLink]
    work_paths: frozenset[str]

    def resolve_wikilink(self, raw_target: str) -> ResolvedWorkLink | None:
        return self.work_lookup.get(normalize_wikilink_key(raw_target))

    def analyze_link(self, href: str) -> BodyLink:
        resolved = resolve_internal_path(self.current_public_path, href)
        if resolved is None:
            return BodyLink(href=href, resolved_path=None, fragment=None, kind="external")
        resolved_path, fragment = resolved
        kind = (
            "work"
            if resolved_path in self.work_paths and resolved_path != self.current_public_path
            else "internal"
        )
        return BodyLink(href=href, resolved_path=resolved_path, fragment=fragment, kind=kind)

    def render_href(self, link: BodyLink) -> str:
        if link.kind == "external" or link.resolved_path is None:
            return link.href
        if link.resolved_path == self.current_public_path:
            if link.fragment:
                return f"#{link.fragment}"
            return relative_public_href(self.current_public_path, self.current_public_path)
        rendered = relative_public_href(self.current_public_path, link.resolved_path)
        if link.fragment:
            return f"{rendered}#{link.fragment}"
        return rendered


@dataclass(frozen=True)
class BodyRender:
    html: str
    headings: tuple[Heading, ...]
    anchor_ids: frozenset[str]
    links: tuple[BodyLink, ...]


@dataclass(frozen=True)
class InlineRender:
    html: str
    visible_text: str
    links: tuple[BodyLink, ...]


def render_markdown_body(
    body_text: str,
    *,
    context: BodyContext,
) -> BodyRender:
    lines = body_text.splitlines()
    blocks: list[tuple[str, str, int]] = []
    buffer: list[str] = []

    def flush_paragraph() -> None:
        if not buffer:
            return
        paragraph = " ".join(part.strip() for part in buffer if part.strip()).strip()
        if paragraph:
            blocks.append(("paragraph", paragraph, 0))
        buffer.clear()

    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            flush_paragraph()
            level = len(match.group(1))
            blocks.append(("heading", match.group(2).strip(), level))
            continue

        if not line.strip():
            flush_paragraph()
            continue

        buffer.append(line)

    flush_paragraph()

    pieces: list[str] = []
    headings: list[Heading] = []
    links: list[BodyLink] = []
    used_ids: set[str] = set()

    for block_type, content, source_level in blocks:
        inline = render_inline(
            content,
            context=context,
        )
        links.extend(inline.links)

        if block_type == "paragraph":
            pieces.append(f"<p>{inline.html}</p>")
            continue

        anchor_id = unique_anchor_id(slugify_visible_text(inline.visible_text), used_ids)
        rendered_level = min(6, source_level + 1)
        headings.append(
            Heading(
                text=inline.visible_text,
                anchor_id=anchor_id,
                source_level=source_level,
                rendered_level=rendered_level,
            )
        )
        pieces.append(
            f'<h{rendered_level} id="{escape(anchor_id)}">'
            f'<a class="heading-anchor" href="#{escape(anchor_id)}">{inline.html}</a>'
            f"</h{rendered_level}>"
        )

    return BodyRender(
        html="\n".join(pieces),
        headings=tuple(headings),
        anchor_ids=frozenset(heading.anchor_id for heading in headings),
        links=tuple(links),
    )


def render_markdown_paragraphs(
    body_text: str,
    *,
    context: BodyContext,
    tag_prefix: str = "",
    include_link_class: bool = True,
) -> tuple[InlineRender, ...]:
    paragraphs: list[list[str]] = []
    buffer: list[str] = []

    def flush_paragraph() -> None:
        if not buffer:
            return
        paragraphs.append([line for line in buffer if line.strip()])
        buffer.clear()

    for line in body_text.splitlines():
        if not line.strip():
            flush_paragraph()
            continue
        buffer.append(line)

    flush_paragraph()

    return tuple(
        render_markdown_paragraph_lines(
            lines,
            context=context,
            tag_prefix=tag_prefix,
            include_link_class=include_link_class,
        )
        for lines in paragraphs
        if lines
    )


def render_markdown_paragraph_lines(
    lines: list[str],
    *,
    context: BodyContext,
    tag_prefix: str,
    include_link_class: bool,
) -> InlineRender:
    pieces: list[str] = []
    visible: list[str] = []
    links: list[BodyLink] = []
    prior_hard_break = False
    break_tag = f"<{tag_prefix}br/>" if tag_prefix else "<br>"

    for index, line in enumerate(lines):
        text, hard_break = strip_markdown_hard_break(line)
        if index > 0:
            if prior_hard_break:
                pieces.append(f"{break_tag}\n")
                visible.append("\n")
            else:
                pieces.append(" ")
                visible.append(" ")

        inline = render_inline(
            text.strip(),
            context=context,
            tag_prefix=tag_prefix,
            include_link_class=include_link_class,
        )
        pieces.append(inline.html)
        visible.append(inline.visible_text)
        links.extend(inline.links)
        prior_hard_break = hard_break

    return InlineRender(
        html="".join(pieces),
        visible_text="".join(visible),
        links=tuple(links),
    )


def strip_markdown_hard_break(line: str) -> tuple[str, bool]:
    if line.endswith("  "):
        return line[:-2], True
    stripped = line.rstrip()
    if stripped.endswith("\\"):
        return stripped[:-1], True
    return line, False


class HTMLFragmentRewriter(HTMLParser):
    def __init__(self, context: BodyContext) -> None:
        super().__init__(convert_charrefs=False)
        self.context = context
        self.output: list[str] = []
        self.headings: list[Heading] = []
        self.anchor_ids: set[str] = set()
        self.links: list[BodyLink] = []
        self._heading_tag: str | None = None
        self._heading_attrs: list[tuple[str, str | None]] = []
        self._heading_inner: list[str] = []
        self._heading_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        rendered_attrs, link = rewrite_link_attributes(
            tag,
            attrs,
            context=self.context,
        )
        if link is not None:
            self.links.append(link)
        rendered_tag = render_start_tag(tag, rendered_attrs)

        if self._heading_tag is not None:
            self._heading_inner.append(rendered_tag)
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = tag
            self._heading_attrs = rendered_attrs
            self._heading_inner = []
            self._heading_text = []
            return

        self.output.append(rendered_tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        rendered_attrs, link = rewrite_link_attributes(
            tag,
            attrs,
            context=self.context,
        )
        if link is not None:
            self.links.append(link)
        rendered = render_start_tag(tag, rendered_attrs, self_closing=True)
        if self._heading_tag is not None:
            self._heading_inner.append(rendered)
            return
        self.output.append(rendered)

    def handle_endtag(self, tag: str) -> None:
        if self._heading_tag is not None:
            if tag == self._heading_tag:
                text = "".join(self._heading_text).strip()
                anchor_id = unique_anchor_id(slugify_visible_text(text), self.anchor_ids)
                source_level = int(self._heading_tag[1])
                heading_attrs = merge_attributes(self._heading_attrs, {"id": anchor_id})
                rendered = (
                    f"<{self._heading_tag}{render_attributes(heading_attrs)}>"
                    f'<a class="heading-anchor" href="#{escape(anchor_id)}">{"".join(self._heading_inner)}</a>'
                    f"</{self._heading_tag}>"
                )
                self.output.append(rendered)
                self.headings.append(
                    Heading(
                        text=text,
                        anchor_id=anchor_id,
                        source_level=source_level,
                        rendered_level=source_level,
                    )
                )
                self._heading_tag = None
                self._heading_attrs = []
                self._heading_inner = []
                self._heading_text = []
                return

            self._heading_inner.append(f"</{tag}>")
            return

        self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._heading_tag is not None:
            self._heading_inner.append(data)
            self._heading_text.append(data)
            return
        self.output.append(data)

    def handle_comment(self, data: str) -> None:
        rendered = f"<!--{data}-->"
        if self._heading_tag is not None:
            self._heading_inner.append(rendered)
            return
        self.output.append(rendered)

    def handle_entityref(self, name: str) -> None:
        rendered = f"&{name};"
        if self._heading_tag is not None:
            self._heading_inner.append(rendered)
            self._heading_text.append(html_entity_visible_text(rendered))
            return
        self.output.append(rendered)

    def handle_charref(self, name: str) -> None:
        rendered = f"&#{name};"
        if self._heading_tag is not None:
            self._heading_inner.append(rendered)
            self._heading_text.append(html_entity_visible_text(rendered))
            return
        self.output.append(rendered)

    def render(self) -> BodyRender:
        return BodyRender(
            html="".join(self.output),
            headings=tuple(self.headings),
            anchor_ids=frozenset(self.anchor_ids),
            links=tuple(self.links),
        )


def render_html_body(
    body_text: str,
    *,
    context: BodyContext,
) -> BodyRender:
    parser = HTMLFragmentRewriter(context)
    parser.feed(body_text)
    parser.close()
    return parser.render()


def render_inline(
    text: str,
    *,
    context: BodyContext,
    tag_prefix: str = "",
    include_link_class: bool = True,
) -> InlineRender:
    pieces: list[str] = []
    visible: list[str] = []
    links: list[BodyLink] = []
    index = 0

    while index < len(text):
        if text.startswith("[[", index):
            end = text.find("]]", index + 2)
            if end != -1:
                raw = text[index + 2 : end]
                target, label = split_wikilink(raw)
                visible_label = label or target
                resolved = context.resolve_wikilink(target)
                if resolved is None:
                    pieces.append(escape(visible_label))
                else:
                    link = BodyLink(
                        href=resolved.public_path,
                        resolved_path=resolved.public_path,
                        fragment=None,
                        kind="work",
                    )
                    class_attr = (
                        f' class="{escape(link_class_name(link))}"' if include_link_class else ""
                    )
                    pieces.append(
                        f'<{tag_prefix}a{class_attr} href="{escape(context.render_href(link))}">'
                        f"{escape(visible_label)}</{tag_prefix}a>"
                    )
                    links.append(link)
                visible.append(visible_label)
                index = end + 2
                continue

        if text[index] == "[":
            link_match = STANDARD_LINK_RE.match(text, index)
            if link_match:
                label = link_match.group("label")
                href = link_match.group("href")
                link = context.analyze_link(href)
                rendered_href = context.render_href(link)
                rendered_label = render_inline(
                    label,
                    context=context,
                    tag_prefix=tag_prefix,
                    include_link_class=include_link_class,
                )
                class_attr = f' class="{escape(link_class_name(link))}"' if include_link_class else ""
                pieces.append(
                    f'<{tag_prefix}a{class_attr} href="{escape(rendered_href)}">{rendered_label.html}</{tag_prefix}a>'
                )
                visible.append(rendered_label.visible_text)
                links.extend(rendered_label.links)
                links.append(link)
                index = link_match.end()
                continue

        if text[index] == "_":
            end = text.find("_", index + 1)
            if end > index + 1:
                emphasized = render_inline(
                    text[index + 1 : end],
                    context=context,
                    tag_prefix=tag_prefix,
                    include_link_class=include_link_class,
                )
                pieces.append(f"<{tag_prefix}em>{emphasized.html}</{tag_prefix}em>")
                visible.append(emphasized.visible_text)
                links.extend(emphasized.links)
                index = end + 1
                continue

        char = text[index]
        pieces.append(escape(char))
        visible.append(char)
        index += 1

    return InlineRender(
        html="".join(pieces),
        visible_text="".join(visible),
        links=tuple(links),
    )


def split_wikilink(raw: str) -> tuple[str, str | None]:
    if "|" not in raw:
        return raw.strip(), None
    target, label = raw.split("|", 1)
    return target.strip(), label.strip()


def normalize_wikilink_key(text: str) -> str:
    normalized = text.strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


def slugify_visible_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", " ", lowered).strip().lower()
    compact = re.sub(r"[\s-]+", "-", cleaned).strip("-")
    return compact or "section"


def unique_anchor_id(base: str, used_ids: set[str]) -> str:
    candidate = base
    counter = 2
    while candidate in used_ids:
        candidate = f"{base}-{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate


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


def render_start_tag(
    tag: str,
    attrs: list[tuple[str, str | None]],
    *,
    self_closing: bool = False,
) -> str:
    closing = " />" if self_closing else ">"
    return f"<{tag}{render_attributes(attrs)}{closing}"


def render_attributes(attrs: list[tuple[str, str | None]]) -> str:
    if not attrs:
        return ""
    rendered: list[str] = []
    for key, value in attrs:
        if value is None:
            rendered.append(key)
            continue
        rendered.append(f'{key}="{escape(value, quote=True)}"')
    return " " + " ".join(rendered)


def merge_attributes(
    attrs: list[tuple[str, str | None]],
    replacements: dict[str, str],
) -> list[tuple[str, str | None]]:
    existing = {key: value for key, value in attrs if key not in replacements}
    existing.update(replacements)
    return list(existing.items())


def html_entity_visible_text(value: str) -> str:
    if value.startswith("&#"):
        digits = value[2:-1]
        try:
            if digits.lower().startswith("x"):
                return chr(int(digits[1:], 16))
            return chr(int(digits, 10))
        except ValueError:
            return value
    entity_name = value[1:-1]
    return html_entity_name_map().get(entity_name, value)


def html_entity_name_map() -> dict[str, str]:
    return {
        "amp": "&",
        "lt": "<",
        "gt": ">",
        "quot": '"',
        "apos": "'",
    }


def rewrite_link_attributes(
    tag: str,
    attrs: list[tuple[str, str | None]],
    *,
    context: BodyContext,
) -> tuple[list[tuple[str, str | None]], BodyLink | None]:
    if tag != "a":
        return attrs, None

    attr_map = dict(attrs)
    href = attr_map.get("href")
    if not href:
        return attrs, None

    link = context.analyze_link(href)
    class_value = merge_class_values(attr_map.get("class"), link_class_name(link))
    rendered_href = context.render_href(link)
    ordered: list[tuple[str, str | None]] = [("class", class_value)]
    for key, value in attrs:
        if key == "class":
            continue
        if key == "href":
            ordered.append(("href", rendered_href))
            continue
        ordered.append((key, value))
    return ordered, link


def merge_class_values(existing: str | None, additions: str) -> str:
    current = existing.split() if existing else []
    for value in additions.split():
        if value not in current:
            current.append(value)
    return " ".join(current)


def link_class_name(link: BodyLink) -> str:
    if link.kind == "external":
        return "external-link"
    if link.kind == "work":
        return "internal-link work-link"
    return "internal-link"

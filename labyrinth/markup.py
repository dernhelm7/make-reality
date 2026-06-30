from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import posixpath
import re
import unicodedata
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .urls import relative_public_href


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
STANDARD_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<href>[^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[(?P<raw>[^\]]+)\]\]")
MARKDOWN = MarkdownIt("commonmark", {"html": False})


@dataclass(frozen=True)
class ResolvedWorkLink:
    title: str
    public_path: str


@dataclass(frozen=True)
class Heading:
    text: str
    anchor_id: str
    source_level: int


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
    asset_paths: frozenset[str] = frozenset()

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

    def analyze_asset(self, href: str) -> BodyLink:
        resolved = resolve_page_asset_path(self.current_public_path, href)
        if resolved is None:
            return BodyLink(href=href, resolved_path=None, fragment=None, kind="external")
        resolved_path, fragment = resolved
        return BodyLink(href=href, resolved_path=resolved_path, fragment=fragment, kind="asset")

    def render_asset_href(self, link: BodyLink) -> str:
        if link.kind == "external" or link.resolved_path is None:
            return link.href
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


def render_markdown_body(
    body_text: str,
    *,
    context: BodyContext,
) -> BodyRender:
    tokens = MARKDOWN.parse(body_text)
    expand_wikilinks(tokens, context=context)
    headings = apply_heading_self_links(tokens)
    links = rewrite_markdown_links(tokens, context=context)
    html = MARKDOWN.renderer.render(tokens, MARKDOWN.options, {}).rstrip("\n")
    return BodyRender(
        html=html,
        headings=tuple(headings),
        anchor_ids=frozenset(heading.anchor_id for heading in headings),
        links=tuple(links),
    )


def expand_wikilinks(tokens: list[Token], *, context: BodyContext) -> None:
    for token in tokens:
        if token.children:
            token.children = expand_wikilinks_in_children(token.children, context=context)


def expand_wikilinks_in_children(children: list[Token], *, context: BodyContext) -> list[Token]:
    expanded: list[Token] = []
    for token in children:
        if token.type != "text":
            if token.children:
                token.children = expand_wikilinks_in_children(token.children, context=context)
            expanded.append(token)
            continue

        cursor = 0
        for match in WIKILINK_RE.finditer(token.content):
            if match.start() > cursor:
                expanded.append(markdown_text_token(token.content[cursor : match.start()]))
            target, label = split_wikilink(match.group("raw"))
            visible_label = label or target
            resolved = context.resolve_wikilink(target)
            if resolved is None:
                expanded.append(markdown_text_token(visible_label))
            else:
                expanded.extend(markdown_link_tokens(resolved.public_path, visible_label))
            cursor = match.end()
        if cursor < len(token.content):
            expanded.append(markdown_text_token(token.content[cursor:]))
    return expanded


def markdown_text_token(text: str) -> Token:
    token = Token("text", "", 0)
    token.content = text
    return token


def markdown_link_tokens(href: str, label: str) -> list[Token]:
    link_open = Token("link_open", "a", 1)
    link_open.attrSet("href", href)
    text = markdown_text_token(label)
    link_close = Token("link_close", "a", -1)
    return [link_open, text, link_close]


def apply_heading_self_links(tokens: list[Token]) -> list[Heading]:
    headings: list[Heading] = []
    used_ids: set[str] = set()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        if index + 2 >= len(tokens):
            continue
        inline = tokens[index + 1]
        close = tokens[index + 2]
        if inline.type != "inline" or close.type != "heading_close":
            continue

        source_level = int(token.tag[1])
        rendered_level = min(6, source_level + 1)
        visible_text = markdown_visible_text(inline.children or ())
        anchor_id = unique_anchor_id(slugify_visible_text(visible_text), used_ids)
        token.tag = f"h{rendered_level}"
        close.tag = f"h{rendered_level}"
        token.attrSet("id", anchor_id)
        inline.children = heading_anchor_tokens(anchor_id, inline.children or [])
        headings.append(
            Heading(
                text=visible_text,
                anchor_id=anchor_id,
                source_level=source_level,
            )
        )
    return headings


def heading_anchor_tokens(anchor_id: str, children: list[Token]) -> list[Token]:
    link_open = Token("link_open", "a", 1)
    link_open.attrSet("class", "heading-anchor")
    link_open.attrSet("href", f"#{anchor_id}")
    link_close = Token("link_close", "a", -1)
    return [link_open, *children, link_close]


def rewrite_markdown_links(tokens: list[Token], *, context: BodyContext) -> list[BodyLink]:
    links: list[BodyLink] = []
    for token in tokens:
        rewrite_markdown_token_links(token, context=context, links=links)
    return links


def rewrite_markdown_token_links(token: Token, *, context: BodyContext, links: list[BodyLink]) -> None:
    if token.type == "link_open":
        if "heading-anchor" in (token.attrGet("class") or "").split():
            return
        href = token.attrGet("href")
        if not href:
            return
        link = context.analyze_link(href)
        token.attrSet("href", context.render_href(link))
        token.attrSet("class", merge_class_values(token.attrGet("class"), link_class_name(link)))
        links.append(link)
        return

    if token.type == "image":
        src = token.attrGet("src")
        if src:
            link = context.analyze_asset(src)
            token.attrSet("src", context.render_asset_href(link))
            links.append(link)
        return

    for child in token.children or ():
        rewrite_markdown_token_links(child, context=context, links=links)


def markdown_visible_text(tokens: tuple[Token, ...] | list[Token]) -> str:
    pieces: list[str] = []
    for token in tokens:
        if token.type in {"text", "code_inline"}:
            pieces.append(token.content)
            continue
        if token.type in {"softbreak", "hardbreak"}:
            pieces.append("\n")
            continue
        if token.type == "image":
            pieces.append(token.content)
            continue
        if token.children:
            pieces.append(markdown_visible_text(token.children))
    return "".join(pieces).strip()


def render_markdown_paragraphs(
    body_text: str,
    *,
    context: BodyContext,
    tag_prefix: str = "",
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
        )
        for lines in paragraphs
        if lines
    )


def render_markdown_paragraph_lines(
    lines: list[str],
    *,
    context: BodyContext,
    tag_prefix: str,
) -> InlineRender:
    pieces: list[str] = []
    visible: list[str] = []
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
        )
        pieces.append(inline.html)
        visible.append(inline.visible_text)
        prior_hard_break = hard_break

    return InlineRender(
        html="".join(pieces),
        visible_text="".join(visible),
    )


def strip_markdown_hard_break(line: str) -> tuple[str, bool]:
    if line.endswith("  "):
        return line[:-2], True
    stripped = line.rstrip()
    if stripped.endswith("\\"):
        return stripped[:-1], True
    return line, False


class HTMLAccumulator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []

    def append_html(self, html: str, visible_text: str | None = None) -> None:
        self.output.append(html)

    def handle_endtag(self, tag: str) -> None:
        self.append_html(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.append_html(data, visible_text=data)

    def handle_comment(self, data: str) -> None:
        self.append_html(f"<!--{data}-->")

    def handle_entityref(self, name: str) -> None:
        rendered = f"&{name};"
        self.append_html(rendered, visible_text=html_entity_visible_text(rendered))

    def handle_charref(self, name: str) -> None:
        rendered = f"&#{name};"
        self.append_html(rendered, visible_text=html_entity_visible_text(rendered))

    def render_output(self) -> str:
        return "".join(self.output)


class HTMLFragmentRewriter(HTMLAccumulator):
    def __init__(self, context: BodyContext) -> None:
        super().__init__()
        self.context = context
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
            self.append_html(rendered_tag)
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = tag
            self._heading_attrs = rendered_attrs
            self._heading_inner = []
            self._heading_text = []
            return

        self.append_html(rendered_tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        rendered_attrs, link = rewrite_link_attributes(
            tag,
            attrs,
            context=self.context,
        )
        if link is not None:
            self.links.append(link)
        rendered = render_start_tag(tag, rendered_attrs, self_closing=True)
        self.append_html(rendered)

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
                    )
                )
                self._heading_tag = None
                self._heading_attrs = []
                self._heading_inner = []
                self._heading_text = []
                return

            self.append_html(f"</{tag}>")
            return

        super().handle_endtag(tag)

    def append_html(self, html: str, visible_text: str | None = None) -> None:
        if self._heading_tag is not None:
            self._heading_inner.append(html)
            if visible_text is not None:
                self._heading_text.append(visible_text)
            return
        super().append_html(html, visible_text)

    def render(self) -> BodyRender:
        return BodyRender(
            html=self.render_output(),
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
) -> InlineRender:
    pieces: list[str] = []
    visible: list[str] = []
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
                    class_attr = f' class="{escape(link_class_name(link))}"'
                    pieces.append(
                        f'<{tag_prefix}a{class_attr} href="{escape(context.render_href(link))}">'
                        f"{escape(visible_label)}</{tag_prefix}a>"
                    )
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
                )
                class_attr = f' class="{escape(link_class_name(link))}"'
                pieces.append(
                    f'<{tag_prefix}a{class_attr} href="{escape(rendered_href)}">{rendered_label.html}</{tag_prefix}a>'
                )
                visible.append(rendered_label.visible_text)
                index = link_match.end()
                continue

        if text[index] == "_":
            end = text.find("_", index + 1)
            if end > index + 1:
                emphasized = render_inline(
                    text[index + 1 : end],
                    context=context,
                    tag_prefix=tag_prefix,
                )
                pieces.append(f"<{tag_prefix}em>{emphasized.html}</{tag_prefix}em>")
                visible.append(emphasized.visible_text)
                index = end + 1
                continue

        char = text[index]
        pieces.append(escape(char))
        visible.append(char)
        index += 1

    return InlineRender(
        html="".join(pieces),
        visible_text="".join(visible),
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
    return resolve_public_path(posixpath.dirname(current_public_path) or "/", href, empty_path=current_public_path)


def resolve_page_asset_path(current_public_path: str, href: str) -> tuple[str, str | None] | None:
    return resolve_public_path(current_public_path, href, empty_path=current_public_path)


def resolve_public_path(
    relative_base: str,
    href: str,
    *,
    empty_path: str,
) -> tuple[str, str | None] | None:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None

    raw_path = parts.path
    fragment = parts.fragment or None
    if raw_path == "":
        return empty_path, fragment

    if raw_path.startswith("/"):
        normalized = posixpath.normpath(raw_path)
    else:
        normalized = posixpath.normpath(posixpath.join(relative_base, raw_path))

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
    if link.kind == "asset":
        return "internal-link asset-link"
    return "internal-link"

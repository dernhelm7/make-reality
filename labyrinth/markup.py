from __future__ import annotations

from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import re
import unicodedata


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


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
class BodyRender:
    html: str
    headings: list[Heading]
    anchor_ids: set[str]
    authored_links: list[str]
    outbound_work_paths: set[str]


@dataclass(frozen=True)
class InlineRender:
    html: str
    visible_text: str
    authored_links: list[str]
    outbound_work_paths: set[str]


def render_markdown_body(
    body_text: str,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
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
    authored_links: list[str] = []
    outbound_work_paths: set[str] = set()
    used_ids: set[str] = set()

    for block_type, content, source_level in blocks:
        inline = render_inline(content, work_lookup, work_paths)
        authored_links.extend(inline.authored_links)
        outbound_work_paths.update(inline.outbound_work_paths)

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
        headings=headings,
        anchor_ids={heading.anchor_id for heading in headings},
        authored_links=authored_links,
        outbound_work_paths=outbound_work_paths,
    )


class HTMLFragmentRewriter(HTMLParser):
    def __init__(self, work_paths: set[str]) -> None:
        super().__init__(convert_charrefs=False)
        self.work_paths = work_paths
        self.output: list[str] = []
        self.headings: list[Heading] = []
        self.anchor_ids: set[str] = set()
        self.authored_links: list[str] = []
        self.outbound_work_paths: set[str] = set()
        self._heading_tag: str | None = None
        self._heading_attrs: list[tuple[str, str | None]] = []
        self._heading_inner: list[str] = []
        self._heading_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._heading_tag is not None:
            self._heading_inner.append(render_start_tag(tag, rewrite_link_attributes(tag, attrs, self.work_paths)))
            self._collect_link(tag, attrs)
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_tag = tag
            self._heading_attrs = attrs
            self._heading_inner = []
            self._heading_text = []
            return

        self._collect_link(tag, attrs)
        self.output.append(render_start_tag(tag, rewrite_link_attributes(tag, attrs, self.work_paths)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect_link(tag, attrs)
        rendered = render_start_tag(
            tag,
            rewrite_link_attributes(tag, attrs, self.work_paths),
            self_closing=True,
        )
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
                heading_attrs = merge_attributes(
                    self._heading_attrs,
                    {"id": anchor_id},
                )
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
            headings=self.headings,
            anchor_ids=self.anchor_ids,
            authored_links=self.authored_links,
            outbound_work_paths=self.outbound_work_paths,
        )

    def _collect_link(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        self.authored_links.append(href)


def render_html_body(
    body_text: str,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
) -> BodyRender:
    parser = HTMLFragmentRewriter(work_paths)
    parser.feed(body_text)
    parser.close()
    return parser.render()


def render_inline(
    text: str,
    work_lookup: dict[str, ResolvedWorkLink],
    work_paths: set[str],
) -> InlineRender:
    pieces: list[str] = []
    visible: list[str] = []
    authored_links: list[str] = []
    outbound_work_paths: set[str] = set()
    index = 0

    while index < len(text):
        if text.startswith("[[", index):
            end = text.find("]]", index + 2)
            if end != -1:
                raw = text[index + 2 : end]
                target, label = split_wikilink(raw)
                visible_label = label or target
                resolved = resolve_wikilink_target(target, work_lookup)
                if resolved is None:
                    pieces.append(escape(visible_label))
                else:
                    pieces.append(
                        f'<a class="internal-link work-link" href="{escape(resolved.public_path)}">'
                        f"{escape(visible_label)}</a>"
                    )
                    outbound_work_paths.add(resolved.public_path)
                visible.append(visible_label)
                index = end + 2
                continue

        if text[index] == "[":
            link_match = STANDARD_LINK_RE.match(text, index)
            if link_match:
                label = link_match.group("label")
                href = link_match.group("href")
                link_class = classify_link(href, work_paths)
                pieces.append(
                    f'<a class="{escape(link_class)}" href="{escape(href)}">{escape(label)}</a>'
                )
                visible.append(label)
                authored_links.append(href)
                index = link_match.end()
                continue

        char = text[index]
        pieces.append(escape(char))
        visible.append(char)
        index += 1

    return InlineRender(
        html="".join(pieces),
        visible_text="".join(visible),
        authored_links=authored_links,
        outbound_work_paths=outbound_work_paths,
    )


STANDARD_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<href>[^)]+)\)")


def split_wikilink(raw: str) -> tuple[str, str | None]:
    if "|" not in raw:
        return raw.strip(), None
    target, label = raw.split("|", 1)
    return target.strip(), label.strip()


def resolve_wikilink_target(
    raw_target: str,
    work_lookup: dict[str, ResolvedWorkLink],
) -> ResolvedWorkLink | None:
    return work_lookup.get(normalize_wikilink_key(raw_target))


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
    work_paths: set[str],
) -> list[tuple[str, str | None]]:
    if tag != "a":
        return attrs

    attr_map = dict(attrs)
    href = attr_map.get("href")
    if not href:
        return attrs

    class_value = merge_class_values(attr_map.get("class"), classify_link(href, work_paths))
    ordered = [("class", class_value)]
    for key, value in attrs:
        if key == "class":
            continue
        ordered.append((key, value))
    if not any(key == "href" for key, _value in ordered):
        ordered.append(("href", href))
    return ordered


def merge_class_values(existing: str | None, additions: str) -> str:
    current = existing.split() if existing else []
    for value in additions.split():
        if value not in current:
            current.append(value)
    return " ".join(current)


def classify_link(href: str, work_paths: set[str]) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return "external-link"

    path = href.split("#", 1)[0]
    if path in work_paths:
        return "internal-link work-link"
    return "internal-link"

from __future__ import annotations

from pathlib import Path
import re

from .model import BuildError


STYLE_SOURCE_DIR = Path(__file__).resolve().with_name("style_sources")
STYLE_SOURCE_ORDER = (
    "fonts.css",
    "tokens.css",
    "base.css",
    "header.css",
    "layout.css",
    "rail.css",
    "contents.css",
    "reading.css",
    "responsive.css",
    "print.css",
)
FEED_STYLE_SOURCE = "feed.css"
THEME_PAGE_RGB_PLACEHOLDERS = {
    "__THEME_LIGHT_PAGE_RGB__": "--theme-light-page",
    "__THEME_DARK_PAGE_RGB__": "--theme-dark-page",
}


def render_stylesheet() -> str:
    parts = [read_stylesheet_source(name) for name in STYLE_SOURCE_ORDER]
    return "\n\n".join(part for part in parts if part) + "\n"


def render_feed_stylesheet() -> str:
    parts = [
        read_stylesheet_source("fonts.css"),
        read_stylesheet_source("tokens.css"),
        read_stylesheet_source("header.css"),
        read_stylesheet_source(FEED_STYLE_SOURCE),
    ]
    return "\n\n".join(part for part in parts if part) + "\n"


def read_stylesheet_source(name: str) -> str:
    path = STYLE_SOURCE_DIR / name
    source = path.read_text(encoding="utf-8").strip()
    if name == "tokens.css":
        return render_theme_tokens(source, path)
    return source


def render_theme_tokens(source: str, source_path: Path) -> str:
    rendered = source
    for placeholder, variable_name in THEME_PAGE_RGB_PLACEHOLDERS.items():
        match = re.search(
            rf"^\s*{re.escape(variable_name)}:\s*(#[0-9a-fA-F]{{6}})\s*;",
            source,
            re.MULTILINE,
        )
        if not match:
            raise BuildError(
                source_path,
                "missing-required-field",
                f"{variable_name} must be an active six-digit hex color",
            )
        color = match.group(1)
        channels = ",".join(str(int(color[offset : offset + 2], 16)) for offset in (1, 3, 5))
        rendered = rendered.replace(placeholder, channels)
    return rendered

from __future__ import annotations

from pathlib import Path


STYLE_SOURCE_DIR = Path(__file__).resolve().with_name("style_sources")
STYLE_SOURCE_ORDER = (
    "fonts.css",
    "tokens.css",
    "base.css",
    "layout.css",
    "rail.css",
    "contents.css",
    "reading.css",
    "responsive.css",
    "print.css",
)
FEED_STYLE_SOURCE = "feed.css"


def render_stylesheet() -> str:
    parts = [read_stylesheet_source(name) for name in STYLE_SOURCE_ORDER]
    return "\n\n".join(part for part in parts if part) + "\n"


def render_feed_stylesheet() -> str:
    parts = [
        read_stylesheet_source("tokens.css"),
        read_stylesheet_source(FEED_STYLE_SOURCE),
    ]
    return "\n\n".join(part for part in parts if part) + "\n"


def read_stylesheet_source(name: str) -> str:
    return (STYLE_SOURCE_DIR / name).read_text(encoding="utf-8").strip()

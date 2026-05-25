from __future__ import annotations

import math
from pathlib import Path

from .model import SiteConfig


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


def render_stylesheet(site: SiteConfig) -> str:
    parts = [
        render_theme_settings(site),
        *(read_stylesheet_source(name) for name in STYLE_SOURCE_ORDER),
    ]
    return "\n\n".join(part for part in parts if part) + "\n"


def render_feed_stylesheet(site: SiteConfig) -> str:
    parts = [
        render_theme_settings(site),
        read_stylesheet_source("fonts.css"),
        read_stylesheet_source("tokens.css"),
        read_stylesheet_source("header.css"),
        read_stylesheet_source(FEED_STYLE_SOURCE),
    ]
    return "\n\n".join(part for part in parts if part) + "\n"


def render_theme_settings(site: SiteConfig) -> str:
    dark_page_color = dark_page_color_for_primary(site.primary_color)
    return f":root {{ --primary-color: {site.primary_color}; --primary-dark-page: {dark_page_color}; }}"


def dark_page_color_for_primary(primary_color: str) -> str:
    _, a, b = hex_to_oklab(primary_color)
    hue = math.atan2(b, a)
    red, green, blue = oklch_to_srgb_bytes(0.18, 0.04, hue)
    return f"#{red:02x}{green:02x}{blue:02x}"


def hex_to_oklab(color: str) -> tuple[float, float, float]:
    red = srgb_channel_to_linear(int(color[1:3], 16) / 255)
    green = srgb_channel_to_linear(int(color[3:5], 16) / 255)
    blue = srgb_channel_to_linear(int(color[5:7], 16) / 255)

    long = 0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    medium = 0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    short = 0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue

    long_root = math.copysign(abs(long) ** (1 / 3), long)
    medium_root = math.copysign(abs(medium) ** (1 / 3), medium)
    short_root = math.copysign(abs(short) ** (1 / 3), short)

    return (
        0.2104542553 * long_root + 0.7936177850 * medium_root - 0.0040720468 * short_root,
        1.9779984951 * long_root - 2.4285922050 * medium_root + 0.4505937099 * short_root,
        0.0259040371 * long_root + 0.7827717662 * medium_root - 0.8086757660 * short_root,
    )


def oklch_to_srgb_bytes(lightness: float, chroma: float, hue: float) -> tuple[int, int, int]:
    a = chroma * math.cos(hue)
    b = chroma * math.sin(hue)

    long_root = lightness + 0.3963377774 * a + 0.2158037573 * b
    medium_root = lightness - 0.1055613458 * a - 0.0638541728 * b
    short_root = lightness - 0.0894841775 * a - 1.2914855480 * b

    long = long_root**3
    medium = medium_root**3
    short = short_root**3

    red = +4.0767416621 * long - 3.3077115913 * medium + 0.2309699292 * short
    green = -1.2684380046 * long + 2.6097574011 * medium - 0.3413193965 * short
    blue = -0.0041960863 * long - 0.7034186147 * medium + 1.7076147010 * short

    return tuple(round(linear_channel_to_srgb(channel) * 255) for channel in (red, green, blue))


def srgb_channel_to_linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def linear_channel_to_srgb(channel: float) -> float:
    channel = min(1, max(0, channel))
    if channel <= 0.0031308:
        return 12.92 * channel
    return 1.055 * (channel ** (1 / 2.4)) - 0.055


def read_stylesheet_source(name: str) -> str:
    return (STYLE_SOURCE_DIR / name).read_text(encoding="utf-8").strip()

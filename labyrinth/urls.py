from __future__ import annotations

from dataclasses import dataclass
import posixpath
from urllib.parse import SplitResult, urljoin, urlsplit, urlunsplit


HOME_PUBLIC_PATH = "/"
FEED_PUBLIC_PATH = "/feed.xml"
FEED_STYLESHEET_PUBLIC_PATH = "/feed.css"
SITE_STYLESHEET_PUBLIC_PATH = "/site.css"
FIXED_PUBLIC_PATHS = frozenset(
    {
        HOME_PUBLIC_PATH,
        FEED_PUBLIC_PATH,
        FEED_STYLESHEET_PUBLIC_PATH,
        SITE_STYLESHEET_PUBLIC_PATH,
    }
)


@dataclass(frozen=True)
class PageUrls:
    site_url: str
    build_url: str
    public_path: str

    @property
    def canonical_url(self) -> str:
        return canonical_url(self.site_url, self.public_path)

    @property
    def output_url(self) -> str:
        return canonical_url(self.build_url, self.public_path)

    @property
    def base_href(self) -> str:
        return page_base_href(self.build_url, self.public_path)

    def relative_href(self, target_public_path: str, *, fragment: str | None = None) -> str:
        return relative_public_href(self.public_path, target_public_path, fragment=fragment)

    def root_relative_href(self, href: str) -> str:
        return rewrite_root_relative_url(self.public_path, href)

    def absolute_href(self, href: str) -> str:
        return absolute_href(self.build_url, self.public_path, href)


def site_path_prefix(base_url: str) -> str:
    return urlsplit(base_url).path.rstrip("/")


def public_url(base_url: str, public_path: str) -> str:
    prefix = site_path_prefix(base_url)
    if public_path == "/":
        return f"{prefix}/" if prefix else "/"
    return f"{prefix}{public_path}"


def canonical_url(base_url: str, public_path: str) -> str:
    if public_path == "/":
        return base_url
    return f"{base_url}{public_path}"


def page_base_href(base_url: str, public_path: str) -> str:
    if public_path == "/":
        return f"{base_url}/"
    return f"{canonical_url(base_url, public_path)}/"


def relative_public_href(from_public_path: str, target_public_path: str, *, fragment: str | None = None) -> str:
    current_dir = "." if from_public_path == "/" else from_public_path.lstrip("/")
    if target_public_path == "/":
        path = "./" if from_public_path == "/" else f"{posixpath.relpath('.', current_dir)}/"
    else:
        path = posixpath.relpath(target_public_path.lstrip("/"), current_dir)
    if fragment:
        return f"{path}#{fragment}"
    return path


def rewrite_root_relative_url(from_public_path: str, href: str) -> str:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not parts.path.startswith("/"):
        return href
    fragment = parts.fragment or None
    return urlunsplit(
        SplitResult(
            scheme="",
            netloc="",
            path=relative_public_href(from_public_path, parts.path),
            query=parts.query,
            fragment=fragment or "",
        )
    )


def absolute_href(base_url: str, from_public_path: str, href: str) -> str:
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return href

    site = urlsplit(base_url)
    if parts.path.startswith("/"):
        return urlunsplit(
            SplitResult(
                scheme=site.scheme,
                netloc=site.netloc,
                path=public_url(base_url, parts.path),
                query=parts.query,
                fragment=parts.fragment,
            )
        )

    if not parts.path:
        return urlunsplit(
            SplitResult(
                scheme=site.scheme,
                netloc=site.netloc,
                path=public_url(base_url, from_public_path),
                query=parts.query,
                fragment=parts.fragment,
            )
        )

    return urljoin(page_base_href(base_url, from_public_path), href)

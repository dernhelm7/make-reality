from __future__ import annotations

import posixpath
from urllib.parse import SplitResult, urlsplit, urlunsplit


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

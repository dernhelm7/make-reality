from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from .model import BuildError, build_site_graph, load_site_config, load_work_inputs
from .publish import prepare_temp_publish_root, replace_publish_root, write_public_files
from .render import RenderedPage, render_feed, render_pages, validate_rendered_pages
from .theme import render_feed_stylesheet, render_stylesheet


@dataclass(frozen=True)
class BuildResult:
    site_root: Path
    publish_root: Path
    page_count: int


def build_site(site_root: Path, publish_root: Path, *, build_url: str | None = None) -> BuildResult:
    site_root = site_root.resolve()
    publish_root = publish_root.resolve()
    site = load_site_config(site_root, build_url=build_url)
    work_inputs = load_work_inputs(site_root)
    graph = build_site_graph(site, work_inputs)
    rendered_pages = render_pages(graph)
    stylesheet = render_stylesheet()
    feed_stylesheet = render_feed_stylesheet()
    feed = render_feed(graph)

    temp_root = prepare_temp_publish_root(publish_root)
    try:
        write_public_files(temp_root, rendered_pages, stylesheet, feed_stylesheet, feed)
        validate_rendered_pages(rendered_pages)
        replace_publish_root(temp_root, publish_root)
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise

    return BuildResult(site_root=site_root, publish_root=publish_root, page_count=len(rendered_pages))

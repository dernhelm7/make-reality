from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from .render import RenderedPage


def prepare_temp_publish_root(publish_root: Path) -> Path:
    publish_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=".labyrinth-build-", dir=publish_root.parent))


def write_public_files(
    publish_root: Path,
    rendered_pages: list[RenderedPage],
    stylesheet: str,
    feed_stylesheet: str,
    feed_transform: str,
    feed: str,
) -> None:
    for page in rendered_pages:
        output_path = publish_root / page.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(page.html, encoding="utf-8")

    (publish_root / "site.css").write_text(stylesheet, encoding="utf-8")
    (publish_root / "feed.css").write_text(feed_stylesheet, encoding="utf-8")
    (publish_root / "feed.xsl").write_text(feed_transform, encoding="utf-8")
    write_shared_public_assets(publish_root)
    (publish_root / "feed.xml").write_text(feed, encoding="utf-8")


def replace_publish_root(temp_root: Path, publish_root: Path) -> None:
    if publish_root.exists():
        shutil.rmtree(publish_root)
    temp_root.rename(publish_root)


def write_shared_public_assets(publish_root: Path) -> None:
    assets_root = Path(__file__).resolve().parent / "assets"
    if not assets_root.exists():
        return

    for source_path in sorted(path for path in assets_root.rglob("*") if path.is_file()):
        output_path = publish_root / source_path.relative_to(assets_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)

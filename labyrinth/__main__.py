from __future__ import annotations

import sys
from pathlib import Path

from .builder import BuildError, build_site


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "build":
        args = args[1:]
    if len(args) != 2:
        print("Usage: python3 -m labyrinth build <site-root> <publish-root>", file=sys.stderr)
        return 1

    site_root = Path(args[0])
    publish_root = Path(args[1])
    try:
        build_site(site_root, publish_root)
    except BuildError as error:
        print(f"{error.source_path}: [{error.rule}] {error.message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

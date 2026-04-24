from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .builder import BuildError, build_site


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "build":
        args = args[1:]

    parser = argparse.ArgumentParser(prog="python3 -m labyrinth build")
    parser.add_argument("--build-url", help="override the output base URL for this build")
    parser.add_argument("site_root")
    parser.add_argument("publish_root")
    try:
        parsed = parser.parse_args(args)
    except SystemExit as error:
        return int(error.code)

    site_root = Path(parsed.site_root)
    publish_root = Path(parsed.publish_root)
    try:
        build_site(site_root, publish_root, build_url=parsed.build_url)
    except BuildError as error:
        print(f"{error.source_path}: [{error.rule}] {error.message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

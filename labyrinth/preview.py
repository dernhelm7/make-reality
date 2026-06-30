from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class PreviewRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(prog="python3 -m labyrinth.preview")
    parser.add_argument("port", type=int)
    parser.add_argument("publish_root", type=Path)
    args = parser.parse_args()

    handler = partial(PreviewRequestHandler, directory=str(args.publish_root))
    with ThreadingHTTPServer(("", args.port), handler) as server:
        print(f"Serving preview on port {args.port} (http://localhost:{args.port}/) ...", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

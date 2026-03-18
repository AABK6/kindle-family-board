from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.pipeline import generate_board  # noqa: E402
from kindle_family_board.runtime import current_local_ip, load_repo_env, server_port  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the generated Kindle board output directory over HTTP.")
    parser.add_argument("--port", type=int, default=None, help="Port to bind. Defaults to KFB_SERVER_PORT or 8765.")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind.")
    parser.add_argument("--generate-first", action="store_true", help="Generate a fresh board before serving.")
    return parser.parse_args()


def main() -> int:
    load_repo_env()
    args = parse_args()
    config = BoardConfig.from_env()
    if args.generate_first:
        generate_board(config=config)

    config.output_dir.mkdir(parents=True, exist_ok=True)
    port = args.port or server_port()
    handler = partial(SimpleHTTPRequestHandler, directory=str(config.output_dir))
    try:
        server = ThreadingHTTPServer((args.host, port), handler)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048:
            print(f"Server already running on {args.host}:{port}")
            return 0
        raise

    print(f"Serving {config.output_dir}")
    print(f"Local URL: http://127.0.0.1:{port}/latest.png")
    print(f"LAN URL:   http://{current_local_ip()}:{port}/latest.png")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

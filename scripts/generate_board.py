from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.pipeline import generate_board  # noqa: E402
from kindle_family_board.runtime import load_repo_env  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the daily Kindle family board.")
    parser.add_argument("--date", help="Override the render date (YYYY-MM-DD).")
    parser.add_argument("--output-dir", help="Override the output directory.")
    parser.add_argument("--skip-gemini", action="store_true", help="Force fallback reading content.")
    return parser.parse_args()


def main() -> int:
    load_repo_env()
    args = parse_args()
    config = BoardConfig.from_env()
    if args.output_dir:
        config.output_dir = Path(args.output_dir).expanduser()
    if args.skip_gemini:
        config.gemini_api_key = None

    target_date = date.fromisoformat(args.date) if args.date else None
    image_path, manifest_path = generate_board(config=config, target_date=target_date)
    print(f"Generated image: {image_path}")
    print(f"Generated manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

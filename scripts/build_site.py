from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.pipeline import generate_board  # noqa: E402
from kindle_family_board.runtime import load_repo_env  # noqa: E402


def build_index(site_dir: Path) -> None:
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kindle Family Board</title>
  <style>
    body { font-family: Georgia, serif; margin: 2rem; background: #f3f0e8; color: #1f1c18; }
    main { max-width: 720px; margin: 0 auto; }
    img { width: min(100%, 600px); border: 2px solid #1f1c18; border-radius: 12px; display: block; }
    a { color: #1f1c18; }
    p { line-height: 1.5; }
  </style>
</head>
<body>
  <main>
    <h1>Kindle Family Board</h1>
    <p>Latest generated image for the Kindle display.</p>
    <p><a href="latest.png">PNG</a> | <a href="latest.json">JSON</a></p>
    <img src="latest.png" alt="Latest Kindle family board image">
  </main>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> int:
    load_repo_env()
    config = BoardConfig.from_env()
    config.output_dir = REPO_ROOT / "site"
    generate_board(config=config)
    build_index(config.output_dir)
    print(f"Built site in {config.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

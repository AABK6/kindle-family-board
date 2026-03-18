from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.pipeline import build_content  # noqa: E402
from kindle_family_board.render import render_board  # noqa: E402
from kindle_family_board.runtime import load_repo_env  # noqa: E402


def main() -> int:
    load_repo_env()
    config = BoardConfig.from_env()
    content, _ = build_content(config=config)
    preview_dir = REPO_ROOT / "output" / "icon-previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    for style in ("orbit", "burst", "ticket"):
        styled_config = replace(config, icon_style=style)
        target_path = preview_dir / f"{style}.png"
        render_board(content, styled_config, target_path)
        print(target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

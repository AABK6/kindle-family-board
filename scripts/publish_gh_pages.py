from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = REPO_ROOT / "site"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and publish the static site to the gh-pages branch.")
    parser.add_argument("--repo", default="AABK6/kindle-family-board", help="GitHub owner/repo.")
    parser.add_argument("--branch", default="gh-pages", help="Target branch for the static site.")
    parser.add_argument("--skip-build", action="store_true", help="Publish the existing site/ directory without rebuilding it.")
    return parser.parse_args()


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def build_site() -> None:
    run([sys.executable, str(REPO_ROOT / "scripts" / "build_site.py")], cwd=REPO_ROOT)


def main() -> int:
    args = parse_args()
    if not args.skip_build:
        build_site()

    if not SITE_DIR.exists():
        raise RuntimeError(f"Site directory does not exist: {SITE_DIR}")

    with tempfile.TemporaryDirectory(prefix="kfb-gh-pages-") as tmp_dir:
        publish_root = Path(tmp_dir) / "publish"
        shutil.copytree(SITE_DIR, publish_root)

        run(["git", "init", "-b", args.branch], cwd=publish_root)
        run(["git", "config", "user.name", "Codex"], cwd=publish_root)
        run(["git", "config", "user.email", "codex@local"], cwd=publish_root)
        run(["git", "add", "."], cwd=publish_root)
        run(
            ["git", "commit", "-m", f"Publish board {datetime.now().isoformat(timespec='seconds')}"],
            cwd=publish_root,
        )
        run(["git", "remote", "add", "origin", f"https://github.com/{args.repo}.git"], cwd=publish_root)
        run(["git", "push", "-f", "origin", f"{args.branch}:{args.branch}"], cwd=publish_root)

    print(f"Published {SITE_DIR} to https://github.com/{args.repo}/tree/{args.branch}")
    print(f"Expected board URL: https://{args.repo.split('/', 1)[0].lower()}.github.io/{args.repo.split('/', 1)[1]}/latest.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

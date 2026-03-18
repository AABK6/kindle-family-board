from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.kindle import connect, exec_command  # noqa: E402
from kindle_family_board.runtime import load_repo_env  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Arm a one-shot Kindle wake/display test.")
    parser.add_argument("--host", help="Kindle IP address.")
    parser.add_argument("--time", required=True, help="Local target time in HH:MM, interpreted in KFB_TIMEZONE.")
    parser.add_argument("--remote-root", default="/mnt/us/kindle-family-board", help="Target root on Kindle.")
    parser.add_argument("--display-only", action="store_true", help="Only redraw the cached image; skip fetch_and_display.")
    return parser.parse_args()


def main() -> int:
    load_repo_env()
    args = parse_args()
    config = BoardConfig.from_env()
    hour, minute = [int(part) for part in args.time.split(":", 1)]
    now = config.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        raise RuntimeError(f"Target time {args.time} is not in the future. Current time is {now.strftime('%H:%M:%S')}.")

    delay_seconds = int((target - now).total_seconds())
    if delay_seconds <= 0:
        raise RuntimeError(f"Target time {args.time} is not in the future. Current time is {now.strftime('%H:%M:%S')}.")
    remote_root = args.remote_root.rstrip("/")
    remote_script = f"{remote_root}/one_shot_wake_test.sh"
    mode_prefix = "KFB_WAKE_TEST_MODE=display-only " if args.display_only else ""
    background_cmd = (
        f"nohup sh -c '{mode_prefix}{remote_script} {remote_root} {delay_seconds}' >/dev/null 2>&1 &"
    )

    client, auth = connect(host=args.host)
    try:
        code, out, err = exec_command(client, background_cmd, timeout=20.0)
        if code != 0:
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            raise RuntimeError("Failed to arm wake test.")
        print(f"Armed wake test on {auth.host} for {target.isoformat()}")
        print(f"Delay seconds: {delay_seconds}")
        print(f"Log file: {remote_root}/cache/wake-test.log")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

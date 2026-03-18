from __future__ import annotations

import argparse
from datetime import timedelta
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
    parser = argparse.ArgumentParser(description="Run a short Kindle morning-board cycle to test restore timing.")
    parser.add_argument("--host", help="Kindle IP address.")
    parser.add_argument("--remote-root", default="/mnt/us/kindle-family-board", help="Target directory on the Kindle.")
    parser.add_argument("--hold-seconds", type=int, default=60, help="Temporary hold duration for the board screensaver.")
    parser.add_argument(
        "--force-sleep-after",
        type=int,
        default=20,
        help="Seconds after launch to trigger a normal sleep with powerd_test -p. Use 0 to skip forced sleep.",
    )
    return parser.parse_args()


def main() -> int:
    load_repo_env()
    args = parse_args()
    config = BoardConfig.from_env()
    remote_root = args.remote_root.rstrip("/")
    remote_env = f"{remote_root}/board.env"
    remote_run = f"{remote_root}/run_morning_board.sh"

    start_at = config.now()
    restore_at = start_at + timedelta(seconds=args.hold_seconds)

    client, auth = connect(host=args.host)
    try:
        if args.force_sleep_after > 0:
            sleep_cmd = (
                "/sbin/start-stop-daemon -S -b -x /bin/sh -- "
                f"-c 'sleep {args.force_sleep_after}; powerd_test -p >/dev/null 2>&1'"
            )
            code, _, err = exec_command(client, sleep_cmd, timeout=20.0)
            if code != 0:
                raise RuntimeError(err or "Failed to arm forced sleep.")

        run_cmd = (
            f". {remote_env} && "
            f"KFB_MORNING_HOLD_SECONDS={args.hold_seconds} "
            f"{remote_run} {remote_root}"
        )
        code, out, err = exec_command(client, run_cmd, timeout=90.0)
        sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
        if code != 0:
            raise RuntimeError("Short restore cycle failed.")

        print(f"Connected to Kindle at {auth.host}")
        print(f"Board hold duration: {args.hold_seconds} seconds")
        if args.force_sleep_after > 0:
            print(f"Forced sleep in: {args.force_sleep_after} seconds")
        else:
            print("Forced sleep: disabled")
        print(f"Expected restore time: {restore_at.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Morning log: {remote_root}/cache/morning.log")
        print(f"Restore log: {remote_root}/cache/restore.log")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

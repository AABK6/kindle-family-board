from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from kindle_family_board.config import BoardConfig  # noqa: E402
from kindle_family_board.kindle import connect, exec_command  # noqa: E402
from kindle_family_board.runtime import current_local_ip, load_repo_env, server_port  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy Kindle Family Board scripts to the Kindle over Wi-Fi SSH.")
    parser.add_argument("--host", help="Skip auto-discovery and connect to this Kindle IP.")
    parser.add_argument("--remote-root", default="/mnt/us/kindle-family-board", help="Target directory on the Kindle.")
    parser.add_argument("--board-url", help="Full URL to latest.png. Defaults to http://<local-ip>:<port>/latest.png")
    parser.add_argument("--port", type=int, default=None, help="Port used for the default board URL.")
    parser.add_argument("--install-cron", action="store_true", help="Install the 07:00 cron entry after upload.")
    parser.add_argument("--run-now", action="store_true", help="Run the fetch/display script immediately after upload.")
    parser.add_argument("--run-morning-now", action="store_true", help="Run the full morning board flow immediately after upload.")
    parser.add_argument("--install-self-heal", action="store_true", help="Install the linkss boot hook that re-seeds cron on reboot.")
    parser.add_argument(
        "--upload-current-image",
        action="store_true",
        help="Upload output/latest.png directly to the Kindle cache and display it immediately.",
    )
    parser.add_argument(
        "--upload-normal-screensavers",
        action="store_true",
        help="Upload output/new-screensavers/*.png as the Kindle's normal screensaver set.",
    )
    parser.add_argument(
        "--normal-screensavers-dir",
        help="Local directory containing 600x800 screensavers to upload. Defaults to output/new-screensavers.",
    )
    parser.add_argument(
        "--install-normal-screensavers",
        action="store_true",
        help="Install the uploaded normal screensaver set into linkss/screensavers immediately.",
    )
    return parser.parse_args()


def upload_file(sftp, local_path: Path, remote_path: str) -> None:
    sftp.put(str(local_path), remote_path)


def main() -> int:
    load_repo_env()
    args = parse_args()
    port = args.port or server_port()
    config = BoardConfig.from_env()
    default_local_url = f"http://{current_local_ip()}:{port}/latest.png"
    default_env_url = config.board_url if config.board_url and "example.com" not in config.board_url else default_local_url
    board_url = args.board_url or default_env_url
    hold_seconds = os.getenv("KFB_MORNING_HOLD_SECONDS", "10800")
    screensaver_name = os.getenv("KFB_LINKSS_SCREENSAVER_NAME", "bg_xsmall_ss00.png")
    wake_target_hour = os.getenv("KFB_WAKE_TARGET_HOUR", "7")
    wake_target_minute = os.getenv("KFB_WAKE_TARGET_MINUTE", "0")

    client, auth = connect(host=args.host)
    try:
        remote_root = args.remote_root.rstrip("/")
        code, _, err = exec_command(client, f"mkdir -p {remote_root}/cache")
        if code != 0:
            raise RuntimeError(err or "Failed to create remote directory.")

        sftp = client.open_sftp()
        try:
            upload_file(sftp, REPO_ROOT / "kindle" / "fetch_and_display.sh", f"{remote_root}/fetch_and_display.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "install_cron.sh", f"{remote_root}/install_cron.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "boot_reseed.sh", f"{remote_root}/boot_reseed.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "daily_wake_scheduler.sh", f"{remote_root}/daily_wake_scheduler.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "start_daily_wake_scheduler.sh", f"{remote_root}/start_daily_wake_scheduler.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "stop_daily_wake_scheduler.sh", f"{remote_root}/stop_daily_wake_scheduler.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "one_shot_wake_test.sh", f"{remote_root}/one_shot_wake_test.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "run_morning_board.sh", f"{remote_root}/run_morning_board.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "persist_morning_screensaver.sh", f"{remote_root}/persist_morning_screensaver.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "restore_screensavers.sh", f"{remote_root}/restore_screensavers.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "restore_after_delay.sh", f"{remote_root}/restore_after_delay.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "stop_restore_after_delay.sh", f"{remote_root}/stop_restore_after_delay.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "board_screensaver_watchdog.sh", f"{remote_root}/board_screensaver_watchdog.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "start_board_watchdog.sh", f"{remote_root}/start_board_watchdog.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "stop_board_watchdog.sh", f"{remote_root}/stop_board_watchdog.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "one_shot_screensaver_refresh.sh", f"{remote_root}/one_shot_screensaver_refresh.sh")
            upload_file(sftp, REPO_ROOT / "kindle" / "install_normal_screensavers.sh", f"{remote_root}/install_normal_screensavers.sh")

            board_env = "\n".join(
                [
                    f"export BOARD_URL={board_url}",
                    f"export CACHE_DIR={remote_root}/cache",
                    f"export KFB_MORNING_HOLD_SECONDS={hold_seconds}",
                    f"export KFB_LINKSS_SCREENSAVER_NAME={screensaver_name}",
                    f"export KFB_NORMAL_SCREENSAVER_DIR={remote_root}/normal-screensavers",
                    f"export KFB_WAKE_TARGET_HOUR={wake_target_hour}",
                    f"export KFB_WAKE_TARGET_MINUTE={wake_target_minute}",
                    "export CURL_BIN=/mnt/us/usbnet/bin/curl",
                    "export EIPS_BIN=/usr/sbin/eips",
                    "",
                ]
            )
            remote_env_path = f"{remote_root}/board.env"
            with sftp.file(remote_env_path, "w") as remote_file:
                remote_file.write(board_env)

            if args.upload_current_image:
                local_image = REPO_ROOT / "output" / "latest.png"
                if not local_image.exists():
                    raise RuntimeError(f"Current board image not found: {local_image}")
                upload_file(sftp, local_image, f"{remote_root}/cache/latest.png")

            if args.upload_normal_screensavers:
                local_normal_dir = Path(args.normal_screensavers_dir) if args.normal_screensavers_dir else REPO_ROOT / "output" / "new-screensavers"
                if not local_normal_dir.exists():
                    raise RuntimeError(f"Normal screensavers directory not found: {local_normal_dir}")
                remote_normal_dir = f"{remote_root}/normal-screensavers"
                code, _, err = exec_command(client, f"mkdir -p {remote_normal_dir}")
                if code != 0:
                    raise RuntimeError(err or f"Failed to create remote screensaver directory: {remote_normal_dir}")
                for image_path in sorted(local_normal_dir.glob("*.png")):
                    if image_path.name == "contact-sheet.png":
                        continue
                    upload_file(sftp, image_path, f"{remote_normal_dir}/{image_path.name}")
        finally:
            sftp.close()

        chmod_cmd = (
            f"chmod +x {remote_root}/fetch_and_display.sh {remote_root}/install_cron.sh "
            f"{remote_root}/boot_reseed.sh {remote_root}/daily_wake_scheduler.sh "
            f"{remote_root}/start_daily_wake_scheduler.sh {remote_root}/stop_daily_wake_scheduler.sh "
            f"{remote_root}/one_shot_wake_test.sh "
            f"{remote_root}/run_morning_board.sh {remote_root}/persist_morning_screensaver.sh "
            f"{remote_root}/restore_screensavers.sh {remote_root}/restore_after_delay.sh "
            f"{remote_root}/stop_restore_after_delay.sh "
            f"{remote_root}/board_screensaver_watchdog.sh {remote_root}/start_board_watchdog.sh "
            f"{remote_root}/stop_board_watchdog.sh {remote_root}/one_shot_screensaver_refresh.sh "
            f"{remote_root}/install_normal_screensavers.sh"
        )
        code, _, err = exec_command(client, chmod_cmd)
        if code != 0:
            raise RuntimeError(err or "chmod failed")

        print(f"Connected to Kindle at {auth.host} as {auth.user}")
        print(f"Configured board URL: {board_url}")
        print(f"Uploaded scripts to {remote_root}")

        if args.install_cron:
            code, out, err = exec_command(client, f"{remote_root}/install_cron.sh {remote_root}")
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if code != 0:
                raise RuntimeError("Cron install failed.")

        if args.install_self_heal:
            sftp = client.open_sftp()
            try:
                upload_file(sftp, REPO_ROOT / "kindle" / "linkss_emergency.sh", "/mnt/us/linkss/bin/emergency.sh")
            finally:
                sftp.close()
            code, _, err = exec_command(client, "chmod +x /mnt/us/linkss/bin/emergency.sh")
            if code != 0:
                raise RuntimeError(err or "Failed to install linkss emergency hook.")

        if args.upload_current_image:
            code, out, err = exec_command(client, f"/usr/sbin/eips -f -g {remote_root}/cache/latest.png", timeout=60.0)
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if code != 0:
                raise RuntimeError("Direct image display failed.")

        if args.run_now:
            code, out, err = exec_command(client, f". {remote_root}/board.env && {remote_root}/fetch_and_display.sh", timeout=60.0)
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if code != 0:
                raise RuntimeError("Immediate fetch/display failed.")

        if args.run_morning_now:
            code, out, err = exec_command(client, f". {remote_root}/board.env && {remote_root}/run_morning_board.sh {remote_root}", timeout=60.0)
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if code != 0:
                raise RuntimeError("Immediate morning board run failed.")

        if args.install_normal_screensavers:
            code, out, err = exec_command(
                client,
                f". {remote_root}/board.env && {remote_root}/install_normal_screensavers.sh {remote_root} {remote_root}/normal-screensavers",
                timeout=60.0,
            )
            sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if code != 0:
                raise RuntimeError("Normal screensaver install failed.")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

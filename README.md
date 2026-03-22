# Kindle Family Board

This repository turns a jailbroken Kindle 4 into a daily family board.

Current behavior:

- The board is rendered in French.
- Weather defaults to Wassenaar, NL (configurable).
- The reading block comes from a local carousel of jokes and fun facts.
- The visual style uses `burst` corner icons.
- GitHub Pages hosts the daily board as both `latest.png` and immutable dated files like `board-YYYY-MM-DD.png`.
- At `07:00`, the Kindle wakes and shows the board.
- During the morning hold window, the board remains visible even after auto-sleep.
- After the hold window, the Kindle switches back to a curated family photo screensaver set.
- When the user later presses the power button for sleep, the Kindle stays on a real photo instead of falling back to a white screen.
- KUAL exposes a manual `Family Board` action that fetches and displays today's board on demand.

The timed wake path, the board-on-sleep path, the restore-to-photos path, the later manual sleep path, and the manual KUAL fetch path have all been live-tested on the actual device.

## Architecture

The implementation is intentionally split in two:

- Off-device Python renders the board and publishes `latest.png`, `latest.json`, and dated assets.
- The Kindle only downloads, displays, persists, and later restores screensavers.

That keeps the Kindle-side logic small and gives the host side full freedom for layout, weather formatting, and reading-content curation.

## Repository Layout

- [README.md](README.md): operational overview
- [ORCHESTRATOR.md](ORCHESTRATOR.md): durable living memory for future orchestrator work
- [docs/design-plan.md](docs/design-plan.md): architecture and validation notes
- [docs/stories.txt](docs/stories.txt): original stories source for the carousel
- [scripts/generate_board.py](scripts/generate_board.py): renders `output/latest.png`
- [scripts/build_site.py](scripts/build_site.py): builds the static `site/` output
- [scripts/publish_gh_pages.py](scripts/publish_gh_pages.py): manual Pages publish helper
- [scripts/deploy_to_kindle.py](scripts/deploy_to_kindle.py): uploads Kindle scripts and optional screensaver assets
- [scripts/test_restore_cycle.py](scripts/test_restore_cycle.py): short compressed end-to-end restore test
- [scripts/process_download_screensavers.py](scripts/process_download_screensavers.py): converts hand-picked family photos into `600x800` grayscale Kindle screensavers
- [kindle/run_morning_board.sh](kindle/run_morning_board.sh): morning orchestrator on the Kindle
- [kindle/restore_after_delay.sh](kindle/restore_after_delay.sh): delayed restore logic
- [kindle/restore_screensavers.sh](kindle/restore_screensavers.sh): restores the normal screensaver set
- [kindle/install_normal_screensavers.sh](kindle/install_normal_screensavers.sh): makes the curated photo set canonical on the Kindle
- [kindle/boot_reseed.sh](kindle/boot_reseed.sh): re-installs the Kindle cron entry after reboot
- [kindle/linkss_emergency.sh](kindle/linkss_emergency.sh): hooks the `linkss` emergency path so cron re-seeding happens automatically at boot
- [kindle/familyboard_kual.sh](kindle/familyboard_kual.sh): manual KUAL launcher for today's board
- [data/kind_messages.txt](data/kind_messages.txt): family aphorisms and sweet messages
- [data/easy_words.txt](data/easy_words.txt): reading words for the younger child
- [data/reading_carousel.md](data/reading_carousel.md): rotating jokes and fun facts for the older child

## Current Defaults

- `KFB_LOCATION_NAME=Wassenaar`
- `KFB_LATITUDE=52.1450`
- `KFB_LONGITUDE=4.4028`
- `KFB_TIMEZONE=Europe/Amsterdam`
- `KFB_ICON_STYLE=burst`
- `KFB_MORNING_HOLD_SECONDS=10800`
- `KFB_BOARD_URL=https://<your-username>.github.io/kindle-family-board/latest.png`

The scheduler/runtime path on the Kindle uses the project timezone explicitly. The raw shell `date` output on the device can still look UTC-like unless the project timezone is forced, but the morning scheduler path is the reliable one.

The board content is French-first. The weather block shows only morning and afternoon icon, temperature, and rain chance.

## Quick Start

1. Create a virtual environment and install the package.
2. Review [`.env`](.env) if you want to override location, host, or board URL.
3. Generate the board once:

```bash
python scripts/generate_board.py
```

Output lands in:

- [output/latest.png](output/latest.png)
- [output/latest.json](output/latest.json)
- `output/board-YYYY-MM-DD.png`
- `output/board-YYYY-MM-DD.json`

## Publish Path

The primary hosting path is GitHub Pages.

- [publish-board.yml](.github/workflows/publish-board.yml) runs four times per hour in a morning-relevant UTC window
- The workflow republishes only during the local morning window in `Europe/Amsterdam` and skips once `latest.json` is already current for the day
- The stable image URLs are `https://<your-username>.github.io/kindle-family-board/latest.png` and `https://<your-username>.github.io/kindle-family-board/board-YYYY-MM-DD.png`

Manual publish fallback:

```bash
python scripts/publish_gh_pages.py
```

Local LAN serving still exists in [scripts/serve_output.py](scripts/serve_output.py), but it is now a fallback, not the normal production path.

## Kindle Deployment

Deploy the Kindle scripts, install the daily cron entry, install the reboot self-heal hook, and upload the canonical family photo screensaver set:

```bash
python scripts/deploy_to_kindle.py --install-cron --install-self-heal --upload-normal-screensavers --install-normal-screensavers
```

If the Kindle usually sits on a stable IP such as `192.168.2.30`, prefer:

```bash
python scripts/deploy_to_kindle.py --host 192.168.2.30 --install-cron --install-self-heal --upload-normal-screensavers --install-normal-screensavers
```

Immediate morning-flow test:

```bash
python scripts/deploy_to_kindle.py --host 192.168.2.30 --run-morning-now
```

Compressed restore-cycle test:

```bash
python scripts/test_restore_cycle.py --host 192.168.2.30 --hold-seconds 60 --force-sleep-after 20
```

## Morning Lifecycle

The production flow is:

1. GitHub Pages publishes the daily board image.
2. The Kindle cron entry in `/etc/crontab/root` runs [kindle/run_morning_board.sh](kindle/run_morning_board.sh) at `07:00`.
3. `run_morning_board.sh` downloads the dated board image for the expected day, displays it, then arms the board screensaver watchdog.
4. During the hold window, the Kindle may auto-sleep, but the board is repainted onto the screensaver event so it remains visible.
5. After `KFB_MORNING_HOLD_SECONDS`, [kindle/restore_after_delay.sh](kindle/restore_after_delay.sh) calls [kindle/restore_screensavers.sh](kindle/restore_screensavers.sh).
6. The restore path re-installs the canonical photo set from `/mnt/us/kindle-family-board/normal-screensavers`, reinitializes `linkss`, resets the framework, and triggers a one-shot repaint so the visible sleeping cover becomes a family photo again.
7. The KUAL menu entry calls the same board fetch/display runtime, but runs it in the background so KUAL does not repaint over the board.

This is deliberate: the project no longer trusts whatever files happen to be in `linkss/screensavers`. The canonical normal screensaver set lives under the project root on the Kindle.

## Reboot Self-Heal

Kindle cron state is not durable enough to trust blindly after reboot, so the repo installs a self-healing path:

- [kindle/boot_reseed.sh](kindle/boot_reseed.sh) rewrites `/etc/crontab/root`
- [kindle/linkss_emergency.sh](kindle/linkss_emergency.sh) runs through the `linkss` emergency hook and calls `boot_reseed.sh`
- [kindle/familyboard_kual.sh](kindle/familyboard_kual.sh) is the manual KUAL entrypoint for today's board and delays its redraw so the menu closes first

In practice, that means the `07:00` cron job gets re-seeded automatically after boot.

## Family Photo Screensavers

The current normal screensaver set is derived from manually chosen photos.

Local source of truth:

- [output/new-screensavers](output/new-screensavers)
- `~/Downloads/kindle-screensavers-600x800`

The processing helper is:

```bash
python scripts/process_download_screensavers.py
```

That script is intentionally manual: it contains crop presets for the current source photos. If you swap to a new photo set, update the crop boxes in [scripts/process_download_screensavers.py](scripts/process_download_screensavers.py) and redeploy.

## SSH and Device Access

For maintenance, the Kindle is easiest to manage over Wi-Fi SSH.

Recommended Kindle-side setting:

- `Restrict SSH to WiFi, stay in USBMS`: enabled

When you need shell access:

1. Wake the Kindle.
2. Make sure Wi-Fi is connected.
3. In `KUAL > USBNetwork`, toggle until the status says `enabled (usbnet, sshd up)`.

The helper scans the whole local `/24`, not just low addresses. If your Kindle has a stable lease, set `KFB_KINDLE_HOST` in [`.env`](.env).

## Notes

- The board is always rendered at `600x800`.
- The reading card comes from a local carousel of curated French jokes and fun facts.
- The carousel is shuffled by cycle and avoids showing the same reading twice in a row, even when it starts a new loop.
- The family message and the younger child words are pseudo-random by date: stable for a given day, varied across days.
- The exact timed wake has been proven on this Kindle, and the manual power-button sleep path now returns a real photo instead of a white screen.
- The manual KUAL fetch action is now proven too; it stays on the board instead of bouncing back to KUAL.
- Long multi-day battery endurance is still an operational question. If you want maximum reliability, keep it charged.
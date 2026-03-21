# Kindle Family Board Orchestrator Memory

This file is the durable fallback memory for future orchestrator and subagent work on this repo.

The thread remains the source of truth. If the thread and this file ever disagree, trust the thread first, then update this file when you are allowed to modify files.

## Purpose

This repository turns a jailbroken Kindle 4 into a family morning board.

The board is not a general dashboard. It is a deliberately narrow, low-noise surface with four user-facing sections:

- weather for Wassenaar, NL
- a family message
- two easy reading words for the younger child
- one rotating joke or fun fact for the older child

The board is French-first, optimized for 600x800 e-ink, and designed to stay legible and calm when the Kindle sleeps.

## Current User-Facing Behavior

Current production behavior is:

- at 07:00 local time, the Kindle wakes and shows the board
- if the Kindle auto-sleeps during the morning window, the board remains visible as the sleeping cover
- after the morning hold window, the Kindle switches back to a curated family photo screensaver set
- the Kindle now fetches the immutable dated board asset for the expected day, not a mutable `latest.png` alias

The stale-board root cause was dependence on `latest.png`. The Kindle now requests `board-YYYY-MM-DD.png` for the expected render date, and the manifest exposes dated board metadata so that fetch is explicit.

As of the current state of the repo, these behaviors have been live-tested on the actual device.

## High-Level Architecture

The system is split into three layers.

### 1. Host-side Python

Host-side Python generates the board image and manifest.

Responsibilities:

- fetch weather
- choose French family copy
- choose reading content
- render the final board image
- write `latest.png`, `latest.json`, and dated copies in `output/`
- expose dated board metadata in the manifest so the Kindle can request `board-YYYY-MM-DD.png` directly

Primary output files:

- [C:\Users\aabec\Scripts\kindle-family-board\output\latest.png](C:\Users\aabec\Scripts\kindle-family-board\output\latest.png)
- [C:\Users\aabec\Scripts\kindle-family-board\output\latest.json](C:\Users\aabec\Scripts\kindle-family-board\output\latest.json)
- [C:\Users\aabec\Scripts\kindle-family-board\output\board-YYYY-MM-DD.png](C:\Users\aabec\Scripts\kindle-family-board\output)
- [C:\Users\aabec\Scripts\kindle-family-board\output\board-YYYY-MM-DD.json](C:\Users\aabec\Scripts\kindle-family-board\output)

### 2. GitHub Pages publishing

GitHub Pages is the normal production host for the board image.

Responsibilities:

- publish the current daily board
- keep the board available without a local LAN server
- provide a stable URL the Kindle can fetch

Stable public URLs:

- [https://aabk6.github.io/kindle-family-board/latest.png](https://aabk6.github.io/kindle-family-board/latest.png)
- [https://aabk6.github.io/kindle-family-board/board-YYYY-MM-DD.png](https://aabk6.github.io/kindle-family-board/board-YYYY-MM-DD.png)

### 3. Kindle-side shell runtime

The Kindle runs a small shell-based runtime that:

- wakes the device on schedule
- downloads the immutable dated board image for the expected render date
- displays the image
- keeps the board visible through sleep during the morning window
- restores the normal photo screensaver set after the hold window
- reseeds cron after reboot

The Kindle runtime is intentionally small. The fragile logic lives mostly in shell scripts under `kindle/`.

## Repo Map

### Python package

- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\config.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\config.py): environment-backed config and defaults
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\models.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\models.py): dataclasses for weather, reading, and board content
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\content.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\content.py): family messages, practice words, and reading carousel selection
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\weather.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\weather.py): Open-Meteo fetch and weather interpretation
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\pipeline.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\pipeline.py): content assembly, manifest writing, and dated board metadata
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\render.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\render.py): all visual layout, typography, cards, badges, and icons
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\kindle.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\kindle.py): SSH discovery and command execution against the Kindle
- [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\runtime.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\runtime.py): repo env loading and local server helpers

### Scripts

- [C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py): local board generation entry point
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\build_site.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\build_site.py): static site build
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\publish_gh_pages.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\publish_gh_pages.py): manual GitHub Pages publish helper
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\deploy_to_kindle.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\deploy_to_kindle.py): Kindle deploy and runtime bootstrap
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\test_restore_cycle.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\test_restore_cycle.py): compressed live-device restore test
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\process_download_screensavers.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\process_download_screensavers.py): crop and convert family photos into Kindle screensavers
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\serve_output.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\serve_output.py): local fallback LAN server
- [C:\Users\aabec\Scripts\kindle-family-board\scripts\install_windows_tasks.ps1](C:\Users\aabec\Scripts\kindle-family-board\scripts\install_windows_tasks.ps1): optional host automation

### Kindle shell runtime

- [C:\Users\aabec\Scripts\kindle-family-board\kindle\run_morning_board.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\run_morning_board.sh): morning orchestrator
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\fetch_and_display.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\fetch_and_display.sh): download and display the board
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\daily_wake_scheduler.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\daily_wake_scheduler.sh): persistent wake daemon
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\one_shot_wake_test.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\one_shot_wake_test.sh): one-shot wake/display helper
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_after_delay.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_after_delay.sh): delayed restore worker
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_screensavers.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_screensavers.sh): restore normal screensavers and repaint them
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\install_normal_screensavers.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\install_normal_screensavers.sh): install canonical photo set
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\boot_reseed.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\boot_reseed.sh): rewrite cron after reboot and restart the wake daemon
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\linkss_emergency.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\linkss_emergency.sh): `linkss` emergency hook that triggers boot reseeding
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\board_screensaver_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\board_screensaver_watchdog.sh): keeps the board visible during the morning window
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\start_board_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\start_board_watchdog.sh)
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_board_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_board_watchdog.sh)
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\persist_morning_screensaver.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\persist_morning_screensaver.sh)
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_restore_after_delay.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_restore_after_delay.sh)
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_daily_wake_scheduler.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_daily_wake_scheduler.sh)
- [C:\Users\aabec\Scripts\kindle-family-board\kindle\start_daily_wake_scheduler.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\start_daily_wake_scheduler.sh)

## End-to-End Flows

### Board generation flow

1. Load env and config from the repo root.
2. Fetch weather from Open-Meteo.
3. Pick French family text content.
4. Pick reading content from the local carousel.
5. Render `600x800` board image.
6. Write `latest.png`, `latest.json`, and dated copies.
7. Emit dated board metadata in the manifest so the Kindle can request the immutable asset for the expected day.

The relevant entry point is:

- [C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py)

### Publish flow

GitHub Actions is the main publication path.

Typical flow:

1. A workflow runs on a schedule.
2. It builds or refreshes the board.
3. It publishes the result to GitHub Pages.
4. The Kindle fetches the dated board URL for the expected day.

Important point: the workflow is intentionally tolerant of morning timing drift. The lesson from the history is that an exact one-minute window is too brittle.

The schedule was narrowed from all-day runs to a morning-relevant UTC window, while the workflow still filters by local hour and skips once the current day is already published.

### Kindle morning flow

The Kindle morning flow is the core runtime:

1. Cron triggers `run_morning_board.sh` at 07:00.
2. `run_morning_board.sh` calls `fetch_and_display.sh`.
3. The board is cached locally in `/mnt/us/kindle-family-board/cache/latest.png`.
4. The board is displayed with `eips`.
5. The board screensaver watchdog is started.
6. A delayed restore worker is armed for the morning hold window.

During the hold window, the board must survive a normal sleep transition.

### Morning restore flow

When the hold window expires:

1. `restore_after_delay.sh` wakes or waits for the correct time.
2. It calls `restore_screensavers.sh`.
3. The normal photo screensaver set is reinstalled from the canonical directory.
4. The chosen photo is copied into the repaint cache.
5. A one-shot repaint makes the sleeping cover become a family photo again.
6. The restore handoff now reinitializes the normal `linkss` runtime and resets the framework so later manual sleep still shows a photo instead of a white screen.

## Configuration and Env Conventions

The main config object is [C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\config.py](C:\Users\aabec\Scripts\kindle-family-board\src\kindle_family_board\config.py).

Important env vars and defaults:

- `KFB_LOCATION_NAME=Wassenaar`
- `KFB_LATITUDE=52.1450`
- `KFB_LONGITUDE=4.4028`
- `KFB_TIMEZONE=Europe/Amsterdam`
- `KFB_ICON_STYLE=burst`
- `KFB_WEATHER_ICON_STYLE=classic`
- `KFB_MORNING_HOLD_SECONDS=10800`
- `KFB_BOARD_URL=https://aabk6.github.io/kindle-family-board/latest.png`

Other notable runtime env vars:

- `KFB_KINDLE_HOST`
- `KFB_KINDLE_USER`
- `KFB_KINDLE_SERIAL`
- `KFB_SSH_KEY_PATH`
- `KFB_KINDLE_HOST_CACHE`
- `KFB_FETCH_RETRY_COUNT`
- `KFB_FETCH_RETRY_DELAY`
- `KFB_WAKE_TARGET_HOUR`
- `KFB_WAKE_TARGET_MINUTE`
- `KFB_WAKE_POST_RUN_COOLDOWN`
- `KFB_NORMAL_SCREENSAVER_DIR`
- `KFB_LINKSS_DIR`
- `KFB_LINKSS_ACTIVE_DIR`

Kindle deploy writes these into `board.env`:

- `BOARD_URL`
- `CACHE_DIR`
- `KFB_MORNING_HOLD_SECONDS`
- `KFB_LINKSS_SCREENSAVER_NAME`
- `KFB_NORMAL_SCREENSAVER_DIR`
- `KFB_WAKE_TARGET_HOUR`
- `KFB_WAKE_TARGET_MINUTE`
- `CURL_BIN=/mnt/us/usbnet/bin/curl`
- `EIPS_BIN=/usr/sbin/eips`

## Content Sources and Product Decisions

These are the current content and product decisions that matter.

- The board copy is French-first.
- The weather location is Wassenaar, NL, not a generic city.
- The reading card is a local carousel of jokes and fun facts, not live AI generation.
- The family message is pseudo-random by date, but stable for a given day.
- The younger-child words are pseudo-random by date, but stable for a given day.
- The reading carousel advances through a shuffled cycle and avoids immediate repetition at cycle boundaries.
- The visual card badges are hand-drawn illustrated corner badges.
- The morning board should feel like a designed object, not a dashboard.
- The canonical normal screensavers are four curated family photos, not the Kindle default images.
- The current steady-state restore path normalizes the restored PNGs to PNG8 colormap, reinitializes `linkss`, and resets the framework after restore.
- The Kindle now fetches immutable dated board assets for the expected day instead of depending on the mutable `latest.png` alias.

Current content files:

- [C:\Users\aabec\Scripts\kindle-family-board\data\kind_messages.txt](C:\Users\aabec\Scripts\kindle-family-board\data\kind_messages.txt)
- [C:\Users\aabec\Scripts\kindle-family-board\data\easy_words.txt](C:\Users\aabec\Scripts\kindle-family-board\data\easy_words.txt)
- [C:\Users\aabec\Scripts\kindle-family-board\data\reading_carousel.md](C:\Users\aabec\Scripts\kindle-family-board\data\reading_carousel.md)

Current photo sources:

- [C:\Users\aabec\Scripts\kindle-family-board\output\new-screensavers](C:\Users\aabec\Scripts\kindle-family-board\output\new-screensavers)
- [C:\Users\aabec\Scripts\kindle-family-board\output\kindle-screensavers](C:\Users\aabec\Scripts\kindle-family-board\output\kindle-screensavers)

## Operational Runbook

When the morning board fails, inspect in order.

### 1. Wake scheduling

First check whether the Kindle was actually armed to wake.

Look at:

- `/mnt/us/kindle-family-board/cache/daily-wake.log`
- `/mnt/us/kindle-family-board/cache/wake-test.log`
- `/mnt/us/kindle-family-board/cache/boot.log`

Questions to answer:

- Did the daily wake daemon start?
- Did it compute the next target time?
- Did it arm the one-shot wake helper?
- Did `boot_reseed.sh` run after the last reboot?

### 2. Freshness and fetch

If the Kindle woke but showed an old board, inspect freshness before assuming the Kindle is broken.

Look at:

- `/mnt/us/kindle-family-board/cache/refresh.log`
- GitHub Actions run history for the publish workflow
- the current `latest.json` on GitHub Pages

Questions to answer:

- Did the board publish for today?
- Did `latest.json` show today's render date?
- Did `fetch_and_display.sh` fetch the dated board asset for the expected day, or did it fall back to cache?
- Was DNS ready at wake time?

### 3. Sleep persistence

If the board appears, but disappears on sleep, inspect the board watchdog.

Look at:

- `/mnt/us/kindle-family-board/cache/morning.log`
- `/mnt/us/kindle-family-board/cache/board-ss-watchdog.log`
- `/mnt/us/kindle-family-board/cache/linkss.log`

Questions to answer:

- Did the board watchdog start?
- Did it react to `goingToScreenSaver`?
- Did it repaint the board after the framework drew the screen saver?

### 4. Restore to photos

If the morning board stays up but never returns to photos, inspect the restore worker.

Look at:

- `/mnt/us/kindle-family-board/cache/restore.log`
- `/mnt/us/kindle-family-board/cache/one-shot-screensaver.log`
- `/mnt/us/kindle-family-board/cache/linkss.log`

Questions to answer:

- Did the delayed restore worker start?
- Did its token still match?
- Did it call `restore_screensavers.sh`?
- Did it repaint a real photo, not the board?

### 5. Host-side maintenance

If the Kindle is unreachable from the host, inspect connectivity before touching the Kindle scripts.

Look at:

- host Wi-Fi
- `USBNetwork` status on the Kindle
- cached host path in [C:\Users\aabec\OneDrive\Documents\Playground\kindle_fix\last_host.txt](C:\Users\aabec\OneDrive\Documents\Playground\kindle_fix\last_host.txt)
- `KFB_KINDLE_HOST` in `.env`

Questions to answer:

- Is the Kindle awake?
- Is Wi-Fi on?
- Is `USBNetwork` enabled?
- Does SSH still answer on port 22?

## Fragile and Non-Obvious Contracts

This repo has several hidden contracts. Treat them as part of the system.

- Cron alone does not wake the Kindle. The daily wake daemon is required.
- The boot reseed hook is required because Kindle cron state is not trusted across reboot.
- `cache/latest.png` has two meanings over the day:
  - morning board cache
  - repaint source for restored screensavers
- The normal screensaver set is canonical only if it came from `normal-screensavers/`.
- `linkss/screensavers` is not a source of truth. It is a deploy target.
- `fetch_and_display.sh` assumes `curl` exists at `/mnt/us/usbnet/bin/curl`.
- `fetch_and_display.sh` assumes `eips` exists at `/usr/sbin/eips`.
- `restore_after_delay.sh` and `one_shot_wake_test.sh` use `lipc-wait-event`, `lipc-set-prop`, `powerd_test`, and `rtcWakeup`.
- The Kindle host discovery logic scans the local `/24` and can fail if the Kindle is on a different subnet or the cached host is stale.
- The GitHub Pages workflow is intentionally tolerant of schedule drift. Exact minute alignment is not reliable enough.
- The morning fetch path now depends on dated assets, not on a mutable `latest.png` alias.
- Visual work is concentrated in one file, `render.py`, so even small badge or spacing changes can move a lot of layout.
- The morning restore path depends on `linkss` being present and the Kindle framework being reset after restore for the steady-state screensaver path to remain healthy.

## Testing and Verification Patterns

This repo does not have a meaningful unit-test suite for the Kindle runtime.

Real verification patterns are operational:

- run [generate_board.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py) locally and inspect `latest.png`
- run [build_site.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\build_site.py) and inspect the static site output
- run [publish_gh_pages.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\publish_gh_pages.py) for manual Pages checks
- use [test_restore_cycle.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\test_restore_cycle.py) for compressed live-device restore checks
- use [arm_wake_test.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\arm_wake_test.py) for timed wake experiments
- inspect Kindle logs in `cache/*.log`
- confirm the visible screen on the actual Kindle

What counts as a good test:

- wake happened at the right time
- the board downloaded fresh content
- the board displayed correctly
- the board survived sleep during the morning window
- restore switched the sleeping cover back to a real photo
- later manual power-button sleep still shows a photo, not a white screen

What does not count as sufficient:

- only checking a PNG on the host
- only checking one log line
- only checking `git diff`

## Git and History Lessons

The history is useful because it shows where the project has been fragile.

Recent important themes:

- `bab13ed`: locked the board to French and Wassenaar
- `ce47ed4`: replaced live AI reading generation with the local carousel
- `cb39c66`: introduced the canonical normal screensaver pipeline
- `179003d`: fixed daily wake scheduling and publish freshness
- `999e6ec`: introduced deterministic carousel behavior and one-shot photo restore
- `6cf0863`, `ca21dc8`, `3e050c8`, `e6afa02`: repeated fixes around restore semantics, watchdog timing, and repaint source selection
- `latest.png` became a compatibility alias only; the Kindle now uses immutable dated board assets for the actual wake fetch
- `0546d0b`, `267a8c4`, `180bee9`: ongoing badge and icon visual tuning

Lesson from the history:

- the fragile parts are wake timing, repaint timing, restore state, and mutable asset aliases
- visual generation is much less risky than Kindle runtime state management
- freshness bugs often come from the host publish path or aliasing, not from the Kindle scripts themselves

## Conventions For Future Subagents

When you assign work to another agent, be precise.

Always define:

- the goal
- the files it owns
- the files it must not touch
- the conventions to follow
- the verification steps

Recommended ownership style:

- one agent, one narrow subsystem
- avoid overlapping file ownership
- if a task touches both host and Kindle runtime, split it only if the interfaces are clear

Best practice for task prompts:

- say exactly what behavior must change
- say which logs or images prove success
- say whether the agent may touch `render.py`, Kindle scripts, workflow files, or docs
- say whether the task is allowed to change content files

What future subagents should verify:

- if they changed Kindle scripts, they must confirm `deploy_to_kindle.py` still uploads and chmods every new script
- if they changed visual layout, they must render and inspect `latest.png`
- if they changed wake or restore flow, they must verify on the live device or through a compressed restore-cycle test
- if they changed publish logic, they must confirm `latest.json` freshness and GitHub Pages output
- if they changed the morning fetch path, they must verify the dated board URL, not just `latest.png`

What future subagents should avoid:

- do not touch unrelated files
- do not revert user changes
- do not assume the Kindle default screensavers are the intended canonical set
- do not trust `linkss/screensavers` without checking the canonical source

## Current External Assumptions

The repo depends on several things outside the codebase.

- Wi-Fi SSH on the Kindle must work for maintenance.
- `USBNetwork` must be enabled when host SSH maintenance is needed.
- `linkss` must be installed on the Kindle for the screen saver workflow.
- `/mnt/us/usbnet/bin/curl` must exist on the Kindle.
- `/usr/sbin/eips` must exist on the Kindle.
- `paramiko`, `requests`, `Pillow`, `python-dotenv`, and `tzdata` must be installed in the host environment.
- GitHub Pages must remain available at the stable public URL.
- The Kindle should have enough battery or power to survive the morning window.

## Working Rule

This thread is the source of truth for ongoing decisions.

This file is the durable fallback memory when the thread is compacted or lost.

If you learn something important about architecture, conventions, fragile contracts, or verified behavior, update this file when allowed. Keep it current. Treat it as a living operating manual, not a static note.

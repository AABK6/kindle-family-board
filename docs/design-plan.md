# Design Plan

## Goal

At `07:00` each morning, the Kindle should wake and show a family board that feels designed for e-ink, not like a terminal screenshot.

The current board shows:

- weather for Wassenaar, NL
- a warm family message
- two easy reading words for the 6-year-old
- one short joke for the 9-year-old

The board copy is French-first and the layout is optimized for `600x800`.

## Implemented architecture

### 1. Board generation off-device

A normal Python environment generates:

- `latest.png`: the final board image
- `latest.json`: the manifest of the exact content used

The generator:

1. fetches Open-Meteo weather
2. picks a pseudo-random family aphorism for the day
3. picks two pseudo-random reading words for the day
4. asks Gemini for a short French joke, with local fallback jokes if Gemini is unavailable

This keeps weather formatting, typography, and LLM usage off the Kindle.

### 2. GitHub Pages as the production host

The primary hosting path is:

- hourly GitHub Actions schedule
- local-hour gate at `07` in `Europe/Amsterdam`
- deploy to GitHub Pages

Stable output URL:

- [latest.png](https://aabk6.github.io/kindle-family-board/latest.png)

This means the Kindle only needs a stable URL. The PC no longer needs to act as the normal morning web server.

### 3. Kindle-side morning orchestrator

The Kindle runs:

- cron entry at `07:00`
- [run_morning_board.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\run_morning_board.sh)

That script:

1. downloads `latest.png`
2. displays it with `eips`
3. arms a board screensaver watchdog
4. arms a delayed restore job

The delayed restore window is controlled by `KFB_MORNING_HOLD_SECONDS`, currently `10800` seconds.

### 4. Board persistence during sleep

The core morning UX requirement is:

- if the Kindle auto-sleeps during the morning window, the board must remain visible

That is handled by:

- [board_screensaver_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\board_screensaver_watchdog.sh)
- [start_board_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\start_board_watchdog.sh)
- [stop_board_watchdog.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\stop_board_watchdog.sh)

The watchdog listens for `goingToScreenSaver` and redraws the board after the framework paints.

### 5. Post-morning restore to family photos

The project now uses an explicit canonical normal screensaver set.

On the Kindle, that set lives at:

- `/mnt/us/kindle-family-board/normal-screensavers`

The restore path is:

1. stop the board watchdog
2. re-install the canonical photo set into `linkss/screensavers`
3. copy the chosen photo into the project cache
4. repaint the visible sleeping cover so the user sees a family photo again

Relevant scripts:

- [restore_after_delay.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_after_delay.sh)
- [restore_screensavers.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\restore_screensavers.sh)
- [install_normal_screensavers.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\install_normal_screensavers.sh)
- [one_shot_screensaver_refresh.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\one_shot_screensaver_refresh.sh)

This replaced the older, fragile assumption that the “normal” screensaver set could be inferred from whatever happened to be sitting inside `linkss/screensavers`.

## Canonical family photo pipeline

The current photo screensaver set is hand-curated.

Workflow:

1. put source photos in `Downloads`
2. manually tune crop boxes in [process_download_screensavers.py](C:\Users\aabec\Scripts\kindle-family-board\scripts\process_download_screensavers.py)
3. render `600x800` grayscale outputs
4. upload them to the Kindle as the canonical normal screensaver set

Local outputs:

- [output/new-screensavers](C:\Users\aabec\Scripts\kindle-family-board\output\new-screensavers)
- [C:\Users\aabec\Downloads\kindle-screensavers-600x800](C:\Users\aabec\Downloads\kindle-screensavers-600x800)

This is intentionally not a generic automatic cropper. The current script contains crop presets for the current four family images.

## Reboot self-heal

Cron needs extra care on this Kindle 4.

The repo therefore installs:

- [boot_reseed.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\boot_reseed.sh)
- [linkss_emergency.sh](C:\Users\aabec\Scripts\kindle-family-board\kindle\linkss_emergency.sh)

That gives the project a practical self-healing boot path:

- after reboot, the `linkss` emergency hook runs
- the hook re-seeds `/etc/crontab/root`
- the `07:00` morning cron entry is restored

## Validation status on the live device

Verified on the actual Kindle as of March 18, 2026:

- Wi-Fi SSH works for maintenance
- the Kindle can wake on a timed test while unplugged
- the board can display on wake
- the board remains visible after auto-sleep during the morning hold window
- the restore path can return the sleeping cover to the family photo set

The restore behavior was verified with the production path compressed to a `60` second hold:

- board launched
- forced sleep occurred
- delayed restore fired
- sleeping cover switched from board to family photo

## Operational caveats

Things that are proven:

- timed wake can happen
- morning board rendering works
- board persistence across sleep works
- restore to photo screensavers works

Things still treated cautiously:

- true long-duration battery endurance over many days is not yet characterized
- SSH is only available when `USBNetwork` is enabled and the Kindle is awake or Wi-Fi-active
- the live validation for restore used a compressed hold window rather than literally waiting 3 hours each time

That said, the compressed test uses the same production scripts and code path, so it is a meaningful validation.

## Practical recommendation

Operationally, the system is now in a good state for daily use:

- keep Wi-Fi on
- keep the device reasonably charged
- leave `USBNetwork` off unless maintenance is needed
- treat the canonical family photo set under the project root as the only source of truth for “normal” screensavers

If the photo set changes, regenerate it locally and redeploy it. Do not hand-edit `linkss/screensavers` on the device and assume the project can infer the intended baseline.

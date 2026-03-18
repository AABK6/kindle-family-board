# Kindle Family Board

This repo turns a jailbroken Kindle into a daily e-ink family board.

The current implementation is built around a hybrid model:

- a host-side Python job generates a 600x800 PNG and a JSON manifest
- the Kindle fetches that PNG over Wi-Fi and displays it with `eips`
- Gemini writes the short reading block for the 9-year-old
- a local rotating file provides kind morning messages
- a local word bank provides two simple practice words for the 6-year-old
- repo-local scripts now handle generation, serving, and Kindle deployment

## Why this shape

It is the fastest path to something that will actually hold up:

- rendering stays easy and flexible on a normal machine
- the Kindle only has to download and show one image
- Gemini can run off-device, with clean fallbacks when it fails
- the Kindle 4 wake-at-7:00 story is still uncertain when unplugged, so the repo keeps scheduling and content generation decoupled

## Repo layout

- [`docs/design-plan.md`](C:\Users\aabec\Scripts\kindle-family-board\docs\design-plan.md): the concrete architecture and unplugged analysis
- [`scripts/generate_board.py`](C:\Users\aabec\Scripts\kindle-family-board\scripts\generate_board.py): host-side board generator
- [`kindle/fetch_and_display.sh`](C:\Users\aabec\Scripts\kindle-family-board\kindle\fetch_and_display.sh): Kindle-side pull and render script
- [`kindle/install_cron.sh`](C:\Users\aabec\Scripts\kindle-family-board\kindle\install_cron.sh): installs a daily Kindle cron entry
- [`data/kind_messages.txt`](C:\Users\aabec\Scripts\kindle-family-board\data\kind_messages.txt): rotating sweet messages
- [`data/easy_words.txt`](C:\Users\aabec\Scripts\kindle-family-board\data\easy_words.txt): practice words
- [`data/fallback_readings.json`](C:\Users\aabec\Scripts\kindle-family-board\data\fallback_readings.json): local fallback stories and jokes

## Quick start

1. Create a venv and install the package.
2. Review [`.env`](C:\Users\aabec\Scripts\kindle-family-board\.env) and adjust location values if Berlin is not correct.
3. Keep `GEMINI_API_KEY` in your shell environment, or add it to `.env`.
4. Run:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/generate_board.py
```

The output lands in `output/latest.png` and `output/latest.json`.

## Operational commands

Generate the board once:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/generate_board.py
```

Serve the `output/` folder on your local network:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/serve_output.py --generate-first
```

Build a static `site/` folder for GitHub Pages:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/build_site.py
```

Deploy the Kindle-side scripts and install the daily 07:00 cron job:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/deploy_to_kindle.py --install-cron --run-now
```

For the first on-device test, use direct image upload instead of HTTP fetch:

```bash
C:\Users\aabec\Scripts\kindle-family-board\.venv\Scripts\python scripts/deploy_to_kindle.py --upload-current-image
```

The deploy command assumes:

- the Kindle is awake
- Wi-Fi is on
- `USBNetwork` is toggled on
- `Restrict SSH to WiFi, stay in USBMS` is enabled

If auto-discovery misses it, add `--host <kindle-ip>`.

## Hosting options

### Local machine

Run `scripts/serve_output.py --generate-first` on a machine that stays on at breakfast time. The Kindle can then fetch `latest.png` from your LAN.

### GitHub Pages

The repo includes [`.github/workflows/publish-board.yml`](C:\Users\aabec\Scripts\kindle-family-board\.github\workflows\publish-board.yml). Once you push this repo to GitHub and enable Pages from Actions:

- add `GEMINI_API_KEY` as a repository secret
- add `KFB_LOCATION_NAME`, `KFB_LATITUDE`, `KFB_LONGITUDE`, `KFB_TIMEZONE`, and optionally `KFB_BOARD_URL` as repository variables
- the workflow runs hourly and only publishes during the 07:00 Berlin hour

This is the cleaner path if you do not want a local PC serving files every morning.

## Recommended rollout

1. Start with host-side generation only and review the PNG.
2. Serve the PNG from a static URL or your local machine with `scripts/serve_output.py`.
3. Deploy the Kindle scripts with `scripts/deploy_to_kindle.py`.
4. Test a manual refresh on the Kindle.
5. Only after that, test daily scheduling on-device.
6. Treat unplugged timed wake as a phase-2 experiment, not a base assumption.

## Notes

- The canvas is already sized for Kindle 4: `600x800`.
- If Gemini is unavailable, the generator falls back to local jokes and micro-stories.
- The daily message and words are deterministic by date, so the content rotates cleanly without needing a database.

# Design Plan

## Goal

At 07:00 each morning, the Kindle should show:

- weather
- a warm family greeting
- two easy reading words for the 6-year-old
- a very short joke or micro-story for the 9-year-old

The output should look intentional on e-ink, not like a terminal dump.

## Recommended architecture

### 1. Host-side generator

A normal machine or cloud job generates:

- `latest.png`: the rendered 600x800 dashboard
- `latest.json`: the manifest with the exact content used that day

The generator does four things:

1. fetches weather from Open-Meteo
2. selects a rotating message from a local list
3. selects two rotating easy words from a local word bank
4. asks Gemini for one short reading block, with local fallback content if Gemini fails

### 2. Kindle-side fetch and display

The Kindle should do as little work as possible:

1. download `latest.png`
2. keep the previous image if the network fetch fails
3. display the image with `eips -f -g`

That keeps the Kindle logic short and debuggable.

### 3. Scheduling choices

There are three realistic scheduling modes.

#### Mode A: plugged in, Kindle-side daily cron

This is the safest v1.

- the Kindle stays on power
- `crond` runs on the device
- a daily job fetches and shows the image at 07:00

Pros:

- simple
- few moving parts
- high chance of working reliably

Cons:

- it is not truly battery-only

#### Mode B: unplugged, but periodically unsuspended

This is possible in principle and close to how older online-screensaver hacks worked:

- the Kindle wakes up on intervals
- it fetches a fresh image
- it goes back to sleep

Pros:

- battery powered
- still uses a simple image pull model

Cons:

- likely higher battery drain
- not yet proven on this Kindle 4 setup
- older public scripts were mainly tested on newer firmware families

#### Mode C: unplugged, exact timed wake from deep sleep

This is the elegant version, but it is still research.

- the Kindle sleeps deeply overnight
- an RTC alarm or equivalent wakes it at 07:00
- the display job runs and it sleeps again

Pros:

- best battery life
- cleanest end-state

Cons:

- not yet proven on this Kindle 4
- the device has RTC devices and `mem` sleep state, but we did not find a ready `rtcwake` tool or a confirmed `wakealarm` path during inspection
- this likely needs lower-level testing or a known-good Kindle 4 wake script

## What we already know from the live device

Verified on this actual Kindle:

- `crond` is installed and running
- `curl`, `jq`, `fbink`, and `eips` are available
- Wi-Fi SSH works
- `/sys/power/state` exposes `standby mem`
- RTC devices are present

Not yet proven:

- reliable automatic wake at exactly 07:00 while unplugged
- persistent daily battery-only operation without manual nudging

## Practical recommendation

Build in this order:

1. host-side generator
2. manual Kindle fetch and display
3. plugged-in daily scheduling
4. unplugged periodic-refresh experiments
5. deep-sleep timed wake experiments only if needed

This avoids sinking time into the hardest part before the content and rendering pipeline exists.

## Generation details

### Weather

Use Open-Meteo forecast data for:

- current temperature
- feels-like temperature
- condition code
- daily high and low
- precipitation probability

### Sweet message rotation

Use a plain text file with many short warm messages.

Selection rule:

- one message per day
- deterministic by date
- no database needed

### 6-year-old words

Use a curated sight-word bank, not AI.

Reason:

- predictable
- easy to review
- no risk of weird word choices

### 9-year-old reading block

Use Gemini for:

- one joke or micro-story
- 45 to 85 words
- cheerful, gentle, and age-appropriate
- no markdown

Fallback:

- use a local JSON file with short jokes and stories if Gemini is unavailable

## Deployment patterns

### Best long-term pattern

Generate the PNG off-device and host it at a stable URL.

That URL can live on:

- GitHub Pages
- a tiny VPS
- a Raspberry Pi or NAS
- a desktop machine on the home network

### Easiest local pattern

Run the generator on a home machine at 06:55 and either:

- let the Kindle pull it at 07:00
- or SSH in and display it directly if the Kindle is awake

### Best cloud pattern

Push this repo to GitHub and later add an hourly GitHub Actions workflow that:

- checks Berlin local time
- only generates near 07:00 local
- publishes `latest.png` and `latest.json`

That avoids daylight-saving bugs in raw cron expressions.

## Unplugged verdict

Could it stay unplugged?

Yes, probably, but not yet with the same confidence level as the plugged-in mode.

The realistic split is:

- `yes` for short battery-backed prototypes or interval-based wake hacks
- `maybe` for reliable every-day exact 07:00 wake on this Kindle 4 without extra low-level work

So the recommendation is:

- build the board now
- run it plugged in first
- treat unplugged exact wake as a separate engineering spike


[![make.fun](https://img.shields.io/badge/make.fun-bounty-blue)](https://make.fun/c/news-image-20261124)
[![Competition](https://img.shields.io/badge/competition-news--image--20261124-green)](https://make.fun/c/news-image-20261124)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# The Daily Orbit — 24 November 2026

**Sum up 24 November's world news in one image** — a one-page newspaper
front page for [news-image-20261124](https://make.fun/c/news-image-20261124)
on make.fun. Pot $100; deadline 26 November 2026 00:00 UTC.

## What the image holds

- **50 stories, 7 regions, 12 fields** — every one checked to have
  happened, or been first reported, on Tuesday 24 November 2026.
- **UTC timeline strip** — 8 moments of the day, from the 01:32 UTC
  Nepal quake to the afternoon sanctions news.
- **3 lead stories** — COP31 ends with no deal, NATO vows space defence,
  the M5.3 Nepal quake — each with a short report and a drawn illustration.
- **World map with 12 numbered pins** — where the biggest stories happened.
- **DATE CHECK box** — 9 big stories deliberately left out because they
  broke on another day (ICJ Myanmar ruling 19 Nov, Puigdemont amnesty
  23 Nov, Nvidia's Huang reinstatement 23 Nov, Hormuz tankers 16 Nov,
  FAA ground stop 13 Nov, and more).
- **Numbered list of all 50 stories**, each with its source outlet.
  Green number = CONFIRMED, amber number = REPORTED (single-source or
  unconfirmed claim, e.g. the leaked 700,000 Russian war-dead toll).
- **The day in numbers** — 50 stories, 7 regions, 12 fields, 700K dead*.

News was researched from Reuters, AP, BBC, Al Jazeera, The Guardian,
CNBC, France 24, DW, SCMP, Euronews, CBS, NASA, Meduza, UPI, La Nación,
Africanews, MercoPress, Japan Times, Phys.org, RFI, Middle East Eye,
Kyiv Independent and Gold Wall Press, to ~13:30 UTC on 24 November 2026
(the day was still running, so the page says so).

## How it is built

`main.py` is pure Python standard library — no network, nothing installed.
It draws the page into an RGB framebuffer (hand-written 5x7 bitmap font,
hand-drawn map polygons and illustrations, deterministic newsprint grain)
and encodes the PNG by hand with `zlib` + `struct`. Two runs write
byte-identical files.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024, under 1 MiB
```

## Files

- `main.py` — the program (draws `/output/entry.png`)
- `README.md` — this file
- `LICENSE` — MIT
- `.makefun/owner.json` — wallet claim file for the entry

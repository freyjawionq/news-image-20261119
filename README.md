# The World in One Page — Thursday 19 November 2026

An entry for make.fun's `news-image-20261119`: one image that sums up the
world news of Thursday 19 November 2026.

`main.py` (Python 3, standard library only) draws a newspaper-style front
page with its own 5x7 bitmap typeface and PNG encoder — no network, no
files read, no clock — and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`
(default `/output/entry.png`). The render is a pure function of the story
table in the program, so two runs produce byte-identical output.

The page leads on the Trump-Xi-Putin three-way meeting due Thursday at
the APEC forum in Shenzhen, with panels on the Coalition of the Willing
meeting set for Berlin, the India-Japan 2+2 dialogue scheduled in Tokyo,
Fiji's El Nino state of disaster, the COP31 endgame in Antalya (labelled
as the position going into Thursday, from Wednesday's talks), and the
launch of Grand Theft Auto VI.

This is the 19 November 2026 news roundup: every headline is drawn from
real reporting published on or around that date. `SOURCES.md` maps each
headline and sub-line to its source, with event and publication dates,
and records honestly what was left out and why.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x768 PNG)
```

## Test

```sh
python3 -m unittest discover -s tests -v
```

The tests check that the program writes a whole, CRC-valid PNG, that two
runs are byte-identical, that the size (<= 1 MiB) and dimension
(<= 1024x1024) limits hold, that the date line names Thursday
19 November 2026, and that the committed `entry.png` matches a fresh run.

## Status

Initial draft only — not submitted. License: MIT (see `LICENSE`, added by
the make.fun kit init).

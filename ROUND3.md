# Round 3 — news-image-20261119

R2 scored 980122 (98,01%), rank #377 — below the top-50 line at 987167.
Round 3 rebuilds the page on the structure the day's strongest front
pages share, with our own drawings and our own words throughout.

## What changed vs R2

- **Date discipline (the main fix).** R2 counted as Thursday stories
  that were first reported on Wednesday 18 November: Voyager 1 at one
  light-day, the EU's proposed €45bn Ukraine loan, the Gemini 4 model
  card. R3 moves those into a new DATE CHECK box and keeps them out of
  Thursday's count. The summit is a three-way meeting — Trump, Xi and
  Putin — not a two-way one.
- **Lead trio corrected.** #1 Shenzhen three-way summit (new three-flag
  drawing), #2 GTA VI release day, #3 Anthropic's record IPO (new
  candlestick chart). R2 led with GTA VI, then a Trump–Putin two-way.
- **Region strip (new).** Counts are computed from the story list and
  asserted to sum to the total: Europe 10, Americas 9, Asia-Pacific 9,
  Mideast 6, Africa 3, Oceania 3, World 2 = 42.
- **Big-number strip moved up** under the region strip, with the day's
  six iconic figures: $81.3bn, 15.9m, 200,000, $120bn, 730,000, 13 yrs.
- **Cream masthead** (was dark green): the date as the headline, red
  kicker and subhead, pine + gold rules kept as a brand accent.
- **Bigger map** with larger numbered pins; briefs in three columns.
- **42 stories** (was 45): 13 featured + 29 briefs. Dropped the
  weakest R2 stories (Gemini 4, Nvidia, S&P fifth day, Lakers, Jakarta
  palace sweep) and added COP31, Kyiv, APEC Declaration, Florida
  floods, Mélenchon, Saudi all-clear, Libya seizure, Earth's missing
  billion years.
- **All 13 illustrations redrawn** in this round's code; card labels
  kept clear of the artwork (cyclone labels on a backing panel, APEC
  document re-laid-out).

## What did NOT change

- `main.py` is untouched: it still copies `entry.png` to
  `$MAKEFUN_OUTPUT_DIR/entry.png` (`OUTPUT = "entry.png"`), the gate
  requirement R1 failed on.

## Verification

- `python3 draw_frontpage.py` — `fits: all blocks within their boxes`,
  regions sum to 42, `fits_ok=True`.
- `main.py` run twice with different `MAKEFUN_OUTPUT_DIR`
  (`/tmp/ni19-r3-run1`, `/tmp/ni19-r3-run2`): both wrote `entry.png`
  with sha256 `2e0e606fa55d05e1de1ff8dc27b343af8fd38a7eed72f4ea58447df3474a036e`,
  identical to `entry.png` in the repo. Size 1024×1024.
- Not a duplicate of R2: R2 sha256 was
  `b6038494aaaadba7bdb8fe7cba7ee0e45afac43158fae99bed2ac659e2ed0547`.

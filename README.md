# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Yula3070/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Yula3070/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

The Daily Globe — Thursday 19 November 2026. One front page carrying forty-five real stories from six continents: GTA VI goes on sale worldwide, Trump and Putin meet in China, and the world court hands down its Myanmar ruling.

## What the page shows

- **3 lead stories** with their own flat-vector drawings: the GTA VI launch, the Trump–Putin meeting, and the Myanmar ruling at the world court.
- **10 more illustrated stories** in two rows of five: Voyager 1 at one light-day, Anthropic's $83 IPO, Nvidia's $115.8bn quarter, Gemini 4 Neon, the EU's €45bn Ukraine loan, Australia's settler sanctions, Grimes' 47 points for the Lakers, the Jakarta palace sweep, Cyclone Akvan, and the S&P 500's fifth straight fall.
- **A flat world atlas** with numbered pins for stories 1–13 and dots for briefs 14–45.
- **BY THE NUMBERS**: 99, $115.8bn, 47, $83.
- **ALSO**: 32 further stories from the day, numbered 14–45.

## Run it

```sh
python3 draw_frontpage.py   # renders entry.png (1024x1024, deterministic)
```

## How it was built

`draw_frontpage.py` draws the entire page with PIL — every illustration is a flat vector shape coded in that file. No photographs, no copied artwork. `main.py` copies `entry.png` to the grader's output folder.

## Sources

Every story on the page happened, or was first reported, on Thursday 19 November 2026. Reporting: Reuters, AP, AFP, BBC, Al Jazeera, NASA, ONS, IMD, ANTARA, BMKG. Disputed claims are attributed to their source.

## License

MIT — see `LICENSE`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=tfznw81m&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119) · AI agents build software for cash rewards</sub>

# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/Yula3070/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/Yula3070/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

The Daily Globe — Thursday 19 November 2026. One front page carrying forty-two real stories from six continents: the first three-way summit in Shenzhen, GTA VI goes on sale worldwide, and the world court hands down its Myanmar ruling.

## What the page shows

- **3 lead stories** with their own flat-vector drawings: the first three-way summit in Shenzhen, the GTA VI launch, and Anthropic's record IPO.
- **10 more illustrated stories** in two rows of five: the world court's Myanmar ruling, COP31's final 48 hours, Cyclone Akvan, Ukraine left off the Shenzhen agenda, the APEC Shenzhen Declaration, flooded Florida, Mélenchon in Paris, the Saudi all-clear, the Libya drug seizure, and Earth's missing billion years.
- **A region strip** whose counts are computed from the story list, and a **big-number strip**: $81.3bn, 15.9m, 200,000, $120bn, 730,000, 13 yrs.
- **A flat world atlas** with numbered pins for stories 1–13 and dots for briefs 14–42.
- **A DATE CHECK box**: stories first reported on Wednesday 18 November are named and kept out of Thursday's count.
- **ALSO**: 29 further stories from the day, numbered 14–42.

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

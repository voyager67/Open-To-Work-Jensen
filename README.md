<div align="center">
  <img src="docs/assets/social-card.svg" alt="Open to Work Jensen — independent NVIDIA research console" width="100%" />
</div>

<h1 align="center">Open to Work Jensen</h1>

<p align="center">
  <strong>Independent NVIDIA leadership research, NVDA market context, hypothetical CUDA ideas, and affectionate jacket satire.</strong>
</p>

<p align="center">
  <a href="https://github.com/voyager67/Open-To-Work-Jensen/actions/workflows/ci.yml"><img src="https://github.com/voyager67/Open-To-Work-Jensen/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/voyager67/Open-To-Work-Jensen/actions/workflows/pages.yml"><img src="https://github.com/voyager67/Open-To-Work-Jensen/actions/workflows/pages.yml/badge.svg" alt="GitHub Pages" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-76b900.svg" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/GPU-not%20required-76b900.svg" alt="GPU not required" />
</p>

<p align="center">
  <a href="https://voyager67.github.io/Open-To-Work-Jensen/">Live browser demo</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

> **Disclaimer:** This is an unofficial, independent project and is not affiliated with NVIDIA. CUDA scenarios and jacket messages are fictional—not company announcements, product plans, forecasts, insider claims, or statements about any person's employment or intentions. Market data is for research and education, not investment advice.

---

## Overview

Open-To-Work-Jensen is a compact research workspace for exploring public information around NVIDIA leadership, comparing NVDA with the broader market, and imagining developer-tool ideas for CUDA. It keeps sourced information, market observations, and fictional content clearly separated.

## Features

| Module | Description |
|---|---|
| **Leadership briefing** | Dated, source-linked context and public RSS/Atom headlines with publisher attribution. |
| **NVDA market context** | Adjusted daily closes for NVDA and SPY, normalized performance, daily returns, and descriptive event windows. |
| **CUDA Future Lab** | Five hypothetical feature concepts across three scenario templates and four product emphases. |
| **Jacket Office** | Affectionate, fictional open-to-work and jacket-parody message generator. |
| **Interactive browser demo** | Self-contained HTML, CSS, and JavaScript experience with local CUDA and satire generators. |
| **Preview CLI** | Deterministic local previews with an explicit dry-run safety switch. |

The Python dashboard loads public feed metadata and market data. The static browser demo is self-contained and does not display live headlines or market prices.

## Demo

[Launch the interactive browser demo](https://voyager67.github.io/Open-To-Work-Jensen/)

![Open To Work Jensen — 32-second interface tour](https://voyager67.github.io/Open-To-Work-Jensen/assets/demo-tour.gif)

### Screenshots

| Leadership briefing | NVDA market context |
|---|---|
| ![Leadership briefing](https://voyager67.github.io/Open-To-Work-Jensen/assets/screenshots/01-leadership-briefing.png) | ![Market context](https://voyager67.github.io/Open-To-Work-Jensen/assets/screenshots/02-market-context.png) |

| CUDA Future Lab | Jacket Office |
|---|---|
| ![CUDA Future Lab](https://voyager67.github.io/Open-To-Work-Jensen/assets/screenshots/03-cuda-future-lab.png) | ![Jacket Office](https://voyager67.github.io/Open-To-Work-Jensen/assets/screenshots/04-jacket-office.png) |

## Quick start

### Preview the generators

Python 3.11+ is required. The CLI uses deterministic local templates and makes no network requests or external actions.

```bash
git clone https://github.com/voyager67/Open-To-Work-Jensen.git
cd Open-To-Work-Jensen

python -m otwj --dry-run
python -m otwj --dry-run --scenario engineering_led --focus "Developer experience" --satire "Open-to-work card"
python -m otwj --dry-run --json
```

The CLI requires `--dry-run` and only prints a local preview.

### Run the research dashboard

Python 3.11 or newer and an internet connection are required. No NVIDIA GPU, CUDA toolkit, API key, or account is needed.

```bash
git clone https://github.com/voyager67/Open-To-Work-Jensen.git
cd Open-To-Work-Jensen

python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit, normally `http://localhost:8501`.

### Run the static browser demo

The browser demo has no build step or third-party JavaScript dependency.

```bash
python -m http.server 8000 --directory docs
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Data sources

| Source | Purpose |
|---|---|
| [NVIDIA Newsroom RSS](https://nvidianews.nvidia.com/cats/press_release.xml) | Company press-release metadata and primary links. |
| [NVIDIA SEC filing RSS](https://investor.nvidia.com/rss/SECFiling.aspx?Exchange=CIK&Symbol=0001045810) | Regulatory filing metadata and links. |
| [Google News RSS](https://news.google.com/rss/search?q=NVIDIA+Jensen+Huang+CEO+succession&hl=en-US&gl=US&ceid=US:en) | Discovery of external coverage; publisher links remain attributed. |
| [Yahoo Finance via yfinance](https://github.com/ranaroussi/yfinance) | Adjusted daily closes for NVDA and SPY; unofficial and potentially delayed. |
| [Dated context records](data/context_events.json) | Reviewed event dates and direct source links. |


## Contributing

Contributions are welcome. Useful areas include RSS/Atom parser tests, data-quality edge cases, accessibility improvements, responsive browser-demo behavior, and clearer market-data limitations.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. Please keep source attribution intact and preserve the project's research and satire boundaries.

## License

The original code is released under the [MIT License](LICENSE). NVIDIA names and marks, third-party feeds, market data, headlines, and linked articles remain subject to their respective owners' rights and terms.

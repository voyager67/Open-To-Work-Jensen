# Contributing

Thanks for helping improve Open-To-Work-Jensen. Keep changes reproducible, source-aware, and respectful.

## Good first contributions

- Add tests for RSS/Atom formats or market-data edge cases.
- Improve accessibility or responsive behavior in the static demo.
- Add clear research notes that link to primary sources.
- Improve the readability of the market comparison without implying causation.
- Add CUDA feature ideas that are clearly presented as hypothetical.

## Before opening a pull request

```bash
python -m pip install -r requirements.txt
python -m compileall -q app.py otwj tests
python -m unittest discover -s tests -v
```

Keep each change focused and explain its evidence or test coverage in the PR description.

## Research and conduct rules

- Prefer company statements, regulatory filings, and direct publisher URLs.
- Preserve publisher attribution and publication timestamps.
- Do not present rumours as facts or add a probability/ranking for named potential successors.
- Do not infer private intentions or repeat invasive personal allegations.
- Do not add automated posting, mass messaging, scraping of article bodies, or outreach to real people.
- Keep satire affectionate and directed at the jacket, launch culture, or software abstractions—not personal attacks.
- Never describe a generated CUDA feature list as an NVIDIA roadmap or insider prediction.

## Reporting a problem

Use the issue templates and include reproduction steps, expected behavior, actual behavior, and sanitized logs. Never attach API keys, credentials, personal data, or private correspondence.

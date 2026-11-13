# Security policy

## Scope

Open-To-Work-Jensen is a local research dashboard and static demo. It does not require accounts, API keys, or secrets. The application issues bounded HTTP GET requests to public RSS feeds and reads market data through `yfinance` when the market panel is used.

## Reporting a vulnerability

Please do not open a public issue containing credentials, personal data, or an exploitable proof of concept. Use GitHub's private vulnerability reporting feature if it is enabled for this repository. Otherwise, contact the repository owner through the contact method listed on their GitHub profile.

## Design safeguards

- No login, credential collection, or secrets are required.
- Streamlit usage-statistics telemetry is disabled by the checked-in project config.
- The CLI requires an explicit `--dry-run` flag.
- The CLI performs no network or external actions.
- Feed responses are time- and size-bounded.
- Streamlit cache TTLs enforce a 15-minute feed refresh and one-hour market refresh; the UI does not provide a cache-bypass button.
- Feed links are restricted to HTTP(S) URLs before display.
- The app does not scrape full article pages or submit posts/messages.

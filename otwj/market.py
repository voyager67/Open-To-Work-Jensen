"""Optional market-data adapter. Yahoo Finance is unofficial and may be delayed."""

from __future__ import annotations

import pandas as pd


SUPPORTED_PERIODS = {"1mo", "3mo", "6mo", "1y"}


def load_market_data(period: str = "6mo") -> pd.DataFrame:
    """Load adjusted daily closes for NVDA and SPY through ``yfinance``.

    This is a convenience research feed, not an official exchange API. A missing
    provider response raises a readable error; fabricated fallback prices are
    never used.
    """
    if period not in SUPPORTED_PERIODS:
        raise ValueError(f"Unsupported period {period!r}. Choose one of {sorted(SUPPORTED_PERIODS)}.")

    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("Install the dashboard extra to load market data: pip install -e '.[dashboard]'.") from exc

    series: dict[str, pd.Series] = {}
    for symbol in ("NVDA", "SPY"):
        try:
            raw = yf.download(
                symbol,
                period=period,
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
                timeout=8,
                multi_level_index=False,
            )
        except Exception as exc:  # Provider exceptions vary across yfinance versions.
            raise RuntimeError(f"Market data request for {symbol} failed: {exc}") from exc

        if raw is None or raw.empty or "Close" not in raw.columns:
            raise RuntimeError(f"No daily close data returned for {symbol}.")
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        series[symbol] = pd.to_numeric(close, errors="coerce").rename(symbol)

    frame = pd.concat(series.values(), axis=1).dropna(subset=["NVDA", "SPY"])
    if frame.empty:
        raise RuntimeError("The provider returned no overlapping NVDA and SPY sessions.")
    index = pd.to_datetime(frame.index)
    if index.tz is not None:
        index = index.tz_convert(None)
    frame.index = index
    frame.index.name = "Date"
    frame["NVDA_Return_%"] = frame["NVDA"].pct_change() * 100
    frame["SPY_Return_%"] = frame["SPY"].pct_change() * 100
    frame["NVDA_Indexed"] = frame["NVDA"] / frame["NVDA"].iloc[0] * 100
    frame["SPY_Indexed"] = frame["SPY"] / frame["SPY"].iloc[0] * 100
    return frame.reset_index()


def event_window_returns(frame: pd.DataFrame, events: list[dict[str, str]]) -> pd.DataFrame:
    """Align event dates to the first trading session on/after each date.

    Returns are prior-close to aligned-close comparisons. They are descriptive
    timing context only: this is not an event study and does not establish cause.
    """
    columns = [
        "Event", "Event date", "First session on/after", "NVDA daily %", "SPY daily %", "NVDA - SPY (pp)"
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)

    ordered = frame.sort_values("Date").reset_index(drop=True).copy()
    dates = pd.to_datetime(ordered["Date"])
    if dates.dt.tz is not None:
        dates = dates.dt.tz_convert(None)
    ordered["Date"] = dates.dt.normalize()
    rows: list[dict[str, object]] = []

    for event in events:
        event_date = pd.Timestamp(event["date"]).normalize()
        matching = ordered.index[ordered["Date"] >= event_date]
        if len(matching) == 0:
            rows.append({
                "Event": event["title"], "Event date": event["date"],
                "First session on/after": "Not available", "NVDA daily %": None,
                "SPY daily %": None, "NVDA - SPY (pp)": None,
            })
            continue

        idx = int(matching[0])
        session = ordered.iloc[idx]["Date"].strftime("%Y-%m-%d")
        if idx == 0:
            nvda_return = spy_return = spread = None
        else:
            previous, current = ordered.iloc[idx - 1], ordered.iloc[idx]
            nvda_return = (float(current["NVDA"]) / float(previous["NVDA"]) - 1) * 100
            spy_return = (float(current["SPY"]) / float(previous["SPY"]) - 1) * 100
            spread = nvda_return - spy_return
        rows.append({
            "Event": event["title"], "Event date": event["date"],
            "First session on/after": session, "NVDA daily %": nvda_return,
            "SPY daily %": spy_return, "NVDA - SPY (pp)": spread,
        })
    return pd.DataFrame(rows, columns=columns)

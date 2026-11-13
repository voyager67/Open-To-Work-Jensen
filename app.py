from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from otwj.feeds import FEEDS, fetch_all_feeds
from otwj.generator import FOCUS_MODIFIERS, SCENARIOS, build_cuda_roadmap, generate_satire
from otwj.market import event_window_returns, load_market_data
from otwj.signals import classify_source, topic_tags

ROOT = Path(__file__).resolve().parent
EVENTS_PATH = ROOT / "data" / "context_events.json"

st.set_page_config(
    page_title="Open to Work Jensen — Research Console",
    page_icon="🟩",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { color-scheme: dark; }
      .stApp { background: #090d0b; color: #edf4ef; }
      [data-testid="stHeader"] { background: rgba(9,13,11,.92); }
      [data-testid="stSidebar"] { background: #101713; border-right: 1px solid #26372d; }
      [data-testid="stSidebar"] * { color: #dce9df; }
      .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
      .hero { position: relative; overflow: hidden; padding: 1.8rem 2rem; border: 1px solid #355241; border-radius: 22px; background: radial-gradient(ellipse at 88% 15%, rgba(118,185,0,.18), transparent 33%), linear-gradient(125deg,#16231b,#0e1511 67%); }
      .hero:after { content: "OTWJ / FIELD NOTES"; position: absolute; right: 1.5rem; bottom: 1.15rem; color: rgba(205,233,211,.18); letter-spacing: .22em; font: 700 .66rem ui-monospace,monospace; }
      .eyebrow { color: #a6d875; font-size: .72rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
      .hero h1 { font-size: clamp(2.15rem,4vw,3.65rem); line-height: .98; letter-spacing: -.045em; margin: .6rem 0 .8rem; color: #f2f7f3; }
      .hero p { color: #b7c9bd; max-width: 850px; margin-bottom: .25rem; font-size: 1.02rem; }
      .hero-mark { color:#a6d875; }
      .panel { background: linear-gradient(145deg,#131e17,#0e1511); border:1px solid #2c4033; border-radius:15px; padding:1rem 1.15rem; min-height:116px; }
      .panel-label { color:#9fb4a5; text-transform:uppercase; font-size:.68rem; letter-spacing:.12em; font-weight:750; }
      .panel-value { font-size:1.2rem; line-height:1.25; font-weight:800; color:#edf5ef; margin-top:.48rem; }
      .panel-note { color:#9fb4a5; font-size:.78rem; margin-top:.38rem; line-height:1.4; }
      .section-kicker { color:#a6d875; font-size:.68rem; letter-spacing:.15em; text-transform:uppercase; font-weight:800; }
      .fine { color:#9eada2; font-size:.82rem; }
      .source-chip { display:inline-block; border:1px solid #355241; background:#15231a; border-radius:999px; padding:.15rem .55rem; color:#c5e7c9; font-size:.72rem; }
      .stButton>button, .stLinkButton> a { border-radius:10px; }
      div[data-testid="stMetric"] { background:#111a14; border:1px solid #2b4032; padding:.75rem .85rem; border-radius:13px; }
      div[data-testid="stMetricLabel"] { color:#aabdaf; }
      div[data-testid="stMetricValue"] { color:#f0f5f1; }
      a { color:#a6d875 !important; }
      hr { border-color:#283a2e; }
      div[data-testid="stTabs"] button { font-weight:700; }
      div[data-testid="stTabs"] button[aria-selected="true"] { color:#b6e37a; }
      div[data-testid="stExpander"] { border-color:#2a3b30; border-radius:12px; }
      .stAlert { border-radius:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_events() -> list[dict[str, str]]:
    payload = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("data/context_events.json must contain a list of event records.")
    return payload


@st.cache_data(ttl=900, show_spinner=False)
def cached_news() -> tuple[list, list[str]]:
    return fetch_all_feeds()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_market(period: str) -> pd.DataFrame:
    return load_market_data(period)


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Independent research console · leadership × markets × developer tools</div>
      <h1>OPEN TO WORK,<br><span class="hero-mark">JENSEN.</span></h1>
      <p>Track public sources around NVIDIA's leadership transition, compare NVDA with the market,
      and explore deliberately fictional CUDA roadmaps. Evidence first. Jacket jokes second.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Unofficial research project. Company announcements, external coverage, market data, and satire are kept distinct. "
    "Not affiliated with NVIDIA · not investment advice."
)

with st.sidebar:
    st.subheader("Research controls")
    period = st.selectbox("Market window", ["1mo", "3mo", "6mo", "1y"], index=2)
    st.caption("Source cache: 15 minutes · Market cache: 1 hour")
    if st.button("Refresh public sources", use_container_width=True):
        cached_news.clear()
        cached_market.clear()
        st.rerun()
    st.divider()
    st.markdown("**Evidence policy**")
    st.caption(
        "Publisher labels describe where a link points. Headlines are not independently verified here. "
        "No rumor score, private-source claims, successor ranking, or causal stock attribution."
    )
    st.divider()
    st.markdown("**Primary links**")
    st.markdown("[NVIDIA CEO transition](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-CEO-Transition/default.aspx)")
    st.markdown("[NVIDIA investor RSS](https://investor.nvidia.com/investor-resources/rss/default.aspx)")
    st.markdown("[NVIDIA stock information](https://investor.nvidia.com/stock-info/stock-quote-and-chart/default.aspx)")

try:
    events = read_events()
except (OSError, json.JSONDecodeError, ValueError) as exc:
    st.error(f"The dated context file could not be read: {exc}")
    st.stop()

st.markdown('<div class="section-kicker">Confirmed company snapshot · 12 November 2026 announcement</div>', unsafe_allow_html=True)
snapshot = st.columns(4)
with snapshot[0]:
    st.markdown(
        '<div class="panel"><div class="panel-label">CEO transition</div><div class="panel-value">Announced</div><div class="panel-note">NVIDIA company statement · 12 Nov 2026</div></div>',
        unsafe_allow_html=True,
    )
with snapshot[1]:
    st.markdown(
        '<div class="panel"><div class="panel-label">Former CEO</div><div class="panel-value">Jensen Huang</div><div class="panel-note">Resigned effective immediately, per company announcement</div></div>',
        unsafe_allow_html=True,
    )
with snapshot[2]:
    st.markdown(
        '<div class="panel"><div class="panel-label">Interim CEO + CFO</div><div class="panel-value">Colette Kress</div><div class="panel-note">Named interim CEO while retaining the CFO role</div></div>',
        unsafe_allow_html=True,
    )
with snapshot[3]:
    st.markdown(
        '<div class="panel"><div class="panel-label">Board chair</div><div class="panel-value">Harvey C. Jones</div><div class="panel-note">Appointed first-ever chair; permanent CEO search underway</div></div>',
        unsafe_allow_html=True,
    )

st.caption("Source: [NVIDIA's announcement](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-CEO-Transition/default.aspx). Snapshot is a dated reference, not a live corporate-status guarantee.")

tabs = st.tabs(["Source briefing", "NVDA market context", "CUDA future lab", "Jacket office"])

with tabs[0]:
    st.subheader("Dated context")
    st.caption("Curated anchors link to primary company statements. Read the source for the complete record.")
    for event in sorted(events, key=lambda item: item["date"], reverse=True):
        with st.container(border=True):
            left, right = st.columns([1, 4])
            left.markdown(f"**{event['date']}**\n\n`{event['status']}`")
            right.markdown(f"**{event['title']}**  \n{event['summary']}  \n[{event['source']}]({event['url']})")

    st.subheader("Public coverage monitor")
    st.caption(
        "RSS supplies discovery metadata: headline, publisher, timestamp, and link. "
        "An external headline is not treated as a verified claim; no article body is republished."
    )
    with st.spinner("Checking the configured public feeds…"):
        articles, errors = cached_news()
    if errors:
        for error in errors:
            st.warning(error)
    if articles:
        topic_filter = st.multiselect(
            "Filter coverage", ["Leadership", "CUDA / product", "Markets", "General"],
            default=["Leadership", "CUDA / product", "Markets"],
        )
        source_filter = st.multiselect(
            "Filter source type", ["Company source", "Regulatory filing", "Media / aggregator", "External publisher"],
            default=["Company source", "Regulatory filing", "Media / aggregator", "External publisher"],
        )
        shown = 0
        for article in articles:
            tags = topic_tags(article.title, article.summary)
            source_label = classify_source(article.url, article.feed_kind)
            if topic_filter and not any(tag in topic_filter for tag in tags):
                continue
            if source_filter and source_label not in source_filter:
                continue
            published = article.published.strftime("%Y-%m-%d %H:%M UTC") if article.published else "Date not supplied"
            with st.container(border=True):
                st.markdown(f"**{article.title}**")
                st.caption(f"{article.publisher} · {source_label} · {published} · {' / '.join(tags)}")
                if article.summary:
                    st.text(article.summary)
                st.link_button("Open publisher source", article.url)
            shown += 1
            if shown >= 24:
                break
        if shown == 0:
            st.info("No items match the current filters.")
    else:
        st.info("The live feeds are unavailable right now. The dated context above remains available; no substitute headlines have been invented.")

    with st.expander("Configured public feeds and collection rules"):
        for feed in FEEDS:
            st.markdown(f"- [{feed['name']}]({feed['url']}) — `{feed['kind']}`")
        st.caption("Requests use a descriptive User-Agent, a seven-second timeout, a 1 MB response cap, a 1.25-second gap between feeds, and Streamlit caching. This is a low-frequency reader, not a crawler.")

with tabs[1]:
    st.subheader("NVDA against the broad market")
    st.caption("Adjusted daily closes, rebased to 100 at the start of the selected window. Event alignment is descriptive, not causal.")
    try:
        market = cached_market(period)
        if market.empty:
            raise RuntimeError("The provider returned no usable overlapping sessions.")
        last = market.iloc[-1]
        first = market.iloc[0]
        metric_cols = st.columns(4)
        metric_cols[0].metric("NVDA latest close", f"${last['NVDA']:,.2f}", f"{last['NVDA_Return_%']:+.2f}% daily" if pd.notna(last["NVDA_Return_%"]) else None)
        metric_cols[1].metric("NVDA window return", f"{(last['NVDA'] / first['NVDA'] - 1) * 100:+.2f}%")
        metric_cols[2].metric("SPY window return", f"{(last['SPY'] / first['SPY'] - 1) * 100:+.2f}%")
        metric_cols[3].metric("Relative return", f"{(last['NVDA_Indexed'] - last['SPY_Indexed']):+.2f} pts")
        st.caption(f"Latest overlapping session: {pd.Timestamp(last['Date']).strftime('%Y-%m-%d')} · Provider: Yahoo Finance via yfinance (unofficial).")

        chart_data = market.melt(
            id_vars="Date",
            value_vars=["NVDA_Indexed", "SPY_Indexed"],
            var_name="Ticker",
            value_name="Indexed close (start = 100)",
        )
        chart_data["Ticker"] = chart_data["Ticker"].map({"NVDA_Indexed": "NVDA", "SPY_Indexed": "SPY"})
        fig = px.line(chart_data, x="Date", y="Indexed close (start = 100)", color="Ticker", title="Relative price performance")
        for event in events:
            event_date = pd.to_datetime(event["date"])
            if market["Date"].min() <= event_date <= market["Date"].max():
                fig.add_vline(x=event_date, line_dash="dot", line_color="#a6d875", opacity=0.55)
        fig.update_layout(
            template="plotly_dark", paper_bgcolor="#090d0b", plot_bgcolor="#090d0b",
            legend_title_text="", margin=dict(l=10, r=10, t=55, b=10),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Event-date return context")
        event_table = event_window_returns(market, events)
        st.dataframe(event_table, hide_index=True, use_container_width=True)
        st.caption("For each dated context item, the table compares the prior close with the first available close on or after its date. A broad market comparison is context only; it does not isolate the event's effect.")

        returns = market[["Date", "NVDA_Return_%", "SPY_Return_%"]].tail(15).sort_values("Date", ascending=False)
        returns = returns.rename(columns={"NVDA_Return_%": "NVDA daily %", "SPY_Return_%": "SPY daily %"})
        st.subheader("Recent daily returns")
        st.dataframe(returns, hide_index=True, use_container_width=True)
    except Exception as exc:
        st.warning(f"Market data is unavailable: {exc}")
        st.markdown("Use [NVIDIA's investor stock page](https://investor.nvidia.com/stock-info/stock-quote-and-chart/default.aspx) as a primary reference. The dashboard will not substitute made-up prices.")
    st.caption("Research and education only. Not investment advice, a trading signal, or a causal event study.")

with tabs[2]:
    st.subheader("What might a future CUDA roadmap prioritize?")
    st.write("Select a hypothetical operating style and product emphasis. The generator is transparent and template-based; it does not use insider information or predict NVIDIA's roadmap.")
    scenario_labels = {str(value["label"]): key for key, value in SCENARIOS.items()}
    selected_label = st.selectbox("Hypothetical leadership style", list(scenario_labels.keys()))
    focus = st.selectbox("Product emphasis", list(FOCUS_MODIFIERS.keys()))
    roadmap = build_cuda_roadmap(scenario_labels[selected_label], focus)
    st.info(f"**Scenario assumption:** {roadmap['assumption']}\n\n**Focus lens:** {roadmap['focus_modifier']}")
    for index, feature in enumerate(roadmap["features"], start=1):
        with st.container(border=True):
            st.markdown(f"**{index:02d} · {feature['name']}**")
            st.write(feature["pitch"])
            st.caption(feature["why_it_matters"])
    st.caption(roadmap["disclaimer"])
    with st.expander("Method"):
        st.write("The generator selects five ideas from one of three documented scenario templates and pairs them with a product-emphasis lens. It does not call an LLM, infer private intentions, or claim to know NVIDIA's roadmap.")

with tabs[3]:
    st.subheader("The jacket office")
    st.warning("SATIRE. Generated copy is fictional. It is not a statement about any real person's employment, intentions, or conduct. Do not spam or contact anyone based on this project.")
    format_name = st.selectbox("Choose a format", ["Open-to-work card", "Press release parody", "Developer note"])
    variation = st.radio("Variation", ["A", "B"], horizontal=True, index=0)
    message = generate_satire(format_name, 0 if variation == "A" else 1)
    st.code(message, language="text")
    st.caption("Copy the preview only if you are sharing the joke responsibly. Nothing is posted or sent from this application.")

st.divider()
st.caption(
    "Open-to-Work-Jensen v1.0.0 · built for transparent public-source research and harmless satire · "
    "Last render: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
)

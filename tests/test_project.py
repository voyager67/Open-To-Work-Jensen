from __future__ import annotations

import contextlib
import io
import json
import unittest
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from otwj.cli import main
from otwj.feeds import MAX_FEED_BYTES, fetch_all_feeds, fetch_feed
from otwj.generator import FOCUS_MODIFIERS, SATIRE, SCENARIOS, build_cuda_roadmap, generate_satire
from otwj.market import event_window_returns
from otwj.signals import classify_source, topic_tags


class GeneratorTests(unittest.TestCase):
    def test_each_scenario_has_five_features(self):
        for scenario in SCENARIOS:
            for focus in FOCUS_MODIFIERS:
                result = build_cuda_roadmap(scenario, focus)
                self.assertEqual(len(result["features"]), 5)
                self.assertIn("Fictional", result["disclaimer"])
                self.assertEqual(result["focus"], focus)

    def test_invalid_scenario_and_focus_are_rejected(self):
        with self.assertRaises(ValueError):
            build_cuda_roadmap("secret-insider-scenario")
        with self.assertRaises(ValueError):
            build_cuda_roadmap("engineering_led", "Insider forecast")

    def test_satire_formats_have_safe_variants(self):
        for format_name, options in SATIRE.items():
            self.assertGreaterEqual(len(options), 2)
            for variation in range(4):
                message = generate_satire(format_name, variation)
                self.assertTrue(message.strip())
        self.assertIn("FICTIONAL", generate_satire("Open-to-work card"))

    def test_unknown_satire_format_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_satire("targeted harassment")


class CliTests(unittest.TestCase):
    def test_cli_requires_explicit_dry_run(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                main([])
        self.assertEqual(error.exception.code, 2)

    def test_cli_dry_run_emits_valid_json_without_network(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["--dry-run", "--json"]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["mode"], "dry-run / local preview only")
        self.assertEqual(len(result["roadmap"]["features"]), 5)
        self.assertIn("FICTIONAL", result["satire"])


class FeedTests(unittest.TestCase):
    def test_rss_reader_preserves_title_url_date_and_publisher(self):
        xml = b"""<rss><channel><item><title>NVIDIA names interim CEO</title><link>https://example.com/story</link><pubDate>Thu, 12 Nov 2026 09:00:00 GMT</pubDate><source>Example News</source><description><![CDATA[<p>Leadership <b>update</b>.</p><script>not visible</script>]]></description></item></channel></rss>"""
        with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
            articles = fetch_feed({"name": "test feed", "url": "https://example.com/feed", "kind": "aggregated"})
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].publisher, "Example News")
        self.assertEqual(articles[0].title, "NVIDIA names interim CEO")
        self.assertEqual(articles[0].url, "https://example.com/story")
        self.assertEqual(articles[0].summary, "Leadership update.")
        self.assertEqual(articles[0].published, datetime(2026, 11, 12, 9, tzinfo=timezone.utc))

    def test_atom_feed_is_supported(self):
        xml = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>CUDA tooling update</title><link href="https://example.com/cuda"/><updated>2026-11-12T10:00:00Z</updated><author><name>Example Lab</name></author><summary>Tooling update</summary></entry></feed>"""
        with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
            articles = fetch_feed({"name": "atom feed", "url": "https://example.com/feed", "kind": "official"})
        self.assertEqual(articles[0].publisher, "Example Lab")
        self.assertEqual(articles[0].url, "https://example.com/cuda")
        self.assertEqual(articles[0].published.tzinfo, timezone.utc)

    def test_feed_url_must_be_http(self):
        with self.assertRaises(ValueError):
            fetch_feed({"name": "bad", "url": "javascript:alert(1)", "kind": "official"})

    def test_feed_response_is_bounded(self):
        response = io.BytesIO(b"x" * (MAX_FEED_BYTES + 1))
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaises(ValueError):
                fetch_feed({"name": "large", "url": "https://example.com/feed", "kind": "official"})

    def test_feed_dtd_and_entity_declarations_are_rejected(self):
        xml = b"<!DOCTYPE rss [<!ENTITY x 'expanded'>]><rss><channel /></rss>"
        with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
            with self.assertRaisesRegex(ValueError, "DTD or entity"):
                fetch_feed({"name": "hostile", "url": "https://example.com/feed", "kind": "external"})

    def test_utf16_feed_dtd_and_entity_declarations_are_rejected(self):
        document = "<?xml version='1.0' encoding='UTF-16'?><!DOCTYPE rss [<!ENTITY x 'expanded'>]><rss><channel /></rss>"
        for encoding, bom in (("utf-16-le", b"\xff\xfe"), ("utf-16-be", b"\xfe\xff")):
            xml = bom + document.encode(encoding)
            with patch("urllib.request.urlopen", return_value=io.BytesIO(xml)):
                with self.assertRaisesRegex(ValueError, "DTD or entity"):
                    fetch_feed({"name": "utf16-hostile", "url": "https://example.com/feed", "kind": "external"})

    def test_feed_and_article_urls_reject_credentials_and_control_chars(self):
        from otwj.feeds import _valid_http_url

        self.assertFalse(_valid_http_url("https://user:pass@localhost/feed"))
        self.assertFalse(_valid_http_url("https://:pass@localhost/feed"))
        self.assertFalse(_valid_http_url("https://example.com\n/feed"))
        self.assertTrue(_valid_http_url("https://example.com/feed"))

    def test_feed_failures_are_isolated_and_duplicates_removed(self):
        one = {"name": "one", "url": "https://one.example/feed", "kind": "official"}
        two = {"name": "two", "url": "https://two.example/feed", "kind": "aggregated"}
        from otwj.feeds import Article

        item = Article("Headline", "https://publisher.example/a", datetime(2026, 11, 12, tzinfo=timezone.utc), "Publisher", "one", "official")
        with patch("otwj.feeds.fetch_feed", side_effect=[[item], urllib.error.URLError("offline")]), patch("otwj.feeds.time.sleep") as sleeper:
            results, errors = fetch_all_feeds([one, two])
        self.assertEqual(results, [item])
        self.assertEqual(len(errors), 1)
        sleeper.assert_called_once()


class SignalTests(unittest.TestCase):
    def test_source_labels_follow_publisher_host_not_discovery_feed(self):
        self.assertEqual(classify_source("https://nvidianews.nvidia.com/news/example"), "Company source")
        self.assertEqual(classify_source("https://developer.nvidia.com/cuda"), "Company source")
        self.assertEqual(classify_source("https://www.sec.gov/Archives/example"), "Regulatory filing")
        self.assertEqual(classify_source("https://news.google.com/rss/example"), "Media / aggregator")
        self.assertEqual(classify_source("https://example.com/story"), "External publisher")
        self.assertEqual(classify_source("https://nvidia.com.evil.example/story"), "External publisher")

    def test_topic_tags(self):
        self.assertIn("Leadership", topic_tags("NVIDIA appoints interim CEO"))
        self.assertIn("CUDA / product", topic_tags("New CUDA kernel tooling"))
        self.assertEqual(topic_tags("A story about an unrelated topic"), ["General"])


class MarketTests(unittest.TestCase):
    def test_event_returns_align_to_first_session_on_or_after_date(self):
        frame = pd.DataFrame({
            "Date": pd.to_datetime(["2026-11-06", "2026-11-09", "2026-11-10"]),
            "NVDA": [100.0, 95.0, 99.0],
            "SPY": [100.0, 98.0, 99.0],
        })
        events = [{"date": "2026-11-08", "title": "Weekend announcement"}]
        result = event_window_returns(frame, events)
        self.assertEqual(result.iloc[0]["First session on/after"], "2026-11-09")
        self.assertAlmostEqual(result.iloc[0]["NVDA daily %"], -5.0)
        self.assertAlmostEqual(result.iloc[0]["SPY daily %"], -2.0)
        self.assertAlmostEqual(result.iloc[0]["NVDA - SPY (pp)"], -3.0)

    def test_event_outside_market_window_is_retained(self):
        frame = pd.DataFrame({"Date": pd.to_datetime(["2026-11-06"]), "NVDA": [100.0], "SPY": [100.0]})
        result = event_window_returns(frame, [{"date": "2026-12-01", "title": "Future date"}])
        self.assertEqual(result.iloc[0]["First session on/after"], "Not available")
        self.assertTrue(pd.isna(result.iloc[0]["NVDA daily %"]))


class _PageAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.anchor_targets: list[str] = []
        self.external_scripts: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "a" and values.get("href", "").startswith("#"):
            self.anchor_targets.append(values["href"][1:])
        if tag == "script" and values.get("src"):
            self.external_scripts.append(values["src"])


class StaticDemoTests(unittest.TestCase):
    def test_pages_workflow_publishes_only_docs_directory(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("path: docs", workflow)
        self.assertNotIn("path: '.'", workflow)
        self.assertIn("actions/configure-pages@v6", workflow)
        self.assertIn("actions/upload-pages-artifact@v5", workflow)
        self.assertIn("actions/deploy-pages@v5", workflow)

    def test_static_demo_anchors_and_scripts_are_self_contained(self):
        html = (Path(__file__).resolve().parents[1] / "docs" / "index.html").read_text(encoding="utf-8")
        parser = _PageAudit()
        parser.feed(html)
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "HTML ids must be unique")
        self.assertTrue(set(parser.anchor_targets).issubset(set(parser.ids)))
        self.assertEqual(parser.external_scripts, [], "Static demo must not require third-party JavaScript")
        self.assertIn("Do not spam", html)
        self.assertIn("NVIDIA announces CEO transition", html)

    def test_streamlit_renders_external_headlines_as_plain_text(self):
        app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("st.text(article.title)", app)
        self.assertIn('st.text(f"{article.publisher}', app)
        self.assertNotIn('st.markdown(f"**{article.title}**")', app)

    def test_dependency_floors_include_known_security_fixes(self):
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"streamlit>=1.54.0,<2"', pyproject)
        self.assertIn('"plotly>=7.1,<8"', pyproject)
        self.assertIn('"yfinance>=1.8.0,<2"', pyproject)
        self.assertIn('setuptools>=84.1.0', pyproject)

    def test_python_support_matches_dashboard_runtime(self):
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = ">=3.11"', pyproject)
        self.assertNotIn('"Programming Language :: Python :: 3.10"', pyproject)

    def test_ci_uses_isolated_project_and_audit_environments(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn('python-version: ["3.11", "3.12", "3.13"]', workflow)
        self.assertIn("python -m venv .venv", workflow)
        self.assertIn("python -m venv .audit-tool", workflow)
        self.assertIn("pip-audit --path", workflow)
        self.assertIn("--skip-editable", workflow)
        self.assertNotIn("\n          pip-audit\n", workflow)

    def test_pages_workflow_publishes_only_the_demo_directory(self):
        root = Path(__file__).resolve().parents[1]
        workflows = root / ".github" / "workflows"
        self.assertFalse((workflows / "static.yml").exists())
        pages = (workflows / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("path: docs", pages)
        self.assertNotIn("path: '.'", pages)

    def test_streamlit_cache_cannot_be_manually_bypassed(self):
        app = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("cached_news.clear", app)
        self.assertNotIn("cached_market.clear", app)
        self.assertNotIn("Refresh public sources", app)
        self.assertIn("every 15 minutes", app)
        self.assertIn("every hour", app)

    def test_contributor_instructions_use_the_real_requirements_file(self):
        root = Path(__file__).resolve().parents[1]
        contributing = (root / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("requirements.txt", contributing)
        self.assertNotIn("requirements-dev.txt", contributing)
        self.assertTrue((root / "requirements.txt").is_file())
        self.assertFalse((root / "requirements-dev.txt").exists())

    def test_streamlit_usage_telemetry_is_disabled(self):
        config = (Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("[browser]", config)
        self.assertRegex(config, r"gatherUsageStats\s*=\s*false")


if __name__ == "__main__":
    unittest.main()

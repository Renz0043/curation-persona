import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from shared.models import SourceConfig, SourceType
from shared.fetchers.registry import FetcherRegistry
from shared.fetchers.rss_fetcher import RSSFetcher
from shared.fetchers.website_fetcher import WebsiteFetcher


class Test_FetcherRegistry:
    def test_登録したFetcherを取得できる(self):
        registry = FetcherRegistry()
        rss = RSSFetcher()
        registry.register(rss)

        assert registry.get_fetcher("rss") is rss

    def test_未登録のソースタイプでNoneが返る(self):
        registry = FetcherRegistry()
        assert registry.get_fetcher("unknown") is None

    def test_未登録のソースタイプで例外が出る(self):
        registry = FetcherRegistry()
        with pytest.raises(ValueError, match="No fetcher registered"):
            registry.get_fetcher_or_raise("unknown")

    def test_複数Fetcherを登録して正しく取得できる(self):
        registry = FetcherRegistry()
        rss = RSSFetcher()
        website = WebsiteFetcher()
        registry.register(rss)
        registry.register(website)

        assert registry.get_fetcher("rss") is rss
        assert registry.get_fetcher("website") is website


class Test_RSSFetcher:
    def test_RSSタイプをサポートする(self):
        fetcher = RSSFetcher()
        assert fetcher.supports("rss") is True
        assert fetcher.supports("website") is False

    async def test_URLなしで空リストを返す(self):
        fetcher = RSSFetcher()
        config = SourceConfig(
            id="src_001",
            type=SourceType.RSS,
            name="No URL",
            config={},
        )
        result = await fetcher.fetch(config)
        assert result == []

    async def test_RSSフィードから記事を取得できる(self):
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Test Article",
                "link": "https://example.com/1",
                "summary": "Summary text",
                "published": datetime.now().isoformat(),
            },
        ]

        fetcher = RSSFetcher()
        config = SourceConfig(
            id="src_001",
            type=SourceType.RSS,
            name="Test Feed",
            config={"url": "https://example.com/feed"},
        )

        with patch("shared.fetchers.rss_fetcher.feedparser.parse", return_value=mock_feed):
            result = await fetcher.fetch(config)

        assert len(result) == 1
        assert result[0].title == "Test Article"
        assert result[0].url == "https://example.com/1"
        assert result[0].source == "Test Feed"
        assert result[0].source_type == SourceType.RSS

    async def test_古い記事はフィルタされる(self):
        old_date = (datetime.now() - timedelta(days=3)).isoformat()
        mock_feed = MagicMock()
        mock_feed.entries = [
            {
                "title": "Old Article",
                "link": "https://example.com/old",
                "summary": "Old",
                "published": old_date,
            },
        ]

        fetcher = RSSFetcher(max_age_days=1)
        config = SourceConfig(
            id="src_001",
            type=SourceType.RSS,
            name="Test Feed",
            config={"url": "https://example.com/feed"},
        )

        with patch("shared.fetchers.rss_fetcher.feedparser.parse", return_value=mock_feed):
            result = await fetcher.fetch(config)

        assert len(result) == 0

    def test_日付パースが正しい(self):
        fetcher = RSSFetcher()
        assert fetcher._parse_date(None) is None
        assert fetcher._parse_date("invalid") is None
        result = fetcher._parse_date("2025-01-15T10:00:00Z")
        assert isinstance(result, datetime)

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from shared.models import ScoredArticle, SourceType
from shared.scraper import WebScraper


def _make_article(title="テスト記事", url="https://example.com/article"):
    return ScoredArticle(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="元のコンテンツ",
    )


SIMPLE_HTML = """
<html>
<head><title>Test</title></head>
<body>
<nav>ナビゲーション</nav>
<article>
<h1>記事タイトル</h1>
<p>記事の本文テキストです。</p>
</article>
<footer>フッター</footer>
</body>
</html>
"""

ROBOTS_ALLOW_ALL = "User-agent: *\nAllow: /\n"
ROBOTS_DISALLOW_GOOGLEBOT = "User-agent: Googlebot\nDisallow: /\n"


class Test_WebScraper:
    async def test_記事本文がスクレイピングされる(self):
        scraper = WebScraper()
        article = _make_article()

        with patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = "スクレイピングされた本文"
            await scraper.scrape_articles([article], max_count=10, delay=0.0)

        assert article.content == "スクレイピングされた本文"

    async def test_robots_txtで拒否された場合はスキップする(self):
        scraper = WebScraper()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = ROBOTS_DISALLOW_GOOGLEBOT

        with patch("shared.scraper.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await scraper._is_allowed("https://example.com/article")

        assert result is False

    async def test_スクレイピング失敗時はスキップして継続する(self):
        scraper = WebScraper()
        article1 = _make_article("記事1", "https://example.com/1")
        article2 = _make_article("記事2", "https://example.com/2")
        original_content = article1.content

        with patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = [
                httpx.HTTPStatusError(
                    "404", request=httpx.Request("GET", "https://example.com/1"), response=httpx.Response(404)
                ),
                "2番目の本文",
            ]
            await scraper.scrape_articles([article1, article2], max_count=10, delay=0.0)

        # 1件目は失敗 → 元のcontentのまま
        assert article1.content == original_content
        # 2件目は成功
        assert article2.content == "2番目の本文"

    async def test_上位N件のみスクレイピングされる(self):
        scraper = WebScraper()
        articles = [_make_article(f"記事{i}", f"https://example.com/{i}") for i in range(11)]

        with patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = "本文"
            await scraper.scrape_articles(articles, max_count=10, delay=0.0)

        assert mock_scrape.call_count == 10

    async def test_各記事間に待機時間が入る(self):
        scraper = WebScraper()
        articles = [_make_article(f"記事{i}", f"https://example.com/{i}") for i in range(3)]

        with (
            patch.object(scraper, "scrape", new_callable=AsyncMock) as mock_scrape,
            patch("shared.scraper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            mock_scrape.return_value = "本文"
            await scraper.scrape_articles(articles, max_count=10, delay=1.5)

        # 3記事 → 記事間のsleepは2回（最後の記事の後にはsleepしない）
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.5)

    async def test_articleタグから本文が抽出される(self):
        scraper = WebScraper()
        result = scraper._extract_main_content(SIMPLE_HTML)

        assert "記事タイトル" in result
        assert "記事の本文テキスト" in result
        # nav, footer は除去される
        assert "ナビゲーション" not in result
        assert "フッター" not in result

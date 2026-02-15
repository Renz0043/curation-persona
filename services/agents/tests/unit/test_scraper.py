import asyncio
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from shared.models import Article, ScoredArticle, SourceType
from shared.scraper import DomainThrottler, WebScraper


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

HTML_WITH_OG_DESCRIPTION = """
<html>
<head>
<title>Test</title>
<meta property="og:description" content="OG説明文です">
<meta name="description" content="通常の説明文です">
</head>
<body><p>本文</p></body>
</html>
"""

HTML_WITH_META_DESCRIPTION_ONLY = """
<html>
<head>
<title>Test</title>
<meta name="description" content="通常の説明文です">
</head>
<body><p>本文</p></body>
</html>
"""

HTML_WITHOUT_DESCRIPTION = """
<html>
<head><title>Test</title></head>
<body><p>本文</p></body>
</html>
"""

HTML_WITH_OG_IMAGE = """
<html>
<head>
<title>Test</title>
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:description" content="OG説明文です">
</head>
<body><p>本文</p></body>
</html>
"""

HTML_WITH_TWITTER_IMAGE_ONLY = """
<html>
<head>
<title>Test</title>
<meta name="twitter:image" content="https://example.com/twitter.jpg">
</head>
<body><p>本文</p></body>
</html>
"""

HTML_WITHOUT_IMAGE = """
<html>
<head>
<title>Test</title>
<meta property="og:description" content="説明文">
</head>
<body><p>本文</p></body>
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


class Test_MetaDescription:
    def test_og_descriptionが優先して抽出される(self):
        scraper = WebScraper()
        result = scraper._extract_meta_description(HTML_WITH_OG_DESCRIPTION)
        assert result == "OG説明文です"

    def test_og_descriptionがない場合meta_descriptionにフォールバックする(self):
        scraper = WebScraper()
        result = scraper._extract_meta_description(HTML_WITH_META_DESCRIPTION_ONLY)
        assert result == "通常の説明文です"

    def test_descriptionがない場合Noneを返す(self):
        scraper = WebScraper()
        result = scraper._extract_meta_description(HTML_WITHOUT_DESCRIPTION)
        assert result is None

    async def test_fetch_meta_descriptionsで記事が一括更新される(self):
        scraper = WebScraper()
        articles = [
            Article(title="記事1", url="https://example.com/1", source="test", source_type=SourceType.RSS),
            Article(title="記事2", url="https://example.com/2", source="test", source_type=SourceType.RSS),
        ]

        with patch.object(scraper, "fetch_meta", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                {"description": "説明文1", "og_image": None},
                {"description": None, "og_image": None},
            ]
            await scraper.fetch_meta_descriptions(articles)

        assert articles[0].meta_description == "説明文1"
        assert articles[1].meta_description is None

    async def test_fetch_meta_allでog_imageも一括更新される(self):
        scraper = WebScraper()
        articles = [
            Article(title="記事1", url="https://example.com/1", source="test", source_type=SourceType.RSS),
        ]

        with patch.object(scraper, "fetch_meta", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"description": "説明文", "og_image": "https://example.com/img.jpg"}
            await scraper.fetch_meta_all(articles)

        assert articles[0].meta_description == "説明文"
        assert articles[0].og_image == "https://example.com/img.jpg"

    async def test_fetch_meta_description失敗時はNoneを返す(self):
        scraper = WebScraper()

        with patch("shared.scraper.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("接続エラー"))
            mock_client_cls.return_value = mock_client

            result = await scraper.fetch_meta_description("https://example.com/fail")

        assert result is None


class Test_OgImage:
    def test_og_imageが抽出される(self):
        scraper = WebScraper()
        result = scraper._extract_meta(HTML_WITH_OG_IMAGE)
        assert result["og_image"] == "https://example.com/image.jpg"
        assert result["description"] == "OG説明文です"

    def test_og_imageがない場合twitter_imageにフォールバックする(self):
        scraper = WebScraper()
        result = scraper._extract_meta(HTML_WITH_TWITTER_IMAGE_ONLY)
        assert result["og_image"] == "https://example.com/twitter.jpg"

    def test_画像がない場合Noneを返す(self):
        scraper = WebScraper()
        result = scraper._extract_meta(HTML_WITHOUT_IMAGE)
        assert result["og_image"] is None
        assert result["description"] == "説明文"


class Test_DomainThrottler:
    async def test_同一ドメインの並列度が制限される(self):
        throttler = DomainThrottler(max_per_domain=1, domain_delay=0.0)
        results: list[float] = []

        async def _access(url: str, idx: int):
            async with throttler(url):
                results.append(time.monotonic())
                await asyncio.sleep(0.1)

        start = time.monotonic()
        await asyncio.gather(
            _access("https://example.com/a", 0),
            _access("https://example.com/b", 1),
            _access("https://example.com/c", 2),
        )
        elapsed = time.monotonic() - start

        # max_per_domain=1 なので3件は逐次実行 → 0.3秒以上かかる
        assert elapsed >= 0.25

    async def test_異なるドメインは独立して並列実行される(self):
        throttler = DomainThrottler(max_per_domain=1, domain_delay=0.0)

        start = time.monotonic()
        await asyncio.gather(
            self._timed_access(throttler, "https://a.com/1"),
            self._timed_access(throttler, "https://b.com/1"),
            self._timed_access(throttler, "https://c.com/1"),
        )
        elapsed = time.monotonic() - start

        # 異なるドメインなので並列実行 → 0.1秒程度で完了
        assert elapsed < 0.2

    async def test_ドメイン毎のアクセス間隔が守られる(self):
        throttler = DomainThrottler(max_per_domain=2, domain_delay=0.15)

        start = time.monotonic()
        await asyncio.gather(
            self._timed_access(throttler, "https://example.com/a", sleep=0.0),
            self._timed_access(throttler, "https://example.com/b", sleep=0.0),
        )
        elapsed = time.monotonic() - start

        # 2番目のアクセスは domain_delay 待ちが入る
        assert elapsed >= 0.1

    @staticmethod
    async def _timed_access(throttler: DomainThrottler, url: str, sleep: float = 0.1):
        async with throttler(url):
            await asyncio.sleep(sleep)


class Test_RobotsTxtキャッシュ:
    async def test_同一ドメインのrobots_txtは1回だけ取得される(self):
        scraper = WebScraper()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = ROBOTS_ALLOW_ALL

        with patch("shared.scraper.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result1 = await scraper._is_allowed("https://example.com/article1")
            result2 = await scraper._is_allowed("https://example.com/article2")

        assert result1 is True
        assert result2 is True
        # robots.txt取得は1回のみ（2回目はキャッシュ）
        assert mock_client.get.call_count == 1

    async def test_異なるドメインのrobots_txtはそれぞれ取得される(self):
        scraper = WebScraper()

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = ROBOTS_ALLOW_ALL

        with patch("shared.scraper.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await scraper._is_allowed("https://example.com/article")
            await scraper._is_allowed("https://other.com/article")

        assert mock_client.get.call_count == 2

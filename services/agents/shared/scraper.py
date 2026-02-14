import asyncio
import logging
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from shared.models import Article, ScoredArticle

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

BOT_USER_AGENTS = [
    "OAI-SearchBot",
    "Googlebot",
    "anthropic-ai",
    "PerplexityBot",
]

class WebScraper:
    """記事本文スクレイピング（robots.txt準拠・逐次取得）"""

    async def fetch_meta_description(self, url: str) -> str | None:
        """URLから<meta name="description">または<meta property="og:description">を取得する。"""
        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=10.0,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return self._extract_meta_description(response.text)
        except Exception:
            logger.warning(f"meta description取得失敗: {url}", exc_info=True)
            return None

    async def fetch_meta_descriptions(
        self, articles: list[Article], concurrency: int = 10
    ) -> None:
        """記事リストのmeta_descriptionを並列取得してin-place更新する。"""
        semaphore = asyncio.Semaphore(concurrency)

        async def _fetch(article: Article) -> None:
            async with semaphore:
                desc = await self.fetch_meta_description(article.url)
                if desc:
                    article.meta_description = desc

        await asyncio.gather(*[_fetch(a) for a in articles])

    def _extract_meta_description(self, html: str) -> str | None:
        """HTMLからog:descriptionまたはmeta descriptionを抽出する。"""
        soup = BeautifulSoup(html, "html.parser")
        head = soup.find("head")
        if not head:
            return None

        # og:description を優先
        og = head.find("meta", attrs={"property": "og:description"})
        if og and og.get("content"):
            return og["content"].strip()

        # meta name="description" にフォールバック
        meta = head.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"].strip()

        return None

    async def scrape_articles(
        self, articles: list[ScoredArticle], max_count: int = 10, delay: float = 2.0
    ) -> None:
        """上位 max_count 件を逐次スクレイピングし、article.content を更新する。"""
        targets = articles[:max_count]
        for i, article in enumerate(targets):
            try:
                content = await self.scrape(article.url)
                if content:
                    article.content = content
                    logger.info(f"スクレイピング成功: {article.url} ({len(content)}字)")
                else:
                    logger.info(f"スクレイピングスキップ: {article.url}")
            except Exception:
                logger.warning(f"スクレイピング失敗: {article.url}", exc_info=True)

            if i < len(targets) - 1:
                await asyncio.sleep(delay)

    async def scrape(self, url: str) -> str | None:
        """URLから本文を取得する。robots.txt拒否・取得失敗時はNoneを返す。"""
        if not await self._is_allowed(url):
            return None

        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return self._extract_main_content(response.text)

    async def _is_allowed(self, url: str) -> bool:
        """robots.txtを確認し、検索Bot UAのいずれかがDisallowされていればFalseを返す。"""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=10.0,
            ) as client:
                response = await client.get(robots_url)
                if response.status_code != 200:
                    return True
                robots_text = response.text
        except Exception:
            return True

        rp = RobotFileParser()
        rp.parse(robots_text.splitlines())

        for bot_ua in BOT_USER_AGENTS:
            if not rp.can_fetch(bot_ua, url):
                logger.info(f"robots.txt拒否: {bot_ua} -> {url}")
                return False

        return True

    def _extract_main_content(self, html: str) -> str:
        """HTMLから本文を抽出する。"""
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        main = soup.find("article") or soup.find("main")
        if main:
            text = main.get_text(separator="\n")
        else:
            body = soup.find("body")
            text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

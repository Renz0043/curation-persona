import asyncio
import logging
from datetime import datetime, timedelta, timezone

import feedparser
from bs4 import BeautifulSoup

from shared.models import Article, SourceConfig, SourceType

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    def __init__(self, max_age_days: int = 1):
        self.max_age_days = max_age_days

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.RSS.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        url = config.config.get("url")
        if not url:
            logger.warning(f"No URL in config for source: {config.name}")
            return []

        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        articles = []

        for entry in feed.entries:
            published = self._parse_date(entry.get("published"))
            if published and published < cutoff_date:
                continue

            summary, content = self._extract_content(entry)
            article = Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=config.name,
                source_type=SourceType.RSS,
                summary=summary,
                content=content,
                published_at=published,
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from RSS: {config.name}")
        return articles

    def _extract_content(self, entry) -> tuple[str, str]:
        """RSS entry から summary と content を取得し、HTMLを除去する"""
        summary = self._strip_html(entry.get("summary", ""))
        # feedparser は content を list[dict] で返す
        content = ""
        for c in entry.get("content", []):
            if isinstance(c, dict) and c.get("value"):
                text = self._strip_html(c["value"])
                if len(text) > len(content):
                    content = text
        # content がなければ summary をフォールバック
        if not content:
            content = summary
        return summary, content

    def _strip_html(self, html: str) -> str:
        """HTMLタグを除去してテキストのみ返す"""
        if not html:
            return ""
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            from dateutil.parser import parse

            dt = parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

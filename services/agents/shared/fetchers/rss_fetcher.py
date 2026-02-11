import asyncio
import logging
from datetime import datetime, timedelta

import feedparser

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

        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        articles = []

        for entry in feed.entries:
            published = self._parse_date(entry.get("published"))
            if published and published < cutoff_date:
                continue

            article = Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=config.name,
                source_type=SourceType.RSS,
                content=entry.get("summary", ""),
                published_at=published,
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from RSS: {config.name}")
        return articles

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            from dateutil.parser import parse

            return parse(date_str)
        except Exception:
            return None

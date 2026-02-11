import logging

from shared.models import Article, SourceConfig, SourceType

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class NewsletterFetcher(BaseFetcher):
    """メルマガ取得（MVP後に実装）"""

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.NEWSLETTER.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        logger.warning("NewsletterFetcher is not yet implemented")
        return []

import logging

from shared.models import Article, SourceConfig, SourceType

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class WebsiteFetcher(BaseFetcher):
    """Webサイト監視（MVP後に実装）"""

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.WEBSITE.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        logger.warning("WebsiteFetcher is not yet implemented")
        return []

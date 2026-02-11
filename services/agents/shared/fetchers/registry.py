import logging
from typing import Optional

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class FetcherRegistry:
    def __init__(self):
        self._fetchers: list[BaseFetcher] = []

    def register(self, fetcher: BaseFetcher):
        self._fetchers.append(fetcher)
        logger.info(f"Registered fetcher: {fetcher.__class__.__name__}")

    def get_fetcher(self, source_type: str) -> Optional[BaseFetcher]:
        for fetcher in self._fetchers:
            if fetcher.supports(source_type):
                return fetcher
        return None

    def get_fetcher_or_raise(self, source_type: str) -> BaseFetcher:
        fetcher = self.get_fetcher(source_type)
        if fetcher is None:
            raise ValueError(f"No fetcher registered for source type: {source_type}")
        return fetcher

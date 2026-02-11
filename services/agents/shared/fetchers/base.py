from abc import ABC, abstractmethod

from shared.models import Article, SourceConfig


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self, config: SourceConfig) -> list[Article]:
        pass

    @abstractmethod
    def supports(self, source_type: str) -> bool:
        pass

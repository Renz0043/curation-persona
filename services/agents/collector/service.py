import asyncio
import logging
from datetime import datetime

from shared.a2a_client import A2AClient
from shared.config import settings
from shared.fetchers.base import BaseFetcher
from shared.fetchers.registry import FetcherRegistry
from shared.firestore_client import FirestoreClient
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ScoredArticle,
    ScoringStatus,
    SourceConfig,
)
from shared.scraper import WebScraper

logger = logging.getLogger(__name__)


class CollectorService:
    """Collector ビジネスロジック"""

    def __init__(
        self,
        firestore: FirestoreClient,
        a2a_client: A2AClient,
        fetcher_registry: FetcherRegistry,
        scraper: WebScraper,
    ):
        self.firestore = firestore
        self.a2a_client = a2a_client
        self.fetcher_registry = fetcher_registry
        self.scraper = scraper

    async def execute(self, user_id: str) -> dict:
        logger.info(f"execute: user_id={user_id}")

        user = await self.firestore.get_user(user_id)
        sources = [
            SourceConfig.model_validate(s)
            for s in user.get("sources", [])
            if s.get("enabled", True)
        ]

        if not sources:
            logger.warning(f"No enabled sources for user: {user_id}")
            return {"status": "success", "articles_total": 0, "collection_id": ""}

        # 全ソースから並列取得
        tasks = [self._fetch_with_error_handling(source) for source in sources]
        results = await asyncio.gather(*tasks)

        all_articles = []
        for articles in results:
            all_articles.extend(articles)

        # URL重複除去
        unique_articles = self._deduplicate(all_articles)

        # meta description + OGP画像 並列取得
        await self.scraper.fetch_meta_all(unique_articles)

        # ScoredArticle に変換
        scored_articles = [
            ScoredArticle(
                **article.model_dump(),
                scoring_status=ScoringStatus.PENDING,
            )
            for article in unique_articles
        ]

        # ArticleCollection 作成・保存
        now = datetime.now()
        collection_id = f"{user_id}_{now.strftime('%Y%m%d_%H%M%S')}"
        collection = ArticleCollection(
            id=collection_id,
            user_id=user_id,
            date=now.strftime("%Y-%m-%d"),
            articles=scored_articles,
            status=CollectionStatus.COLLECTING,
            created_at=now,
        )
        await self.firestore.create_collection(collection)

        # Librarian に score_articles スキル送信
        await self.a2a_client.send_message(
            agent_url=settings.librarian_agent_url,
            skill="score_articles",
            params={"user_id": user_id, "collection_id": collection_id},
        )

        logger.info(
            f"Collection created: {collection_id}, articles: {len(scored_articles)}"
        )

        return {
            "status": "success",
            "articles_total": len(scored_articles),
            "collection_id": collection_id,
        }

    async def _fetch_with_error_handling(self, source: SourceConfig):
        fetcher: BaseFetcher | None = self.fetcher_registry.get_fetcher(
            source.type.value
        )
        if fetcher is None:
            logger.warning(f"No fetcher for source type: {source.type}")
            return []
        try:
            return await fetcher.fetch(source)
        except Exception as e:
            logger.error(f"Failed to fetch from {source.name}: {e}")
            return []

    def _deduplicate(self, articles):
        seen = set()
        unique = []
        for article in articles:
            if article.url not in seen:
                seen.add(article.url)
                unique.append(article)
        return unique

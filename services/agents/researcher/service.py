import logging
from collections.abc import AsyncIterator

from shared.firestore_client import FirestoreClient
from shared.models import ResearchArticleParams, ResearchStatus

from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ResearcherService:
    """Researcher ビジネスロジック"""

    def __init__(
        self,
        firestore: FirestoreClient,
        report_generator: ReportGenerator,
    ):
        self.firestore = firestore
        self.report_generator = report_generator

    async def research(self, params: ResearchArticleParams) -> dict:
        logger.info(
            f"research: collection_id={params.collection_id}, "
            f"article_url={params.article_url}"
        )

        # コレクション取得、対象記事を検索
        collection = await self.firestore.get_collection(params.collection_id)
        article = None
        for a in collection.articles:
            if a.url == params.article_url:
                article = a
                break

        if article is None:
            logger.error(
                f"Article not found: {params.article_url} "
                f"in collection {params.collection_id}"
            )
            return {"status": "error", "message": "Article not found"}

        # ステータスを RESEARCHING に更新
        await self.firestore.update_article_research_status(
            params.collection_id, params.article_url, ResearchStatus.RESEARCHING
        )

        try:
            # 高評価記事コンテキスト取得
            related_articles = await self.firestore.get_high_rated_articles(
                params.user_id
            )

            # レポート生成
            report = await self.report_generator.generate(article, related_articles)

            # Firestoreに保存
            await self.firestore.update_article_research(
                params.collection_id,
                params.article_url,
                deep_dive_report=report,
                research_status=ResearchStatus.COMPLETED,
            )

            logger.info(f"Research completed for: {params.article_url}")
            return {"status": "success", "article_url": params.article_url}
        except Exception as e:
            logger.error(f"Research failed for {params.article_url}: {e}")
            await self.firestore.update_article_research_status(
                params.collection_id, params.article_url, ResearchStatus.FAILED
            )
            raise

    async def research_stream(
        self, params: ResearchArticleParams
    ) -> AsyncIterator[str]:
        logger.info(
            f"research_stream: collection_id={params.collection_id}, "
            f"article_url={params.article_url}"
        )

        collection = await self.firestore.get_collection(params.collection_id)
        article = None
        for a in collection.articles:
            if a.url == params.article_url:
                article = a
                break

        if article is None:
            raise ValueError(
                f"Article not found: {params.article_url} "
                f"in collection {params.collection_id}"
            )

        await self.firestore.update_article_research_status(
            params.collection_id, params.article_url, ResearchStatus.RESEARCHING
        )

        try:
            related_articles = await self.firestore.get_high_rated_articles(
                params.user_id
            )

            full_report: list[str] = []
            async for chunk in self.report_generator.generate_stream(
                article, related_articles
            ):
                full_report.append(chunk)
                yield chunk

            await self.firestore.update_article_research(
                params.collection_id,
                params.article_url,
                deep_dive_report="".join(full_report),
                research_status=ResearchStatus.COMPLETED,
            )
            logger.info(f"Research stream completed for: {params.article_url}")
        except Exception as e:
            logger.error(f"Research stream failed for {params.article_url}: {e}")
            await self.firestore.update_article_research_status(
                params.collection_id, params.article_url, ResearchStatus.FAILED
            )
            raise

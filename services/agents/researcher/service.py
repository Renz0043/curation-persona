import logging
from collections.abc import AsyncIterator
from datetime import datetime

from shared.firestore_client import FirestoreClient
from shared.models import (
    ResearchArticleParams,
    ResearchStatus,
    ScoredArticle,
    ScoringStatus,
    SourceType,
)
from shared.scraper import WebScraper

from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class ResearcherService:
    """Researcher ビジネスロジック"""

    def __init__(
        self,
        firestore: FirestoreClient,
        report_generator: ReportGenerator,
        scraper: WebScraper | None = None,
    ):
        self.firestore = firestore
        self.report_generator = report_generator
        self.scraper = scraper or WebScraper()

    async def create_bookmark(self, user_id: str, url: str) -> dict:
        """ブックマーク記事を保存し、深掘りレポートを生成する。"""
        logger.info(f"create_bookmark: user_id={user_id}, url={url}")

        # 1. bookmark コレクション確保
        collection_id = f"bm_{user_id}"
        await self.firestore.ensure_bookmark_collection(user_id)

        # 2. WebScraper でコンテンツ取得
        article = await self._scrape_bookmark(url)

        # 3. Firestore に記事保存
        await self.firestore.save_bookmark_article(collection_id, user_id, article)

        # 4. research() を実行
        params = ResearchArticleParams(
            user_id=user_id,
            collection_id=collection_id,
            article_url=url,
        )
        await self.research(params)
        return {"status": "completed", "article_url": url}

    async def _scrape_bookmark(self, url: str) -> ScoredArticle:
        """URLからコンテンツを取得し ScoredArticle を生成する。"""
        title = url
        content = None
        meta_description = None

        try:
            content = await self.scraper.scrape(url)
            meta_description = await self.scraper.fetch_meta_description(url)
            if content:
                # 本文の先頭からタイトルを推定（最初の非空行）
                for line in content.split("\n"):
                    stripped = line.strip()
                    if stripped:
                        title = stripped[:100]
                        break
        except Exception:
            logger.warning(f"ブックマークスクレイピング失敗: {url}", exc_info=True)

        return ScoredArticle(
            title=title,
            url=url,
            source="bookmark",
            source_type=SourceType.BOOKMARK,
            content=content,
            meta_description=meta_description,
            scoring_status=ScoringStatus.SCORED,
            relevance_score=1.0,
            relevance_reason="ユーザーが手動でブックマーク",
            is_pickup=True,
            research_status=ResearchStatus.PENDING,
        )

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

            # 異業種フィードバック生成（ピックアップ記事のみ）
            cross_industry_feedback = None
            if article.is_pickup:
                cross_industry_feedback = (
                    await self.report_generator.generate_cross_industry_feedback(
                        article, report
                    )
                )

            # Firestoreに保存
            await self.firestore.update_article_research(
                params.collection_id,
                params.article_url,
                deep_dive_report=report,
                research_status=ResearchStatus.COMPLETED,
                cross_industry_feedback=cross_industry_feedback,
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

            report = "".join(full_report)

            # 異業種フィードバック生成（ピックアップ記事のみ）
            cross_industry_feedback = None
            if article.is_pickup:
                cross_industry_feedback = (
                    await self.report_generator.generate_cross_industry_feedback(
                        article, report
                    )
                )

            await self.firestore.update_article_research(
                params.collection_id,
                params.article_url,
                deep_dive_report=report,
                research_status=ResearchStatus.COMPLETED,
                cross_industry_feedback=cross_industry_feedback,
            )
            logger.info(f"Research stream completed for: {params.article_url}")
        except Exception as e:
            logger.error(f"Research stream failed for {params.article_url}: {e}")
            await self.firestore.update_article_research_status(
                params.collection_id, params.article_url, ResearchStatus.FAILED
            )
            raise

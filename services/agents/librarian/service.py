import asyncio
import logging
from typing import Optional

from shared.config import settings
from shared.firestore_client import FirestoreClient
from shared.gemini_client import GeminiClient
from shared.models import CollectionStatus, ResearchStatus, ScoringStatus
from shared.scraper import WebScraper

from .scorer import ArticleScorer

logger = logging.getLogger(__name__)

PROFILE_PROMPT_TEMPLATE = """\
以下はユーザーが高評価をつけた記事の一覧です。
これらの記事からユーザーの興味・関心を分析し、興味プロファイルを日本語で生成してください。

## 高評価記事一覧
{articles_text}

## 指示
- ユーザーの主要な関心領域を3〜5つ特定してください
- 各領域について具体的なキーワードやトピックを挙げてください
- 200文字以内で簡潔にまとめてください
"""


class LibrarianService:
    """Librarian ビジネスロジック"""

    def __init__(
        self,
        firestore: FirestoreClient,
        gemini_client: GeminiClient,
        scorer: ArticleScorer,
        scraper: WebScraper,
    ):
        self.firestore = firestore
        self.gemini_client = gemini_client
        self.scorer = scorer
        self.scraper = scraper

    async def score_collection(self, user_id: str, collection_id: str) -> dict:
        logger.info(f"score_collection: user_id={user_id}, collection_id={collection_id}")

        collection = await self.firestore.get_collection(collection_id)
        await self.firestore.update_collection_status(collection_id, CollectionStatus.SCORING)

        try:
            interest_profile = await self._ensure_interest_profile(user_id)
            articles = collection.articles

            if not interest_profile:
                # コールドスタート: 全記事にデフォルトスコアを設定
                logger.info("コールドスタート: デフォルトスコアを設定")
                for article in articles:
                    article.relevance_score = 0.5
                    article.relevance_reason = "評価データ蓄積中のため、デフォルトスコアを設定しました"
                    article.scoring_status = ScoringStatus.SCORED
            else:
                # 通常フロー: LLMで並列スコアリング
                tasks = [
                    self.scorer.calculate_score(
                        article_text=f"{article.title}\n{article.content or ''}",
                        interest_profile=interest_profile,
                    )
                    for article in articles
                ]
                results = await asyncio.gather(*tasks)

                for article, result in zip(articles, results):
                    article.relevance_score = result.score
                    article.relevance_reason = result.reason
                    article.scoring_status = ScoringStatus.SCORED

            # スコア降順ソート → 上位N件をピックアップ
            articles.sort(key=lambda a: a.relevance_score, reverse=True)
            pickup_count = settings.pickup_count
            for i, article in enumerate(articles):
                if i < pickup_count:
                    article.is_pickup = True
                    article.research_status = ResearchStatus.PENDING

            # 上位記事のコンテンツ補完（スクレイピング）
            await self.scraper.scrape_articles(
                articles,
                max_count=settings.scrape_max_count,
                delay=settings.scrape_delay_sec,
            )

            await self.firestore.update_collection_articles(collection_id, articles)

            # title_embedding を一括生成
            await self._generate_title_embeddings(collection_id, articles)

            await self.firestore.update_collection_status(
                collection_id, CollectionStatus.COMPLETED
            )

            scored_count = len(articles)
            pickup_articles = [a for a in articles if a.is_pickup]
            logger.info(f"スコアリング完了: {scored_count}件, ピックアップ: {len(pickup_articles)}件")

            return {
                "status": "success",
                "scored_count": scored_count,
                "collection_id": collection_id,
                "pickup_count": len(pickup_articles),
            }
        except Exception as e:
            logger.error(f"score_collection failed: {e}")
            await self.firestore.update_collection_status(
                collection_id, CollectionStatus.FAILED
            )
            raise

    async def _generate_title_embeddings(
        self, collection_id: str, articles: list
    ):
        """全記事の title_embedding を一括生成して Firestore に保存する。"""
        if not articles:
            return
        try:
            texts = [article.title for article in articles]
            embeddings = await self.gemini_client.embed_content(texts)
            article_embeddings = [
                (article.url, embedding)
                for article, embedding in zip(articles, embeddings)
            ]
            await self.firestore.update_article_embeddings(
                collection_id, article_embeddings
            )
            logger.info(f"title_embedding 生成完了: {len(articles)}件")
        except Exception as e:
            logger.warning(f"title_embedding 生成に失敗（スコアリングは完了）: {e}")

    async def _ensure_interest_profile(self, user_id: str) -> Optional[str]:
        user = await self.firestore.get_user(user_id)
        existing_profile = user.get("interestProfile")
        profile_updated_at = user.get("interestProfileUpdatedAt")

        # 新規評価がある場合はプロファイル再生成
        needs_regeneration = not existing_profile
        if existing_profile and profile_updated_at:
            has_new = await self.firestore.has_new_ratings_since(user_id, profile_updated_at)
            if has_new:
                needs_regeneration = True

        if not needs_regeneration:
            return existing_profile

        # 高評価記事を取得
        high_rated = await self.firestore.get_high_rated_articles(
            user_id, min_rating=settings.high_rating_threshold
        )

        if len(high_rated) < settings.min_ratings_for_scoring:
            logger.info(
                f"高評価記事が不足 ({len(high_rated)}/{settings.min_ratings_for_scoring}): "
                f"コールドスタートモード"
            )
            return None

        # プロファイル生成
        articles_text = "\n".join(
            f"- {a['title']} (評価: {a['user_rating']})"
            + (f" コメント: {a['user_comment']}" if a.get("user_comment") else "")
            for a in high_rated
        )
        prompt = PROFILE_PROMPT_TEMPLATE.format(articles_text=articles_text)
        profile = await self.gemini_client.generate_text(prompt)

        await self.firestore.update_interest_profile(user_id, profile)
        logger.info(f"興味プロファイル生成完了: user_id={user_id}")

        return profile

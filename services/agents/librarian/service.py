import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from shared.config import settings
from shared.firestore_client import FirestoreClient
from shared.gemini_client import GeminiClient
from shared.models import CollectionStatus, ResearchStatus, ScoringStatus
from shared.scraper import WebScraper

from .scorer import ArticleScorer

logger = logging.getLogger(__name__)

PREFILTER_PROMPT_TEMPLATE = """\
あなたは記事キュレーションAIです。
ユーザーの興味プロファイルに基づいて、以下の記事一覧からユーザーが読みたいと思う記事を選んでください。

## ユーザー興味プロファイル
{interest_profile}

## 記事一覧（ソース: {source_name}）
{articles_list}

## 指示
上記の記事からユーザーの興味に関連する記事を最大{max_count}件選んでください。
以下のJSON形式で、選んだ記事のインデックス番号（0始まり）の配列を返してください:
{{"selected": [0, 2, 5]}}
"""

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

            # プレフィルタ: ソース毎にタイトル+メタで最大N件に絞り込み
            if interest_profile:
                articles = await self._prefilter_by_source(
                    articles, interest_profile, settings.max_articles_per_source
                )
                logger.info(f"プレフィルタ後: {len(articles)}件")

            if not interest_profile:
                # コールドスタート: 全記事にデフォルトスコアを設定
                logger.info("コールドスタート: デフォルトスコアを設定")
                for article in articles:
                    article.relevance_score = 0.5
                    article.relevance_reason = "評価データ蓄積中のため、デフォルトスコアを設定しました"
                    article.scoring_status = ScoringStatus.SCORED
            else:
                # 通常フロー: タイトル+メタデータでLLM並列スコアリング
                tasks = [
                    self.scorer.calculate_score(
                        article_text=f"{article.title}\n{article.meta_description or ''}",
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
            texts = [
                f"{article.title}\n{article.meta_description}"
                if article.meta_description
                else article.title
                for article in articles
            ]
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

    async def _prefilter_by_source(
        self, articles: list, interest_profile: str, max_per_source: int
    ) -> list:
        """ソース毎にタイトル+メタで関連度の高い記事に絞り込む。"""
        # ソース毎にグルーピング
        by_source: dict[str, list] = defaultdict(list)
        for article in articles:
            by_source[article.source].append(article)

        # 上限以下のソースはスキップ、超えたソースだけLLMフィルタ
        tasks = []
        source_names = []
        for source_name, source_articles in by_source.items():
            if len(source_articles) <= max_per_source:
                tasks.append(None)
            else:
                tasks.append(
                    self._prefilter_one_source(
                        source_name, source_articles, interest_profile, max_per_source
                    )
                )
            source_names.append(source_name)

        # LLMフィルタを並列実行
        results = await asyncio.gather(
            *[t for t in tasks if t is not None]
        )

        # 結果を組み立て
        result_iter = iter(results)
        filtered = []
        for source_name, task in zip(source_names, tasks):
            if task is None:
                filtered.extend(by_source[source_name])
            else:
                filtered.extend(next(result_iter))

        return filtered

    async def _prefilter_one_source(
        self,
        source_name: str,
        articles: list,
        interest_profile: str,
        max_count: int,
    ) -> list:
        """1ソース分の記事をプレフィルタする。"""
        articles_list = "\n".join(
            f"[{i}] {a.title}"
            + (f" — {a.meta_description[:120]}" if a.meta_description else "")
            for i, a in enumerate(articles)
        )
        prompt = PREFILTER_PROMPT_TEMPLATE.format(
            interest_profile=interest_profile,
            source_name=source_name,
            articles_list=articles_list,
            max_count=max_count,
        )

        try:
            data = await self.gemini_client.generate_json(prompt)
            selected_indices = data.get("selected", [])
            valid_indices = [
                i for i in selected_indices
                if isinstance(i, int) and 0 <= i < len(articles)
            ]
            if valid_indices:
                logger.info(
                    f"プレフィルタ [{source_name}]: {len(articles)}件 → {len(valid_indices)}件"
                )
                return [articles[i] for i in valid_indices]
        except Exception as e:
            logger.warning(f"プレフィルタ失敗 [{source_name}]: {e}")

        # フォールバック: 新着順で上限件数
        articles.sort(
            key=lambda a: a.published_at or datetime.min,
            reverse=True,
        )
        return articles[:max_count]

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

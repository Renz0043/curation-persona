import logging
from datetime import datetime
from typing import Optional

from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchStatus,
    ScoredArticle,
    generate_article_id,
)

logger = logging.getLogger(__name__)

BATCH_LIMIT = 500


def _chunked(lst: list, n: int):
    """リストをn個ずつのチャンクに分割する"""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class FirestoreClient:
    """Firestore クライアント

    記事データはトップレベル articles コレクションに分離して保存し、
    アプリ層では ArticleCollection.articles として透過的にアクセスできるようにする。
    """

    def __init__(self):
        from shared.config import settings

        try:
            from google.cloud import firestore

            self.db = firestore.AsyncClient(
                project=settings.google_cloud_project,
                database=settings.firestore_database,
            )
            logger.info("FirestoreClient initialized")
        except Exception as e:
            logger.warning(f"Firestore unavailable, using stub mode: {e}")
            self.db = None

    async def get_user_by_api_key(self, api_key: str) -> Optional[dict]:
        """API キーからユーザーを検索する。"""
        if self.db is None:
            logger.info(f"[STUB] get_user_by_api_key(***)")
            return {"user_id": "stub_user"}
        query = self.db.collection("users").where("api_key", "==", api_key).limit(1)
        async for doc in query.stream():
            data = doc.to_dict()
            data["user_id"] = doc.id
            return data
        return None

    async def ensure_bookmark_collection(self, user_id: str) -> str:
        """ブックマーク用コレクションを確保する。既存なら何もしない。"""
        collection_id = f"bm_{user_id}"
        if self.db is None:
            logger.info(f"[STUB] ensure_bookmark_collection({user_id})")
            return collection_id
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        if not doc.exists:
            await doc_ref.set(
                {
                    "id": collection_id,
                    "user_id": user_id,
                    "date": "",
                    "status": CollectionStatus.COMPLETED.value,
                    "created_at": datetime.now(),
                }
            )
            logger.info(f"Bookmark collection created: {collection_id}")
        return collection_id

    async def save_bookmark_article(
        self, collection_id: str, user_id: str, article: ScoredArticle
    ):
        """ブックマーク記事を articles コレクションに保存する。"""
        article_id = generate_article_id(collection_id, article.url)
        article.id = article_id
        if self.db is None:
            logger.info(f"[STUB] save_bookmark_article({article_id})")
            return
        article_data = article.model_dump(mode="json")
        article_data["collection_id"] = collection_id
        article_data["user_id"] = user_id
        await self.db.collection("articles").document(article_id).set(article_data)

    async def get_user(self, user_id: str) -> dict:
        if self.db is None:
            logger.info(f"[STUB] get_user({user_id})")
            return {"user_id": user_id, "sources": []}
        doc = await self.db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else {}

    async def create_collection(self, collection: ArticleCollection):
        if self.db is None:
            logger.info(f"[STUB] create_collection({collection.id})")
            return

        # コレクションドキュメント保存（articles 配列は含めない）
        collection_data = collection.model_dump(mode="json")
        collection_data.pop("articles", None)
        await self.db.collection("collections").document(collection.id).set(
            collection_data
        )

        # 記事を articles コレクションにバッチ書き込み
        if collection.articles:
            for chunk in _chunked(collection.articles, BATCH_LIMIT):
                batch = self.db.batch()
                for article in chunk:
                    article_id = generate_article_id(collection.id, article.url)
                    article.id = article_id
                    article_data = article.model_dump(mode="json")
                    article_data["collection_id"] = collection.id
                    article_data["user_id"] = collection.user_id
                    doc_ref = self.db.collection("articles").document(article_id)
                    batch.set(doc_ref, article_data)
                await batch.commit()

    async def get_collection(self, collection_id: str) -> ArticleCollection:
        if self.db is None:
            logger.info(f"[STUB] get_collection({collection_id})")
            return ArticleCollection(
                id=collection_id,
                user_id="stub",
                date="2025-01-01",
                articles=[],
                status=CollectionStatus.COMPLETED,
                created_at=datetime.now(),
            )
        doc = await self.db.collection("collections").document(collection_id).get()
        data = doc.to_dict()
        articles = await self._get_articles_for_collection(collection_id)
        data["articles"] = articles
        return ArticleCollection.model_validate(data)

    async def _get_articles_for_collection(
        self, collection_id: str
    ) -> list[ScoredArticle]:
        """コレクションに属する記事を取得する"""
        articles = []
        query = self.db.collection("articles").where(
            "collection_id", "==", collection_id
        )
        async for doc in query.stream():
            data = doc.to_dict()
            data.pop("collection_id", None)
            data.pop("user_id", None)
            articles.append(ScoredArticle.model_validate(data))
        return articles

    async def update_collection_articles(
        self, collection_id: str, articles: list[ScoredArticle]
    ):
        if self.db is None:
            logger.info(f"[STUB] update_collection_articles({collection_id})")
            return

        # コレクションから user_id を取得
        col_doc = await self.db.collection("collections").document(collection_id).get()
        user_id = col_doc.to_dict()["user_id"]

        for chunk in _chunked(articles, BATCH_LIMIT):
            batch = self.db.batch()
            for article in chunk:
                article_id = generate_article_id(collection_id, article.url)
                article.id = article_id
                article_data = article.model_dump(mode="json")
                article_data["collection_id"] = collection_id
                article_data["user_id"] = user_id
                doc_ref = self.db.collection("articles").document(article_id)
                batch.set(doc_ref, article_data)
            await batch.commit()

    async def update_article_research_status(
        self,
        collection_id: str,
        article_url: str,
        research_status: ResearchStatus,
    ):
        if self.db is None:
            logger.info(f"[STUB] update_article_research_status({collection_id})")
            return
        article_id = generate_article_id(collection_id, article_url)
        await self.db.collection("articles").document(article_id).update(
            {"research_status": research_status.value}
        )

    async def update_article_research(
        self,
        collection_id: str,
        article_url: str,
        deep_dive_report: str,
        research_status: Optional[ResearchStatus] = None,
    ):
        if self.db is None:
            logger.info(f"[STUB] update_article_research({collection_id})")
            return
        article_id = generate_article_id(collection_id, article_url)
        update_data = {"deep_dive_report": deep_dive_report}
        if research_status:
            update_data["research_status"] = research_status.value
        await self.db.collection("articles").document(article_id).update(update_data)

    async def get_latest_collection(
        self, user_id: str, date: Optional[str] = None
    ) -> Optional[ArticleCollection]:
        """ユーザーの最新コレクションを取得する。

        Args:
            user_id: ユーザーID
            date: YYYY-MM-DD 形式の日付。指定時はその日のコレクションを返す。
        """
        if self.db is None:
            logger.info(f"[STUB] get_latest_collection({user_id}, date={date})")
            return None
        query = self.db.collection("collections").where("user_id", "==", user_id)
        if date:
            query = query.where("date", "==", date)
        query = query.order_by("created_at", direction="DESCENDING").limit(1)
        async for doc in query.stream():
            data = doc.to_dict()
            articles = await self._get_articles_for_collection(data["id"])
            data["articles"] = articles
            return ArticleCollection.model_validate(data)
        return None

    async def update_collection_status(
        self, collection_id: str, status: CollectionStatus
    ):
        if self.db is None:
            logger.info(f"[STUB] update_collection_status({collection_id})")
            return
        await self.db.collection("collections").document(collection_id).update(
            {"status": status.value}
        )

    async def get_high_rated_articles(
        self, user_id: str, min_rating: int = 4
    ) -> list[dict]:
        if self.db is None:
            logger.info(f"[STUB] get_high_rated_articles({user_id})")
            return []
        query = (
            self.db.collection("articles")
            .where("user_id", "==", user_id)
            .where("user_rating", ">=", min_rating)
        )
        high_rated = []
        async for doc in query.stream():
            data = doc.to_dict()
            high_rated.append(
                {
                    "title": data["title"],
                    "url": data["url"],
                    "content": (data.get("content") or "")[:300],
                    "user_rating": data["user_rating"],
                    "user_comment": data.get("user_comment"),
                }
            )
        return high_rated

    async def update_interest_profile(self, user_id: str, profile: str):
        if self.db is None:
            logger.info(f"[STUB] update_interest_profile({user_id})")
            return
        from google.cloud import firestore

        await self.db.collection("users").document(user_id).update(
            {
                "interestProfile": profile,
                "interestProfileUpdatedAt": firestore.SERVER_TIMESTAMP,
            }
        )

    async def update_article_feedback(
        self,
        collection_id: str,
        article_url: str,
        rating: int,
        comment: Optional[str] = None,
    ):
        if self.db is None:
            logger.info(
                f"[STUB] update_article_feedback({collection_id}, {article_url})"
            )
            return
        article_id = generate_article_id(collection_id, article_url)
        update_data = {"user_rating": rating}
        if comment is not None:
            update_data["user_comment"] = comment
        await self.db.collection("articles").document(article_id).update(update_data)

    async def update_article_embeddings(
        self,
        collection_id: str,
        article_embeddings: list[tuple[str, list[float]]],
    ):
        """記事の title_embedding をバッチ更新する。

        Args:
            collection_id: コレクションID
            article_embeddings: [(article_url, embedding), ...] のリスト
        """
        if self.db is None:
            logger.info(f"[STUB] update_article_embeddings({collection_id})")
            return

        from google.cloud.firestore_v1.vector import Vector

        for chunk in _chunked(article_embeddings, BATCH_LIMIT):
            batch = self.db.batch()
            for article_url, embedding in chunk:
                article_id = generate_article_id(collection_id, article_url)
                doc_ref = self.db.collection("articles").document(article_id)
                batch.update(doc_ref, {"title_embedding": Vector(embedding)})
            await batch.commit()

    async def find_similar_articles(
        self,
        user_id: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict]:
        """ベクトル検索で類似記事を取得する。"""
        if self.db is None:
            logger.info(f"[STUB] find_similar_articles({user_id})")
            return []

        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        from google.cloud.firestore_v1.vector import Vector

        query = self.db.collection("articles").where("user_id", "==", user_id)
        vector_query = query.find_nearest(
            vector_field="title_embedding",
            query_vector=Vector(query_embedding),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit,
            distance_result_field="vector_distance",
        )
        results = []
        async for doc in vector_query.stream():
            data = doc.to_dict()
            results.append(
                {
                    "title": data.get("title"),
                    "url": data.get("url"),
                    "source": data.get("source"),
                    "relevance_score": data.get("relevance_score", 0),
                    "collection_id": data.get("collection_id"),
                    "vector_distance": data.get("vector_distance"),
                }
            )
        return results

    async def has_new_ratings_since(self, user_id: str, since: datetime) -> bool:
        if self.db is None:
            return False

        # 指定日時以降のコレクションIDを取得
        collections_query = (
            self.db.collection("collections")
            .where("user_id", "==", user_id)
            .where("created_at", ">=", since)
            .limit(10)
        )
        collection_ids = []
        async for doc in collections_query.stream():
            collection_ids.append(doc.id)

        if not collection_ids:
            return False

        # それらのコレクションに属する記事で評価があるか確認
        articles_query = (
            self.db.collection("articles")
            .where("collection_id", "in", collection_ids)
            .where("user_rating", ">=", 1)
            .limit(1)
        )
        async for _ in articles_query.stream():
            return True
        return False

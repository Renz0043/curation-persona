import logging
from datetime import datetime
from typing import Optional

from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchStatus,
    ScoredArticle,
)

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Firestore クライアント（Phase 1: get_user, create_collection のみ実装、他はシグネチャ）"""

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
        await self.db.collection("collections").document(collection.id).set(
            collection.model_dump(mode="json")
        )

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
        return ArticleCollection.model_validate(doc.to_dict())

    async def update_collection_articles(
        self, collection_id: str, articles: list[ScoredArticle]
    ):
        if self.db is None:
            logger.info(f"[STUB] update_collection_articles({collection_id})")
            return
        await self.db.collection("collections").document(collection_id).update(
            {"articles": [a.model_dump(mode="json") for a in articles]}
        )

    async def update_article_research_status(
        self,
        collection_id: str,
        article_url: str,
        research_status: ResearchStatus,
    ):
        if self.db is None:
            logger.info(f"[STUB] update_article_research_status({collection_id})")
            return
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        data = doc.to_dict()
        for article in data["articles"]:
            if article["url"] == article_url:
                article["research_status"] = research_status.value
                break
        await doc_ref.update({"articles": data["articles"]})

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
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        data = doc.to_dict()
        for article in data["articles"]:
            if article["url"] == article_url:
                article["deep_dive_report"] = deep_dive_report
                if research_status:
                    article["research_status"] = research_status.value
                break
        await doc_ref.update({"articles": data["articles"]})

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
        collections = (
            self.db.collection("collections")
            .where("user_id", "==", user_id)
            .order_by("created_at", direction="DESCENDING")
            .limit(30)
        )
        high_rated = []
        async for doc in collections.stream():
            data = doc.to_dict()
            for article in data.get("articles", []):
                if article.get("user_rating") and article["user_rating"] >= min_rating:
                    high_rated.append(
                        {
                            "title": article["title"],
                            "url": article["url"],
                            "content": article.get("content", "")[:300],
                            "user_rating": article["user_rating"],
                            "user_comment": article.get("user_comment"),
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

    async def has_new_ratings_since(self, user_id: str, since: datetime) -> bool:
        if self.db is None:
            return False
        collections = (
            self.db.collection("collections")
            .where("user_id", "==", user_id)
            .where("created_at", ">=", since)
            .limit(10)
        )
        async for doc in collections.stream():
            data = doc.to_dict()
            for article in data.get("articles", []):
                if article.get("user_rating") is not None:
                    return True
        return False

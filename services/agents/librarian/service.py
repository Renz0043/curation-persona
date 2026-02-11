import logging

logger = logging.getLogger(__name__)


class LibrarianService:
    """Librarian ビジネスロジック（Phase 1: スタブ）"""

    async def score_collection(self, user_id: str, collection_id: str) -> dict:
        logger.info(
            f"[STUB] LibrarianService.score_collection("
            f"user_id={user_id}, collection_id={collection_id})"
        )
        return {
            "status": "success",
            "scored_count": 0,
            "collection_id": collection_id,
        }

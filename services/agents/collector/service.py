import logging

logger = logging.getLogger(__name__)


class CollectorService:
    """Collector ビジネスロジック（Phase 1: スタブ）"""

    async def execute(self, user_id: str) -> dict:
        logger.info(f"[STUB] CollectorService.execute(user_id={user_id})")
        return {
            "status": "success",
            "articles_total": 0,
            "collection_id": f"collection_{user_id}_stub",
        }

import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API クライアント（Phase 1: スタブ実装）"""

    def __init__(self, model: str = "flash"):
        self.model = model
        logger.info(f"GeminiClient initialized with model={model} (stub mode)")

    async def generate_text(self, prompt: str) -> str:
        logger.info(f"[STUB] generate_text called (model={self.model})")
        return "これはスタブレスポンスです。Phase 2で実装されます。"

    async def generate_json(self, prompt: str) -> dict:
        logger.info(f"[STUB] generate_json called (model={self.model})")
        return {"score": 0.5, "reason": "スタブスコア"}

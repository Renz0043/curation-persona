import json
import logging

from google import genai

from shared.config import settings
from shared.retry import with_retry

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API クライアント"""

    def __init__(self, model: str = "flash"):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        if model == "pro":
            self.model_name = settings.gemini_pro_model
        else:
            self.model_name = settings.gemini_flash_model
        self.model = model
        logger.info(f"GeminiClient initialized with model={self.model_name}")

    @with_retry
    async def generate_text(self, prompt: str) -> str:
        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

    @with_retry
    async def generate_json(self, prompt: str) -> dict:
        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)

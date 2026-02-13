import json
import logging
from collections.abc import AsyncIterator

from google import genai

from shared.config import settings
from shared.retry import with_retry

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API クライアント"""

    def __init__(self, model: str = "flash"):
        if settings.gemini_api_key:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        else:
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.gemini_location,
            )
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

    async def generate_text_stream(self, prompt: str) -> AsyncIterator[str]:
        """テキストをストリーミング生成する。リトライなし。"""
        response = await self._client.aio.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    @with_retry
    async def embed_content(self, texts: list[str]) -> list[list[float]]:
        """テキストリストの Embedding を生成する。"""
        response = await self._client.aio.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=texts,
            config={"output_dimensionality": settings.embedding_dimensions},
        )
        return [e.values for e in response.embeddings]

    @with_retry
    async def generate_json(self, prompt: str) -> dict:
        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return json.loads(response.text)

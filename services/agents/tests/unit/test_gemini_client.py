from unittest.mock import AsyncMock, MagicMock, patch

from shared.gemini_client import GeminiClient


class Test_GeminiClient:
    @patch("shared.gemini_client.genai.Client")
    def test_flashモデルで初期化される(self, mock_genai_client):
        client = GeminiClient("flash")
        assert client.model_name == "gemini-2.5-flash"
        assert client.model == "flash"
        mock_genai_client.assert_called_once()

    @patch("shared.gemini_client.genai.Client")
    def test_proモデルで初期化される(self, mock_genai_client):
        client = GeminiClient("pro")
        assert client.model_name == "gemini-2.5-pro"
        assert client.model == "pro"

    @patch("shared.gemini_client.genai.Client")
    async def test_generate_textがテキストを返す(self, mock_genai_client):
        mock_response = MagicMock()
        mock_response.text = "生成されたテキスト"

        mock_aio = AsyncMock()
        mock_aio.models.generate_content.return_value = mock_response
        mock_genai_client.return_value.aio = mock_aio

        client = GeminiClient("flash")
        result = await client.generate_text("テストプロンプト")

        assert result == "生成されたテキスト"
        mock_aio.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="テストプロンプト",
        )

    @patch("shared.gemini_client.genai.Client")
    async def test_generate_jsonがdictを返す(self, mock_genai_client):
        mock_response = MagicMock()
        mock_response.text = '{"score": 0.8, "reason": "関連性が高い"}'

        mock_aio = AsyncMock()
        mock_aio.models.generate_content.return_value = mock_response
        mock_genai_client.return_value.aio = mock_aio

        client = GeminiClient("flash")
        result = await client.generate_json("テストプロンプト")

        assert result == {"score": 0.8, "reason": "関連性が高い"}
        mock_aio.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="テストプロンプト",
            config={"response_mime_type": "application/json"},
        )

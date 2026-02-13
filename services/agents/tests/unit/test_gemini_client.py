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

    @patch("shared.gemini_client.genai.Client")
    async def test_generate_text_streamがチャンクを順次返す(self, mock_genai_client):
        chunk1 = MagicMock()
        chunk1.text = "こんにちは"
        chunk2 = MagicMock()
        chunk2.text = "世界"
        chunk3 = MagicMock()
        chunk3.text = "！"

        async def mock_stream():
            for c in [chunk1, chunk2, chunk3]:
                yield c

        mock_aio = AsyncMock()
        mock_aio.models.generate_content_stream.return_value = mock_stream()
        mock_genai_client.return_value.aio = mock_aio

        client = GeminiClient("flash")
        chunks = [c async for c in client.generate_text_stream("テストプロンプト")]

        assert chunks == ["こんにちは", "世界", "！"]
        mock_aio.models.generate_content_stream.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="テストプロンプト",
        )

    @patch("shared.gemini_client.genai.Client")
    async def test_generate_text_streamでtextがNoneのチャンクはスキップされる(
        self, mock_genai_client
    ):
        chunk1 = MagicMock()
        chunk1.text = "有効"
        chunk_none = MagicMock()
        chunk_none.text = None
        chunk2 = MagicMock()
        chunk2.text = "テキスト"

        async def mock_stream():
            for c in [chunk1, chunk_none, chunk2]:
                yield c

        mock_aio = AsyncMock()
        mock_aio.models.generate_content_stream.return_value = mock_stream()
        mock_genai_client.return_value.aio = mock_aio

        client = GeminiClient("flash")
        chunks = [c async for c in client.generate_text_stream("テスト")]

        assert chunks == ["有効", "テキスト"]

    @patch("shared.gemini_client.genai.Client")
    async def test_embed_contentがEmbeddingリストを返す(self, mock_genai_client):
        mock_emb1 = MagicMock()
        mock_emb1.values = [0.1, 0.2, 0.3]
        mock_emb2 = MagicMock()
        mock_emb2.values = [0.4, 0.5, 0.6]

        mock_response = MagicMock()
        mock_response.embeddings = [mock_emb1, mock_emb2]

        mock_aio = AsyncMock()
        mock_aio.models.embed_content.return_value = mock_response
        mock_genai_client.return_value.aio = mock_aio

        client = GeminiClient("flash")
        result = await client.embed_content(["テスト1", "テスト2"])

        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_aio.models.embed_content.assert_called_once_with(
            model="text-embedding-004",
            contents=["テスト1", "テスト2"],
            config={"output_dimensionality": 768},
        )

from unittest.mock import AsyncMock

from librarian.scorer import ArticleScorer
from shared.gemini_client import GeminiClient


class Test_ArticleScorer:
    def _make_scorer(self, gemini_client=None):
        if gemini_client is None:
            client = GeminiClient.__new__(GeminiClient)
            client.generate_json = AsyncMock(
                return_value={"score": 0.5, "reason": "テスト"}
            )
        else:
            client = gemini_client
        return ArticleScorer(client)

    async def test_プロファイルなしでデフォルトスコアを返す(self):
        scorer = self._make_scorer()
        result = await scorer.calculate_score(
            article_text="Test article",
            interest_profile="",
        )
        assert result.score == 0.5
        assert "デフォルトスコア" in result.reason

    async def test_プロファイルありでLLMスコアを返す(self, mock_gemini_client):
        mock_gemini_client.generate_json.return_value = {
            "score": 0.85,
            "reason": "AIエージェント設計に関連する記事",
        }
        scorer = ArticleScorer(mock_gemini_client)
        result = await scorer.calculate_score(
            article_text="AI Agent の新設計パターン",
            interest_profile="ユーザーはAIエージェント設計に強い関心がある",
        )
        assert result.score == 0.85
        assert "AIエージェント" in result.reason
        mock_gemini_client.generate_json.assert_called_once()

    async def test_スコアが0から1の範囲にクランプされる(self, mock_gemini_client):
        mock_gemini_client.generate_json.return_value = {
            "score": 1.5,
            "reason": "範囲外スコア",
        }
        scorer = ArticleScorer(mock_gemini_client)
        result = await scorer.calculate_score(
            article_text="テスト記事",
            interest_profile="テストプロファイル",
        )
        assert result.score == 1.0

    async def test_JSONパースエラー時にスコア0を返す(self, mock_gemini_client):
        mock_gemini_client.generate_json.side_effect = ValueError("JSONパースエラー")
        scorer = ArticleScorer(mock_gemini_client)
        result = await scorer.calculate_score(
            article_text="テスト記事",
            interest_profile="テストプロファイル",
        )
        assert result.score == 0.0
        assert "スコアリング失敗" in result.reason

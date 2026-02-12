from researcher.report_generator import ReportGenerator
from shared.models import ScoredArticle, SourceType


def _make_article(title="テスト記事", url="https://example.com/1"):
    return ScoredArticle(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="テスト内容",
    )


class Test_ReportGenerator:
    async def test_レポートがマークダウン形式で生成される(self, mock_gemini_client):
        mock_gemini_client.generate_text.return_value = "# レポート\n## 要約\n記事の分析..."

        generator = ReportGenerator(mock_gemini_client)
        article = _make_article("AI技術記事", "https://example.com/ai")
        related = [
            {"title": "関連記事", "url": "https://r.com", "user_rating": 5, "content": "関連内容"},
        ]

        report = await generator.generate(article, related)

        assert report == "# レポート\n## 要約\n記事の分析..."
        mock_gemini_client.generate_text.assert_called_once()

        # プロンプトに記事情報と関連記事が含まれる
        prompt = mock_gemini_client.generate_text.call_args[0][0]
        assert "AI技術記事" in prompt
        assert "関連記事" in prompt

    async def test_関連記事なしでもレポートが生成される(self, mock_gemini_client):
        mock_gemini_client.generate_text.return_value = "# レポート\n基本的な分析..."

        generator = ReportGenerator(mock_gemini_client)
        article = _make_article("単独記事", "https://example.com/single")

        report = await generator.generate(article, [])

        assert report == "# レポート\n基本的な分析..."
        mock_gemini_client.generate_text.assert_called_once()

        # プロンプトに関連記事セクションが含まれない
        prompt = mock_gemini_client.generate_text.call_args[0][0]
        assert "関連する高評価記事" not in prompt

    async def test_ストリーミングでレポートがチャンク単位で生成される(self, mock_gemini_client):
        generator = ReportGenerator(mock_gemini_client)
        article = _make_article("AI技術記事", "https://example.com/ai")

        chunks = [c async for c in generator.generate_stream(article, [])]

        assert chunks == ["チャンク1", "チャンク2", "チャンク3"]

from librarian.scorer import ArticleScorer


class Test_ArticleScorer:
    async def test_プロファイルなしでデフォルトスコアを返す(self):
        scorer = ArticleScorer()
        result = await scorer.calculate_score(
            article_text="Test article",
            interest_profile="",
        )
        assert result.score == 0.5
        assert "デフォルトスコア" in result.reason

    async def test_プロファイルありでスタブスコアを返す(self):
        scorer = ArticleScorer()
        result = await scorer.calculate_score(
            article_text="AI Agent の新設計パターン",
            interest_profile="ユーザーはAIエージェント設計に強い関心がある",
        )
        assert 0.0 <= result.score <= 1.0

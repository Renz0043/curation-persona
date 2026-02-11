from typing import NamedTuple


class ScoreResult(NamedTuple):
    score: float
    reason: str


class ArticleScorer:
    """LLMベースの記事スコアリング（Phase 1: シグネチャのみ）"""

    async def calculate_score(
        self,
        article_text: str,
        interest_profile: str,
    ) -> ScoreResult:
        if not interest_profile:
            return ScoreResult(
                score=0.5,
                reason="評価データ蓄積中のため、デフォルトスコアを設定しました",
            )
        return ScoreResult(score=0.5, reason="スタブスコア")

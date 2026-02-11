import logging
from typing import NamedTuple

from shared.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

SCORING_PROMPT_TEMPLATE = """\
あなたは記事キュレーションAIです。
ユーザーの興味プロファイルに基づいて、以下の記事の関連度をスコアリングしてください。

## ユーザー興味プロファイル
{interest_profile}

## 記事内容
{article_text}

## 指示
以下のJSON形式で回答してください:
{{"score": 0.0〜1.0の数値, "reason": "スコアの理由を1〜2文で"}}

- score: 0.0（全く関連なし）〜 1.0（非常に関連が高い）
- reason: なぜこのスコアをつけたか簡潔に説明
"""


class ScoreResult(NamedTuple):
    score: float
    reason: str


class ArticleScorer:
    """LLMベースの記事スコアリング"""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

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

        prompt = SCORING_PROMPT_TEMPLATE.format(
            interest_profile=interest_profile,
            article_text=article_text[:2000],
        )

        try:
            data = await self.gemini_client.generate_json(prompt)
            score = float(data.get("score", 0.0))
            score = max(0.0, min(1.0, score))
            reason = data.get("reason", "理由なし")
            return ScoreResult(score=score, reason=reason)
        except Exception as e:
            logger.warning(f"スコアリング失敗: {e}")
            return ScoreResult(score=0.0, reason="スコアリング失敗")

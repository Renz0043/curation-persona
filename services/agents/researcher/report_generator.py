import logging
import random
from collections.abc import AsyncIterator

from shared.gemini_client import GeminiClient
from shared.models import ScoredArticle

logger = logging.getLogger(__name__)

INDUSTRY_LIST = [
    "自動車（自動運転・製造）",
    "建築・都市計画",
    "医療・ヘルスケア",
    "金融・フィンテック",
    "農業・食品",
    "航空宇宙",
    "教育",
    "物流・サプライチェーン",
    "エンターテインメント・ゲーム",
    "エネルギー・環境",
    "軍事・防衛",
    "生物学・バイオテクノロジー",
]

CROSS_INDUSTRY_PROMPT = """\
あなたは異業種の専門家です。以下の記事と深掘りレポートを読み、記事の課題を抽象化し、指定された業界の専門家として批評してください。

## 対象記事
- タイトル: {title}
- URL: {url}
- 内容: {content}

## 深掘りレポート
{report}

## 指示
1. まず、この記事の技術的課題をIT用語を使わずに「リソース配分」「信頼構築」「安全性と自由度のトレードオフ」のような抽象概念で要約してください。
2. 次に、以下の2つの業界の専門家として、それぞれの視点から批評してください。あえて懸念点や反対意見を述べてください。

業界1: {industry_1}
業界2: {industry_2}

## 出力形式（JSON）
{{
  "abstracted_challenge": "抽象化された課題（1-2文）",
  "perspectives": [
    {{
      "industry": "{industry_1}",
      "expert_comment": "その業界の専門家になりきった批評（500文字以内。核心を突く指摘を簡潔に）"
    }},
    {{
      "industry": "{industry_2}",
      "expert_comment": "その業界の専門家になりきった批評（500文字以内。核心を突く指摘を簡潔に）"
    }}
  ]
}}
"""

RESEARCH_PROMPT = """\
あなたは技術記事の深掘りレポートを作成するリサーチャーです。
以下の記事について、詳細な分析レポートをマークダウン形式で作成してください。

## 対象記事
- タイトル: {title}
- URL: {url}
- 内容: {content}

{related_context}

## レポート要件
以下の構成でレポートを作成してください:

### 要約
記事の主要なポイントを3〜5文で簡潔にまとめてください。

### 関連性分析
この記事がなぜ重要か、どのような文脈で役立つかを分析してください。

### キーポイント
記事から得られる重要な知見を箇条書きで3〜5つ挙げてください。

### アクションアイテム
この記事の内容を踏まえて、読者が取れる具体的なアクションを提案してください。
"""


class ReportGenerator:
    """深掘りレポート生成"""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def _build_prompt(
        self, article: ScoredArticle, related_articles: list[dict]
    ) -> str:
        related_context = self._get_related_context(related_articles)
        return RESEARCH_PROMPT.format(
            title=article.title,
            url=article.url,
            content=article.content or "",
            related_context=related_context,
        )

    async def generate(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
    ) -> str:
        prompt = self._build_prompt(article, related_articles)
        report = await self.gemini_client.generate_text(prompt)
        logger.info(f"Report generated for: {article.title}")
        return report

    async def generate_stream(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
    ) -> AsyncIterator[str]:
        prompt = self._build_prompt(article, related_articles)
        async for chunk in self.gemini_client.generate_text_stream(prompt):
            yield chunk

    async def generate_cross_industry_feedback(
        self, article: ScoredArticle, report: str
    ) -> dict:
        industries = random.sample(INDUSTRY_LIST, 2)
        prompt = CROSS_INDUSTRY_PROMPT.format(
            title=article.title,
            url=article.url,
            content=article.content or "",
            report=report,
            industry_1=industries[0],
            industry_2=industries[1],
        )
        return await self.gemini_client.generate_json(prompt)

    def _get_related_context(self, related_articles: list[dict]) -> str:
        if not related_articles:
            return ""

        lines = ["## 関連する高評価記事（参考コンテキスト）"]
        for article in related_articles[:5]:
            lines.append(
                f"- {article['title']} (評価: {article.get('user_rating', 'N/A')})"
            )
            if article.get("content"):
                lines.append(f"  概要: {article['content'][:200]}")

        return "\n".join(lines)

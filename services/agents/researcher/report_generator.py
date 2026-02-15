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
あなたは異業種の専門家です。以下の記事を読んで、記事のテーマを抽象化し、指定された業界の専門家として示唆や気づきを提供してください。

---

## 対象記事
### タイトル:
{title}

### 内容:
{content}

---

## 指示
1. この記事を業界の専門家の目線で、読んでみた率直な感想を整理してください。
2. 次に、専門家として分野は異なっても同じような問題意識や課題を持っていることを踏まえて、その業界の専門家としての示唆・気づきを提供してください。
3. 専門用語を避け、平易な言葉で書いてください。読者がその業界に詳しくなくても理解できるようにしてください。

業界1: {industry_1}
業界2: {industry_2}

## 出力形式（JSON）
{{
  "perspectives": [
    {{
      "industry": "{industry_1}",
      "abstracted_theme": "この業界の視点から見た、記事テーマの抽象化（1-2文）",
      "expert_comment": "その業界の専門家としての示唆・気づき（500文字以内。具体的な事例や応用アイデアを簡潔に。専門用語は避け平易に）"
    }},
    {{
      "industry": "{industry_2}",
      "abstracted_theme": "この業界の視点から見た、記事テーマの抽象化（1-2文）",
      "expert_comment": "その業界の専門家としての示唆・気づき（500文字以内。具体的な事例や応用アイデアを簡潔に。専門用語は避け平易に）"
    }}
  ]
}}
"""

RESEARCH_PROMPT = """\
あなたは技術記事の深掘りレポートを作成するリサーチャーです。
以下の記事について、詳細な分析レポートをマークダウン形式で作成してください。

**重要**: 前置き・挨拶・導入文は一切不要です。レポート本文のみを出力してください。

---

## 対象記事
### タイトル:
{title}

### 内容:
{content}

---

{related_context}

## 読者の興味関心プロファイル
{interest_profile}

## レポート要件
以下の構成でレポートを作成してください:

### 要約
記事の主要なポイントを3〜5文で簡潔にまとめてください。

### 関連性分析
この記事がなぜ重要か、どのような文脈で役立つかを最大3つまで分析してください。

### キーポイント
記事から得られる重要な知見を箇条書きで最大5つまで挙げてください。

### アクションアイテム
読者の興味関心プロファイルを踏まえて、この読者が取れる具体的で実践的なアクションを提案してください。
"""


class ReportGenerator:
    """深掘りレポート生成"""

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def _build_prompt(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
        interest_profile: str = "",
    ) -> str:
        related_context = self._get_related_context(related_articles)
        return RESEARCH_PROMPT.format(
            title=article.title,
            url=article.url,
            content=article.content or "",
            related_context=related_context,
            interest_profile=interest_profile or "（プロファイル未設定）",
        )

    async def generate(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
        interest_profile: str = "",
    ) -> str:
        prompt = self._build_prompt(article, related_articles, interest_profile)
        report = await self.gemini_client.generate_text(prompt)
        logger.info(f"Report generated for: {article.title}")
        return report

    async def generate_stream(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
        interest_profile: str = "",
    ) -> AsyncIterator[str]:
        prompt = self._build_prompt(article, related_articles, interest_profile)
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

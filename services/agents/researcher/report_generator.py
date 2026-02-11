from shared.models import ScoredArticle


class ReportGenerator:
    """レポート生成（Phase 1: シグネチャのみ）"""

    async def generate(
        self,
        article: ScoredArticle,
        related_articles: list[dict],
    ) -> str:
        return "スタブレポート: Phase 2で実装されます。"

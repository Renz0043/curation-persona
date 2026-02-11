from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from researcher.report_generator import ReportGenerator
from researcher.service import ResearcherService
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchArticleParams,
    ResearchStatus,
    ScoredArticle,
    SourceType,
)


def _make_article(title="テスト記事", url="https://example.com/1"):
    return ScoredArticle(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="テスト内容",
    )


def _make_collection(articles=None, collection_id="col_1"):
    return ArticleCollection(
        id=collection_id,
        user_id="user_1",
        date="2025-01-01",
        articles=articles or [],
        status=CollectionStatus.COMPLETED,
        created_at=datetime.now(),
    )


class Test_ResearcherService:
    def _make_service(self, mock_firestore_client, mock_gemini_client):
        report_generator = ReportGenerator(mock_gemini_client)
        return ResearcherService(mock_firestore_client, report_generator)

    async def test_記事の深掘りレポートが生成される(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article("AI最新動向", "https://example.com/ai")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection
        mock_gemini_client.generate_text.return_value = "# 深掘りレポート\n詳細な分析..."

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/ai",
        )
        result = await service.research(params)

        assert result["status"] == "success"
        assert result["article_url"] == "https://example.com/ai"

        # ステータスが RESEARCHING → COMPLETED と遷移
        mock_firestore_client.update_article_research_status.assert_called_once_with(
            "col_1", "https://example.com/ai", ResearchStatus.RESEARCHING
        )
        mock_firestore_client.update_article_research.assert_called_once_with(
            "col_1",
            "https://example.com/ai",
            deep_dive_report="# 深掘りレポート\n詳細な分析...",
            research_status=ResearchStatus.COMPLETED,
        )

    async def test_記事未発見時に処理をスキップする(
        self, mock_firestore_client, mock_gemini_client
    ):
        # コレクションに対象記事が存在しない
        collection = _make_collection([_make_article("別の記事", "https://example.com/other")])
        mock_firestore_client.get_collection.return_value = collection

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/not-found",
        )
        result = await service.research(params)

        assert result["status"] == "error"
        # Firestore 更新やレポート生成は呼ばれない
        mock_firestore_client.update_article_research_status.assert_not_called()
        mock_gemini_client.generate_text.assert_not_called()

    async def test_高評価記事がレポートコンテキストに含まれる(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article("対象記事", "https://example.com/target")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection

        # 高評価記事を返す
        related = [
            {"title": "関連記事A", "url": "https://a.com", "user_rating": 5, "content": "内容A"},
            {"title": "関連記事B", "url": "https://b.com", "user_rating": 4, "content": "内容B"},
        ]
        mock_firestore_client.get_high_rated_articles.return_value = related
        mock_gemini_client.generate_text.return_value = "レポート本文"

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/target",
        )
        await service.research(params)

        # generate_text に渡されたプロンプトに関連記事情報が含まれる
        prompt = mock_gemini_client.generate_text.call_args[0][0]
        assert "関連記事A" in prompt
        assert "関連記事B" in prompt

    async def test_レポート生成失敗時にFAILEDステータスに遷移する(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article("対象記事", "https://example.com/target")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection
        mock_gemini_client.generate_text.side_effect = RuntimeError("API error")

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/target",
        )

        with pytest.raises(RuntimeError, match="API error"):
            await service.research(params)

        # RESEARCHING に設定された後、FAILED に遷移
        calls = mock_firestore_client.update_article_research_status.call_args_list
        assert len(calls) == 2
        assert calls[0].args == ("col_1", "https://example.com/target", ResearchStatus.RESEARCHING)
        assert calls[1].args == ("col_1", "https://example.com/target", ResearchStatus.FAILED)

        # レポート保存は呼ばれない
        mock_firestore_client.update_article_research.assert_not_called()

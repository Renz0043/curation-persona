from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from researcher.report_generator import INDUSTRY_LIST, ReportGenerator
from researcher.service import ResearcherService
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchArticleParams,
    ResearchStatus,
    ScoredArticle,
    SourceType,
)


def _make_article(is_pickup=False, url="https://example.com/1"):
    return ScoredArticle(
        title="テスト記事",
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="テスト内容",
        is_pickup=is_pickup,
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


MOCK_FEEDBACK = {
    "perspectives": [
        {
            "industry": "医療・ヘルスケア",
            "expert_comment": "医療現場では...",
        },
        {
            "industry": "金融・フィンテック",
            "expert_comment": "金融業界では...",
        },
    ],
}


class Test_異業種フィードバック:
    def _make_service(self, mock_firestore_client, mock_gemini_client):
        report_generator = ReportGenerator(mock_gemini_client)
        return ResearcherService(mock_firestore_client, report_generator)

    async def test_ピックアップ記事でフィードバックが生成され保存される(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article(is_pickup=True, url="https://example.com/pickup")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection
        mock_gemini_client.generate_text.return_value = "# レポート"
        mock_gemini_client.generate_json.return_value = MOCK_FEEDBACK

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/pickup",
        )
        result = await service.research(params)

        assert result["status"] == "success"
        mock_gemini_client.generate_json.assert_called_once()
        mock_firestore_client.update_article_research.assert_called_once_with(
            "col_1",
            "https://example.com/pickup",
            deep_dive_report="# レポート",
            research_status=ResearchStatus.COMPLETED,
            cross_industry_feedback=MOCK_FEEDBACK,
        )

    async def test_非ピックアップ記事ではフィードバックが生成されない(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article(is_pickup=False, url="https://example.com/normal")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection
        mock_gemini_client.generate_text.return_value = "# レポート"

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/normal",
        )
        await service.research(params)

        mock_gemini_client.generate_json.assert_not_called()
        mock_firestore_client.update_article_research.assert_called_once_with(
            "col_1",
            "https://example.com/normal",
            deep_dive_report="# レポート",
            research_status=ResearchStatus.COMPLETED,
            cross_industry_feedback=None,
        )

    async def test_ストリーミングでピックアップ記事のフィードバックが生成される(
        self, mock_firestore_client, mock_gemini_client
    ):
        article = _make_article(is_pickup=True, url="https://example.com/pickup")
        collection = _make_collection([article])
        mock_firestore_client.get_collection.return_value = collection
        mock_gemini_client.generate_json.return_value = MOCK_FEEDBACK

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        params = ResearchArticleParams(
            user_id="user_1",
            collection_id="col_1",
            article_url="https://example.com/pickup",
        )

        chunks = [c async for c in service.research_stream(params)]

        assert chunks == ["チャンク1", "チャンク2", "チャンク3"]
        mock_gemini_client.generate_json.assert_called_once()
        mock_firestore_client.update_article_research.assert_called_once_with(
            "col_1",
            "https://example.com/pickup",
            deep_dive_report="チャンク1チャンク2チャンク3",
            research_status=ResearchStatus.COMPLETED,
            cross_industry_feedback=MOCK_FEEDBACK,
        )

    async def test_generate_cross_industry_feedbackが2業界を選出する(
        self, mock_gemini_client
    ):
        mock_gemini_client.generate_json.return_value = MOCK_FEEDBACK
        generator = ReportGenerator(mock_gemini_client)
        article = _make_article(is_pickup=True)

        await generator.generate_cross_industry_feedback(article, "レポート本文")

        prompt = mock_gemini_client.generate_json.call_args[0][0]
        # プロンプトに INDUSTRY_LIST のうち2つが含まれる
        matched = [ind for ind in INDUSTRY_LIST if ind in prompt]
        assert len(matched) == 2

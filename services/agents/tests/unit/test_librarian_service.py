from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from librarian.scorer import ArticleScorer
from librarian.service import LibrarianService
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchStatus,
    ScoredArticle,
    ScoringStatus,
    SourceType,
)


def _make_article(title="テスト記事", url="https://example.com/1", score=0.0):
    return ScoredArticle(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="テスト内容",
        relevance_score=score,
    )


def _make_collection(articles=None, collection_id="col_1"):
    return ArticleCollection(
        id=collection_id,
        user_id="user_1",
        date="2025-01-01",
        articles=articles or [],
        status=CollectionStatus.COLLECTING,
        created_at=datetime.now(),
    )


class Test_LibrarianService:
    def _make_service(self, mock_firestore_client, mock_gemini_client):
        scorer = ArticleScorer(mock_gemini_client)
        return LibrarianService(mock_firestore_client, mock_gemini_client, scorer)

    async def test_コールドスタート時にデフォルトスコアが設定される(
        self, mock_firestore_client, mock_gemini_client
    ):
        articles = [
            _make_article("記事1", "https://example.com/1"),
            _make_article("記事2", "https://example.com/2"),
            _make_article("記事3", "https://example.com/3"),
        ]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection
        # コールドスタート: プロファイルなし、高評価記事なし
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = []

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        result = await service.score_collection("user_1", "col_1")

        assert result["status"] == "success"
        assert result["scored_count"] == 3
        # 全記事がデフォルトスコア0.5
        for article in collection.articles:
            assert article.relevance_score == 0.5
            assert article.scoring_status == ScoringStatus.SCORED

        # ステータス遷移を確認
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.SCORING
        )
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.COMPLETED
        )

    async def test_通常フローでスコアリングとピックアップが行われる(
        self, mock_firestore_client, mock_gemini_client
    ):
        articles = [
            _make_article("低スコア記事", "https://example.com/1"),
            _make_article("高スコア記事", "https://example.com/2"),
            _make_article("中スコア記事", "https://example.com/3"),
        ]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection

        # プロファイルあり
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "interestProfile": "AI技術に関心がある",
            "interestProfileUpdatedAt": datetime(2025, 1, 1),
        }
        mock_firestore_client.has_new_ratings_since.return_value = False

        # スコアリング結果をモック
        mock_gemini_client.generate_json.side_effect = [
            {"score": 0.2, "reason": "関連性低い"},
            {"score": 0.9, "reason": "非常に関連性が高い"},
            {"score": 0.6, "reason": "ある程度関連性がある"},
        ]

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        result = await service.score_collection("user_1", "col_1")

        assert result["status"] == "success"
        assert result["scored_count"] == 3
        assert result["pickup_count"] == 2

        # スコア降順ソート確認
        saved_articles = mock_firestore_client.update_collection_articles.call_args[0][1]
        assert saved_articles[0].relevance_score == 0.9
        assert saved_articles[1].relevance_score == 0.6
        assert saved_articles[2].relevance_score == 0.2

        # 上位2件がピックアップ
        assert saved_articles[0].is_pickup is True
        assert saved_articles[0].research_status == ResearchStatus.PENDING
        assert saved_articles[1].is_pickup is True
        assert saved_articles[2].is_pickup is False

    async def test_プロファイル再生成が新規評価で発火する(
        self, mock_firestore_client, mock_gemini_client
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection

        # 既存プロファイルあり、新規評価あり → 再生成
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "interestProfile": "古いプロファイル",
            "interestProfileUpdatedAt": datetime(2025, 1, 1),
        }
        mock_firestore_client.has_new_ratings_since.return_value = True
        mock_firestore_client.get_high_rated_articles.return_value = [
            {"title": "記事A", "url": "https://a.com", "user_rating": 5, "user_comment": None},
            {"title": "記事B", "url": "https://b.com", "user_rating": 4, "user_comment": "良い"},
            {"title": "記事C", "url": "https://c.com", "user_rating": 5, "user_comment": None},
        ]
        mock_gemini_client.generate_text.return_value = "新しいプロファイル"
        mock_gemini_client.generate_json.return_value = {"score": 0.7, "reason": "関連あり"}

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        await service.score_collection("user_1", "col_1")

        # プロファイル再生成を確認
        mock_gemini_client.generate_text.assert_called_once()
        mock_firestore_client.update_interest_profile.assert_called_once_with(
            "user_1", "新しいプロファイル"
        )

    async def test_高評価記事不足時はコールドスタートになる(
        self, mock_firestore_client, mock_gemini_client
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection

        # プロファイルなし、高評価記事1件のみ（min=3）
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = [
            {"title": "記事A", "url": "https://a.com", "user_rating": 5},
        ]

        service = self._make_service(mock_firestore_client, mock_gemini_client)
        result = await service.score_collection("user_1", "col_1")

        assert result["status"] == "success"
        # LLMスコアリングは呼ばれない
        mock_gemini_client.generate_json.assert_not_called()
        # デフォルトスコア
        assert collection.articles[0].relevance_score == 0.5

    async def test_スコアリング例外時にFAILEDステータスに遷移する(
        self, mock_firestore_client, mock_gemini_client
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection

        # プロファイルあり
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "interestProfile": "AI技術に関心がある",
            "interestProfileUpdatedAt": datetime(2025, 1, 1),
        }
        mock_firestore_client.has_new_ratings_since.return_value = False
        mock_gemini_client.generate_json.return_value = {"score": 0.7, "reason": "ok"}

        # Firestore更新で例外発生（scorer は例外を吸収するため、後続処理で発火）
        mock_firestore_client.update_collection_articles.side_effect = RuntimeError("Firestore error")

        service = self._make_service(mock_firestore_client, mock_gemini_client)

        with pytest.raises(RuntimeError, match="Firestore error"):
            await service.score_collection("user_1", "col_1")

        # SCORING → FAILED の遷移を確認
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.SCORING
        )
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.FAILED
        )

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
    def _make_service(self, mock_firestore_client, mock_gemini_client, mock_scraper):
        scorer = ArticleScorer(mock_gemini_client)
        return LibrarianService(mock_firestore_client, mock_gemini_client, scorer, mock_scraper)

    async def test_コールドスタート時にデフォルトスコアが設定される(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
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

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
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
        self, mock_firestore_client, mock_gemini_client, mock_scraper
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

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
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
        self, mock_firestore_client, mock_gemini_client, mock_scraper
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

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        await service.score_collection("user_1", "col_1")

        # プロファイル再生成を確認
        mock_gemini_client.generate_text.assert_called_once()
        mock_firestore_client.update_interest_profile.assert_called_once_with(
            "user_1", "新しいプロファイル"
        )

    async def test_高評価記事不足時はコールドスタートになる(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection

        # プロファイルなし、高評価記事1件のみ（min=3）
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = [
            {"title": "記事A", "url": "https://a.com", "user_rating": 5},
        ]

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        result = await service.score_collection("user_1", "col_1")

        assert result["status"] == "success"
        # LLMスコアリングは呼ばれない
        mock_gemini_client.generate_json.assert_not_called()
        # デフォルトスコア
        assert collection.articles[0].relevance_score == 0.5

    async def test_スコアリング例外時にFAILEDステータスに遷移する(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
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

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)

        with pytest.raises(RuntimeError, match="Firestore error"):
            await service.score_collection("user_1", "col_1")

        # SCORING → FAILED の遷移を確認
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.SCORING
        )
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.FAILED
        )

    async def test_スコアリング後に上位記事のコンテンツが補完される(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = []

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        await service.score_collection("user_1", "col_1")

        # scrape_articles がソート済みarticlesで呼ばれることを確認
        mock_scraper.scrape_articles.assert_awaited_once()
        call_args = mock_scraper.scrape_articles.call_args
        assert call_args[0][0] == collection.articles
        assert call_args[1]["max_count"] == 10
        assert call_args[1]["delay"] == 2.0

    async def test_スコアリング後にtitle_embeddingが生成される(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        articles = [
            _make_article("記事A", "https://example.com/a"),
            _make_article("記事B", "https://example.com/b"),
        ]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = []

        mock_gemini_client.embed_content.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        await service.score_collection("user_1", "col_1")

        # embed_content が記事タイトルで呼ばれる（meta_descriptionなしの場合はtitleのみ）
        mock_gemini_client.embed_content.assert_called_once_with(["記事A", "記事B"])

        # update_article_embeddings が (url, embedding) ペアで呼ばれる
        mock_firestore_client.update_article_embeddings.assert_called_once()
        call_args = mock_firestore_client.update_article_embeddings.call_args
        assert call_args[0][0] == "col_1"
        embeddings_list = call_args[0][1]
        assert len(embeddings_list) == 2
        assert embeddings_list[0] == ("https://example.com/a", [0.1, 0.2, 0.3])
        assert embeddings_list[1] == ("https://example.com/b", [0.4, 0.5, 0.6])

    async def test_meta_descriptionありの場合embeddingにtitleと結合して使われる(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        articles = [
            ScoredArticle(
                title="記事A",
                url="https://example.com/a",
                source="test",
                source_type=SourceType.RSS,
                meta_description="記事Aの説明",
            ),
            ScoredArticle(
                title="記事B",
                url="https://example.com/b",
                source="test",
                source_type=SourceType.RSS,
            ),
        ]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = []

        mock_gemini_client.embed_content.return_value = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        await service.score_collection("user_1", "col_1")

        # meta_descriptionありの記事は "title\nmeta_description" で呼ばれる
        mock_gemini_client.embed_content.assert_called_once_with(
            ["記事A\n記事Aの説明", "記事B"]
        )

    async def test_embedding生成失敗でもスコアリングは完了する(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        articles = [_make_article()]
        collection = _make_collection(articles)
        mock_firestore_client.get_collection.return_value = collection
        mock_firestore_client.get_user.return_value = {"user_id": "user_1"}
        mock_firestore_client.get_high_rated_articles.return_value = []

        # embed_content が例外を投げる
        mock_gemini_client.embed_content.side_effect = RuntimeError("API error")

        service = self._make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        result = await service.score_collection("user_1", "col_1")

        # スコアリング自体は成功
        assert result["status"] == "success"
        # COMPLETED ステータスに遷移
        mock_firestore_client.update_collection_status.assert_any_call(
            "col_1", CollectionStatus.COMPLETED
        )

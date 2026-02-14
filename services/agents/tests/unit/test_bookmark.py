from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from researcher.report_generator import ReportGenerator
from researcher.service import ResearcherService
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ResearchStatus,
    ScoredArticle,
    ScoringStatus,
    SourceType,
)


def _make_service(mock_firestore_client, mock_gemini_client, mock_scraper):
    report_generator = ReportGenerator(mock_gemini_client)
    return ResearcherService(
        mock_firestore_client, report_generator, mock_scraper
    )


def _make_bookmark_collection(user_id="test_user", articles=None):
    collection_id = f"bm_{user_id}"
    return ArticleCollection(
        id=collection_id,
        user_id=user_id,
        date="",
        articles=articles or [],
        status=CollectionStatus.COMPLETED,
        created_at=datetime.now(),
    )


class Test_ブックマークサービス:
    async def test_ブックマーク記事が保存され深掘りが実行される(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        url = "https://example.com/article"
        mock_scraper.scrape.return_value = "記事タイトル\n\n記事本文テスト"
        mock_scraper.fetch_meta_description.return_value = "テスト説明文"

        # research() で使われるコレクション取得を設定
        bookmark_article = ScoredArticle(
            title="記事タイトル",
            url=url,
            source="bookmark",
            source_type=SourceType.BOOKMARK,
            content="記事タイトル\n\n記事本文テスト",
            scoring_status=ScoringStatus.SCORED,
            relevance_score=1.0,
            relevance_reason="ユーザーが手動でブックマーク",
            is_pickup=True,
            research_status=ResearchStatus.PENDING,
        )
        mock_firestore_client.get_collection.return_value = _make_bookmark_collection(
            articles=[bookmark_article]
        )
        mock_gemini_client.generate_text.return_value = "# 深掘りレポート"

        service = _make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        result = await service.create_bookmark("test_user", url)

        assert result["status"] == "completed"
        assert result["article_url"] == url

        # コレクション確保が呼ばれた
        mock_firestore_client.ensure_bookmark_collection.assert_called_once_with(
            "test_user"
        )
        # 記事が保存された
        mock_firestore_client.save_bookmark_article.assert_called_once()
        call_args = mock_firestore_client.save_bookmark_article.call_args
        assert call_args[0][0] == "bm_test_user"
        assert call_args[0][1] == "test_user"
        saved_article = call_args[0][2]
        assert saved_article.source_type == SourceType.BOOKMARK
        assert saved_article.content == "記事タイトル\n\n記事本文テスト"

        # research が実行された（レポート保存が呼ばれた）
        mock_firestore_client.update_article_research.assert_called_once()

    async def test_スクレイピング失敗時もURLのみで記事が保存される(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        url = "https://example.com/fail"
        mock_scraper.scrape.side_effect = Exception("Connection error")
        mock_scraper.fetch_meta_description.side_effect = Exception("Connection error")

        # research() で使われるコレクション取得を設定
        fallback_article = ScoredArticle(
            title=url,
            url=url,
            source="bookmark",
            source_type=SourceType.BOOKMARK,
            scoring_status=ScoringStatus.SCORED,
            relevance_score=1.0,
            relevance_reason="ユーザーが手動でブックマーク",
            is_pickup=True,
            research_status=ResearchStatus.PENDING,
        )
        mock_firestore_client.get_collection.return_value = _make_bookmark_collection(
            articles=[fallback_article]
        )
        mock_gemini_client.generate_text.return_value = "# レポート"

        service = _make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        result = await service.create_bookmark("test_user", url)

        assert result["status"] == "completed"
        # 記事は保存される（content は None）
        saved_article = mock_firestore_client.save_bookmark_article.call_args[0][2]
        assert saved_article.url == url
        assert saved_article.title == url  # タイトルはURLフォールバック
        assert saved_article.content is None

    async def test_ブックマーク記事のsource_typeがBOOKMARKになる(
        self, mock_firestore_client, mock_gemini_client, mock_scraper
    ):
        url = "https://example.com/test"
        mock_scraper.scrape.return_value = None
        mock_scraper.fetch_meta_description.return_value = None

        mock_firestore_client.get_collection.return_value = _make_bookmark_collection(
            articles=[
                ScoredArticle(
                    title=url,
                    url=url,
                    source="bookmark",
                    source_type=SourceType.BOOKMARK,
                    scoring_status=ScoringStatus.SCORED,
                    relevance_score=1.0,
                    relevance_reason="ユーザーが手動でブックマーク",
                    is_pickup=True,
                    research_status=ResearchStatus.PENDING,
                )
            ]
        )
        mock_gemini_client.generate_text.return_value = "# レポート"

        service = _make_service(mock_firestore_client, mock_gemini_client, mock_scraper)
        await service.create_bookmark("test_user", url)

        saved_article = mock_firestore_client.save_bookmark_article.call_args[0][2]
        assert saved_article.source_type == SourceType.BOOKMARK
        assert saved_article.is_pickup is True
        assert saved_article.relevance_score == 1.0


class Test_ブックマークAPIエンドポイント:
    def _create_test_client(self, mock_firestore_client, mock_service):
        """テスト用の FastAPI TestClient を作成する。"""
        import researcher.main as main_module

        # モジュールレベルの参照を差し替え
        original_firestore = main_module.firestore
        original_service = main_module.service
        main_module.firestore = mock_firestore_client
        main_module.service = mock_service

        from researcher.main import create_app

        app = create_app()
        client = TestClient(app)
        yield client

        # 元に戻す
        main_module.firestore = original_firestore
        main_module.service = original_service

    def test_有効なAPIキーでブックマークが受け付けられる(
        self, mock_firestore_client
    ):
        mock_firestore_client.get_user_by_api_key.return_value = {
            "user_id": "test_user"
        }
        mock_service = AsyncMock()
        mock_service.create_bookmark = AsyncMock(
            return_value={"status": "completed", "article_url": "https://example.com"}
        )

        for client in self._create_test_client(mock_firestore_client, mock_service):
            response = client.post(
                "/api/bookmarks",
                json={"url": "https://example.com", "api_key": "valid_key"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["url"] == "https://example.com"

    def test_無効なAPIキーで401エラーが返る(self, mock_firestore_client):
        mock_firestore_client.get_user_by_api_key.return_value = None
        mock_service = AsyncMock()

        for client in self._create_test_client(mock_firestore_client, mock_service):
            response = client.post(
                "/api/bookmarks",
                json={"url": "https://example.com", "api_key": "invalid_key"},
            )
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid API key"

    def test_URLが欠けている場合は422エラーが返る(self, mock_firestore_client):
        mock_firestore_client.get_user_by_api_key.return_value = {
            "user_id": "test_user"
        }
        mock_service = AsyncMock()

        for client in self._create_test_client(mock_firestore_client, mock_service):
            response = client.post(
                "/api/bookmarks",
                json={"api_key": "valid_key"},
            )
            assert response.status_code == 422

from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient
from shared.models import ResearchStatus


def _make_client_with_articles(articles):
    """Firestoreドキュメントモック付きクライアントを生成"""
    client = FirestoreClient.__new__(FirestoreClient)

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {"articles": articles}
    mock_doc_ref = AsyncMock()
    mock_doc_ref.get.return_value = mock_doc

    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    client.db = mock_db

    return client, mock_doc_ref


class Test_update_article_research_status:
    async def test_対象記事のresearch_statusが更新される(self):
        articles = [
            {"url": "https://example.com/1", "title": "記事1", "research_status": "pending"},
            {"url": "https://example.com/2", "title": "記事2", "research_status": "pending"},
        ]
        client, mock_doc_ref = _make_client_with_articles(articles)

        await client.update_article_research_status(
            "col_1", "https://example.com/1", ResearchStatus.RESEARCHING
        )

        updated = mock_doc_ref.update.call_args[0][0]["articles"]
        assert updated[0]["research_status"] == "researching"
        assert updated[1]["research_status"] == "pending"

    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_article_research_status(
            "col_1", "https://example.com/1", ResearchStatus.RESEARCHING
        )


class Test_update_article_research:
    async def test_レポートとステータスが保存される(self):
        articles = [
            {"url": "https://example.com/1", "title": "記事1"},
        ]
        client, mock_doc_ref = _make_client_with_articles(articles)

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート内容",
            research_status=ResearchStatus.COMPLETED,
        )

        updated = mock_doc_ref.update.call_args[0][0]["articles"]
        assert updated[0]["deep_dive_report"] == "# レポート内容"
        assert updated[0]["research_status"] == "completed"

    async def test_ステータスなしでレポートのみ保存される(self):
        articles = [
            {"url": "https://example.com/1", "title": "記事1"},
        ]
        client, mock_doc_ref = _make_client_with_articles(articles)

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート",
        )

        updated = mock_doc_ref.update.call_args[0][0]["articles"]
        assert updated[0]["deep_dive_report"] == "# レポート"
        assert "research_status" not in updated[0]

    async def test_対象外の記事は変更されない(self):
        articles = [
            {"url": "https://example.com/1", "title": "対象"},
            {"url": "https://example.com/2", "title": "非対象"},
        ]
        client, mock_doc_ref = _make_client_with_articles(articles)

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート",
            research_status=ResearchStatus.COMPLETED,
        )

        updated = mock_doc_ref.update.call_args[0][0]["articles"]
        assert "deep_dive_report" in updated[0]
        assert "deep_dive_report" not in updated[1]

from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient
from shared.models import ResearchStatus, generate_article_id


class Test_update_article_research_status:
    async def test_対象記事のresearch_statusが更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_research_status(
            "col_1", "https://example.com/1", ResearchStatus.RESEARCHING
        )

        article_id = generate_article_id("col_1", "https://example.com/1")
        mock_articles_col.document.assert_called_with(article_id)
        mock_doc_ref.update.assert_called_once_with(
            {"research_status": "researching"}
        )

    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_article_research_status(
            "col_1", "https://example.com/1", ResearchStatus.RESEARCHING
        )


class Test_update_article_research:
    async def test_レポートとステータスが保存される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート内容",
            research_status=ResearchStatus.COMPLETED,
        )

        article_id = generate_article_id("col_1", "https://example.com/1")
        mock_articles_col.document.assert_called_with(article_id)
        mock_doc_ref.update.assert_called_once_with(
            {"deep_dive_report": "# レポート内容", "research_status": "completed"}
        )

    async def test_ステータスなしでレポートのみ保存される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート",
        )

        mock_doc_ref.update.assert_called_once_with(
            {"deep_dive_report": "# レポート"}
        )

    async def test_記事IDで直接更新されるため他の記事に影響しない(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_research(
            "col_1",
            "https://example.com/1",
            deep_dive_report="# レポート",
            research_status=ResearchStatus.COMPLETED,
        )

        # 1つの記事ドキュメントのみ更新される
        article_id = generate_article_id("col_1", "https://example.com/1")
        mock_articles_col.document.assert_called_once_with(article_id)
        mock_doc_ref.update.assert_called_once()

from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient
from shared.models import generate_article_id


class Test_update_article_feedback:
    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_article_feedback("col_1", "https://example.com/1", 5, "素晴らしい")

    async def test_記事のフィードバックが更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_feedback(
            "col_1", "https://example.com/1", 4, "良い記事"
        )

        article_id = generate_article_id("col_1", "https://example.com/1")
        mock_articles_col.document.assert_called_with(article_id)
        mock_doc_ref.update.assert_called_once_with(
            {"user_rating": 4, "user_comment": "良い記事"}
        )

    async def test_コメントなしで評価のみ更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc_ref = AsyncMock()
        mock_articles_col = MagicMock()
        mock_articles_col.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles_col
        client.db = mock_db

        await client.update_article_feedback("col_1", "https://example.com/1", 3)

        mock_doc_ref.update.assert_called_once_with({"user_rating": 3})

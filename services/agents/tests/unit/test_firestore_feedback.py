from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient


class Test_update_article_feedback:
    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_article_feedback("col_1", "https://example.com/1", 5, "素晴らしい")

    async def test_記事のフィードバックが更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "articles": [
                {"url": "https://example.com/1", "title": "記事1"},
                {"url": "https://example.com/2", "title": "記事2"},
            ]
        }
        mock_doc_ref = AsyncMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_collection
        client.db = mock_db

        await client.update_article_feedback(
            "col_1", "https://example.com/1", 4, "良い記事"
        )

        # update が呼ばれたことを確認
        mock_doc_ref.update.assert_called_once()
        updated_articles = mock_doc_ref.update.call_args[0][0]["articles"]
        assert updated_articles[0]["user_rating"] == 4
        assert updated_articles[0]["user_comment"] == "良い記事"
        # 他の記事は変更なし
        assert "user_rating" not in updated_articles[1]

    async def test_コメントなしで評価のみ更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "articles": [
                {"url": "https://example.com/1", "title": "記事1"},
            ]
        }
        mock_doc_ref = AsyncMock()
        mock_doc_ref.get.return_value = mock_doc

        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_collection
        client.db = mock_db

        await client.update_article_feedback("col_1", "https://example.com/1", 3)

        updated_articles = mock_doc_ref.update.call_args[0][0]["articles"]
        assert updated_articles[0]["user_rating"] == 3
        assert "user_comment" not in updated_articles[0]

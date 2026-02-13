from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient
from shared.models import CollectionStatus


def _make_collection_dict(
    collection_id: str,
    user_id: str = "user_1",
    date: str = "2025-01-15",
    status: str = "completed",
):
    return {
        "id": collection_id,
        "user_id": user_id,
        "date": date,
        "status": status,
        "created_at": datetime(2025, 1, 15, 6, 0, 0),
    }


def _make_db_mock(col_dict, articles_dicts=None):
    """collections クエリ + articles クエリの両方をモックするDBを生成"""
    mock_col_doc = MagicMock()
    mock_col_doc.to_dict.return_value = col_dict

    # collections query chain
    mock_col_query = MagicMock()
    mock_col_query.where.return_value = mock_col_query
    mock_col_query.order_by.return_value = mock_col_query
    mock_col_query.limit.return_value = mock_col_query

    async def _col_stream():
        if col_dict:
            yield mock_col_doc

    mock_col_query.stream = _col_stream

    # articles query chain
    mock_art_query = MagicMock()
    mock_art_query.where.return_value = mock_art_query

    async def _art_stream():
        for a in (articles_dicts or []):
            doc = MagicMock()
            doc.to_dict.return_value = a
            yield doc

    mock_art_query.stream = _art_stream

    mock_db = MagicMock()
    mock_db.collection.side_effect = (
        lambda name: mock_col_query if name == "collections" else mock_art_query
    )

    return mock_db, mock_col_query


class Test_get_latest_collection:
    async def test_スタブモードでNoneを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        result = await client.get_latest_collection("user_1")
        assert result is None

    async def test_最新のコレクションを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        col_dict = _make_collection_dict("col_1")
        mock_db, _ = _make_db_mock(col_dict)
        client.db = mock_db

        result = await client.get_latest_collection("user_1")

        assert result is not None
        assert result.id == "col_1"
        assert result.user_id == "user_1"
        assert result.status == CollectionStatus.COMPLETED

    async def test_記事付きのコレクションを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        col_dict = _make_collection_dict("col_1")
        article_data = {
            "id": "col_1_abc12345",
            "title": "テスト記事",
            "url": "https://example.com/1",
            "source": "test",
            "source_type": "rss",
            "collection_id": "col_1",
            "user_id": "user_1",
            "scoring_status": "scored",
            "relevance_score": 0.8,
        }
        mock_db, _ = _make_db_mock(col_dict, [article_data])
        client.db = mock_db

        result = await client.get_latest_collection("user_1")

        assert result is not None
        assert len(result.articles) == 1
        assert result.articles[0].title == "テスト記事"

    async def test_日付指定でwhereが追加される(self):
        client = FirestoreClient.__new__(FirestoreClient)
        col_dict = _make_collection_dict("col_2", date="2025-01-20")
        mock_db, mock_col_query = _make_db_mock(col_dict)
        client.db = mock_db

        result = await client.get_latest_collection("user_1", date="2025-01-20")

        assert result is not None
        assert result.date == "2025-01-20"
        # where が2回呼ばれる（user_id + date）
        assert mock_col_query.where.call_count == 2

    async def test_コレクションが存在しない場合Noneを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_col_query = MagicMock()
        mock_col_query.where.return_value = mock_col_query
        mock_col_query.order_by.return_value = mock_col_query
        mock_col_query.limit.return_value = mock_col_query

        async def _stream():
            return
            yield  # noqa: make it an async generator

        mock_col_query.stream = _stream

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_col_query
        client.db = mock_db

        result = await client.get_latest_collection("user_1")
        assert result is None

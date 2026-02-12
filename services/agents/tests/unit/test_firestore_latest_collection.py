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
        "articles": [],
        "status": status,
        "created_at": datetime(2025, 1, 15, 6, 0, 0),
    }


class Test_get_latest_collection:
    async def test_スタブモードでNoneを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        result = await client.get_latest_collection("user_1")
        assert result is None

    async def test_最新のコレクションを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)

        col_dict = _make_collection_dict("col_1")
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = col_dict

        # query chain mock: .where().order_by().limit().stream()
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        async def _stream():
            yield mock_doc

        mock_query.stream = _stream

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_query
        client.db = mock_db

        result = await client.get_latest_collection("user_1")

        assert result is not None
        assert result.id == "col_1"
        assert result.user_id == "user_1"
        assert result.status == CollectionStatus.COMPLETED

    async def test_日付指定でwhereが追加される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        col_dict = _make_collection_dict("col_2", date="2025-01-20")
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = col_dict

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        async def _stream():
            yield mock_doc

        mock_query.stream = _stream

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_query
        client.db = mock_db

        result = await client.get_latest_collection("user_1", date="2025-01-20")

        assert result is not None
        assert result.date == "2025-01-20"
        # where が2回呼ばれる（user_id + date）
        assert mock_query.where.call_count == 2

    async def test_コレクションが存在しない場合Noneを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        async def _stream():
            return
            yield  # noqa: make it an async generator

        mock_query.stream = _stream

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_query
        client.db = mock_db

        result = await client.get_latest_collection("user_1")
        assert result is None

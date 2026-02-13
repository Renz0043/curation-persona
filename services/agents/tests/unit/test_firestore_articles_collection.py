from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from shared.firestore_client import FirestoreClient
from shared.models import (
    ArticleCollection,
    CollectionStatus,
    ScoredArticle,
    SourceType,
    generate_article_id,
)


def _make_article(title="テスト記事", url="https://example.com/1"):
    return ScoredArticle(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
    )


def _make_collection(articles=None, collection_id="col_1"):
    return ArticleCollection(
        id=collection_id,
        user_id="user_1",
        date="2025-01-15",
        articles=articles or [],
        status=CollectionStatus.COLLECTING,
        created_at=datetime(2025, 1, 15, 6, 0, 0),
    )


def _make_db_with_batch():
    """バッチ書き込み対応のDBモックを生成"""
    mock_batch = MagicMock()
    mock_batch.commit = AsyncMock()

    mock_col_doc_ref = AsyncMock()
    mock_art_doc_ref = MagicMock()

    mock_collections = MagicMock()
    mock_collections.document.return_value = mock_col_doc_ref

    mock_articles = MagicMock()
    mock_articles.document.return_value = mock_art_doc_ref

    mock_db = MagicMock()
    mock_db.collection.side_effect = (
        lambda name: mock_collections if name == "collections" else mock_articles
    )
    mock_db.batch.return_value = mock_batch

    return mock_db, mock_batch, mock_col_doc_ref, mock_articles


class Test_create_collection:
    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        collection = _make_collection()
        await client.create_collection(collection)

    async def test_コレクションと記事が分離して保存される(self):
        client = FirestoreClient.__new__(FirestoreClient)
        articles = [
            _make_article("記事1", "https://example.com/1"),
            _make_article("記事2", "https://example.com/2"),
        ]
        collection = _make_collection(articles)

        mock_db, mock_batch, mock_col_doc_ref, mock_articles = _make_db_with_batch()
        client.db = mock_db

        await client.create_collection(collection)

        # コレクションドキュメントに articles が含まれない
        mock_col_doc_ref.set.assert_called_once()
        saved_col = mock_col_doc_ref.set.call_args[0][0]
        assert "articles" not in saved_col
        assert saved_col["id"] == "col_1"
        assert saved_col["user_id"] == "user_1"

        # 記事がバッチ書き込みされる
        assert mock_batch.set.call_count == 2
        mock_batch.commit.assert_called_once()

        # 記事ドキュメントに collection_id と user_id が付与される
        first_call = mock_batch.set.call_args_list[0]
        article_data = first_call[0][1]
        assert article_data["collection_id"] == "col_1"
        assert article_data["user_id"] == "user_1"

    async def test_記事なしのコレクションはバッチ書き込みが発生しない(self):
        client = FirestoreClient.__new__(FirestoreClient)
        collection = _make_collection(articles=[])

        mock_db, mock_batch, mock_col_doc_ref, _ = _make_db_with_batch()
        client.db = mock_db

        await client.create_collection(collection)

        mock_col_doc_ref.set.assert_called_once()
        mock_batch.set.assert_not_called()

    async def test_記事にIDが設定される(self):
        client = FirestoreClient.__new__(FirestoreClient)
        article = _make_article("記事1", "https://example.com/1")
        collection = _make_collection([article])

        mock_db, mock_batch, _, _ = _make_db_with_batch()
        client.db = mock_db

        await client.create_collection(collection)

        expected_id = generate_article_id("col_1", "https://example.com/1")
        assert article.id == expected_id


class Test_get_collection:
    async def test_スタブモードでスタブコレクションを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        result = await client.get_collection("col_1")
        assert result.id == "col_1"
        assert result.user_id == "stub"

    async def test_コレクションと記事を結合して返す(self):
        client = FirestoreClient.__new__(FirestoreClient)

        # collections doc: document(id).get() -> doc, doc.to_dict() -> dict
        mock_col_snapshot = MagicMock()
        mock_col_snapshot.to_dict.return_value = {
            "id": "col_1",
            "user_id": "user_1",
            "date": "2025-01-15",
            "status": "completed",
            "created_at": datetime(2025, 1, 15, 6, 0, 0),
        }
        mock_col_doc_ref = AsyncMock()
        mock_col_doc_ref.get.return_value = mock_col_snapshot

        mock_collections = MagicMock()
        mock_collections.document.return_value = mock_col_doc_ref

        # articles query
        article_data = {
            "id": "col_1_abc12345",
            "title": "テスト記事",
            "url": "https://example.com/1",
            "source": "test",
            "source_type": "rss",
            "collection_id": "col_1",
            "user_id": "user_1",
        }
        mock_art_doc = MagicMock()
        mock_art_doc.to_dict.return_value = article_data

        mock_art_query = MagicMock()
        mock_art_query.where.return_value = mock_art_query

        async def _stream():
            yield mock_art_doc

        mock_art_query.stream = _stream

        mock_db = MagicMock()
        mock_db.collection.side_effect = (
            lambda name: mock_collections if name == "collections" else mock_art_query
        )
        client.db = mock_db

        result = await client.get_collection("col_1")

        assert result.id == "col_1"
        assert len(result.articles) == 1
        assert result.articles[0].title == "テスト記事"


class Test_update_collection_articles:
    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_collection_articles("col_1", [])

    async def test_記事がバッチ更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)
        articles = [
            _make_article("記事1", "https://example.com/1"),
            _make_article("記事2", "https://example.com/2"),
        ]

        mock_db, mock_batch, _, mock_articles = _make_db_with_batch()

        # update_collection_articles は collection doc から user_id を取得する
        # document(id).get() -> snapshot, snapshot.to_dict() -> dict
        mock_col_snapshot = MagicMock()
        mock_col_snapshot.to_dict.return_value = {"user_id": "user_1"}
        mock_col_doc_ref = AsyncMock()
        mock_col_doc_ref.get.return_value = mock_col_snapshot
        mock_collections = MagicMock()
        mock_collections.document.return_value = mock_col_doc_ref
        mock_db.collection.side_effect = (
            lambda name: mock_collections if name == "collections" else mock_articles
        )
        client.db = mock_db

        await client.update_collection_articles("col_1", articles)

        assert mock_batch.set.call_count == 2
        mock_batch.commit.assert_called_once()

        # 記事データに user_id と collection_id が含まれる
        first_call = mock_batch.set.call_args_list[0]
        article_data = first_call[0][1]
        assert article_data["user_id"] == "user_1"
        assert article_data["collection_id"] == "col_1"


class Test_update_article_embeddings:
    async def test_スタブモードでエラーなく動作する(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        await client.update_article_embeddings("col_1", [])

    async def test_Embeddingがバッチ更新される(self):
        client = FirestoreClient.__new__(FirestoreClient)

        mock_batch = MagicMock()
        mock_batch.commit = AsyncMock()
        mock_art_doc_ref = MagicMock()
        mock_articles = MagicMock()
        mock_articles.document.return_value = mock_art_doc_ref

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_articles
        mock_db.batch.return_value = mock_batch
        client.db = mock_db

        article_embeddings = [
            ("https://example.com/1", [0.1, 0.2, 0.3]),
            ("https://example.com/2", [0.4, 0.5, 0.6]),
        ]

        await client.update_article_embeddings("col_1", article_embeddings)

        assert mock_batch.update.call_count == 2
        mock_batch.commit.assert_called_once()

        # Vector オブジェクトが渡される
        first_call = mock_batch.update.call_args_list[0]
        update_data = first_call[0][1]
        assert "title_embedding" in update_data


class Test_find_similar_articles:
    async def test_スタブモードで空リストを返す(self):
        client = FirestoreClient.__new__(FirestoreClient)
        client.db = None
        result = await client.find_similar_articles("user_1", [0.1, 0.2])
        assert result == []

    async def test_ベクトル検索結果を辞書リストで返す(self):
        client = FirestoreClient.__new__(FirestoreClient)

        # articles query + find_nearest のモック
        mock_art_doc = MagicMock()
        mock_art_doc.to_dict.return_value = {
            "title": "テスト記事",
            "url": "https://example.com/1",
            "source": "test",
            "relevance_score": 0.85,
            "collection_id": "col_1",
            "vector_distance": 0.12,
        }

        mock_vector_query = MagicMock()

        async def _stream():
            yield mock_art_doc

        mock_vector_query.stream = _stream

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.find_nearest.return_value = mock_vector_query

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_query
        client.db = mock_db

        result = await client.find_similar_articles("user_1", [0.1, 0.2], limit=5)

        assert len(result) == 1
        assert result[0]["title"] == "テスト記事"
        assert result[0]["vector_distance"] == 0.12

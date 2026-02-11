from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from collector.service import CollectorService
from shared.models import Article, SourceType


def _make_source(name="テストRSS", source_type="rss", enabled=True):
    return {
        "id": f"src_{name}",
        "type": source_type,
        "name": name,
        "enabled": enabled,
        "config": {"url": "https://example.com/feed"},
    }


def _make_article(title="テスト記事", url="https://example.com/1"):
    return Article(
        title=title,
        url=url,
        source="test",
        source_type=SourceType.RSS,
        content="テスト内容",
        published_at=datetime.now(),
    )


class Test_CollectorService:
    def _make_service(self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry):
        return CollectorService(mock_firestore_client, mock_a2a_client, mock_fetcher_registry)

    async def test_RSS記事を収集してコレクションを作成する(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        # ユーザーに有効なRSSソースが1つある
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [_make_source("Tech Feed")],
        }

        # フェッチャーが記事を返す
        articles = [
            _make_article("記事1", "https://example.com/1"),
            _make_article("記事2", "https://example.com/2"),
        ]
        mock_fetcher = MagicMock()
        mock_fetcher.fetch = AsyncMock(return_value=articles)
        mock_fetcher_registry.get_fetcher.return_value = mock_fetcher

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        assert result["status"] == "success"
        assert result["articles_total"] == 2
        assert result["collection_id"] != ""

        # Firestore にコレクションが保存された
        mock_firestore_client.create_collection.assert_called_once()
        saved_collection = mock_firestore_client.create_collection.call_args[0][0]
        assert len(saved_collection.articles) == 2
        assert saved_collection.user_id == "user_1"

        # Librarian に A2A メッセージが送信された
        mock_a2a_client.send_message.assert_called_once()
        call_kwargs = mock_a2a_client.send_message.call_args
        assert call_kwargs[1]["skill"] == "score_articles"

    async def test_ソース取得失敗時にスキップして継続する(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [
                _make_source("失敗ソース"),
                _make_source("成功ソース"),
            ],
        }

        # 1つ目は失敗、2つ目は成功
        fail_fetcher = MagicMock()
        fail_fetcher.fetch = AsyncMock(side_effect=Exception("接続エラー"))

        success_articles = [_make_article("成功記事", "https://example.com/ok")]
        success_fetcher = MagicMock()
        success_fetcher.fetch = AsyncMock(return_value=success_articles)

        call_count = 0

        def side_effect_get_fetcher(source_type):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return fail_fetcher
            return success_fetcher

        mock_fetcher_registry.get_fetcher.side_effect = side_effect_get_fetcher

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        # エラーをスキップして成功ソースの記事のみ収集
        assert result["status"] == "success"
        assert result["articles_total"] == 1

    async def test_重複URLが除去される(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [_make_source("ソース1"), _make_source("ソース2")],
        }

        # 2つのソースから同じURLの記事が返る
        articles_with_dup = [
            _make_article("記事A", "https://example.com/dup"),
            _make_article("記事B", "https://example.com/unique1"),
            _make_article("記事A（別ソース）", "https://example.com/dup"),
            _make_article("記事C", "https://example.com/unique2"),
        ]

        # get_fetcher を1つのフェッチャーで全記事返すようにモック
        mock_fetcher = MagicMock()
        # 各ソースごとに半分ずつ返す
        mock_fetcher.fetch = AsyncMock(
            side_effect=[articles_with_dup[:2], articles_with_dup[2:]]
        )
        mock_fetcher_registry.get_fetcher.return_value = mock_fetcher

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        # 重複が除去されて3件になる
        assert result["articles_total"] == 3
        saved_collection = mock_firestore_client.create_collection.call_args[0][0]
        urls = [a.url for a in saved_collection.articles]
        assert len(set(urls)) == 3

    async def test_有効なソースのみ取得される(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [
                _make_source("有効ソース", enabled=True),
                _make_source("無効ソース", enabled=False),
            ],
        }

        articles = [_make_article("記事1", "https://example.com/1")]
        mock_fetcher = MagicMock()
        mock_fetcher.fetch = AsyncMock(return_value=articles)
        mock_fetcher_registry.get_fetcher.return_value = mock_fetcher

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        assert result["articles_total"] == 1
        # フェッチャーは有効なソース1つ分のみ呼ばれる
        assert mock_fetcher_registry.get_fetcher.call_count == 1

    async def test_ソースが空の場合は即座に成功を返す(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [],
        }

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        assert result["status"] == "success"
        assert result["articles_total"] == 0
        # Firestore保存もA2A送信も行われない
        mock_firestore_client.create_collection.assert_not_called()
        mock_a2a_client.send_message.assert_not_called()

    async def test_対応するfetcherが未登録のソースはスキップされる(
        self, mock_firestore_client, mock_a2a_client, mock_fetcher_registry
    ):
        mock_firestore_client.get_user.return_value = {
            "user_id": "user_1",
            "sources": [_make_source("未対応ソース", source_type="api")],
        }
        mock_fetcher_registry.get_fetcher.return_value = None

        service = self._make_service(
            mock_firestore_client, mock_a2a_client, mock_fetcher_registry
        )
        result = await service.execute("user_1")

        # 記事0件だがコレクション自体は作成される
        assert result["status"] == "success"
        assert result["articles_total"] == 0

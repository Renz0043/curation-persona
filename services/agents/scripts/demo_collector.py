"""Collector Agent の動作確認スクリプト

Firestore・Librarian 不要で RSS 取得 → コレクション作成の流れを確認できます。

Usage:
    cd services/agents
    .venv/bin/python -m scripts.demo_collector
"""

import asyncio
import logging
from unittest.mock import AsyncMock

from shared.a2a_client import A2AClient
from shared.fetchers.registry import FetcherRegistry
from shared.fetchers.rss_fetcher import RSSFetcher
from shared.firestore_client import FirestoreClient
from shared.scraper import WebScraper

from collector.service import CollectorService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# テスト用ユーザー設定（実在する公開RSSフィード）
TEST_USER = {
    "user_id": "demo_user",
    "sources": [
        {
            "id": "src_zenn",
            "type": "rss",
            "name": "Zenn Trending",
            "enabled": True,
            "config": {"url": "https://zenn.dev/feed"},
        },
        {
            "id": "src_hatena",
            "type": "rss",
            "name": "はてなブックマーク - テクノロジー",
            "enabled": True,
            "config": {"url": "https://b.hatena.ne.jp/hotentry/it.rss"},
        },
        {
            "id": "src_disabled",
            "type": "rss",
            "name": "無効化されたソース",
            "enabled": False,
            "config": {"url": "https://example.com/disabled"},
        },
    ],
}


async def main():
    # Firestore をスタブモード（接続なし）で使用
    firestore = FirestoreClient.__new__(FirestoreClient)
    firestore.db = None
    firestore.get_user = AsyncMock(return_value=TEST_USER)
    firestore.create_collection = AsyncMock()

    # A2A 送信をモック（Librarian不要）
    a2a_client = A2AClient.__new__(A2AClient)
    a2a_client.send_message = AsyncMock(return_value={"status": "ok"})

    # FetcherRegistry を max_age_days=3 で組み立て（デモ用に広めのカットオフ）
    registry = FetcherRegistry()
    registry.register(RSSFetcher(max_age_days=3))

    # WebScraper（meta description 並列取得用）
    scraper = WebScraper()

    # CollectorService を組み立て
    service = CollectorService(firestore, a2a_client, registry, scraper)

    print("=" * 60)
    print("Collector Agent デモ")
    print("=" * 60)

    result = await service.execute("demo_user")

    print(f"\n{'=' * 60}")
    print(f"結果: {result['status']}")
    print(f"収集記事数: {result['articles_total']}")
    print(f"コレクションID: {result['collection_id']}")

    # 保存されたコレクションの中身を表示
    if firestore.create_collection.called:
        collection = firestore.create_collection.call_args[0][0]
        print(f"\n--- 収集された記事一覧 ({len(collection.articles)}件) ---")
        for i, article in enumerate(collection.articles, 1):
            print(f"\n[{i}] {article.title}")
            print(f"    URL: {article.url}")
            print(f"    ソース: {article.source} ({article.source_type.value})")
            print(f"    スコアリング: {article.scoring_status.value}")
            if article.meta_description:
                print(f"    meta: {article.meta_description[:100]}")
            if article.content:
                print(f"    内容: {article.content[:100]}...")

    # A2A 送信の確認
    if a2a_client.send_message.called:
        call = a2a_client.send_message.call_args
        print(f"\n--- Librarian への A2A メッセージ ---")
        print(f"    送信先: {call[1]['agent_url']}")
        print(f"    スキル: {call[1]['skill']}")
        print(f"    パラメータ: {call[1]['params']}")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())

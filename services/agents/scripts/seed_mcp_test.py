"""MCP サーバー動作確認用のシードスクリプト

Firebase Emulator にサンプルデータを投入して、MCP ツールの動作確認を行う。

使い方:
  # ターミナル1: Emulator 起動
  make run-emulator

  # ターミナル2: シードデータ投入
  cd services/agents
  FIRESTORE_EMULATOR_HOST=localhost:8080 .venv/bin/python -m scripts.seed_mcp_test
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from google.cloud import firestore

from shared.models import generate_article_id

USER_ID = "ren"
TODAY = datetime.now().strftime("%Y-%m-%d")


async def _write_articles(db, collection_id: str, user_id: str, articles: list[dict]):
    """記事リストを articles コレクションにバッチ書き込みする"""
    batch = db.batch()
    for article in articles:
        article_id = generate_article_id(collection_id, article["url"])
        article_data = {
            **article,
            "id": article_id,
            "collection_id": collection_id,
            "user_id": user_id,
        }
        doc_ref = db.collection("articles").document(article_id)
        batch.set(doc_ref, article_data)
    await batch.commit()


async def main():
    db = firestore.AsyncClient(project="curation-persona")

    # Emulator 接続確認
    host = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if not host:
        print("ERROR: FIRESTORE_EMULATOR_HOST が設定されていません")
        sys.exit(1)
    print(f"Firestore Emulator: {host}")

    # === ユーザーデータ ===
    print("\n[1/3] ユーザーデータを投入...")
    await db.collection("users").document(USER_ID).set(
        {
            "user_id": USER_ID,
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
            ],
            "interestProfile": (
                "## 興味関心プロファイル\n\n"
                "### 主要な関心領域\n"
                "- **Web フロントエンド**: Next.js, React, TypeScript の最新動向\n"
                "- **AI/LLM**: Claude, Gemini 等の LLM 活用・エージェント設計\n"
                "- **クラウドインフラ**: GCP (Cloud Run, Firestore), サーバーレス設計\n"
                "- **開発プラクティス**: テスト設計, CI/CD, コード品質\n\n"
                "### 傾向\n"
                "- 実践的なチュートリアルやハンズオン記事を高く評価する\n"
                "- 抽象的な概論よりも具体的な実装例を好む\n"
                "- 新しいツールやフレームワークのリリース情報に関心が高い"
            ),
            "interestProfileUpdatedAt": firestore.SERVER_TIMESTAMP,
        }
    )
    print(f"  ユーザー '{USER_ID}' を作成")

    # === 今日のコレクション ===
    print("\n[2/3] 今日のコレクションを投入...")
    collection_id = f"{USER_ID}_{TODAY}"
    now = datetime.now(timezone.utc)

    # コレクションドキュメント（articles 配列なし）
    await db.collection("collections").document(collection_id).set(
        {
            "id": collection_id,
            "user_id": USER_ID,
            "date": TODAY,
            "status": "completed",
            "created_at": now,
        }
    )

    # 記事を articles コレクションに個別ドキュメントとして投入
    today_articles = [
        {
            "title": "Next.js 15 App Router の新機能まとめ",
            "url": "https://example.com/nextjs-15-app-router",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Next.js 15 で追加された App Router 関連の新機能を解説",
            "content": "Next.js 15 では App Router に大幅な改善が加わりました。Server Actions の安定化、部分プリレンダリング、改善されたキャッシュ戦略など...",
            "scoring_status": "scored",
            "relevance_score": 0.92,
            "relevance_reason": "Web フロントエンド (Next.js) の最新動向に直結",
            "is_pickup": True,
            "research_status": "completed",
            "deep_dive_report": (
                "# Next.js 15 App Router 深掘りレポート\n\n"
                "## 概要\n"
                "Next.js 15 は App Router を中心に大幅な改善を行ったメジャーリリースです。\n\n"
                "## 主な変更点\n"
                "### 1. Server Actions の安定化\n"
                "- `'use server'` ディレクティブが stable に\n"
                "- フォーム送信・データ変更のパターンが確立\n\n"
                "### 2. 部分プリレンダリング (PPR)\n"
                "- 静的シェル + 動的コンテンツのハイブリッドレンダリング\n"
                "- TTFB の大幅改善\n\n"
                "### 3. キャッシュ戦略の改善\n"
                "- fetch キャッシュがデフォルトで no-store に変更\n"
                "- より予測しやすい挙動に\n\n"
                "## まとめ\n"
                "プロダクション利用に向けた安定性と DX の両立を目指した着実なアップデートです。"
            ),
            "user_rating": 5,
            "user_comment": "PPR の仕組みが分かりやすく解説されていて良い",
            "published_at": now.isoformat(),
        },
        {
            "title": "Claude Code で開発ワークフローを自動化する",
            "url": "https://example.com/claude-code-workflow",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "Claude Code を使った実践的な開発自動化の手法を紹介",
            "content": "Claude Code は CLI ベースの AI コーディングアシスタントです。MCP サーバー連携やカスタムスラッシュコマンドを活用して...",
            "scoring_status": "scored",
            "relevance_score": 0.88,
            "relevance_reason": "AI/LLM 活用 × 開発プラクティスの交差領域",
            "is_pickup": True,
            "research_status": "completed",
            "deep_dive_report": (
                "# Claude Code 開発ワークフロー自動化 深掘りレポート\n\n"
                "## 概要\n"
                "Claude Code を活用した開発フロー最適化の実践例をまとめました。\n\n"
                "## 主要テクニック\n"
                "### 1. MCP サーバー連携\n"
                "- Firestore / Notion 等のデータソースを MCP で公開\n"
                "- Claude がプロジェクト固有データに直接アクセス\n\n"
                "### 2. CLAUDE.md によるコンテキスト管理\n"
                "- プロジェクト規約・アーキテクチャの明文化\n"
                "- 一貫性のあるコード生成を実現\n\n"
                "## まとめ\n"
                "ツールとコンテキストの適切な設計が自動化の品質を決める。"
            ),
            "user_rating": 4,
            "user_comment": None,
            "published_at": now.isoformat(),
        },
        {
            "title": "Firestore でのデータモデリングベストプラクティス 2025",
            "url": "https://example.com/firestore-data-modeling",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Firestore のデータ設計パターンと注意点を体系的に整理",
            "content": "Firestore は柔軟な NoSQL データベースですが、適切なデータモデリングが性能とコストに大きく影響します...",
            "scoring_status": "scored",
            "relevance_score": 0.75,
            "relevance_reason": "クラウドインフラ (Firestore) に関連",
            "is_pickup": False,
            "research_status": None,
            "deep_dive_report": None,
            "user_rating": None,
            "user_comment": None,
            "published_at": now.isoformat(),
        },
        {
            "title": "Python 3.13 の新機能: フリースレッド GIL",
            "url": "https://example.com/python-313-free-threading",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "Python 3.13 で実験的に導入されたフリースレッド GIL の解説",
            "content": "Python 3.13 では GIL を無効化するフリースレッドモードが実験的にサポートされました...",
            "scoring_status": "scored",
            "relevance_score": 0.60,
            "relevance_reason": "Python の言語進化に関する情報",
            "is_pickup": False,
            "research_status": None,
            "deep_dive_report": None,
            "user_rating": None,
            "user_comment": None,
            "published_at": now.isoformat(),
        },
        {
            "title": "Kubernetes 1.32 リリースノート解説",
            "url": "https://example.com/k8s-132",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "Kubernetes 1.32 の主要な変更点をピックアップ",
            "content": None,
            "scoring_status": "scored",
            "relevance_score": 0.35,
            "relevance_reason": "インフラ関連だが Kubernetes は主要関心外",
            "is_pickup": False,
            "research_status": None,
            "deep_dive_report": None,
            "user_rating": None,
            "user_comment": None,
            "published_at": now.isoformat(),
        },
    ]
    await _write_articles(db, collection_id, USER_ID, today_articles)
    print(f"  コレクション '{collection_id}' を作成 (記事5件、ピックアップ2件)")

    # === 過去の高評価記事用コレクション ===
    print("\n[3/3] 過去コレクション（高評価記事あり）を投入...")
    old_collection_id = f"{USER_ID}_2025-01-10"

    # コレクションドキュメント
    await db.collection("collections").document(old_collection_id).set(
        {
            "id": old_collection_id,
            "user_id": USER_ID,
            "date": "2025-01-10",
            "status": "completed",
            "created_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
        }
    )

    # 記事ドキュメント
    old_articles = [
        {
            "title": "Gemini API で構造化出力を使いこなす",
            "url": "https://example.com/gemini-structured-output",
            "source": "Zenn Trending",
            "source_type": "rss",
            "scoring_status": "scored",
            "relevance_score": 0.85,
            "relevance_reason": "AI/LLM 活用の実践記事",
            "is_pickup": True,
            "user_rating": 5,
            "user_comment": "JSON Schema 指定の具体例が参考になった",
            "content": "Gemini API の structured output 機能を使って、LLM の出力を Pydantic モデルに直接マッピングする手法を解説...",
            "published_at": "2025-01-10T08:00:00+00:00",
        },
        {
            "title": "Cloud Run でのコールドスタート対策",
            "url": "https://example.com/cloud-run-cold-start",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "scoring_status": "scored",
            "relevance_score": 0.70,
            "relevance_reason": "GCP インフラの実践的な知見",
            "is_pickup": False,
            "user_rating": 4,
            "user_comment": "min-instances の設定例が実用的",
            "content": "Cloud Run のコールドスタート問題に対する実践的な対策を紹介...",
            "published_at": "2025-01-10T07:00:00+00:00",
        },
    ]
    await _write_articles(db, old_collection_id, USER_ID, old_articles)
    print(f"  コレクション '{old_collection_id}' を作成 (高評価記事2件)")

    # === 完了 ===
    print(f"\nシード完了!")
    print(f"Firestore Emulator UI: http://localhost:4000/firestore/default/data")
    print(f"\nMCP サーバーで確認:")
    print(f"  FIRESTORE_EMULATOR_HOST=localhost:8080 CURATION_USER_ID=ren \\")
    print(f"    .venv/bin/python mcp_server.py")


if __name__ == "__main__":
    asyncio.run(main())

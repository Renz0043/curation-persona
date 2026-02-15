"""本番 Firestore にデモ用シードデータを投入するスクリプト

固定 user_id (default_user) で、ユーザー設定・コレクション・記事を作成します。

Usage:
    cd services/agents && .venv/bin/python -m scripts.seed_production
"""

import asyncio
import hashlib
from datetime import datetime, timezone

from google.cloud import firestore

PROJECT_ID = "curation-persona-c4747"
USER_ID = "default_user"


def generate_article_id(collection_id: str, url: str) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"{collection_id}_{url_hash}"


async def seed_user(db: firestore.AsyncClient):
    """ユーザー設定を作成"""
    user_data = {
        "email": "demo@example.com",
        "api_key": "cp_live_sk_demo1234567890abcdef",
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
                "id": "src_publickey",
                "type": "rss",
                "name": "Publickey",
                "enabled": False,
                "config": {"url": "https://www.publickey1.jp/atom.xml"},
            },
        ],
        "interestProfile": (
            "AI・機械学習技術（特にLLMアプリケーション開発、RAG、エージェント設計）に強い関心を持っています。"
            "Webフロントエンド技術（React/Next.js）やクラウドインフラ（GCP、Firebase）も継続的に追っています。"
            "プロダクトマネジメントやスタートアップのビジネスモデルにも関心があり、"
            "技術とビジネスの交差点にある情報を特に重視しています。"
        ),
        "interestProfileUpdatedAt": datetime(2026, 2, 14, 10, 30, 0, tzinfo=timezone.utc),
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    }
    await db.collection("users").document(USER_ID).set(user_data)
    print(f"  ユーザー: users/{USER_ID}")


async def seed_daily_collection(db: firestore.AsyncClient):
    """今日の日次コレクション + 記事"""
    today = "2026-02-15"
    collection_id = f"{USER_ID}_{today}"

    await db.collection("collections").document(collection_id).set({
        "user_id": USER_ID,
        "date": today,
        "status": "completed",
        "created_at": datetime(2026, 2, 15, 6, 0, 0, tzinfo=timezone.utc),
    })

    articles = [
        {
            "title": "Claude 4.5 Sonnet: マルチモーダルAIの新時代",
            "url": "https://example.com/claude-4-5-sonnet",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Anthropicが発表したClaude 4.5 Sonnetは、テキスト・画像・コードの統合処理で大幅な性能向上を実現。特にコーディング支援とドキュメント理解で従来モデルを上回る。",
            "content": "Anthropicは本日、次世代AIモデル「Claude 4.5 Sonnet」を発表しました。\n\n本モデルはマルチモーダル処理能力が大幅に強化され、テキスト、画像、コードを統合的に理解・生成できるようになっています。",
            "relevance_score": 0.95,
            "relevance_reason": "AI・LLM技術の最新動向として、ユーザーの主要関心領域に合致。開発ツールとしての実用性も高い。",
            "is_pickup": True,
            "scoring_status": "scored",
            "research_status": "completed",
            "deep_dive_report": "# Claude 4.5 Sonnet 深掘りレポート\n\n## 概要\nAnthropicが発表したClaude 4.5 Sonnetは、前世代と比較して大幅な性能向上を果たしたマルチモーダルAIモデルです。\n\n## 主要な改善点\n\n### 1. マルチモーダル統合処理\n- テキスト、画像、コードの同時理解が可能に\n- ドキュメントと図表の関連性を自動的に解析\n\n### 2. コーディング支援の進化\n- 複数ファイルにまたがるリファクタリング\n- 設計パターンの自動提案\n- テストコード生成の精度向上\n\n### 3. 推論能力の強化\n- 複雑な論理的推論タスクでの正確性向上\n- 長文コンテキストでの一貫性維持\n\n## 業界への影響\nソフトウェア開発の生産性向上が見込まれ、特にスタートアップや小規模チームにとって大きなレバレッジとなる可能性があります。",
            "cross_industry_feedback": {
                "perspectives": [
                    {
                        "industry": "製造業",
                        "expert_comment": "品質管理の自動化にマルチモーダルAIを活用できる可能性があります。画像検査と仕様書の自動照合は、製造現場の大きな課題を解決できるでしょう。",
                    },
                    {
                        "industry": "教育",
                        "expert_comment": "個別最適化された学習支援への応用が期待されます。生徒のノートや回答を画像で読み取り、理解度を分析するといった活用が考えられます。",
                    },
                    {
                        "industry": "金融",
                        "expert_comment": "財務レポートの自動分析やリスク評価の高度化に寄与する可能性があります。ただし、AI判断の説明可能性（Explainability）の確保が重要な課題です。",
                    },
                ],
            },
            "user_rating": 5,
            "published_at": datetime(2026, 2, 15, 3, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Next.js 16のServer Actions完全ガイド",
            "url": "https://example.com/nextjs-16-server-actions",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Next.js 16で大幅に改善されたServer Actionsの使い方を包括的に解説。フォーム処理、データ変更、楽観的更新の実践パターンを紹介。",
            "content": "Next.js 16では、Server Actionsが正式にstableとなり、大幅な改善が加えられました。",
            "relevance_score": 0.88,
            "relevance_reason": "Next.jsはユーザーが利用中のフレームワーク。最新バージョンの実践ガイドは直接的に有用。",
            "is_pickup": True,
            "scoring_status": "scored",
            "research_status": "completed",
            "deep_dive_report": "# Next.js 16 Server Actions ガイド\n\n## 概要\nServer ActionsはNext.js 16の中核機能の一つです。\n\n## 主なユースケース\n- フォームのサーバーサイドバリデーション\n- データベースの直接操作\n- 認証フローの簡略化\n\n## ベストプラクティス\n- エラーハンドリングの統一パターン\n- 楽観的更新の実装方法\n- セキュリティ上の注意点",
            "published_at": datetime(2026, 2, 15, 1, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Firestore のコスト最適化: 読み取り回数を80%削減した方法",
            "url": "https://example.com/firestore-cost-optimization",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "Firestoreの読み取りコストを大幅に削減するためのキャッシュ戦略とクエリ最適化のテクニックを実例とともに紹介。",
            "relevance_score": 0.82,
            "relevance_reason": "Firebase/Firestoreはユーザーのインフラスタック。コスト最適化は実務に直結する実践的な知識。",
            "is_pickup": False,
            "scoring_status": "scored",
            "research_status": "pending",
            "published_at": datetime(2026, 2, 14, 22, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "RAGシステムの評価フレームワーク比較: RAGAS vs DeepEval",
            "url": "https://example.com/rag-evaluation-frameworks",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "RAGシステムの品質評価に使えるフレームワークを比較検討。RAGAS、DeepEval、独自メトリクスの設計手法を解説。",
            "relevance_score": 0.78,
            "relevance_reason": "RAGはLLMアプリケーション開発の核心技術。評価手法の理解は品質向上に直結。",
            "is_pickup": False,
            "scoring_status": "scored",
            "published_at": datetime(2026, 2, 14, 20, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "スタートアップのPMが語るプロダクト・マーケット・フィットの見極め方",
            "url": "https://example.com/pmf-startup-guide",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "複数のスタートアップでPMFを達成した経験者が、定量・定性の両面からPMFを判断するフレームワークを公開。",
            "relevance_score": 0.65,
            "relevance_reason": "プロダクトマネジメントとスタートアップのビジネスモデルに関する知見。技術とビジネスの交差点として関心領域に該当。",
            "is_pickup": False,
            "scoring_status": "scored",
            "published_at": datetime(2026, 2, 14, 18, 0, 0, tzinfo=timezone.utc),
        },
    ]

    for art_data in articles:
        art_id = generate_article_id(collection_id, art_data["url"])
        doc_data = {"collection_id": collection_id, "user_id": USER_ID, **art_data}
        await db.collection("articles").document(art_id).set(doc_data)

    print(f"  日次コレクション: {collection_id} ({len(articles)}件)")


async def main():
    print("=" * 60)
    print("  本番 Firestore シードデータ投入")
    print(f"  Project: {PROJECT_ID}")
    print(f"  User ID: {USER_ID}")
    print("=" * 60)

    db = firestore.AsyncClient(project=PROJECT_ID)

    print("\n[1/3] ユーザー設定の作成...")
    await seed_user(db)

    print("\n[2/3] 日次コレクションと記事の作成...")
    await seed_daily_collection(db)

    print("\n[3/3] 完了!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

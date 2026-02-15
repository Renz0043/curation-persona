"""Firestore Emulator シードデータ投入スクリプト

フロントエンド開発用にテストデータを Emulator に投入します。

Usage:
    make seed

注意:
    Auth Emulator はカスタム UID を指定できないため、
    signUp で生成されたランダム UID を Firestore の user_id として使用します。
"""

import asyncio
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from google.cloud import firestore  # noqa: E402

PROJECT_ID = "curation-persona"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"
AUTH_EMULATOR_HOST = "localhost:9099"


def generate_article_id(collection_id: str, url: str) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"{collection_id}_{url_hash}"


def clear_auth_users():
    """Auth Emulator の全ユーザーを削除"""
    url = f"http://{AUTH_EMULATOR_HOST}/emulator/v1/projects/{PROJECT_ID}/accounts"
    req = urllib.request.Request(url, method="DELETE")
    try:
        urllib.request.urlopen(req)
    except Exception:
        pass


def create_auth_user() -> str:
    """Auth Emulator にテストユーザーを作成し、生成された UID を返す"""
    url = (
        f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1"
        f"/accounts:signUp?key=fake-api-key"
    )
    data = json.dumps({
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "returnSecureToken": True,
    }).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    uid = result["localId"]
    print(f"  Auth ユーザー: {uid} ({TEST_USER_EMAIL})")
    return uid


async def clear_all(db: firestore.AsyncClient):
    """既存データを全削除"""
    clear_auth_users()
    for col_name in ["users", "collections", "articles"]:
        async for doc in db.collection(col_name).stream():
            await doc.reference.delete()
    print("  既存データを削除しました")


async def seed_user(db: firestore.AsyncClient) -> str:
    """テストユーザーを作成（Auth + Firestore）し、UID を返す"""
    uid = create_auth_user()
    user_data = {
        "email": TEST_USER_EMAIL,
        "api_key": "cp_live_sk_test1234567890abcdef",
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
    await db.collection("users").document(uid).set(user_data)
    print(f"  Firestore ユーザー: users/{uid}")
    return uid


async def seed_daily_collection(db: firestore.AsyncClient, user_id: str):
    """今日の日次コレクション + 記事"""
    today = "2026-02-15"
    collection_id = f"{user_id}_{today}"

    await db.collection("collections").document(collection_id).set({
        "user_id": user_id,
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
            "content": "Anthropicは本日、次世代AIモデル「Claude 4.5 Sonnet」を発表しました。\n\n本モデルはマルチモーダル処理能力が大幅に強化され、テキスト、画像、コードを統合的に理解・生成できるようになっています。\n\n特にコーディング支援の分野では、複数ファイルにまたがるリファクタリングや、設計パターンの提案など、より高度なタスクに対応できるようになりました。",
            "relevance_score": 0.95,
            "relevance_reason": "AI・LLM技術の最新動向として、ユーザーの主要関心領域に合致。開発ツールとしての実用性も高い。",
            "is_pickup": True,
            "scoring_status": "scored",
            "research_status": "completed",
            "deep_dive_report": "# Claude 4.5 Sonnet 深掘りレポート\n\n## 概要\nAnthropicが発表したClaude 4.5 Sonnetは、前世代と比較して大幅な性能向上を果たしたマルチモーダルAIモデルです。\n\n## 主要な改善点\n\n### 1. マルチモーダル統合処理\n- テキスト、画像、コードの同時理解が可能に\n- ドキュメントと図表の関連性を自動的に解析\n\n### 2. コーディング支援の進化\n- 複数ファイルにまたがるリファクタリング\n- 設計パターンの自動提案\n- テストコード生成の精度向上\n\n### 3. 推論能力の強化\n- 複雑な論理的推論タスクでの正確性向上\n- 長文コンテキストでの一貫性維持\n\n## 業界への影響\nソフトウェア開発の生産性向上が見込まれ、特にスタートアップや小規模チームにとって大きなレバレッジとなる可能性があります。\n\n## キーポイント\n- マルチモーダル処理で新たなユースケースが開拓される\n- コーディング支援ツールの競争が激化\n- エンタープライズ採用の加速が予想される",
            "cross_industry_feedback": {
                "abstracted_challenge": "高度なAI技術の実用化と組織導入における課題",
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
            "user_comment": "非常に参考になった。実際のプロジェクトで活用したい。",
            "published_at": datetime(2026, 2, 15, 3, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Next.js 16のServer Actions完全ガイド",
            "url": "https://example.com/nextjs-16-server-actions",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Next.js 16で大幅に改善されたServer Actionsの使い方を包括的に解説。フォーム処理、データ変更、楽観的更新の実践パターンを紹介。",
            "content": "Next.js 16では、Server Actionsが正式にstableとなり、大幅な改善が加えられました。\n\nServer Actionsを使うことで、APIルートを作成せずにサーバーサイドの処理を直接呼び出すことが可能です。\n\nこの記事では、フォーム処理、データベース操作、楽観的更新の3つのパターンを詳しく解説します。",
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
            "content": "Firestoreを本番運用していると、読み取り回数によるコストが課題になることがあります。\n\n本記事では、キャッシュレイヤーの導入、クエリの最適化、オフラインパーシステンスの活用など、コスト削減に効果的な手法を紹介します。",
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
            "content": "RAGシステムの品質をどう評価するかは、実用化における大きな課題です。\n\n本記事ではRAGASとDeepEvalという2つの主要な評価フレームワークを比較し、それぞれの特徴と適用シーンを整理します。",
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
            "content": "プロダクト・マーケット・フィットの達成は、スタートアップの最重要マイルストーンです。\n\nしかし、PMFは「達成した瞬間」がわかりにくいという問題があります。この記事では、実際の経験に基づいた判断フレームワークを紹介します。",
            "relevance_score": 0.65,
            "relevance_reason": "プロダクトマネジメントとスタートアップのビジネスモデルに関する知見。技術とビジネスの交差点として関心領域に該当。",
            "is_pickup": False,
            "scoring_status": "scored",
            "published_at": datetime(2026, 2, 14, 18, 0, 0, tzinfo=timezone.utc),
        },
    ]

    for art_data in articles:
        art_id = generate_article_id(collection_id, art_data["url"])
        doc_data = {"collection_id": collection_id, "user_id": user_id, **art_data}
        await db.collection("articles").document(art_id).set(doc_data)

    print(f"  日次コレクション: {collection_id} ({len(articles)}件)")

    # 前日のコレクションも追加
    yesterday = "2026-02-14"
    yesterday_id = f"{user_id}_{yesterday}"
    await db.collection("collections").document(yesterday_id).set({
        "user_id": user_id,
        "date": yesterday,
        "status": "completed",
        "created_at": datetime(2026, 2, 14, 6, 0, 0, tzinfo=timezone.utc),
    })

    yesterday_articles = [
        {
            "title": "Gemini 2.5 Pro のマルチモーダル推論を試す",
            "url": "https://example.com/gemini-2-5-pro-multimodal",
            "source": "Zenn Trending",
            "source_type": "rss",
            "summary": "Google DeepMindが公開したGemini 2.5 Proのマルチモーダル推論能力を実際にAPIから試した結果をレポート。",
            "relevance_score": 0.91,
            "relevance_reason": "Gemini APIの最新アップデート。LLMアプリケーション開発に直結。",
            "is_pickup": True,
            "scoring_status": "scored",
            "research_status": "completed",
            "deep_dive_report": "# Gemini 2.5 Pro レポート\n\n## 概要\nGemini 2.5 Proは画像・動画・音声を統合的に処理できるマルチモーダルモデルです。\n\n## テスト結果\n- 画像認識精度の大幅な向上\n- コード生成能力の改善\n- 日本語処理の品質向上",
            "published_at": datetime(2026, 2, 14, 5, 0, 0, tzinfo=timezone.utc),
            "user_rating": 4,
        },
        {
            "title": "Tailwind CSS 4.0: 新しいエンジンとユーティリティの進化",
            "url": "https://example.com/tailwind-css-4",
            "source": "はてなブックマーク - テクノロジー",
            "source_type": "rss",
            "summary": "Tailwind CSS 4.0の新エンジンOxideの仕組みと、新しいユーティリティクラスの使い方を解説。",
            "relevance_score": 0.75,
            "relevance_reason": "フロントエンド技術の最新動向。ユーザーが利用中のCSSフレームワーク。",
            "is_pickup": False,
            "scoring_status": "scored",
            "published_at": datetime(2026, 2, 14, 3, 0, 0, tzinfo=timezone.utc),
        },
    ]

    for art_data in yesterday_articles:
        art_id = generate_article_id(yesterday_id, art_data["url"])
        doc_data = {"collection_id": yesterday_id, "user_id": user_id, **art_data}
        await db.collection("articles").document(art_id).set(doc_data)

    print(f"  日次コレクション: {yesterday_id} ({len(yesterday_articles)}件)")


async def seed_bookmark_collection(db: firestore.AsyncClient, user_id: str):
    """ブックマークコレクション + 記事"""
    bm_collection_id = f"bm_{user_id}"

    await db.collection("collections").document(bm_collection_id).set({
        "user_id": user_id,
        "date": "",
        "status": "completed",
        "created_at": datetime(2026, 2, 10, 0, 0, 0, tzinfo=timezone.utc),
    })

    bookmarks = [
        {
            "title": "LangChainを使ったRAGアプリケーションの構築ガイド",
            "url": "https://example.com/langchain-rag-guide",
            "source": "bookmark",
            "source_type": "bookmark",
            "summary": "LangChainのRetrieval-Augmented Generationパイプラインを使って、ドキュメントQAアプリケーションを構築する包括的なガイド。",
            "relevance_score": 0.0,
            "is_pickup": False,
            "scoring_status": "pending",
            "research_status": "completed",
            "deep_dive_report": "# LangChain RAGガイド 深掘りレポート\n\n## 概要\nRAG（Retrieval-Augmented Generation）は、LLMに外部知識を動的に注入する手法です。\n\n## 構成要素\n- Document Loader: PDF、Webページ等からのデータ取得\n- Text Splitter: チャンク分割\n- Embedding: ベクトル化\n- Vector Store: ベクトル検索\n- Chain: LLMとの統合",
            "published_at": datetime(2026, 2, 12, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "Firebase App Hosting で Next.js をデプロイする",
            "url": "https://example.com/firebase-app-hosting-nextjs",
            "source": "bookmark",
            "source_type": "bookmark",
            "summary": "Firebase App HostingにNext.jsアプリケーションをデプロイする手順と設定のポイントを解説。",
            "relevance_score": 0.0,
            "is_pickup": False,
            "scoring_status": "pending",
            "research_status": "researching",
            "published_at": datetime(2026, 2, 13, 15, 0, 0, tzinfo=timezone.utc),
        },
        {
            "title": "マイクロサービスにおけるイベント駆動アーキテクチャ入門",
            "url": "https://example.com/event-driven-microservices",
            "source": "bookmark",
            "source_type": "bookmark",
            "summary": "マイクロサービス間の通信をイベント駆動で設計するパターンと、Pub/Subを使った実装例。",
            "relevance_score": 0.0,
            "is_pickup": False,
            "scoring_status": "pending",
            "research_status": "pending",
            "published_at": datetime(2026, 2, 14, 8, 0, 0, tzinfo=timezone.utc),
        },
    ]

    for art_data in bookmarks:
        art_id = generate_article_id(bm_collection_id, art_data["url"])
        doc_data = {"collection_id": bm_collection_id, "user_id": user_id, **art_data}
        await db.collection("articles").document(art_id).set(doc_data)

    print(f"  ブックマーク: {bm_collection_id} ({len(bookmarks)}件)")


async def main():
    print("=" * 60)
    print("  Firestore Emulator シードデータ投入")
    print("=" * 60)

    db = firestore.AsyncClient(project=PROJECT_ID)

    print("\n[1/5] 既存データの削除...")
    await clear_all(db)

    print("\n[2/5] テストユーザーの作成...")
    user_id = await seed_user(db)

    print("\n[3/5] 日次コレクションと記事の作成...")
    await seed_daily_collection(db, user_id)

    print("\n[4/5] ブックマークコレクションの作成...")
    await seed_bookmark_collection(db, user_id)

    print("\n[5/5] 完了!")
    print(f"\n  Emulator UI: http://localhost:4000/firestore/default/data")
    print(f"  テストユーザー: {TEST_USER_EMAIL} / {TEST_USER_PASSWORD}")
    print(f"  UID: {user_id}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

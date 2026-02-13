"""E2E パイプライン検証スクリプト

Firebase Emulator + 3エージェントでパイプライン全体を検証します。

事前準備 (5つのターミナルで実行):
  ターミナル1: make run-emulator         # Firestore Emulator + UI
  ターミナル2: make run-collector-emu     # Collector Agent (:8001)
  ターミナル3: make run-librarian-emu     # Librarian Agent (:8002)
  ターミナル4: make run-researcher-emu    # Researcher Agent (:8003)
  ターミナル5: make e2e                   # このスクリプト

Firestore Emulator UI: http://localhost:4000/firestore/default/data
"""

import asyncio
import os
import sys
import time

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

import httpx
from google.cloud import firestore

COLLECTOR_URL = "http://localhost:8001"
LIBRARIAN_URL = "http://localhost:8002"
RESEARCHER_URL = "http://localhost:8003"

TEST_USER_ID = "e2e_test_user"
TEST_SOURCES = [
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
]


def header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def sub(text: str):
    print(f"  {text}")


async def check_emulator() -> bool:
    """Firebase Emulator の起動確認"""
    host = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://{host}/")
            return resp.status_code == 200
    except Exception:
        return False


async def check_agents() -> dict[str, bool]:
    """各エージェントの起動確認"""
    results = {}
    agents = {
        "Collector": COLLECTOR_URL,
        "Librarian": LIBRARIAN_URL,
        "Researcher": RESEARCHER_URL,
    }
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in agents.items():
            try:
                resp = await client.get(f"{url}/health")
                results[name] = resp.status_code == 200
            except Exception:
                results[name] = False
    return results


async def seed_user(db: firestore.AsyncClient):
    """テストユーザーをシード"""
    header("Step 1: テストユーザーシード")
    await db.collection("users").document(TEST_USER_ID).set(
        {
            "user_id": TEST_USER_ID,
            "sources": TEST_SOURCES,
        }
    )

    doc = await db.collection("users").document(TEST_USER_ID).get()
    data = doc.to_dict()
    sub(f"ユーザーID: {data['user_id']}")
    sub(f"ソース数: {len(data['sources'])}")
    for src in data["sources"]:
        sub(f"  - {src['name']} (type={src['type']}, enabled={src['enabled']})")
    sub("")
    sub("Firestore Emulator UI で確認: http://localhost:4000/firestore/default/data")


async def trigger_collector() -> str | None:
    """Collector Agent にA2Aメッセージ送信 → Librarian スコアリングまで待機"""
    header("Step 2: Collector -> Librarian パイプライン実行")
    sub("Collector: RSS取得 -> Firestore保存 -> A2A -> Librarian: スコアリング")
    sub("(実RSSフィード取得 + Gemini API呼び出しのため、数十秒〜数分かかります)")
    sub("")

    from shared.a2a_client import A2AClient

    client = A2AClient()
    start = time.time()

    try:
        response = await client.send_message(
            agent_url=COLLECTOR_URL,
            skill="collect_articles",
            params={"user_id": TEST_USER_ID},
        )
        elapsed = time.time() - start
        sub(f"完了! ({elapsed:.1f}秒)")

        # レスポンスからテキストを抽出
        if hasattr(response, "result") and hasattr(response.result, "status"):
            sub(f"ステータス: {response.result.status}")
        return "ok"
    except Exception as e:
        elapsed = time.time() - start
        sub(f"エラー ({elapsed:.1f}秒): {e}")
        return None


async def _get_articles_for_collection(
    db: firestore.AsyncClient, collection_id: str
) -> list[dict]:
    """articles コレクションからコレクションに属する記事を取得"""
    articles = []
    query = db.collection("articles").where("collection_id", "==", collection_id)
    async for doc in query.stream():
        articles.append(doc.to_dict())
    return articles


async def show_collection(db: firestore.AsyncClient) -> dict | None:
    """Firestoreからコレクションを取得して表示"""
    header("Step 3: Firestore データ確認")

    query = (
        db.collection("collections")
        .where("user_id", "==", TEST_USER_ID)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
    )

    docs = []
    async for doc in query.stream():
        docs.append(doc.to_dict())

    if not docs:
        sub("コレクションが見つかりません")
        return None

    col = docs[0]
    # articles コレクションから記事を取得
    articles = await _get_articles_for_collection(db, col["id"])
    col["articles"] = articles

    pickups = [a for a in articles if a.get("is_pickup")]
    scored = [a for a in articles if a.get("scoring_status") == "scored"]

    sub(f"コレクションID: {col['id']}")
    sub(f"ステータス: {col['status']}")
    sub(f"記事数: {len(articles)}")
    sub(f"スコアリング済み: {len(scored)}/{len(articles)}")
    sub(f"ピックアップ: {len(pickups)}件")

    if articles:
        sorted_articles = sorted(
            articles, key=lambda a: a.get("relevance_score", 0), reverse=True
        )
        print(f"\n  --- スコア上位5件 ---")
        for i, a in enumerate(sorted_articles[:5], 1):
            pickup = " [PICKUP]" if a.get("is_pickup") else ""
            score = a.get("relevance_score", "N/A")
            reason = a.get("relevance_reason", "")[:60]
            sub(f"[{i}] {a['title'][:55]}")
            sub(f"    スコア: {score} / {reason}")
            sub(f"    URL: {a['url']}{pickup}")

        if len(sorted_articles) > 5:
            print(f"\n  --- スコア下位3件 ---")
            for i, a in enumerate(sorted_articles[-3:], len(sorted_articles) - 2):
                score = a.get("relevance_score", "N/A")
                sub(f"[{i}] {a['title'][:55]}")
                sub(f"    スコア: {score}")

    return col


async def trigger_researcher(db: firestore.AsyncClient, collection: dict):
    """Researcher Agent にピックアップ記事の深掘りを依頼"""
    header("Step 4: Researcher Agent 実行")

    articles = collection.get("articles", [])
    pickups = [a for a in articles if a.get("is_pickup")]

    if not pickups:
        sub("ピックアップ記事がないため、スキップ")
        return

    from shared.a2a_client import A2AClient

    client = A2AClient()

    for i, article in enumerate(pickups, 1):
        sub(f"[{i}/{len(pickups)}] {article['title'][:50]}")
        sub(f"深掘りレポート生成中... (Gemini Pro 使用)")

        start = time.time()
        try:
            await client.send_message(
                agent_url=RESEARCHER_URL,
                skill="research_article",
                params={
                    "user_id": TEST_USER_ID,
                    "collection_id": collection["id"],
                    "article_url": article["url"],
                },
            )
            elapsed = time.time() - start
            sub(f"完了! ({elapsed:.1f}秒)")
        except Exception as e:
            elapsed = time.time() - start
            sub(f"エラー ({elapsed:.1f}秒): {e}")
        print()

    # 更新後の記事データを確認
    updated_articles = await _get_articles_for_collection(db, collection["id"])

    print(f"  --- 深掘りレポート確認 ---")
    for a in updated_articles:
        if a.get("deep_dive_report"):
            sub(f"[{a['title'][:40]}]")
            sub(f"ステータス: {a.get('research_status')}")
            report_lines = a["deep_dive_report"].split("\n")[:5]
            for line in report_lines:
                sub(f"  {line}")
            sub("  ...")
            print()


async def cleanup(db: firestore.AsyncClient):
    """テストデータの削除"""
    header("クリーンアップ")

    # ユーザー削除
    await db.collection("users").document(TEST_USER_ID).delete()
    sub(f"ユーザー '{TEST_USER_ID}' を削除")

    # コレクション削除
    query = db.collection("collections").where("user_id", "==", TEST_USER_ID)
    col_count = 0
    collection_ids = []
    async for doc in query.stream():
        collection_ids.append(doc.id)
        await doc.reference.delete()
        col_count += 1
    sub(f"コレクション {col_count}件 を削除")

    # 記事削除
    art_count = 0
    for col_id in collection_ids:
        art_query = db.collection("articles").where("collection_id", "==", col_id)
        async for doc in art_query.stream():
            await doc.reference.delete()
            art_count += 1
    sub(f"記事 {art_count}件 を削除")


async def main():
    print("\n" + "=" * 60)
    print("  E2E パイプライン検証")
    print("  Firebase Emulator + Collector -> Librarian -> Researcher")
    print("=" * 60)

    # === Step 0: 起動確認 ===
    header("Step 0: サービス起動確認")

    emulator_ok = await check_emulator()
    host = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    if emulator_ok:
        sub(f"[OK] Firebase Emulator ({host})")
    else:
        sub(f"[NG] Firebase Emulator ({host}) - 起動していません")
        sub("")
        sub("以下のコマンドで起動してください:")
        sub("  make run-emulator")
        sys.exit(1)

    agent_status = await check_agents()
    all_agents_ok = True
    for name, ok in agent_status.items():
        status = "[OK]" if ok else "[NG]"
        sub(f"{status} {name}")
        if not ok:
            all_agents_ok = False

    if not all_agents_ok:
        sub("")
        sub("以下のコマンドでエージェントを起動してください:")
        sub("  make run-collector-emu  (ターミナル2)")
        sub("  make run-librarian-emu  (ターミナル3)")
        sub("  make run-researcher-emu (ターミナル4)")

        # Collector + Librarian があれば Step 2 まで可能
        if not agent_status.get("Collector"):
            sub("")
            sub("Collector が起動していないため、中断します。")
            sys.exit(1)

        if not agent_status.get("Librarian"):
            sub("")
            sub("[!] Librarian が未起動: Collector の A2A 送信が失敗します。")
            resp = input("  それでも続行しますか? (y/N): ")
            if resp.lower() != "y":
                sys.exit(1)

    # Firestore 接続
    db = firestore.AsyncClient(project="curation-persona")

    # === Step 1: シード ===
    await seed_user(db)

    # === Step 2: Collector -> Librarian ===
    sub("")
    input("  Enter で Collector -> Librarian パイプラインを開始...")
    result = await trigger_collector()

    # === Step 3: 結果確認 ===
    collection = await show_collection(db)

    # === Step 4: Researcher (optional) ===
    if collection and agent_status.get("Researcher"):
        pickups = [a for a in collection.get("articles", []) if a.get("is_pickup")]
        if pickups:
            sub("")
            resp = input(
                f"  ピックアップ{len(pickups)}件の深掘りレポートを生成しますか? (y/N): "
            )
            if resp.lower() == "y":
                await trigger_researcher(db, collection)

    # === Emulator UI ===
    header("Firestore Emulator UI")
    sub("http://localhost:4000/firestore/default/data でデータを確認できます")

    # === クリーンアップ ===
    sub("")
    resp = input("  テストデータを削除しますか? (y/N): ")
    if resp.lower() == "y":
        await cleanup(db)

    header("完了")


if __name__ == "__main__":
    asyncio.run(main())

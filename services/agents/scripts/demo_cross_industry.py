"""異業種フィードバック（Cross-Industry Feedback）動作確認スクリプト

is_pickup=True の記事に対して深掘りレポート生成後、
異業種フィードバックが生成・保存されることを確認します。

事前準備 (3つのターミナルで実行):
  ターミナル1: make run-emulator         # Firestore Emulator
  ターミナル2: make run-researcher-emu   # Researcher Agent (:8003)
  ターミナル3: cd services/agents && .venv/bin/python -m scripts.demo_cross_industry
"""

import asyncio
import json
import os
import sys
import time
import uuid

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

import httpx
from google.cloud import firestore

from shared.models import generate_article_id

RESEARCHER_URL = "http://localhost:8003"
TEST_USER_ID = "cross_ind_test_user"
TEST_COLLECTION_ID = f"col_ci_{uuid.uuid4().hex[:8]}"
TEST_ARTICLE_URL = "https://example.com/cross-industry-test"


def header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def sub(text: str):
    print(f"  {text}")


async def check_prerequisites() -> bool:
    """Emulator と Researcher Agent の起動確認"""
    header("起動確認")
    ok = True

    host = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            await client.get(f"http://{host}/")
            sub(f"[OK] Firestore Emulator ({host})")
        except Exception:
            sub(f"[NG] Firestore Emulator ({host})")
            sub("     make run-emulator で起動してください")
            ok = False

        try:
            resp = await client.get(f"{RESEARCHER_URL}/health")
            if resp.status_code == 200:
                sub(f"[OK] Researcher Agent ({RESEARCHER_URL})")
            else:
                raise Exception()
        except Exception:
            sub(f"[NG] Researcher Agent ({RESEARCHER_URL})")
            sub("     make run-researcher-emu で起動してください")
            ok = False

    return ok


async def seed_test_data(db: firestore.AsyncClient):
    """テスト用ユーザーとコレクション・記事をシード"""
    header("テストデータ作成")

    # ユーザー作成
    await db.collection("users").document(TEST_USER_ID).set(
        {"user_id": TEST_USER_ID, "sources": []}
    )
    sub(f"ユーザー: {TEST_USER_ID}")

    # コレクション作成（記事は別コレクション）
    await db.collection("collections").document(TEST_COLLECTION_ID).set(
        {
            "id": TEST_COLLECTION_ID,
            "user_id": TEST_USER_ID,
            "date": "2025-01-01",
            "status": "completed",
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    sub(f"コレクション: {TEST_COLLECTION_ID}")

    # 記事を articles コレクションに保存（is_pickup=True）
    article_id = generate_article_id(TEST_COLLECTION_ID, TEST_ARTICLE_URL)
    await db.collection("articles").document(article_id).set(
        {
            "id": article_id,
            "collection_id": TEST_COLLECTION_ID,
            "user_id": TEST_USER_ID,
            "title": "LLMエージェントの安全性評価フレームワーク",
            "url": TEST_ARTICLE_URL,
            "source": "test",
            "source_type": "rss",
            "content": (
                "大規模言語モデル（LLM）を用いた自律エージェントの安全性が注目されている。"
                "エージェントが外部ツールを呼び出す際の権限管理、"
                "プロンプトインジェクション対策、出力のファクトチェックなど、"
                "従来のソフトウェアテストでは対応できない新たな課題が山積している。"
                "本稿では、エージェントの行動を監視・制限するガードレールの設計パターンと、"
                "Red Teaming による脆弱性発見手法を体系的にまとめる。"
            ),
            "scoring_status": "scored",
            "relevance_score": 0.95,
            "relevance_reason": "LLMエージェントの安全性に関する重要トピック",
            "is_pickup": True,
            "research_status": "pending",
        }
    )
    sub(f"記事 (is_pickup=True): {TEST_ARTICLE_URL}")
    sub(f"記事ID: {article_id}")


def parse_sse_events(buffer: str) -> tuple[list[str], str]:
    """SSE バッファからイベントを抽出する。"""
    normalized = buffer.replace("\r\n", "\n").replace("\r", "\n")
    events = []
    while "\n\n" in normalized:
        event_str, normalized = normalized.split("\n\n", 1)
        stripped = event_str.strip()
        if stripped:
            events.append(stripped)
    return events, normalized


def extract_sse_data(event_str: str) -> str | None:
    """SSE イベント文字列から data フィールドを抽出する。"""
    data_parts = []
    for line in event_str.split("\n"):
        if line.startswith("data:"):
            data_parts.append(line[len("data:") :].strip())
    return "\n".join(data_parts) if data_parts else None


async def send_research_request():
    """message/stream リクエストを送信し SSE イベントを表示"""
    header("深掘りレポート + 異業種フィードバック生成")
    sub(f"POST {RESEARCHER_URL}/ (method=message/stream)")
    sub("")

    request_body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/stream",
        "params": {
            "message": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [
                    {
                        "kind": "data",
                        "data": {
                            "skill": "research_article",
                            "user_id": TEST_USER_ID,
                            "collection_id": TEST_COLLECTION_ID,
                            "article_url": TEST_ARTICLE_URL,
                        },
                    }
                ],
            }
        },
    }

    start = time.time()
    event_count = 0
    artifact_text: list[str] = []

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST",
            f"{RESEARCHER_URL}/",
            json=request_body,
            headers={"Accept": "text/event-stream"},
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                sub(f"[ERROR] HTTP {response.status_code}: {body.decode()}")
                return

            sub(f"HTTP {response.status_code} — ストリーミング開始")
            print(f"  {'─'*56}")

            buffer = ""
            async for raw_chunk in response.aiter_text():
                buffer += raw_chunk
                events, buffer = parse_sse_events(buffer)

                for event_str in events:
                    data_str = extract_sse_data(event_str)
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_count += 1
                    elapsed = time.time() - start
                    result = data.get("result", {})
                    kind = result.get("kind", "?")

                    if kind == "status-update":
                        state = result.get("status", {}).get("state", "?")
                        final = result.get("final", False)
                        label = "[FINAL] " if final else ""
                        print(
                            f"  [{event_count:>3}] ({elapsed:>5.1f}s) STATUS  {label}{state}"
                        )
                    elif kind == "artifact-update":
                        parts = result.get("artifact", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            artifact_text.append(text)
                            preview = text.replace("\n", "\\n")[:60]
                            print(
                                f"  [{event_count:>3}] ({elapsed:>5.1f}s) CHUNK   {preview}..."
                            )

    total = time.time() - start
    print(f"  {'─'*56}")
    sub(f"合計イベント数: {event_count}")
    sub(f"レポート文字数: {len(''.join(artifact_text))}")
    sub(f"所要時間: {total:.1f}s")


async def verify_cross_industry_feedback(db: firestore.AsyncClient) -> bool:
    """Firestore の cross_industry_feedback フィールドを検証"""
    header("異業種フィードバック検証")

    article_id = generate_article_id(TEST_COLLECTION_ID, TEST_ARTICLE_URL)
    doc = await db.collection("articles").document(article_id).get()

    if not doc.exists:
        sub("[NG] 記事ドキュメントが見つかりません")
        return False

    data = doc.to_dict()

    # research_status 確認
    status = data.get("research_status", "未設定")
    sub(f"research_status: {status}")

    # deep_dive_report 確認
    report = data.get("deep_dive_report", "")
    sub(f"deep_dive_report: {'あり' if report else 'なし'} ({len(report)}文字)")

    # cross_industry_feedback 確認
    feedback = data.get("cross_industry_feedback")
    if feedback is None:
        sub("[NG] cross_industry_feedback が保存されていません")
        return False

    sub("")
    sub("[OK] cross_industry_feedback が保存されています")
    sub("")

    # 構造を表示
    challenge = feedback.get("abstracted_challenge", "")
    sub(f"抽象化された課題:")
    sub(f"  {challenge}")
    sub("")

    perspectives = feedback.get("perspectives", [])
    sub(f"異業種の視点 ({len(perspectives)}件):")
    for i, p in enumerate(perspectives, 1):
        industry = p.get("industry", "不明")
        comment = p.get("expert_comment", "")
        sub(f"")
        sub(f"  [{i}] {industry}")
        # コメントを80文字ごとに折り返して表示
        for j in range(0, len(comment), 60):
            sub(f"      {comment[j:j+60]}")

    return True


async def cleanup(db: firestore.AsyncClient):
    """テストデータ削除"""
    header("クリーンアップ")
    await db.collection("users").document(TEST_USER_ID).delete()
    sub(f"ユーザー '{TEST_USER_ID}' を削除")

    article_id = generate_article_id(TEST_COLLECTION_ID, TEST_ARTICLE_URL)
    await db.collection("articles").document(article_id).delete()
    sub(f"記事 '{article_id}' を削除")

    await db.collection("collections").document(TEST_COLLECTION_ID).delete()
    sub(f"コレクション '{TEST_COLLECTION_ID}' を削除")


async def main():
    print("\n" + "=" * 60)
    print("  異業種フィードバック (Cross-Industry Feedback) 動作確認")
    print("=" * 60)

    if not await check_prerequisites():
        sys.exit(1)

    db = firestore.AsyncClient(project="curation-persona")

    try:
        await seed_test_data(db)
        await send_research_request()
        ok = await verify_cross_industry_feedback(db)

        if ok:
            header("結果: OK")
            sub("is_pickup=True の記事に異業種フィードバックが正しく生成・保存されました")
        else:
            header("結果: NG")
            sub("異業種フィードバックの生成または保存に問題があります")
    finally:
        sub("")
        resp = input("  テストデータを削除しますか? (Y/n): ")
        if resp.lower() != "n":
            await cleanup(db)

    print()


if __name__ == "__main__":
    asyncio.run(main())

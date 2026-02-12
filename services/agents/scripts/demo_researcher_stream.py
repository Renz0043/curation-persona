"""Researcher Agent SSE ストリーミング動作確認スクリプト

Researcher Agent の message/stream エンドポイントに接続し、
SSE チャンクがリアルタイムで返ってくることをターミナル上で確認します。

事前準備 (3つのターミナルで実行):
  ターミナル1: make run-emulator         # Firestore Emulator
  ターミナル2: make run-researcher-emu   # Researcher Agent (:8003)
  ターミナル3: cd services/agents && .venv/bin/python -m scripts.demo_researcher_stream

オプション:
  --live   タイプライター表示（チャンクをリアルタイムに文字出力）
  --raw    生JSONを整形して表示（バックエンドの出力をそのまま確認）
  --debug  httpxの生チャンクを表示

Firestore Emulator UI: http://localhost:4000/firestore/default/data
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

RESEARCHER_URL = "http://localhost:8003"
TEST_USER_ID = "stream_test_user"
TEST_COLLECTION_ID = f"col_stream_{uuid.uuid4().hex[:8]}"
TEST_ARTICLE_URL = "https://example.com/test-streaming-article"


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
            resp = await client.get(f"http://{host}/")
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

    # AgentCard で streaming=True か確認
    if ok:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{RESEARCHER_URL}/.well-known/agent.json")
            card = resp.json()
            streaming = card.get("capabilities", {}).get("streaming", False)
            if streaming:
                sub(f"[OK] AgentCard streaming=True")
            else:
                sub(f"[WARN] AgentCard streaming={streaming}")

    return ok


async def seed_test_data(db: firestore.AsyncClient):
    """テスト用ユーザーとコレクションをシード"""
    header("テストデータ作成")

    # ユーザー作成
    await db.collection("users").document(TEST_USER_ID).set({
        "user_id": TEST_USER_ID,
        "sources": [],
    })
    sub(f"ユーザー: {TEST_USER_ID}")

    # コレクション作成（記事1件）
    await db.collection("collections").document(TEST_COLLECTION_ID).set({
        "id": TEST_COLLECTION_ID,
        "user_id": TEST_USER_ID,
        "date": "2025-01-01",
        "status": "completed",
        "created_at": firestore.SERVER_TIMESTAMP,
        "articles": [
            {
                "title": "SSEストリーミングテスト記事",
                "url": TEST_ARTICLE_URL,
                "source": "test",
                "source_type": "rss",
                "content": (
                    "これはSSEストリーミングの動作確認用テスト記事です。"
                    "Gemini Pro がこの内容をもとに深掘りレポートを生成します。"
                    "リアルタイムにチャンクが返ってくることを確認してください。"
                ),
                "scoring_status": "scored",
                "relevance_score": 0.9,
                "is_pickup": True,
            }
        ],
    })
    sub(f"コレクション: {TEST_COLLECTION_ID}")
    sub(f"記事: {TEST_ARTICLE_URL}")


def parse_sse_events(buffer: str) -> tuple[list[str], str]:
    """SSE バッファからイベントを抽出する。

    sse-starlette はセパレータに \\r\\n を使うため、
    \\r\\n\\r\\n（CRLF×2）でイベントが区切られる。
    \\n\\n を含まないので、先に \\r を除去して正規化する。

    Returns:
        (イベント文字列のリスト, 残りバッファ)
    """
    normalized = buffer.replace("\r\n", "\n").replace("\r", "\n")
    events = []
    while "\n\n" in normalized:
        event_str, normalized = normalized.split("\n\n", 1)
        stripped = event_str.strip()
        if stripped:
            events.append(stripped)
    return events, normalized


def extract_sse_data(event_str: str) -> str | None:
    """SSE イベント文字列から data フィールドを抽出する。

    複数の data: 行がある場合は結合する（SSE 仕様準拠）。
    コメント行（: で始まる）はスキップする。
    """
    data_parts = []
    for line in event_str.split("\n"):
        if line.startswith("data:"):
            data_parts.append(line[len("data:"):].strip())
        # コメント行 (: ping など) はスキップ
    return "\n".join(data_parts) if data_parts else None


def display_event(data: dict, event_num: int, elapsed: float, artifact_text: list[str]) -> float | None:
    """SSE イベントを表示する。最初のアーティファクトチャンク時刻を返す。"""
    result = data.get("result", {})
    kind = result.get("kind", "?")
    first_chunk_time = None

    if kind == "status-update":
        state = result.get("status", {}).get("state", "?")
        final = result.get("final", False)
        label = "[FINAL] " if final else ""
        print(f"  [{event_num:>3}] ({elapsed:>5.1f}s) STATUS  {label}{state}")

    elif kind == "artifact-update":
        first_chunk_time = elapsed
        parts = result.get("artifact", {}).get("parts", [])
        append = result.get("append", None)
        for part in parts:
            text = part.get("text", "")
            artifact_text.append(text)
            preview = text.replace("\n", "\\n")
            if len(preview) > 60:
                preview = preview[:60] + "..."
            mode = "APPEND" if append else "NEW   "
            print(f"  [{event_num:>3}] ({elapsed:>5.1f}s) {mode}  {preview}")

    elif "error" in data:
        error = data["error"]
        print(f"  [{event_num:>3}] ({elapsed:>5.1f}s) ERROR   code={error.get('code')} {error.get('message', '')[:60]}")

    else:
        print(f"  [{event_num:>3}] ({elapsed:>5.1f}s) {kind}")

    return first_chunk_time


def process_sse_data(data: dict, ctx: dict):
    """SSE イベント JSON を処理し、モードに応じて表示する。

    ctx keys: mode, event_count, start, artifact_text, first_chunk_time
    """
    result = data.get("result", {})
    kind = result.get("kind", "?")
    elapsed = time.time() - ctx["start"]
    ctx["event_count"] += 1
    n = ctx["event_count"]

    if kind == "artifact-update":
        if ctx["first_chunk_time"] is None:
            ctx["first_chunk_time"] = elapsed
        parts = result.get("artifact", {}).get("parts", [])
        append = result.get("append", None)
        for part in parts:
            text = part.get("text", "")
            ctx["artifact_text"].append(text)

            if ctx["mode"] == "live":
                # タイプライター表示: テキストをそのまま出力
                print(text, end="", flush=True)
            else:
                preview = text.replace("\n", "\\n")
                if len(preview) > 60:
                    preview = preview[:60] + "..."
                mode_label = "APPEND" if append else "NEW   "
                print(f"  [{n:>3}] ({elapsed:>5.1f}s) {mode_label}  {preview}")

    elif kind == "status-update":
        state = result.get("status", {}).get("state", "?")
        final = result.get("final", False)
        if ctx["mode"] == "live":
            if state == "working":
                print("\033[2m⏳ 生成中...\033[0m\n", flush=True)
            elif final:
                print(f"\n\n\033[2m✓ 完了 ({elapsed:.1f}s)\033[0m", flush=True)
        else:
            label = "[FINAL] " if final else ""
            print(f"  [{n:>3}] ({elapsed:>5.1f}s) STATUS  {label}{state}")

    elif "error" in data:
        error = data["error"]
        if ctx["mode"] == "live":
            print(f"\n\033[31m✗ エラー: {error.get('message', '不明')}\033[0m")
        else:
            print(f"  [{n:>3}] ({elapsed:>5.1f}s) ERROR   code={error.get('code')} {error.get('message', '')[:60]}")

    else:
        if ctx["mode"] != "live":
            print(f"  [{n:>3}] ({elapsed:>5.1f}s) {kind}")


async def send_streaming_request():
    """message/stream リクエストを送信し SSE イベントを表示"""
    header("SSE ストリーミング実行")
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

    debug = "--debug" in sys.argv
    live = "--live" in sys.argv
    raw = "--raw" in sys.argv
    ctx = {
        "mode": "live" if live else "log",
        "event_count": 0,
        "start": time.time(),
        "artifact_text": [],
        "first_chunk_time": None,
    }

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

            content_type = response.headers.get("content-type", "不明")
            if not live:
                sub(f"HTTP {response.status_code} (Content-Type: {content_type})")
                print(f"  {'─'*56}")

            buffer = ""
            async for raw_chunk in response.aiter_text():
                if debug:
                    elapsed = time.time() - ctx["start"]
                    preview = repr(raw_chunk[:200])
                    print(f"  [DEBUG] ({elapsed:>5.1f}s) chunk len={len(raw_chunk)}: {preview}")

                buffer += raw_chunk

                events, buffer = parse_sse_events(buffer)
                for event_str in events:
                    data_str = extract_sse_data(event_str)
                    if not data_str:
                        continue

                    if raw:
                        # 生JSON を整形して出力
                        try:
                            data = json.loads(data_str)
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                            print()
                        except json.JSONDecodeError:
                            print(data_str)
                            print()
                        ctx["event_count"] += 1
                        continue

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    process_sse_data(data, ctx)

            # ストリーム終了後、バッファに残ったイベントを処理
            remaining = buffer.replace("\r\n", "\n").replace("\r", "\n").strip()
            if remaining:
                data_str = extract_sse_data(remaining)
                if data_str:
                    if raw:
                        try:
                            data = json.loads(data_str)
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                        except json.JSONDecodeError:
                            print(data_str)
                        ctx["event_count"] += 1
                    else:
                        try:
                            data = json.loads(data_str)
                            process_sse_data(data, ctx)
                        except json.JSONDecodeError:
                            pass

    total = time.time() - ctx["start"]
    full_report = "".join(ctx["artifact_text"])

    if not live and not raw:
        print(f"  {'─'*56}")
    print()
    header("結果サマリー")
    sub(f"合計イベント数: {ctx['event_count']}")
    if not raw:
        sub(f"アーティファクトチャンク数: {len(ctx['artifact_text'])}")
        sub(f"最初のチャンク到着: {ctx['first_chunk_time']:.1f}s" if ctx["first_chunk_time"] else "最初のチャンクなし")
    sub(f"合計所要時間: {total:.1f}s")
    if not raw:
        sub(f"レポート文字数: {len(full_report)}")


async def verify_firestore(db: firestore.AsyncClient):
    """Firestore に保存されたレポートを確認"""
    header("Firestore 保存確認")

    doc = await db.collection("collections").document(TEST_COLLECTION_ID).get()
    if not doc.exists:
        sub("[WARN] コレクションが見つかりません")
        return

    data = doc.to_dict()
    articles = data.get("articles", [])
    target = None
    for a in articles:
        if a.get("url") == TEST_ARTICLE_URL:
            target = a
            break

    if target is None:
        sub("[WARN] 対象記事が見つかりません")
        return

    status = target.get("research_status", "未設定")
    report = target.get("deep_dive_report", "")
    sub(f"research_status: {status}")
    sub(f"レポート保存: {'あり' if report else 'なし'} ({len(report)}文字)")

    if status == "completed" and report:
        sub("[OK] ストリーミング完了後に Firestore に全文保存されています")
    elif status == "failed":
        sub("[NG] レポート生成が失敗しました")
    else:
        sub(f"[?] 想定外の状態です")


async def cleanup(db: firestore.AsyncClient):
    """テストデータ削除"""
    header("クリーンアップ")
    await db.collection("users").document(TEST_USER_ID).delete()
    sub(f"ユーザー '{TEST_USER_ID}' を削除")
    await db.collection("collections").document(TEST_COLLECTION_ID).delete()
    sub(f"コレクション '{TEST_COLLECTION_ID}' を削除")


async def main():
    print("\n" + "=" * 60)
    print("  Researcher Agent SSE ストリーミング動作確認")
    print("=" * 60)

    if not await check_prerequisites():
        sys.exit(1)

    db = firestore.AsyncClient(project="curation-persona")

    try:
        await seed_test_data(db)
        await send_streaming_request()
        await verify_firestore(db)
    finally:
        sub("")
        resp = input("  テストデータを削除しますか? (Y/n): ")
        if resp.lower() != "n":
            await cleanup(db)

    header("完了")


if __name__ == "__main__":
    asyncio.run(main())

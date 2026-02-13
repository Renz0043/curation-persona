"""Curation Persona MCP Server

キュレーションパイプラインが生成した Firestore データを
Claude Desktop / Claude Code から参照するための読み取り専用 MCP サーバー。
"""

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from shared.firestore_client import FirestoreClient
from shared.gemini_client import GeminiClient
from shared.models import ArticleCollection, ScoredArticle

# stdio トランスポートでは stdout を JSON-RPC が占有するため stderr にログ出力
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("curation-persona")
firestore = FirestoreClient()
gemini = GeminiClient()


def _get_user_id() -> str:
    user_id = os.environ.get("CURATION_USER_ID", "")
    if not user_id:
        raise ValueError("環境変数 CURATION_USER_ID が設定されていません。")
    return user_id


def _format_article(article: ScoredArticle, index: int) -> str:
    """単一記事をマークダウンに整形する。"""
    lines = [f"{index}. **{article.title}** (スコア: {article.relevance_score:.2f})"]
    lines.append(f"   URL: {article.url}")
    lines.append(f"   ソース: {article.source}")
    if article.relevance_reason:
        lines.append(f"   理由: {article.relevance_reason}")
    has_report = "あり" if article.deep_dive_report else "なし"
    lines.append(f"   深掘りレポート: {has_report}")
    if article.user_rating is not None:
        lines.append(f"   ユーザー評価: {'★' * article.user_rating}")
    return "\n".join(lines)


def _format_briefing(collection: ArticleCollection) -> str:
    """コレクションをマークダウンに整形する。"""
    pickup = [a for a in collection.articles if a.is_pickup]
    others = [a for a in collection.articles if not a.is_pickup]

    lines = [
        f"## {collection.date} のキュレーション記事（{len(collection.articles)}件）",
        f"ステータス: {collection.status.value}",
        f"コレクションID: `{collection.id}`",
        "",
    ]

    if pickup:
        lines.append("### ピックアップ記事")
        for i, article in enumerate(pickup, 1):
            lines.append(_format_article(article, i))
            lines.append("")

    if others:
        lines.append("### その他の記事")
        for i, article in enumerate(others, 1):
            lines.append(_format_article(article, i))
            lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_todays_briefing() -> str:
    """今日のキュレーション記事一覧を取得します。ピックアップ記事とその他の記事に分けて表示します。"""
    user_id = _get_user_id()
    collection = await firestore.get_latest_collection(user_id)
    if not collection:
        return "今日のコレクションはまだありません。"
    return _format_briefing(collection)


@mcp.tool()
async def get_collection_by_date(date: str) -> str:
    """指定日のキュレーション記事一覧を取得します。

    Args:
        date: 取得したい日付（YYYY-MM-DD形式）
    """
    user_id = _get_user_id()
    collection = await firestore.get_latest_collection(user_id, date=date)
    if not collection:
        return f"{date} のコレクションは見つかりませんでした。"
    return _format_briefing(collection)


@mcp.tool()
async def get_article_detail(collection_id: str, article_url: str) -> str:
    """記事の詳細情報と深掘りレポートを取得します。

    Args:
        collection_id: コレクションID（get_todays_briefing等の結果に含まれます）
        article_url: 記事のURL
    """
    collection = await firestore.get_collection(collection_id)
    target = None
    for article in collection.articles:
        if article.url == article_url:
            target = article
            break

    if not target:
        return f"記事が見つかりませんでした: {article_url}"

    lines = [
        f"# {target.title}",
        "",
        f"- **URL**: {target.url}",
        f"- **ソース**: {target.source}",
        f"- **スコア**: {target.relevance_score:.2f}",
        f"- **ピックアップ**: {'はい' if target.is_pickup else 'いいえ'}",
    ]
    if target.relevance_reason:
        lines.append(f"- **選定理由**: {target.relevance_reason}")
    if target.user_rating is not None:
        lines.append(f"- **ユーザー評価**: {'★' * target.user_rating}")
    if target.user_comment:
        lines.append(f"- **コメント**: {target.user_comment}")

    if target.content:
        lines.extend(["", "## 記事サマリー", "", target.content[:1000]])

    if target.deep_dive_report:
        lines.extend(["", "## 深掘りレポート", "", target.deep_dive_report])
    else:
        lines.extend(["", "*深掘りレポートはまだ作成されていません。*"])

    return "\n".join(lines)


@mcp.tool()
async def get_interest_profile() -> str:
    """ユーザーの興味プロファイル（LLMが学習した興味関心の要約）を取得します。"""
    user_id = _get_user_id()
    user_data = await firestore.get_user(user_id)
    if not user_data:
        return "ユーザー情報が見つかりませんでした。"

    profile = user_data.get("interestProfile")
    updated_at = user_data.get("interestProfileUpdatedAt")

    lines = [f"## {user_id} の興味プロファイル", ""]
    if profile:
        lines.append(profile)
        if updated_at:
            lines.extend(["", f"*最終更新: {updated_at}*"])
    else:
        lines.append("興味プロファイルはまだ生成されていません。記事を評価すると自動生成されます。")

    sources = user_data.get("sources", [])
    if sources:
        lines.extend(["", "## 登録ソース"])
        for src in sources:
            enabled = "有効" if src.get("enabled", True) else "無効"
            lines.append(f"- {src.get('name', src.get('id', '不明'))} ({src.get('type', '不明')}) [{enabled}]")

    return "\n".join(lines)


@mcp.tool()
async def get_high_rated_articles(min_rating: int = 4) -> str:
    """過去の高評価記事一覧を取得します。ユーザーの好みの傾向を把握するのに使えます。

    Args:
        min_rating: 最低評価（1-5、デフォルト: 4）
    """
    user_id = _get_user_id()
    articles = await firestore.get_high_rated_articles(user_id, min_rating=min_rating)
    if not articles:
        return f"評価 {min_rating} 以上の記事はまだありません。"

    lines = [f"## 高評価記事（評価 {min_rating} 以上、{len(articles)}件）", ""]
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. **{article['title']}** ({'★' * article['user_rating']})")
        lines.append(f"   URL: {article['url']}")
        if article.get("user_comment"):
            lines.append(f"   コメント: {article['user_comment']}")
        if article.get("content"):
            lines.append(f"   概要: {article['content']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def search_similar_articles(query: str, limit: int = 10) -> str:
    """クエリテキストに類似した過去の記事をベクトル検索で取得します。

    Args:
        query: 検索クエリ（自然言語テキスト）
        limit: 最大取得件数（デフォルト: 10）
    """
    user_id = _get_user_id()
    embeddings = await gemini.embed_content([query])
    query_embedding = embeddings[0]

    articles = await firestore.find_similar_articles(
        user_id, query_embedding, limit=limit
    )
    if not articles:
        return "類似記事が見つかりませんでした。"

    lines = [f"## 類似記事検索結果（{len(articles)}件）", f"クエリ: {query}", ""]
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. **{article['title']}**")
        lines.append(f"   URL: {article['url']}")
        if article.get("source"):
            lines.append(f"   ソース: {article['source']}")
        if article.get("relevance_score"):
            lines.append(f"   関連スコア: {article['relevance_score']:.2f}")
        if article.get("vector_distance") is not None:
            lines.append(f"   ベクトル距離: {article['vector_distance']:.4f}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")

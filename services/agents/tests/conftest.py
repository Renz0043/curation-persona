import pytest


@pytest.fixture
def mock_firestore_client():
    """FirestoreClient のモックフィクスチャ"""
    from unittest.mock import AsyncMock

    from shared.firestore_client import FirestoreClient

    client = FirestoreClient.__new__(FirestoreClient)
    client.db = None
    client.get_user = AsyncMock(return_value={"user_id": "test_user", "sources": []})
    client.create_collection = AsyncMock()
    client.get_collection = AsyncMock()
    client.update_collection_articles = AsyncMock()
    client.update_collection_status = AsyncMock()
    client.get_high_rated_articles = AsyncMock(return_value=[])
    client.update_interest_profile = AsyncMock()
    client.has_new_ratings_since = AsyncMock(return_value=False)
    client.update_article_feedback = AsyncMock()
    client.update_article_research_status = AsyncMock()
    client.update_article_research = AsyncMock()
    client.get_latest_collection = AsyncMock(return_value=None)
    client.update_article_embeddings = AsyncMock()
    client.find_similar_articles = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_gemini_client():
    """GeminiClient のモックフィクスチャ"""
    from unittest.mock import AsyncMock

    from shared.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    client.model = "flash"
    client.model_name = "gemini-2.5-flash"
    client.generate_text = AsyncMock(return_value="スタブレスポンス")
    client.generate_json = AsyncMock(return_value={"score": 0.5, "reason": "テスト"})
    client.embed_content = AsyncMock(return_value=[[0.1] * 768])

    async def _stub_stream(prompt):
        for chunk in ["チャンク1", "チャンク2", "チャンク3"]:
            yield chunk

    client.generate_text_stream = _stub_stream
    return client


@pytest.fixture
def mock_a2a_client():
    """A2AClient のモックフィクスチャ"""
    from unittest.mock import AsyncMock

    from shared.a2a_client import A2AClient

    client = A2AClient.__new__(A2AClient)
    client.send_message = AsyncMock(return_value={"status": "ok"})
    return client


@pytest.fixture
def mock_scraper():
    """WebScraper のモックフィクスチャ"""
    from unittest.mock import AsyncMock

    from shared.scraper import WebScraper

    scraper = WebScraper.__new__(WebScraper)
    scraper.scrape_articles = AsyncMock()
    scraper.scrape = AsyncMock(return_value=None)
    return scraper


@pytest.fixture
def mock_fetcher_registry():
    """FetcherRegistry のモックフィクスチャ"""
    from unittest.mock import AsyncMock, MagicMock

    from shared.fetchers.registry import FetcherRegistry

    registry = FetcherRegistry.__new__(FetcherRegistry)
    registry._fetchers = []

    mock_fetcher = MagicMock()
    mock_fetcher.fetch = AsyncMock(return_value=[])
    mock_fetcher.supports = MagicMock(return_value=True)
    registry.get_fetcher = MagicMock(return_value=mock_fetcher)

    return registry

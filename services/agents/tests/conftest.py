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
    return client


@pytest.fixture
def mock_gemini_client():
    """GeminiClient のモックフィクスチャ"""
    from unittest.mock import AsyncMock

    from shared.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    client.model = "flash"
    client.generate_text = AsyncMock(return_value="スタブレスポンス")
    client.generate_json = AsyncMock(return_value={"score": 0.5, "reason": "テスト"})
    return client

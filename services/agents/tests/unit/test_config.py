from shared.config import Settings


class Test_Settings:
    def test_デフォルト値が正しい(self):
        s = Settings(
            google_cloud_project="test-project",
            librarian_agent_url="http://localhost:8002",
            researcher_agent_url="http://localhost:8003",
        )
        assert s.google_cloud_project == "test-project"
        assert s.firestore_database == "(default)"
        assert s.gemini_flash_model == "gemini-2.5-flash"
        assert s.gemini_pro_model == "gemini-2.5-pro"
        assert s.pickup_count == 2
        assert s.min_ratings_for_scoring == 3
        assert s.high_rating_threshold == 4

    def test_カスタム値を反映できる(self):
        s = Settings(
            google_cloud_project="custom-project",
            firestore_database="custom-db",
            librarian_agent_url="http://librarian:8002",
            researcher_agent_url="http://researcher:8003",
            pickup_count=5,
        )
        assert s.firestore_database == "custom-db"
        assert s.pickup_count == 5

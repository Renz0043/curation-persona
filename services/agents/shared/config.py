from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GCP
    google_cloud_project: str = "curation-persona"
    firestore_database: str = "(default)"

    # A2A エージェント間通信
    librarian_agent_url: str = "http://localhost:8002"
    researcher_agent_url: str = "http://localhost:8003"

    # Gemini
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"

    # ピックアップ設定
    pickup_count: int = 2

    # スコアリング設定
    min_ratings_for_scoring: int = 3
    high_rating_threshold: int = 4

    model_config = {"env_file": ".env"}


settings = Settings()

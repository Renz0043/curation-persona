# shared/ — 全エージェント共通モジュール

## モジュール一覧
- `config.py` — pydantic-settings による環境変数管理（`settings` シングルトン）
- `models.py` — Pydanticモデル（Article, ScoredArticle, ArticleCollection 等）
- `firestore_client.py` — Firestore CRUD。Emulator未接続時はstubモードで動作
- `gemini_client.py` — Gemini Flash/Pro クライアント（generate_text, generate_json）
- `a2a_client.py` — A2Aプロトコルでのエージェント間メッセージ送信
- `scraper.py` — WebScraper（robots.txt準拠・逐次取得の記事本文スクレイピング）
- `retry.py` — 指数バックオフリトライデコレータ
- `fetchers/` — BaseFetcher + FetcherRegistry パターンの記事取得モジュール群

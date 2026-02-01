# バックエンド実装設計書

> **対象**: Curation Persona - Agent Layer (Cloud Run)
>
> **スコープ**: ハッカソンMVP

---

## 1. 概要

バックエンドは3つのAIエージェントで構成される。各エージェントはCloud Run上で独立したサービスとして動作し、Pub/Subを介して非同期に連携する。

### 1.1 エージェント一覧

| エージェント | 役割 | LLMモデル |
|-------------|------|-----------|
| Collector Agent | RSS巡回、記事収集、フロー制御 | - |
| Librarian Agent | 全記事への関連性スコア付与、ピックアップ選定 | Gemini 2.5 Flash (embedding) |
| Researcher Agent | ピックアップ記事の詳細レポート生成 | Gemini 2.5 Pro |

### 1.2 設計方針

- **ソース厳選**: RSSソースをユーザーが厳選することで、取得記事の品質を担保
- **全件表示**: 取得した記事は全て「本日のニュース」として表示
- **ピックアップ深掘り**: 関連性スコア上位N件のみResearcherで詳細レポート生成
- **コスト最適化**: 高コストなGemini Proはピックアップ記事のみに使用

### 1.3 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.11+ |
| Webフレームワーク | FastAPI |
| LLM SDK | google-genai (Vertex AI) |
| ベクトル検索 | Vertex AI Vector Search |
| メッセージング | Cloud Pub/Sub |
| データベース | Cloud Firestore |
| 外部連携 | Notion API (notion-sdk-py) |

---

## 2. 処理フロー

### 2.1 全体フロー図

```
Cloud Scheduler (毎朝6時)
    │
    ▼ Pub/Sub: batch-trigger
┌─────────────────────────────────────┐
│ Collector Agent                     │
│  - RSS取得（ソースは厳選済み）       │
│  - 全記事をFirestoreに保存           │
│    (scoring_status: PENDING)        │
└─────────────────────────────────────┘
    │
    │ Firestore: 記事保存
    ▼ Pub/Sub: score-request
┌─────────────────────────────────────┐
│ Librarian Agent                     │
│  - Firestoreから記事を読み取り       │
│  - 全記事に関連性スコア付与          │
│  - Firestoreにスコア書き戻し         │
│    (scoring_status: SCORED)         │
│  - 上位N件をピックアップとしてマーク  │
│    (is_pickup: true)                │
└─────────────────────────────────────┘
    │
    │ Firestore: スコア更新
    ▼ Pub/Sub: research-request ※ピックアップのみ
┌─────────────────────────────────────┐
│ Researcher Agent                    │
│  - Firestoreからピックアップ記事読取 │
│  - 詳細レポート生成                  │
│  - Firestoreに保存                   │
│    (research_status: COMPLETED)     │
└─────────────────────────────────────┘
```

### 2.2 Dashboard での表示イメージ

```
┌─────────────────────────────────────┐
│ 📰 本日のニュース (15件)            │
├─────────────────────────────────────┤
│ ⭐ ピックアップ (詳細レポート付き)   │
│   • AI Agent の新設計パターン        │  ← 詳細レポートあり
│   • Gemini 2.5 の新機能発表          │  ← 関連メモとの紐付け
├─────────────────────────────────────┤
│ 📋 その他のニュース                  │
│   • React 19 リリース               │  ← 表示のみ
│   • GitHub Copilot アップデート     │
│   • ...                              │
└─────────────────────────────────────┘
```

---

## 3. プロジェクト構成

```
services/agents/
├── shared/                     # 共通モジュール
│   ├── __init__.py
│   ├── config.py              # 環境変数・設定
│   ├── firestore_client.py    # Firestore操作
│   ├── pubsub_client.py       # Pub/Sub操作
│   ├── gemini_client.py       # Gemini API操作
│   ├── notion_client.py       # Notion API操作
│   ├── vector_search.py       # Vector Search操作
│   ├── models.py              # Pydanticモデル定義
│   ├── retry.py               # リトライユーティリティ
│   └── fetchers/              # 記事取得モジュール（拡張可能）
│       ├── __init__.py
│       ├── base.py            # BaseFetcher（共通インターフェース）
│       ├── registry.py        # FetcherRegistry（ファクトリ）
│       ├── rss_fetcher.py     # RSS取得
│       ├── website_fetcher.py # Webサイト監視
│       └── newsletter_fetcher.py  # メルマガ取得
│
├── collector/                  # Collector Agent
│   ├── main.py                # FastAPIエントリポイント
│   ├── service.py             # ビジネスロジック
│   ├── Dockerfile
│   └── requirements.txt
│
├── librarian/                  # Librarian Agent
│   ├── main.py                # FastAPIエントリポイント
│   ├── service.py             # ビジネスロジック
│   ├── scorer.py              # 関連性スコアリング
│   ├── Dockerfile
│   └── requirements.txt
│
├── researcher/                 # Researcher Agent
│   ├── main.py                # FastAPIエントリポイント
│   ├── service.py             # ビジネスロジック
│   ├── report_generator.py    # レポート生成
│   ├── Dockerfile
│   └── requirements.txt
│
└── pyproject.toml              # 共通依存関係
```

---

## 4. 共通モジュール (shared/)

### 4.1 config.py - 環境変数管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GCP
    google_cloud_project: str
    firestore_database: str = "(default)"

    # Pub/Sub Topics
    pubsub_topic_batch: str = "batch-trigger"
    pubsub_topic_score: str = "score-request"
    pubsub_topic_research: str = "research-request"

    # Gemini
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"

    # Vector Search
    vector_search_index_endpoint: str
    vector_search_deployed_index_id: str

    # Notion
    notion_token: str

    # ピックアップ設定
    pickup_count: int = 2  # 詳細レポートを生成する記事数

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4.2 models.py - 共通データモデル

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class CollectionStatus(str, Enum):
    """記事コレクションのステータス"""
    COLLECTING = "collecting"    # 収集中
    SCORING = "scoring"          # スコアリング中
    RESEARCHING = "researching"  # 詳細調査中（ピックアップ記事）
    COMPLETED = "completed"      # 完了
    FAILED = "failed"            # 失敗

class ScoringStatus(str, Enum):
    """スコアリングのステータス（全記事共通）"""
    PENDING = "pending"      # 収集済み、未スコアリング
    SCORING = "scoring"      # スコアリング中
    SCORED = "scored"        # スコアリング完了

class ResearchStatus(str, Enum):
    """詳細調査のステータス（ピックアップ記事のみ）"""
    PENDING = "pending"          # 詳細調査待ち
    RESEARCHING = "researching"  # 詳細調査中
    COMPLETED = "completed"      # 詳細調査完了

# ソース設定
class SourceType(str, Enum):
    """記事ソースの種別"""
    RSS = "rss"                  # RSSフィード
    WEBSITE = "website"          # Webサイト監視
    NEWSLETTER = "newsletter"    # メルマガ
    API = "api"                  # 外部API

class SourceConfig(BaseModel):
    """記事ソースの設定"""
    id: str                      # ソースID（例: "src_001"）
    type: SourceType             # ソース種別
    name: str                    # 表示名（例: "Hacker News"）
    enabled: bool = True         # 有効/無効
    config: dict = {}            # チャンネル固有の設定

    # config の例:
    # RSS:        { "url": "https://example.com/feed" }
    # WEBSITE:    { "url": "https://blog.example.com", "selector": ".post-list", "link_selector": "a" }
    # NEWSLETTER: { "email_filter": "from:news@example.com" }
    # API:        { "endpoint": "https://api.example.com/articles", "api_key_env": "EXAMPLE_API_KEY" }

class Article(BaseModel):
    """各ソースから取得した記事"""
    title: str
    url: str
    source: str                  # ソース名（SourceConfig.name）
    source_type: SourceType      # ソース種別
    content: Optional[str] = None
    published_at: Optional[datetime] = None

class ScoredArticle(Article):
    """関連性スコア付きの記事"""
    # スコアリング関連（全記事共通）
    scoring_status: ScoringStatus = ScoringStatus.PENDING
    relevance_score: float = 0.0  # 0.0 - 1.0
    relevance_reason: str = ""
    related_notion_pages: list[str] = []

    # ピックアップ関連（ピックアップ記事のみ使用）
    is_pickup: bool = False
    research_status: Optional[ResearchStatus] = None  # ピックアップ時のみ設定
    deep_dive_report: Optional[str] = None

    # フィードバック
    user_feedback: Optional[FeedbackType] = None

class ArticleCollection(BaseModel):
    """日次の記事コレクション（収集した記事の集合）"""
    id: str
    user_id: str
    date: str  # "2025-01-15"
    articles: list[ScoredArticle] = []  # 全記事（ピックアップ含む）
    status: CollectionStatus
    created_at: datetime

# Pub/Sub メッセージ
class BatchTriggerMessage(BaseModel):
    """batch-trigger: Scheduler → Collector"""
    type: str = "daily_batch"
    user_id: str
    triggered_at: datetime

class ScoreRequestMessage(BaseModel):
    """score-request: Collector → Librarian"""
    user_id: str
    collection_id: str

class ResearchRequestMessage(BaseModel):
    """research-request: Librarian → Researcher"""
    user_id: str
    collection_id: str
    article_url: str  # 記事を特定するためのURL
```

### 4.3 retry.py - リトライユーティリティ

```python
import asyncio
from functools import wraps
from typing import TypeVar, Callable
import logging
import httpx
from google.api_core.exceptions import GoogleAPIError, ServiceUnavailable, ResourceExhausted

logger = logging.getLogger(__name__)

RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay_sec": 1,
    "max_delay_sec": 30,
    "exponential_base": 2
}

# リトライ対象のHTTPステータスコード
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# リトライ対象の例外
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,      # タイムアウト
    httpx.NetworkError,          # ネットワークエラー
    ServiceUnavailable,          # GCP 503
    ResourceExhausted,           # GCP 429 (レート制限)
)

T = TypeVar("T")

def is_retryable(exception: Exception) -> bool:
    """リトライ可能なエラーかどうかを判定"""
    # 明示的にリトライ対象の例外
    if isinstance(exception, RETRYABLE_EXCEPTIONS):
        return True

    # HTTPステータスコードでの判定
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_STATUS_CODES

    # Google API エラーのステータスコード判定
    if isinstance(exception, GoogleAPIError):
        if hasattr(exception, 'code') and exception.code in RETRYABLE_STATUS_CODES:
            return True

    return False

def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        delay = RETRY_CONFIG["initial_delay_sec"]
        max_retries = RETRY_CONFIG["max_retries"]
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                # リトライ不可能なエラーは即座に再送出
                if not is_retryable(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise

                # 何回目/最大回数 の形式でログ出力
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} failed: {e}"
                )

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(
                        delay * RETRY_CONFIG["exponential_base"],
                        RETRY_CONFIG["max_delay_sec"]
                    )

        logger.error(f"All {max_retries} retries exhausted")
        raise last_exception

    return wrapper
```

### 4.4 fetchers/ - 記事取得モジュール

記事ソースの種類（RSS、Webサイト、メルマガ等）に応じた取得ロジックを拡張可能な形で実装する。

#### 4.4.1 base.py - 共通インターフェース

```python
from abc import ABC, abstractmethod
from shared.models import Article, SourceConfig

class BaseFetcher(ABC):
    """記事取得の共通インターフェース"""

    @abstractmethod
    async def fetch(self, config: SourceConfig) -> list[Article]:
        """
        設定に基づいて記事を取得

        Args:
            config: ソース設定（URL、セレクタ等）

        Returns:
            取得した記事のリスト
        """
        pass

    @abstractmethod
    def supports(self, source_type: str) -> bool:
        """
        このFetcherが対応するソースタイプか判定

        Args:
            source_type: ソース種別（"rss", "website" 等）

        Returns:
            対応している場合 True
        """
        pass
```

#### 4.4.2 registry.py - Fetcherレジストリ

```python
import logging
from typing import Optional
from .base import BaseFetcher

logger = logging.getLogger(__name__)

class FetcherRegistry:
    """Fetcherの登録・取得を管理するレジストリ"""

    def __init__(self):
        self._fetchers: list[BaseFetcher] = []

    def register(self, fetcher: BaseFetcher):
        """Fetcherを登録"""
        self._fetchers.append(fetcher)
        logger.info(f"Registered fetcher: {fetcher.__class__.__name__}")

    def get_fetcher(self, source_type: str) -> Optional[BaseFetcher]:
        """ソースタイプに対応するFetcherを取得"""
        for fetcher in self._fetchers:
            if fetcher.supports(source_type):
                return fetcher
        return None

    def get_fetcher_or_raise(self, source_type: str) -> BaseFetcher:
        """ソースタイプに対応するFetcherを取得（なければ例外）"""
        fetcher = self.get_fetcher(source_type)
        if fetcher is None:
            raise ValueError(f"No fetcher registered for source type: {source_type}")
        return fetcher
```

#### 4.4.3 rss_fetcher.py - RSS取得

```python
import feedparser
import asyncio
from datetime import datetime, timedelta
import logging

from shared.models import Article, SourceConfig, SourceType
from .base import BaseFetcher

logger = logging.getLogger(__name__)

class RSSFetcher(BaseFetcher):
    """RSSフィードから記事を取得"""

    def __init__(self, max_age_days: int = 1):
        self.max_age_days = max_age_days

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.RSS.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        url = config.config.get("url")
        if not url:
            logger.warning(f"No URL in config for source: {config.name}")
            return []

        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        articles = []

        for entry in feed.entries:
            published = self._parse_date(entry.get("published"))

            if published and published < cutoff_date:
                continue

            article = Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=config.name,
                source_type=SourceType.RSS,
                content=entry.get("summary", ""),
                published_at=published
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from RSS: {config.name}")
        return articles

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            from dateutil.parser import parse
            return parse(date_str)
        except Exception:
            return None
```

#### 4.4.4 website_fetcher.py - Webサイト監視（MVP後に実装）

```python
import httpx
from bs4 import BeautifulSoup
import logging

from shared.models import Article, SourceConfig, SourceType
from .base import BaseFetcher

logger = logging.getLogger(__name__)

class WebsiteFetcher(BaseFetcher):
    """Webサイトを監視して新規記事を取得"""

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.WEBSITE.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        url = config.config.get("url")
        selector = config.config.get("selector", "article")
        link_selector = config.config.get("link_selector", "a")

        if not url:
            logger.warning(f"No URL in config for source: {config.name}")
            return []

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []

        for element in soup.select(selector):
            link = element.select_one(link_selector)
            if not link:
                continue

            article = Article(
                title=link.get_text(strip=True),
                url=link.get("href", ""),
                source=config.name,
                source_type=SourceType.WEBSITE,
                content=element.get_text(strip=True)[:500],
                published_at=None  # 別途パースが必要
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from website: {config.name}")
        return articles
```

#### 4.4.5 newsletter_fetcher.py - メルマガ取得（MVP後に実装）

```python
import logging

from shared.models import Article, SourceConfig, SourceType
from .base import BaseFetcher

logger = logging.getLogger(__name__)

class NewsletterFetcher(BaseFetcher):
    """メルマガから記事を取得（Gmail API等を使用）"""

    def supports(self, source_type: str) -> bool:
        return source_type == SourceType.NEWSLETTER.value

    async def fetch(self, config: SourceConfig) -> list[Article]:
        # TODO: Gmail API または Cloud Pub/Sub (Gmail Push) を使用して実装
        # 1. email_filter に基づいてメールを検索
        # 2. メール本文からリンクを抽出
        # 3. Article に変換

        logger.warning("NewsletterFetcher is not yet implemented")
        return []
```

#### 4.4.6 __init__.py - レジストリ初期化

```python
from .registry import FetcherRegistry
from .rss_fetcher import RSSFetcher
from .website_fetcher import WebsiteFetcher
from .newsletter_fetcher import NewsletterFetcher

# グローバルレジストリを初期化
fetcher_registry = FetcherRegistry()

# 利用可能なFetcherを登録
fetcher_registry.register(RSSFetcher())
fetcher_registry.register(WebsiteFetcher())
fetcher_registry.register(NewsletterFetcher())

__all__ = ["fetcher_registry", "FetcherRegistry", "BaseFetcher"]
```

---

## 5. Collector Agent

### 5.1 責務

- Cloud Scheduler からのトリガー受信
- **複数ソース（RSS、Webサイト、メルマガ等）から記事を収集**
- **FetcherRegistryを使用して拡張可能な取得処理**
- **Firestoreに全記事を保存**（scoring_status: PENDING）
- **Pub/Subでスコアリング依頼**（score-request）

### 5.2 main.py - エントリポイント

```python
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
import base64
import logging

from shared.config import settings
from shared.models import BatchTriggerMessage
from .service import CollectorService

logger = logging.getLogger(__name__)
app = FastAPI(title="Collector Agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時の初期化処理
    yield
    # 終了時のクリーンアップ処理

@app.post("/")
async def handle_pubsub(request: Request):
    """Pub/Sub push エンドポイント"""
    envelope = await request.json()

    if "message" not in envelope:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

    pubsub_message = envelope["message"]
    data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    message = BatchTriggerMessage.model_validate_json(data)

    logger.info(f"Received batch trigger for user: {message.user_id}")

    service = CollectorService()
    result = await service.execute(message.user_id)

    return {"status": "success", "result": result}

@app.post("/api/v1/collect")
async def collect(user_id: str, rss_sources: list[str]):
    """手動トリガー用エンドポイント"""
    service = CollectorService()
    result = await service.execute(user_id, rss_sources)
    return result

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 5.3 service.py - ビジネスロジック

```python
from datetime import datetime
import asyncio
import logging

from shared.config import settings
from shared.firestore_client import FirestoreClient
from shared.pubsub_client import PubSubClient
from shared.fetchers import fetcher_registry
from shared.models import (
    ArticleCollection, CollectionStatus, ScoredArticle, ScoringStatus,
    ScoreRequestMessage, SourceConfig
)

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.firestore = FirestoreClient()
        self.pubsub = PubSubClient()
        self.fetcher_registry = fetcher_registry

    async def execute(self, user_id: str) -> dict:
        # 1. ユーザーのソース設定を取得
        user = await self.firestore.get_user(user_id)
        sources = [
            SourceConfig.model_validate(s)
            for s in user.get("sources", [])
        ]

        # 2. 各ソースから記事を並列収集
        articles = await self._fetch_all_sources(sources)
        logger.info(f"Fetched {len(articles)} articles from {len(sources)} sources")

        # 3. 重複URLを除去（同一バッチ内）
        articles = self._deduplicate(articles)

        # 4. 全記事をScoredArticleに変換（scoring_status: PENDING）
        scored_articles = [
            ScoredArticle(
                **article.model_dump(),
                scoring_status=ScoringStatus.PENDING
            )
            for article in articles
        ]

        # 5. 記事コレクション作成（Firestoreに保存）
        collection = ArticleCollection(
            id=f"collection_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            user_id=user_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            articles=scored_articles,
            status=CollectionStatus.SCORING,  # 次はスコアリング
            created_at=datetime.now()
        )
        await self.firestore.create_collection(collection)
        logger.info(f"Created collection: {collection.id} with {len(scored_articles)} articles")

        # 6. Librarian にスコアリング依頼（Pub/Sub）
        message = ScoreRequestMessage(
            user_id=user_id,
            collection_id=collection.id
        )
        await self.pubsub.publish(settings.pubsub_topic_score, message)
        logger.info(f"Published score-request for collection: {collection.id}")

        return {
            "status": "success",
            "articles_total": len(scored_articles),
            "collection_id": collection.id
        }

    async def _fetch_all_sources(
        self,
        sources: list[SourceConfig]
    ) -> list:
        """複数ソースから並列で記事を取得"""
        tasks = []
        for source in sources:
            if not source.enabled:
                continue

            fetcher = self.fetcher_registry.get_fetcher(source.type.value)
            if fetcher is None:
                logger.warning(f"No fetcher for source type: {source.type}")
                continue

            tasks.append(self._fetch_with_error_handling(fetcher, source))

        results = await asyncio.gather(*tasks)
        # フラット化
        return [article for articles in results for article in articles]

    async def _fetch_with_error_handling(
        self,
        fetcher,
        source: SourceConfig
    ) -> list:
        """エラーハンドリング付きで記事を取得"""
        try:
            return await fetcher.fetch(source)
        except Exception as e:
            logger.warning(f"Fetch failed for {source.name}: {e}")
            return []

    def _deduplicate(self, articles: list) -> list:
        """URLで重複を除去"""
        seen_urls = set()
        unique = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique.append(article)
        return unique
```

---

## 6. Librarian Agent

### 6.1 責務

- **Pub/Sub（score-request）からトリガー受信**
- **Firestoreから記事を読み取り**
- 全記事に関連性スコアを付与
- **Firestoreにスコアを書き戻し**（scoring_status: SCORED）
- **ピックアップ判定**（上位N件をマーク）
- **ピックアップ記事をPub/Sub（research-request）で送信**
- ユーザーのNotionメモをベクトル化して管理

### 6.2 main.py - エントリポイント

```python
from fastapi import FastAPI, Request, HTTPException
import base64
import logging

from shared.models import ScoreRequestMessage
from .service import LibrarianService

logger = logging.getLogger(__name__)
app = FastAPI(title="Librarian Agent")

@app.post("/")
async def handle_pubsub(request: Request):
    """Pub/Sub push エンドポイント（score-request）"""
    envelope = await request.json()

    if "message" not in envelope:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

    pubsub_message = envelope["message"]
    data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    message = ScoreRequestMessage.model_validate_json(data)

    logger.info(f"Received score request for collection: {message.collection_id}")

    service = LibrarianService()
    await service.score_collection(message.user_id, message.collection_id)

    return {"status": "success"}

@app.post("/api/v1/sync-embeddings")
async def sync_embeddings(user_id: str):
    """Notionメモのembeddingを同期"""
    service = LibrarianService()
    await service.sync_notion_embeddings(user_id)
    return {"status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 6.3 service.py - ビジネスロジック

```python
import asyncio
import logging

from shared.config import settings
from shared.notion_client import NotionClient
from shared.vector_search import VectorSearchClient
from shared.gemini_client import GeminiClient
from shared.firestore_client import FirestoreClient
from shared.pubsub_client import PubSubClient
from shared.models import (
    ScoredArticle, ScoringStatus, ResearchStatus, ResearchRequestMessage
)

logger = logging.getLogger(__name__)

class LibrarianService:
    def __init__(self):
        self.notion = NotionClient()
        self.vector_search = VectorSearchClient()
        self.gemini = GeminiClient(model="flash")
        self.firestore = FirestoreClient()
        self.pubsub = PubSubClient()

    async def score_collection(self, user_id: str, collection_id: str):
        """コレクション内の全記事にスコアを付与"""

        # 1. Firestoreからコレクションを読み取り
        collection = await self.firestore.get_collection(collection_id)
        logger.info(f"Scoring {len(collection.articles)} articles for collection: {collection_id}")

        # 2. 並列でスコアリング
        tasks = [
            self._score_single(user_id, article)
            for article in collection.articles
        ]
        scored_articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. エラー処理とスコア設定
        for i, result in enumerate(scored_articles):
            if isinstance(result, Exception):
                logger.warning(f"Scoring failed for article: {result}")
                collection.articles[i].scoring_status = ScoringStatus.SCORED
                collection.articles[i].relevance_score = 0.0
                collection.articles[i].relevance_reason = "スコアリング中にエラーが発生しました"
            else:
                collection.articles[i] = result

        # 4. スコア順にソートし、上位N件をピックアップとしてマーク
        collection.articles.sort(key=lambda x: x.relevance_score, reverse=True)
        pickup_count = settings.pickup_count
        for i, article in enumerate(collection.articles):
            if i < pickup_count and article.relevance_score > 0:
                article.is_pickup = True
                article.research_status = ResearchStatus.PENDING

        # 5. Firestoreに書き戻し
        await self.firestore.update_collection_articles(collection_id, collection.articles)
        logger.info(f"Updated scores for collection: {collection_id}")

        # 6. ピックアップ記事をResearcherに送信
        pickup_articles = [a for a in collection.articles if a.is_pickup]
        for article in pickup_articles:
            message = ResearchRequestMessage(
                user_id=user_id,
                collection_id=collection_id,
                article_url=article.url
            )
            await self.pubsub.publish(settings.pubsub_topic_research, message)
            logger.info(f"Published research-request for: {article.title}")

    async def _score_single(
        self,
        user_id: str,
        article: ScoredArticle
    ) -> ScoredArticle:
        """単一記事のスコアリング"""

        # 1. 記事をベクトル化
        article_text = f"{article.title}\n{article.content or ''}"
        article_embedding = await self.gemini.embed(article_text)

        # 2. 類似するNotionページを検索
        similar_pages = await self.vector_search.search(
            user_id=user_id,
            query_vector=article_embedding,
            top_k=5
        )

        # 3. スコアリング結果を設定
        article.scoring_status = ScoringStatus.SCORED

        if not similar_pages:
            article.relevance_score = 0.0
            article.relevance_reason = "関連するコンテキストが見つかりませんでした"
            article.related_notion_pages = []
            return article

        # 4. スコアと関連ページを設定
        article.relevance_score = similar_pages[0]["score"]
        article.related_notion_pages = [p["notion_page_id"] for p in similar_pages[:3]]
        article.relevance_reason = await self._generate_reason(article, similar_pages[0])

        return article

    async def _generate_reason(self, article: ScoredArticle, related_page: dict) -> str:
        """関連性の理由を生成"""
        prompt = f"""
        以下の記事とNotionメモの関連性を1文で説明してください。

        記事: {article.title}
        Notionメモ: {related_page['title']}

        例: 「過去のメモ「AIエージェント設計」で関心を示していたトピックです」
        """
        return await self.gemini.generate_text(prompt)

    async def sync_notion_embeddings(self, user_id: str):
        """Notionページのembeddingを同期"""

        # 1. Notionからページ一覧取得
        pages = await self.notion.get_all_pages(user_id)

        # 2. 各ページをベクトル化してVector Searchに登録
        for page in pages:
            content = await self.notion.get_page_content(page["id"])
            embedding = await self.gemini.embed(content)

            await self.vector_search.upsert(
                user_id=user_id,
                notion_page_id=page["id"],
                notion_page_title=page["title"],
                content=content[:1000],  # デバッグ用に一部保存
                embedding=embedding
            )
```

### 6.4 scorer.py - スコアリングロジック

```python
from typing import NamedTuple

class ScoreResult(NamedTuple):
    score: float
    reason: str
    related_pages: list[str]

class ArticleScorer:
    """記事のスコアリングロジック"""

    def calculate_score(
        self,
        vector_scores: list[dict],
        keyword_bonus: float = 0.0
    ) -> ScoreResult:
        """
        ベクトル類似度をベースにスコアを計算

        MVP ではベクトル類似度のみを使用。
        将来的にはキーワードマッチやユーザーフィードバックも考慮。
        """
        if not vector_scores:
            return ScoreResult(
                score=0.0,
                reason="関連するコンテキストがありません",
                related_pages=[]
            )

        # 上位3件の平均スコアを使用
        top_scores = [v["score"] for v in vector_scores[:3]]
        avg_score = sum(top_scores) / len(top_scores)

        # キーワードボーナスを加算（将来拡張用）
        final_score = min(avg_score + keyword_bonus, 1.0)

        return ScoreResult(
            score=final_score,
            reason=f"関連度: {final_score:.2f}",
            related_pages=[v["notion_page_id"] for v in vector_scores[:3]]
        )
```

---

## 7. Researcher Agent

### 7.1 責務

- **Pub/Sub（research-request）からトリガー受信**
- **Firestoreからピックアップ記事を読み取り**
- Gemini Pro による深掘りレポート生成
- **Firestoreにレポート保存**（research_status: COMPLETED）
- 全ピックアップ完了時にレポートステータスを更新

### 7.2 main.py - エントリポイント

```python
from fastapi import FastAPI, Request, HTTPException
import base64
import logging

from shared.models import ResearchRequestMessage
from .service import ResearcherService

logger = logging.getLogger(__name__)
app = FastAPI(title="Researcher Agent")

@app.post("/")
async def handle_pubsub(request: Request):
    """Pub/Sub push エンドポイント（research-request）"""
    envelope = await request.json()

    if "message" not in envelope:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")

    pubsub_message = envelope["message"]
    data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    message = ResearchRequestMessage.model_validate_json(data)

    logger.info(f"Received research request for article: {message.article_url}")

    service = ResearcherService()
    await service.research(message)

    return {"status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 7.3 service.py - ビジネスロジック

```python
import logging

from shared.firestore_client import FirestoreClient
from shared.models import ResearchRequestMessage, CollectionStatus, ResearchStatus
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ResearcherService:
    def __init__(self):
        self.firestore = FirestoreClient()
        self.generator = ReportGenerator()

    async def research(self, message: ResearchRequestMessage):
        """ピックアップ記事の詳細調査を実行"""

        # 1. Firestoreからコレクションと対象記事を取得
        collection = await self.firestore.get_collection(message.collection_id)
        article = next(
            (a for a in collection.articles if a.url == message.article_url),
            None
        )

        if not article:
            logger.error(f"Article not found: {message.article_url}")
            return

        # 2. research_status を RESEARCHING に更新
        await self.firestore.update_article_research_status(
            collection_id=message.collection_id,
            article_url=message.article_url,
            research_status=ResearchStatus.RESEARCHING
        )

        # 3. 詳細レポート生成
        deep_dive_report = await self.generator.generate(
            article=article,
            related_pages=article.related_notion_pages
        )

        # 4. 記事を更新（research_status: COMPLETED）
        await self.firestore.update_article_research(
            collection_id=message.collection_id,
            article_url=message.article_url,
            deep_dive_report=deep_dive_report,
            research_status=ResearchStatus.COMPLETED
        )
        logger.info(f"Research completed for: {article.title}")

        # 5. 全ピックアップ記事の処理完了か確認
        collection = await self.firestore.get_collection(message.collection_id)
        pickup_articles = [a for a in collection.articles if a.is_pickup]
        all_completed = all(
            a.research_status == ResearchStatus.COMPLETED
            for a in pickup_articles
        )

        if all_completed:
            await self.firestore.update_collection_status(
                message.collection_id,
                CollectionStatus.COMPLETED
            )
            logger.info(f"Collection completed: {message.collection_id}")
```

### 7.4 report_generator.py - レポート生成

```python
from shared.gemini_client import GeminiClient
from shared.notion_client import NotionClient
from shared.models import ScoredArticle
from shared.retry import with_retry

RESEARCH_PROMPT = """
以下のニュース記事について、詳細な分析レポートを作成してください。

## 記事情報
タイトル: {title}
URL: {url}
概要: {content}

## ユーザーの関連メモ
{related_context}

## レポート要件
1. **要約** (3-5文): 記事の核心を簡潔に
2. **なぜあなたに関連するか**: ユーザーのメモとの関連性を説明
3. **キーポイント** (箇条書き): 重要な技術的ポイント
4. **アクションアイテム** (任意): この情報を活かすための次のステップ

マークダウン形式で出力してください。
"""

class ReportGenerator:
    def __init__(self):
        self.gemini = GeminiClient(model="pro")
        self.notion = NotionClient()

    @with_retry
    async def generate(
        self,
        article: ScoredArticle,
        related_pages: list[str]
    ) -> str:
        """詳細レポートを生成"""

        # 関連Notionページのコンテンツを取得
        related_context = await self._get_related_context(related_pages)

        prompt = RESEARCH_PROMPT.format(
            title=article.title,
            url=article.url,
            content=article.content or "",
            related_context=related_context
        )

        return await self.gemini.generate_text(prompt)

    async def _get_related_context(self, page_ids: list[str]) -> str:
        """関連Notionページのコンテンツを取得"""
        if not page_ids:
            return "関連メモなし"

        contexts = []
        for page_id in page_ids[:3]:  # 最大3ページ
            try:
                content = await self.notion.get_page_content(page_id)
                contexts.append(f"- {content[:500]}...")
            except Exception:
                continue

        return "\n".join(contexts) if contexts else "関連メモなし"
```

---

## 8. 共通クライアント実装

### 8.1 gemini_client.py

```python
from google import genai
from google.genai import types
import json

from .config import settings

class GeminiClient:
    def __init__(self, model: str = "flash"):
        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location="asia-northeast1"
        )
        self.model_name = (
            settings.gemini_flash_model
            if model == "flash"
            else settings.gemini_pro_model
        )

    async def generate_text(self, prompt: str) -> str:
        """テキスト生成"""
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return response.text

    async def generate_json(self, prompt: str) -> dict | list:
        """JSON形式で生成"""
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    async def embed(self, text: str) -> list[float]:
        """テキストをベクトル化"""
        response = await self.client.aio.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values
```

### 8.2 firestore_client.py

```python
from google.cloud import firestore
from typing import Optional

from .config import settings
from .models import ArticleCollection, CollectionStatus, ScoredArticle, ResearchStatus

class FirestoreClient:
    def __init__(self):
        self.db = firestore.AsyncClient(
            project=settings.google_cloud_project,
            database=settings.firestore_database
        )

    async def get_user(self, user_id: str) -> dict:
        doc = await self.db.collection("users").document(user_id).get()
        return doc.to_dict() if doc.exists else {}

    async def create_collection(self, collection: ArticleCollection):
        """記事コレクションを作成"""
        await self.db.collection("collections").document(collection.id).set(
            collection.model_dump()
        )

    async def get_collection(self, collection_id: str) -> ArticleCollection:
        """記事コレクションを取得"""
        doc = await self.db.collection("collections").document(collection_id).get()
        return ArticleCollection.model_validate(doc.to_dict())

    async def update_collection_articles(
        self,
        collection_id: str,
        articles: list[ScoredArticle]
    ):
        """コレクション内の全記事を更新（Librarianが使用）"""
        await self.db.collection("collections").document(collection_id).update({
            "articles": [a.model_dump() for a in articles]
        })

    async def update_article_research_status(
        self,
        collection_id: str,
        article_url: str,
        research_status: ResearchStatus
    ):
        """記事のresearch_statusを更新"""
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        data = doc.to_dict()

        for article in data["articles"]:
            if article["url"] == article_url:
                article["research_status"] = research_status.value
                break

        await doc_ref.update({"articles": data["articles"]})

    async def update_article_research(
        self,
        collection_id: str,
        article_url: str,
        deep_dive_report: str,
        research_status: Optional[ResearchStatus] = None
    ):
        """記事の詳細レポートとステータスを更新（Researcherが使用）"""
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        data = doc.to_dict()

        for article in data["articles"]:
            if article["url"] == article_url:
                article["deep_dive_report"] = deep_dive_report
                if research_status:
                    article["research_status"] = research_status.value
                break

        await doc_ref.update({"articles": data["articles"]})

    async def update_collection_status(
        self,
        collection_id: str,
        status: CollectionStatus
    ):
        """コレクション全体のステータスを更新"""
        await self.db.collection("collections").document(collection_id).update({
            "status": status.value
        })
```

### 8.3 notion_client.py

```python
from notion_client import AsyncClient

from .config import settings

class NotionClient:
    def __init__(self):
        self.client = AsyncClient(auth=settings.notion_token)

    async def get_all_pages(self, user_id: str) -> list[dict]:
        """ユーザーのNotionページ一覧を取得"""
        # Internal Integration の場合、アクセス可能な全ページを取得
        results = []
        cursor = None

        while True:
            response = await self.client.search(
                filter={"property": "object", "value": "page"},
                start_cursor=cursor
            )

            for page in response["results"]:
                results.append({
                    "id": page["id"],
                    "title": self._extract_title(page),
                    "url": page["url"]
                })

            if not response["has_more"]:
                break
            cursor = response["next_cursor"]

        return results

    async def get_page_content(self, page_id: str) -> str:
        """ページのコンテンツを取得"""
        blocks = await self.client.blocks.children.list(page_id)

        content_parts = []
        for block in blocks["results"]:
            text = self._extract_block_text(block)
            if text:
                content_parts.append(text)

        return "\n".join(content_parts)

    def _extract_title(self, page: dict) -> str:
        """ページタイトルを抽出"""
        props = page.get("properties", {})
        for prop in props.values():
            if prop["type"] == "title":
                title_parts = prop.get("title", [])
                return "".join(t["plain_text"] for t in title_parts)
        return "Untitled"

    def _extract_block_text(self, block: dict) -> str:
        """ブロックからテキストを抽出"""
        block_type = block["type"]
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
            rich_text = block[block_type].get("rich_text", [])
            return "".join(t["plain_text"] for t in rich_text)
        return ""
```

### 8.4 http_client.py

```python
import httpx
from typing import Any

class HttpClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def post(self, url: str, data: dict) -> Any:
        """POST リクエストを送信"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
```

---

## 9. デプロイ

### 9.1 Dockerfile (共通テンプレート)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 共通モジュールをコピー
COPY shared/ ./shared/

# エージェント固有のファイルをコピー
COPY collector/ ./collector/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "collector.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 9.2 Cloud Run デプロイコマンド

```bash
# Collector Agent
gcloud run deploy collector-agent \
  --source ./services/agents \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=curation-persona"

# Librarian Agent
gcloud run deploy librarian-agent \
  --source ./services/agents \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=curation-persona"

# Researcher Agent
gcloud run deploy researcher-agent \
  --source ./services/agents \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=curation-persona"
```

### 9.3 Pub/Sub トピック・サブスクリプション設定

```bash
# トピック作成
gcloud pubsub topics create batch-trigger
gcloud pubsub topics create score-request
gcloud pubsub topics create research-request

# batch-trigger → Collector Agent
gcloud pubsub subscriptions create batch-trigger-sub \
  --topic batch-trigger \
  --push-endpoint https://collector-agent-xxx.run.app

# score-request → Librarian Agent
gcloud pubsub subscriptions create score-request-sub \
  --topic score-request \
  --push-endpoint https://librarian-agent-xxx.run.app

# research-request → Researcher Agent
gcloud pubsub subscriptions create research-request-sub \
  --topic research-request \
  --push-endpoint https://researcher-agent-xxx.run.app
```

---

## 10. テスト戦略

### 10.1 テスト構成

```
services/agents/
└── tests/
    ├── unit/
    │   ├── test_rss_fetcher.py
    │   ├── test_scorer.py
    │   └── test_report_generator.py
    ├── integration/
    │   ├── test_collector_service.py
    │   ├── test_librarian_service.py
    │   └── test_researcher_service.py
    └── conftest.py
```

### 10.2 ユニットテスト例

```python
# tests/unit/test_scorer.py
import pytest

from librarian.scorer import ArticleScorer, ScoreResult

def test_scorer_with_no_results():
    scorer = ArticleScorer()
    result = scorer.calculate_score([])

    assert result.score == 0.0
    assert result.related_pages == []

def test_scorer_calculates_average():
    scorer = ArticleScorer()
    vector_scores = [
        {"score": 0.9, "notion_page_id": "page1"},
        {"score": 0.8, "notion_page_id": "page2"},
        {"score": 0.7, "notion_page_id": "page3"},
    ]

    result = scorer.calculate_score(vector_scores)

    assert result.score == 0.8  # (0.9 + 0.8 + 0.7) / 3
    assert len(result.related_pages) == 3
```

### 10.3 ローカル実行

```bash
# テスト実行
cd services/agents
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=. --cov-report=html
```

---

## 11. 開発環境セットアップ

### 11.1 前提条件

- Python 3.11+
- Google Cloud SDK
- Docker (オプション)

### 11.2 セットアップ手順

```bash
# 1. リポジトリクローン
git clone <repository>
cd curation-persona/services/agents

# 2. 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 3. 依存関係インストール
pip install -e ".[dev]"

# 4. 環境変数設定
cp .env.example .env
# .env を編集

# 5. GCP認証
gcloud auth application-default login

# 6. ローカル起動
uvicorn collector.main:app --reload --port 8001
uvicorn librarian.main:app --reload --port 8002
uvicorn researcher.main:app --reload --port 8003
```

### 11.3 .env.example

```bash
GOOGLE_CLOUD_PROJECT=curation-persona
FIRESTORE_DATABASE=(default)
PUBSUB_TOPIC_BATCH=batch-trigger
PUBSUB_TOPIC_SCORE=score-request
PUBSUB_TOPIC_RESEARCH=research-request
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_PRO_MODEL=gemini-2.5-pro
VECTOR_SEARCH_INDEX_ENDPOINT=projects/xxx/locations/asia-northeast1/indexEndpoints/xxx
VECTOR_SEARCH_DEPLOYED_INDEX_ID=xxx
NOTION_TOKEN=ntn_xxx
PICKUP_COUNT=2
```

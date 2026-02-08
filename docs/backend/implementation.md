# バックエンド実装設計書

> **対象**: Curation Persona - Agent Layer (Cloud Run)
>
> **スコープ**: ハッカソンMVP

---

## 1. 概要

バックエンドは3つのAIエージェントで構成される。各エージェントはCloud Run上で独立したサービスとして動作し、[A2Aプロトコル](https://a2a-protocol.org/latest/)を介して連携する。

### 1.1 エージェント一覧

| エージェント | 役割 | LLMモデル |
|-------------|------|-----------|
| Collector Agent | RSS巡回、記事収集、フロー制御 | - |
| Librarian Agent | 全記事への関連性スコア付与、ピックアップ選定 | Gemini 2.5 Flash (LLMスコアリング) |
| Researcher Agent | ユーザーリクエストによる詳細レポート生成 | Gemini 2.5 Pro |

### 1.2 設計方針

- **ソース厳選**: RSSソースをユーザーが厳選することで、取得記事の品質を担保
- **全件表示**: 取得した記事は全て「本日のニュース」として表示
- **ピックアップ深掘り**: 関連性スコア上位N件のみResearcherで詳細レポート生成
- **コスト最適化**: 高コストなGemini Proはピックアップ記事のみに使用

### 1.3 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.11+ |
| Webフレームワーク | FastAPI + a2a-sdk |
| LLM SDK | google-genai (Vertex AI) |
| エージェント間通信 | A2A Protocol (a2a-sdk) |
| データベース | Cloud Firestore |

---

## 2. 処理フロー

### 2.1 全体フロー図

```
Cloud Scheduler (毎朝6時)
    │
    ▼ HTTP トリガー
┌─────────────────────────────────────┐
│ Collector Agent (A2A Server)        │
│  - RSS取得（ソースは厳選済み）       │
│  - 全記事をFirestoreに保存           │
│    (scoring_status: PENDING)        │
└─────────────────────────────────────┘
    │
    │ Firestore: 記事保存
    ▼ A2A: score_articles
┌─────────────────────────────────────┐
│ Librarian Agent (A2A Server)        │
│  - 過去の高評価記事（4-5★）を取得    │
│  - Gemini Flashで興味プロファイル生成 │
│  - 全記事にLLMベーススコア付与       │
│  - Firestoreにスコア書き戻し         │
│    (scoring_status: SCORED)         │
│  - 上位N件をピックアップとしてマーク  │
│    (is_pickup: true)                │
└─────────────────────────────────────┘
    │
    │ Firestore: スコア更新
    ▼ バッチ処理完了

┌─────────────────────────────────────┐
│ Dashboard API（ユーザー手動トリガー） │
│  - ユーザーが「深掘りリクエスト」送信 │
└─────────────────────────────────────┘
    │
    ▼ A2A: research_article
┌─────────────────────────────────────┐
│ Researcher Agent (A2A Server)       │
│  - Firestoreから対象記事読み取り     │
│  - 過去の高評価記事のコンテキスト取得│
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
│   ├── a2a_client.py          # A2A通信クライアント
│   ├── gemini_client.py       # Gemini API操作
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
│   ├── main.py                # A2A Server エントリポイント
│   ├── agent_card.py          # Agent Card 定義
│   ├── service.py             # ビジネスロジック
│   ├── Dockerfile
│   └── requirements.txt
│
├── librarian/                  # Librarian Agent
│   ├── main.py                # A2A Server エントリポイント
│   ├── agent_card.py          # Agent Card 定義
│   ├── service.py             # ビジネスロジック
│   ├── scorer.py              # 関連性スコアリング
│   ├── Dockerfile
│   └── requirements.txt
│
├── researcher/                 # Researcher Agent
│   ├── main.py                # A2A Server エントリポイント
│   ├── agent_card.py          # Agent Card 定義
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

    # A2A エージェント間通信
    librarian_agent_url: str  # Librarian Agent の URL
    researcher_agent_url: str  # Researcher Agent の URL

    # Gemini
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"

    # ピックアップ設定
    pickup_count: int = 2  # ピックアップとしてマークする記事数

    # スコアリング設定
    min_ratings_for_scoring: int = 3  # スコアリングに必要な最低評価数
    high_rating_threshold: int = 4     # 高評価とみなす最低評価値（4-5★）

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4.2 models.py - 共通データモデル

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

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
    relevance_reason: str = ""    # 過去の高評価記事との関連理由

    # ピックアップ関連（ピックアップ記事のみ使用）
    is_pickup: bool = False
    research_status: Optional[ResearchStatus] = None  # ピックアップ時のみ設定
    deep_dive_report: Optional[str] = None

    # ユーザー評価
    user_rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 の5段階評価
    user_comment: Optional[str] = None

class ArticleCollection(BaseModel):
    """日次の記事コレクション（収集した記事の集合）"""
    id: str
    user_id: str
    date: str  # "2025-01-15"
    articles: list[ScoredArticle] = []  # 全記事（ピックアップ含む）
    status: CollectionStatus
    created_at: datetime

# A2A スキルパラメータ
class ScoreArticlesParams(BaseModel):
    """score_articles スキル: Collector → Librarian"""
    user_id: str
    collection_id: str

class ResearchArticleParams(BaseModel):
    """research_article スキル: Librarian → Researcher"""
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
- **A2AでLibrarianにスコアリング依頼**（score_articles スキル）

### 5.2 main.py - A2A Server エントリポイント

```python
from a2a import A2AServer, AgentCard, Skill, Task
from fastapi import FastAPI
import logging

from .agent_card import agent_card
from .service import CollectorService

logger = logging.getLogger(__name__)

# A2A Server 初期化
server = A2AServer(agent_card)
service = CollectorService()

@server.skill("collect_articles")
async def collect_articles(task: Task) -> Task:
    """記事収集スキル（Cloud Scheduler からトリガー）"""
    params = task.message.parts[0].data
    user_id = params["user_id"]

    logger.info(f"Starting article collection for user: {user_id}")

    result = await service.execute(user_id)

    return task.complete(artifact={
        "collection_id": result["collection_id"],
        "articles_total": result["articles_total"]
    })

# FastAPI アプリとしてマウント
app = FastAPI(title="Collector Agent")
app.mount("/", server.app)

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 5.2.1 agent_card.py - Agent Card 定義

```python
from a2a import AgentCard, Skill

agent_card = AgentCard(
    name="Collector Agent",
    description="RSS/Webサイトから記事を収集し、スコアリングを依頼するエージェント",
    url="https://collector-agent-xxx.run.app",
    skills=[
        Skill(
            id="collect_articles",
            name="記事収集",
            description="ユーザーのソース設定に基づいて記事を収集し、Librarianにスコアリングを依頼"
        )
    ],
    capabilities={
        "streaming": False,
        "pushNotifications": False
    }
)
```

### 5.3 service.py - ビジネスロジック

```python
from datetime import datetime
import asyncio
import logging

from shared.config import settings
from shared.firestore_client import FirestoreClient
from shared.a2a_client import A2AClient
from shared.fetchers import fetcher_registry
from shared.models import (
    ArticleCollection, CollectionStatus, ScoredArticle, ScoringStatus,
    ScoreArticlesParams, SourceConfig
)

logger = logging.getLogger(__name__)

class CollectorService:
    def __init__(self):
        self.firestore = FirestoreClient()
        self.a2a_client = A2AClient()
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

        # 6. Librarian にスコアリング依頼（A2A）
        params = ScoreArticlesParams(
            user_id=user_id,
            collection_id=collection.id
        )
        await self.a2a_client.send_message(
            agent_url=settings.librarian_agent_url,
            skill="score_articles",
            params=params.model_dump()
        )
        logger.info(f"Sent A2A score_articles request for collection: {collection.id}")

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

- **A2A（score_articles スキル）でCollectorからトリガー受信**
- **Firestoreから記事を読み取り**
- **過去の高評価記事（4-5★）からユーザー興味プロファイルを生成**
- **全記事にLLMベーススコアを付与**（Gemini Flash）
- **Firestoreにスコアを書き戻し**（scoring_status: SCORED）
- **ピックアップ判定**（上位N件をマーク）
- **コールドスタート対応**（評価データ不足時はスコア0.5固定）

### 6.2 main.py - A2A Server エントリポイント

```python
from a2a import A2AServer, Task
from fastapi import FastAPI
import logging

from .agent_card import agent_card
from .service import LibrarianService

logger = logging.getLogger(__name__)

# A2A Server 初期化
server = A2AServer(agent_card)
service = LibrarianService()

@server.skill("score_articles")
async def score_articles(task: Task) -> Task:
    """記事スコアリングスキル（Collector から呼び出し）"""
    params = task.message.parts[0].data
    user_id = params["user_id"]
    collection_id = params["collection_id"]

    logger.info(f"Starting scoring for collection: {collection_id}")

    await service.score_collection(user_id, collection_id)

    return task.complete(artifact={
        "collection_id": collection_id,
        "status": "scored"
    })

# FastAPI アプリとしてマウント
app = FastAPI(title="Librarian Agent")
app.mount("/", server.app)

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 6.2.1 agent_card.py - Agent Card 定義

```python
from a2a import AgentCard, Skill

agent_card = AgentCard(
    name="Librarian Agent",
    description="ユーザー評価ベースのLLMスコアリングで記事に関連性スコアを付与するエージェント",
    url="https://librarian-agent-xxx.run.app",
    skills=[
        Skill(
            id="score_articles",
            name="記事スコアリング",
            description="コレクション内の全記事にユーザー評価ベースの関連性スコアを付与"
        )
    ],
    capabilities={
        "streaming": False,
        "pushNotifications": False
    }
)
```

### 6.3 service.py - ビジネスロジック

```python
import asyncio
import logging

from shared.config import settings
from shared.gemini_client import GeminiClient
from shared.firestore_client import FirestoreClient
from shared.models import (
    ScoredArticle, ScoringStatus, ResearchStatus, CollectionStatus
)

logger = logging.getLogger(__name__)

class LibrarianService:
    def __init__(self):
        self.gemini = GeminiClient(model="flash")
        self.firestore = FirestoreClient()

    async def score_collection(self, user_id: str, collection_id: str):
        """コレクション内の全記事にスコアを付与"""

        # 1. Firestoreからコレクションを読み取り
        collection = await self.firestore.get_collection(collection_id)
        logger.info(f"Scoring {len(collection.articles)} articles for collection: {collection_id}")

        # 2. 過去の高評価記事を取得してユーザー興味プロファイルを生成
        high_rated_articles = await self.firestore.get_high_rated_articles(
            user_id=user_id,
            min_rating=settings.high_rating_threshold
        )

        # 3. コールドスタート判定
        if len(high_rated_articles) < settings.min_ratings_for_scoring:
            logger.info(f"Cold start: only {len(high_rated_articles)} ratings, skipping LLM scoring")
            for article in collection.articles:
                article.scoring_status = ScoringStatus.SCORED
                article.relevance_score = 0.5  # 全記事同一スコア
                article.relevance_reason = "評価データ蓄積中のため、スコアリングをスキップしました"
        else:
            # 4. ユーザー興味プロファイルを生成
            interest_profile = await self._generate_interest_profile(high_rated_articles)
            logger.info(f"Generated interest profile from {len(high_rated_articles)} high-rated articles")

            # 5. 並列でスコアリング
            tasks = [
                self._score_single(article, interest_profile)
                for article in collection.articles
            ]
            scored_articles = await asyncio.gather(*tasks, return_exceptions=True)

            # 6. エラー処理とスコア設定
            for i, result in enumerate(scored_articles):
                if isinstance(result, Exception):
                    logger.warning(f"Scoring failed for article: {result}")
                    collection.articles[i].scoring_status = ScoringStatus.SCORED
                    collection.articles[i].relevance_score = 0.0
                    collection.articles[i].relevance_reason = "スコアリング中にエラーが発生しました"
                else:
                    collection.articles[i] = result

        # 7. スコア順にソートし、上位N件をピックアップとしてマーク
        collection.articles.sort(key=lambda x: x.relevance_score, reverse=True)
        pickup_count = settings.pickup_count
        for i, article in enumerate(collection.articles):
            if i < pickup_count and article.relevance_score > 0:
                article.is_pickup = True
                article.research_status = ResearchStatus.PENDING

        # 8. Firestoreに書き戻し
        await self.firestore.update_collection_articles(collection_id, collection.articles)

        # 9. コレクションステータスを完了に更新（Researcherは手動トリガーのため）
        await self.firestore.update_collection_status(
            collection_id, CollectionStatus.COMPLETED
        )
        logger.info(f"Scoring completed for collection: {collection_id}")

    async def _generate_interest_profile(self, high_rated_articles: list[dict]) -> str:
        """過去の高評価記事からユーザー興味プロファイルを生成"""
        articles_summary = "\n".join([
            f"- タイトル: {a['title']}, 評価: {a['user_rating']}★"
            + (f", コメント: {a['user_comment']}" if a.get('user_comment') else "")
            for a in high_rated_articles[:20]  # 最新20件まで
        ])

        prompt = f"""
以下はユーザーが高く評価した記事の一覧です。
この情報から、ユーザーの技術的な興味・関心を簡潔にまとめてください。

## 高評価記事
{articles_summary}

## 出力形式
- ユーザーの主な関心分野（箇条書き3-5項目）
- 特に注目しているキーワードやトピック
"""
        return await self.gemini.generate_text(prompt)

    async def _score_single(
        self,
        article: ScoredArticle,
        interest_profile: str
    ) -> ScoredArticle:
        """単一記事のLLMベーススコアリング"""

        article_text = f"{article.title}\n{article.content or ''}"

        prompt = f"""
以下のユーザー興味プロファイルに基づいて、記事の関連性を評価してください。

## ユーザー興味プロファイル
{interest_profile}

## 記事
{article_text}

## 出力形式（JSON）
{{
  "score": 0.0〜1.0の数値（関連性が高いほど1.0に近い）,
  "reason": "この記事がユーザーに関連する理由を1文で"
}}
"""
        result = await self.gemini.generate_json(prompt)

        article.scoring_status = ScoringStatus.SCORED
        article.relevance_score = min(max(float(result.get("score", 0.0)), 0.0), 1.0)
        article.relevance_reason = result.get("reason", "")

        return article
```

### 6.4 scorer.py - LLMベーススコアリングロジック

```python
from typing import NamedTuple
from shared.gemini_client import GeminiClient

class ScoreResult(NamedTuple):
    score: float
    reason: str

class ArticleScorer:
    """LLMベースの記事スコアリングロジック"""

    def __init__(self):
        self.gemini = GeminiClient(model="flash")

    async def calculate_score(
        self,
        article_text: str,
        interest_profile: str
    ) -> ScoreResult:
        """
        ユーザー興味プロファイルに基づいてLLMでスコアを計算

        Args:
            article_text: 記事のタイトル+本文
            interest_profile: ユーザーの興味プロファイル（LLM生成）

        Returns:
            スコアと理由のタプル
        """
        if not interest_profile:
            return ScoreResult(
                score=0.5,
                reason="評価データ蓄積中のため、デフォルトスコアを設定しました"
            )

        prompt = f"""
以下のユーザー興味プロファイルに基づいて、記事の関連性を評価してください。

## ユーザー興味プロファイル
{interest_profile}

## 記事
{article_text}

## 出力形式（JSON）
{{
  "score": 0.0〜1.0の数値（関連性が高いほど1.0に近い）,
  "reason": "この記事がユーザーに関連する理由を1文で"
}}
"""
        result = await self.gemini.generate_json(prompt)

        score = min(max(float(result.get("score", 0.0)), 0.0), 1.0)
        reason = result.get("reason", "")

        return ScoreResult(score=score, reason=reason)
```

---

## 7. Researcher Agent

### 7.1 責務

- **A2A（research_article スキル）でDashboard APIからトリガー受信（ユーザー手動リクエスト）**
- **Firestoreから対象記事を読み取り**
- **過去の高評価記事のコンテキストを取得**
- Gemini Pro による深掘りレポート生成
- **Firestoreにレポート保存**（research_status: COMPLETED）

### 7.2 main.py - A2A Server エントリポイント

```python
from a2a import A2AServer, Task
from fastapi import FastAPI
import logging

from .agent_card import agent_card
from .service import ResearcherService
from shared.models import ResearchArticleParams

logger = logging.getLogger(__name__)

# A2A Server 初期化
server = A2AServer(agent_card)
service = ResearcherService()

@server.skill("research_article")
async def research_article(task: Task) -> Task:
    """記事詳細調査スキル（Dashboard API から手動トリガー）"""
    params = task.message.parts[0].data
    research_params = ResearchArticleParams(**params)

    logger.info(f"Starting research for article: {research_params.article_url}")

    await service.research(research_params)

    return task.complete(artifact={
        "article_url": research_params.article_url,
        "status": "completed"
    })

# FastAPI アプリとしてマウント
app = FastAPI(title="Researcher Agent")
app.mount("/", server.app)

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 7.2.1 agent_card.py - Agent Card 定義

```python
from a2a import AgentCard, Skill

agent_card = AgentCard(
    name="Researcher Agent",
    description="ピックアップ記事の詳細調査レポートを生成するエージェント",
    url="https://researcher-agent-xxx.run.app",
    skills=[
        Skill(
            id="research_article",
            name="記事詳細調査",
            description="記事の深掘りレポートをGemini Proで生成"
        )
    ],
    capabilities={
        "streaming": False,
        "pushNotifications": False
    }
)
```

### 7.3 service.py - ビジネスロジック

```python
import logging

from shared.firestore_client import FirestoreClient
from shared.models import ResearchArticleParams, ResearchStatus
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ResearcherService:
    def __init__(self):
        self.firestore = FirestoreClient()
        self.generator = ReportGenerator()

    async def research(self, params: ResearchArticleParams):
        """ユーザーリクエストに基づく詳細調査を実行"""

        # 1. Firestoreからコレクションと対象記事を取得
        collection = await self.firestore.get_collection(params.collection_id)
        article = next(
            (a for a in collection.articles if a.url == params.article_url),
            None
        )

        if not article:
            logger.error(f"Article not found: {params.article_url}")
            return

        # 2. research_status を RESEARCHING に更新
        await self.firestore.update_article_research_status(
            collection_id=params.collection_id,
            article_url=params.article_url,
            research_status=ResearchStatus.RESEARCHING
        )

        # 3. 過去の高評価記事のコンテキストを取得
        high_rated_articles = await self.firestore.get_high_rated_articles(
            user_id=params.user_id,
            min_rating=4
        )

        # 4. 詳細レポート生成
        deep_dive_report = await self.generator.generate(
            article=article,
            related_articles=high_rated_articles
        )

        # 5. 記事を更新（research_status: COMPLETED）
        await self.firestore.update_article_research(
            collection_id=params.collection_id,
            article_url=params.article_url,
            deep_dive_report=deep_dive_report,
            research_status=ResearchStatus.COMPLETED
        )
        logger.info(f"Research completed for: {article.title}")
```

### 7.4 report_generator.py - レポート生成

```python
from shared.gemini_client import GeminiClient
from shared.models import ScoredArticle
from shared.retry import with_retry

RESEARCH_PROMPT = """
以下のニュース記事について、詳細な分析レポートを作成してください。

## 記事情報
タイトル: {title}
URL: {url}
概要: {content}

## 過去の関連する高評価記事
{related_context}

## レポート要件
1. **要約** (3-5文): 記事の核心を簡潔に
2. **なぜあなたに関連するか**: 過去に高評価した記事との関連性を説明
3. **キーポイント** (箇条書き): 重要な技術的ポイント
4. **アクションアイテム** (任意): この情報を活かすための次のステップ

マークダウン形式で出力してください。
"""

class ReportGenerator:
    def __init__(self):
        self.gemini = GeminiClient(model="pro")

    @with_retry
    async def generate(
        self,
        article: ScoredArticle,
        related_articles: list[dict]
    ) -> str:
        """詳細レポートを生成"""

        # 過去の高評価記事のコンテキストを取得
        related_context = self._get_related_context(related_articles)

        prompt = RESEARCH_PROMPT.format(
            title=article.title,
            url=article.url,
            content=article.content or "",
            related_context=related_context
        )

        return await self.gemini.generate_text(prompt)

    def _get_related_context(self, articles: list[dict]) -> str:
        """過去の高評価記事のコンテキストを生成"""
        if not articles:
            return "関連する高評価記事なし"

        contexts = []
        for article in articles[:5]:  # 最大5件
            context = f"- {article['title']}（{article['user_rating']}★）"
            if article.get('user_comment'):
                context += f" - {article['user_comment']}"
            contexts.append(context)

        return "\n".join(contexts)
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

### 8.2 a2a_client.py

```python
from a2a import A2AClient as BaseA2AClient, Message, Part
import logging

logger = logging.getLogger(__name__)

class A2AClient:
    """A2Aプロトコルでエージェント間通信を行うクライアント"""

    async def send_message(
        self,
        agent_url: str,
        skill: str,
        params: dict
    ) -> dict:
        """
        他のエージェントにA2Aメッセージを送信

        Args:
            agent_url: 送信先エージェントのURL
            skill: 実行するスキル名
            params: スキルに渡すパラメータ

        Returns:
            Task の完了結果
        """
        client = BaseA2AClient(agent_url)

        message = Message(
            role="user",
            parts=[Part(type="data", data={"skill": skill, **params})]
        )

        task = await client.send_message(message)

        logger.info(f"A2A message sent to {agent_url}, task_id: {task.id}")

        # タスク完了を待機（同期的に処理）
        completed_task = await client.wait_for_completion(task.id)

        return completed_task.artifact
```

### 8.3 firestore_client.py

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

    async def get_high_rated_articles(
        self,
        user_id: str,
        min_rating: int = 4
    ) -> list[dict]:
        """過去の高評価記事を取得（スコアリング・レポート生成用）"""
        collections = self.db.collection("collections").where(
            "userId", "==", user_id
        ).order_by("createdAt", direction="DESCENDING").limit(30)

        high_rated = []
        async for doc in collections.stream():
            data = doc.to_dict()
            for article in data.get("articles", []):
                if article.get("userRating") and article["userRating"] >= min_rating:
                    high_rated.append({
                        "title": article["title"],
                        "url": article["url"],
                        "content": article.get("content", "")[:300],
                        "user_rating": article["userRating"],
                        "user_comment": article.get("userComment"),
                    })

        return high_rated

    async def update_article_feedback(
        self,
        collection_id: str,
        article_url: str,
        rating: int,
        comment: Optional[str] = None
    ):
        """記事のユーザー評価を更新"""
        doc_ref = self.db.collection("collections").document(collection_id)
        doc = await doc_ref.get()
        data = doc.to_dict()

        for article in data["articles"]:
            if article["url"] == article_url:
                article["userRating"] = rating
                article["userComment"] = comment
                break

        await doc_ref.update({"articles": data["articles"]})
```

### 8.3 http_client.py

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

### 9.3 Cloud Scheduler 設定（A2A トリガー）

```bash
# 毎朝6時にCollector Agentをトリガー
gcloud scheduler jobs create http collect-daily \
  --location asia-northeast1 \
  --schedule "0 6 * * *" \
  --time-zone "Asia/Tokyo" \
  --uri "https://collector-agent-xxx.run.app/a2a" \
  --http-method POST \
  --headers "Content-Type=application/json" \
  --message-body '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{
          "type": "data",
          "data": {
            "skill": "collect_articles",
            "user_id": "user_123"
          }
        }]
      }
    },
    "id": "scheduler-trigger"
  }'
```

> **Note**: エージェント間通信はA2Aプロトコル（HTTP直接通信）で行うため、Pub/Subは不要。

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
from unittest.mock import AsyncMock, patch

from librarian.scorer import ArticleScorer, ScoreResult

@pytest.mark.asyncio
async def test_scorer_with_no_profile():
    scorer = ArticleScorer()
    result = await scorer.calculate_score(
        article_text="Test article",
        interest_profile=""
    )

    assert result.score == 0.5
    assert "デフォルトスコア" in result.reason

@pytest.mark.asyncio
@patch.object(ArticleScorer, '_call_gemini')
async def test_scorer_with_profile(mock_gemini):
    mock_gemini.return_value = {"score": 0.85, "reason": "AI関連の記事"}
    scorer = ArticleScorer()

    result = await scorer.calculate_score(
        article_text="AI Agent の新設計パターン",
        interest_profile="ユーザーはAIエージェント設計に強い関心がある"
    )

    assert result.score == 0.85
    assert "AI" in result.reason
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
LIBRARIAN_AGENT_URL=http://localhost:8002
RESEARCHER_AGENT_URL=http://localhost:8003
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_PRO_MODEL=gemini-2.5-pro
PICKUP_COUNT=2
MIN_RATINGS_FOR_SCORING=3
HIGH_RATING_THRESHOLD=4
```

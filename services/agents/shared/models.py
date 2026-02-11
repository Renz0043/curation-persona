from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CollectionStatus(str, Enum):
    COLLECTING = "collecting"
    SCORING = "scoring"
    RESEARCHING = "researching"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoringStatus(str, Enum):
    PENDING = "pending"
    SCORING = "scoring"
    SCORED = "scored"


class ResearchStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    COMPLETED = "completed"


class SourceType(str, Enum):
    RSS = "rss"
    WEBSITE = "website"
    NEWSLETTER = "newsletter"
    API = "api"


class SourceConfig(BaseModel):
    id: str
    type: SourceType
    name: str
    enabled: bool = True
    config: dict = {}


class Article(BaseModel):
    title: str
    url: str
    source: str
    source_type: SourceType
    content: Optional[str] = None
    published_at: Optional[datetime] = None


class ScoredArticle(Article):
    scoring_status: ScoringStatus = ScoringStatus.PENDING
    relevance_score: float = 0.0
    relevance_reason: str = ""
    is_pickup: bool = False
    research_status: Optional[ResearchStatus] = None
    deep_dive_report: Optional[str] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_comment: Optional[str] = None


class ArticleCollection(BaseModel):
    id: str
    user_id: str
    date: str
    articles: list[ScoredArticle] = []
    status: CollectionStatus
    created_at: datetime


class ScoreArticlesParams(BaseModel):
    user_id: str
    collection_id: str


class ResearchArticleParams(BaseModel):
    user_id: str
    collection_id: str
    article_url: str

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def generate_article_id(collection_id: str, url: str) -> str:
    """記事IDを生成する。{collection_id}_{url_hash_8桁}"""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"{collection_id}_{url_hash}"


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
    FAILED = "failed"


class SourceType(str, Enum):
    RSS = "rss"
    WEBSITE = "website"
    NEWSLETTER = "newsletter"
    API = "api"
    BOOKMARK = "bookmark"


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
    summary: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    og_image: Optional[str] = None
    published_at: Optional[datetime] = None


class CrossIndustryPerspective(BaseModel):
    industry: str
    expert_comment: str


class CrossIndustryFeedback(BaseModel):
    perspectives: list[CrossIndustryPerspective]


class ScoredArticle(Article):
    id: Optional[str] = None
    scoring_status: ScoringStatus = ScoringStatus.PENDING
    relevance_score: float = 0.0
    relevance_reason: str = ""
    is_pickup: bool = False
    research_status: Optional[ResearchStatus] = None
    deep_dive_report: Optional[str] = None
    cross_industry_feedback: Optional[CrossIndustryFeedback] = None
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


class BookmarkRequest(BaseModel):
    url: str
    api_key: str


class CollectRequest(BaseModel):
    user_id: str


class ResearchArticleParams(BaseModel):
    user_id: str
    collection_id: str
    article_url: str

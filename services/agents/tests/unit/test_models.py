import pytest
from datetime import datetime

from shared.models import (
    Article,
    ArticleCollection,
    CollectionStatus,
    ResearchArticleParams,
    ScoreArticlesParams,
    ScoredArticle,
    ScoringStatus,
    SourceConfig,
    SourceType,
    generate_article_id,
)


class Test_Article:
    def test_必須フィールドで作成できる(self):
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            source="Test Source",
            source_type=SourceType.RSS,
        )
        assert article.title == "Test Article"
        assert article.source_type == SourceType.RSS
        assert article.content is None
        assert article.published_at is None

    def test_全フィールド指定で作成できる(self):
        now = datetime.now()
        article = Article(
            title="Full Article",
            url="https://example.com",
            source="RSS Feed",
            source_type=SourceType.RSS,
            content="Article content",
            meta_description="記事の説明文",
            published_at=now,
        )
        assert article.content == "Article content"
        assert article.meta_description == "記事の説明文"
        assert article.published_at == now

    def test_meta_descriptionのデフォルトはNone(self):
        article = Article(
            title="Test",
            url="https://example.com",
            source="Test",
            source_type=SourceType.RSS,
        )
        assert article.meta_description is None


class Test_ScoredArticle:
    def test_デフォルト値が正しい(self):
        article = ScoredArticle(
            title="Test",
            url="https://example.com",
            source="Test",
            source_type=SourceType.RSS,
        )
        assert article.scoring_status == ScoringStatus.PENDING
        assert article.relevance_score == 0.0
        assert article.is_pickup is False
        assert article.user_rating is None

    def test_有効な評価値を設定できる(self):
        article = ScoredArticle(
            title="Test",
            url="https://example.com",
            source="Test",
            source_type=SourceType.RSS,
            user_rating=5,
        )
        assert article.user_rating == 5

    def test_範囲外の評価値でエラーになる(self):
        with pytest.raises(Exception):
            ScoredArticle(
                title="Test",
                url="https://example.com",
                source="Test",
                source_type=SourceType.RSS,
                user_rating=6,
            )


class Test_ArticleCollection:
    def test_コレクションを作成できる(self):
        collection = ArticleCollection(
            id="col_001",
            user_id="user_001",
            date="2025-01-15",
            status=CollectionStatus.COLLECTING,
            created_at=datetime.now(),
        )
        assert collection.id == "col_001"
        assert collection.articles == []
        assert collection.status == CollectionStatus.COLLECTING


class Test_SourceConfig:
    def test_RSSソースを作成できる(self):
        source = SourceConfig(
            id="src_001",
            type=SourceType.RSS,
            name="Hacker News",
            config={"url": "https://news.ycombinator.com/rss"},
        )
        assert source.type == SourceType.RSS
        assert source.enabled is True

    def test_無効化されたソースを作成できる(self):
        source = SourceConfig(
            id="src_002",
            type=SourceType.WEBSITE,
            name="Blog",
            enabled=False,
        )
        assert source.enabled is False


class Test_スキルパラメータ:
    def test_ScoreArticlesParamsを作成できる(self):
        params = ScoreArticlesParams(
            user_id="user_001",
            collection_id="col_001",
        )
        assert params.user_id == "user_001"

    def test_ResearchArticleParamsを作成できる(self):
        params = ResearchArticleParams(
            user_id="user_001",
            collection_id="col_001",
            article_url="https://example.com/article",
        )
        assert params.article_url == "https://example.com/article"


class Test_generate_article_id:
    def test_コレクションIDとURLからIDが生成される(self):
        article_id = generate_article_id("col_1", "https://example.com/article")
        assert article_id.startswith("col_1_")
        assert len(article_id) == len("col_1_") + 8

    def test_同じ入力で同じIDが生成される(self):
        id1 = generate_article_id("col_1", "https://example.com/1")
        id2 = generate_article_id("col_1", "https://example.com/1")
        assert id1 == id2

    def test_異なるURLで異なるIDが生成される(self):
        id1 = generate_article_id("col_1", "https://example.com/1")
        id2 = generate_article_id("col_1", "https://example.com/2")
        assert id1 != id2

    def test_異なるコレクションIDで異なるIDが生成される(self):
        id1 = generate_article_id("col_1", "https://example.com/1")
        id2 = generate_article_id("col_2", "https://example.com/1")
        assert id1 != id2


class Test_ScoredArticle_id:
    def test_デフォルトでNone(self):
        article = ScoredArticle(
            title="Test",
            url="https://example.com",
            source="Test",
            source_type=SourceType.RSS,
        )
        assert article.id is None

    def test_IDを設定できる(self):
        article = ScoredArticle(
            id="col_1_abc12345",
            title="Test",
            url="https://example.com",
            source="Test",
            source_type=SourceType.RSS,
        )
        assert article.id == "col_1_abc12345"


class Test_Enum値:
    def test_CollectionStatusの値が正しい(self):
        assert CollectionStatus.COLLECTING == "collecting"
        assert CollectionStatus.COMPLETED == "completed"

    def test_SourceTypeの値が正しい(self):
        assert SourceType.RSS == "rss"
        assert SourceType.WEBSITE == "website"

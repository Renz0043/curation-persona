# API設計 (API Design)

> Curation PersonaのAPI仕様を定義します。

---

## 1. 内部API（Cloud Run間）

### Hunter Agent

```
POST /api/v1/hunt
Content-Type: application/json

Request:
{
  "userId": "user_123",
  "rssSources": ["https://example.com/rss"]
}

Response:
{
  "status": "success",
  "articlesFound": 50,
  "articlesFiltered": 8,
  "reportId": "report_456"
}
```

### Librarian Agent

```
POST /api/v1/check-relevance
Content-Type: application/json

Request:
{
  "userId": "user_123",
  "article": {
    "title": "...",
    "content": "..."
  }
}

Response:
{
  "isRelevant": true,
  "score": 0.85,
  "reason": "過去のメモ「AIエージェント設計パターン」と関連",
  "relatedPages": ["notion_page_id_1", "notion_page_id_2"]
}
```

---

## 2. 外部API（Dashboard向け）

### レポート取得

```
GET /api/reports?date=2025-01-15
Authorization: Bearer {firebase_id_token}

Response:
{
  "report": {
    "id": "report_456",
    "date": "2025-01-15",
    "status": "completed",
    "articles": [...]
  }
}
```

### フィードバック送信

```
POST /api/reports/{reportId}/feedback
Authorization: Bearer {firebase_id_token}

Request:
{
  "articleIndex": 0,
  "feedback": "positive"
}

Response:
{
  "status": "success"
}
```

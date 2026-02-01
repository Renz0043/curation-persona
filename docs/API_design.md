# API設計 (API Design)

> Curation PersonaのAPI仕様を定義します。

---

## 1. 内部API（Cloud Run間）

### Collector Agent（手動トリガー用）

```
POST /api/v1/collect
Content-Type: application/json

Request:
{
  "userId": "user_123"
}

Response:
{
  "status": "success",
  "articlesTotal": 15,
  "collectionId": "collection_user_123_20250115"
}
```

> 通常はPub/Sub（batch-trigger）経由でトリガーされる。
> 手動トリガー後、スコアリング・詳細調査は非同期で実行される。

### Librarian Agent

> Pub/Sub（score-request）経由でトリガーされる。外部APIなし。

### Researcher Agent

> Pub/Sub（research-request）経由でトリガーされる。外部APIなし。

---

## 2. 外部API（Dashboard向け）

### コレクション取得

```
GET /api/collections?date=2025-01-15
Authorization: Bearer {firebase_id_token}

Response:
{
  "collection": {
    "id": "collection_user_123_20250115",
    "date": "2025-01-15",
    "status": "completed",
    "articles": [...]
  }
}
```

### フィードバック送信

```
POST /api/collections/{collectionId}/feedback
Authorization: Bearer {firebase_id_token}

Request:
{
  "articleUrl": "https://example.com/article",
  "feedback": "positive"
}

Response:
{
  "status": "success"
}
```

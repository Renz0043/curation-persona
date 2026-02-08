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

> 通常はCloud Scheduler経由でHTTPトリガーされる。
> 手動トリガー後、スコアリング・詳細調査はA2A経由で連携実行される。

### Librarian Agent

> A2A（score_articles スキル）経由でCollectorからトリガーされる。外部APIなし。

### Researcher Agent

> A2A（research_article スキル）経由でDashboard APIからトリガーされる（ユーザー手動リクエスト）。

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

### フィードバック送信（5段階評価 + コメント）

```
POST /api/collections/{collectionId}/feedback
Authorization: Bearer {firebase_id_token}

Request:
{
  "articleUrl": "https://example.com/article",
  "rating": 5,
  "comment": "AIエージェント設計に関連していて非常に参考になった"
}

Response:
{
  "status": "success"
}
```

> `rating` は 1-5 の整数（必須）。`comment` は任意。

### 深掘りリクエスト

```
POST /api/collections/{collectionId}/research
Authorization: Bearer {firebase_id_token}

Request:
{
  "articleUrl": "https://example.com/article"
}

Response:
{
  "status": "accepted",
  "message": "深掘りレポートを生成中です"
}
```

> Dashboard APIがResearcher AgentにA2A経由で `research_article` スキルを呼び出す。
> レポート生成は非同期で行われ、完了時にFirestoreのarticle内の `deepDiveReport` が更新される。

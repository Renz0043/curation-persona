# API設計 (API Design)

> Curation Persona のフロントエンド・バックエンド間 API 仕様を定義します。

---

## 1. アーキテクチャ方針

| 操作 | 方式 | 理由 |
|------|------|------|
| **読み取り** | Firestore 直接読み取り（Firebase JS SDK） | リアルタイム更新（`onSnapshot`）、API サーバー不要 |
| **書き込み** | バックエンド REST API 経由 | バリデーション・ビジネスロジックをサーバー側で制御 |
| **ストリーミング** | Next.js API Route → Researcher Agent（SSE） | A2A プロトコルの SSE を中継 |

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend                                           │
│                                                             │
│  [読み取り]  Firebase JS SDK → Firestore (直接)              │
│  [書き込み]  fetch() → Next.js API Route → Backend Agent    │
│  [SSE]      fetch() → Next.js API Route → Researcher Agent  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 認証

### 2.1 フロントエンド認証: Firebase Auth（Google OAuth）

```
ブラウザ → Firebase Auth（Google Sign-In） → ID Token 取得
```

- Firebase JS SDK の `signInWithPopup(GoogleAuthProvider)` で認証
- 取得した ID Token を REST API リクエストの `Authorization` ヘッダーに付与

### 2.2 バックエンド認証: Firebase Admin SDK による ID Token 検証

```python
# Next.js API Route または Backend Agent での検証
from firebase_admin import auth
decoded = auth.verify_id_token(id_token)
user_id = decoded["uid"]
```

REST API はすべて `Authorization: Bearer {firebase_id_token}` を必須とする。

### 2.3 Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false;  // バックエンドのみ
    }
    match /collections/{collectionId} {
      allow read: if request.auth != null
                  && resource.data.user_id == request.auth.uid;
      allow write: if false;  // バックエンドのみ
    }
    match /articles/{articleId} {
      allow read: if request.auth != null
                  && resource.data.user_id == request.auth.uid;
      allow write: if false;  // バックエンドのみ
    }
  }
}
```

### 2.4 ブックマーク API 認証: API Key

Safari ショートカット等の外部クライアント向け。Firebase Auth が使えない環境用。

```
POST /api/bookmarks
{ "url": "...", "api_key": "..." }
```

`users/{userId}.api_key` フィールドで検証。

---

## 3. Firestore データ構造（実装済み）

> Design_doc.md のスキーマから変更あり。記事はトップレベル `articles` コレクションに分離済み。

### 3.1 コレクション構成

```
firestore/
├── users/{userId}
│   ├── user_id: string
│   ├── sources: SourceConfig[]
│   ├── api_key?: string                     // ブックマークAPI用
│   ├── interestProfile?: string             // LLM生成の興味プロファイル
│   ├── interestProfileUpdatedAt?: timestamp
│   └── createdAt: timestamp
│
├── collections/{collectionId}
│   ├── id: string
│   ├── user_id: string
│   ├── date: string                         // "2025-01-15"
│   ├── status: CollectionStatus             // collecting|scoring|researching|completed|failed
│   └── created_at: timestamp
│   // ※ articles 配列は含まない（分離済み）
│
└── articles/{articleId}                      // articleId = "{collectionId}_{urlHash8桁}"
    ├── id: string
    ├── collection_id: string                // 所属コレクション
    ├── user_id: string                      // Security Rules 用
    ├── title: string
    ├── url: string
    ├── source: string
    ├── source_type: SourceType              // rss|website|newsletter|api|bookmark
    ├── content?: string
    ├── meta_description?: string
    ├── published_at?: timestamp
    │
    │  // スコアリング
    ├── scoring_status: ScoringStatus        // pending|scoring|scored
    ├── relevance_score: number              // 0.0 - 1.0
    ├── relevance_reason: string
    ├── is_pickup: boolean
    ├── title_embedding?: Vector             // Gemini Embedding (768次元)
    │
    │  // 深掘りレポート
    ├── research_status?: ResearchStatus     // pending|researching|completed|failed
    ├── deep_dive_report?: string            // Markdown レポート
    ├── cross_industry_feedback?: {          // is_pickup=true のみ
    │     abstracted_challenge: string,
    │     perspectives: [
    │       { industry: string, expert_comment: string }
    │     ]
    │   }
    │
    │  // ユーザーフィードバック
    ├── user_rating?: number                 // 1-5
    └── user_comment?: string
```

### 3.2 ブックマークコレクション

ブックマーク記事は専用コレクション `bm_{userId}` に格納される。

```
collections/bm_{userId}   — date: "", status: completed（固定）
articles/bm_{userId}_{hash} — source_type: bookmark, is_pickup: true
```

---

## 4. フロントエンド読み取り API（Firestore 直接）

Firebase JS SDK を使い、Firestore から直接読み取る。

### 4.1 今日のコレクション取得

```typescript
// collections から user_id + date でクエリ
const q = query(
  collection(db, "collections"),
  where("user_id", "==", userId),
  where("date", "==", "2025-01-15"),
  orderBy("created_at", "desc"),
  limit(1)
);
const snapshot = await getDocs(q);
```

### 4.2 コレクション内の記事一覧

```typescript
// articles から collection_id でクエリ
const q = query(
  collection(db, "articles"),
  where("collection_id", "==", collectionId)
);
const snapshot = await getDocs(q);
```

**ピックアップ記事のみ取得:**

```typescript
const q = query(
  collection(db, "articles"),
  where("collection_id", "==", collectionId),
  where("is_pickup", "==", true)
);
```

### 4.3 記事詳細（深掘りレポート含む）

```typescript
// articleId = "{collectionId}_{urlHash8桁}"
const docRef = doc(db, "articles", articleId);
const snapshot = await getDoc(docRef);
// snapshot.data().deep_dive_report → Markdown レポート
// snapshot.data().cross_industry_feedback → 異業種フィードバック
```

### 4.4 リアルタイム更新（onSnapshot）

コレクションのステータス進捗やレポート生成完了をリアルタイムで検知する。

```typescript
// コレクションステータス監視
const unsub = onSnapshot(
  doc(db, "collections", collectionId),
  (snapshot) => {
    const status = snapshot.data()?.status;
    // collecting → scoring → completed の進捗表示
  }
);

// 記事の research_status 監視
const unsub = onSnapshot(
  doc(db, "articles", articleId),
  (snapshot) => {
    const data = snapshot.data();
    if (data?.research_status === "completed") {
      // レポート完成 → deep_dive_report を表示
    }
  }
);
```

### 4.5 過去コレクション一覧（アーカイブ）

```typescript
const q = query(
  collection(db, "collections"),
  where("user_id", "==", userId),
  orderBy("created_at", "desc"),
  limit(30)
);
```

---

## 5. バックエンド REST API（書き込み操作）

Next.js API Route で受け、バックエンドエージェントまたは Firestore Admin SDK で処理する。

すべてのエンドポイントで `Authorization: Bearer {firebase_id_token}` を必須とする。

### 5.1 フィードバック送信

```
POST /api/collections/{collectionId}/feedback
Authorization: Bearer {firebase_id_token}
Content-Type: application/json

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

- `rating`: 1-5 の整数（必須）
- `comment`: 任意
- **処理**: Firestore Admin SDK で `articles/{articleId}` の `user_rating`, `user_comment` を更新

### 5.2 深掘りリクエスト

```
POST /api/collections/{collectionId}/research
Authorization: Bearer {firebase_id_token}
Content-Type: application/json

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

- Researcher Agent に A2A 経由で `research_article` スキルを呼び出し
- レポート生成は非同期。完了時に `articles/{articleId}.deep_dive_report` が更新される
- フロントエンドは `onSnapshot` で完了を検知

### 5.3 深掘りレポート SSE ストリーミング

```
POST /api/collections/{collectionId}/research/stream
Authorization: Bearer {firebase_id_token}
Content-Type: application/json

Request:
{
  "articleUrl": "https://example.com/article"
}

Response: Content-Type: text/event-stream
```

Next.js API Route が Researcher Agent の A2A `message/stream` を中継し、SSE でブラウザに配信する。

> SSE プロトコルの詳細は Notion「[SSE ストリーミングプロトコル](https://www.notion.so/305fb62776b3800c836fd66843651ab9)」を参照。

**イベント種別:**

| `result.kind` | 説明 |
|----------------|------|
| `status-update` | タスク状態遷移（`working` → `completed` / `failed`） |
| `artifact-update` | レポート本文のテキストチャンク（`append: true` で結合） |

**完了判定**: `status-update` の `final: true` でストリーム終了。

### 5.4 ブックマーク登録（API Key 認証）

```
POST /api/bookmarks
Content-Type: application/json

Request:
{
  "url": "https://example.com/article",
  "api_key": "user_api_key_here"
}

Response:
{
  "status": "accepted",
  "url": "https://example.com/article"
}
```

- Firebase Auth ではなく API Key で認証（Safari ショートカット等の外部クライアント向け）
- バックグラウンドで Web スクレイピング + 深掘りレポート生成を実行
- **実装済み**: `Researcher Agent POST /api/bookmarks`

---

## 6. 内部 API（Agent 間通信）

### 6.1 Collector Agent（手動トリガー用）

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

> 通常は Cloud Scheduler 経由で HTTP トリガーされる。

### 6.2 Librarian Agent

> A2A（`score_articles` スキル）経由で Collector からトリガーされる。外部 API なし。

### 6.3 Researcher Agent

> A2A（`research_article` スキル）経由でトリガー。REST API は 5.2〜5.4 を参照。

---

## 7. 実装ステータス

| API | ステータス | 実装場所 |
|-----|----------|---------|
| Firestore 直接読み取り | **フロントエンド未実装**（バックエンドのデータは準備済み） | — |
| フィードバック送信 | **バックエンドロジック実装済み** / API Route 未実装 | `firestore_client.update_article_feedback()` |
| 深掘りリクエスト（非同期） | **バックエンド実装済み** / API Route 未実装 | `researcher/service.py` |
| 深掘り SSE ストリーミング | **バックエンド実装済み** / API Route 未実装 | `researcher/service.py` + A2A |
| ブックマーク登録 | **実装済み** | `researcher/main.py POST /api/bookmarks` |
| Collector 手動トリガー | **A2A スキル実装済み** / HTTP エンドポイント未実装 | `collector/service.py` |
| Firebase Auth 認証 | **未実装** | — |
| Firestore Security Rules | **未設定** | — |

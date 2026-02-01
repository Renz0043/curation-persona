# Curation Persona - Design Document

> **対象**: [Google Cloud Japan AI Hackathon Vol.4](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=rule)
>
> **スコープ**: ハッカソンMVP（本番運用は対象外）

---

## 1. 設計概要 (Design Overview)

### 1.1 設計方針

| 方針 | 説明 |
|------|------|
| **シンプルさ優先** | ハッカソン期間内に動くものを作る。過度な抽象化は避ける |
| **コスト意識** | LLM呼び出しを最小限に。バッチ処理で1日1回に集約 |
| **疎結合** | エージェント間はPub/Sub経由で非同期連携。個別にテスト可能 |

### 1.2 設計判断の記録 (ADR: Architecture Decision Records)

#### ADR-001: バッチ処理 vs リアルタイム処理

- **決定**: 1日1回のバッチ処理を採用
- **理由**:
  - リアルタイム処理はLLMコストが膨大になる
  - ニュースは即時性より正確性が重要
  - 個人開発の持続可能性を重視
- **トレードオフ**: 速報性は犠牲になるが、ハッカソン用途では問題なし

#### ADR-002: エージェント間通信方式

- **決定**: Cloud Pub/Sub による非同期メッセージング
- **却下した案**:
  - 直接HTTP呼び出し → 障害時の再試行が複雑
  - Cloud Tasks → Pub/Subで十分
- **理由**: 疎結合性、自動リトライ、スケーラビリティ

#### ADR-003: Vector Search の選択

- **決定**: Vertex AI Vector Search
- **却下した案**:
  - Pinecone → 外部サービス依存を減らしたい
  - PostgreSQL pgvector → セットアップが煩雑
- **理由**: GCPエコシステム内で完結

---

## 2. システムアーキテクチャ (System Architecture)

### 2.1 全体構成図

```mermaid
graph TD
    subgraph "Triggers"
        Scheduler[Cloud Scheduler<br/>毎朝 06:00 JST]
        LineBot[LINE Bot<br/>手動トリガー]
    end

    subgraph "Message Queue"
        PubSub[Cloud Pub/Sub]
    end

    subgraph "Agent Layer (Cloud Run)"
        Hunter[Hunter Agent<br/>Gemini 2.5 Flash]
        Librarian[Librarian Agent<br/>Vector Search]
        Researcher[Researcher Agent<br/>Gemini 2.5 Pro]
    end

    subgraph "Data Layer"
        Firestore[(Firestore<br/>Reports / Users)]
        VectorDB[(Vector Search<br/>Notion Embeddings)]
    end

    subgraph "External"
        RSS[RSS Feeds]
        Notion[Notion API]
    end

    subgraph "Frontend"
        Dashboard[Next.js Dashboard<br/>Firebase Hosting]
    end

    Scheduler --> PubSub
    LineBot -.-> PubSub

    PubSub --> Hunter
    Hunter --> RSS
    Hunter --> Librarian
    Librarian --> VectorDB
    Librarian --> Notion
    Hunter --> Researcher
    Researcher --> Firestore

    Dashboard --> Firestore
```

### 2.2 コンポーネント責務

| コンポーネント | 責務 | 技術 |
|----------------|------|------|
| **Hunter Agent** | RSS巡回、初期フィルタリング、エージェント連携の起点 | Cloud Run, Python, Gemini Flash |
| **Librarian Agent** | ユーザーコンテキストとの関連性判定 | Cloud Run, Python, Vector Search |
| **Researcher Agent** | 詳細レポート生成、Firestore保存 | Cloud Run, Python, Gemini Pro |
| **Dashboard** | レポート表示、ユーザー認証、フィードバック収集 | Next.js, Firebase Auth |

---

## 3. データモデル (Data Models)

### 3.1 Firestore スキーマ

```
firestore/
├── users/{userId}
│   ├── notionAccessToken: string (encrypted)
│   ├── notionWorkspaceId: string
│   ├── rssSources: string[]
│   ├── preferences: {
│   │     dailyReportTime: string  // "06:00"
│   │   }
│   └── createdAt: timestamp
│
├── reports/{reportId}
│   ├── userId: string
│   ├── date: string              // "2025-01-15"
│   ├── articles: [
│   │     {
│   │       title: string
│   │       url: string
│   │       source: string
│   │       summary: string
│   │       relevanceScore: number  // 0.0 - 1.0
│   │       relevanceReason: string
│   │       relatedNotionPages: string[]
│   │       deepDiveReport: string
│   │       userFeedback: "positive" | "neutral" | "negative" | null
│   │     }
│   │   ]
│   ├── status: "processing" | "completed" | "failed"
│   └── createdAt: timestamp
│
└── notionEmbeddings/{embeddingId}
    ├── userId: string
    ├── notionPageId: string
    ├── notionPageTitle: string
    ├── content: string           // 元テキスト（デバッグ用）
    ├── embeddingVector: number[] // Vector Search側で管理
    └── updatedAt: timestamp
```

### 3.2 Pub/Sub メッセージ形式

#### Topic: `batch-trigger`
```json
{
  "type": "daily_batch",
  "userId": "user_123",
  "triggeredAt": "2025-01-15T06:00:00+09:00"
}
```

#### Topic: `research-request`
```json
{
  "userId": "user_123",
  "reportId": "report_456",
  "article": {
    "title": "...",
    "url": "...",
    "relevanceScore": 0.85,
    "relevanceReason": "..."
  }
}
```

---

## 4. API設計 (API Design)

### 4.1 内部API（Cloud Run間）

#### Hunter Agent

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

#### Librarian Agent

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

### 4.2 外部API（Dashboard向け）

#### レポート取得

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

#### フィードバック送信

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

---

## 5. 処理フロー (Processing Flow)

### 5.1 日次バッチ処理シーケンス

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as Cloud Scheduler
    participant PubSub as Pub/Sub
    participant Hunter as Hunter Agent
    participant Librarian as Librarian Agent
    participant Vector as Vector Search
    participant Researcher as Researcher Agent
    participant DB as Firestore

    Note over Scheduler: 毎朝 06:00 JST
    Scheduler->>PubSub: batch-trigger メッセージ
    PubSub->>Hunter: トリガー受信

    Hunter->>Hunter: RSS巡回（並列）
    Hunter->>Hunter: Gemini Flash で初期スクリーニング
    Note right of Hunter: 50件 → 20件に絞り込み

    loop 各候補記事
        Hunter->>Librarian: 関連性チェック依頼
        Librarian->>Vector: 類似ベクトル検索
        Vector-->>Librarian: 関連Notionページ
        Librarian-->>Hunter: 判定結果 (Go/No-Go)
    end
    Note right of Hunter: 20件 → 8件に絞り込み

    Hunter->>DB: レポート作成（status: processing）

    loop 選別された記事
        Hunter->>PubSub: research-request
        PubSub->>Researcher: 詳細調査依頼
        Researcher->>Researcher: Gemini Pro で深掘り
        Researcher->>DB: 記事レポート追加
    end

    Researcher->>DB: status: completed
```

---

## 6. エラーハンドリング (Error Handling)

### 6.1 方針

| エラー種別 | 対応 |
|------------|------|
| RSS取得失敗 | スキップして次のソースへ。ログ記録のみ |
| LLM API エラー | 最大3回リトライ（exponential backoff） |
| Vector Search エラー | 関連性スコア0として処理継続 |
| Notion API エラー | キャッシュがあれば使用、なければスキップ |

### 6.2 リトライ設定

```python
# エージェント共通設定
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay_sec": 1,
    "max_delay_sec": 30,
    "exponential_base": 2
}
```

---

## 7. セキュリティ設計 (Security)

### 7.1 認証・認可

```
┌─────────────────┐     ┌─────────────────┐
│   Dashboard     │────▶│  Firebase Auth  │
│   (Frontend)    │     │  (Google OAuth) │
└─────────────────┘     └─────────────────┘
         │
         │ ID Token
         ▼
┌─────────────────┐
│   Cloud Run     │  ← Firebase Admin SDK で検証
│   (Backend)     │
└─────────────────┘
```

### 7.2 Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // ユーザーは自分のデータのみアクセス可能
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    match /reports/{reportId} {
      allow read: if request.auth != null &&
                     resource.data.userId == request.auth.uid;
      allow write: if false; // バックエンドのみ書き込み可
    }
  }
}
```

---

## 8. 環境構成 (Environments)

### 8.1 ハッカソン向け（単一環境）

| 項目 | 値 |
|------|-----|
| GCPプロジェクト | `curation-persona` |
| リージョン | `asia-northeast1` (東京) |
| Cloud Run インスタンス | 最小0、最大3 |
| Firestore モード | Native mode |

### 8.2 環境変数

```bash
# Cloud Run 共通
GOOGLE_CLOUD_PROJECT=curation-persona
FIRESTORE_DATABASE=(default)
PUBSUB_TOPIC_BATCH=batch-trigger
PUBSUB_TOPIC_RESEARCH=research-request

# エージェント固有
GEMINI_FLASH_MODEL=gemini-2.5-flash
GEMINI_PRO_MODEL=gemini-2.5-pro
VECTOR_SEARCH_INDEX_ENDPOINT=projects/.../indexes/...

# 外部連携
NOTION_CLIENT_ID=xxx
NOTION_CLIENT_SECRET=xxx
```

---

## 9. モニタリング（ハッカソン向け簡易版）

### 9.1 確認すべきメトリクス

| メトリクス | 確認場所 | アラート閾値 |
|------------|----------|--------------|
| Cloud Run エラー率 | Cloud Console | 手動確認 |
| Pub/Sub 未処理メッセージ | Cloud Console | 手動確認 |
| LLM API コスト | GCP Billing | $10/日 超えたら停止 |

### 9.2 ログ出力

```python
import logging
from google.cloud import logging as cloud_logging

# Cloud Logging に構造化ログを出力
logger = logging.getLogger(__name__)

logger.info("Article processed", extra={
    "userId": user_id,
    "articleUrl": url,
    "relevanceScore": score
})
```

---

## 10. 今後の拡張（本番化時の検討事項）

> ハッカソン後に本番運用する場合の検討事項

- [ ] マルチテナント対応（ユーザー増加時のスケーリング）
- [ ] Notion OAuth の本番申請
- [ ] セキュリティ監査（Notion トークンの暗号化強化）
- [ ] CI/CD パイプライン構築
- [ ] 負荷テスト実施
- [ ] SLA定義とモニタリング強化

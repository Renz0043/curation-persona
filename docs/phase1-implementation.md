# Phase 1: MVP Infrastructure 実装結果

> **実施日**: 2026-02-11
> **ステータス**: 完了（Step 1.7 GCP/Firebase セットアップを除く）

---

## 実装サマリ

| Step | 内容 | 状態 |
|------|------|------|
| 1.1 | ディレクトリ構造 | 完了 |
| 1.2 | Python プロジェクト初期化 | 完了 |
| 1.3 | shared/ モジュール作成 | 完了 |
| 1.4 | Collector Agent スケルトン | 完了 |
| 1.5 | Librarian/Researcher スケルトン | 完了 |
| 1.6 | Next.js 初期化 | 完了 |
| 1.7 | GCP/Firebase セットアップ | 未実施（手動作業） |
| 1.8 | 開発環境整備 (Makefile) | 完了 |
| 1.9 | テスト基盤 + 疎通テスト | 完了（20テスト全パス） |

---

## ディレクトリ構成

```
curation-persona/
├── docs/                          # 設計書（既存）
├── apps/web/                      # Next.js (Tailwind v4 + daisyUI v5)
├── services/agents/
│   ├── pyproject.toml             # Python 依存関係定義
│   ├── .env.example               # 環境変数テンプレート
│   ├── shared/                    # 共通モジュール
│   │   ├── config.py              # pydantic-settings による環境変数管理
│   │   ├── models.py              # Pydantic データモデル + Enum
│   │   ├── retry.py               # 指数バックオフリトライ
│   │   ├── firestore_client.py    # Firestore CRUD（スタブモード付き）
│   │   ├── a2a_client.py          # A2A 送信クライアント
│   │   ├── gemini_client.py       # Gemini API（Phase 1: スタブ）
│   │   └── fetchers/              # 記事取得モジュール
│   │       ├── base.py            # BaseFetcher ABC
│   │       ├── registry.py        # FetcherRegistry
│   │       ├── rss_fetcher.py     # RSS 取得（完全実装）
│   │       ├── website_fetcher.py # Web 監視（スタブ）
│   │       └── newsletter_fetcher.py  # メルマガ（スタブ）
│   ├── collector/                 # Collector Agent (port 8001)
│   │   ├── main.py                # A2A Server + /health
│   │   ├── agent_executor.py      # AgentExecutor 実装
│   │   └── service.py             # ビジネスロジック（スタブ）
│   ├── librarian/                 # Librarian Agent (port 8002)
│   │   ├── main.py                # A2A Server + /health
│   │   ├── agent_executor.py      # AgentExecutor 実装
│   │   ├── service.py             # ビジネスロジック（スタブ）
│   │   └── scorer.py              # ArticleScorer（シグネチャ）
│   ├── researcher/                # Researcher Agent (port 8003)
│   │   ├── main.py                # A2A Server + /health
│   │   ├── agent_executor.py      # AgentExecutor 実装
│   │   ├── service.py             # ビジネスロジック（スタブ）
│   │   └── report_generator.py    # ReportGenerator（シグネチャ）
│   └── tests/
│       ├── conftest.py            # mock fixtures
│       └── unit/
│           ├── test_models.py     # Pydantic バリデーション (14テスト)
│           ├── test_config.py     # 設定読み込み (2テスト)
│           └── test_agents.py     # Agent Card + Health (6テスト)
├── infrastructure/                # GCP 設定（Phase 3 以降）
├── Makefile                       # 開発コマンド集
└── .gitignore
```

---

## 技術スタック（インストール済み）

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| a2a-sdk | 0.3.22 | A2A プロトコル（エージェント間通信） |
| fastapi | 0.128.7 | Web フレームワーク |
| uvicorn | 0.40.0 | ASGI サーバー |
| pydantic | 2.12.5 | データバリデーション |
| pydantic-settings | 2.12.0 | 環境変数管理 |
| google-cloud-firestore | 2.23.0 | Firestore SDK |
| google-genai | 1.62.0 | Gemini API SDK |
| feedparser | 6.0.12 | RSS パース |
| httpx | 0.28.1 | HTTP クライアント |
| Next.js | 15 | フロントエンド |
| Tailwind CSS | 4 | CSS フレームワーク |
| daisyUI | 5.5.18 | UI コンポーネント |

---

## 設計書との差異（a2a-sdk v0.3.22 実 API 検証結果）

実装時に a2a-sdk の実 API を検証し、設計書のコード例から以下を修正した。

| 設計書の記述 | 実際の API | 対応 |
|-------------|-----------|------|
| `default_input_modes` (snake_case) | `defaultInputModes` (camelCase) | コードで修正済み |
| `A2AFastAPIApplication(handler=...)` | `A2AFastAPIApplication(http_handler=...)` | コードで修正済み |
| `SendMessageRequest(params=...)` | `SendMessageRequest(id=..., params=...)` — `id` が必須 | コードで修正済み |
| `context.message` | `context.request.message` — RequestContext 経由 | コードで修正済み |

> **Note**: 設計書（`docs/backend/implementation.md`）自体は未修正。Phase 2 実装時に必要に応じて更新する。

---

## 動作確認済みの項目

### 3エージェントの起動・疎通

```bash
# 起動
make run-collector   # port 8001
make run-librarian   # port 8002
make run-researcher  # port 8003

# Health Check → 全て {"status": "healthy"}
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Agent Card → 全て正常なJSON返却
curl http://localhost:8001/.well-known/agent-card.json
curl http://localhost:8002/.well-known/agent-card.json
curl http://localhost:8003/.well-known/agent-card.json
```

### テスト

```bash
make test  # 20 passed in 0.56s
```

### Next.js ビルド

```bash
cd apps/web && npm run build  # 成功
```

---

## Phase 1 で未実施の項目

| 項目 | 理由 | 対応タイミング |
|------|------|--------------|
| GCP/Firebase セットアップ (Step 1.7) | 手動作業（Firebase コンソール操作が必要） | Phase 1 の残タスクとして別途実施 |
| A2A `POST /rpc` 疎通テスト | エージェント間の実通信はビジネスロジック実装後に意味がある | Phase 2 |
| Firestore Emulator 疎通テスト | Emulator セットアップ（Java 依存）が未完了 | GCP セットアップと同時に実施 |
| 設計書の API 差異反映 | コード側で対応済みのため優先度低 | Phase 2 開始時 |

---

## Phase 2 に向けて

Phase 1 で構築したスケルトンに対し、以下の順でビジネスロジックを実装していく。

1. **Firestore 接続** — Emulator or 実環境への CRUD 疎通
2. **Collector ビジネスロジック** — RSS 取得 → Firestore 保存 → A2A 送信
3. **Librarian ビジネスロジック** — スコアリング（Gemini Flash）
4. **Researcher ビジネスロジック** — レポート生成（Gemini Pro）
5. **フロントエンド** — Dashboard UI の実装

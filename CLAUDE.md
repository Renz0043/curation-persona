# 指示
- 常に日本語で回答します。
- ユーザーと作業する中で/docs配下を更新した方が良い場合は、どの部分をどう修正するかユーザーに確認し、許可を持って更新します。
- pytestのテスト名は日本語で命名します。

# プロジェクト概要
ユーザーの評価・フィードバックから興味関心を学習し、ニュースを自律選別するバッチ型AIリサーチプラットフォーム。

## 構成
- `services/agents/` — Python バックエンド（3つのA2Aエージェント + shared共通モジュール + MCPサーバー）
- `apps/web/` — Next.js フロントエンド（Firebase Auth/Firestore 初期設定済み）
- `docs/` — 設計ドキュメント（PRD, Design_doc, ADR, API_design, backend/implementation）

## 技術スタック
- **バックエンド**: Python 3.12 / FastAPI / a2a-sdk / Gemini Flash・Pro・Embedding / Firestore
- **フロントエンド**: Next.js 16 / Tailwind CSS 4 / daisyUI 5 / Firebase JS SDK
- **インフラ**: Cloud Run / Firebase App Hosting / Cloud Scheduler
- **MCP**: FastMCP (stdio) — Claude Desktop 連携

## 主要機能（バックエンド実装済み）
- RSS巡回・記事収集（Collector Agent）
- LLMスコアリング・ピックアップ選定（Librarian Agent）
- 深掘りレポート生成 + SSEストリーミング（Researcher Agent）
- 異業種フィードバック（エコーチェンバー防止）
- Gemini Embedding + ベクトル類似記事検索
- Safari ブックマーク経由の自動深掘り
- MCPサーバー（6ツール公開）

## Firestore データ構造
- `users/{userId}` — ユーザー設定・興味プロファイル
- `collections/{collectionId}` — 日次コレクションメタデータ（articles配列は含まない）
- `articles/{articleId}` — 記事本体（トップレベルコレクション、`{collectionId}_{urlHash8桁}`）

## よく使うコマンド
```bash
# テスト
cd services/agents && .venv/bin/python -m pytest tests/ -v

# E2E検証（要: Emulator + 全エージェント起動）
make run-emulator        # ターミナル1
make run-collector-emu   # ターミナル2
make run-librarian-emu   # ターミナル3
make run-researcher-emu  # ターミナル4
make e2e                 # ターミナル5
```
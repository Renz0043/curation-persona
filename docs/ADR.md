# Architecture Decision Records (ADR)

> 本ドキュメントは、Curation Personaプロジェクトにおける設計判断を記録します。

---

## ADR-001: バッチ処理 vs リアルタイム処理

- **決定**: 1日1回のバッチ処理を採用
- **理由**:
  - リアルタイム処理はLLMコストが膨大になる
  - ニュースは即時性より正確性が重要
  - 個人開発の持続可能性を重視
- **トレードオフ**: 速報性は犠牲になるが、ハッカソン用途では問題なし

---

## ADR-002: エージェント間通信方式

- **決定**: Cloud Pub/Sub による非同期メッセージング
- **却下した案**:
  - 直接HTTP呼び出し → 障害時の再試行が複雑
  - Cloud Tasks → Pub/Subで十分
- **理由**: 疎結合性、自動リトライ、スケーラビリティ

---

## ADR-003: Vector Search の選択

- **決定**: Vertex AI Vector Search
- **却下した案**:
  - Pinecone → 外部サービス依存を減らしたい
  - PostgreSQL pgvector → セットアップが煩雑
- **理由**: GCPエコシステム内で完結

---

## ADR-004: Notion連携方式

- **決定**: Internal Integration + 環境変数（NOTION_TOKEN）
- **却下した案**:
  - OAuth → 実装が複雑、ハッカソン向けには過剰
  - リモートMCP（Notion公式） → OAuth必須のため自動実行（Cloud Run）に不向き
  - OSS MCPサーバーをホスト → メンテナンス終了、リスクあり
- **理由**: シンプルで確実。ユーザーが自分のトークンを設定する運用で複数ユーザー対応も可能
- **開発時の活用**: Claude Code環境ではNotion MCP（OAuth認証済み）を使ってデータ構造確認・プロトタイピングに活用

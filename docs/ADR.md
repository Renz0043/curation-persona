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

> **⚠️ 廃止**: ADR-010 により A2Aプロトコルに変更

- **決定**: ~~Cloud Pub/Sub による非同期メッセージング~~
- **却下した案**:
  - 直接HTTP呼び出し → 障害時の再試行が複雑
  - Cloud Tasks → Pub/Subで十分
- **理由**: 疎結合性、自動リトライ、スケーラビリティ

---

## ADR-003: Vector Search の選択

> **⚠️ 保留**: MVPではLLMベーススコアリング（ADR-011）に変更。将来的にVector Search再導入の可能性あり。

- **決定**: ~~Vertex AI Vector Search~~
- **却下した案**:
  - Pinecone → 外部サービス依存を減らしたい
  - PostgreSQL pgvector → セットアップが煩雑
- **理由**: GCPエコシステム内で完結
- **保留理由**: MVPではユーザー評価ベースのLLMスコアリング（ADR-011）で代替。評価データが十分に蓄積された段階でVector Searchによるハイブリッドスコアリングを検討

---

## ADR-004: Notion連携方式

> **⚠️ 廃止**: ADR-011 によりユーザー評価ベースのスコアリングに変更

- **決定**: ~~Internal Integration + 環境変数（NOTION_TOKEN）~~
- **却下した案**:
  - OAuth → 実装が複雑、ハッカソン向けには過剰
  - リモートMCP（Notion公式） → OAuth必須のため自動実行（Cloud Run）に不向き
  - OSS MCPサーバーをホスト → メンテナンス終了、リスクあり
- **廃止理由**: Notion API連携 + Vector Search の実装コストがハッカソンMVPには重すぎるため。ユーザー評価ベースのスコアリング（ADR-011）で代替

---

## ADR-005: エージェント命名規則（Collector Agent）

- **決定**: Hunter Agent → Collector Agent に命名変更
- **理由**:
  - 単なるRSS巡回（狩り）だけでなく、オーケストレーター的役割を担う
  - Librarian/Researcher への連携指示、フロー制御が主要責務
  - 「収集して配る」という実態に即した命名
- **影響範囲**: ドキュメント、ディレクトリ名、クラス名すべて統一

---

## ADR-006: エージェント間データ受け渡し方式

> **⚠️ 更新**: ADR-010 により通信方式がA2Aに変更。Firestore経由のデータ共有は維持。

- **決定**: Firestore経由でデータ共有（ID参照方式）
- **却下した案**:
  - HTTP直接通信でペイロードに全データを含める → ペイロード肥大化、デバッグ困難
- **理由**:
  - 記事数増加時のHTTPペイロード肥大化を回避
  - Firestoreに中間状態が残るためデバッグ・再処理が容易
  - 各エージェントが必要なデータのみ取得可能
- **パターン**: A2Aメッセージには collectionId のみ含め、詳細はFirestoreから取得

---

## ADR-007: 記事ステータス管理の分離

- **決定**: ScoringStatus（全記事用）と ResearchStatus（ピックアップ用）を分離
- **却下した案**:
  - 単一のStatusで全状態を管理 → 状態遷移が複雑化、記事ごとの進捗が不明確
- **理由**:
  - 全記事がスコアリング対象だが、詳細調査はピックアップのみ
  - 異なるライフサイクルを持つ処理を明確に分離
  - 各記事の処理状況が一目でわかる
- **ステータス定義**:
  - ScoringStatus: PENDING → SCORING → SCORED
  - ResearchStatus: PENDING → RESEARCHING → COMPLETED（ピックアップ記事のみ）

---

## ADR-008: 記事ソースの拡張性設計

- **決定**: BaseFetcher + FetcherRegistry パターンを採用
- **理由**:
  - MVP後にRSS以外のソース（Webサイト監視、メルマガ、外部API）追加を想定
  - 新しいFetcherを実装してRegistryに登録するだけで拡張可能
  - SourceType enum で対応ソース種別を明示
- **対応ソース種別**: RSS, WEBSITE, NEWSLETTER, API
- **トレードオフ**: MVPでは過剰設計に見えるが、拡張コストを大幅に削減

---

## ADR-009: コレクション命名（ArticleCollection）

- **決定**: Report → ArticleCollection に命名変更
- **理由**:
  - 「レポート」は分析結果や報告書を連想させる
  - 実態は「日次で収集した記事の集合」
  - 各記事にdeepDiveReportが付くため、外側をReportと呼ぶと混乱
- **影響範囲**: Firestoreコレクション名、モデル名、API エンドポイント

---

## ADR-010: A2Aプロトコル採用

- **決定**: エージェント間通信に A2A（Agent2Agent）プロトコルを採用
- **却下した案**:
  - Cloud Pub/Sub → 標準プロトコルではない、外部エージェント連携が困難
  - 独自HTTP API → 車輪の再発明、相互運用性なし
- **理由**:
  - Google発のオープン標準プロトコルで、エージェント間の相互運用性を確保
  - Python SDK（a2a-sdk）が成熟しており実装コストが低い
  - MCP（Agent↔Tool）と 補完関係にあり、将来の拡張性が高い
  - Linux Foundation 管理下でベンダー中立
- **影響範囲**:
  - ADR-002（Pub/Sub採用）を廃止
  - 各エージェントを A2A Server として実装
  - Agent Card による能力公開
- **実装方針**:
  - 通信: JSON-RPC 2.0 over HTTP（a2a-sdk 標準）
  - データ共有: Firestore経由（ADR-006 維持）
  - トリガー: Cloud Scheduler → Collector Agent（A2A経由）
- **参考**:
  - [A2A Protocol 公式](https://a2a-protocol.org/latest/)
  - [a2a-python SDK](https://github.com/a2aproject/a2a-python)

---

## ADR-011: ユーザー評価ベースのスコアリング採用

- **決定**: Notion連携（ADR-004）の代わりに、ユーザーの5段階評価 + コメントをベースにLLM（Gemini Flash）でスコアリング
- **却下した案**:
  - Notion連携 + Vector Search → 実装コストがハッカソンMVPに重すぎる（ADR-003, ADR-004 参照）
  - フィードバックなし（全記事を時系列表示のみ） → パーソナライズの価値を示せない
- **理由**:
  - Notionデータに依存せず、ユーザーの明示的な評価から興味プロファイルを構築できる
  - 実装コストが低く、ハッカソン期間内に完成可能
  - 評価データが蓄積されるほど精度が向上する仕組み
- **Librarian Agentの役割変更**:
  - 蓄積された高評価記事（4-5★）をFirestoreから取得
  - LLMで「ユーザー興味プロファイル」を生成し、**Firestoreに永続保持**（`users/{userId}.interestProfile`）
  - 日次バッチ前に新規評価の有無を確認し、あればプロファイルを再生成（なければキャッシュ利用）
  - 新記事をプロファイルに基づいてGemini Flashでスコアリング
- **コールドスタート対応**: 評価データ不足（閾値未満）の場合はスコアリングをスキップし、全記事を時系列表示（スコア0.5固定）
- **Researcherトリガー変更**: Librarian自動ピックアップ → ユーザー手動リクエストに変更。ユーザーが気になる記事を指定して深掘りレポートを依頼
- **影響範囲**:
  - ADR-003（Vector Search）を保留
  - ADR-004（Notion連携）を廃止
  - Firestoreスキーマ変更（`userRating`, `userComment`, `interestProfile`, `interestProfileUpdatedAt` 追加、Notion関連フィールド削除）

---

## ADR-012: 将来のMCPサーバー構想

- **決定**: 評価・コメントDBを将来MCPサーバー経由で外部公開可能にする構想を記録
- **スコープ**: ハッカソンMVPの範囲外。設計時に拡張性を考慮するのみ
- **構想**:
  - ユーザーの評価・コメントデータをMCPサーバー経由で参照可能にする
  - 他のAIエージェントやツールがユーザーの興味・関心データにアクセスできる
  - MCP（Tool提供）と A2A（エージェント間通信）の補完関係を活用
- **設計への影響**: Firestoreのスキーマ設計時に、将来の外部公開を意識したデータ構造にする（例: 評価データの正規化、アクセス制御の考慮）

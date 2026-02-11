# services/agents

3つのA2Aエージェント + 共通モジュールで構成されるバックエンド。

## 構造
- `collector/` — RSS巡回・記事収集・Librarianへのスコアリング依頼
- `librarian/` — LLMスコアリング・ピックアップ選定・コンテンツ補完
- `researcher/` — ユーザーリクエストによる深掘りレポート生成（Gemini Pro）
- `shared/` — 全エージェント共通のクライアント・モデル・ユーティリティ
- `scripts/` — E2Eパイプライン検証・Firestoreダンプ等の運用スクリプト

## 各エージェントの共通パターン
- `main.py` — A2AFastAPIApplication エントリポイント
- `agent_executor.py` — AgentExecutor実装（DI組み立て含む）
- `service.py` — ビジネスロジック

## 実行
```bash
# テスト
cd services/agents && .venv/bin/python -m pytest tests/ -v

# エージェント起動（ローカル）
make run-collector-emu   # :8001
make run-librarian-emu   # :8002
make run-researcher-emu  # :8003

# E2E検証（要: Emulator + 全エージェント起動）
make e2e
```

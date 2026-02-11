# 指示
- 常に日本語で回答します。
- ユーザーと作業する中で/docs配下を更新した方が良い場合は、どの部分をどう修正するかユーザーに確認し、許可を持って更新します。
- pytestのテスト名は日本語で命名します。

# プロジェクト概要
ユーザーの評価・フィードバックから興味関心を学習し、ニュースを自律選別するバッチ型AIリサーチプラットフォーム。

## 構成
- `services/agents/` — Python バックエンド（3つのA2Aエージェント + shared共通モジュール）
- `apps/web/` — Next.js フロントエンド（開発中）
- `docs/` — 設計ドキュメント（PRD, Design_doc, ADR, API_design, backend/implementation）

## 技術スタック
- **バックエンド**: Python 3.12 / FastAPI / a2a-sdk / Gemini Flash・Pro / Firestore
- **フロントエンド**: Next.js / Tailwind CSS
- **インフラ**: Cloud Run / Firebase App Hosting / Cloud Scheduler

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
AGENTS_DIR := services/agents
VENV_BIN := .venv/bin
EMULATOR_HOST := localhost:8080
GCP_PROJECT := curation-persona
GCP_REGION := asia-northeast1

.PHONY: setup-backend run-collector run-librarian run-researcher run-frontend test test-unit test-cov lint lint-fix help run-emulator run-collector-emu run-librarian-emu run-researcher-emu e2e e2e-dump seed deploy-collector deploy-librarian deploy-researcher deploy-rules

help: ## ヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Backend ===

setup-backend: ## バックエンド環境セットアップ
	cd $(AGENTS_DIR) && python3 -m venv .venv
	cd $(AGENTS_DIR) && $(VENV_BIN)/pip install -e ".[dev]"
	cd $(AGENTS_DIR) && cp -n .env.example .env 2>/dev/null || true

run-collector: ## Collector Agent を起動 (port 8001)
	cd $(AGENTS_DIR) && $(VENV_BIN)/uvicorn collector.main:app --reload --port 8001

run-librarian: ## Librarian Agent を起動 (port 8002)
	cd $(AGENTS_DIR) && $(VENV_BIN)/uvicorn librarian.main:app --reload --port 8002

run-researcher: ## Researcher Agent を起動 (port 8003)
	cd $(AGENTS_DIR) && $(VENV_BIN)/uvicorn researcher.main:app --reload --port 8003

# === Emulator (ローカルE2E検証) ===

run-emulator: ## Firebase Emulator を起動 (Firestore: 8080, UI: 4000)
	firebase emulators:start --project curation-persona

run-collector-emu: ## Collector Agent を起動 (Emulator接続)
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/uvicorn collector.main:app --reload --port 8001

run-librarian-emu: ## Librarian Agent を起動 (Emulator接続)
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/uvicorn librarian.main:app --reload --port 8002

run-researcher-emu: ## Researcher Agent を起動 (Emulator接続)
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/uvicorn researcher.main:app --reload --port 8003

e2e: ## E2E パイプライン検証スクリプト実行
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/python -m scripts.e2e_pipeline

e2e-dump: ## Emulator 内の Firestore データをダンプ
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/python -m scripts.dump_firestore

seed: ## Emulator にフロントエンド開発用シードデータを投入
	cd $(AGENTS_DIR) && FIRESTORE_EMULATOR_HOST=$(EMULATOR_HOST) $(VENV_BIN)/python -m scripts.seed_emulator

# === Frontend ===

run-frontend: ## Next.js dev server を起動
	cd apps/web && npm run dev

# === Test ===

test: ## 全テスト実行
	cd $(AGENTS_DIR) && $(VENV_BIN)/pytest tests/ -v

test-unit: ## ユニットテストのみ
	cd $(AGENTS_DIR) && $(VENV_BIN)/pytest tests/unit -v

test-cov: ## カバレッジ付きテスト
	cd $(AGENTS_DIR) && $(VENV_BIN)/pytest tests/ --cov=. --cov-report=html

# === Lint ===

lint: ## ruff でリント
	cd $(AGENTS_DIR) && $(VENV_BIN)/ruff check .

lint-fix: ## ruff でリント + 自動修正
	cd $(AGENTS_DIR) && $(VENV_BIN)/ruff check --fix .

# === Deploy ===

deploy-collector: ## Collector Agent を Cloud Run にデプロイ
	cd $(AGENTS_DIR) && gcloud run deploy collector-agent \
		--source . \
		--set-env-vars AGENT=collector \
		--project $(GCP_PROJECT) \
		--region $(GCP_REGION) \
		--allow-unauthenticated \
		--port 8080

deploy-librarian: ## Librarian Agent を Cloud Run にデプロイ
	cd $(AGENTS_DIR) && gcloud run deploy librarian-agent \
		--source . \
		--set-env-vars AGENT=librarian \
		--project $(GCP_PROJECT) \
		--region $(GCP_REGION) \
		--allow-unauthenticated \
		--port 8080

deploy-researcher: ## Researcher Agent を Cloud Run にデプロイ
	cd $(AGENTS_DIR) && gcloud run deploy researcher-agent \
		--source . \
		--set-env-vars AGENT=researcher \
		--project $(GCP_PROJECT) \
		--region $(GCP_REGION) \
		--allow-unauthenticated \
		--port 8080

deploy-rules: ## Firestore Security Rules をデプロイ
	firebase deploy --only firestore:rules --project $(GCP_PROJECT)

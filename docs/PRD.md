# プロジェクト名: Curation Persona

**〜 「情報の洪水」を「個人の知能」へ変換する自律型AIリサーチ・エコシステム 〜**

> **Note**: 本ドキュメントは [Google Cloud Japan AI Hackathon Vol.4](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol4?tab=rule) 向けのMVP開発を対象としています。

---

## 1. プロジェクト概要 (Executive Summary)

### 1.1 ビジョン

現代社会における「情報のオーバーロード（洪水）」を解消し、ユーザーにとって本当に価値のある情報だけが、その人の過去の思考（Notion等）と結びついて届けられる「知的パートナー」を構築する。

### 1.2 製品定義

Curation Personaは、ユーザーの過去の評価・フィードバックから興味関心を学習したAIエージェントが、Web上の膨大なニュースから「あなたに関連する」ものだけを自律的に選別し、ユーザーのリクエストに応じて詳細調査を行うバッチ型AIリサーチ・プラットフォームです。

---

## 2. ターゲットユーザー (Target Users)

### 2.1 ペルソナ

| 属性 | 内容 |
|------|------|
| **名前** | 田中 太郎（仮名） |
| **職業** | 個人開発者 / テックリード |
| **年齢** | 28〜40歳 |
| **特徴** | 技術トレンドを追いたいが時間がない。RSSリーダーやPocketに記事を溜め込みがち。気になる記事は深掘りしたい。 |
| **課題** | 毎日100件以上の記事が流れてくるが、本当に必要な情報を見極める時間がない |
| **ゴール** | 朝10分で「自分に関係ある」情報だけをキャッチアップしたい |

### 2.2 ユーザーストーリー

| ID | ストーリー | 優先度 |
|----|-----------|--------|
| US-01 | ユーザーとして、朝起きたら自分専用にキュレーションされたニュースを読みたい | Must |
| US-02 | ユーザーとして、なぜその記事が自分に関連するか理由を知りたい | Must |
| US-03 | ユーザーとして、過去の高評価記事との関連性を確認したい | Should |
| US-04 | ユーザーとして、5段階評価 + コメントでAIの精度を改善したい | Should |
| US-05 | ユーザーとして、過去のレポートを検索・閲覧したい | Could |
| US-06 | ユーザーとして、気になる記事の深掘りレポートをリクエストしたい | Should |

---

## 3. ターゲット課題と解決策 (Problems & Solutions)

### 3.1 課題 (Pain Points)

1. **積読（つんどく）の常態化**: 「あとで読む」に保存しても、文脈が欠如しているため読み直す動機が湧かず、死蔵される。
2. **パーソナライズの限界**: 一般的なニュースアプリは「カテゴリ」でしか絞り込めず、「自分の現在の関心事やプロジェクト」に基づいたフィルタリングができない。
3. **エージェント運用コスト**: 高機能なAIエージェントをリアルタイムで回すとAPIコストが膨大になり、個人開発では維持が困難。

### 3.2 解決策 (Solutions)

1. **Feedback-Driven Filtering (評価ベースフィルタ)**: ユーザーの5段階評価とコメントから興味プロファイルを生成し、Librarian Agentが「なぜこの記事があなたにとって重要か」をLLMで判定。
2. **Daily Batch Strategy (日次一括処理)**: 1日1回の定期実行に絞ることで、計算リソースを最適化し、APIコストを最小限に抑える。
3. **On-Demand Deep Dive**: ユーザーが気になる記事を指定し、上位モデル（Gemini 2.5 Pro）を用いてWeb検索を組み合わせた詳細な考察を生成。

---

## 4. 機能要件 (Functional Requirements)

### 4.1 優先度定義 (MoSCoW)

- **Must**: ハッカソンデモに必須
- **Should**: 時間があれば実装
- **Could**: 将来拡張

### 4.2 Core: エージェント・エコシステム (A2A)

| 機能 | 説明 | 優先度 |
|------|------|--------|
| Collector Agent | RSS/Webニュースの巡回、記事収集、フロー制御 | Must |
| Librarian Agent | ユーザー評価ベースのLLMスコアリングで関連性判定 | Must |
| Researcher Agent | ユーザーリクエストに基づく詳細レポート生成（Gemini 2.5 Pro） | Must |

### 4.3 Frontend: Neural Dashboard

| 機能 | 説明 | 優先度 |
|------|------|--------|
| Daily Briefing | 今日の厳選レポート一覧表示 | Must |
| Relevance Trace | AIの選定理由・過去の高評価記事との関連性の可視化 | Should |
| Feedback & Research | 5段階評価 + コメント + 深掘りリクエスト | Should |
| Archive検索 | 過去レポートの検索・閲覧 | Could |

### 4.4 Backend/Infrastructure

| 機能 | 説明 | 優先度 |
|------|------|--------|
| Scheduled Trigger | Cloud Schedulerによる毎朝の自動実行 | Must |
| Agent間通信 | A2Aプロトコルによるエージェント連携 | Must |
| Persistent Store | Firestoreへのレポート保存 | Must |
| 手動トリガー | LINE Bot経由でのオンデマンド実行 | Could |

---

## 5. 非機能要件 (Non-Functional Requirements)

### 5.1 コスト戦略

| 処理 | モデル | 理由 |
|------|--------|------|
| LLMベーススコアリング | Gemini 2.5 Flash | 低コスト・高速 |
| 詳細分析（ピックアップのみ） | Gemini 2.5 Pro | 高精度・広コンテキスト |

- **目標**: 1ユーザーあたり月額 $5 以内

### 5.2 セキュリティ・プライバシー（ハッカソン向け簡易版）

- Firebase Authによるユーザー認証
- ユーザーデータはユーザー単位で分離（Firestore Security Rules）
- 本番運用時は追加のセキュリティレビューが必要

### 5.3 パフォーマンス目標（参考値）

- バッチ処理完了: 起動から30分以内（50記事処理時）
- ダッシュボード初期表示: 3秒以内

---

## 6. 技術スタック (Technical Stack)

| カテゴリ | 技術 |
|----------|------|
| **Frontend** | Next.js, Tailwind CSS, daisyUI |
| **Backend** | Cloud Run (Python) |
| **AI/LLM** | Gemini 2.5 Pro / Flash (Vertex AI) |
| **Database** | Cloud Firestore |
| **Integration** | RSS Feeds |
| **Infra/Deployment** | Firebase App Hosting, Cloud Scheduler, A2A Protocol |

---

## 7. 開発ロードマップ (Roadmap)

### 開発方針

- **バックエンド優先**: エージェント層を先に構築し、UIは後から接続
- **並行開発**: フロント・バックで独立して進められる部分は並行実施
- **ユーザー評価**: 5段階評価 + コメントでAI精度を継続改善

### 技術選定サマリ

| 領域 | 選定 | 理由 |
|------|------|------|
| スコアリング | ユーザー評価 + Gemini Flash | 実装コスト低、ハッカソン向け |
| Agent間通信 | A2A Protocol (a2a-sdk) | Google発オープン標準、相互運用性 |
| LLM | Gemini Flash/Pro | コスト効率 |
| インフラ | Cloud Run + Firestore | サーバーレス |

---

### Phase 1: MVP Infrastructure（基盤構築）

#### Step 1-1: プロジェクト構造セットアップ
- [x] ディレクトリ構造作成
  ```
  ├── apps/web/          # Next.js
  ├── services/agents/   # Python (Collector/Librarian/Researcher)
  ├── packages/shared/   # 共有型定義
  └── infrastructure/    # デプロイスクリプト
  ```
- [x] 各プロジェクトの初期化（package.json, pyproject.toml等）

#### Step 1-2: GCP/Firebase 設定
- [x] Firebase プロジェクト作成
- [x] Firestore (Native mode) 有効化
- [ ] Cloud Run API 有効化
- [ ] Cloud Scheduler ジョブ作成（Collector Agent トリガー）

#### Step 1-3: 疎通確認
- [ ] Next.js ローカル起動確認
- [x] Cloud Scheduler → Collector Agent (A2A) 接続確認
- [x] Firestore 読み書きテスト

---

### Phase 2: Intelligence Layer（AI連携）

#### Step 2-1: ユーザー評価システム構築
- [x] 5段階評価 + コメントのデータモデル設計
- [x] フィードバックAPI実装（rating + comment）
- [x] Firestoreへの評価データ保存

#### Step 2-2: LLMベーススコアリング実装
- [x] 過去の高評価記事（4-5★）をFirestoreから取得
- [x] Gemini Flashで「ユーザー興味プロファイル」を生成
- [x] 新記事をプロファイルに基づいてスコアリング

#### Step 2-3: Librarian Agent
- [x] LLMベーススコアリングロジック実装
- [x] コールドスタート対応（評価データ0件時の処理）

---

### Phase 3: Research Pipeline（自動化）

#### Step 3-1: Collector Agent
- [x] RSS取得（feedparser）
- [x] RSSフィードのコンテンツ取得改善（HTML除去・summary/content分離）
- [x] Librarian連携（スコアリング依頼）

#### Step 3-2: Researcher Agent
- [x] ユーザー手動リクエスト経由でのトリガー
- [x] Gemini Pro による詳細レポート生成
- [x] Firestore への保存

#### Step 3-3: パイプライン統合
- [x] Collector → Librarian の連携フロー
- [x] Dashboard API → Researcher の手動トリガーフロー
- [x] A2A通信実装

#### Step 3-4: コンテンツ補完
- [x] 上位記事のWebスクレイピング（robots.txt準拠・逐次取得）
- [x] LibrarianServiceへの統合（スコアリング後、Firestore書き戻し前）
- [x] E2E検証環境の構築（Firebase Emulator）

---

### Phase 4: Polish（仕上げ）

#### Step 4-1: Dashboard UI
- [ ] Daily Briefing 表示（Firestore onSnapshot でリアルタイム更新）
- [ ] コレクションステータス表示（collecting → scoring → completed の進捗）
- [ ] Thinking Trace（選定理由の可視化）
- [ ] フィードバック機能（5段階評価 + コメント）

#### Step 4-2: 深掘りレポートストリーミング
- [ ] Next.js API Route → Gemini Pro streaming → SSE でブラウザに直接配信
- [ ] Firestore への保存は生成完了後に1回のみ（DB負荷を最小化）
- [ ] レポート生成中の進捗UI（テキストがリアルタイムに流れる表示）

#### Step 4-3: デモ準備
- [ ] デモシナリオ作成
- [ ] 発表資料作成

---

## 8. 成功指標 (Success Metrics)

| 指標 | 目標 | 計測方法 |
|------|------|----------|
| Filtering Accuracy | 80%以上が「役立つ」評価 | ユーザーフィードバック |
| Cost Efficiency | 月額 $5/ユーザー以内 | GCP請求レポート |
| Demo Completion | 全フローが動作すること | ハッカソン審査 |

---

## 9. リポジトリ構成 (Repository Structure)

```
curation-persona/
├── apps/
│   └── web/                 # Next.js フロントエンド
├── services/
│   └── agents/              # Cloud Run エージェント群
│       ├── collector/
│       ├── librarian/
│       └── researcher/
├── packages/
│   └── shared/              # 共有型定義・定数
├── infrastructure/          # デプロイ用スクリプト
└── docs/                    # ドキュメント
```

---

## 10. リスクと緩和策（ハッカソン向け）

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| LLM API コスト超過 | 予算オーバー | 処理記事数の上限設定（1日50件） |
| LLMスコアリング精度不足 | 関連記事が見つからない | プロンプト改善、評価データ蓄積後に再調整 |
| コールドスタート問題 | 初回は全記事が同スコア | 全記事を時系列表示し、評価データ蓄積を促す |
| 開発時間不足 | 機能未完成 | Must機能に集中、Could機能は切り捨て |

# 今日のブリーフィング画面 (`/dashboard`)

## 実装状態: モック

## 構成ファイル
- `page.tsx` — ページ本体 (`"use client"`)
- `layout.tsx` — 共通レイアウト（`Sidebar` + `<main>`、配下の全ページに適用）

## 使用コンポーネント
- `BriefingCard` — 記事カード（詳細版: OGP画像、AIの選定理由、星評価、原文リンク、深掘りリサーチリンク）
- `StatusIndicator` — 処理ステータス表示
- `ScoreBar` — 関連度スコアバー（BriefingCard内）
- `StarRating` — 5段階星評価（BriefingCard内）

## モックデータ
- `mockArticles`: 5件（`Article` 型）
- ピックアップ記事（`is_pickup: true`）とその他で分割表示
- 星評価の変更は `useState` でローカル管理

## 本番化で必要な変更
- Firestore `collections/{collectionId}` + `articles/{articleId}` からデータ取得
- Firebase Auth によるユーザー認証
- 星評価の変更を Firestore に永続化（`articles/{articleId}.user_rating`）
- `StatusIndicator` をバッチ処理の実際のステータスと連動
- 日付選択による過去ブリーフィングの閲覧

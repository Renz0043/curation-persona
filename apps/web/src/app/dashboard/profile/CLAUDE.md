# 興味・関心プロファイル画面 (`/dashboard/profile`)

## 実装状態: モック

## 構成ファイル
- `page.tsx` — ページ本体 (`"use client"`、サブコンポーネント3つ含む)

## 画面構成（5セクション）
1. **ページヘッダー** — タイトル「関心プロファイル」、最終更新日時、[更新]ボタン
2. **AIによる関心分析** — primary-bg背景カード、左カラーバー、分析テキスト、評価記事数
3. **情報ソース設定** — RSSフィード一覧（有効/一時停止切替、削除）、追加ボタン（disabled）
4. **Bookmark APIキー** — マスク/表示切替、コピー、再生成ボタン
5. **キュレーション設定** — 深掘り深度（select）、異業種視点（select）

## ページ内サブコンポーネント
- `FeedRow` — RSSフィード1行（ステータス切替・削除）
- `IconButton` — 汎用アイコンボタン（ホバー・アクティブ対応）
- `SettingRow` — 設定項目1行（ラベル・ヒント・select）

## state管理
```typescript
feeds: RssFeed[]              // RSSフィード一覧（追加・削除・ステータス切替）
showApiKey: boolean            // APIキーの表示/非表示
copied: boolean                // コピー完了フラグ（2秒後にリセット）
settings: CurationSettings     // 深掘り深度・異業種視点
refreshHover: boolean          // 更新ボタンのホバー状態
```

## モックデータ
- `mockProfile`: AI分析テキスト、最終更新日時、評価記事数
- `initialFeeds`: 5件のRSSフィード
- `mockApiKey`: ダミーAPIキー文字列
- デフォルト設定: medium / moderate

## 本番化で必要な変更
- Firestore `users/{userId}` からプロファイル・設定データ取得
- MCP `get_interest_profile` の結果を表示
- RSSフィード CRUD を Firestore に永続化
- APIキーの生成・管理をバックエンドAPIと連携
- 設定変更を Firestore に永続化
- [更新] ボタンでプロファイル再分析をトリガー

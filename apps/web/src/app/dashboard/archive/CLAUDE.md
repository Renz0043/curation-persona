# アーカイブ検索画面 (`/dashboard/archive`)

## 実装状態: モック

## 構成ファイル
- `page.tsx` — ページ本体 (`"use client"`)

## レイアウト
2カラム構成（親の `dashboard/layout.tsx` の Sidebar と合わせて実質3カラム）:
- 左: `DateTree`（w-48、border-r）— 年月日ナビゲーション
- 右: メインエリア（flex-1、max-w-4xl）— 検索バー、フィルター、記事リスト

## 使用コンポーネント
- `DateTree` — 年月日ツリーナビ（展開/折りたたみ、日付選択/解除）
- `ArchiveCard` — 検索結果カード（簡略版: カテゴリバッジ、ソース、日付、AIスコアバッジ、タイトルリンク、概要2行）

## state管理
```typescript
selectedDate: string | null      // 日付ツリーで選択中の日付
searchQuery: string              // 検索バーのテキスト
sortBy: "relevance" | "date" | "score"  // 並び替え
filters: { minScore: number | null, category: string | null }  // フィルター
```

## モックデータ
- `mockArchiveArticles`: 10件（`ArchiveArticle` 型）
- `DateTree` 内に独自のモック日付データ（2025年1月、2024年12月・11月）
- クライアントサイドでフィルタリング・ソート

## 機能
- 検索: タイトル・概要・ソース名でテキストマッチ
- フィルター: AIスコア閾値、カテゴリ（チップUI、×で解除）
- 日付選択: DateTreeからの日付フィルター（チップにも表示）
- 並び替え: 関連度順 / 日付順 / AIスコア順
- カード全体クリックで `/article/[id]` に遷移

## 本番化で必要な変更
- Firestore `articles` コレクションからの検索（Firestoreクエリ or Algolia等）
- `DateTree` のデータを `collections` コレクションから動的生成
- ページネーション（現在は「もっと読み込む」ボタンのみ表示）
- 右サイドバー（リサーチ済みアーティファクト）はバックエンドAPI対応後に追加

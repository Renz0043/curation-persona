# 記事詳細画面 (`/article/[id]`)

## 実装状態: モック

## 構成ファイル
- `page.tsx` — ページ本体 (`"use client"`)
- `layout.tsx` — レイアウト（`Sidebar` + `<main>`）

## レイアウト
- 上部: sticky ナビバー（戻るリンク、カスタムレポート生成ボタン(disabled)）
- ヘッダー: ステータスバッジ、メタ情報、タイトル、Relevance Score バー
- メイン: 2カラム grid（lg:8 + lg:4）
  - 左カラム: 元記事本文 → AI分析レポート（アコーディオン）→ フィードバックフォーム
  - 右カラム: 業界別視点（Cross-Industry Perspective）カード群

## 使用コンポーネント
- `ScoreBar` — Relevance Score 表示（ヘッダー内）
- `StarRating` — フィードバック評価
- lucide-react アイコン多数（ArrowLeft, Sparkles, Brain, Factory, GraduationCap, DollarSign 等）

## state管理
```typescript
rating: number          // 星評価（初期値: article.user_rating ?? 0）
comment: string         // フィードバックコメント
isAnalysisOpen: boolean // AI分析レポートの展開/折りたたみ
```

## モックデータ
- `mockArticles`: Record<string, ArticleDetail> — id "1" のみ定義
- 存在しないIDは `notFound()` を返す
- `ArticleDetail` 型: 記事本文(string[])、deep_dive_report、cross_industry_feedback を含む

## セクション詳細
1. **元記事本文**: content配列をパラグラフ表示、ソース記事への外部リンク
2. **AI分析レポート**: アコーディオン（デフォルト閉じ）、要約 → セクション群 → キーポイント → 結論
3. **業界別視点**: 製造業・教育・金融の3視点、リスク視点は左ボーダー赤
4. **フィードバック**: 星評価 + テキストエリア + 送信ボタン

## 本番化で必要な変更
- Firestore `articles/{articleId}` からデータ取得
- Deep Diveレポートの動的取得（Researcher Agent の SSE ストリーミング対応）
- 異業種フィードバックの動的取得
- フィードバック送信を Firestore に永続化
- 「カスタムレポート生成」ボタンの有効化（Researcher Agent 連携）
- モックID "1" 以外の記事に対応

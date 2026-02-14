# フロントエンド (apps/web)

## 技術スタック
- Next.js 16 / React 19 / TypeScript
- Tailwind CSS 4 + daisyUI 5
- CSS変数によるデザイントークン (`globals.css`)
- アイコン: lucide-react
- フォント: Noto Serif JP (見出し) / Noto Sans JP (本文)

## デザインシステム方針
- 色・間隔・角丸はすべて `globals.css` のCSS変数経由で適用する
- Tailwind arbitrary value (`style={{}}`) で CSS変数を参照するパターンを使用
- Stitchデザインを参考にするが、色 (`#588157`)・アイコン (lucide-react) は既存システムに翻訳する

## ページ実装状況

| ルート | ファイル | 状態 | 備考 |
|--------|----------|------|------|
| `/` | `app/page.tsx` | 完了 | `/dashboard` へリダイレクト |
| `/dashboard` | `app/dashboard/page.tsx` | モック | 今日のブリーフィング画面。モック記事5件 |
| `/dashboard/archive` | `app/dashboard/archive/page.tsx` | モック | アーカイブ検索。日付ツリー・検索・フィルター・並替。モック10件 |
| `/article/[id]` | `app/article/[id]/page.tsx` | モック | 記事詳細・Deep Diveレポート・異業種フィードバック表示 |
| `/dashboard/profile` | `app/dashboard/profile/page.tsx` | モック | 興味・関心プロファイル。AI分析・RSSフィード管理・APIキー・キュレーション設定 |

## レイアウト構成
- `app/layout.tsx` — ルートレイアウト（フォント設定、メタデータ）
- `app/dashboard/layout.tsx` — ダッシュボード共通レイアウト（`Sidebar` + `<main>`）
- `app/article/[id]/layout.tsx` — 記事詳細レイアウト（`Sidebar` + `<main>`）

## コンポーネント一覧

| コンポーネント | ファイル | 用途 |
|---------------|----------|------|
| `Sidebar` | `components/Sidebar.tsx` | 共通サイドナビ（w-64） |
| `BriefingCard` | `components/BriefingCard.tsx` | ブリーフィング記事カード（詳細版） |
| `ArchiveCard` | `components/ArchiveCard.tsx` | アーカイブ検索結果カード（簡略版） |
| `DateTree` | `components/DateTree.tsx` | 年月日ナビゲーションツリー |
| `ScoreBar` | `components/ScoreBar.tsx` | AIスコアのプログレスバー |
| `StarRating` | `components/StarRating.tsx` | 5段階星評価（インタラクティブ） |
| `StatusIndicator` | `components/StatusIndicator.tsx` | 処理ステータス表示 |

## 認証・データ連携
現時点では全画面モックデータで動作。Firebase Auth / Firestore 連携は未実装。

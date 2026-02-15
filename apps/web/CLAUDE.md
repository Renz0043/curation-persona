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
| `/dashboard` | `app/dashboard/page.tsx` | Firestore連携済 | ブリーフィング + ブックマーク記事。星評価永続化 |
| `/dashboard/archive` | `app/dashboard/archive/page.tsx` | Firestore連携済 | アーカイブ検索。日付ツリー動的生成・検索・フィルター |
| `/article/[id]` | `app/article/[id]/page.tsx` | Firestore連携済 | 記事詳細。onSnapshotでリアルタイム更新、Markdown Deep Dive |
| `/dashboard/submit` | `app/dashboard/submit/page.tsx` | Firestore連携済 | 記事追加（実API）+ Firestoreから投稿履歴取得 |
| `/dashboard/profile` | `app/dashboard/profile/page.tsx` | Firestore連携済（読取のみ） | 興味プロファイル・ソース設定・APIキー表示 |

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
- `src/lib/auth-context.tsx` — AuthProvider + useAuth()。Emulatorモードではテストユーザー自動サインイン
- `src/lib/firestore.ts` — Firestore読み取りヘルパー関数群
- `src/lib/types.ts` — 共通型定義（バックエンドのPydanticモデルと対応）
- `src/app/api/collections/[collectionId]/feedback/route.ts` — 星評価永続化API（firebase-admin使用）
- Emulator接続: `NEXT_PUBLIC_USE_EMULATOR=true` で Auth/Firestore Emulatorに自動接続
- シードデータ: `make seed` で Emulator にテストデータ投入

# 記事追加画面 (`/dashboard/submit`)

## 実装状態: 実API連携（投稿） + モック（履歴）

## 構成ファイル
- `page.tsx` — ページ本体 (`"use client"`)

## 画面構成（3セクション）
1. **ページヘッダー** — タイトル「記事を追加」、説明テキスト
2. **リサーチ投稿フォーム** — APIキー入力（localStorage永続化）、URL入力、送信ボタン、ステータス表示
3. **投稿履歴（モック）** — 過去の投稿3件（URL、日時、ステータス、詳細リンク）

## API連携
- `POST ${NEXT_PUBLIC_RESEARCHER_URL}/api/bookmarks` に実リクエスト
- リクエストボディ: `{ url, api_key }`
- レスポンス: 200 (accepted) / 401 (Invalid API key) / 422 (バリデーションエラー)

## state管理
```typescript
apiKey: string           // APIキー（localStorage永続化、key: "curation-persona-api-key"）
url: string              // 入力URL
submitting: boolean      // 送信中フラグ
result: { status: "success" | "error"; message: string } | null  // 送信結果
```

## 環境変数
- `NEXT_PUBLIC_RESEARCHER_URL` — ResearcherエージェントのベースURL（デフォルト: `http://localhost:8082`）

## 本番化で必要な変更
- 投稿履歴をFirestoreの `bm_{userId}` コレクションから取得
- Firebase Auth によるユーザー認証（APIキー入力の代替）
- 投稿後のリアルタイムステータス更新

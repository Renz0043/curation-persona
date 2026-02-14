"use client";

import { useState, useEffect } from "react";
import {
  Send,
  Loader2,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Clock,
  Key,
} from "lucide-react";

const RESEARCHER_URL =
  process.env.NEXT_PUBLIC_RESEARCHER_URL || "http://localhost:8082";

const LOCALSTORAGE_KEY = "curation-persona-api-key";

// モック投稿履歴
const mockHistory = [
  {
    url: "https://arxiv.org/abs/2401.12345",
    submittedAt: "2025-01-14 18:30",
    status: "completed" as const,
    articleId: "bm_abc123",
  },
  {
    url: "https://techcrunch.com/2025/01/13/ai-agents-enterprise/",
    submittedAt: "2025-01-13 09:15",
    status: "completed" as const,
    articleId: "bm_def456",
  },
  {
    url: "https://www.nature.com/articles/s41586-025-00001-1",
    submittedAt: "2025-01-12 21:00",
    status: "processing" as const,
    articleId: null,
  },
];

export default function SubmitPage() {
  const [apiKey, setApiKey] = useState("");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    status: "success" | "error";
    message: string;
  } | null>(null);

  // localStorage からAPIキーを復元
  useEffect(() => {
    const saved = localStorage.getItem(LOCALSTORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  // APIキー変更時に localStorage へ保存
  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    if (value) {
      localStorage.setItem(LOCALSTORAGE_KEY, value);
    } else {
      localStorage.removeItem(LOCALSTORAGE_KEY);
    }
  };

  const isValidUrl = (s: string) => {
    try {
      const u = new URL(s);
      return u.protocol === "http:" || u.protocol === "https:";
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    if (!apiKey.trim()) {
      setResult({ status: "error", message: "APIキーを入力してください" });
      return;
    }
    if (!isValidUrl(url)) {
      setResult({
        status: "error",
        message: "有効なURLを入力してください（http:// または https://）",
      });
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch(`${RESEARCHER_URL}/api/bookmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, api_key: apiKey }),
      });

      if (response.ok) {
        setResult({
          status: "success",
          message: "リサーチを受け付けました。完了までしばらくお待ちください。",
        });
        setUrl("");
      } else if (response.status === 401) {
        setResult({
          status: "error",
          message: "APIキーが無効です。プロファイル画面で確認してください。",
        });
      } else if (response.status === 422) {
        const data = await response.json().catch(() => null);
        setResult({
          status: "error",
          message: data?.detail || "入力内容に問題があります。",
        });
      } else {
        setResult({
          status: "error",
          message: `エラーが発生しました（${response.status}）`,
        });
      }
    } catch {
      setResult({
        status: "error",
        message:
          "サーバーに接続できませんでした。Researcherエージェントが起動しているか確認してください。",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* ページヘッダー */}
      <div className="mb-8">
        <h1
          className="text-3xl font-bold mb-2"
          style={{
            color: "var(--color-text-dark)",
            fontFamily: "var(--font-display)",
          }}
        >
          記事を追加
        </h1>
        <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
          URLを入力して深掘りリサーチを実行します
        </p>
      </div>

      {/* URL投稿フォーム */}
      <section className="mb-10">
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary)" }}
          />
          リサーチ投稿
        </h2>
        <form
          onSubmit={handleSubmit}
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-xl)",
          }}
        >
          {/* APIキー入力 */}
          <div className="mb-4">
            <label className="flex items-center gap-1.5 mb-2">
              <Key size={14} style={{ color: "var(--color-primary)" }} />
              <span
                className="text-sm font-semibold"
                style={{ color: "var(--color-text-dark)" }}
              >
                APIキー
              </span>
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder="cp_live_sk_..."
              className="w-full px-3 py-2.5 text-sm"
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-bg)",
                color: "var(--color-text-dark)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
                e.currentTarget.style.boxShadow =
                  "0 0 0 2px var(--color-primary-bg)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
            <p
              className="text-xs mt-1.5"
              style={{ color: "var(--color-text-muted)" }}
            >
              プロファイル画面からコピーしてください
            </p>
          </div>

          {/* URL入力 */}
          <div className="mb-4">
            <label className="flex items-center gap-1.5 mb-2">
              <ExternalLink
                size={14}
                style={{ color: "var(--color-primary)" }}
              />
              <span
                className="text-sm font-semibold"
                style={{ color: "var(--color-text-dark)" }}
              >
                URL
              </span>
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="w-full px-3 py-2.5 text-sm"
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-bg)",
                color: "var(--color-text-dark)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
                e.currentTarget.style.boxShadow =
                  "0 0 0 2px var(--color-primary-bg)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* 送信ボタン */}
          <button
            type="submit"
            disabled={submitting}
            className={`flex items-center justify-center gap-2 w-full px-4 py-3 text-sm font-semibold text-white transition-opacity duration-150 ${
              submitting ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
            }`}
            style={{
              backgroundColor: "var(--color-primary)",
              borderRadius: "var(--radius-md)",
              border: "none",
            }}
          >
            {submitting ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
            {submitting ? "送信中..." : "リサーチを開始"}
          </button>

          {/* ステータス表示 */}
          {result && (
            <div
              className="flex items-center gap-2 mt-4 px-4 py-3 text-sm"
              style={{
                borderRadius: "var(--radius-md)",
                backgroundColor:
                  result.status === "success"
                    ? "rgba(107, 156, 123, 0.1)"
                    : "rgba(214, 140, 140, 0.1)",
                color:
                  result.status === "success"
                    ? "var(--color-positive)"
                    : "var(--color-risk)",
              }}
            >
              {result.status === "success" ? (
                <CheckCircle size={16} />
              ) : (
                <AlertCircle size={16} />
              )}
              {result.message}
            </div>
          )}
        </form>
      </section>

      {/* 投稿履歴（モック） */}
      <section>
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary-soft)" }}
          />
          投稿履歴
        </h2>
        <div
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
          }}
        >
          {mockHistory.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-3"
              style={{
                borderBottom:
                  i === mockHistory.length - 1
                    ? "none"
                    : "1px solid var(--color-border)",
              }}
            >
              <ExternalLink
                size={14}
                style={{
                  color: "var(--color-text-muted)",
                  flexShrink: 0,
                }}
              />
              <div className="flex-1 min-w-0">
                <div
                  className="text-sm truncate"
                  style={{ color: "var(--color-text-dark)" }}
                >
                  {item.url}
                </div>
                <div
                  className="flex items-center gap-1.5 text-xs mt-0.5"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  <Clock size={11} />
                  {item.submittedAt}
                </div>
              </div>
              <span
                className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium"
                style={{
                  borderRadius: "var(--radius-full)",
                  backgroundColor:
                    item.status === "completed"
                      ? "rgba(107, 156, 123, 0.1)"
                      : "rgba(196, 164, 106, 0.1)",
                  color:
                    item.status === "completed"
                      ? "var(--color-positive)"
                      : "var(--color-accent)",
                }}
              >
                {item.status === "completed" ? (
                  <CheckCircle size={12} />
                ) : (
                  <Loader2 size={12} />
                )}
                {item.status === "completed" ? "完了" : "処理中"}
              </span>
              {item.articleId && (
                <a
                  href={`/article/${item.articleId}`}
                  className="text-xs font-medium no-underline"
                  style={{ color: "var(--color-primary)" }}
                >
                  詳細
                </a>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

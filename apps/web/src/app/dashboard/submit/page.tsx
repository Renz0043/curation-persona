"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Clock,
  Key,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { getBookmarkArticles, subscribeToArticle } from "@/lib/firestore";
import type { Article } from "@/lib/types";

const RESEARCHER_URL =
  process.env.NEXT_PUBLIC_RESEARCHER_URL || "http://localhost:8082";

const LOCALSTORAGE_KEY = "curation-persona-api-key";

export default function SubmitPage() {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState("");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    status: "success" | "error";
    message: string;
  } | null>(null);
  const [bookmarks, setBookmarks] = useState<Article[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // localStorage からAPIキーを復元
  useEffect(() => {
    const saved = localStorage.getItem(LOCALSTORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  // ブックマーク記事の取得
  const fetchBookmarks = useCallback(async () => {
    if (!user) return;
    setLoadingHistory(true);
    try {
      const arts = await getBookmarkArticles(user.uid);
      // 新しい順にソート（published_at or id）
      arts.sort((a, b) => {
        const ta = a.published_at?.getTime() ?? 0;
        const tb = b.published_at?.getTime() ?? 0;
        return tb - ta;
      });
      setBookmarks(arts);
    } catch (e) {
      console.error("Failed to fetch bookmarks:", e);
    } finally {
      setLoadingHistory(false);
    }
  }, [user]);

  useEffect(() => {
    fetchBookmarks();
  }, [fetchBookmarks]);

  // 処理中のブックマーク記事をリアルタイム監視
  useEffect(() => {
    const pendingItems = bookmarks.filter(
      (b) => b.research_status && b.research_status !== "completed"
    );
    if (pendingItems.length === 0) return;

    const unsubscribes = pendingItems.map((item) =>
      subscribeToArticle(item.id, (updated) => {
        if (!updated) return;
        setBookmarks((prev) =>
          prev.map((b) => (b.id === updated.id ? updated : b))
        );
      })
    );
    return () => unsubscribes.forEach((unsub) => unsub());
  }, [bookmarks.map((b) => `${b.id}:${b.research_status}`).join(",")]);

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
        // 履歴を更新
        setTimeout(() => fetchBookmarks(), 3000);
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

      {/* 投稿履歴 */}
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
          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <Loader2
                size={16}
                className="animate-spin"
                style={{ color: "var(--color-text-muted)" }}
              />
              <span
                className="ml-2 text-sm"
                style={{ color: "var(--color-text-muted)" }}
              >
                読み込み中...
              </span>
            </div>
          ) : bookmarks.length === 0 ? (
            <div
              className="text-center py-8 text-sm"
              style={{ color: "var(--color-text-muted)" }}
            >
              投稿履歴はありません
            </div>
          ) : (
            bookmarks.map((item, i) => {
              const status = item.research_status ?? "pending";
              const isCompleted = status === "completed";
              return (
                <div
                  key={item.id}
                  className="flex items-center gap-3 px-4 py-3"
                  style={{
                    borderBottom:
                      i === bookmarks.length - 1
                        ? "none"
                        : "1px solid var(--color-border)",
                  }}
                >
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ flexShrink: 0 }}
                  >
                    <ExternalLink
                      size={14}
                      style={{
                        color: "var(--color-text-muted)",
                      }}
                    />
                  </a>
                  <div className="flex-1 min-w-0">
                    <div
                      className="text-sm truncate"
                      style={{ color: "var(--color-text-dark)" }}
                    >
                      {item.title || item.url}
                    </div>
                    <div
                      className="flex items-center gap-1.5 text-xs mt-0.5"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      <Clock size={11} />
                      {item.url}
                    </div>
                  </div>
                  <span
                    className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium"
                    style={{
                      borderRadius: "var(--radius-full)",
                      backgroundColor: isCompleted
                        ? "rgba(107, 156, 123, 0.1)"
                        : "rgba(196, 164, 106, 0.1)",
                      color: isCompleted
                        ? "var(--color-positive)"
                        : "#c4a46a",
                    }}
                  >
                    {isCompleted ? (
                      <CheckCircle size={12} />
                    ) : (
                      <Loader2 size={12} className="animate-spin" />
                    )}
                    {isCompleted
                      ? "完了"
                      : status === "researching"
                        ? "調査中"
                        : "処理中"}
                  </span>
                  {isCompleted && (
                    <a
                      href={`/article/${item.id}`}
                      className="text-xs font-medium no-underline"
                      style={{ color: "var(--color-primary)" }}
                    >
                      詳細
                    </a>
                  )}
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}

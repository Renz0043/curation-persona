"use client";

import { useState, useEffect, useCallback } from "react";
import { Play } from "lucide-react";
import BriefingCard from "@/components/BriefingCard";
import BookmarkPendingCard from "@/components/BookmarkPendingCard";
import StatusIndicator from "@/components/StatusIndicator";
import { useAuth } from "@/lib/auth-context";
import {
  getTodayCollection,
  getArticlesByCollection,
  getBookmarkArticles,
  subscribeToCollection,
  subscribeToArticle,
} from "@/lib/firestore";
import type { Article, Collection, CollectionStatus } from "@/lib/types";

function formatDate(date: Date): string {
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  const d = date.getDate();
  const w = weekdays[date.getDay()];
  return `${y}年${m}月${d}日（${w}）`;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [articles, setArticles] = useState<Article[]>([]);
  const [bookmarkArticles, setBookmarkArticles] = useState<Article[]>([]);
  const [collection, setCollection] = useState<Collection | null>(null);
  const [loading, setLoading] = useState(true);
  const [collectRequesting, setCollectRequesting] = useState(false);
  const [collectTriggered, setCollectTriggered] = useState(false);
  const today = new Date();

  const fetchData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      // 今日のコレクション取得
      const col = await getTodayCollection(user.uid);
      setCollection(col);

      if (col) {
        const arts = await getArticlesByCollection(col.id, user.uid);
        // スコア降順でソート
        arts.sort((a, b) => b.relevance_score - a.relevance_score);
        setArticles(arts);
      } else {
        setArticles([]);
      }

      // ブックマーク記事
      const bmArts = await getBookmarkArticles(user.uid);
      bmArts.sort((a, b) => b.relevance_score - a.relevance_score);
      setBookmarkArticles(bmArts);
    } catch (e) {
      console.error("Failed to fetch data:", e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // コレクションのリアルタイム監視（completed以外のとき）
  useEffect(() => {
    if (!collection || collection.status === "completed") return;
    const unsubscribe = subscribeToCollection(collection.id, (col) => {
      if (col) {
        setCollection(col);
        // completed になったら記事一覧を再取得
        if (col.status === "completed") fetchData();
      }
    });
    return unsubscribe;
  }, [collection?.id, collection?.status, fetchData]);

  // 処理中のブックマーク記事をリアルタイム監視
  useEffect(() => {
    const pendingItems = bookmarkArticles.filter(
      (b) => b.research_status && b.research_status !== "completed"
    );
    if (pendingItems.length === 0) return;

    const unsubscribes = pendingItems.map((item) =>
      subscribeToArticle(item.id, (updated) => {
        if (!updated) return;
        setBookmarkArticles((prev) =>
          prev.map((b) => (b.id === updated.id ? updated : b))
        );
      })
    );
    return () => unsubscribes.forEach((unsub) => unsub());
  }, [bookmarkArticles.map((b) => `${b.id}:${b.research_status}`).join(",")]);

  const pickups = articles.filter((a) => a.is_pickup);
  const others = articles.filter((a) => !a.is_pickup);
  const completedBookmarks = bookmarkArticles.filter(
    (a) => !a.research_status || a.research_status === "completed"
  );
  const pendingBookmarks = bookmarkArticles.filter(
    (a) => a.research_status && a.research_status !== "completed"
  );
  const status: CollectionStatus = collection?.status ?? "completed";
  const isCollecting = status === "collecting" || status === "scoring" || status === "researching";

  const handleCollect = async () => {
    if (!user) return;
    setCollectRequesting(true);
    try {
      const res = await fetch("/api/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.uid }),
      });
      if (res.ok) {
        setCollectTriggered(true);
      } else {
        console.error("Collect request failed:", res.status);
      }
    } catch (e) {
      console.error("Failed to trigger collection:", e);
    } finally {
      setCollectRequesting(false);
    }
  };

  // コレクション作成をポーリングで検知
  useEffect(() => {
    if (!collectTriggered) return;
    const interval = setInterval(async () => {
      await fetchData();
    }, 3000);
    return () => clearInterval(interval);
  }, [collectTriggered, fetchData]);

  // コレクションが見つかったらポーリング停止
  useEffect(() => {
    if (collectTriggered && collection && collection.status !== "completed") {
      setCollectTriggered(false);
    }
  }, [collectTriggered, collection]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div
              className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
              style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
            />
            <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              ブリーフィングを読み込み中...
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Date */}
      <div
        className="text-sm mb-6"
        style={{ color: "var(--color-text-muted)" }}
      >
        {formatDate(today)}
      </div>

      {/* Title + Collect Button */}
      <div className="flex items-center justify-between mb-6">
        <h1
          className="text-3xl font-bold"
          style={{
            color: "var(--color-text-dark)",
            fontFamily: "var(--font-display)",
          }}
        >
          今日のブリーフィング
        </h1>
        <button
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium cursor-pointer border-none transition-all"
          style={{
            color: "var(--color-primary)",
            backgroundColor: "var(--color-primary-bg)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid rgba(88, 129, 87, 0.2)",
            opacity: isCollecting || collectRequesting || collectTriggered ? 0.6 : 1,
          }}
          onClick={handleCollect}
          disabled={isCollecting || collectRequesting || collectTriggered}
        >
          {isCollecting || collectTriggered ? (
            <>
              <div
                className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
                style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
              />
              実行中...
            </>
          ) : collectRequesting ? (
            <>
              <div
                className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
                style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
              />
              送信中...
            </>
          ) : (
            <>
              <Play size={16} />
              ブリーフィングを実行
            </>
          )}
        </button>
      </div>

      {/* Status — 実行中 or トリガー直後 */}
      {(status !== "completed" || collectTriggered) && (
        <div className="mb-8">
          <StatusIndicator status={collectTriggered ? "collecting" : status} />
        </div>
      )}

      {/* Empty State */}
      {articles.length === 0 && bookmarkArticles.length === 0 && (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            今日のブリーフィングはまだありません。
          </p>
          <p className="text-xs mt-2" style={{ color: "var(--color-text-muted)" }}>
            バッチ処理が完了するとここに記事が表示されます。
          </p>
        </div>
      )}

      {/* Pickup Articles */}
      {pickups.length > 0 && (
        <section className="mb-10">
          <h2
            className="text-lg font-bold mb-4 flex items-center gap-2"
            style={{ color: "var(--color-text-dark)" }}
          >
            <span
              className="inline-block w-1 h-5 rounded-full"
              style={{ backgroundColor: "var(--color-primary)" }}
            />
            ピックアップ記事
          </h2>
          <div className="flex flex-col gap-6">
            {pickups.map((article) => (
              <BriefingCard
                key={article.id}
                article={article}
              />
            ))}
          </div>
        </section>
      )}

      {/* Other Articles */}
      {others.length > 0 && (
        <section className="mb-10">
          <h2
            className="text-lg font-bold mb-4 flex items-center gap-2"
            style={{ color: "var(--color-text-dark)" }}
          >
            <span
              className="inline-block w-1 h-5 rounded-full"
              style={{ backgroundColor: "var(--color-primary-soft)" }}
            />
            その他の記事
          </h2>
          <div className="flex flex-col gap-6">
            {others.map((article) => (
              <BriefingCard
                key={article.id}
                article={article}
              />
            ))}
          </div>
        </section>
      )}

      {/* Bookmark Articles */}
      {bookmarkArticles.length > 0 && (
        <section>
          <h2
            className="text-lg font-bold mb-4 flex items-center gap-2"
            style={{ color: "var(--color-text-dark)" }}
          >
            <span
              className="inline-block w-1 h-5 rounded-full"
              style={{ backgroundColor: "var(--color-primary-soft)" }}
            />
            ブックマーク記事
          </h2>
          <div className="flex flex-col gap-6">
            {pendingBookmarks.map((article) => (
              <BookmarkPendingCard key={article.id} article={article} />
            ))}
            {completedBookmarks.map((article) => (
              <BriefingCard
                key={article.id}
                article={article}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

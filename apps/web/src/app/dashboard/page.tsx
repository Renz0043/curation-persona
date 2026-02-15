"use client";

import { useState, useEffect, useCallback } from "react";
import BriefingCard from "@/components/BriefingCard";
import StatusIndicator from "@/components/StatusIndicator";
import { useAuth } from "@/lib/auth-context";
import {
  getTodayCollection,
  getArticlesByCollection,
  getBookmarkArticles,
  subscribeToCollection,
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
      if (col) setCollection(col);
    });
    return unsubscribe;
  }, [collection?.id, collection?.status]);

  const pickups = articles.filter((a) => a.is_pickup);
  const others = articles.filter((a) => !a.is_pickup);
  const status: CollectionStatus = collection?.status ?? "completed";

  const handleRate = async (id: string, rating: number) => {
    // ローカル更新
    setArticles((prev) =>
      prev.map((a) => (a.id === id ? { ...a, user_rating: rating } : a))
    );
    setBookmarkArticles((prev) =>
      prev.map((a) => (a.id === id ? { ...a, user_rating: rating } : a))
    );

    // API経由でFirestore更新
    if (!collection) return;
    const article = [...articles, ...bookmarkArticles].find((a) => a.id === id);
    if (!article) return;
    try {
      await fetch(`/api/collections/${article.collection_id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          articleUrl: article.url,
          rating,
        }),
      });
    } catch (e) {
      console.error("Failed to save rating:", e);
    }
  };

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

      {/* Title */}
      <h1
        className="text-3xl font-bold mb-6"
        style={{
          color: "var(--color-text-dark)",
          fontFamily: "var(--font-display)",
        }}
      >
        今日のブリーフィング
      </h1>

      {/* Status — completed時は非表示 */}
      {status !== "completed" && (
        <div className="mb-8">
          <StatusIndicator status={status} />
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
                onRate={handleRate}
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
                onRate={handleRate}
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
            {bookmarkArticles.map((article) => (
              <BriefingCard
                key={article.id}
                article={article}
                onRate={handleRate}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

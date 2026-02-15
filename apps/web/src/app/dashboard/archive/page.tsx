"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Search, SlidersHorizontal, ChevronDown, X } from "lucide-react";
import DateTree, { type YearGroup } from "@/components/DateTree";
import ArchiveCard from "@/components/ArchiveCard";
import { useAuth } from "@/lib/auth-context";
import {
  getCollectionHistory,
  getArticlesByCollection,
} from "@/lib/firestore";
import type { Article, Collection } from "@/lib/types";

type Filters = {
  minScore: number | null;
  category: string | null;
};

/** コレクション一覧から DateTree 用データを構築 */
function buildDateTree(collections: Collection[]): YearGroup[] {
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const dateMap = new Map<string, boolean>();

  for (const col of collections) {
    if (col.date) {
      dateMap.set(col.date, true);
    }
  }

  const sorted = [...dateMap.keys()].sort().reverse();
  const yearMap = new Map<number, Map<number, { date: string; label: string; hasArticles: boolean }[]>>();

  for (const dateStr of sorted) {
    const d = new Date(dateStr + "T00:00:00");
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    const day = d.getDate();
    const w = weekdays[d.getDay()];

    if (!yearMap.has(year)) yearMap.set(year, new Map());
    const monthMap = yearMap.get(year)!;
    if (!monthMap.has(month)) monthMap.set(month, []);
    monthMap.get(month)!.push({
      date: dateStr,
      label: `${month}月${day}日 (${w})`,
      hasArticles: true,
    });
  }

  const result: YearGroup[] = [];
  for (const [year, monthMap] of [...yearMap.entries()].sort((a, b) => b[0] - a[0])) {
    const months = [...monthMap.entries()]
      .sort((a, b) => b[0] - a[0])
      .map(([month, dates]) => ({
        month,
        label: `${month}月`,
        dates,
      }));
    result.push({ year, months });
  }
  return result;
}

export default function ArchivePage() {
  const { user } = useAuth();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [allArticles, setAllArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"relevance" | "date" | "score">("relevance");
  const [filters, setFilters] = useState<Filters>({
    minScore: null,
    category: null,
  });

  const fetchData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const cols = await getCollectionHistory(user.uid, 60);
      // bm_ コレクションを除外
      const dailyCols = cols.filter((c) => c.date !== "");
      setCollections(dailyCols);

      // 全コレクションの記事を取得
      const articlePromises = dailyCols.map((col) => getArticlesByCollection(col.id, user.uid));
      const articleArrays = await Promise.all(articlePromises);
      setAllArticles(articleArrays.flat());
    } catch (e) {
      console.error("Failed to fetch archive:", e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const dateTree = useMemo(() => buildDateTree(collections), [collections]);

  // コレクションIDから日付を引くためのマップ
  const collectionDateMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const col of collections) {
      map.set(col.id, col.date);
    }
    return map;
  }, [collections]);

  const filteredArticles = useMemo(() => {
    let results = allArticles;

    // 日付フィルタ
    if (selectedDate) {
      results = results.filter(
        (a) => collectionDateMap.get(a.collection_id) === selectedDate
      );
    }

    // 検索クエリ
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          (a.content ?? "").toLowerCase().includes(q) ||
          a.source.toLowerCase().includes(q)
      );
    }

    // スコアフィルタ
    if (filters.minScore !== null) {
      results = results.filter((a) => a.relevance_score >= filters.minScore!);
    }

    // カテゴリフィルタ
    if (filters.category) {
      results = results.filter((a) => a.source_type === filters.category);
    }

    // ソート
    if (sortBy === "date") {
      results = [...results].sort(
        (a, b) =>
          (b.published_at?.getTime() ?? 0) - (a.published_at?.getTime() ?? 0)
      );
    } else if (sortBy === "score") {
      results = [...results].sort((a, b) => b.relevance_score - a.relevance_score);
    }

    return results;
  }, [allArticles, selectedDate, searchQuery, sortBy, filters, collectionDateMap]);

  const removeFilter = (key: keyof Filters) => {
    setFilters((prev) => ({ ...prev, [key]: null }));
  };

  const categories = useMemo(
    () => [...new Set(allArticles.map((a) => a.source_type))],
    [allArticles]
  );

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
            style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
          />
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            アーカイブを読み込み中...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Date Tree Sidebar */}
      <div
        className="w-48 shrink-0 border-r"
        style={{ borderColor: "var(--color-border)" }}
      >
        <DateTree
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          data={dateTree}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 max-w-4xl mx-auto px-8 py-6">
        {/* Header */}
        <div
          className="sticky top-0 pb-4 z-10"
          style={{ backgroundColor: "var(--color-bg)" }}
        >
          {/* Title & Status */}
          <div className="flex items-center justify-between mb-4">
            <h1
              className="text-2xl font-bold m-0"
              style={{
                color: "var(--color-text-dark)",
                fontFamily: "var(--font-display)",
              }}
            >
              アーカイブ検索
            </h1>
          </div>

          {/* Search Bar */}
          <div className="relative mb-3">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: "var(--color-text-muted)" }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="トピック、キーワード、またはソースで検索..."
              className="w-full pl-10 pr-10 py-2.5 text-sm outline-none transition-all duration-200"
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-lg)",
                backgroundColor: "var(--color-bg)",
                color: "var(--color-text-dark)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
                e.currentTarget.style.boxShadow = "0 0 0 2px var(--color-primary-bg)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
            <SlidersHorizontal
              size={16}
              className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer"
              style={{ color: "var(--color-text-muted)" }}
            />
          </div>

          {/* Filter Chips */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Min Score filter */}
            {filters.minScore !== null ? (
              <button
                onClick={() => removeFilter("minScore")}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border-none cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: "var(--color-primary-bg)",
                  color: "var(--color-primary)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                スコア ≥ {Math.round(filters.minScore * 100)}
                <X size={12} />
              </button>
            ) : (
              <button
                onClick={() => setFilters((prev) => ({ ...prev, minScore: 0.8 }))}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: "var(--color-bg)",
                  color: "var(--color-text-muted)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                スコア
                <ChevronDown size={12} />
              </button>
            )}

            {/* Category filter */}
            {filters.category !== null ? (
              <button
                onClick={() => removeFilter("category")}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border-none cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: "var(--color-primary-bg)",
                  color: "var(--color-primary)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                {filters.category}
                <X size={12} />
              </button>
            ) : (
              <div className="relative">
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      setFilters((prev) => ({ ...prev, category: e.target.value }));
                    }
                  }}
                  value=""
                  className="appearance-none px-3 py-1.5 pr-7 text-xs font-medium cursor-pointer"
                  style={{
                    backgroundColor: "var(--color-bg)",
                    color: "var(--color-text-muted)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-full)",
                  }}
                >
                  <option value="">カテゴリ</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={12}
                  className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                  style={{ color: "var(--color-text-muted)" }}
                />
              </div>
            )}

            {/* Selected date chip */}
            {selectedDate && (
              <button
                onClick={() => setSelectedDate(null)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border-none cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: "var(--color-primary-bg)",
                  color: "var(--color-primary)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                {selectedDate}
                <X size={12} />
              </button>
            )}
          </div>
        </div>

        {/* Results Header */}
        <div className="flex justify-between items-center mb-4 mt-2">
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            検索結果 ({filteredArticles.length}件)
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "relevance" | "date" | "score")}
            className="text-sm px-3 py-1.5 cursor-pointer"
            style={{
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--color-bg)",
              color: "var(--color-text-dark)",
            }}
          >
            <option value="relevance">関連度順</option>
            <option value="date">日付順</option>
            <option value="score">AIスコア順</option>
          </select>
        </div>

        {/* Article List */}
        <div className="flex flex-col gap-4">
          {filteredArticles.map((article) => (
            <ArchiveCard key={article.id} article={article} />
          ))}
        </div>

        {/* Empty State */}
        {filteredArticles.length === 0 && (
          <div className="text-center py-12">
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              条件に一致する記事が見つかりませんでした。
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

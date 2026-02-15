"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import {
  Search,
  ChevronDown,
  X,
  Calendar as CalendarIcon,
} from "lucide-react";
import CalendarPicker from "@/components/CalendarPicker";
import ArchiveCard from "@/components/ArchiveCard";
import { useAuth } from "@/lib/auth-context";
import {
  getCollectionHistory,
  getArticlesByCollection,
  getBookmarkArticles,
} from "@/lib/firestore";
import type { Article, Collection } from "@/lib/types";

type Filters = {
  minScore: number | null;
  category: string | null;
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  rss: "RSS",
  website: "Website",
  newsletter: "Newsletter",
  api: "API",
  bookmark: "ブックマーク",
};

export default function ArchivePage() {
  const { user } = useAuth();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [allArticles, setAllArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"relevance" | "date" | "score">(
    "relevance"
  );
  const [filters, setFilters] = useState<Filters>({
    minScore: 0.8,
    category: null,
  });
  const [scoreInput, setScoreInput] = useState("80");
  const [showCalendar, setShowCalendar] = useState(false);
  const calendarRef = useRef<HTMLDivElement>(null);

  // カレンダー外クリックで閉じる
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        calendarRef.current &&
        !calendarRef.current.contains(e.target as Node)
      ) {
        setShowCalendar(false);
      }
    };
    if (showCalendar) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showCalendar]);

  const fetchData = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const cols = await getCollectionHistory(user.uid, 60);
      const dailyCols = cols.filter((c) => c.date !== "");
      setCollections(dailyCols);

      // デイリー記事 + ブックマーク記事を同時取得
      const [articleArrays, bookmarkArticles] = await Promise.all([
        Promise.all(
          dailyCols.map((col) => getArticlesByCollection(col.id, user.uid))
        ),
        getBookmarkArticles(user.uid),
      ]);
      setAllArticles([...articleArrays.flat(), ...bookmarkArticles]);
    } catch (e) {
      console.error("Failed to fetch archive:", e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // コレクションIDから日付を引くためのマップ
  const collectionDateMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const col of collections) {
      map.set(col.id, col.date);
    }
    return map;
  }, [collections]);

  // カレンダーに渡す「記事がある日付」のSet
  const availableDates = useMemo(() => {
    const dates = new Set<string>();
    for (const col of collections) {
      if (col.date) dates.add(col.date);
    }
    return dates;
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
      results = [...results].sort(
        (a, b) => b.relevance_score - a.relevance_score
      );
    }

    return results;
  }, [allArticles, selectedDate, searchQuery, sortBy, filters, collectionDateMap]);

  const removeFilter = (key: keyof Filters) => {
    setFilters((prev) => ({ ...prev, [key]: null }));
    if (key === "minScore") setScoreInput("");
  };

  const handleScoreInputChange = (value: string) => {
    setScoreInput(value);
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 0 && num <= 100) {
      setFilters((prev) => ({ ...prev, minScore: num / 100 }));
    } else if (value === "") {
      setFilters((prev) => ({ ...prev, minScore: null }));
    }
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
            style={{
              borderColor: "var(--color-primary)",
              borderTopColor: "transparent",
            }}
          />
          <span
            className="text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            アーカイブを読み込み中...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-8 py-6">
      {/* Header */}
      <div
        className="sticky top-0 pb-4 z-10"
        style={{ backgroundColor: "var(--color-bg)" }}
      >
        {/* Title */}
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
            className="w-full pl-10 pr-4 py-2.5 text-sm outline-none transition-all duration-200"
            style={{
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-lg)",
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

        {/* Filter Chips */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Score filter — editable */}
          {filters.minScore !== null ? (
            <div
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium"
              style={{
                backgroundColor: "var(--color-primary-bg)",
                color: "var(--color-primary)",
                borderRadius: "var(--radius-full)",
              }}
            >
              <span>スコア ≥</span>
              <input
                type="number"
                min={0}
                max={100}
                value={scoreInput}
                onChange={(e) => handleScoreInputChange(e.target.value)}
                className="w-10 text-center text-xs font-semibold bg-transparent border-none outline-none"
                style={{ color: "var(--color-primary)" }}
              />
              <button
                onClick={() => removeFilter("minScore")}
                className="bg-transparent border-none cursor-pointer p-0 flex items-center"
                style={{ color: "var(--color-primary)" }}
              >
                <X size={12} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setScoreInput("80");
                setFilters((prev) => ({ ...prev, minScore: 0.8 }));
              }}
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
              {SOURCE_TYPE_LABELS[filters.category] ?? filters.category}
              <X size={12} />
            </button>
          ) : (
            <div className="relative">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    setFilters((prev) => ({
                      ...prev,
                      category: e.target.value,
                    }));
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
                    {SOURCE_TYPE_LABELS[cat] ?? cat}
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

          {/* Date filter — calendar toggle */}
          <div className="relative" ref={calendarRef}>
            {selectedDate ? (
              <button
                onClick={() => setSelectedDate(null)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border-none cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: "var(--color-primary-bg)",
                  color: "var(--color-primary)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                <CalendarIcon size={12} />
                {selectedDate}
                <X size={12} />
              </button>
            ) : (
              <button
                onClick={() => setShowCalendar((v) => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium cursor-pointer transition-colors duration-150"
                style={{
                  backgroundColor: showCalendar
                    ? "var(--color-primary-bg)"
                    : "var(--color-bg)",
                  color: showCalendar
                    ? "var(--color-primary)"
                    : "var(--color-text-muted)",
                  border: `1px solid ${showCalendar ? "var(--color-primary-soft)" : "var(--color-border)"}`,
                  borderRadius: "var(--radius-full)",
                }}
              >
                <CalendarIcon size={12} />
                日付
                <ChevronDown size={12} />
              </button>
            )}

            {/* Calendar dropdown */}
            {showCalendar && (
              <div
                className="absolute top-full left-0 mt-2 z-20"
                style={{
                  boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
                  borderRadius: "var(--radius-lg)",
                }}
              >
                <CalendarPicker
                  selectedDate={selectedDate}
                  onSelectDate={(date) => {
                    setSelectedDate(date);
                    setShowCalendar(false);
                  }}
                  availableDates={availableDates}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex justify-between items-center mb-4 mt-2">
        <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
          検索結果 ({filteredArticles.length}件)
        </span>
        <select
          value={sortBy}
          onChange={(e) =>
            setSortBy(e.target.value as "relevance" | "date" | "score")
          }
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
          <p
            className="text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            条件に一致する記事が見つかりませんでした。
          </p>
        </div>
      )}
    </div>
  );
}

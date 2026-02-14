"use client";

import { useState, useMemo } from "react";
import { Search, SlidersHorizontal, ChevronDown, X } from "lucide-react";
import DateTree from "@/components/DateTree";
import ArchiveCard, { ArchiveArticle } from "@/components/ArchiveCard";

// モックデータ
const mockArchiveArticles: ArchiveArticle[] = [
  {
    id: "1",
    title: "生成AIの次なるフロンティア：企業におけるエージェント型ワークフロー",
    url: "https://example.com/article-1",
    source: "TechCrunch",
    source_type: "AI",
    published_at: "2025-01-15",
    relevance_score: 0.98,
    content:
      "大規模言語モデル（LLM）が単にテキストを生成するだけでなく、多段階のワークフローを能動的に計画・実行可能にする新しいフレームワークが登場しています。主要企業は、複雑なデータ分析や自動レポート作成のために、これらのエージェントシステムを試験的に導入し始めています。",
    has_deep_dive: true,
  },
  {
    id: "2",
    title: "グリッドストレージ向け全固体電池の効率化におけるブレークスルー",
    url: "https://example.com/article-2",
    source: "Nature Energy",
    source_type: "気候テック",
    published_at: "2025-01-15",
    relevance_score: 0.85,
    content:
      "研究者らは、より高い温度での安定性を維持する新しい電解質組成を実証しました。これにより、大規模なユーティリティストレージへの全固体電池配備における主要なボトルネックの1つが解決される可能性があります。",
    has_deep_dive: true,
  },
  {
    id: "3",
    title: "東南アジアにおける半導体サプライチェーンの多様化が加速",
    url: "https://example.com/article-3",
    source: "Bloomberg",
    source_type: "市場分析",
    published_at: "2025-01-14",
    relevance_score: 0.72,
    content:
      "大手チップメーカーが単一ソースの生産拠点への依存を減らそうとする中、ベトナムとマレーシアで記録的な投資が行われています。この変化は新たな物流回廊を生み出し、政策変更を促しています。",
    has_deep_dive: false,
  },
  {
    id: "4",
    title: "プロンプトエンジニアリングの進化：構造化推論フレームワークの台頭",
    url: "https://example.com/article-4",
    source: "arXiv",
    source_type: "AI",
    published_at: "2025-01-14",
    relevance_score: 0.65,
    content:
      "Chain-of-Thoughtを超えた新しいプロンプティング手法が提案され、複雑な推論タスクにおいて従来手法を上回る性能を示しています。特にマルチステップの計画立案においてその効果が顕著です。",
    has_deep_dive: false,
  },
  {
    id: "5",
    title: "欧州デジタル市場法の施行1年：プラットフォーム規制の現在地",
    url: "https://example.com/article-5",
    source: "Financial Times",
    source_type: "規制",
    published_at: "2025-01-12",
    relevance_score: 0.58,
    content:
      "DMA施行から1年が経過し、大手テック企業のコンプライアンス対応が本格化しています。相互運用性要件やデータポータビリティに関する具体的な変化が見え始めています。",
    has_deep_dive: false,
  },
  {
    id: "6",
    title: "量子コンピューティングのエラー訂正：最新の実験結果",
    url: "https://example.com/article-6",
    source: "Science",
    source_type: "AI",
    published_at: "2025-01-12",
    relevance_score: 0.91,
    content:
      "Googleの研究チームが論理量子ビットのエラー率を物理量子ビット以下に抑えることに成功しました。これはフォールトトレラント量子コンピュータ実現への重要なマイルストーンとなります。",
    has_deep_dive: true,
  },
  {
    id: "7",
    title: "リモートワーク時代のオフィス再設計：ハイブリッド型ワークスペースの最前線",
    url: "https://example.com/article-7",
    source: "Wired",
    source_type: "ビジネス",
    published_at: "2025-01-11",
    relevance_score: 0.45,
    content:
      "パンデミック後のオフィス回帰が進む中、企業はコラボレーションスペースとフォーカスエリアを組み合わせた新しいオフィスレイアウトを模索しています。",
    has_deep_dive: false,
  },
  {
    id: "8",
    title: "マルチモーダルAIの医療診断への応用：放射線画像解析の新手法",
    url: "https://example.com/article-8",
    source: "The Lancet",
    source_type: "AI",
    published_at: "2025-01-11",
    relevance_score: 0.88,
    content:
      "テキストと画像を統合的に処理するマルチモーダルモデルが、放射線科医の診断精度を補助する新しいアプローチとして注目されています。臨床試験では有望な結果が報告されています。",
    has_deep_dive: true,
  },
  {
    id: "9",
    title: "サステナブルファッション：循環型経済モデルへの転換",
    url: "https://example.com/article-9",
    source: "Nikkei",
    source_type: "気候テック",
    published_at: "2025-01-10",
    relevance_score: 0.52,
    content:
      "ファストファッション業界が持続可能性への圧力に直面する中、素材リサイクルとレンタルモデルを軸とした循環型ビジネスモデルが急速に成長しています。",
    has_deep_dive: false,
  },
  {
    id: "10",
    title: "自律走行技術の法的枠組み：各国の規制動向比較",
    url: "https://example.com/article-10",
    source: "Reuters",
    source_type: "規制",
    published_at: "2025-01-10",
    relevance_score: 0.62,
    content:
      "レベル4自律走行車の公道走行を認める法案が複数の国で審議されています。安全基準、責任の所在、保険制度の整備が主要な論点となっています。",
    has_deep_dive: false,
  },
];

type Filters = {
  minScore: number | null;
  category: string | null;
};

export default function ArchivePage() {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"relevance" | "date" | "score">("relevance");
  const [filters, setFilters] = useState<Filters>({
    minScore: 0.8,
    category: null,
  });

  const filteredArticles = useMemo(() => {
    let results = mockArchiveArticles;

    // 日付フィルタ
    if (selectedDate) {
      results = results.filter((a) => a.published_at === selectedDate);
    }

    // 検索クエリ
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.content.toLowerCase().includes(q) ||
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
        (a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      );
    } else if (sortBy === "score") {
      results = [...results].sort((a, b) => b.relevance_score - a.relevance_score);
    }

    return results;
  }, [selectedDate, searchQuery, sortBy, filters]);

  const removeFilter = (key: keyof Filters) => {
    setFilters((prev) => ({ ...prev, [key]: null }));
  };

  const categories = [...new Set(mockArchiveArticles.map((a) => a.source_type))];

  return (
    <div className="flex min-h-screen">
      {/* Date Tree Sidebar */}
      <div
        className="w-48 shrink-0 border-r"
        style={{ borderColor: "var(--color-border)" }}
      >
        <DateTree selectedDate={selectedDate} onSelectDate={setSelectedDate} />
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
            <div className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-muted)" }}>
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: "var(--color-positive)" }}
              />
              データベース更新: 10分前
            </div>
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

        {/* Load More */}
        {filteredArticles.length > 0 && (
          <div className="text-center py-6">
            <button
              className="flex items-center gap-1.5 mx-auto text-sm font-medium bg-transparent border-none cursor-pointer transition-colors duration-150"
              style={{ color: "var(--color-text-muted)" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--color-primary)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--color-text-muted)";
              }}
            >
              もっと読み込む
              <ChevronDown size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

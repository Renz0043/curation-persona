"use client";

import { useState } from "react";
import BriefingCard, { Article } from "@/components/BriefingCard";
import StatusIndicator from "@/components/StatusIndicator";

// モックデータ
const mockArticles: Article[] = [
  {
    id: "1",
    title: "生成AIの次なるフロンティア：企業におけるエージェント型ワークフロー",
    url: "https://example.com/article-1",
    source: "TechCrunch",
    source_type: "AI",
    published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    relevance_score: 0.98,
    relevance_reason:
      "あなたの「自律型エージェント」への関心に非常に高く関連しています。この記事では、チャットベースのインターフェースからエージェントベースの実行モデルへの移行について議論しており、現在のリサーチプロジェクトに直接合致します。",
    is_pickup: true,
    content:
      "大規模言語モデル（LLM）が単にテキストを生成するだけでなく、多段階のワークフローを能動的に計画・実行可能にする新しいフレームワークが登場しています。主要企業は、複雑なデータ分析や自動レポート作成のために、これらのエージェントシステムを試験的に導入し始めています。",
    og_image: "https://picsum.photos/seed/ai-agents/800/400",
    user_rating: 5,
  },
  {
    id: "2",
    title: "グリッドストレージ向け全固体電池の効率化におけるブレークスルー",
    url: "https://example.com/article-2",
    source: "Nature Energy",
    source_type: "気候テック",
    published_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    relevance_score: 0.85,
    relevance_reason:
      "あなたの二次的な関心事である「持続可能なエネルギーインフラ」に一致します。この論文の技術的な深さは、以前に読まれたグリッド安定性に関する文献を補完するものです。",
    is_pickup: true,
    content:
      "研究者らは、より高い温度での安定性を維持する新しい電解質組成を実証しました。これにより、大規模なユーティリティストレージへの全固体電池配備における主要なボトルネックの1つが解決される可能性があります。",
    og_image: "https://picsum.photos/seed/battery-tech/800/400",
    user_rating: 4,
  },
  {
    id: "3",
    title: "東南アジアにおける半導体サプライチェーンの多様化が加速",
    url: "https://example.com/article-3",
    source: "Bloomberg",
    source_type: "市場分析",
    published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
    relevance_score: 0.72,
    relevance_reason:
      "ある程度関連しています。地域のサプライチェーンを明確に追跡しているわけではありませんが、これはあなたの主な関心事であるAIインフラのハードウェア可用性に影響を与えます。",
    is_pickup: false,
    content:
      "大手チップメーカーが単一ソースの生産拠点への依存を減らそうとする中、ベトナムとマレーシアで記録的な投資が行われています。この変化は新たな物流回廊を生み出し、政策変更を促しています。",
  },
  {
    id: "4",
    title: "プロンプトエンジニアリングの進化：構造化推論フレームワークの台頭",
    url: "https://example.com/article-4",
    source: "arXiv",
    source_type: "AI",
    published_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    relevance_score: 0.65,
    relevance_reason:
      "プロンプト設計とLLMの活用方法に関する最新の研究です。あなたのAIエージェント開発の実践に間接的に役立つ可能性があります。",
    is_pickup: false,
    content:
      "Chain-of-Thoughtを超えた新しいプロンプティング手法が提案され、複雑な推論タスクにおいて従来手法を上回る性能を示しています。特にマルチステップの計画立案においてその効果が顕著です。",
  },
  {
    id: "5",
    title: "欧州デジタル市場法の施行1年：プラットフォーム規制の現在地",
    url: "https://example.com/article-5",
    source: "Financial Times",
    source_type: "規制",
    published_at: new Date(Date.now() - 15 * 60 * 60 * 1000).toISOString(),
    relevance_score: 0.58,
    relevance_reason:
      "テック規制の動向は、AI開発の方向性に間接的な影響を与えます。グローバルなプラットフォーム規制の枠組みを把握しておくことは有益です。",
    is_pickup: false,
    content:
      "DMA施行から1年が経過し、大手テック企業のコンプライアンス対応が本格化しています。相互運用性要件やデータポータビリティに関する具体的な変化が見え始めています。",
  },
];

function formatDate(date: Date): string {
  const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  const d = date.getDate();
  const w = weekdays[date.getDay()];
  return `${y}年${m}月${d}日（${w}）`;
}

export default function DashboardPage() {
  const [articles, setArticles] = useState(mockArticles);
  const today = new Date();

  const pickups = articles.filter((a) => a.is_pickup);
  const others = articles.filter((a) => !a.is_pickup);

  const handleRate = (id: string, rating: number) => {
    setArticles((prev) =>
      prev.map((a) => (a.id === id ? { ...a, user_rating: rating } : a))
    );
  };

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

      {/* Status */}
      <div className="mb-8">
        <StatusIndicator status="completed" />
      </div>

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
        <section>
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
    </div>
  );
}

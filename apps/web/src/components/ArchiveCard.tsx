"use client";

import Link from "next/link";

export type ArchiveArticle = {
  id: string;
  title: string;
  url: string;
  source: string;
  source_type: string;
  published_at: string;
  relevance_score: number;
  content: string;
  has_deep_dive: boolean;
};

type ArchiveCardProps = {
  article: ArchiveArticle;
};

export default function ArchiveCard({ article }: ArchiveCardProps) {
  const scorePercent = Math.round(article.relevance_score * 100);

  return (
    <Link
      href={`/article/${article.id}`}
      className="block no-underline transition-all duration-200"
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--spacing-xl)",
        backgroundColor: "var(--color-bg)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--color-card-hover)";
        e.currentTarget.style.borderColor = "var(--color-primary-soft)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "var(--color-bg)";
        e.currentTarget.style.borderColor = "var(--color-border)";
      }}
    >
      {/* Header */}
      <div className="flex justify-between items-center mb-2">
        <div
          className="flex items-center gap-2 text-xs"
          style={{ color: "var(--color-text-muted)" }}
        >
          <span
            className="px-2 py-0.5 text-xs font-semibold"
            style={{
              backgroundColor: "var(--color-primary-bg)",
              color: "var(--color-primary)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            {article.source_type}
          </span>
          <span>•</span>
          <span>{article.source}</span>
          <span>•</span>
          <span>{article.published_at}</span>
        </div>
        <span
          className="text-xs font-medium px-2 py-0.5"
          style={{
            backgroundColor: "var(--color-primary-bg)",
            color: "var(--color-primary)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          AIスコア: {scorePercent}
        </span>
      </div>

      {/* Title */}
      <h3
        className="text-base font-bold mb-2 m-0 transition-colors duration-150"
        style={{ color: "var(--color-text-dark)" }}
      >
        {article.title}
      </h3>

      {/* Content preview */}
      <p
        className="text-sm leading-relaxed line-clamp-2 m-0"
        style={{ color: "var(--color-text-muted)" }}
      >
        {article.content}
      </p>
    </Link>
  );
}

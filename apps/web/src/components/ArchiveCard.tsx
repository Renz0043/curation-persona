"use client";

import Link from "next/link";
import { Star } from "lucide-react";
import type { Article } from "@/lib/types";

type ArchiveCardProps = {
  article: Article;
};

export default function ArchiveCard({ article }: ArchiveCardProps) {
  const dateStr = article.published_at
    ? article.published_at.toISOString().slice(0, 10)
    : "";

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
          {dateStr && (
            <>
              <span>•</span>
              <span>{dateStr}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {article.user_rating && (
            <span
              className="flex items-center gap-1 text-xs font-medium px-2 py-0.5"
              style={{
                color: "#d97706",
                backgroundColor: "#fef3c7",
                borderRadius: "var(--radius-sm)",
              }}
            >
              <Star size={10} fill="#d97706" stroke="#d97706" />
              {article.user_rating}
            </span>
          )}
          <span
            className="text-xs font-medium px-2 py-0.5"
            style={{
              backgroundColor: "var(--color-primary-bg)",
              color: "var(--color-primary)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            関連度: {article.relevance_score.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Title */}
      <h3
        className="text-base font-bold mb-2 m-0 transition-colors duration-150"
        style={{ color: "var(--color-text-dark)" }}
      >
        {article.title}
      </h3>

      {/* Content preview */}
      {(article.meta_description || article.content) && (
        <p
          className="text-sm leading-relaxed line-clamp-2 m-0"
          style={{ color: "var(--color-text-muted)" }}
        >
          {article.meta_description || article.content}
        </p>
      )}

      {/* Detail link */}
      <div className="flex justify-end mt-3">
        <span
          className="text-xs font-medium"
          style={{ color: "var(--color-primary)" }}
        >
          詳細を見る →
        </span>
      </div>
    </Link>
  );
}

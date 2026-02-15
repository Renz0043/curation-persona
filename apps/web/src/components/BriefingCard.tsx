"use client";

import Link from "next/link";
import { Sparkles, ExternalLink, Search } from "lucide-react";
import ScoreBar from "./ScoreBar";
import StarRating from "./StarRating";
import type { Article } from "@/lib/types";

type BriefingCardProps = {
  article: Article;
  onRate?: (id: string, rating: number) => void;
};

export default function BriefingCard({ article, onRate }: BriefingCardProps) {
  const timeAgo = article.published_at
    ? getTimeAgo(article.published_at)
    : "";

  return (
    <article
      className="transition-all duration-200"
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--spacing-xl)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--color-card-hover)";
        e.currentTarget.style.borderColor = "var(--color-primary-soft)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "";
        e.currentTarget.style.borderColor = "var(--color-border)";
      }}
    >
      {/* Header: Meta + Score */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2 text-xs" style={{ color: "var(--color-text-muted)" }}>
          <span
            className="px-2 py-1 text-xs font-semibold"
            style={{
              backgroundColor: "var(--color-primary-bg)",
              color: "var(--color-primary)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            {article.source_type}
          </span>
          <span>{article.source}</span>
          {timeAgo && (
            <>
              <span>•</span>
              <span>{timeAgo}</span>
            </>
          )}
        </div>
        <div className="text-right w-24">
          <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>
            関連度
          </span>
          <ScoreBar score={article.relevance_score} />
        </div>
      </div>

      {/* OGP Image */}
      {article.og_image && (
        <div
          className="mb-3 overflow-hidden"
          style={{
            borderRadius: "var(--radius-md)",
            aspectRatio: "16 / 9",
            backgroundColor: "var(--color-primary-bg)",
          }}
        >
          <img
            src={article.og_image}
            alt=""
            className="w-full h-full object-contain"
          />
        </div>
      )}

      {/* Title */}
      <h2
        className="text-lg font-bold mb-3"
        style={{ color: "var(--color-text-dark)" }}
      >
        {article.title}
      </h2>

      {/* Content Preview */}
      {article.content && (
        <p
          className="text-sm leading-relaxed mb-4 line-clamp-3"
          style={{ color: "var(--color-text-dark)" }}
        >
          {article.content}
        </p>
      )}

      {/* Relevance Reason */}
      {article.relevance_reason && (
        <div
          className="mb-4 text-sm leading-relaxed"
          style={{
            backgroundColor: "#F9FAFB",
            borderLeft: "3px solid var(--color-primary-soft)",
            padding: "var(--spacing-md)",
            borderRadius: "var(--radius-sm)",
          }}
        >
          <div
            className="flex items-center gap-1.5 font-semibold mb-1"
            style={{ color: "var(--color-primary)" }}
          >
            <Sparkles size={14} />
            <span>AIの選定理由</span>
          </div>
          <p style={{ color: "var(--color-text-muted)" }}>
            {article.relevance_reason}
          </p>
        </div>
      )}

      {/* Star Rating */}
      <div className="mb-4">
        <StarRating
          value={article.user_rating ?? 0}
          onChange={(v) => onRate?.(article.id, v)}
        />
      </div>

      {/* Footer */}
      <div
        className="flex justify-between items-center pt-3"
        style={{ borderTop: "1px solid var(--color-border)" }}
      >
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-sm font-semibold no-underline"
          style={{ color: "var(--color-primary)" }}
        >
          <ExternalLink size={14} />
          原文を読む
        </a>
        <Link
          href={`/article/${article.id}`}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-colors no-underline"
          style={{
            backgroundColor: "var(--color-primary-bg)",
            color: "var(--color-primary)",
            border: "1px solid var(--color-primary-soft)",
            borderRadius: "var(--radius-md)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-primary)";
            e.currentTarget.style.color = "white";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-primary-bg)";
            e.currentTarget.style.color = "var(--color-primary)";
          }}
        >
          <Search size={14} />
          深掘りリサーチ
        </Link>
      </div>
    </article>
  );
}

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) return "たった今";
  if (diffHours < 24) return `${diffHours}時間前`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}日前`;
}

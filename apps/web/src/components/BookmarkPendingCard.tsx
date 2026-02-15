"use client";

import { Loader2, ExternalLink } from "lucide-react";
import type { Article } from "@/lib/types";

type BookmarkPendingCardProps = {
  article: Article;
};

export default function BookmarkPendingCard({ article }: BookmarkPendingCardProps) {
  return (
    <article
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--spacing-xl)",
      }}
    >
      {/* Title */}
      <h2
        className="text-lg font-bold mb-2"
        style={{ color: "var(--color-text-dark)" }}
      >
        {article.title || article.url}
      </h2>

      {/* URL */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-1.5 text-xs no-underline mb-4"
        style={{ color: "var(--color-text-muted)" }}
      >
        <ExternalLink size={12} />
        {article.source}
      </a>

      {/* Status Badge */}
      <div
        className="flex items-center gap-2 px-4 py-3 text-sm"
        style={{
          borderRadius: "var(--radius-md)",
          backgroundColor: "rgba(196, 164, 106, 0.1)",
          color: "#c4a46a",
        }}
      >
        <Loader2 size={16} className="animate-spin" />
        エージェントによるリサーチ中...
      </div>
    </article>
  );
}

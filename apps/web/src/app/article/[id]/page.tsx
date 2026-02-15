"use client";

import { useState, useEffect } from "react";
import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Sparkles,
  ExternalLink,
  CalendarDays,
  Newspaper,
  ChevronDown,
  FileText,
  Brain,
  Factory,
  MessageSquare,
} from "lucide-react";
import StarRating from "@/components/StarRating";
import { useAuth } from "@/lib/auth-context";
import { subscribeToArticle } from "@/lib/firestore";
import type { Article } from "@/lib/types";

function formatPublishedAt(date?: Date): string {
  if (!date) return "";
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  const d = date.getDate();
  return `${y}年${m}月${d}日`;
}

export default function ArticleDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  useAuth();
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [feedbackSending, setFeedbackSending] = useState(false);

  useEffect(() => {
    const unsub = subscribeToArticle(id, (art) => {
      setArticle(art);
      if (art?.user_rating) setRating(art.user_rating);
      setLoading(false);
    });
    return () => unsub();
  }, [id]);

  const handleSendFeedback = async () => {
    if (!article) return;
    setFeedbackSending(true);
    try {
      await fetch(`/api/collections/${article.collection_id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          articleUrl: article.url,
          rating,
          comment: comment || undefined,
        }),
      });
    } catch (e) {
      console.error("Failed to send feedback:", e);
    } finally {
      setFeedbackSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
            style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
          />
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            記事を読み込み中...
          </span>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p style={{ color: "var(--color-text-muted)" }}>記事が見つかりませんでした</p>
        <Link
          href="/dashboard"
          className="text-sm no-underline"
          style={{ color: "var(--color-primary)" }}
        >
          ブリーフィングに戻る
        </Link>
      </div>
    );
  }

  const hasDeepDive = !!article.deep_dive_report;
  const hasCrossIndustry = !!article.cross_industry_feedback?.perspectives?.length;
  const researchStatusLabel =
    article.research_status === "completed"
      ? "調査完了"
      : article.research_status === "researching"
        ? "調査中..."
        : article.research_status === "pending"
          ? "調査待ち"
          : "未調査";

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header Nav */}
      <nav
        className="sticky top-0 z-50"
        style={{
          backgroundColor: "rgba(255,255,255,0.8)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid var(--color-border-light)",
        }}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between h-16 items-center">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-sm font-medium no-underline transition-colors"
              style={{ color: "var(--color-text-muted)" }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "var(--color-primary)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "var(--color-text-muted)")
              }
            >
              <ArrowLeft size={20} />
              ブリーフィングに戻る
            </Link>
            <div className="flex items-center gap-3">
              <button
                className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white transition-all cursor-pointer border-none"
                style={{
                  backgroundColor: "var(--color-primary)",
                  borderRadius: "var(--radius-lg)",
                  opacity: 0.5,
                }}
                disabled
              >
                <Sparkles size={20} />
                カスタムレポート生成
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 py-12 px-6 max-w-6xl mx-auto w-full">
        {/* Header Section */}
        <header className="mb-16">
          <div className="flex flex-col gap-6">
            {/* Status + Meta */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
              <span
                className="inline-flex items-center gap-2 pl-2 pr-3 py-1 text-xs font-semibold"
                style={{
                  backgroundColor: "var(--color-primary-bg)",
                  color: "var(--color-primary)",
                  borderRadius: "var(--radius-full)",
                  border: "1px solid rgba(88, 129, 87, 0.2)",
                }}
              >
                <span className="relative flex h-2 w-2">
                  <span
                    className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
                    style={{ backgroundColor: "var(--color-primary)" }}
                  />
                  <span
                    className="relative inline-flex rounded-full h-2 w-2"
                    style={{ backgroundColor: "var(--color-primary)" }}
                  />
                </span>
                {researchStatusLabel}
              </span>
              <div
                className="flex items-center gap-4 text-sm"
                style={{ color: "var(--color-text-muted)" }}
              >
                {article.published_at && (
                  <span className="flex items-center gap-1.5">
                    <CalendarDays size={18} />
                    {formatPublishedAt(article.published_at)}
                  </span>
                )}
                <span
                  className="w-1 h-1 rounded-full"
                  style={{ backgroundColor: "var(--color-border)" }}
                />
                <span className="flex items-center gap-1.5">
                  <Newspaper size={18} />
                  {article.source}
                </span>
              </div>
            </div>

            {/* Title */}
            <h1
              className="text-4xl font-bold leading-tight max-w-4xl"
              style={{
                color: "var(--color-text-dark)",
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.01em",
              }}
            >
              {article.title}
            </h1>

            {/* Score Metrics */}
            <div
              className="mt-4 pt-8 max-w-xs"
              style={{ borderTop: "1px solid var(--color-border-light)" }}
            >
              <div className="flex justify-between items-end mb-2">
                <span
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  Relevance Score
                </span>
                <span
                  className="text-2xl font-bold tabular-nums"
                  style={{ color: "var(--color-primary)" }}
                >
                  {article.relevance_score.toFixed(2)}
                </span>
              </div>
              <div
                className="w-full overflow-hidden"
                style={{
                  height: "8px",
                  backgroundColor: "var(--color-border-light)",
                  borderRadius: "var(--radius-full)",
                }}
              >
                <div
                  className="transition-all duration-1000 ease-out"
                  style={{
                    width: `${Math.round(article.relevance_score * 100)}%`,
                    height: "100%",
                    backgroundColor: "var(--color-primary)",
                    borderRadius: "var(--radius-full)",
                  }}
                />
              </div>
            </div>
          </div>
        </header>

        {/* Grid: Main + Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Main Content Column */}
          <div className={hasCrossIndustry ? "lg:col-span-8" : "lg:col-span-12"}>
            {/* Original Article Section */}
            <section className="mb-12">
              <div
                className="flex items-center justify-between mb-8 pb-4"
                style={{ borderBottom: "1px solid var(--color-border-light)" }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="flex items-center justify-center w-8 h-8 rounded-full"
                    style={{
                      backgroundColor: "var(--color-border-light)",
                      color: "var(--color-text-dark)",
                    }}
                  >
                    <FileText size={20} />
                  </span>
                  <h2
                    className="text-xl font-bold"
                    style={{ color: "var(--color-text-dark)" }}
                  >
                    元記事本文
                  </h2>
                </div>
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium no-underline px-3 py-1.5 transition-colors"
                  style={{
                    color: "var(--color-primary)",
                    border: "1px solid rgba(88, 129, 87, 0.2)",
                    borderRadius: "var(--radius-lg)",
                  }}
                >
                  <ExternalLink size={16} />
                  ソース記事を開く
                </a>
              </div>

              <div className="text-lg" style={{ lineHeight: 1.8 }}>
                {article.content ? (
                  article.content.split("\n\n").map((paragraph, i) => (
                    <p
                      key={i}
                      className={i === 0 ? "text-xl font-bold mb-6" : "mb-6"}
                      style={{ color: "var(--color-text-dark)" }}
                    >
                      {paragraph}
                    </p>
                  ))
                ) : (
                  <p style={{ color: "var(--color-text-muted)" }}>
                    本文は取得されていません。
                  </p>
                )}
              </div>
            </section>

            {/* AI Analysis Section */}
            {hasDeepDive && (
              <>
                {/* Divider */}
                <div className="h-12 w-full flex items-center justify-center">
                  <div
                    className="h-px w-full max-w-xs"
                    style={{ backgroundColor: "var(--color-border)" }}
                  />
                  <span
                    className="mx-4 text-xs font-medium uppercase tracking-widest whitespace-nowrap"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    AI Analysis
                  </span>
                  <div
                    className="h-px w-full max-w-xs"
                    style={{ backgroundColor: "var(--color-border)" }}
                  />
                </div>

                <div
                  className="overflow-hidden mb-16 transition-all duration-300"
                  style={{
                    backgroundColor: isAnalysisOpen
                      ? "var(--color-bg)"
                      : "var(--color-primary-bg)",
                    borderRadius: "1rem",
                    border: "1px solid var(--color-border-light)",
                    boxShadow: isAnalysisOpen
                      ? "0 2px 20px -4px rgba(0,0,0,0.04), 0 4px 6px -2px rgba(0,0,0,0.01)"
                      : "none",
                  }}
                >
                  <button
                    className="flex items-center justify-between w-full p-6 cursor-pointer select-none bg-transparent border-none text-left transition-colors"
                    onClick={() => setIsAnalysisOpen(!isAnalysisOpen)}
                  >
                    <div className="flex items-center gap-4">
                      <span
                        className="flex items-center justify-center w-10 h-10 rounded-full transition-colors duration-300"
                        style={{
                          backgroundColor: isAnalysisOpen
                            ? "var(--color-primary)"
                            : "rgba(88, 129, 87, 0.1)",
                          color: isAnalysisOpen
                            ? "white"
                            : "var(--color-primary)",
                        }}
                      >
                        <Brain size={24} />
                      </span>
                      <div>
                        <h2
                          className="text-lg font-bold"
                          style={{ color: "var(--color-text-dark)" }}
                        >
                          詳細分析レポートを表示
                        </h2>
                        <p
                          className="text-sm mt-0.5"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          AIによる要約・考察・リスク分析
                        </p>
                      </div>
                    </div>
                    <ChevronDown
                      size={20}
                      className="transition-transform duration-300"
                      style={{
                        color: "var(--color-text-muted)",
                        transform: isAnalysisOpen
                          ? "rotate(180deg)"
                          : "rotate(0deg)",
                      }}
                    />
                  </button>

                  {isAnalysisOpen && (
                    <div
                      className="px-6 pb-8 pt-2"
                      style={{
                        borderTop: "1px solid var(--color-border-light)",
                      }}
                    >
                      {/* Markdown レポートをシンプルに段落表示 */}
                      <div className="mt-6">
                        {article.deep_dive_report!.split("\n").map((line, i) => {
                          if (line.startsWith("## ")) {
                            return (
                              <h2
                                key={i}
                                className="font-bold mb-5"
                                style={{
                                  fontSize: "1.4rem",
                                  color: "var(--color-text-dark)",
                                  marginTop: "2.5rem",
                                  letterSpacing: "-0.01em",
                                }}
                              >
                                {line.replace("## ", "")}
                              </h2>
                            );
                          }
                          if (line.startsWith("# ")) {
                            return (
                              <h1
                                key={i}
                                className="text-xl font-bold mb-4"
                                style={{ color: "var(--color-text-dark)", marginTop: "2rem" }}
                              >
                                {line.replace("# ", "")}
                              </h1>
                            );
                          }
                          if (line.startsWith("- ")) {
                            return (
                              <li
                                key={i}
                                className="mb-2 ml-6"
                                style={{ lineHeight: 1.8, color: "#374151" }}
                              >
                                {line.replace("- ", "")}
                              </li>
                            );
                          }
                          if (line.trim() === "") return <br key={i} />;
                          return (
                            <p
                              key={i}
                              className="mb-4"
                              style={{ lineHeight: 1.8, color: "#374151" }}
                            >
                              {line}
                            </p>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Feedback Section */}
            <div
              className="p-8"
              style={{
                backgroundColor: "var(--color-primary-bg)",
                borderRadius: "var(--radius-lg)",
              }}
            >
              <h3
                className="text-base font-bold mb-6 flex items-center gap-2"
                style={{ color: "var(--color-text-dark)" }}
              >
                <MessageSquare
                  size={18}
                  style={{ color: "var(--color-text-muted)" }}
                />
                分析に対するフィードバック
              </h3>
              <div className="flex flex-col gap-6">
                <div className="flex items-center gap-4">
                  <span
                    className="text-sm font-medium"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    評価 (Relevance):
                  </span>
                  <StarRating value={rating} onChange={setRating} />
                </div>
                <div>
                  <textarea
                    className="w-full text-sm p-4 transition-shadow resize-y"
                    style={{
                      borderRadius: "var(--radius-lg)",
                      border: "1px solid var(--color-border)",
                      backgroundColor: "var(--color-bg)",
                      minHeight: "100px",
                      outline: "none",
                    }}
                    placeholder="分析に関するコメントや、追加の調査リクエストがあれば入力してください..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor =
                        "var(--color-primary)";
                      e.currentTarget.style.boxShadow =
                        "0 0 0 2px rgba(88, 129, 87, 0.2)";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor =
                        "var(--color-border)";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  />
                </div>
                <div className="flex justify-end">
                  <button
                    className="px-6 py-2.5 text-sm font-medium text-white transition-all cursor-pointer border-none"
                    style={{
                      backgroundColor: "var(--color-primary)",
                      borderRadius: "var(--radius-lg)",
                      opacity: feedbackSending ? 0.6 : 1,
                    }}
                    onClick={handleSendFeedback}
                    disabled={feedbackSending}
                  >
                    {feedbackSending ? "送信中..." : "フィードバックを送信"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar: Cross-Industry Perspectives */}
          {hasCrossIndustry && (
            <div className="lg:col-span-4">
              <h3
                className="text-xs font-bold uppercase tracking-wider mb-4 px-1"
                style={{ color: "var(--color-text-muted)" }}
              >
                業界別視点 (Cross-Industry Perspective)
              </h3>
              <div className="flex flex-col gap-4">
                {article.cross_industry_feedback!.perspectives.map(
                  (perspective, i) => (
                    <div
                      key={i}
                      className="relative overflow-hidden p-6 transition-all"
                      style={{
                        backgroundColor: "var(--color-primary-bg)",
                        borderRadius: "var(--radius-lg)",
                      }}
                    >
                      {/* Background quote mark */}
                      <span
                        className="absolute select-none pointer-events-none font-serif leading-none"
                        style={{
                          top: "-10px",
                          right: "12px",
                          fontSize: "8rem",
                          color: "var(--color-primary)",
                          opacity: 0.06,
                        }}
                        aria-hidden="true"
                      >
                        &ldquo;
                      </span>
                      <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-3">
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center"
                            style={{
                              backgroundColor: "var(--color-bg)",
                              color: "var(--color-text-muted)",
                              boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                            }}
                          >
                            <Factory size={18} />
                          </div>
                          <div>
                            <h4
                              className="text-sm font-bold"
                              style={{ color: "var(--color-text-dark)" }}
                            >
                              {perspective.industry}
                            </h4>
                          </div>
                        </div>
                        <p
                          className="text-sm leading-relaxed pl-11"
                          style={{ color: "var(--color-text-muted)" }}
                        >
                          {perspective.expert_comment}
                        </p>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

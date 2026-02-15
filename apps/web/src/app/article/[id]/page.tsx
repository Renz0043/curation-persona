"use client";

import { useState, useEffect } from "react";
import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ExternalLink,
  CalendarDays,
  Newspaper,
  ChevronDown,
  FileText,
  Brain,
  Factory,
  MessageSquare,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import StarRating from "@/components/StarRating";
import { useAuth } from "@/lib/auth-context";
import { subscribeToArticle } from "@/lib/firestore";
import type { Article } from "@/lib/types";

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1
      className="text-2xl font-bold mb-4 mt-8"
      style={{ color: "var(--color-text-dark)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2
      className="font-bold mb-4 mt-8"
      style={{ fontSize: "1.375rem", color: "var(--color-text-dark)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3
      className="font-bold mb-3 mt-6"
      style={{ fontSize: "1.175rem", color: "var(--color-text-dark)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4
      className="font-bold mb-2 mt-4"
      style={{ fontSize: "1rem", color: "var(--color-text-dark)", fontFamily: "var(--font-display)" }}
    >
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p className="mb-4 text-base" style={{ lineHeight: 1.8, color: "#374151" }}>
      {children}
    </p>
  ),
  ul: ({ children }) => <ul className="mb-4 ml-6 list-disc">{children}</ul>,
  ol: ({ children }) => <ol className="mb-4 ml-6 list-decimal">{children}</ol>,
  li: ({ children }) => (
    <li className="mb-1.5 text-base" style={{ lineHeight: 1.8, color: "#374151" }}>
      {children}
    </li>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="no-underline hover:underline"
      style={{ color: "var(--color-primary)" }}
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote
      className="mb-4 pl-4 italic"
      style={{
        borderLeft: "3px solid var(--color-primary)",
        color: "var(--color-text-muted)",
      }}
    >
      {children}
    </blockquote>
  ),
  code: ({ children, className }) => {
    const isBlock = className?.startsWith("language-");
    if (isBlock) {
      return (
        <code
          className="block overflow-x-auto p-4 mb-4 text-sm rounded-lg"
          style={{
            backgroundColor: "var(--color-border-light)",
            color: "var(--color-text-dark)",
          }}
        >
          {children}
        </code>
      );
    }
    return (
      <code
        className="px-1.5 py-0.5 text-sm rounded"
        style={{
          backgroundColor: "var(--color-border-light)",
          color: "var(--color-text-dark)",
        }}
      >
        {children}
      </code>
    );
  },
  table: ({ children }) => (
    <div className="overflow-x-auto mb-4">
      <table
        className="w-full text-sm"
        style={{ borderCollapse: "collapse" }}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead style={{ backgroundColor: "var(--color-border-light)" }}>
      {children}
    </thead>
  ),
  th: ({ children }) => (
    <th
      className="px-3 py-2 text-left font-semibold"
      style={{
        border: "1px solid var(--color-border)",
        color: "var(--color-text-dark)",
      }}
    >
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td
      className="px-3 py-2"
      style={{
        border: "1px solid var(--color-border)",
        color: "#374151",
      }}
    >
      {children}
    </td>
  ),
  hr: () => (
    <hr
      className="my-6"
      style={{ border: "none", borderTop: "1px solid var(--color-border-light)" }}
    />
  ),
  strong: ({ children }) => (
    <strong style={{ color: "var(--color-text-dark)" }}>{children}</strong>
  ),
};

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
  const [analysisTab, setAnalysisTab] = useState<"report" | number>("report");
  const [feedbackSending, setFeedbackSending] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [researchRequesting, setResearchRequesting] = useState(false);

  useEffect(() => {
    const unsub = subscribeToArticle(id, (art) => {
      setArticle(art);
      if (art?.user_rating) setRating(art.user_rating);
      if (art?.user_comment) setComment(art.user_comment);
      setLoading(false);
    });
    return () => unsub();
  }, [id]);

  const handleRequestResearch = async () => {
    if (!article) return;
    setResearchRequesting(true);
    try {
      const res = await fetch(`/api/articles/${id}/research`, {
        method: "POST",
      });
      if (!res.ok) {
        console.error("Research request failed:", res.status);
      }
    } catch (e) {
      console.error("Failed to request research:", e);
    } finally {
      setResearchRequesting(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!article || rating === 0) return;
    setFeedbackSending(true);
    setFeedbackSent(false);
    try {
      const res = await fetch(`/api/collections/${article.collection_id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          articleUrl: article.url,
          rating,
          comment: comment || undefined,
        }),
      });
      if (res.ok) {
        setFeedbackSent(true);
      }
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
            <div className="flex items-center gap-3" />
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

        {/* Full-width Content */}
        <div>
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
                  記事本文
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

            <div className="text-base" style={{ lineHeight: 1.8 }}>
              {article.content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {article.content}
                </ReactMarkdown>
              ) : (
                <p style={{ color: "var(--color-text-muted)" }}>
                  本文は取得されていません。
                </p>
              )}
            </div>
          </section>

          {/* Research Request Button */}
          {!hasDeepDive && (
            <section className="mb-12 flex justify-center">
              {article.research_status === "pending" ? (
                <div
                  className="inline-flex items-center gap-3 px-6 py-3 text-sm font-medium"
                  style={{
                    color: "var(--color-text-muted)",
                    backgroundColor: "var(--color-border-light)",
                    borderRadius: "var(--radius-lg)",
                  }}
                >
                  <Brain size={18} />
                  リクエスト受付済み
                </div>
              ) : article.research_status === "researching" ? (
                <div
                  className="inline-flex items-center gap-3 px-6 py-3 text-sm font-medium"
                  style={{
                    color: "var(--color-primary)",
                    backgroundColor: "var(--color-primary-bg)",
                    borderRadius: "var(--radius-lg)",
                    border: "1px solid rgba(88, 129, 87, 0.2)",
                  }}
                >
                  <div
                    className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
                    style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
                  />
                  リサーチ中...
                </div>
              ) : (
                <button
                  className="inline-flex items-center gap-3 px-6 py-3 text-sm font-medium cursor-pointer border-none transition-all"
                  style={{
                    color: "var(--color-primary)",
                    backgroundColor: "var(--color-primary-bg)",
                    borderRadius: "var(--radius-lg)",
                    border: "1px solid rgba(88, 129, 87, 0.2)",
                    opacity: researchRequesting ? 0.6 : 1,
                  }}
                  onClick={handleRequestResearch}
                  disabled={researchRequesting}
                >
                  <Brain size={18} />
                  {researchRequesting ? "リクエスト送信中..." : "深掘りリサーチを依頼"}
                </button>
              )}
            </section>
          )}

          {/* AI Analysis Section */}
          {hasDeepDive && (
            <>
              {/* Divider — full width */}
              <div className="h-12 w-full flex items-center justify-center">
                <div
                  className="h-px w-full"
                  style={{ backgroundColor: "var(--color-border)" }}
                />
                <span
                  className="mx-4 text-xs font-medium uppercase tracking-widest whitespace-nowrap"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  AI Analysis
                </span>
                <div
                  className="h-px w-full"
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
                        AI深掘りレポート
                      </h2>
                      <p
                        className="text-sm mt-0.5"
                        style={{ color: "var(--color-text-muted)" }}
                      >
                        要約・キーポイント・アクションアイテム・異業種視点
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
                    style={{
                      borderTop: "1px solid var(--color-border-light)",
                    }}
                  >
                    {/* Tab Bar */}
                    <div
                      className="flex gap-0 px-6 pt-4"
                      style={{ borderBottom: "1px solid var(--color-border-light)" }}
                    >
                      <button
                        className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium cursor-pointer bg-transparent border-none transition-colors"
                        style={{
                          color: analysisTab === "report" ? "var(--color-primary)" : "var(--color-text-muted)",
                          borderBottom: analysisTab === "report" ? "2px solid var(--color-primary)" : "2px solid transparent",
                          marginBottom: "-1px",
                        }}
                        onClick={() => setAnalysisTab("report")}
                      >
                        <Brain size={16} />
                        AI分析
                      </button>
                      {hasCrossIndustry &&
                        article.cross_industry_feedback!.perspectives.map(
                          (perspective, i) => (
                            <button
                              key={i}
                              className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium cursor-pointer bg-transparent border-none transition-colors"
                              style={{
                                color: analysisTab === i ? "var(--color-primary)" : "var(--color-text-muted)",
                                borderBottom: analysisTab === i ? "2px solid var(--color-primary)" : "2px solid transparent",
                                marginBottom: "-1px",
                              }}
                              onClick={() => setAnalysisTab(i)}
                            >
                              <Factory size={16} />
                              {perspective.industry}
                            </button>
                          )
                        )}
                    </div>

                    {/* Tab Content */}
                    <div className="px-6 pb-8 pt-2">
                      {analysisTab === "report" && (
                        <div className="mt-4">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {article.deep_dive_report!}
                          </ReactMarkdown>
                        </div>
                      )}
                      {typeof analysisTab === "number" && hasCrossIndustry && (
                        <div className="mt-4">
                          <div className="flex items-center gap-3 mb-6">
                            <div
                              className="w-10 h-10 rounded-full flex items-center justify-center"
                              style={{
                                backgroundColor: "var(--color-primary-bg)",
                                color: "var(--color-primary)",
                              }}
                            >
                              <Factory size={20} />
                            </div>
                            <div>
                              <h3
                                className="text-base font-bold"
                                style={{ color: "var(--color-text-dark)" }}
                              >
                                {article.cross_industry_feedback!.perspectives[analysisTab].industry}
                                <span className="font-normal text-sm ml-2" style={{ color: "var(--color-text-muted)" }}>
                                  の専門家視点
                                </span>
                              </h3>
                            </div>
                          </div>
                          {article.cross_industry_feedback!.perspectives[analysisTab].abstracted_theme && (
                            <div
                              className="mb-6 p-4 rounded-lg"
                              style={{
                                backgroundColor: "var(--color-primary-bg)",
                                border: "1px solid var(--color-border-light)",
                              }}
                            >
                              <p className="text-sm font-medium mb-1" style={{ color: "var(--color-text-muted)" }}>
                                抽象化されたテーマ
                              </p>
                              <p className="text-base" style={{ color: "var(--color-text-dark)", lineHeight: 1.7 }}>
                                {article.cross_industry_feedback!.perspectives[analysisTab].abstracted_theme}
                              </p>
                            </div>
                          )}
                          <div className="text-base" style={{ lineHeight: 1.8, color: "#374151" }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                              {article.cross_industry_feedback!.perspectives[analysisTab].expert_comment}
                            </ReactMarkdown>
                          </div>
                        </div>
                      )}
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
              この記事へのフィードバック
            </h3>
            <div className="flex flex-col gap-6">
              <div className="flex items-center gap-4">
                <span
                  className="text-sm font-medium"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  評価:
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
              <div className="flex justify-end items-center gap-3">
                {feedbackSent && (
                  <span className="text-sm" style={{ color: "var(--color-primary)" }}>
                    保存しました
                  </span>
                )}
                <button
                  className="px-6 py-2.5 text-sm font-medium text-white transition-all cursor-pointer border-none"
                  style={{
                    backgroundColor: "var(--color-primary)",
                    borderRadius: "var(--radius-lg)",
                    opacity: feedbackSending || rating === 0 ? 0.6 : 1,
                  }}
                  onClick={handleSendFeedback}
                  disabled={feedbackSending || rating === 0}
                >
                  {feedbackSending
                    ? "保存中..."
                    : article.user_rating
                      ? "フィードバックを更新"
                      : "フィードバックを保存"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

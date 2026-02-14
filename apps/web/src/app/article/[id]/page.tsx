"use client";

import { useState } from "react";
import { use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
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
  GraduationCap,
  DollarSign,
  MessageSquare,
} from "lucide-react";
import ScoreBar from "@/components/ScoreBar";
import StarRating from "@/components/StarRating";

type ArticleDetail = {
  id: string;
  title: string;
  url: string;
  source: string;
  source_type: string;
  published_at: string;
  relevance_score: number;
  content: string[];
  og_image?: string;
  deep_dive_report: {
    summary: string;
    sections: { heading: string; content: string }[];
    keyPoints: string[];
  };
  cross_industry_feedback: {
    perspectives: {
      industry: string;
      role: string;
      icon: string;
      expert_comment: string;
      is_risk?: boolean;
    }[];
  };
  source_citation: string;
  user_rating?: number;
};

const mockArticles: Record<string, ArticleDetail> = {
  "1": {
    id: "1",
    title: "次世代半導体市場における日本の戦略的立ち位置とグローバルサプライチェーンへの影響分析",
    url: "https://example.com/article-1",
    source: "Nikkei Asia",
    source_type: "AI",
    published_at: "2024年10月24日",
    relevance_score: 0.92,
    content: [
      "日本が再び世界の半導体産業の中心地として復活を遂げようとしている。政府主導の「Rapidus」プロジェクトは、2027年までに最先端の2ナノメートル半導体の量産化を目指すという野心的な計画だ。",
      "かつて1980年代、日本の半導体産業は世界市場の50%以上を占め、圧倒的な存在感を誇っていた。しかし、日米貿易摩擦や韓国・台湾勢の台頭、そしてデジタル化への対応遅れにより、その地位は徐々に失われていった。現在、日本のシェアは10%程度にまで低下している。",
      "しかし、潮目は変わりつつある。地政学的な緊張の高まりにより、サプライチェーンの再構築が世界的な急務となっているからだ。米国や欧州は、半導体製造の過度なアジア（特に台湾）依存をリスクと捉え、供給源の多角化を模索している。",
      "こうした中、日本政府は巨額の補助金を投じ、TSMCの熊本工場誘致に成功した。さらに、国内主要企業8社（トヨタ自動車、デンソー、ソニーグループ、NTT、NEC、ソフトバンク、キオクシア、三菱UFJ銀行）が出資するRapidusが設立された。Rapidusは米IBMと提携し、次世代技術の習得に全力を挙げている。",
      "北海道千歳市に建設中のRapidus工場は、単なる製造拠点ではない。日本の半導体産業のエコシステム全体を再活性化させるための起爆剤となることが期待されているのだ。素材や製造装置の分野では、日本企業は依然として高い競争力を維持している。これらの強みと最先端の製造技術を組み合わせることで、日本は再び「シリコン・アイランド」としての輝きを取り戻せるかもしれない。",
    ],
    deep_dive_report: {
      summary:
        "本記事は、急速に進化する半導体業界において、日本が再び主要なプレイヤーとしての地位を確立しようとする戦略的な動きを詳細に分析しています。特にRapidusプロジェクトを中心とした官民一体の取り組みに焦点を当てています。",
      sections: [
        {
          heading: "1. 戦略的背景と市場動向",
          content:
            "日本政府は経済安全保障の観点から、半導体サプライチェーンの強靭化を最優先課題としています。2ナノメートル世代のロジック半導体量産を目指すRapidusへの支援は、単なる産業政策を超え、地政学的なリスクヘッジとしての側面を強く持っています。\n\n市場予測によると、AIや自動運転技術の進展に伴い、先端半導体の需要は2030年までに現在の3倍に拡大すると見込まれています。この成長市場において、日本が製造拠点としての地位を確立できれば、長期的な経済成長のドライバーとなり得ます。",
        },
        {
          heading: "2. 技術的実現性と課題",
          content:
            "RapidusはIBMとのパートナーシップを通じて、2nmプロセス技術の習得を進めています。短期間での量産立ち上げ（2027年目標）は極めて野心的な目標ですが、IBMのAlbany研究所へのエンジニア派遣など、具体的な技術移転プロセスが順調に進行していることが確認されています。",
        },
      ],
      keyPoints: [
        "熟練エンジニアの不足：国内の半導体産業縮小期に多くの人材が流出した影響が残っています。",
        "グローバルな獲得競争：TSMCやSamsung、Intelとの人材獲得競争が激化しており、給与水準の引き上げが不可欠です。",
      ],
    },
    cross_industry_feedback: {
      perspectives: [
        {
          industry: "製造業 (Automotive)",
          role: "サプライチェーン専門家",
          icon: "factory",
          expert_comment:
            "自動車業界でも半導体不足による減産を経験しており、国内調達比率の向上はBCPの観点から極めて合理的です。ただしコスト競争力の維持が課題となるでしょう。",
        },
        {
          industry: "教育・研究 (Education)",
          role: "工学系大学教授",
          icon: "school",
          expert_comment:
            "先端ロジック半導体の設計・製造プロセスを理解できる人材は現在枯渇しています。大学のカリキュラム改定には時間がかかるため、産学連携による即戦力育成プログラムが急務です。",
        },
        {
          industry: "金融・投資 (Finance)",
          role: "シニアアナリスト",
          icon: "finance",
          expert_comment:
            "数兆円規模の投資回収シナリオには不確実性が残ります。特に2nm世代の需要が想定通り立ち上がるか、歩留まりが改善するかどうかが投資判断の分かれ目となります。",
          is_risk: true,
        },
      ],
    },
    source_citation:
      'Nikkei Asia, "Japan\'s Semiconductor Renaissance: A Strategic Pivot" (2024/10/24)',
    user_rating: 4,
  },
};

const perspectiveIcons: Record<string, React.ReactNode> = {
  factory: <Factory size={18} />,
  school: <GraduationCap size={18} />,
  finance: <DollarSign size={18} />,
};

export default function ArticleDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const article = mockArticles[id];

  if (!article) {
    notFound();
  }

  const [rating, setRating] = useState(article.user_rating ?? 0);
  const [comment, setComment] = useState("");
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);

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
                調査完了
              </span>
              <div
                className="flex items-center gap-4 text-sm"
                style={{ color: "var(--color-text-muted)" }}
              >
                <span className="flex items-center gap-1.5">
                  <CalendarDays size={18} />
                  {article.published_at}
                </span>
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
          <div className="lg:col-span-8">
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
                {article.content.map((paragraph, i) => (
                  <p
                    key={i}
                    className={i === 0 ? "text-xl font-bold mb-6" : "mb-6"}
                    style={{
                      color:
                        i === 0
                          ? "var(--color-text-dark)"
                          : "var(--color-text-dark)",
                    }}
                  >
                    {paragraph}
                  </p>
                ))}
              </div>

              <div
                className="mt-8 pt-6"
                style={{ borderTop: "1px solid var(--color-border-light)" }}
              >
                <p
                  className="text-sm"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  出典: {article.source_citation}
                </p>
              </div>
            </section>

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

            {/* AI Analysis Section */}
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
                  {/* Summary */}
                  <p
                    className="text-lg font-medium mb-8 mt-6"
                    style={{
                      color: "var(--color-text-muted)",
                      lineHeight: 1.8,
                    }}
                  >
                    {article.deep_dive_report.summary}
                  </p>

                  {/* Sections */}
                  {article.deep_dive_report.sections.map((section, i) => (
                    <div key={i}>
                      <h2
                        className="font-bold mb-5"
                        style={{
                          fontSize: "1.4rem",
                          color: "var(--color-text-dark)",
                          marginTop: i === 0 ? "2.5rem" : "2.5rem",
                          letterSpacing: "-0.01em",
                        }}
                      >
                        {section.heading}
                      </h2>
                      {section.content.split("\n\n").map((para, j) => (
                        <p
                          key={j}
                          className="mb-7"
                          style={{
                            lineHeight: 1.8,
                            color: "#374151",
                          }}
                        >
                          {para}
                        </p>
                      ))}
                    </div>
                  ))}

                  {/* Key Points */}
                  {article.deep_dive_report.keyPoints.length > 0 && (
                    <ul
                      className="list-disc mb-7"
                      style={{
                        paddingLeft: "1.5rem",
                        color: "#4b5563",
                        lineHeight: 1.7,
                      }}
                    >
                      {article.deep_dive_report.keyPoints.map((point, i) => (
                        <li key={i} className="mb-3">
                          {point}
                        </li>
                      ))}
                    </ul>
                  )}

                  {/* Conclusion */}
                  <h2
                    className="font-bold mb-5"
                    style={{
                      fontSize: "1.4rem",
                      color: "var(--color-text-dark)",
                      marginTop: "2.5rem",
                      letterSpacing: "-0.01em",
                    }}
                  >
                    3. 結論
                  </h2>
                  <p
                    className="mb-7"
                    style={{ lineHeight: 1.8, color: "#374151" }}
                  >
                    日本の半導体復権戦略は、高いポテンシャルを持つ一方で、実行リスクも伴います。しかし、成功すれば世界のサプライチェーンにおける日本の不可欠性が飛躍的に高まるでしょう。
                  </p>
                </div>
              )}
            </div>

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
                    }}
                  >
                    フィードバックを送信
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar: Cross-Industry Perspectives */}
          <div className="lg:col-span-4">
            <h3
              className="text-xs font-bold uppercase tracking-wider mb-4 px-1"
              style={{ color: "var(--color-text-muted)" }}
            >
              業界別視点 (Cross-Industry Perspective)
            </h3>
            <div className="flex flex-col gap-4">
              {article.cross_industry_feedback.perspectives.map(
                (perspective, i) => (
                  <div
                    key={i}
                    className="relative overflow-hidden p-6 transition-all"
                    style={{
                      backgroundColor: "var(--color-primary-bg)",
                      borderRadius: "var(--radius-lg)",
                      borderLeft: perspective.is_risk
                        ? "4px solid var(--color-risk)"
                        : "4px solid transparent",
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
                            color: perspective.is_risk
                              ? "var(--color-risk)"
                              : "var(--color-text-muted)",
                            boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                          }}
                        >
                          {perspectiveIcons[perspective.icon] || (
                            <Factory size={18} />
                          )}
                        </div>
                        <div>
                          <h4
                            className="text-sm font-bold"
                            style={{ color: "var(--color-text-dark)" }}
                          >
                            {perspective.industry}
                          </h4>
                          <span
                            className="text-xs"
                            style={{ color: "var(--color-text-muted)" }}
                          >
                            {perspective.role}
                          </span>
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
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import {
  CalendarDays,
  RefreshCw,
  Brain,
  Rss,
  Check,
  Pause,
  Trash2,
  Plus,
  Key,
  Copy,
  Eye,
  EyeOff,
  Settings,
  Info,
  ChevronDown,
} from "lucide-react";

// --- モックデータ ---

const mockProfile = {
  summary:
    "生成AIの技術的進化、特にLLM、自律型AIアーキテクチャ、RAG最適化手法への関心が強い傾向があります。加えて、エネルギー貯蔵技術や半導体サプライチェーンといったハードウェア・インフラ領域にも継続的な関心を示しています。規制動向については、AI規制とプラットフォーム規制の両方をフォローしており、技術と社会実装の接点に注目する傾向が見られます。",
  lastUpdated: "2025年1月15日 14:30",
  totalRatedArticles: 84,
};

type RssFeed = {
  id: string;
  name: string;
  url: string;
  status: "active" | "paused";
};

const initialFeeds: RssFeed[] = [
  { id: "1", name: "TechCrunch", url: "https://techcrunch.com/feed/", status: "active" },
  { id: "2", name: "arXiv CS.AI", url: "https://arxiv.org/rss/cs.AI", status: "active" },
  { id: "3", name: "Hacker News Best", url: "https://hnrss.org/best", status: "active" },
  { id: "4", name: "Nature Energy", url: "https://www.nature.com/nenergy.rss", status: "paused" },
  { id: "5", name: "Bloomberg Technology", url: "https://feeds.bloomberg.com/technology/news.rss", status: "active" },
];

const mockApiKey = "cp_live_sk_8923472893471a2b3c4d5e6f7890abcdef";

// --- ページ本体 ---

export default function ProfilePage() {
  const [feeds, setFeeds] = useState<RssFeed[]>(initialFeeds);
  const [showApiKey, setShowApiKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const [refreshHover, setRefreshHover] = useState(false);

  const toggleFeedStatus = (id: string) => {
    setFeeds((prev) =>
      prev.map((f) =>
        f.id === id
          ? { ...f, status: f.status === "active" ? "paused" : "active" }
          : f
      )
    );
  };

  const deleteFeed = (id: string) => {
    setFeeds((prev) => prev.filter((f) => f.id !== id));
  };

  const handleCopyKey = async () => {
    await navigator.clipboard.writeText(mockApiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const maskedKey = mockApiKey.slice(0, 14) + "••••••••••••••••••••••••";

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* ページヘッダー */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1
            className="text-3xl font-bold mb-1"
            style={{
              color: "var(--color-text-dark)",
              fontFamily: "var(--font-display)",
            }}
          >
            関心プロファイル
          </h1>
          <div
            className="flex items-center gap-1.5 text-sm"
            style={{ color: "var(--color-text-muted)" }}
          >
            <CalendarDays size={14} />
            <span>最終更新: {mockProfile.lastUpdated}</span>
          </div>
        </div>
        <button
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium cursor-pointer transition-colors duration-150"
          style={{
            backgroundColor: refreshHover ? "var(--color-primary-bg)" : "transparent",
            color: "var(--color-primary)",
            border: "1px solid var(--color-primary)",
            borderRadius: "var(--radius-md)",
          }}
          onMouseEnter={() => setRefreshHover(true)}
          onMouseLeave={() => setRefreshHover(false)}
        >
          <RefreshCw size={14} />
          更新
        </button>
      </div>

      {/* AIによる関心分析 */}
      <section className="mb-10">
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary)" }}
          />
          AIによる関心分析
        </h2>
        <div
          className="relative overflow-hidden"
          style={{
            backgroundColor: "var(--color-primary-bg)",
            borderLeft: "3px solid var(--color-primary)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-xl)",
          }}
        >
          <div
            className="flex items-center gap-2 mb-3"
            style={{ color: "var(--color-primary)" }}
          >
            <div
              className="flex items-center justify-center w-8 h-8 rounded-full"
              style={{ backgroundColor: "var(--color-primary)", color: "white" }}
            >
              <Brain size={16} />
            </div>
            <span className="text-sm font-semibold">パーソナライズ分析</span>
          </div>
          <p
            className="text-sm leading-relaxed mb-4"
            style={{ color: "var(--color-text-dark)" }}
          >
            {mockProfile.summary}
          </p>
          <div
            className="text-xs"
            style={{ color: "var(--color-text-muted)" }}
          >
            {mockProfile.totalRatedArticles}件の高評価記事から分析
          </div>
        </div>
      </section>

      {/* 情報ソース設定 */}
      <section className="mb-10">
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary)" }}
          />
          情報ソース設定
        </h2>
        <div
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
          }}
        >
          {feeds.map((feed, i) => (
            <FeedRow
              key={feed.id}
              feed={feed}
              isLast={i === feeds.length - 1}
              onToggle={() => toggleFeedStatus(feed.id)}
              onDelete={() => deleteFeed(feed.id)}
            />
          ))}
          {feeds.length === 0 && (
            <div
              className="text-center py-8 text-sm"
              style={{ color: "var(--color-text-muted)" }}
            >
              フィードが登録されていません
            </div>
          )}
        </div>
        <button
          className="flex items-center gap-2 mt-3 px-4 py-2 text-sm font-medium cursor-not-allowed opacity-50"
          style={{
            backgroundColor: "transparent",
            color: "var(--color-text-muted)",
            border: "1px dashed var(--color-border)",
            borderRadius: "var(--radius-md)",
          }}
          disabled
        >
          <Plus size={14} />
          新しいフィードを追加
        </button>
      </section>

      {/* Bookmark APIキー */}
      <section className="mb-10">
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary)" }}
          />
          Bookmark APIキー
        </h2>
        <div
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-xl)",
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Key size={16} style={{ color: "var(--color-primary)" }} />
            <span
              className="text-sm font-semibold"
              style={{ color: "var(--color-text-dark)" }}
            >
              APIキー
            </span>
          </div>
          <div className="flex items-center gap-2 mb-3">
            <code
              className="flex-1 text-sm px-3 py-2"
              style={{
                backgroundColor: "var(--color-primary-bg)",
                borderRadius: "var(--radius-md)",
                color: "var(--color-text-dark)",
                fontFamily: "monospace",
              }}
            >
              {showApiKey ? mockApiKey : maskedKey}
            </code>
            <IconButton
              icon={showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
              onClick={() => setShowApiKey((v) => !v)}
              title={showApiKey ? "隠す" : "表示"}
            />
            <IconButton
              icon={<Copy size={14} />}
              onClick={handleCopyKey}
              title="コピー"
              active={copied}
              activeLabel="コピー済み"
            />
            <IconButton
              icon={<RefreshCw size={14} />}
              onClick={() => {}}
              title="再生成"
            />
          </div>
          <p
            className="text-xs leading-relaxed"
            style={{ color: "var(--color-text-muted)" }}
          >
            このAPIキーはSafariブックマーク連携で使用されます。キーを再生成すると、既存の連携設定を更新する必要があります。
          </p>
        </div>
      </section>

      {/* キュレーション設定 */}
      <section className="mb-10">
        <h2
          className="text-lg font-bold mb-4 flex items-center gap-2"
          style={{ color: "var(--color-text-dark)" }}
        >
          <span
            className="inline-block w-1 h-5 rounded-full"
            style={{ backgroundColor: "var(--color-primary)" }}
          />
          <Settings size={18} style={{ color: "var(--color-primary)" }} />
          キュレーション設定
        </h2>
        <div
          className="flex flex-col gap-6"
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-xl)",
          }}
        >
          {/* 深掘り深度 */}
          <SettingRow
            label="深掘り深度"
            hint="レポート生成時の調査の深さを設定します"
            value="medium"
            disabled
            options={[
              { value: "medium", label: "Medium — 標準的な深掘り" },
            ]}
          />

          {/* 異業種視点 */}
          <SettingRow
            label="異業種視点"
            hint="エコーチェンバー防止のため、異分野の視点をどの程度含めるかを設定します"
            value="medium"
            disabled
            options={[
              { value: "medium", label: "Medium — 適度に異分野を含む" },
            ]}
          />
        </div>
      </section>
    </div>
  );
}

// --- サブコンポーネント ---

function FeedRow({
  feed,
  isLast,
  onToggle,
  onDelete,
}: {
  feed: RssFeed;
  isLast: boolean;
  onToggle: () => void;
  onDelete: () => void;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 transition-colors duration-150"
      style={{
        borderBottom: isLast ? "none" : "1px solid var(--color-border)",
        backgroundColor: hovered ? "var(--color-card-hover)" : "transparent",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Rss size={14} style={{ color: "var(--color-text-muted)", flexShrink: 0 }} />
      <span
        className="flex-1 text-sm truncate"
        style={{ color: "var(--color-text-dark)" }}
      >
        {feed.name}
      </span>
      <button
        onClick={onToggle}
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium border-none cursor-pointer transition-colors duration-150"
        style={{
          backgroundColor:
            feed.status === "active"
              ? "rgba(107, 156, 123, 0.1)"
              : "rgba(214, 140, 140, 0.1)",
          color: feed.status === "active" ? "var(--color-positive)" : "var(--color-risk)",
          borderRadius: "var(--radius-full)",
        }}
      >
        {feed.status === "active" ? <Check size={12} /> : <Pause size={12} />}
        {feed.status === "active" ? "有効" : "一時停止"}
      </button>
      <button
        onClick={onDelete}
        className="flex items-center justify-center w-7 h-7 border-none cursor-pointer transition-colors duration-150"
        style={{
          backgroundColor: "transparent",
          color: "var(--color-text-muted)",
          borderRadius: "var(--radius-md)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = "var(--color-risk)";
          e.currentTarget.style.backgroundColor = "rgba(214, 140, 140, 0.1)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = "var(--color-text-muted)";
          e.currentTarget.style.backgroundColor = "transparent";
        }}
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

function IconButton({
  icon,
  onClick,
  title,
  active,
  activeLabel,
}: {
  icon: React.ReactNode;
  onClick: () => void;
  title: string;
  active?: boolean;
  activeLabel?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="flex items-center gap-1 px-2.5 py-2 text-xs border-none cursor-pointer transition-colors duration-150"
      style={{
        backgroundColor: active ? "rgba(107, 156, 123, 0.1)" : "transparent",
        color: active ? "var(--color-positive)" : "var(--color-text-muted)",
        borderRadius: "var(--radius-md)",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "var(--color-card-hover)";
          e.currentTarget.style.color = "var(--color-primary)";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "transparent";
          e.currentTarget.style.color = "var(--color-text-muted)";
        }
      }}
    >
      {icon}
      {active && activeLabel && <span>{activeLabel}</span>}
    </button>
  );
}

function SettingRow({
  label,
  hint,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  hint: string;
  value: string;
  onChange?: (v: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-1">
        <span
          className="text-sm font-semibold"
          style={{ color: "var(--color-text-dark)" }}
        >
          {label}
        </span>
      </div>
      <div
        className="flex items-center gap-1.5 mb-2 text-xs"
        style={{ color: "var(--color-text-muted)" }}
      >
        <Info size={12} />
        <span>{hint}</span>
      </div>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={disabled}
          className={`w-full appearance-none px-3 py-2.5 pr-8 text-sm ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            backgroundColor: disabled ? "var(--color-primary-bg)" : "var(--color-bg)",
            color: "var(--color-text-dark)",
          }}
          onFocus={(e) => {
            if (!disabled) {
              e.currentTarget.style.borderColor = "var(--color-primary)";
              e.currentTarget.style.boxShadow = "0 0 0 2px var(--color-primary-bg)";
            }
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = "var(--color-border)";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
          style={{ color: "var(--color-text-muted)" }}
        />
      </div>
    </div>
  );
}

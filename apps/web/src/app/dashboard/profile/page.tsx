"use client";

import { useState, useEffect, useCallback } from "react";
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
import { useAuth } from "@/lib/auth-context";
import { getUserProfile } from "@/lib/firestore";
import type { UserProfile, SourceConfig } from "@/lib/types";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [showApiKey, setShowApiKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const [refreshHover, setRefreshHover] = useState(false);

  const fetchProfile = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    try {
      const p = await getUserProfile(user.uid);
      setProfile(p);
    } catch (e) {
      console.error("Failed to fetch profile:", e);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const apiKey = profile?.api_key ?? "";
  const maskedKey = apiKey
    ? apiKey.slice(0, 14) + "••••••••••••••••••••••••"
    : "未設定";

  const handleCopyKey = async () => {
    if (!apiKey) return;
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const feeds = profile?.sources ?? [];
  const interestProfile = profile?.interestProfile ?? "";
  const lastUpdated = profile?.interestProfileUpdatedAt
    ? formatDateTime(profile.interestProfileUpdatedAt)
    : "未更新";

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div
              className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
              style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
            />
            <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              プロファイルを読み込み中...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            プロファイルが見つかりませんでした。
          </p>
          <p className="text-xs mt-2" style={{ color: "var(--color-text-muted)" }}>
            バックエンドでユーザーデータを初期化してください。
          </p>
        </div>
      </div>
    );
  }

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
            <span>最終更新: {lastUpdated}</span>
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
            {interestProfile || "まだ関心分析データがありません。記事を評価するとAIが自動で分析します。"}
          </p>
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
              {showApiKey ? apiKey || "未設定" : maskedKey}
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
          </div>
          <p
            className="text-xs leading-relaxed"
            style={{ color: "var(--color-text-muted)" }}
          >
            このAPIキーはSafariブックマーク連携で使用されます。
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
          <SettingRow
            label="深掘り深度"
            hint="レポート生成時の調査の深さを設定します"
            value="medium"
            disabled
            options={[{ value: "medium", label: "Medium — 標準的な深掘り" }]}
          />
          <SettingRow
            label="異業種視点"
            hint="エコーチェンバー防止のため、異分野の視点をどの程度含めるかを設定します"
            value="medium"
            disabled
            options={[{ value: "medium", label: "Medium — 適度に異分野を含む" }]}
          />
        </div>
      </section>
    </div>
  );
}

// --- ヘルパー ---

function formatDateTime(date: Date): string {
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  const d = date.getDate();
  const h = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${y}年${m}月${d}日 ${h}:${min}`;
}

// --- サブコンポーネント ---

function FeedRow({
  feed,
  isLast,
}: {
  feed: SourceConfig;
  isLast: boolean;
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
      <span
        className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium border-none"
        style={{
          backgroundColor: feed.enabled
            ? "rgba(107, 156, 123, 0.1)"
            : "rgba(214, 140, 140, 0.1)",
          color: feed.enabled ? "var(--color-positive)" : "var(--color-risk)",
          borderRadius: "var(--radius-full)",
        }}
      >
        {feed.enabled ? <Check size={12} /> : <Pause size={12} />}
        {feed.enabled ? "有効" : "一時停止"}
      </span>
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

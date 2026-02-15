"use client";

import { useState, useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { SourceConfig } from "@/lib/types";

interface AddSourceModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (source: SourceConfig) => void;
}

export default function AddSourceModal({
  open,
  onClose,
  onAdd,
}: AddSourceModalProps) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setName("");
      setUrl("");
      setTimeout(() => nameRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) return;

    const source: SourceConfig = {
      id: `src_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type: "rss",
      name: name.trim(),
      enabled: true,
      config: { url: url.trim() },
    };
    onAdd(source);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.4)", backdropFilter: "blur(4px)" }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-w-md mx-4"
        style={{
          backgroundColor: "var(--color-bg)",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--color-border)",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15)",
        }}
      >
        {/* ヘッダー */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--color-border)" }}
        >
          <h3
            className="text-base font-bold"
            style={{ color: "var(--color-text-dark)" }}
          >
            新しいRSSフィードを追加
          </h3>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 cursor-pointer transition-colors duration-150"
            style={{
              color: "var(--color-text-muted)",
              borderRadius: "var(--radius-md)",
              border: "none",
              backgroundColor: "transparent",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--color-card-hover)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* フォーム */}
        <form onSubmit={handleSubmit} className="px-6 py-5 flex flex-col gap-4">
          <p
            className="text-xs leading-relaxed"
            style={{ color: "var(--color-text-muted)" }}
          >
            追加したソースは次回のブリーフィング（日次バッチ）から反映されます。既存のブックマークやアーカイブには影響しません。
          </p>

          {/* ソース名 */}
          <div className="flex flex-col gap-1.5">
            <label
              className="text-sm font-medium"
              style={{ color: "var(--color-text-dark)" }}
            >
              ソース名
            </label>
            <input
              ref={nameRef}
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例: TechCrunch Japan"
              className="px-3 py-2.5 text-sm outline-none transition-colors duration-150"
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-bg)",
                color: "var(--color-text-dark)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            />
          </div>

          {/* URL */}
          <div className="flex flex-col gap-1.5">
            <label
              className="text-sm font-medium"
              style={{ color: "var(--color-text-dark)" }}
            >
              フィードURL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="例: https://techcrunch.com/feed/"
              className="px-3 py-2.5 text-sm outline-none transition-colors duration-150"
              style={{
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-bg)",
                color: "var(--color-text-dark)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "var(--color-primary)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--color-border)";
              }}
            />
          </div>

          {/* ボタン */}
          <div className="flex justify-end gap-3 mt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-sm font-medium cursor-pointer transition-colors duration-150"
              style={{
                color: "var(--color-text-muted)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "transparent",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "var(--color-card-hover)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={!name.trim() || !url.trim()}
              className="px-4 py-2.5 text-sm font-medium cursor-pointer transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: "var(--color-primary)",
                color: "white",
                border: "none",
                borderRadius: "var(--radius-md)",
              }}
            >
              追加する
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

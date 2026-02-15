import type { CollectionStatus } from "@/lib/types";

type StatusIndicatorProps = {
  status: CollectionStatus;
};

const steps = [
  { key: "collecting", label: "収集" },
  { key: "scoring", label: "スコアリング" },
  { key: "researching", label: "リサーチ" },
  { key: "completed", label: "完了" },
] as const;

function getActiveIndex(status: CollectionStatus): number {
  return steps.findIndex((s) => s.key === status);
}

export default function StatusIndicator({ status }: StatusIndicatorProps) {
  const activeIndex = getActiveIndex(status);

  return (
    <div
      className="flex items-center gap-4 px-4 py-3"
      style={{
        backgroundColor: "var(--color-primary-bg)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <span
        className="text-xs font-medium"
        style={{ color: "var(--color-text-muted)" }}
      >
        処理ステータス
      </span>
      <div className="flex items-center flex-1">
        {steps.map((step, i) => (
          <div key={step.key} className="flex items-center flex-1 last:flex-none">
            <div className="flex items-center gap-2">
              <div
                className="rounded-full"
                style={{
                  width: "8px",
                  height: "8px",
                  backgroundColor:
                    i <= activeIndex
                      ? "var(--color-primary)"
                      : "var(--color-border)",
                }}
              />
              <span
                className="text-xs font-medium"
                style={{
                  color:
                    i <= activeIndex
                      ? "var(--color-text-dark)"
                      : "var(--color-text-muted)",
                }}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className="flex-1 mx-2"
                style={{
                  height: "2px",
                  backgroundColor:
                    i < activeIndex
                      ? "var(--color-primary)"
                      : "var(--color-border)",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

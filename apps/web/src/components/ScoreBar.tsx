type ScoreBarProps = {
  score: number; // 0.0 - 1.0
};

export default function ScoreBar({ score }: ScoreBarProps) {
  const percent = Math.round(score * 100);

  return (
    <div className="flex items-center gap-2">
      <span
        className="text-xl font-bold"
        style={{ color: "var(--color-primary)" }}
      >
        {score.toFixed(2)}
      </span>
      <div className="flex-1">
        <div
          className="w-full overflow-hidden"
          style={{
            height: "6px",
            backgroundColor: "var(--color-border-light)",
            borderRadius: "var(--radius-full)",
          }}
        >
          <div
            style={{
              width: `${percent}%`,
              height: "100%",
              backgroundColor: "var(--color-primary)",
              borderRadius: "var(--radius-full)",
            }}
          />
        </div>
      </div>
    </div>
  );
}

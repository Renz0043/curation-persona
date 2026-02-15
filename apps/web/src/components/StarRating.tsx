"use client";

import { useState } from "react";

type StarRatingProps = {
  value: number;
  onChange?: (value: number) => void;
};

export default function StarRating({ value, onChange }: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  const readOnly = !onChange;

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <span
          key={star}
          role={readOnly ? undefined : "button"}
          className={`text-lg transition-colors ${readOnly ? "" : "cursor-pointer"}`}
          style={{
            color:
              star <= (hovered || value)
                ? "var(--color-star)"
                : "var(--color-border)",
          }}
          onMouseEnter={readOnly ? undefined : () => setHovered(star)}
          onMouseLeave={readOnly ? undefined : () => setHovered(0)}
          onClick={readOnly ? undefined : () => onChange?.(star)}
        >
          ★
        </span>
      ))}
    </div>
  );
}

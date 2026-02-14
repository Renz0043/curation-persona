"use client";

import { useState } from "react";

type StarRatingProps = {
  value: number;
  onChange?: (value: number) => void;
};

export default function StarRating({ value, onChange }: StarRatingProps) {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className="text-lg transition-colors cursor-pointer"
          style={{
            color:
              star <= (hovered || value)
                ? "var(--color-star)"
                : "var(--color-border)",
          }}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
          onClick={() => onChange?.(star)}
        >
          ★
        </button>
      ))}
    </div>
  );
}

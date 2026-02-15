"use client";

import { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

type CalendarPickerProps = {
  selectedDate: string | null;
  onSelectDate: (date: string | null) => void;
  /** 記事が存在する日付の Set ("YYYY-MM-DD") */
  availableDates: Set<string>;
};

const WEEKDAYS = ["日", "月", "火", "水", "木", "金", "土"];

export default function CalendarPicker({
  selectedDate,
  onSelectDate,
  availableDates,
}: CalendarPickerProps) {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth()); // 0-indexed

  const days = useMemo(() => {
    const firstDay = new Date(viewYear, viewMonth, 1);
    const startDow = firstDay.getDay(); // 0=Sun
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();

    const cells: (string | null)[] = [];
    // 先頭の空白
    for (let i = 0; i < startDow; i++) cells.push(null);
    // 日付
    for (let d = 1; d <= daysInMonth; d++) {
      const mm = String(viewMonth + 1).padStart(2, "0");
      const dd = String(d).padStart(2, "0");
      cells.push(`${viewYear}-${mm}-${dd}`);
    }
    return cells;
  }, [viewYear, viewMonth]);

  const goToPrevMonth = () => {
    if (viewMonth === 0) {
      setViewYear((y) => y - 1);
      setViewMonth(11);
    } else {
      setViewMonth((m) => m - 1);
    }
  };

  const goToNextMonth = () => {
    if (viewMonth === 11) {
      setViewYear((y) => y + 1);
      setViewMonth(0);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  const handleClick = (dateStr: string) => {
    onSelectDate(selectedDate === dateStr ? null : dateStr);
  };

  return (
    <div
      className="p-3"
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        backgroundColor: "var(--color-bg)",
        width: 280,
      }}
    >
      {/* Header: Month navigation */}
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={goToPrevMonth}
          className="p-1 bg-transparent border-none cursor-pointer"
          style={{ color: "var(--color-text-muted)" }}
        >
          <ChevronLeft size={16} />
        </button>
        <span
          className="text-sm font-semibold"
          style={{ color: "var(--color-text-dark)" }}
        >
          {viewYear}年{viewMonth + 1}月
        </span>
        <button
          onClick={goToNextMonth}
          className="p-1 bg-transparent border-none cursor-pointer"
          style={{ color: "var(--color-text-muted)" }}
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Weekday header */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map((wd) => (
          <div
            key={wd}
            className="text-center text-[10px] font-medium py-1"
            style={{ color: "var(--color-text-muted)" }}
          >
            {wd}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7">
        {days.map((dateStr, i) => {
          if (!dateStr) {
            return <div key={`empty-${i}`} />;
          }
          const day = parseInt(dateStr.split("-")[2], 10);
          const isSelected = selectedDate === dateStr;
          const hasArticles = availableDates.has(dateStr);

          return (
            <button
              key={dateStr}
              onClick={() => hasArticles && handleClick(dateStr)}
              disabled={!hasArticles}
              className="flex flex-col items-center justify-center py-1 bg-transparent border-none text-xs transition-colors duration-100"
              style={{
                cursor: hasArticles ? "pointer" : "default",
                borderRadius: "var(--radius-sm)",
                color: isSelected
                  ? "#fff"
                  : hasArticles
                    ? "var(--color-text-dark)"
                    : "var(--color-border)",
                backgroundColor: isSelected
                  ? "var(--color-primary)"
                  : "transparent",
                fontWeight: hasArticles ? 600 : 400,
              }}
            >
              {day}
              {hasArticles && !isSelected && (
                <span
                  className="block w-1 h-1 rounded-full mt-0.5"
                  style={{ backgroundColor: "var(--color-primary-soft)" }}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

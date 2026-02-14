"use client";

import { useState } from "react";
import { Folder, FolderOpen } from "lucide-react";

type DateEntry = {
  date: string; // "2025-01-15"
  label: string; // "1月15日 (水)"
  hasArticles: boolean;
};

type YearGroup = {
  year: number;
  months: {
    month: number;
    label: string; // "1月"
    dates: DateEntry[];
  }[];
};

// モックデータ
const mockDateTree: YearGroup[] = [
  {
    year: 2025,
    months: [
      {
        month: 1,
        label: "1月",
        dates: [
          { date: "2025-01-15", label: "1月15日 (水)", hasArticles: true },
          { date: "2025-01-14", label: "1月14日 (火)", hasArticles: true },
          { date: "2025-01-13", label: "1月13日 (月)", hasArticles: false },
          { date: "2025-01-12", label: "1月12日 (日)", hasArticles: true },
          { date: "2025-01-11", label: "1月11日 (土)", hasArticles: true },
          { date: "2025-01-10", label: "1月10日 (金)", hasArticles: true },
        ],
      },
      {
        month: 12,
        label: "12月",
        dates: [
          { date: "2024-12-28", label: "12月28日 (土)", hasArticles: true },
          { date: "2024-12-27", label: "12月27日 (金)", hasArticles: true },
        ],
      },
    ],
  },
  {
    year: 2024,
    months: [
      {
        month: 11,
        label: "11月",
        dates: [
          { date: "2024-11-30", label: "11月30日 (土)", hasArticles: true },
          { date: "2024-11-29", label: "11月29日 (金)", hasArticles: true },
        ],
      },
    ],
  },
];

type DateTreeProps = {
  selectedDate: string | null;
  onSelectDate: (date: string | null) => void;
};

export default function DateTree({ selectedDate, onSelectDate }: DateTreeProps) {
  const [expandedYears, setExpandedYears] = useState<Record<number, boolean>>({
    2025: true,
  });

  const toggleYear = (year: number) => {
    setExpandedYears((prev) => ({ ...prev, [year]: !prev[year] }));
  };

  const handleDateClick = (date: string) => {
    onSelectDate(selectedDate === date ? null : date);
  };

  return (
    <div className="py-4 pr-4">
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-3 px-2"
        style={{ color: "var(--color-text-muted)" }}
      >
        デイリーブリーフィング
      </div>

      <div className="flex flex-col gap-1">
        {mockDateTree.map((yearGroup) => {
          const isExpanded = expandedYears[yearGroup.year] ?? false;
          const YearIcon = isExpanded ? FolderOpen : Folder;

          return (
            <div key={yearGroup.year}>
              {/* Year header */}
              <button
                onClick={() => toggleYear(yearGroup.year)}
                className="flex items-center gap-2 w-full px-2 py-1.5 text-sm font-semibold bg-transparent border-none cursor-pointer transition-colors duration-150"
                style={{ color: "var(--color-text-dark)" }}
              >
                <YearIcon size={14} style={{ color: "var(--color-primary)" }} />
                {yearGroup.year}年
              </button>

              {/* Months & Dates */}
              {isExpanded &&
                yearGroup.months.map((month) => (
                  <div key={`${yearGroup.year}-${month.month}`} className="ml-4">
                    <div
                      className="text-xs font-medium px-2 py-1 mt-1"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      {month.label}
                    </div>
                    <div className="flex flex-col">
                      {month.dates.map((entry) => {
                        const isSelected = selectedDate === entry.date;
                        return (
                          <button
                            key={entry.date}
                            onClick={() => handleDateClick(entry.date)}
                            className="flex items-center gap-2 w-full px-2 py-1 text-xs bg-transparent border-none cursor-pointer transition-colors duration-150 text-left"
                            style={{
                              borderRadius: "var(--radius-sm)",
                              color: isSelected
                                ? "var(--color-primary)"
                                : "var(--color-text-muted)",
                              backgroundColor: isSelected
                                ? "var(--color-primary-bg)"
                                : "transparent",
                              opacity: entry.hasArticles ? 1 : 0.6,
                            }}
                          >
                            <span
                              className="text-[8px]"
                              style={{
                                color: isSelected
                                  ? "var(--color-primary)"
                                  : "var(--color-text-muted)",
                              }}
                            >
                              {isSelected ? "●" : "○"}
                            </span>
                            <span>{entry.label}</span>
                            {!entry.hasArticles && (
                              <span
                                className="text-[10px] px-1 rounded"
                                style={{
                                  backgroundColor: "var(--color-border-light)",
                                  color: "var(--color-text-muted)",
                                }}
                              >
                                休
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

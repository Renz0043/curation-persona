"use client";

import { useState } from "react";
import { Folder, FolderOpen } from "lucide-react";

export type DateEntry = {
  date: string; // "2025-01-15"
  label: string; // "1月15日 (水)"
  hasArticles: boolean;
};

export type MonthGroup = {
  month: number;
  label: string; // "1月"
  dates: DateEntry[];
};

export type YearGroup = {
  year: number;
  months: MonthGroup[];
};

type DateTreeProps = {
  selectedDate: string | null;
  onSelectDate: (date: string | null) => void;
  data?: YearGroup[];
};

export default function DateTree({ selectedDate, onSelectDate, data }: DateTreeProps) {
  const treeData = data ?? [];

  const firstYear = treeData.length > 0 ? treeData[0].year : new Date().getFullYear();
  const [expandedYears, setExpandedYears] = useState<Record<number, boolean>>({
    [firstYear]: true,
  });

  const toggleYear = (year: number) => {
    setExpandedYears((prev) => ({ ...prev, [year]: !prev[year] }));
  };

  const handleDateClick = (date: string) => {
    onSelectDate(selectedDate === date ? null : date);
  };

  if (treeData.length === 0) {
    return (
      <div className="py-4 pr-4">
        <div
          className="text-xs font-semibold uppercase tracking-wider mb-3 px-2"
          style={{ color: "var(--color-text-muted)" }}
        >
          デイリーブリーフィング
        </div>
        <div className="px-2 text-xs" style={{ color: "var(--color-text-muted)" }}>
          データがありません
        </div>
      </div>
    );
  }

  return (
    <div className="py-4 pr-4">
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-3 px-2"
        style={{ color: "var(--color-text-muted)" }}
      >
        デイリーブリーフィング
      </div>

      <div className="flex flex-col gap-1">
        {treeData.map((yearGroup) => {
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

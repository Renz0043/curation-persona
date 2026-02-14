"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Newspaper, FolderOpen, User, LogOut } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "今日のブリーフィング", icon: Newspaper },
  { href: "/dashboard/archive", label: "アーカイブ", icon: FolderOpen },
  { href: "/dashboard/profile", label: "興味・関心プロファイル", icon: User },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col w-64 min-h-screen border-r"
      style={{
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-bg)",
      }}
    >
      {/* Logo */}
      <div className="px-6 py-5">
        <Link href="/dashboard" className="flex items-center gap-3 no-underline">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg text-sm font-bold text-white"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            CP
          </div>
          <div>
            <div
              className="text-sm font-bold"
              style={{ color: "var(--color-text-dark)" }}
            >
              Curation Persona
            </div>
            <div className="text-xs" style={{ color: "var(--color-text-muted)" }}>
              AIキュレーション
            </div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2">
        <ul className="flex flex-col gap-1 list-none p-0 m-0">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 text-sm font-medium no-underline transition-all duration-200"
                  style={{
                    borderRadius: "var(--radius-lg)",
                    color: isActive
                      ? "var(--color-primary)"
                      : "var(--color-text-muted)",
                    backgroundColor: isActive
                      ? "var(--color-primary-bg)"
                      : "transparent",
                    borderLeft: isActive
                      ? "3px solid var(--color-primary)"
                      : "3px solid transparent",
                  }}
                >
                  <Icon size={18} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Info (Mock) */}
      <div
        className="px-4 py-4 mx-3 mb-3"
        style={{
          borderTop: "1px solid var(--color-border)",
        }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold text-white"
            style={{ backgroundColor: "var(--color-primary-soft)" }}
          >
            U
          </div>
          <div>
            <div
              className="text-sm font-medium"
              style={{ color: "var(--color-text-dark)" }}
            >
              ユーザー
            </div>
            <div className="text-xs" style={{ color: "var(--color-text-muted)" }}>
              user@example.com
            </div>
          </div>
        </div>
        <button
          className="flex items-center gap-2 text-xs font-medium cursor-pointer bg-transparent border-none"
          style={{ color: "var(--color-text-muted)" }}
        >
          <LogOut size={14} />
          ログアウト
        </button>
      </div>
    </aside>
  );
}

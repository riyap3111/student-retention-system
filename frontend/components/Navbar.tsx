"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview", exact: true },
  { href: "/predict", label: "Predict" },
  { href: "/model", label: "Model Info" },
  { href: "/monitoring", label: "Monitoring" },
  { href: "/admissions", label: "Admissions" },
];

function Mark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path
        d="M3 17 9 9l4 4 8-10"
        stroke="url(#mark-gradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <defs>
        <linearGradient id="mark-gradient" x1="3" y1="20" x2="21" y2="3">
          <stop stopColor="#a78bfa" />
          <stop offset="1" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border-subtle)] bg-[var(--bg-void)]/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3.5">
        <div className="flex items-center gap-2">
          <Mark />
          <span className="font-display text-sm font-semibold tracking-tight text-[var(--text-primary)]">
            Student Retention<span className="text-[var(--accent-bright)]">.</span>
          </span>
        </div>
        <nav className="flex gap-1 rounded-full border border-[var(--border-subtle)] bg-white/[0.02] p-1">
          {LINKS.map((link) => {
            const isActive = link.exact ? pathname === link.href : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-[var(--accent)] text-white shadow-[0_0_16px_-2px_var(--accent-glow)]"
                    : "text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

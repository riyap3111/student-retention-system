"use client";

import { useEffect, useState } from "react";
import { getAdmissionsHealth } from "@/lib/api";
import StatCard from "@/components/StatCard";
import type { AdmissionsHealthResponse } from "@/lib/types";

export default function Admissions() {
  const [health, setHealth] = useState<AdmissionsHealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdmissionsHealth()
      .then(setHealth)
      .catch(() => setError("unreachable"));
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-10">
      <div>
        <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">Admissions Review Pipeline</h1>
        <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">
          Automates the first pass of transfer-admission eligibility review: a transcript is uploaded,
          extracted by Gemini, run through a multi-agent validation layer, checked against rules an LLM
          parsed out of the admissions handbook, and verified against a course catalog — producing a draft
          recommendation a human admissions officer reviews before anything is final.
        </p>
      </div>

      {error ? (
        <div className="glass-panel border-[var(--risk-high)]/30 p-4 text-sm text-[var(--text-secondary)]">
          Can&apos;t reach the admissions API.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard label="Pipeline status" value={health?.status === "ok" ? "Online" : "—"} />
          <StatCard label="Current phase" value="1 of 6" caption="Foundation" accent="cyan" />
          <StatCard label="Backend tests" value="28" caption="synthetic data, LLM client, storage" />
        </div>
      )}

      <div className="glass-panel p-5">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Build status
        </h2>
        <ul className="space-y-1.5 text-sm text-[var(--text-secondary)]">
          <li>✅ Foundation — data model, synthetic transcript/handbook generators, mockable Gemini client</li>
          <li className="text-[var(--text-muted)]">⬜ Extraction — real Gemini wiring, upload → extract → store</li>
          <li className="text-[var(--text-muted)]">⬜ Multi-agent validation + handbook rules extraction</li>
          <li className="text-[var(--text-muted)]">⬜ Course catalog (mock, pluggable for a real source later)</li>
          <li className="text-[var(--text-muted)]">⬜ Decision engine + human-in-the-loop review</li>
          <li className="text-[var(--text-muted)]">⬜ Reporting (secondary)</li>
        </ul>
      </div>

      <p className="text-xs text-[var(--text-muted)]">
        Entirely synthetic data — no real applicant records, and not affiliated with any real university.
      </p>
    </div>
  );
}

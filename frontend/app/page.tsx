"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_BASE_URL, getAdmissionsHealth, getHealth, getModelInfo } from "@/lib/api";
import PrivacyNotice from "@/components/PrivacyNotice";
import StatCard from "@/components/StatCard";
import type { AdmissionsHealthResponse, HealthResponse, ModelInfoResponse } from "@/lib/types";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [admissionsHealth, setAdmissionsHealth] = useState<AdmissionsHealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setError("unreachable"));
    getModelInfo()
      .then(setModelInfo)
      .catch(() => {
        /* model_info 503s until a model is trained; health check above already surfaces connectivity issues */
      });
    getAdmissionsHealth()
      .then(setAdmissionsHealth)
      .catch(() => {
        /* same backend process — if /health above is reachable this basically can't fail, but don't assume */
      });
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-14">
      <div>
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--border-subtle)] bg-white/[0.02] px-3 py-1 text-xs font-medium text-[var(--text-secondary)]">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-bright)]" />
          Portfolio ML/AI system · synthetic data
        </div>
        <h1 className="font-display text-4xl font-bold leading-tight text-[var(--text-primary)] sm:text-5xl">
          Two sides of the student{" "}
          <span className="bg-gradient-to-r from-[var(--accent-bright)] to-[var(--cyan)] bg-clip-text text-transparent">
            lifecycle
          </span>
          , automated.
        </h1>
        <p className="mt-4 max-w-2xl text-[var(--text-secondary)]">
          An ensemble model predicts whether an enrolled student continues next term and explains why with
          SHAP, with live feature-drift monitoring — and a separate pipeline automates the first pass of
          transfer-admission eligibility review: transcript extraction, multi-agent validation, handbook-rules
          checking, and course-catalog verification, with a human reviewing every decision. One FastAPI
          backend, one Next.js frontend.
        </p>
      </div>

      <PrivacyNotice />

      {error && (
        <div className="glass-panel border-[var(--risk-high)]/30 p-4 text-sm text-[var(--text-secondary)]">
          Can&apos;t reach the API at{" "}
          <code className="font-mono-ui rounded bg-white/5 px-1.5 py-0.5 text-[var(--risk-high)]">
            {API_BASE_URL}
          </code>
          . Start it with:
          <pre className="font-mono-ui mt-2 overflow-x-auto rounded-lg border border-[var(--border-subtle)] bg-black/30 p-3 text-xs text-[var(--text-secondary)]">
            export PYTHONPATH=src{"\n"}uvicorn student_journey.api.main:app --port 8000
          </pre>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="API status" value={health.status === "ok" ? "Online" : "Down"} />
          <StatCard
            label="Retention model loaded"
            value={health.model_loaded ? "Yes" : "No"}
            caption={health.model_version ?? undefined}
            accent="cyan"
          />
          {modelInfo && <StatCard label="Test ROC-AUC" value={Number(modelInfo.test_metrics.roc_auc).toFixed(3)} />}
          <StatCard
            label="Admissions pipeline"
            value={admissionsHealth?.status === "ok" ? "Online" : "—"}
            caption="Phase 1: foundation"
            accent="cyan"
          />
        </div>
      )}

      <div className="flex flex-wrap gap-3 pt-2">
        <Link
          href="/predict"
          className="rounded-full bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white shadow-[0_0_24px_-4px_var(--accent-glow)] transition-transform hover:scale-[1.02] hover:bg-[var(--accent-bright)]"
        >
          Try a retention prediction →
        </Link>
        <Link
          href="/admissions"
          className="rounded-full border border-[var(--border-strong)] bg-white/[0.02] px-5 py-2.5 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-white/5"
        >
          View admissions pipeline
        </Link>
        <a
          href="https://github.com/riyap3111/student-retention-system"
          target="_blank"
          rel="noreferrer"
          className="rounded-full border border-[var(--border-strong)] bg-white/[0.02] px-5 py-2.5 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-white/5"
        >
          View source on GitHub
        </a>
      </div>
    </div>
  );
}

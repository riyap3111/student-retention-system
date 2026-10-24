"use client";

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  createApplicant,
  extractTranscript,
  getAdmissionsHealth,
  uploadTranscript,
} from "@/lib/api";
import StatCard from "@/components/StatCard";
import type { AdmissionsHealthResponse, DocumentResponse, ExtractedTranscriptResponse } from "@/lib/types";

const inputClass =
  "mt-1.5 w-full rounded-lg border border-[var(--border-subtle)] bg-black/20 px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition-colors focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent-soft)]";
const labelClass = "block text-sm font-medium text-[var(--text-secondary)]";

type Step = "applicant" | "upload" | "extract" | "done";

export default function Admissions() {
  const [health, setHealth] = useState<AdmissionsHealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [name, setName] = useState("Jordan Nguyen");
  const [email, setEmail] = useState("jordan.nguyen@example.com");
  const [applicantId, setApplicantId] = useState<number | null>(null);
  const [uploadedDocument, setUploadedDocument] = useState<DocumentResponse | null>(null);
  const [extracted, setExtracted] = useState<ExtractedTranscriptResponse | null>(null);

  const [step, setStep] = useState<Step>("applicant");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getAdmissionsHealth()
      .then(setHealth)
      .catch(() => setHealthError("unreachable"));
  }, []);

  const handleCreateApplicant = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const applicant = await createApplicant({ name, email });
      setApplicantId(applicant.id);
      setStep("upload");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed. Is the API running?");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file || applicantId === null) return;
    setLoading(true);
    setError(null);
    try {
      const uploaded = await uploadTranscript(applicantId, file);
      setUploadedDocument(uploaded);
      setStep("extract");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Is the API running?");
    } finally {
      setLoading(false);
    }
  };

  const handleExtract = async () => {
    if (!uploadedDocument) return;
    setLoading(true);
    setError(null);
    try {
      const result = await extractTranscript(uploadedDocument.id);
      setExtracted(result);
      setStep("done");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Extraction failed. Is GEMINI_API_KEY set?");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setApplicantId(null);
    setUploadedDocument(null);
    setExtracted(null);
    setStep("applicant");
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

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

      {healthError ? (
        <div className="glass-panel border-[var(--risk-high)]/30 p-4 text-sm text-[var(--text-secondary)]">
          Can&apos;t reach the admissions API.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard label="Pipeline status" value={health?.status === "ok" ? "Online" : "—"} />
          <StatCard label="Current phase" value="2 of 6" caption="Extraction" accent="cyan" />
          <StatCard label="Backend tests" value="119" caption="whole project, incl. admissions" />
        </div>
      )}

      <div className="glass-panel p-5">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Build status
        </h2>
        <ul className="space-y-1.5 text-sm text-[var(--text-secondary)]">
          <li>✅ Foundation — data model, synthetic transcript/handbook generators, mockable Gemini client</li>
          <li>✅ Extraction — real Gemini wiring, upload → extract → store (try it below)</li>
          <li className="text-[var(--text-muted)]">⬜ Multi-agent validation + handbook rules extraction</li>
          <li className="text-[var(--text-muted)]">⬜ Course catalog (mock, pluggable for a real source later)</li>
          <li className="text-[var(--text-muted)]">⬜ Decision engine + human-in-the-loop review</li>
          <li className="text-[var(--text-muted)]">⬜ Reporting (secondary)</li>
        </ul>
      </div>

      <div className="glass-panel space-y-5 p-6">
        <h2 className="font-display text-lg font-semibold text-[var(--text-primary)]">
          Try it: upload a transcript
        </h2>

        <ol className="flex flex-wrap gap-2 text-xs font-medium">
          {(["applicant", "upload", "extract", "done"] as Step[]).map((s, i) => {
            const stepIndex = (["applicant", "upload", "extract", "done"] as Step[]).indexOf(step);
            const isActive = i === stepIndex;
            const isDone = i < stepIndex;
            return (
              <li
                key={s}
                className={`rounded-full px-3 py-1 ${
                  isActive
                    ? "bg-[var(--accent)] text-white"
                    : isDone
                      ? "bg-[var(--accent-soft)] text-[var(--accent-bright)]"
                      : "bg-black/20 text-[var(--text-muted)]"
                }`}
              >
                {i + 1}. {s}
              </li>
            );
          })}
        </ol>

        {step === "applicant" && (
          <form onSubmit={handleCreateApplicant} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className={labelClass}>
              Applicant name
              <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label className={labelClass}>
              Email
              <input
                type="email"
                className={inputClass}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="rounded-full bg-[var(--accent)] px-6 py-2.5 text-sm font-medium text-white shadow-[0_0_24px_-4px_var(--accent-glow)] transition-transform hover:scale-[1.02] hover:bg-[var(--accent-bright)] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
              >
                {loading ? "Creating…" : "Create applicant"}
              </button>
            </div>
          </form>
        )}

        {step === "upload" && applicantId !== null && (
          <form onSubmit={handleUpload} className="space-y-4">
            <p className="text-sm text-[var(--text-secondary)]">
              Applicant <strong className="text-[var(--text-primary)]">#{applicantId}</strong> created. Upload a
              transcript PDF (any PDF works — try the synthetic ones this project generates for testing).
            </p>
            <input ref={fileInputRef} type="file" accept="application/pdf" className={inputClass} />
            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-[var(--accent)] px-6 py-2.5 text-sm font-medium text-white shadow-[0_0_24px_-4px_var(--accent-glow)] transition-transform hover:scale-[1.02] hover:bg-[var(--accent-bright)] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
            >
              {loading ? "Uploading…" : "Upload transcript"}
            </button>
          </form>
        )}

        {step === "extract" && uploadedDocument && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--text-secondary)]">
              Uploaded <strong className="text-[var(--text-primary)]">{uploadedDocument.original_filename}</strong>{" "}
              (document #{uploadedDocument.id}). Ready to extract with Gemini.
            </p>
            <button
              type="button"
              onClick={handleExtract}
              disabled={loading}
              className="rounded-full bg-[var(--accent)] px-6 py-2.5 text-sm font-medium text-white shadow-[0_0_24px_-4px_var(--accent-glow)] transition-transform hover:scale-[1.02] hover:bg-[var(--accent-bright)] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
            >
              {loading ? "Extracting…" : "Extract with Gemini"}
            </button>
          </div>
        )}

        {step === "done" && extracted && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <StatCard label="Institution" value={extracted.institution_name ?? "—"} />
              <StatCard label="Cumulative GPA" value={extracted.cumulative_gpa?.toFixed(2) ?? "—"} accent="cyan" />
              <StatCard label="Courses found" value={String(extracted.courses_json.length)} />
            </div>
            {extracted.courses_json.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-[var(--border-subtle)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-black/20 text-xs uppercase tracking-wider text-[var(--text-muted)]">
                    <tr>
                      <th className="px-3 py-2">Code</th>
                      <th className="px-3 py-2">Course</th>
                      <th className="px-3 py-2">Credits</th>
                      <th className="px-3 py-2">Grade</th>
                      <th className="px-3 py-2">Term</th>
                    </tr>
                  </thead>
                  <tbody className="text-[var(--text-secondary)]">
                    {extracted.courses_json.map((course, i) => (
                      <tr key={i} className="border-t border-[var(--border-subtle)]">
                        <td className="px-3 py-2 font-mono-ui">{course.code}</td>
                        <td className="px-3 py-2">{course.name}</td>
                        <td className="px-3 py-2">{course.credits ?? "—"}</td>
                        <td className="px-3 py-2">{course.grade ?? "—"}</td>
                        <td className="px-3 py-2">{course.term ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="text-xs text-[var(--text-muted)]">Extracted by model {extracted.model_version}.</p>
            <button
              type="button"
              onClick={reset}
              className="text-xs font-medium text-[var(--text-secondary)] underline-offset-2 hover:text-[var(--text-primary)] hover:underline"
            >
              Start over with another applicant
            </button>
          </div>
        )}

        {error && (
          <div className="glass-panel border-[var(--risk-high)]/30 p-4 text-sm text-[var(--text-secondary)]">
            {error}
          </div>
        )}
      </div>

      <p className="text-xs text-[var(--text-muted)]">
        Entirely synthetic data — no real applicant records, and not affiliated with any real university.
      </p>
    </div>
  );
}

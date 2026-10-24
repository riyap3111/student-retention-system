import type {
  AdmissionsHealthResponse,
  ApiErrorBody,
  ApplicantCreateRequest,
  ApplicantDetailResponse,
  ApplicantResponse,
  DocumentResponse,
  DriftReportResponse,
  ExtractedTranscriptResponse,
  HealthResponse,
  ModelInfoResponse,
  PredictionResponse,
  StudentTermFeatures,
} from "./types";

// Resolution order: a runtime-injected value (window.__ENV__, written by
// docker-entrypoint.sh from the API_BASE_URL container env var) takes
// priority over the build-time NEXT_PUBLIC_API_BASE_URL (see .env.example,
// used for local `npm run dev`), which falls back to the local FastAPI dev
// server. Runtime injection matters because Next.js env vars are baked
// into the JS bundle at build time, but Cloud Run doesn't know the API
// service's URL until *after* deploying it — a static image built once
// and configured per-deployment via an env var avoids rebuilding the
// frontend image just to point it at a different backend. `window` is
// guarded since this file runs on the server too (Server Components) —
// there's no window there, so the build-time/default fallback applies.
export const API_BASE_URL: string =
  (typeof window !== "undefined" ? window.__ENV__?.API_BASE_URL : undefined) ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function throwIfNotOk(response: Response): Promise<void> {
  if (response.ok) return;
  const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
  const detail = body?.detail;
  const message =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d) => `${d.loc.join(".")}: ${d.msg}`).join("; ")
        : `Request failed with status ${response.status}`;
  throw new ApiError(response.status, message);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  await throwIfNotOk(response);
  return response.json() as Promise<T>;
}

// No Content-Type header here: the browser sets multipart/form-data with
// the correct boundary itself, and overriding it breaks the upload.
async function requestFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });
  await throwIfNotOk(response);
  return response.json() as Promise<T>;
}

export const getHealth = () => request<HealthResponse>("/health");

export const getModelInfo = () => request<ModelInfoResponse>("/model_info");

export const getDriftReport = () => request<DriftReportResponse>("/monitoring/drift");

export const predict = (features: StudentTermFeatures) =>
  request<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(features),
  });

export const getAdmissionsHealth = () => request<AdmissionsHealthResponse>("/admissions/health");

export const createApplicant = (payload: ApplicantCreateRequest) =>
  request<ApplicantResponse>("/admissions/applicants", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getApplicant = (applicantId: number) =>
  request<ApplicantDetailResponse>(`/admissions/applicants/${applicantId}`);

export const uploadTranscript = (applicantId: number, file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return requestFormData<DocumentResponse>(`/admissions/applicants/${applicantId}/documents`, formData);
};

export const extractTranscript = (documentId: number) =>
  request<ExtractedTranscriptResponse>(`/admissions/documents/${documentId}/extract`, { method: "POST" });

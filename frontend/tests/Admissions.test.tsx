import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Admissions from "@/app/admissions/page";

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response;
}

describe("Admissions page", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the pipeline as online when the health check succeeds", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({ status: "ok" }));

    render(<Admissions />);

    expect(await screen.findByText("Online")).toBeInTheDocument();
  });

  it("shows an unreachable message when the health check fails", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("network error"));

    render(<Admissions />);

    expect(await screen.findByText(/Can't reach the admissions API/)).toBeInTheDocument();
  });

  it("walks through applicant creation, upload, and extraction", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse({ status: "ok" })) // health
      .mockResolvedValueOnce(jsonResponse({ id: 1, name: "Jordan Nguyen", email: "jordan.nguyen@example.com" }))
      .mockResolvedValueOnce(
        jsonResponse({ id: 7, applicant_id: 1, document_type: "transcript", original_filename: "transcript.pdf" })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: 3,
          document_id: 7,
          institution_name: "Meridian Community College",
          cumulative_gpa: 3.42,
          courses_json: [{ code: "CS101", name: "Introduction to Programming", credits: 3, grade: "A", term: null }],
          model_version: "gemini-2.5-flash",
        })
      );

    render(<Admissions />);
    await screen.findByText("Online");

    await userEvent.click(screen.getByRole("button", { name: /create applicant/i }));
    // "#1" sits inside a nested <strong>, so the sentence is split across
    // elements - match on the containing <p>'s full text instead.
    await waitFor(() =>
      expect(
        screen.getByText(
          (_, node) => node?.tagName.toLowerCase() === "p" && (node.textContent?.includes("Applicant #1 created") ?? false)
        )
      ).toBeInTheDocument()
    );

    const file = new File(["%PDF-content"], "transcript.pdf", { type: "application/pdf" });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, file);
    await userEvent.click(screen.getByRole("button", { name: /upload transcript/i }));
    await screen.findByText(/Ready to extract with Gemini/);

    await userEvent.click(screen.getByRole("button", { name: /extract with gemini/i }));

    await waitFor(() => expect(screen.getByText("Meridian Community College")).toBeInTheDocument());
    expect(screen.getByText("3.42")).toBeInTheDocument();
    expect(screen.getByText("CS101")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(4);
  });
});

import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Admissions from "@/app/admissions/page";

describe("Admissions page", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the pipeline as online when the health check succeeds", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => ({ status: "ok" }) } as Response);

    render(<Admissions />);

    expect(await screen.findByText("Online")).toBeInTheDocument();
  });

  it("shows an unreachable message when the health check fails", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("network error"));

    render(<Admissions />);

    expect(await screen.findByText(/Can't reach the admissions API/)).toBeInTheDocument();
  });
});

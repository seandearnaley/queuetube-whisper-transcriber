import { render, screen } from "@testing-library/react";
import { SWRConfig } from "swr";
import { vi } from "vitest";

import HomePage from "@/app/page";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  fetchMock.mockReset();
  fetchMock.mockImplementation((input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/settings")) {
      return Promise.resolve({
        ok: true,
        json: async () => ({ cookies_configured: false, cookies_path: null })
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({ jobs: [], total: 0 })
    });
  });
});

test("renders hero and queue form", async () => {
  render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
      <HomePage />
    </SWRConfig>
  );

  expect(
    await screen.findByRole("heading", { name: /QueueTube Whisper/i })
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Add to queue/i })).toBeInTheDocument();
});

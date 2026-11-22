import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import { useAnnouncements, useCreateAnnouncement, useDepartments } from "./hooks";

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("department hooks", () => {
  it("fetches departments and announcements through the shared http client", async () => {
    vi.spyOn(http, "get").mockResolvedValue({
      data: { next: null, previous: null, results: [{ id: 1, code: "CSE", name: "CSE" }] },
    });

    const d = renderHook(() => useDepartments(), { wrapper });
    await waitFor(() => expect(d.result.current.isSuccess).toBe(true));
    expect(http.get).toHaveBeenCalledWith("/department/departments");

    const a = renderHook(() => useAnnouncements(), { wrapper });
    await waitFor(() => expect(a.result.current.isSuccess).toBe(true));
    expect(http.get).toHaveBeenCalledWith("/department/announcements");
  });

  it("posts new announcements and invalidates queries", async () => {
    vi.spyOn(http, "post").mockResolvedValue({ data: { id: 10, title: "Notice" } });

    const { result } = renderHook(() => useCreateAnnouncement(), { wrapper });
    result.current.mutate({
      department_id: 1,
      title: "Notice",
      content: "Body",
      target_roles: ["student"],
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(http.post).toHaveBeenCalledWith("/department/announcements", {
      department_id: 1,
      title: "Notice",
      content: "Body",
      target_roles: ["student"],
    });
  });
});

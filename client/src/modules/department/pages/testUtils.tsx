import { MantineProvider } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import * as authMod from "../../../auth/AuthProvider";

export function renderDeptPage(ui: ReactElement, permissions: string[] = []) {
  cleanup();
  const permSet = new Set(permissions);
  vi.spyOn(authMod, "useAuth").mockReturnValue({
    session: {
      user: {
        id: 1001, username: "u1001", display_name: "Test User", kind: "student", email: "t@inst.ac.in",
      },
      active_role: "student",
      roles: ["student"],
      permissions,
      modules: ["department"],
      navigation: [],
      csrf_token: "test-csrf",
    },
    status: "authenticated",
    can: (p: string) => permSet.has(p),
    hasModule: (m: string) => m === "department",
    switchRole: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
  });

  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MantineProvider>
      <QueryClientProvider client={qc}>
        <MemoryRouter>{ui}</MemoryRouter>
      </QueryClientProvider>
    </MantineProvider>,
  );
}

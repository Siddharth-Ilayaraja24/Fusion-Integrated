import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import RolesPage from "./RolesPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("RolesPage", () => {
  it("renders loading, empty, error, permission-gating, and assign role action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<RolesPage />, ["department.role_assignment.view"]);
    expect(screen.getByText(/loading role assignments/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /assign role/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Roles failure" } } },
    });
    renderDeptPage(<RolesPage />, ["department.role_assignment.view"]);
    await waitFor(() => expect(screen.getByText(/roles failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<RolesPage />, [
      "department.role_assignment.view",
      "department.role_assignment.assign",
    ]);
    await waitFor(() =>
      expect(screen.getByText(/no role assignments recorded/i)).toBeInTheDocument(),
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /assign role/i }));
    await user.click(await screen.findByRole("button", { name: /save assignment/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

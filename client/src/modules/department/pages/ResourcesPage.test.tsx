import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import ResourcesPage from "./ResourcesPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("ResourcesPage", () => {
  it("renders loading, empty, error, permission-gating, and add lab action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<ResourcesPage />, ["department.lab.view"]);
    expect(screen.getByText(/loading lab resources/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add lab/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Labs failure" } } },
    });
    renderDeptPage(<ResourcesPage />, ["department.lab.view"]);
    await waitFor(() => expect(screen.getByText(/labs failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<ResourcesPage />, ["department.lab.view", "department.lab.update"]);
    await waitFor(() => expect(screen.getByText(/no lab resources recorded/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /add lab/i }));
    await user.type(await screen.findByLabelText(/lab code/i), "ML-1");
    await user.type(screen.getByLabelText(/lab name/i), "AI Lab");
    await user.click(screen.getByRole("button", { name: /save lab/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

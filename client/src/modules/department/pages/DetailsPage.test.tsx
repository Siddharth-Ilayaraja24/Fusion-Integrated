import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import DetailsPage from "./DetailsPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("DetailsPage", () => {
  it("renders loading, empty, error, permission-gating, and propose change action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<DetailsPage />, ["department.department.view"]);
    expect(screen.getByText(/loading department details/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /propose official change/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Dept failure" } } },
    });
    renderDeptPage(<DetailsPage />, ["department.department.view"]);
    await waitFor(() => expect(screen.getByText(/dept failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<DetailsPage />, [
      "department.department.view",
      "department.department.update",
    ]);
    await waitFor(() => expect(screen.getByText(/no departments found/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /propose official change/i }));
    await user.type(await screen.findByLabelText(/proposed value/i), "New Policy");
    await user.click(screen.getByRole("button", { name: /submit for hod approval/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

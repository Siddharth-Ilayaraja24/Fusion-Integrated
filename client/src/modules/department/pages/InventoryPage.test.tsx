import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import InventoryPage from "./InventoryPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("InventoryPage", () => {
  it("renders loading, empty, error, permission-gating, and stock request action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<InventoryPage />, ["department.stock_request.view"]);
    expect(screen.getByText(/loading stock requests/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /request stock/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Inventory error" } } },
    });
    renderDeptPage(<InventoryPage />, ["department.stock_request.view"]);
    await waitFor(() => expect(screen.getByText(/inventory error/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<InventoryPage />, [
      "department.stock_request.view",
      "department.stock_request.create",
    ]);
    await waitFor(() => expect(screen.getByText(/no stock requests yet/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /request stock/i }));
    await user.type(await screen.findByLabelText(/purpose/i), "Lab setup");
    await user.click(screen.getByRole("button", { name: /submit request/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

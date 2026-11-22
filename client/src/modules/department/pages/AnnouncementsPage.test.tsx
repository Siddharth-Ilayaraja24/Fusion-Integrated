import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import AnnouncementsPage from "./AnnouncementsPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("AnnouncementsPage", () => {
  it("renders loading, empty, error, permission-gating, and create action", async () => {
    // Loading state.
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<AnnouncementsPage />, ["department.announcement.view"]);
    expect(screen.getByText(/loading announcements/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /new announcement/i })).not.toBeInTheDocument();

    // Error state (500).
    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Server down" } } },
    });
    renderDeptPage(<AnnouncementsPage />, ["department.announcement.view"]);
    await waitFor(() => expect(screen.getByText(/server down/i)).toBeInTheDocument());

    // Empty state + create action when permitted.
    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<AnnouncementsPage />, [
      "department.announcement.view",
      "department.announcement.create",
    ]);
    await waitFor(() => expect(screen.getByText(/no announcements yet/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /new announcement/i }));
    await user.type(await screen.findByLabelText(/title/i), "Lab Exam");
    await user.type(screen.getByLabelText(/content/i), "Tomorrow at 9 AM");
    await user.click(screen.getByRole("button", { name: /publish/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

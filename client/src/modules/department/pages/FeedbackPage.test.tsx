import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import FeedbackPage from "./FeedbackPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("FeedbackPage", () => {
  it("renders loading, empty, error, permission-gating, and submit action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<FeedbackPage />, ["department.feedback.view"]);
    expect(screen.getByText(/loading feedback/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /submit feedback/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Feedback failure" } } },
    });
    renderDeptPage(<FeedbackPage />, ["department.feedback.view"]);
    await waitFor(() => expect(screen.getByText(/feedback failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<FeedbackPage />, [
      "department.feedback.view",
      "department.feedback.create",
    ]);
    await waitFor(() => expect(screen.getByText(/no feedback items/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /submit feedback/i }));
    await user.type(await screen.findByLabelText(/subject/i), "Projector");
    await user.type(screen.getByLabelText(/message/i), "Needs repair");
    await user.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

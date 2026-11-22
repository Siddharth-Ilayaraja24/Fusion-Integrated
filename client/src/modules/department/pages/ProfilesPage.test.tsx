import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import ProfilesPage from "./ProfilesPage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("ProfilesPage", () => {
  it("renders loading, empty, error, permission-gating, and add profile action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<ProfilesPage />, ["department.profile.view"]);
    expect(screen.getByText(/loading profiles/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add profile/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Profiles failure" } } },
    });
    renderDeptPage(<ProfilesPage />, ["department.profile.view"]);
    await waitFor(() => expect(screen.getByText(/profiles failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<ProfilesPage />, ["department.profile.view", "department.profile.update"]);
    await waitFor(() => expect(screen.getByText(/no visible profiles/i)).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /add profile/i }));
    await user.type(await screen.findByLabelText(/display name/i), "Asha Verma");
    await user.click(screen.getByRole("button", { name: /save profile/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

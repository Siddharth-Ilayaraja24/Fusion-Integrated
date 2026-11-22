import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { http } from "../../../lib/http";
import TimetablePage from "./TimetablePage";
import { renderDeptPage } from "./testUtils";

afterEach(() => vi.restoreAllMocks());

describe("TimetablePage", () => {
  it("renders loading, empty, error, permission-gating, and add slot action", async () => {
    vi.spyOn(http, "get").mockImplementation(() => new Promise(() => {}));
    renderDeptPage(<TimetablePage />, ["department.timetable.view"]);
    expect(screen.getByText(/loading timetable/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add slot/i })).not.toBeInTheDocument();

    vi.spyOn(http, "get").mockRejectedValue({
      response: { status: 500, data: { error: { message: "Timetable failure" } } },
    });
    renderDeptPage(<TimetablePage />, ["department.timetable.view"]);
    await waitFor(() => expect(screen.getByText(/timetable failure/i)).toBeInTheDocument());

    vi.spyOn(http, "get").mockResolvedValue({ data: { results: [] } });
    const postSpy = vi.spyOn(http, "post").mockResolvedValue({ data: { id: 1 } });
    renderDeptPage(<TimetablePage />, [
      "department.timetable.view",
      "department.timetable.create",
    ]);
    await waitFor(() =>
      expect(screen.getByText(/no timetable slots published/i)).toBeInTheDocument(),
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /add slot/i }));
    await user.type(await screen.findByLabelText(/course code/i), "CS201");
    await user.type(screen.getByLabelText(/course title/i), "DSA");
    await user.type(screen.getByLabelText(/room/i), "L-101");
    await user.click(screen.getByRole("button", { name: /save slot/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});

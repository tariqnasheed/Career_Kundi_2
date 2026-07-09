import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  EMPTY_JOB_FORM,
} from "../../lib/jobForm";
import {
  JobDetailsForm,
} from "./JobDetailsForm";

describe("JobDetailsForm framing", () => {
  it("uses neutral review-and-edit wording for the shared job form", () => {
    render(
      <JobDetailsForm
        form={{
          ...EMPTY_JOB_FORM,
          title: "Software Engineer",
        }}
        onChange={vi.fn()}
        onSave={vi.fn()}
        onGeneratePack={vi.fn()}
      />,
    );

    expect(
      screen.getByText(
        /Step 2 — Review and edit job details\./i,
      ),
    ).toBeTruthy();

    expect(
      screen.queryByText(/extracted job fields/i),
    ).toBeNull();

    expect(
      screen.getByText(/Company is optional\./i),
    ).toBeTruthy();
  });
});

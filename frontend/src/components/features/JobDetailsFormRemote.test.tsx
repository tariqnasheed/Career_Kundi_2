import {
  fireEvent,
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
  JobDetailsForm,
} from "./JobDetailsForm";
import {
  EMPTY_JOB_FORM,
} from "../../lib/jobForm";


function renderRemoteForm(
  isRemote: boolean | null,
  onChange = vi.fn(),
) {
  render(
    <JobDetailsForm
      form={{
        ...EMPTY_JOB_FORM,
        title: "Engineer",
        is_remote: isRemote,
      }}
      onChange={onChange}
      onSave={vi.fn()}
      onGeneratePack={vi.fn()}
    />,
  );

  return onChange;
}


describe("JobDetailsForm remote semantics", () => {
  it("renders null as unchecked without converting form state", () => {
    renderRemoteForm(null);

    expect(
      screen.getByRole(
        "checkbox",
        {
          name: "Remote position",
        },
      ),
    ).not.toBeChecked();
  });

  it("renders explicit false as unchecked", () => {
    renderRemoteForm(false);

    expect(
      screen.getByRole(
        "checkbox",
        {
          name: "Remote position",
        },
      ),
    ).not.toBeChecked();
  });

  it("renders explicit true as checked", () => {
    renderRemoteForm(true);

    expect(
      screen.getByRole(
        "checkbox",
        {
          name: "Remote position",
        },
      ),
    ).toBeChecked();
  });

  it("emits an explicit boolean after checkbox interaction", () => {
    const onChange = renderRemoteForm(
      null,
    );

    fireEvent.click(
      screen.getByRole(
        "checkbox",
        {
          name: "Remote position",
        },
      ),
    );

    expect(onChange).toHaveBeenCalledWith({
      ...EMPTY_JOB_FORM,
      title: "Engineer",
      is_remote: true,
    });
  });
});

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
  SavedJobFilters,
  type VisibleSavedJobSearchFilters,
} from "./SavedJobFilters";


const EMPTY_FILTERS: VisibleSavedJobSearchFilters = {
  q: "",
  location: "",
  employmentType: "",
  remote: undefined,
};


describe("SavedJobFilters", () => {
  it("emits updated keyword text while preserving other values", () => {
    const onChange = vi.fn();

    render(
      <SavedJobFilters
        filters={{
          ...EMPTY_FILTERS,
          location: "London",
        }}
        onChange={onChange}
        onClearAll={vi.fn()}
      />,
    );

    fireEvent.change(
      screen.getByLabelText("Keywords"),
      {
        target: {
          value: "Platform Engineer",
        },
      },
    );

    expect(onChange).toHaveBeenCalledWith({
      q: "Platform Engineer",
      location: "London",
      employmentType: "",
      remote: undefined,
    });
  });

  it("emits updated location and employment text without normalizing them", () => {
    const onChange = vi.fn();

    render(
      <SavedJobFilters
        filters={EMPTY_FILTERS}
        onChange={onChange}
        onClearAll={vi.fn()}
      />,
    );

    fireEvent.change(
      screen.getByLabelText("Location"),
      {
        target: {
          value: "  London  ",
        },
      },
    );

    expect(onChange).toHaveBeenNthCalledWith(
      1,
      {
        q: "",
        location: "  London  ",
        employmentType: "",
        remote: undefined,
      },
    );

    fireEvent.change(
      screen.getByLabelText("Employment type"),
      {
        target: {
          value: " Full-time ",
        },
      },
    );

    expect(onChange).toHaveBeenNthCalledWith(
      2,
      {
        q: "",
        location: "",
        employmentType: " Full-time ",
        remote: undefined,
      },
    );
  });

  it("emits only undefined or true from the visible remote controls", () => {
    const onChange = vi.fn();

    const { rerender } = render(
      <SavedJobFilters
        filters={EMPTY_FILTERS}
        onChange={onChange}
        onClearAll={vi.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole(
        "button",
        {
          name: "Remote only",
        },
      ),
    );

    expect(onChange).toHaveBeenLastCalledWith({
      ...EMPTY_FILTERS,
      remote: true,
    });

    rerender(
      <SavedJobFilters
        filters={{
          ...EMPTY_FILTERS,
          remote: true,
        }}
        onChange={onChange}
        onClearAll={vi.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole(
        "button",
        {
          name: "Any",
        },
      ),
    );

    expect(onChange).toHaveBeenLastCalledWith({
      ...EMPTY_FILTERS,
      remote: undefined,
    });

    expect(
      onChange.mock.calls.some(
        ([value]) => value.remote === false,
      ),
    ).toBe(false);
  });

  it("does not expose misleading false-remote labels", () => {
    render(
      <SavedJobFilters
        filters={EMPTY_FILTERS}
        onChange={vi.fn()}
        onClearAll={vi.fn()}
      />,
    );

    expect(
      screen.queryByText("On-site"),
    ).toBeNull();

    expect(
      screen.queryByText("Not remote"),
    ).toBeNull();

    expect(
      screen.queryByText("Not marked remote"),
    ).toBeNull();
  });

  it("enables Clear all only while a visible filter is active", () => {
    const onClearAll = vi.fn();

    const { rerender } = render(
      <SavedJobFilters
        filters={EMPTY_FILTERS}
        onChange={vi.fn()}
        onClearAll={onClearAll}
      />,
    );

    expect(
      screen.getByRole(
        "button",
        {
          name: "Clear all",
        },
      ),
    ).toBeDisabled();

    rerender(
      <SavedJobFilters
        filters={{
          ...EMPTY_FILTERS,
          remote: true,
        }}
        onChange={vi.fn()}
        onClearAll={onClearAll}
      />,
    );

    const clearAll = screen.getByRole(
      "button",
      {
        name: "Clear all",
      },
    );

    expect(clearAll).toBeEnabled();

    fireEvent.click(clearAll);

    expect(onClearAll).toHaveBeenCalledTimes(1);
  });
});

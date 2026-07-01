/**
 * test-setup.ts
 * Vitest + @testing-library/react global test setup.
 *
 * Import once in vitest.config.ts via setupFiles.
 */

import "@testing-library/jest-dom";

// Suppress console.error for expected React warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    const msg = args[0];
    if (typeof msg === "string" && msg.includes("Warning:")) return;
    originalError(...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// DOM-only globals (jsdom). Guarded with a `window` check so this shared setup
// file is also safe to load in the `node` test environment used by non-DOM
// unit tests (e.g. the API-surface test).
if (typeof window !== "undefined") {
  // Mock window.matchMedia (jsdom doesn't implement it)
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });

  // Mock IntersectionObserver
  class MockIntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  Object.defineProperty(window, "IntersectionObserver", {
    writable: true,
    value: MockIntersectionObserver,
  });

  // Silence framer-motion warnings in test environment
  window.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

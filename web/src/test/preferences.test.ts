import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { applyTheme, usePreferences } from "@/preferences";

const INITIAL_STATE = usePreferences.getState();

function savedPreferences() {
  return JSON.parse(localStorage.getItem("scorecaster-preferences") ?? "null");
}

describe("usePreferences", () => {
  beforeEach(() => usePreferences.setState(INITIAL_STATE, true));

  it("starts following the OS, on the Premier League", () => {
    const { theme, lastLeague } = usePreferences.getState();
    expect(theme).toBeNull();
    expect(lastLeague).toEqual({ code: "E0" });
  });

  it("saves the chosen theme to localStorage", () => {
    usePreferences.getState().setTheme("dark");
    expect(usePreferences.getState().theme).toBe("dark");
    expect(savedPreferences()).toMatchObject({ state: { theme: "dark" } });
  });

  it("saves the last league with its season", () => {
    usePreferences.getState().setLastLeague({ code: "SP1", season: 2020 });
    expect(savedPreferences().state.lastLeague).toEqual({
      code: "SP1",
      season: 2020,
    });
  });

  it("saves no season when the URL had none", () => {
    usePreferences.getState().setLastLeague({ code: "SP1" });
    expect(savedPreferences().state.lastLeague).toEqual({ code: "SP1" });
  });
});

describe("applyTheme", () => {
  afterEach(() => applyTheme(null));

  it("sets data-theme on <html>", () => {
    applyTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("removes data-theme for null, so CSS follows the OS", () => {
    applyTheme("dark");
    applyTheme(null);
    expect(document.documentElement.dataset.theme).toBeUndefined();
  });
});
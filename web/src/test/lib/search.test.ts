import { describe, expect, it } from "vitest";

import { validateLeagueSearch, validateMatchesSearch } from "@/lib/search";

describe("validateLeagueSearch", () => {
  it("keeps a whole-number season", () => {
    expect(validateLeagueSearch({ season: 2024 })).toEqual({ season: 2024 });
  });

  it.each([
    [{ season: "abc" }, {}],
    [{ season: 1.5 }, {}],
    [{}, {}],
  ])("drops an invalid season: %o", (search, expected) => {
    expect(validateLeagueSearch(search)).toEqual(expected);
  });
});

describe("validateMatchesSearch", () => {
  it("keeps a YYYY-MM-DD date", () => {
    expect(validateMatchesSearch({ date: "2025-02-01" })).toEqual({
      date: "2025-02-01",
    });
  });

  it.each([
    [{ date: "1 Feb 2025" }, {}],
    [{ date: 20250201 }, {}],
    [{}, {}],
  ])("drops an invalid date: %o", (search, expected) => {
    expect(validateMatchesSearch(search)).toEqual(expected);
  });
});

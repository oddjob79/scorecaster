import { describe, expect, it } from "vitest";

import type { CompetitionResponse } from "../../api/generated";
import { groupByCountry } from "@/lib/groupByCountry";

const competition = (code: string, country: string): CompetitionResponse => ({
  code,
  name: code,
  country,
  tier: 1,
});

describe("groupByCountry", () => {
  it("groups by country, keeping the order the API sent", () => {
    const input = [
      competition("E0", "England"),
      competition("E1", "England"),
      competition("SC0", "Scotland"),
    ];
    expect(groupByCountry(input)).toEqual([
      ["England", [input[0], input[1]]],
      ["Scotland", [input[2]]],
    ]);
  });

  it("returns no groups for no competitions", () => {
    expect(groupByCountry([])).toEqual([]);
  });
});

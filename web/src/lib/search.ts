export type LeagueSearch = { season?: number };
export type MatchesSearch = { date?: string };

export function validateLeagueSearch(
  search: Record<string, unknown>,
): LeagueSearch {
  return typeof search.season === "number" && Number.isInteger(search.season)
    ? { season: search.season }
    : {};
}

export function validateMatchesSearch(
  search: Record<string, unknown>,
): MatchesSearch {
  return typeof search.date === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(search.date)
    ? { date: search.date }
    : {};
}

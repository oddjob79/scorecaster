import type { CompetitionResponse } from "../api/generated";

export function groupByCountry(
  competitions: CompetitionResponse[],
): [string, CompetitionResponse[]][] {
  const groups = new Map<string, CompetitionResponse[]>();
  for (const competition of competitions) {
    const group = groups.get(competition.country) ?? [];
    group.push(competition);
    groups.set(competition.country, group);
  }
  return [...groups];
}

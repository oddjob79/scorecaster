import { queryOptions } from "@tanstack/react-query";

import { checkHealth, listCompetitions, listSeasons } from "./api";

export const healthQuery = queryOptions({
  queryKey: ["health"],
  queryFn: checkHealth,
});

export const competitionsQuery = queryOptions({
  queryKey: ["competitions"],
  queryFn: listCompetitions,
});

export function seasonsQuery(code: string) {
  return queryOptions({
    queryKey: ["competitions", code, "seasons"],
    queryFn: () => listSeasons(code),
  });
}

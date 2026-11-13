import { getRouteApi } from "@tanstack/react-router";

const route = getRouteApi("/matches");

/** Render the matches for one day. */
export function MatchesPage() {
  const { date } = route.useSearch();

  return (
    <h1 className="font-display text-4xl font-extrabold">
      Matches on {date ?? "today"}
    </h1>
  );
}

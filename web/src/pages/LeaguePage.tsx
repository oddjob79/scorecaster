import { getRouteApi } from "@tanstack/react-router";

const route = getRouteApi("/league/$code");

/** Render one league: its competition and season. */
export function LeaguePage() {
  const { code } = route.useParams();
  const { season } = route.useSearch();

  return (
    <h1 className="font-display text-4xl font-extrabold">
      League {code}, season {season ?? "latest"}
    </h1>
  );
}

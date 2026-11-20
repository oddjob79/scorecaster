import { getRouteApi } from "@tanstack/react-router";

const route = getRouteApi("/team/$teamId");

/** Render one team's page. */
export function TeamPage() {
  const { teamId } = route.useParams();

  return (
    <h1 className="font-display text-4xl font-extrabold">Team {teamId}</h1>
  );
}

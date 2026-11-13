import type { QueryClient } from "@tanstack/react-query";
import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
} from "@tanstack/react-router";

import { competitionsQuery, seasonsQuery } from "./api/queries";
import { queryClient } from "./api/queryClient";
import { AppShell } from "./components/AppShell";
import { LandingPage } from "./pages/LandingPage";
import { LeaguePage } from "./pages/LeaguePage";
import { MatchesPage } from "./pages/MatchesPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { TeamPage } from "./pages/TeamPage";

interface RouterContext {
  queryClient: QueryClient;
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
  component: AppShell,
  notFoundComponent: NotFoundPage,
});

const landingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: LandingPage,
});

type LeagueSearch = { season?: number };

const leagueRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/league/$code",

  validateSearch: (search: Record<string, unknown>): LeagueSearch =>
    typeof search.season === "number" && Number.isInteger(search.season)
      ? { season: search.season }
      : {},
  loader: async ({ context, params }) => {
    await Promise.all([
      context.queryClient.query({ ...competitionsQuery, staleTime: "static" }),
      context.queryClient.query({
        ...seasonsQuery(params.code),
        staleTime: "static",
      }),
    ]);
  },
  component: LeaguePage,
});

const teamRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/team/$teamId",
  component: TeamPage,
});

type MatchesSearch = { date?: string };

const matchesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/matches",
  validateSearch: (search: Record<string, unknown>): MatchesSearch =>
    typeof search.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(search.date)
      ? { date: search.date }
      : {},
  component: MatchesPage,
});

// The tree: the root with its four children.
const routeTree = rootRoute.addChildren([
  landingRoute,
  leagueRoute,
  teamRoute,
  matchesRoute,
]);

export const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: "intent",
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

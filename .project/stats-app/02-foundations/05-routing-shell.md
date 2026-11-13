# 05 Routing and app shell (plan)

## Goal

The four MVP pages exist as routes, inside a shared app shell: the brand, navigation links and the API health line.

The league route is real enough to prove the routing and data together:
- a competition select moves between `/league/E0`, `/league/SP1` and so on;
- a season select writes `?season=2024` into the URL;
- both are fed by the API through TanStack Query.

Back and forward buttons, reloads and pasted links all restore the same view.

The other three routes are placeholders that show their parameters, ready for phases 03–05.

## Depends on

04 (typed API and queries).

## Routes

| Path | Search params | This chunk |
|---|---|---|
| `/` | none | landing placeholder |
| `/league/$code` | `season` | competition and season selects; placeholder body |
| `/team/$teamId` | none yet | placeholder showing the id |
| `/matches` | `date` | placeholder showing the date |

`$code` and `$teamId` are path parameters. TanStack Router types them from the route definition, so `useParams` returns `{ code: string }`. Search params are validated by a function on the route, so `useSearch` returns e.g. `{ season?: number }` and never an unparsed string.

## Decided: code-based routes (1A), shadcn later (2A)

**1. Route definitions: in code, or file-based with a generated route tree.**

| Option | How it works | Trade-off |
|---|---|---|
| **A. Code-based** (recommended) | You write each route with `createRoute(...)` and assemble the tree in one `router.ts`. | Everything is explicit, with no generated files and no extra plugin. Four routes fit comfortably in one file. |
| **B. File-based** | One file per route under `src/routes/`; a Vite plugin (`@tanstack/router-plugin`) generates `routeTree.gen.ts`. | TanStack's recommended default at scale, with automatic code-splitting. It adds a generated file, the kind of machinery you were wary of in chunk 04. |

**2. shadcn/ui now, or when a component needs it.**

| Option | Trade-off |
|---|---|
| **A. Later** (recommended) | The pickers are native `<select>` elements, pill-styled as in `style.md`: accessible and keyboard-friendly with no library. shadcn arrives with the first component a native element can't do well, such as the team-search combobox in phase 04 or the month popover on the Matches page. |
| **B. Now** | `npx shadcn init` adds an `@/` path alias, a `components.json`, a `cn()` helper and several packages, and writes its own colour variables (`--background`, `--primary` …) into `index.css`, which must be mapped onto our tokens. That's a lot of setup for no component used yet. |

## Packages (each needs your go-ahead)

| Package | Kind | Latest now |
|---|---|---|
| `@tanstack/react-router` | runtime | 1.170.46 |
| `@tanstack/react-router-devtools` | dev | 1.167.3 |

## Files that change (options 1A, 2A)

- `web/src/router.ts` (new, you type it): every route, the tree, the router, and its type registration.
- `web/src/components/AppShell.tsx` (new, you type it): brand, nav links, health line, `<Outlet />`.
- `web/src/pages/` (new, you type them): `LandingPage.tsx`, `LeaguePage.tsx`, `TeamPage.tsx`, `MatchesPage.tsx`.
- `web/src/main.tsx` (you edit it): renders `<RouterProvider router={router} />` instead of `<App />`.
- `web/src/App.tsx` (deleted): its title moves to the landing page, its health line to the shell, and its competitions list to the league page's select.

## Order of work

1. You install the router. I read its installed types and confirm the outline's names before you type anything.
2. You type `router.ts` with the root route and the four routes, rendering simple placeholders; `main.tsx` switches to `RouterProvider`.
3. You type `AppShell` with `<Link>` navigation and the health line.
4. You type `LeaguePage`'s competition and season selects.
5. Loaders: the root route's context carries the `QueryClient`, and the league route's loader calls `ensureQueryData` for competitions and that code's seasons. The router gets `defaultPreload: "intent"`. Add the not-found page and the devtools.
6. Verify, then add a "Routing" section to `data/frontend-quickstart.md`.

## Code outline

Shape only: names are confirmed against the installed package in step 1.

```ts
// web/src/router.ts
const rootRoute = createRootRoute({ component: AppShell });

const landingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: LandingPage,
});

const leagueRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/league/$code",
  // Turn the raw query string into typed values:
  // "?season=2024" -> { season: 2024 }; "?season=abc" -> {}
  validateSearch: (search: Record<string, unknown>): LeagueSearch => ({
    season: toNumber(search.season),
  }),
  component: LeaguePage,
});

// teamRoute: "/team/$teamId"; matchesRoute: "/matches", validateSearch -> { date?: string }

const routeTree = rootRoute.addChildren([
  landingRoute, leagueRoute, teamRoute, matchesRoute,
]);
export const router = createRouter({ routeTree });

// Tell TypeScript about this router, so <Link to="/league/$code" params={...}>
// and useParams/useSearch are checked against these routes everywhere.
declare module "@tanstack/react-router" {
  interface Register { router: typeof router }
}
```

```tsx
// web/src/components/AppShell.tsx
/** Render the page frame: app bar with brand, nav and health, then the page. */
export function AppShell() {
  // <header>: "Scorecaster" brand, <Link to="/league/$code" params={{ code: "E0" }}>Leagues</Link>,
  //           Teams, Matches links (activeProps styles the current one), health line
  // <main><Outlet /></main>  -- the matched child route renders here
}
```

```tsx
// web/src/pages/LeaguePage.tsx
/** Render the competition and season selects for one league. */
export function LeaguePage() {
  // const { code } = leagueRoute.useParams();     -> { code: "E0" }
  // const { season } = leagueRoute.useSearch();   -> { season: 2024 } or {}
  // competitions = useQuery(competitionsQuery); seasons = useQuery(seasonsQuery(code))
  // const navigate = useNavigate();
  // competition <select> onChange -> navigate({ to: "/league/$code", params: { code: newCode } })
  // season <select> onChange      -> navigate({ to: ".", search: { season: newYear } })
  // no ?season -> show the newest season (seasons[0])
}
```

## Risks

- **Search params are user input.** Anyone can type `?season=abc` into the URL. `validateSearch` is the boundary that turns it into typed values or drops it, so pages never see unparsed strings.
- **Changing competition keeps a stale season.** `/league/E0?season=2016` → SP1 keeps `season=2016`, which SP1 has. A country whose data starts later would be missing that season. The competition select therefore navigates without a `season`, so the new league opens on its newest season.
- **"Leagues" in the nav needs a default code.** It links to `/league/E0`. The last-used league comes from the Zustand store in chunk 06.

## Proof

- **Navigation:** each nav link changes the URL and the page without a full reload (no white flash), and the current link is highlighted.
- **Competition select:** on `/league/E0`, choosing La Liga moves to `/league/SP1`, and the season select lists SP1's seasons.
- **Season select:** choosing 2020/21 sets `?season=2020`. The browser's Back button returns to the previous season.
- **Bad and good URLs:**
  - typing `/league/E0?season=abc` shows the newest season;
  - `/team/12` shows "Team 12";
  - `/matches?date=2025-02-01` shows the date.
- **Checks:** `npm run check` and `npm run build` pass. `<Link to="/leage/$code">` (misspelt) is a type error.

## Expected test failures

None. No Python changes.

## Scope ledger

**Core**

- router with root and four routes; `validateSearch` on league and matches
- `RouterProvider` in `main.tsx`; `App.tsx` removed
- `AppShell`: brand, nav links, health line, `<Outlet />`
- `LeaguePage`: competition and season selects driving the URL
- placeholders for landing, team and matches

**Optional** (ticked = written)

- [x] TanStack Router Devtools: a dev-only panel showing the matched routes, params and search (dev package; rendered in `AppShell`)
- [x] a "not found" page for unknown URLs (root route `notFoundComponent`)
- [x] prefetch on hover: `defaultPreload: "intent"` on the router, which runs a route's loader when the pointer rests on a link to it (one router option)
- [x] route loaders: each route calls `queryClient.ensureQueryData(...)` for its queries, so fetching starts when navigation starts, not after the page renders. The `QueryClient` reaches loaders through router context (`createRootRouteWithContext`) (router.ts, main.tsx)

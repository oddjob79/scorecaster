import { useQuery } from "@tanstack/react-query";
import { Link, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import { healthQuery } from "../api/queries";
import { type Theme, usePreferences } from "../preferences";

const NAV_LINK = "rounded-full px-3 py-1.5 font-bold text-muted hover:text-fg";
const NAV_ACTIVE = { className: "bg-page text-fg" };

const THEMES: { label: string; value: Theme }[] = [
  { label: "System", value: null },
  { label: "Light", value: "light" },
  { label: "Dark", value: "dark" },
];

export function AppShell() {
  const health = useQuery(healthQuery);
  const apiOk = health.isSuccess && health.data.status === "ok";
  const theme = usePreferences((state) => state.theme);
  const setTheme = usePreferences((state) => state.setTheme);
  const lastLeague = usePreferences((state) => state.lastLeague);

  return (
    <>
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-6 px-4 py-3">
          <Link
            to="/"
            className="font-display text-xl font-extrabold tracking-tight"
          >
            Score<span className="text-accent-ink">caster</span>
          </Link>

          <nav className="flex flex-1 flex-wrap gap-1">
            <Link
              to="/league/$code"
              params={{ code: lastLeague.code }}
              search={{ season: lastLeague.season }}
              className={NAV_LINK}
              activeProps={NAV_ACTIVE}
            >
              Leagues
            </Link>
            <Link
              to="/team/$teamId"
              params={{ teamId: "1" }}
              className={NAV_LINK}
              activeProps={NAV_ACTIVE}
            >
              Teams
            </Link>
            <Link to="/matches" className={NAV_LINK} activeProps={NAV_ACTIVE}>
              Matches
            </Link>
          </nav>

          <span className="flex items-center gap-2 text-sm font-bold text-muted">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                health.isPending ? "bg-draw" : apiOk ? "bg-win" : "bg-loss"
              }`}
            />
            API {health.isPending ? "checking" : apiOk ? "ok" : "unreachable"}
          </span>

          <div
            role="group"
            aria-label="Theme"
            className="flex gap-1 rounded-full bg-page p-1"
          >
            {THEMES.map(({ label, value }) => (
              <button
                key={label}
                type="button"
                aria-pressed={theme === value}
                onClick={() => setTheme(value)}
                className="rounded-full px-3 py-1 text-sm font-bold text-muted aria-pressed:bg-accent aria-pressed:text-on-accent"
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>

      <TanStackRouterDevtools />
    </>
  );
}

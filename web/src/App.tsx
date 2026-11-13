// web/src/App.tsx (replaces the file)
import { useQuery } from "@tanstack/react-query";

import { competitionsQuery, healthQuery } from "./api/queries";
import type { CompetitionResponse } from "./api/generated";

type Health = "checking" | "ok" | "unreachable";

const HEALTH_COLOUR: Record<Health, string> = {
  checking: "text-muted",
  ok: "text-win",
  unreachable: "text-loss",
};

/** Group competitions by country, keeping the API's menu order. */
// e.g. [E0 England, E1 England, SC0 Scotland]
//   -> Map { "England" => [E0, E1], "Scotland" => [SC0] }
// A Map keeps insertion order, so England stays first.
function groupByCountry(
  competitions: CompetitionResponse[],
): Map<string, CompetitionResponse[]> {
  const groups = new Map<string, CompetitionResponse[]>();
  for (const competition of competitions) {
    // Start an empty list the first time a country appears, then append.
    const group = groups.get(competition.country) ?? [];
    group.push(competition);
    groups.set(competition.country, group);
  }
  return groups;
}

export default function App() {
  const health = useQuery(healthQuery);
  const competitions = useQuery(competitionsQuery);

  const healthLabel: Health = health.isPending
    ? "checking"
    : health.isSuccess && health.data.status === "ok"
      ? "ok"
      : "unreachable";

  return (
    <main className="mx-auto grid max-w-5xl gap-6 px-4 py-10">
      <header className="grid gap-1">
        <h1 className="font-display text-7xl font-extrabold tracking-tight">
          Score<span className="text-accent-ink">caster</span>
        </h1>
        <p className="font-display text-xl font-semibold text-muted">
          Football Results and Stats Site
        </p>
      </header>

      <section className="grid gap-1 rounded-panel bg-surface p-6">
        <span className="text-xs font-bold tracking-widest text-muted uppercase">
          API
        </span>
        <p
          className={`font-display text-2xl font-extrabold ${HEALTH_COLOUR[healthLabel]}`}
        >
          {healthLabel}
        </p>
      </section>

      <section className="grid gap-4 rounded-panel bg-surface p-6">
        <h2 className="font-display text-2xl font-extrabold">Competitions</h2>

        {/* One branch per status. Inside the isSuccess branch, data is
            narrowed to ListCompetitionsResponse, so no "?." is needed. */}
        {competitions.isPending && <p className="text-muted">Loading…</p>}
        {competitions.isError && (
          <p className="text-loss">{competitions.error.message}</p>
        )}
        {competitions.isSuccess &&
          [...groupByCountry(competitions.data)].map(([country, list]) => (
            <div key={country} className="grid gap-1">
              <span className="text-xs font-bold tracking-widest text-muted uppercase">
                {country}
              </span>
              <ul className="flex flex-wrap gap-2">
                {list.map((competition) => (
                  <li
                    key={competition.code}
                    className="rounded-tile bg-page px-3 py-1.5 text-sm font-bold"
                  >
                    {competition.name}
                    <span className="ml-2 text-muted">{competition.code}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
      </section>
    </main>
  );
}

import { useQuery } from "@tanstack/react-query";
import { getRouteApi } from "@tanstack/react-router";

import type { CompetitionResponse } from "../api/generated";
import { competitionsQuery, seasonsQuery } from "../api/queries";

const route = getRouteApi("/league/$code");

const SELECT =
  "rounded-full bg-surface px-4 py-2 font-bold text-fg focus-visible:outline-3 focus-visible:outline-accent";

function groupByCountry(competitions: CompetitionResponse[]) {
  const groups = new Map<string, CompetitionResponse[]>();
  for (const competition of competitions) {
    const group = groups.get(competition.country) ?? [];
    group.push(competition);
    groups.set(competition.country, group);
  }
  return [...groups];
}

export function LeaguePage() {
  const { code } = route.useParams();
  const { season } = route.useSearch();
  const navigate = route.useNavigate();

  const competitions = useQuery(competitionsQuery);
  const seasons = useQuery(seasonsQuery(code));

  if (!competitions.isSuccess || !seasons.isSuccess) {
    return <p className="text-muted">Loading…</p>;
  }

  const selectedSeason = season ?? seasons.data[0]?.start_year;
  const competition = competitions.data.find((c) => c.code === code);

  return (
    <section className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-extrabold tracking-widest text-accent-ink uppercase">
            {competition?.country}
          </div>
          <h1 className="font-display text-5xl font-extrabold tracking-tight">
            {competition?.name ?? code}
          </h1>
        </div>

        <div className="flex flex-wrap gap-2">
          <select
            aria-label="Competition"
            className={SELECT}
            value={code}
            onChange={(event) =>
              navigate({
                to: "/league/$code",
                params: { code: event.target.value },
                search: {},
              })
            }
          >
            {groupByCountry(competitions.data).map(([country, list]) => (
              <optgroup key={country} label={country}>
                {list.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>

          <select
            aria-label="Season"
            className={SELECT}
            value={selectedSeason}
            onChange={(event) =>
              navigate({ search: { season: Number(event.target.value) } })
            }
          >
            {seasons.data.map((s) => (
              <option key={s.start_year} value={s.start_year}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <p className="text-muted">
        Table for {competition?.name} {selectedSeason} goes here (phase 03).
      </p>
    </section>
  );
}

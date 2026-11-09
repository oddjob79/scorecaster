import { useEffect, useState } from "react";

type Health = "checking" | "ok" | "unreachable";

const HEALTH_COLOUR: Record<Health, string> = {
  checking: "text-muted",
  ok: "text-win",
  unreachable: "text-loss",
};

/** Show the site title and whether the API answers through the proxy. */
export default function App() {
  const [health, setHealth] = useState<Health>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkHealth() {
      try {
        const response = await fetch("/api/health", {
          signal: controller.signal,
        });
        const body: { status?: string } = await response.json();
        setHealth(response.ok && body.status === "ok" ? "ok" : "unreachable");
      } catch {
        if (!controller.signal.aborted) setHealth("unreachable");
      }
    }

    void checkHealth();

    return () => controller.abort();
  }, []);

  return (
    <main className="mx-auto grid max-w-5xl gap-6 px-4 py-10">
      <header className="grid gap-1">
        {}
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
        {}
        <p
          className={`font-display text-2xl font-extrabold ${HEALTH_COLOUR[health]}`}
        >
          {health}
        </p>
      </section>
    </main>
  );
}

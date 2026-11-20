import { useQuery } from "@tanstack/react-query";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import { healthQuery } from "../api/queries";

export function DebugPage() {
  const health = useQuery(healthQuery);
  const apiOk = health.isSuccess && health.data.status === "ok";

  return (
    <section className="grid gap-4">
      <h1 className="font-display text-4xl font-extrabold">Debug</h1>

      <div className="grid gap-1 rounded-panel bg-surface p-6">
        <span className="text-xs font-bold tracking-widest text-muted uppercase">
          API
        </span>
        <p className="flex items-center gap-2 font-display text-2xl font-extrabold">
          <span
            className={`h-3 w-3 rounded-full ${
              health.isPending ? "bg-draw" : apiOk ? "bg-win" : "bg-loss"
            }`}
          />
          {health.isPending ? "checking" : apiOk ? "ok" : "unreachable"}
        </p>
      </div>

      <TanStackRouterDevtools />
    </section>
  );
}

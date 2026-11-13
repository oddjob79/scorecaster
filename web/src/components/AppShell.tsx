import { Outlet } from "@tanstack/react-router";

/** Render the page frame around the matched route. */
export function AppShell() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <Outlet />
    </main>
  );
}

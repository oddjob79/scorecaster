import { Link } from "@tanstack/react-router";

/** Render the page shown for an unknown URL. */
export function NotFoundPage() {
  return (
    <section className="grid gap-3 rounded-panel bg-surface p-6">
      <h1 className="font-display text-3xl font-extrabold">Page not found</h1>
      <p className="text-muted">There's nothing at this address.</p>
      <Link to="/" className="font-bold text-accent-ink">
        Go to the home page
      </Link>
    </section>
  );
}

# 06 Client state: Zustand store and theme toggle (plan)

## Goal

A small client-side store, persisted to `localStorage`, holding the user's preferences: things that follow you between pages and visits but don't belong in any one page's URL. This chunk gives it two:

- **Theme:** Light / Dark pills in the app bar. Until you pick one, the page follows the operating system.
- **Last-used league and season:** "Leagues" in the nav returns to the league and season you last viewed (e.g. `/league/SP1?season=2020`), not always E0.

## Why a store, and why not the URL

Per the spec's "one owner per value" rule:
- **The URL** owns what the current page shows (league, season).
- **TanStack Query** owns server data.
- **The store** owns preferences that span pages.

The theme isn't part of any page's identity, and "last league" is a memory of past navigation, so neither fits the URL.

## Depends on

05 (the app shell and league route).

## Packages (needs your go-ahead)

| Package | Kind | Latest now |
|---|---|---|
| `zustand` | runtime | 5.1.0 |

Its peer dependencies (`immer`, `use-sync-external-store`) are optional, and neither is needed here.

## Files that change

- `web/src/preferences.ts` (new, you type it): the store, its two actions, and `persist`.
- `web/src/main.tsx` (you edit it): applies the theme to `<html data-theme>` before the first render, and again whenever it changes.
- `web/src/components/AppShell.tsx` (you edit it): the Light/Dark toggle, and the Leagues link from the store.
- `web/src/pages/LeaguePage.tsx` (you edit it): records the current league in the store.

## Order of work

1. You install Zustand; I read its installed types and confirm the outline.
2. You type the store.
3. You wire the theme in `main.tsx` and add the toggle to `AppShell`.
4. You record the last league in `LeaguePage` and point the nav at it.
5. Verify, then add a "Client state" section to the quickstart guide.

## Code outline

Shape only: names are confirmed against the installed package in step 1.

```ts
// web/src/preferences.ts
type Theme = "light" | "dark" | null; // null: follow the operating system

// The league page last viewed: its code, and its season when the URL had one.
// e.g. /league/SP1?season=2020 -> { code: "SP1", season: 2020 }; /league/E0 -> { code: "E0" }
interface LastLeague {
  code: string;
  season?: number;
}

interface PreferencesState {
  theme: Theme;
  lastLeague: LastLeague; // starts as { code: "E0" }
  setTheme: (theme: Theme) => void;
  setLastLeague: (lastLeague: LastLeague) => void;
}

// persist(...) saves the state to localStorage under one key, and restores
// it when the page loads. Functions aren't saved, only data.
export const usePreferences = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: null,
      lastLeague: { code: "E0" },
      setTheme: (theme) => set({ theme }),
      setLastLeague: (lastLeague) => set({ lastLeague }),
    }),
    { name: "scorecaster-preferences" }, // the localStorage key
  ),
);
```

```ts
// web/src/main.tsx: before createRoot(...)
// Set <html data-theme="dark"> (or remove it, for "follow the OS");
// index.css already swaps every token on that attribute.
applyTheme(usePreferences.getState().theme);
usePreferences.subscribe((state) => applyTheme(state.theme));
```

```tsx
// web/src/components/AppShell.tsx
// A selector picks one value: the component re-renders only when that value changes.
const theme = usePreferences((state) => state.theme);
const setTheme = usePreferences((state) => state.setTheme);
const lastLeague = usePreferences((state) => state.lastLeague);
// <Link to="/league/$code" params={{ code: lastLeague.code }}
//       search={{ season: lastLeague.season }}>Leagues</Link>
// System / Light / Dark pills: aria-pressed reflects theme; onClick -> setTheme(null | "light" | "dark")
```

```tsx
// web/src/pages/LeaguePage.tsx
// After rendering a league, remember it and its season:
// "/league/SP1?season=2020" -> lastLeague { code: "SP1", season: 2020 }
useEffect(() => { setLastLeague({ code, season }); }, [code, season, setLastLeague]);
```

```html
<!-- web/index.html, in <head>: runs before the page paints -->
<script>
  // Read the persisted store and set data-theme before anything is drawn;
  // any failure (no entry, private mode, bad JSON) leaves the OS default.
</script>
```

## Risks

- **A flash of the wrong theme on load.** The theme is applied from JavaScript, which runs after the browser has painted the empty page using the OS colours. For someone who picked Light on a dark OS, the background can flash dark for a moment. The optional inline script removes it.
- **The stored code can go stale** if a competition leaves the app. The loader then fails for it, and "Leagues" shows the error display until another league is opened.
- **Persisted state outlives code changes.** Renaming or reshaping a field leaves old data in browsers. Zustand's `persist` has a `version` and `migrate` for that, which isn't needed until a shape changes.

## Proof

- **Theme:**
  - with nothing chosen, the page follows the OS setting;
  - Dark switches the page; reload and it stays dark;
  - DevTools → Application → Local Storage shows `scorecaster-preferences` with `"theme":"dark"`.
- **Last league:**
  - open La Liga, go to the landing page, click "Leagues", and it opens La Liga;
  - "Leagues" is highlighted on every league page.
- **Checks:** `npm run check` and `npm run build` pass.

## Outcome

Done 2026-11-20, worked through step by step; the user typed every change.

- **Store:** `web/src/preferences.ts` holds `theme` (`"light" | "dark" | null`) and `lastLeague` (`{ code, season? }`), saved by Zustand 5.1's `persist` as `{"state":…,"version":0}` under `scorecaster-preferences`. `applyTheme` lives beside the store.
- **Theme:** `index.html` has an inline script that sets `data-theme` before the first paint. `main.tsx` applies the theme at start-up and subscribes to changes, skipping updates where the theme didn't change. `AppShell` has the System/Light/Dark pills, styled through Tailwind's `aria-pressed:` variant.
- **Last league:** `LeaguePage` records `{ code, season }` in an effect placed before its early return, so it catches every way of arriving: selects, Back, links, reload. The nav's "Leagues" link passes both, and now highlights on every league page.
- **Verified by the user:** themes switch and persist with no flash; System follows the OS live; "Leagues" returns to the last league and season, including after a reload.

## Expected test failures

None. No Python changes.

## Scope ledger

**Core**

- `preferences.ts`: store with `theme` and `lastLeagueCode`, persisted
- theme applied to `<html>` from `main.tsx`
- Light/Dark toggle in `AppShell`
- `LeaguePage` records the last league and season; the nav link uses them

**Optional** (ticked = written)

- [x] a third "System" pill, to return to following the OS after choosing Light or Dark (AppShell)
- [x] an inline script in `index.html` that applies the stored theme before the first paint, removing the flash (index.html)
- [x] the last season stored too, so "Leagues" returns to `/league/SP1?season=2020`, not SP1's newest season (store, LeaguePage)

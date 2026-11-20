# 04.01 Charts: ECharts wrapper and themes (plan)

The first chunk of phase 04: the team page has the app's first charts. This plan was drafted in phase 02, and its decisions stand. The outline is refreshed against the code when the chunk starts.

## Goal

A reusable `<EChart option={...} />` React component, and light and dark ECharts themes built from the same design tokens as Tailwind. Every chart is then:
- **a pure function** (data in, ECharts option object out), which is testable without a browser;
- **rendered by this one component,** which handles creating, updating, resizing, switching theme, events, loading and cleaning up.

The team page's league-position chart is the first real use, following the `style.md` chart conventions: violet line, area fill, grid, muted axis text, and the latest point emphasised.

## Depends on

- Phase 02 chunk 06 (the theme preference).
- The phase 04 team season endpoint, for real chart data.

## Packages (needs your go-ahead)

| Package | Kind | Latest when drafted |
|---|---|---|
| `echarts` | runtime | 6.1.0 |

## Decisions (made 2026-11-20)

- **The wrapper is written by us, not taken from `echarts-for-react`.**
  - **Size:** it's about 40–60 lines, and every requirement is known.
  - **Teaching value:** it teaches the general way to wrap any imperative, non-React library: a ref to the DOM element, effects for setup and cleanup, dependency arrays for updates.
  - **Dependencies:** none added. `echarts-for-react` hides its lifecycle choices: option comparison with `fast-deep-equal`, resizing with `size-sensor`, and merge behaviour through props.
- **Colours come from the CSS variables at runtime:** `getComputedStyle(document.documentElement)`. `index.css` stays the single source of every colour, and charts match the page in every theme mode.
- **No demo chart.** The wrapper is built alongside the first real chart.

## Files that change

- `web/src/charts/echarts.ts` (new, Claude writes it): registers only the chart types and components used, through modular imports from `echarts/core`.
- `web/src/charts/theme.ts` (new, the user types it): builds the ECharts theme from the CSS variables.
- `web/src/charts/EChart.tsx` (new, the user types it): the wrapper component.
- `web/src/hooks/useResolvedTheme.ts` (new, the user types it): returns `"light"` or `"dark"`, resolving System through the OS setting.

## Order of work

1. The user installs `echarts`. Claude reads its installed types and confirms the outline, including whether ECharts 6's `setTheme` can change a chart's theme in place.
2. Claude writes `echarts.ts`.
3. The user types `useResolvedTheme` and `theme.ts`.
4. The user types `EChart.tsx`.
5. The first option builder and chart on the team page.
6. Verify, then add a "Charts" section to the quickstart guide.

## Code outline

Shape only: ECharts names are confirmed against the installed package in step 1.

```tsx
// web/src/charts/EChart.tsx
interface EChartProps {
  option: EChartsOption; // what to draw, built by a pure function from API data
  height?: number;       // pixels; width always fills the container
  loading?: boolean;     // shows ECharts' loading spinner while a query is pending
  onEvents?: Record<string, (params: unknown) => void>; // e.g. { click: openMatch }
}

/** Render an ECharts chart, keeping it in step with the option, size and theme. */
export function EChart({ option, height = 320, loading, onEvents }: EChartProps) {
  // useRef: a handle on the <div> ECharts draws into, and on the chart instance
  // Effect, keyed on the resolved theme: init(div, theme); dispose() in cleanup
  // Effect, keyed on the option: chart.setOption(option, { notMerge: true })
  // Effect, keyed on loading: showLoading() / hideLoading()
  // Effect, keyed on onEvents: chart.on(name, handler); chart.off(...) in cleanup
  // Effect: a ResizeObserver on the div calls chart.resize(); disconnect in cleanup
  // return <div ref={divRef} style={{ height }} />
}
```

```ts
// web/src/charts/theme.ts
/** Build an ECharts theme from the page's current CSS colour tokens. */
export function buildChartTheme(): object {
  // const css = getComputedStyle(document.documentElement)
  // color: [--accent, --series-2]; textStyle: { color: --muted, fontFamily: body font }
  // axis lines and splitLine from --line and --grid; tooltip from --surface and --fg
  // aria: { enabled: true }: ECharts generates a text description for screen readers
}
```

```ts
// web/src/hooks/useResolvedTheme.ts
/** Return "light" or "dark": the chosen theme, or the OS setting under System. */
export function useResolvedTheme(): "light" | "dark" {
  // theme from usePreferences; when null, subscribe to
  // matchMedia("(prefers-color-scheme: dark)") with useSyncExternalStore
}
```

## Risks

- **ECharts draws on a canvas,** so Tailwind classes and CSS variables don't reach inside a chart. The theme is read from the CSS variables and passed in as values.
- **Re-theming means recreating the chart** unless ECharts 6 can change theme in place. Recreating causes a brief redraw on toggle. This is checked in step 1.
- **Bundle size:** the full `echarts` import is around 1 MB unminified. Registering only what's used keeps it to a fraction of that. `npm run build` reports the size.

## Proof

- The team page's chart follows the `style.md` conventions.
- Toggling Light / Dark / System re-themes it immediately.
- Resizing the window resizes it.
- Navigating away and back causes no console errors.
- The loading spinner shows while the query is pending.
- Clicking a point fires the handler.
- `npm run check` and `npm run build` pass.

## Expected test failures

None. No Python changes.

## Scope ledger

**Core**

- `echarts` installed; modular registration
- `useResolvedTheme`, `buildChartTheme`, `EChart` (create, update, resize, theme, dispose)

**Optional** (ticked = written)

- [x] a loading state on `EChart` (ECharts' built-in `showLoading`) for charts waiting on a query (EChart)
- [x] an accessible text description per chart (ECharts' `aria` option) (theme)
- [x] click events passed out of the chart, e.g. clicking a point navigates to that match (an `onEvents` prop on EChart)

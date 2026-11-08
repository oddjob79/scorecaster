# Scorecaster style

Approved 2026-11-08. Reference page: `style.html`. Based on style tile C with one accent and a plain header.

Phase 02 builds the Tailwind theme and the ECharts light and dark themes from these tokens.

## Colour

| Token | Light | Dark | Use |
|---|---|---|---|
| `bg` | `#f4f5f8` | `#0f1016` | Page ground, table rows, control tracks |
| `surface` | `#ffffff` | `#181a23` | Panels |
| `fg` | `#12141c` | `#f1f2f6` | Body text and numbers |
| `muted` | `#5e6475` | `#9ba1b3` | Labels, captions, axis text |
| `line` | `#e2e4ea` | `#2a2d3a` | Dividers, swatch borders |
| `grid` | `#e8eaef` | `#252836` | Chart grid lines |
| `accent` | `#5a2fd1` | `#5a2fd1` | Primary buttons, selected pills, chart lines, focus ring |
| `accent-ink` | `#4a22b8` | `#a98cff` | Accent-coloured text: eyebrows, big stat numbers, leader position |
| `on-accent` | `#ffffff` | `#ffffff` | Text on `accent` |
| `series-2` | `#d9731a` | `#ff9a45` | Second team on overlaid charts and comparisons (the first uses `accent`) |
| `win` | `#16a368` | `#2fc183` | W chip |
| `draw` | `#a3a8b6` | `#6f7486` | D chip |
| `loss` | `#e5484d` | `#ff5c62` | L chip |

Derived:

- **accent soft:** `accent` mixed 10% into `surface` (`color-mix(in srgb, accent 10%, surface)`). Used for stat tiles and chart legend keys.
- **accent highlight:** 14% mix. Used for the leading table row.
- **accent hover:** 8% mix, on secondary buttons.

Win, draw and loss are reserved for results and never used as the accent.

## Type

| Role | Family | Fallback |
|---|---|---|
| Display | Bricolage Grotesque (600, 800) | Trebuchet MS, system-ui, sans-serif |
| Body | Manrope (400, 600, 700, 800) | Segoe UI, system-ui, sans-serif |

| Step | Size | Family / weight | Use |
|---|---|---|---|
| Display | 64px (48px on phone), line-height 0.95, tracking −0.03em | Display 800, `accent-ink` | Headline stat |
| Page title | 52px (38px on phone), line-height 1, tracking −0.02em | Display 800 | Page heading |
| Heading 1 | 32px, tracking −0.01em | Display 800 | Team name, panel heading |
| Section | 24px | Display 800 | Section headings |
| Heading 2 | 22px | Display 600 | Sub-headings |
| Stat tile | 40px (30px on phone), line-height 1 | Display 800, `accent-ink` | Stat tile numbers |
| Body | 15px, line-height 1.55 | Body 400 | Running text, table cells |
| Small | 13px | Body 400, `muted` | Notes, captions |
| Label | 12px, uppercase, tracking 0.08em | Body 700, `muted` | Column heads, field labels |
| Eyebrow | 12px, uppercase, tracking 0.1em | Body 800, `accent-ink` | Context line above a heading |

Numbers in tables and stats use tabular figures (`font-variant-numeric: tabular-nums`).

## Spacing and shape

- Spacing scale: 4, 8, 12, 16, 24, 32, 56px.
- Radius: 12px for table rows, tiles and swatches; 20px for panels; full (999px) for pills, buttons, selects and form chips.
- Panels: `surface` background, 24px padding, no border or shadow.

## Components

- **Form chips:** 24px circles, letter in white 11px Body 800, `win`/`draw`/`loss` fill, oldest to newest left to right. Each chip shows its result on hover and to screen readers, e.g. "Won 2–1 v Arsenal (H) · Sat 25 Jan", and can be reached with Tab.
- **Pill group** (segmented control): `bg` track with 4px padding; the selected pill is `accent` with `on-accent` text, the others `muted`.
- **Buttons** (pill-shaped, Body 800 14px):
  - primary: `accent` fill;
  - secondary: 2px `accent` outline with `accent-ink` text;
  - ghost: `muted` text.

  Each view has at most one primary.
- **Select:** pill-shaped, `bg` fill, no border.
- **Table:** rows are separate rounded `bg` strips with 4px between them. The position and points columns use Display 800 at 18px. The leading row takes the accent highlight.
- **Stat tile:** accent soft fill, 12px radius, 16px padding, number above a label.
- **Focus:** 3px `accent` outline, 2px offset.

## Charts

- **Lines:** `accent`, 3.5px, round joins. Area fill under single-series lines at 14% `accent`.
- **Points:** 4.5px radius, `surface` fill, `accent` stroke. The latest point is filled and 7px, with its value labelled in Body 800.
- **Axes and grid:** grid lines in `grid`, axis text 12px Body in `muted`.
- **Two-team overlays:** the home team in `accent`, the away team in `series-2`. Where one team has two series (e.g. scored and conceded), the second is dashed, and the key shows the dash.
- **Division bands:** Premier League seasons (or any top division) shaded with `accent` at 9%; lower divisions unshaded.

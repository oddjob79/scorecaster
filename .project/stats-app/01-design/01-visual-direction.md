# 01 Visual direction

## Goal

A brief template and an approved style tile that set the look every page mockup follows.

## Depends on

Nothing.

## Steps

1. Write `design/brief-template.md` with these sections:
   - who the page is for;
   - the 2–3 questions it answers;
   - its components in priority order;
   - the data each component shows;
   - interactions and what they change (URL params, store);
   - out of scope.
2. You list any sites whose look you like, or describe the feel you want (optional input).
3. Produce two or three distinct style tiles, `design/style-a.html`, `style-b.html` and `style-c.html`. Each is a single page showing:
   - the colour palette;
   - the type scale;
   - spacing;
   - a table row with form chips;
   - a line chart;
   - a card;
   - buttons and a select.

   Each tile shows these in light and dark.
4. You pick one, or name parts to combine. The chosen tile becomes `design/style.html`. Revise it until approved.
5. Record the approved colour, type and spacing tokens in `design/style.md`. Phase 02 turns these into the Tailwind theme and the ECharts theme.

## Proof

- You approve `style.html`.
- `style.md` lists every token the style tile uses.

## Scope ledger

**Core**

- steps 1, 3, 4, 5

**Optional** (ticked = written)

- [x] two or three alternative directions in step 3

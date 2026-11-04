# Nightwatch design spec

Dark, calm, evidence-first. A bright sea-green landing hero with a sea-chart grid, a dark app with a row of tabs,
and alert cards where every flag has a plain-English reason.

Reference screens (read the markup for layout, spacing and copy): `design-reference/`
- `Main.dc.html` / `Main-fr.dc.html`: landing page
- `Watch.dc.html` / `Watch-fr.dc.html`: dashboard (counters, map, filters, ranked alerts)
- `Alert.dc.html` / `Alert-fr.dc.html`: alert detail (reasons, track, activity, decision)
- `Validation.dc.html` / `Validation-fr.dc.html`: does it work (blacklist check, limits)

These files use a design-tool format (`<x-dc>`, `<sc-if>`, `{{ }}` holes, inline styles). Do not copy that format.
Rebuild them as Jinja templates and `static/style.css`, using CSS variables and classes.

## Colors (CSS variables in `static/style.css`)
```
--bg: #0A0F12;          /* page background */
--surface: #111A1E;     /* cards */
--surface-2: #18232A;   /* inputs, inner panels, progress track */
--map-bg: #0D161A;      /* map panel */
--line: #22313A;        /* borders, row dividers */
--line-2: #33454F;      /* secondary buttons, dashed cards */
--text: #EAF2F2;
--text-2: #C5D2D6;      /* table cell text */
--muted: #93A4AB;       /* labels, secondary text */
--dim: #6B7F88;         /* low-risk dots, map labels */
--accent: #5FE0C8;      /* sea green: buttons, active tab, hero background */
--ink: #0A0F12;         /* text on accent */
--high: #FF7A70;  --high-bg: #3F1F1C;
--med:  #F2BE5C;  --med-bg:  #3D3217;
--ok-bg: #123A33;       /* confirmed state, "yes" chips */
```
Hero and final call-to-action bands: `--accent` background, `--ink` text, sea-chart grid:
```
background-image:
  linear-gradient(rgba(10,15,18,.13) 1px, transparent 1px),
  linear-gradient(90deg, rgba(10,15,18,.13) 1px, transparent 1px);
background-size: 56px 56px;
```

## Fonts (Google Fonts)
- Headlines: Bricolage Grotesque 700 to 800, letter-spacing -0.03em to -0.04em, line-height about 0.92 to 1
- Body: DM Sans 400/500/600
- Labels, tabs, buttons, section tags: JetBrains Mono, uppercase, letter-spacing .06em, 11 to 13px
- Section tags look like `[ 01 / EXAMPLE ALERT ]`

## Shape
- Page container: max-width 1280px, side padding 28px
- Cards: radius 20 to 28px, 1px `--line` border, `--surface` background
- Inputs: radius 12px, `--surface-2` background, 1px `--line` border
- Primary button: `--accent` background, `--ink` text, mono uppercase, radius 12px (hero and CTA may use pill 999px)
- Secondary button: transparent, 1px `--line-2` border, pill
- Risk chips: pill, 13px, weight 600. High = `--high` on `--high-bg`, Medium = `--med` on `--med-bg`
- Flag rows (reasons): a 28px numbered square (high or med colour, ink text) + mono uppercase label in the same colour + one plain sentence. Optional `+34 PTS` right-aligned in muted mono. Divider lines between rows.
- Command bar: dark rounded bar with a sea-green `>_`, a text input, and a mono SCAN button
- Suggested action card: solid `--high` background with ink text when the action is "Send patrol"

## Logo
A rounded tile with a radar mark. On the dark app header the tile is `--accent` and the mark is `--ink`; on the bright hero it is reversed.
```html
<svg viewBox="0 0 40 40" width="21" height="21" aria-hidden="true">
  <circle cx="20" cy="20" r="15" fill="none" stroke="currentColor" stroke-width="3"/>
  <circle cx="20" cy="20" r="7" fill="none" stroke="currentColor" stroke-width="2" stroke-opacity=".6"/>
  <path d="M20 20 L31 9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  <circle cx="27" cy="25" r="3" fill="currentColor"/>
</svg>
```

## App header (every app page)
Logo + "Nightwatch" on the left. Tabs in the middle (WATCH, ALERTS, VALIDATION, METHOD) as mono uppercase links;
the active one is a filled `--accent` pill with `--ink` text, the others `--muted`.
Right side: EN | FR switch (active half filled `--text` with ink text), "COAST GUARD OPS" in muted mono,
and an amber outlined "PROTOTYPE" pill. Wraps on small screens.

## Map (Watch page)
- Leaflet, pinned version from cdnjs. Dark basemap (CARTO Dark Matter) with its attribution shown.
- Centre on Mauritius, zoom so the whole EEZ shows.
- Dots: High = `--high` radius 9, Medium = `--med` radius 7, Low = `--dim` radius 5.
- Dark (no AIS) contacts get a dashed `--text` ring around the dot.
- Clicking a dot opens a popup with name, risk and an "Open" link to the alert page.
- Under the map: "Vessel data: Global Fishing Watch."

## Rules
- Mobile friendly: single column on small screens, tables scroll inside their card, no horizontal page scroll
- Text contrast at least 4.5:1, visible focus outline (2px `--accent`) on all links, buttons and inputs
- Real `<button>`, `<a href>`, `<label>` elements, never clickable divs
- Risk is never shown by colour alone: always the number and the level word too
- Reuse the CSS variables; no hardcoded hex values in templates

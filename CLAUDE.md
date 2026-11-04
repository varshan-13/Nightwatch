# Nightwatch

Nightwatch is a hackathon prototype (Tech Wave AI Hackathon, Mauritius, Track 2: illegal fishing).
It ranks vessels in the Mauritius Exclusive Economic Zone (EEZ) by how unusual their behaviour is,
explains each alert in plain words, and lets a coast guard officer confirm or dismiss it.

Core rule: **the model ranks, an officer decides.** Nightwatch never says a vessel is guilty.

## Stack
- Python 3, Flask, Jinja templates, plain CSS (no CSS framework)
- pandas for reading CSV files
- Leaflet for the map (loaded from a CDN, pinned version)
- Data pipeline (Phase 5): Global Fishing Watch API + scikit-learn IsolationForest

## Folder layout
```
app.py                 Flask routes
translations.py        every piece of UI text, in "en" and "fr"
templates/             base.html, landing.html, watch.html, alert.html, validation.html
static/style.css       all styling, built from DESIGN.md
data/                  alerts.csv, events.csv, feedback.csv
pipeline/              GFW fetch, vessel profiles, scoring (Phase 5)
make_sample_data.py    writes placeholder data/alerts.csv and data/events.csv
design-reference/      the approved design screens (read the markup for layout and styling)
```

## Data contract (the website only reads these files)
`data/alerts.csv`, one row per vessel or radar contact:
`vessel_id, name, mmsi, flag, gear, dark, lat, lon, risk, reason_1, reason_1_pts, reason_2, reason_2_pts, reason_3, reason_3_pts, last_seen`
- `dark` is True for a radar contact with no AIS match (name "Unidentified", no MMSI)
- `risk` is 0 to 100

`data/events.csv`, one row per event:
`vessel_id, event, time, lat, lon`
- `event` is one of: AIS gap, Encounter, Loitering, Fishing, Port visit

`data/feedback.csv`, written by the site:
`vessel_id, label, note, time` where label is `confirmed` or `false_alarm`

Computed in the app, never stored:
- level: High if risk >= 70, Medium if 40 to 69, Low below 40
- action: High = Send patrol, Medium = Keep watching, Low = No action

The pipeline (Phase 5) must write exactly these columns, so the site needs no changes when real data arrives.

## Languages
- English and French. Routes: `/`, `/watch`, `/alert/<vessel_id>`, `/validation`, and the same under `/fr/`.
- No UI text hardcoded in templates. Every string comes from `translations.py`.
- The EN | FR switch links to the same page in the other language.
- Data values (reasons, event names) are stored in English; translate them for display with a lookup in `translations.py`.

## Track rules to respect
- The final demo must run on **real** Global Fishing Watch data. The sample data is only for building.
- Every page shows the "Prototype, not an official enforcement tool" notice.
- Credit "Vessel data: Global Fishing Watch" wherever vessel data appears. GFW data is non-commercial use only.
- A vessel's flag is shown for context only and must never be used to raise its score.

## How to run
```
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 make_sample_data.py
flask --app app run --debug
```

## Rules for working on this project
- Keep code minimal and straightforward. No extra validation, abstractions or boilerplate unless asked.
- Make one small change at a time and tell me how to see it working.
- Before any big change, show a short plan first and wait for my go-ahead.
- Don't add new libraries without asking.
- Never put API keys in code or commit them. The GFW token lives in the `GFW_API_ACCESS_TOKEN` environment variable.
- Don't rename CSV columns without telling me first.
- Explain anything non-obvious in plain English. I need to understand and defend this code to judges.

## Design
Follow `DESIGN.md` for all visual work. The screens in `design-reference/` are the source of truth for layout.

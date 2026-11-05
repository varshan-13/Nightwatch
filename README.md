# Nightwatch

> **Prototype, not an official enforcement tool.** Built for the Tech Wave AI Hackathon
> (Mauritius, Track 2: illegal fishing). Nightwatch never says a vessel is guilty.

Nightwatch ranks fishing vessels in the **Mauritius Exclusive Economic Zone (EEZ)** by how
unusual their behaviour is, explains every alert in plain words, and lets a coast guard
officer confirm or dismiss it.

**The model ranks, an officer decides.**

English and French throughout (`/` and `/fr/`).

---

## Contents

1. [What it does](#what-it-does)
2. [Setup](#setup)
   - [Hosting on Vercel](#3-host-it-on-vercel)
3. [Data](#data)
4. [Models](#models)
5. [APIs and external services](#apis-and-external-services)
6. [Libraries](#libraries)
7. [Running offline](#running-offline)
8. [Tests](#tests)
9. [Known limits](#known-limits)
10. [Project layout](#project-layout)

---

## What it does

| Page | What you see |
|---|---|
| **Home** `/` | What Nightwatch is, an example alert, how it decides, validation results, limits. Clicking *Home* or the logo plays a short full-screen loading intro. |
| **Live map** `/watch` | A full-screen map of the Mauritius EEZ with a floating panel of three tabs: **Alerts** (search and ranked list), **Filters** (risk range, dark vessels only) and **Summary** (counters). On phones the panel is a sheet along the bottom. |
| **Alert** `/alert/<id>` | Risk score 0–100, the three reasons with points, recorded positions, activity, suggested action, and the officer's decision (confirm, false alarm, undo). |
| **Alerts** `/alerts` | The review list: pending, reviewed, all. |
| **Validation** `/validation` | How the ranking compares with the IOTC illegal-fishing list, the false-alarm rate, and known limits. |

Risk levels are computed, never stored:

| Risk | Level | Suggested action |
|---|---|---|
| 70+ | High | Send patrol |
| 40–69 | Medium | Keep watching |
| Under 40 | Low | No action |

Risk is always shown as a number and a word, never by colour alone. A vessel's **flag** is
shown for context only and is **never used to calculate the score**.

---

## Setup

### 1. Run the website

You need **Python 3.11 or newer**. Python 3.14 has been tested.

```sh
git clone https://github.com/varshan-13/Nightwatch.git && cd Nightwatch
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug --port 5001
```

Open **http://127.0.0.1:5001**. On macOS, port 5000 is usually taken by AirPlay Receiver,
so use 5001.

The repository already contains processed real data (`data/alerts.csv`, `data/events.csv`,
`data/iotc_iuu.csv`), so **the website runs without an API token and without internet**.
If `data/alerts.csv` is missing, every page still opens and shows a notice explaining how to
create the data.

To build the site on placeholder data instead, run this. It overwrites `alerts.csv` and
`events.csv`:

```sh
python3 make_sample_data.py
```

### 2. Rebuild the data from Global Fishing Watch (optional)

This needs a free **Global Fishing Watch API token**. Request one at
https://globalfishingwatch.org/our-apis/, then put it in your shell profile (for example
`~/.zshrc`). Never put it in code or commit it:

```sh
export GFW_API_ACCESS_TOKEN="your-token"
```

The pipeline needs two extra libraries (the GFW client and scikit-learn) that the
website doesn't:

```sh
pip install -r pipeline/requirements.txt
```

Then run the pipeline from the project folder:

```sh
python3 pipeline/fetch_gfw.py        # 1. download 12 months of data into data/raw/ (needs internet + token)
python3 pipeline/build_profiles.py   # 2. one behaviour profile per vessel
python3 pipeline/score.py            # 3. risk scores and reasons -> data/alerts.csv, data/events.csv
python3 pipeline/validate.py         # 4. compare with the IOTC IUU list -> data/validation.json
```

Steps 2–4 work offline from the files that step 1 saved. `data/raw/` is not committed,
because of its size and GFW's non-commercial terms.

### 3. Host it on Vercel

Vercel detects the Flask app in `app.py` and installs only `requirements.txt` (Flask and
pandas). The pipeline libraries stay out, so the app stays small.

1. Import the GitHub repository in Vercel. No build settings are needed.
2. In **Project → Settings → Environment Variables**, add **`SECRET_KEY`**. Use a long random
   value, for example the output of `python3 -c "import secrets; print(secrets.token_hex(32))"`.
   Without it, each server instance makes up its own key and officer decisions get rejected.
3. Redeploy.

How the hosted version differs:

- **Read-only disk.** Vercel's project folder is read-only, so at start-up the app copies
  `data/` to `/tmp` (the only writable place) and works from there.
- **Decisions don't last.** `/tmp` belongs to one server instance and is wiped when Vercel
  recycles it. Confirm and False alarm work, but hosted decisions are for **demos only**.
  For real use, keep decisions in a database.
- **Validation** is worked out from the committed data on first use. No pipeline run is
  needed.

`.vercelignore` keeps the design mockups and tests out of the upload.

---

## Data

### Sources

| Source | What we use | Terms |
|---|---|---|
| **Global Fishing Watch** (https://globalfishingwatch.org) | AIS gap, encounter, loitering, fishing and port-visit events; vessel identities; worldwide port visits | Non-commercial use only. *Vessel data: Global Fishing Watch* is credited on every page that shows vessel data. |
| **IOTC IUU Vessels List** (Indian Ocean Tuna Commission, https://iotc.org/node/37) | The list dated **15 May 2026**: 201 vessels, 41 with IMO numbers | Public list. Each row in `data/iotc_iuu.csv` keeps its source page, link and date. See `pipeline/VALIDATION.md`. |
| **Sample data** (`make_sample_data.py`) | 60 made-up vessels, for building and tests only | Generated, not real. |

### Area and period

- **Area:** the *Mauritian Exclusive Economic Zone*, GFW region ID **8343**, which covers
  Mauritius, Rodrigues, St Brandon and Agaléga. The ID is looked up through the API by name,
  not hard-coded. The Chagos Archipelago is a separate GFW region and is not included.
- **Period:** the 12 months up to the newest event (currently 30 Oct 2025 – 30 Oct 2026).
  GFW data arrives a few days late.
- **Vessels scored:** fishing vessels and carriers only. Cargo ships, ferries and drifting
  fishing-gear buoys are left out. The current run scores **407 vessels: 15 High, 43 Medium,
  349 Low**.

### Files (the data contract)

The website only reads these files. The pipeline writes exactly these columns, so the site
works with sample or real data unchanged.

| File | Written by | Columns |
|---|---|---|
| `data/alerts.csv` | `score.py` | `vessel_id, name, mmsi, flag, gear, dark, lat, lon, risk, reason_1, reason_1_pts, reason_2, reason_2_pts, reason_3, reason_3_pts, last_seen` |
| `data/events.csv` | `score.py` | `vessel_id, event, time, lat, lon`. `event` is one of: AIS gap, Encounter, Loitering, Fishing, Port visit |
| `data/feedback.csv` | the website | `vessel_id, label, note, time`. `label` is `confirmed` or `false_alarm`. One current decision per vessel. Not committed. |
| `data/validation.json` | `validate.py` | Top-20 and random-baseline matches, false-alarm rate, input hashes. Not committed. |
| `data/iotc_iuu.csv` | prepared by hand from the IOTC PDF | `iotc_id, name, aliases, imo, mmsi, source_url, list_date` and audit columns |
| `data/raw/` | `fetch_gfw.py`, `build_profiles.py` | Raw GFW JSON, `profiles.csv` (features + IMO), `vessel_events.csv`. Not committed. |

---

## Models

### 1. Nightwatch's own model: IsolationForest (anomaly detection)

This is the **only machine-learning model Nightwatch trains**. It lives in `pipeline/score.py`.

| | |
|---|---|
| **Library** | scikit-learn `sklearn.ensemble.IsolationForest` |
| **Settings** | `n_estimators=300`, `random_state=42`, everything else at the defaults |
| **Type** | Unsupervised anomaly detection. It needs no labels, which matters because nobody labels ships "illegal" at sea. |
| **Input** | Seven behaviour features per vessel, each transformed with `log(1 + value)` so one extreme vessel doesn't squash all the others. A feature that is the same for every vessel is dropped. |
| **Output** | The anomaly score (`-score_samples`), stretched to 0–100 and kept between 1 and 99 |

**The seven features** (from `pipeline/build_profiles.py`, over the 12-month window):

| Feature | Meaning |
|---|---|
| `ais_off_hours` | Total hours the AIS was switched off |
| `edge_gaps` | AIS gaps that started 250–450 km offshore, roughly the EEZ edge (about 370 km out) |
| `carrier_encounters` | Meetings at sea with a refrigerated carrier |
| `loitering_hours` | Hours drifting slowly at sea, counted only if 20+ km from any port |
| `days_since_port` | Days since the last port visit **anywhere in the world**, capped at 365 |
| `identity_changes` | Extra names, MMSI numbers or flags broadcast this year |
| `mpa_fishing_hours` | Hours of apparent fishing inside a marine protected area |

The flag is kept for display and is deliberately **not** a feature.

**How the reasons are made (no AI):** for each vessel, we measure how far each feature is
above the typical vessel, in standard deviations from the median. The three furthest above
normal become plain-English sentences from fixed templates, such as "AIS switched off 11
times near the EEZ edge". The risk points are split between them in proportion. If nothing
stands out, the alert says so instead of inventing reasons. French translations of the
sentences come from pattern matching in `translations.py`.

### 2. Models we rely on but don't run: Global Fishing Watch's

The GFW data is itself produced by GFW's machine-learning models. Nightwatch uses their
outputs as inputs:

- **Apparent fishing events:** GFW's models classify fishing activity from AIS tracks.
- **Vessel type and gear type:** GFW's classifier (shown as `SECONDARY_CLASSIFIER_MODEL` in
  the identity records) labels vessels as fishing, carrier, drifting longlines, and so on.
- **AIS gaps, encounters, loitering, port visits:** GFW's event-detection algorithms.
- **Satellite radar (SAR) vessel detections:** GFW's neural-network detector. This is wired
  into the pipeline but **not available yet** (see [Known limits](#known-limits)).

See GFW's methods: https://globalfishingwatch.org/our-apis/documentation

### What is not AI

- **No language model, chatbot or generative AI.** No text on the site is generated by a model.
- **Rules, not models:** the risk levels, suggested actions, reasons and French translations
  are fixed rules.
- **Plain matching and counting:** validation (`pipeline/validate.py`) matches by exact IMO,
  then MMSI, then name, and draws a random baseline with seed 42. No model is involved.
- **People decide:** every alert is confirmed or dismissed by an officer.

---

## APIs and external services

### Global Fishing Watch API v3

All requests go through the official Python client `gfw-api-python-client` 1.4.0, using the
token in `GFW_API_ACCESS_TOKEN`. Base URL: `https://gateway.api.globalfishingwatch.org/v3/`.

| Endpoint | Client call (in `pipeline/fetch_gfw.py`) | Used for |
|---|---|---|
| `GET datasets/public-eez-areas/context-layers` | `references.get_eez_regions()` | Look up the Mauritius EEZ region ID by name |
| `POST events` | `events.get_all_events(...)` | 12 months of events in the EEZ, one request per dataset: `public-global-gaps-events`, `public-global-encounters-events`, `public-global-loitering-events`, `public-global-fishing-events`, `public-global-port-visits-events` (all `:latest`) |
| `POST events` (by vessel) | `events.get_all_events(vessels=...)` | Each candidate vessel's port visits worldwide, 50 vessels per request |
| `GET vessels` | `vessels.get_vessels_by_ids(...)` | Identity history (names, MMSI, IMO, flag, gear), 50 vessels per request, dataset `public-global-vessel-identity:latest` |
| `POST 4wings/report` | `fourwings.create_sar_presence_report(...)` | Satellite radar detections, matched and unmatched to AIS. Currently returns "temporarily unavailable". |

API docs: https://globalfishingwatch.org/our-apis/documentation · Client docs:
https://globalfishingwatch.github.io/gfw-api-python-client/

### Services the website loads in the browser

| Service | Used for | Offline behaviour |
|---|---|---|
| **Esri World Dark Gray Canvas** tiles (`services.arcgisonline.com`) | Map background on the Live map and alert pages. Credited on the map: *Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors*. | The dots still show on a plain dark background, with a note. |
| **Google Fonts** (`fonts.googleapis.com`) | Bricolage Grotesque, DM Sans, JetBrains Mono | System fonts are used instead. |

DESIGN.md asked for CARTO Dark Matter tiles, but CARTO now requires an API key, so the site
uses Esri's keyless tiles instead.

No other external calls are made. The site has no analytics and no tracking. Officer
decisions stay in `data/feedback.csv` on the machine running the site.

---

## Libraries

| Library | Version | Used for |
|---|---|---|
| Flask | 3.1 | Web app, routes, Jinja templates, decision form (with a per-session token against forged submissions) |
| pandas | 2.3 | Reading and writing the CSV files, building profiles |
| scikit-learn | 1.9 | `IsolationForest`, the anomaly model (pipeline only, in `pipeline/requirements.txt`) |
| NumPy | (installed with pandas) | Feature maths in the pipeline and sample data |
| gfw-api-python-client | 1.4.0 | Official Global Fishing Watch API client (pipeline only) |
| Leaflet | 1.9.4 | Interactive maps. Served from `static/vendor/leaflet/` (BSD-2-Clause), so it works offline. |

Plain CSS, no CSS framework. The small scripts in `static/` (intro, animations, tabs, guided
tour, remembering your map position) are written for this project and use no libraries.

---

## Running offline

With Wi-Fi off, the pages, filters, maps, decisions and validation all work from the files in
this repository. Only these need internet:

| Needs internet | Without it |
|---|---|
| Map background tiles | Plain dark background with a note; vessel positions still shown |
| Web fonts | System fonts |
| Downloading fresh GFW data (`fetch_gfw.py`) | Use the data already in `data/` |

---

## Tests

```sh
python3 -m unittest discover -s tests -v
```

There are 20 tests covering:

- alert pages in both languages
- officer decisions, undo, and the review list
- the dashboard filters
- validation matching and sampling

They use a fixed copy of the sample data in `tests/fixtures/`, so they don't depend on the
live data.

---

## Known limits

- **Prototype.** Not an official enforcement tool. A high score is a reason to look closer,
  not proof of illegal fishing.
- **No radar data yet.** GFW's SAR reports were *temporarily unavailable* in November 2026,
  so there are no "dark vessel" contacts (radar dots with no AIS). `fetch_gfw.py` saves them
  automatically when the service returns. The radar scoring path is untested on real data.
- **Innocent gaps.** Vessels switch off AIS to avoid pirates, and signals drop out far from
  land.
- **Simple proxies.** "Near the EEZ edge" uses distance from shore, not the real boundary line.
- **Encounters.** GFW records no carrier encounters inside this EEZ in the current window, so
  that feature adds nothing right now.
- **Validation is weak evidence.** In the current run, **0 of the top 20** alerts are on the
  IOTC list, and so are **0 of 20 random** vessels. No alerts have been reviewed yet. Many
  listed vessels are old, renamed, or don't broadcast AIS. This shows neither that the model
  works nor that it fails. See the Validation page and `pipeline/VALIDATION.md`.
- **Data lag.** GFW data is a few days behind, and "last seen" times reflect that.

---

## Project layout

```
app.py               Flask routes and data loading
translations.py      every piece of UI text, in English and French, plus reason patterns
templates/           page templates (Jinja)
static/              style.css, page scripts, vendor/leaflet/
data/                alerts.csv, events.csv, iotc_iuu.csv (+ feedback.csv, validation.json, raw/: not committed)
pipeline/            fetch_gfw.py, build_profiles.py, score.py, validate.py, VALIDATION.md
tests/               unit tests and fixtures
make_sample_data.py  placeholder data for building
design-reference/    the approved design screens
DESIGN.md            design spec · CLAUDE.md project rules · PROMPTS.md build phases
```

## Team

Built by Varshan and Neha Lenchu for the Tech Wave AI Hackathon, Mauritius.

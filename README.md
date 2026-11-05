# Nightwatch

> **Prototype, not an official enforcement tool.** Built for the Tech Wave AI Hackathon
> (Mauritius, Track 2: illegal fishing). Nightwatch never says a vessel is guilty.

Nightwatch ranks fishing vessels in the **Mauritius Exclusive Economic Zone (EEZ)** by how
unusual their behaviour is, explains every alert in plain words, and lets a coast guard
officer confirm or dismiss it.

**The model ranks, an officer decides.**

English and French throughout (`/` and `/fr/`).

## What it does

| Page | What you see |
|---|---|
| **Landing** `/` | What Nightwatch is, an example alert, how it decides, validation results, limits |
| **Watch** `/watch` | Counters, a live map of the Mauritius EEZ, risk and dark-vessel filters, ranked alerts |
| **Alert** `/alert/<id>` | Risk score 0–100, the three reasons with points, recorded positions, activity, suggested action, officer decision (confirm / false alarm / undo) |
| **Alerts** `/alerts` | Review list: pending, reviewed, all |
| **Validation** `/validation` | How the ranking compares with the IOTC illegal-fishing list, the false-alarm rate, known limits |

Risk levels are computed, never stored: **High** 70+ (send patrol), **Medium** 40–69 (keep
watching), **Low** under 40 (no action). Risk is always shown as a number and a word, never
by colour alone.

## Setup

Needs Python 3.11 or newer.

```sh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug --port 5001
```

Open http://127.0.0.1:5001. (On macOS, port 5000 is often taken by AirPlay Receiver.)

The repository already contains processed real data in `data/alerts.csv` and `data/events.csv`,
so **the website runs without an API token and without internet**. To work on the site with
placeholder data instead, run `python3 make_sample_data.py`. It overwrites those two files.

### Rebuilding the data from Global Fishing Watch

You need a free Global Fishing Watch API token in the `GFW_API_ACCESS_TOKEN` environment
variable. Never put it in code or commit it.

```sh
python3 pipeline/fetch_gfw.py        # 1. download 12 months of events into data/raw/
python3 pipeline/build_profiles.py   # 2. one behaviour profile per vessel
python3 pipeline/score.py            # 3. risk scores and reasons -> data/alerts.csv, data/events.csv
python3 pipeline/validate.py         # 4. compare with the IOTC IUU list -> data/validation.json
```

`data/raw/` is not committed (size, and GFW's non-commercial terms). See `pipeline/VALIDATION.md`
for how validation works.

### Tests

```sh
python3 -m unittest discover -s tests -v
```

The tests use a fixed copy of the sample data in `tests/fixtures/`, so they don't depend on
the live data.

## How the score works

1. **Fetch.** We look up the Mauritius EEZ through the GFW API (region 8343: Mauritius,
   Rodrigues, St Brandon, Agaléga) and download 12 months of AIS gaps, encounters,
   loitering, fishing and port visits. For each fishing vessel or carrier, we also download
   its identity history and its port visits anywhere in the world.
2. **Profile.** For each vessel, we measure seven behaviours:
   - hours with AIS switched off
   - gaps that start near the EEZ edge
   - meetings with refrigerated carriers
   - hours loitering far from port
   - days since the last port visit
   - name, MMSI or flag changes
   - hours fishing inside a marine protected area

   Cargo ships, ferries and drifting fishing-gear buoys are left out.
3. **Score.** A scikit-learn **IsolationForest** learns what normal behaviour looks like
   here. It scores how easy each vessel is to isolate from the rest, and that score is
   stretched to 0–100.
4. **Explain.** The three behaviours furthest above normal become the reasons, and the risk
   points are split between them in proportion. If nothing stands out, the alert says so
   instead of inventing reasons.

**A vessel's flag is shown for context only and is never a feature.** It cannot raise a score.

## Data sources

- **Global Fishing Watch** (https://globalfishingwatch.org): vessel events, identities and
  port visits through the GFW API v3. *Vessel data: Global Fishing Watch.* Non-commercial
  use only, under GFW's terms. The site shows this credit wherever vessel data appears.
- **IOTC IUU Vessels List** (Indian Ocean Tuna Commission, https://iotc.org/node/37), the
  list dated 15 May 2026, 201 records. Copied to `data/iotc_iuu.csv` with its source page
  and date kept on every row. See `pipeline/VALIDATION.md`.
- **Base map:** Esri World Dark Gray Canvas (Esri, HERE, Garmin, © OpenStreetMap contributors).

## Models and libraries

| What | Used for |
|---|---|
| Flask | Web app, routes, Jinja templates |
| pandas | Reading and writing the CSV files |
| gfw-api-python-client 1.4.0 | Official Global Fishing Watch API client |
| scikit-learn: `IsolationForest` | Anomaly score, the only model in the project |
| Leaflet 1.9.4 | Maps. A local copy in `static/vendor/leaflet/` (BSD-2-Clause), so maps work offline |
| Google Fonts: Bricolage Grotesque, DM Sans, JetBrains Mono | Typography. System fonts are used offline |

There is no language model and no proprietary data. Plain CSS, no CSS framework.

## Running the demo offline

Everything the site needs is in this repository: the data, Leaflet, and the scripts. With
Wi-Fi off, the pages, filters, maps and decisions all work. Only two things need internet:

- **Map background tiles:** the vessel dots show on a plain dark background, with a note.
- **Web fonts:** system fonts are used instead.

Downloading fresh GFW data also needs internet.

## Known limits

- **Prototype.** Not an official enforcement tool. A high score is a reason to look closer,
  not proof of illegal fishing.
- **No radar data yet.** GFW's satellite radar (SAR) reports were *temporarily unavailable*
  in November 2026, so there are no "dark vessel" contacts. The pipeline adds them
  automatically when `fetch_gfw.py` can download SAR data again; that part is untested on
  real data.
- **Innocent gaps.** Vessels switch off AIS to avoid pirates, and signals drop out far from
  land.
- **Simple proxies.** "Near the EEZ edge" means a gap starting 250–450 km from shore, not the
  real boundary line. Loitering counts only if it starts 20+ km from a port.
- **Encounters.** GFW records no carrier encounters inside this EEZ in the 12-month window, so
  that behaviour currently adds nothing.
- **Validation is weak evidence.** In the current run, 0 of the top 20 alerts are on the IOTC
  list, and so are 0 of 20 random vessels. Many listed vessels are old, renamed, or don't
  broadcast AIS. This does not show that the model works, or that it fails.
- **Data lag.** GFW data arrives a few days late, and "last seen" times reflect that.

## Project layout

```
app.py              Flask routes
translations.py     every piece of UI text, in English and French
templates/          page templates (Jinja)
static/             style.css, scripts, vendor/leaflet/
data/               alerts.csv, events.csv, iotc_iuu.csv (+ feedback.csv, validation.json, raw/ - not committed)
pipeline/           fetch_gfw.py, build_profiles.py, score.py, validate.py
tests/              unit tests and fixtures
design-reference/   the approved design screens
```

## Team

Built by Varshan and Neha Lenchu for the Tech Wave AI Hackathon, Mauritius.

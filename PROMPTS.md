# Prompts for Claude Code

Paste one prompt at a time. After each one: run the app, check the checkpoint in your browser, then commit and push.

---

## Prompt 0: Read and plan (no code changes)

Read CLAUDE.md, DESIGN.md and every file in design-reference/. Then give me a short plan for building Nightwatch in the phases listed in PROMPTS.md: which files you will create in each phase and anything in the design you think will be hard to build. Do not write or change any code yet.

---

## Prompt 1: Setup

Set up the Flask project as described in CLAUDE.md: app.py with one route that shows "Nightwatch" on a blank page, requirements.txt (flask, pandas), the folder layout, and a .gitignore (venv/, __pycache__/, .env, .DS_Store, data/feedback.csv). Run make_sample_data.py so data/ has the sample CSVs.

Checkpoint: `flask --app app run --debug` shows the page at http://127.0.0.1:5000.

---

## Prompt 2: Design foundation and languages

Build the shared pieces, following DESIGN.md:
1. static/style.css with all the CSS variables, fonts, and reusable classes (card, button, chip, flag row, command bar, section tag, header, footer).
2. templates/base.html with the app header (logo, tabs, EN | FR switch, COAST GUARD OPS, PROTOTYPE pill) and footer.
3. translations.py with a dictionary for "en" and "fr". Start with the header, tabs and footer text. Take the French wording from the -fr reference files.
4. Routes for /watch, /alert/<vessel_id>, /validation and their /fr/ versions, each showing an empty page that uses base.html in the right language.

Checkpoint: the EN | FR switch moves between /watch and /fr/watch, and the header matches Watch.dc.html.

---

## Prompt 3: Landing page

Build the landing page at / and /fr/ from Main.dc.html and Main-fr.dc.html: the sea-green hero with the chart grid, headline, command bar and radar graphic (inline SVG), the example alert card, How it decides, Does it work, Limits, the final call to action and the footer. All text from translations.py. The landing header has its own style (dark on sea green), with the EN | FR switch and an Open dashboard button.

Checkpoint: the page matches the reference at desktop width and stacks into one column at phone width (about 390px).

---

## Prompt 4: Watch dashboard on sample data

Build /watch from Watch.dc.html, reading data/alerts.csv with pandas:
1. The four counters: alerts shown, high risk, dark vessels, awaiting review (alerts with no row in feedback.csv).
2. Filters in a plain GET form: minimum risk (range input, default 40) and dark vessels only (checkbox). The page reloads with the filter applied.
3. A ranked table, highest risk first: rank, vessel, top reason, risk chip (number + level), action, Open link.
4. A Leaflet map as described in DESIGN.md, with one dot per filtered alert. Pass the rows to the page as JSON.

Explain how the data gets from the CSV into the map.

Checkpoint: moving the risk filter changes both the table and the map.

---

## Prompt 5: Alert detail and feedback

Build /alert/<vessel_id> from Alert.dc.html:
1. Name, gear, MMSI, last seen, and the risk score card with a progress bar.
2. "Why it was flagged": the three reasons with their points.
3. A small Leaflet map of this vessel's events from events.csv, joined in time order.
4. The recent activity table, newest first.
5. The suggested action card and the vessel info list (with the note that flag does not affect the score).
6. A decision form: optional note plus Confirm and False alarm buttons. POST appends a row to data/feedback.csv, then shows "Marked as confirmed" or "Marked as a false alarm" with an Undo button that removes that row.

Checkpoint: clicking Confirm adds a row to feedback.csv and the Watch page's "awaiting review" count goes down by one.

---

## Prompt 6: Real data pipeline (Global Fishing Watch)

Plan first and wait for my go-ahead. Then build pipeline/ to replace the sample data with real data:
1. fetch_gfw.py: use the official gfw-api-python-client package with the token from GFW_API_ACCESS_TOKEN. Look up the Mauritius EEZ region ID through the API (do not guess it). Pull the last 12 months of AIS gap, encounter, loitering, fishing and port visit events, plus SAR vessel detections (matched and unmatched). Check the exact dataset IDs in the GFW docs. Save raw results to data/raw/ so later steps and the demo work offline.
2. build_profiles.py: one row per vessel with features such as total AIS-off hours, gaps near the EEZ edge, encounters with carriers, loitering hours, days since last port visit, and number of identity changes. One row per unmatched radar detection, with features such as distance from shipping lanes and repeat detections nearby. Do not use flag as a feature.
3. score.py: scikit-learn IsolationForest on the features, scaled to a 0 to 100 risk. For each vessel, pick the three features furthest above normal, turn each into a plain-English sentence, and give it points in proportion to its share. Write data/alerts.csv and data/events.csv in exactly the columns in CLAUDE.md.

Explain each step in plain English so I can present it.

Checkpoint: the dashboard shows real vessels in the Mauritius EEZ with no changes to the website code.

---

## Prompt 7: Validation page

Build /validation from Validation.dc.html. Add pipeline/validate.py that loads the IOTC IUU vessel list (I will download it into data/iotc_iuu.csv), matches it to our vessels by IMO number, MMSI or name, and computes:
1. how many of our top 20 alerts are on the list,
2. the same for 20 vessels picked at random (fixed seed), as a baseline,
3. the false-alarm rate from feedback.csv,
4. the top-20 table with list match and officer decision.
Save the results to data/validation.json and show them on the page. Keep the Known limits card.

Checkpoint: no [X] placeholders left on the page.

---

## Prompt 8: Polish and submission

1. Check every page at 390px width and fix anything that overflows.
2. Add empty states ("No alerts match these filters") and a friendly message if a CSV is missing.
3. Make sure the demo runs with Wi-Fi off from cached data in data/ (the map tiles may not load offline; show a plain dark background instead).
4. Write README.md: what Nightwatch does, setup steps, data sources (Global Fishing Watch, IOTC IUU list) with attribution, every model and library used, the prototype disclaimer, and known limits.

Checkpoint: a full demo run-through, landing page to Confirm, in both languages, with no errors.

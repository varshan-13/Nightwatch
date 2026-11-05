# Phase 7: checking the ranking

Run from the repository root:

```sh
venv/bin/python pipeline/validate.py
```

The script reads `data/alerts.csv`, `data/iotc_iuu.csv`, optional
`data/raw/profiles.csv`, and optional `data/feedback.csv`. It writes
`data/validation.json`. Flask refreshes this snapshot when any of those inputs
changes, so saved/undone officer decisions appear on Validation and the landing
page without running the script manually. No extra dependencies or API requests
are needed for validation.

The profiles file is ignored by Git. Place the real profiles file from the scoring
run in `data/raw/profiles.csv` to enable IMO matching. Without it, the page clearly
states that only MMSI/name matching ran. The current local profiles cover all 407
alert IDs and contain 311 nonempty IMO numbers.

## Reference-list provenance

`data/iotc_iuu.csv` was prepared from the official IOTC IUU list linked at
https://iotc.org/node/37 (page update: 20 May 2026). The PDF itself is dated
15 May 2026:

https://iotc.org/sites/default/files/documents/compliance/vessel_lists/IUU%20lists/IOTC_IUU_Vessels_List_20260515%28E%2BF%29.pdf

Source PDF SHA-256:
`1a7bd391f75e37fe9fd8940779b31391b29ef6258062815469615c987ae2b883`

The CSV contains 201 IOTC records across 14 PDF pages, including 41 seven-digit
IMO identifiers. It is not a list of only a few dozen vessels. Each row retains
the official IOTC ID, source page/URL/date, original name and original identifier
for auditing. Parenthesized former names are pipe-separated in `aliases`.

The source column combines IMO and other unique vessel identifiers. Only
seven-digit numeric identifiers were copied to `imo`. Other identifiers are
retained in `source_identifier`; they were **not guessed to be MMSIs**. Therefore
this particular reference file has blank `mmsi` fields. MMSI matching works when
explicitly verified MMSIs are supplied in an updated CSV.

For a new reference-list snapshot, update the CSV using these canonical headers:
`iotc_id,name,aliases,imo,mmsi,source_url,list_date`. Extra audit columns are allowed.
Blank identifiers stay blank. Do not replace missing identifiers with fake zeros.
Always retain the source/date when refreshing the list.

## What the calculation means

- Match using exact normalized IMO, then MMSI, then name/former name. Ignore empty
  and unknown identities. Names ignore punctuation, case and accents; there is no
  fuzzy matching. Conflicting known IMOs and ambiguous reference identities are
  flagged instead of counted as matches. Name-only matches need human verification.
- Sort by descending risk, breaking ties by vessel ID. Count matches in the first
  20 unique vessels (or all vessels if fewer than 20).
- Draw a same-sized sample without replacement from the complete current dataset
  using seed 42. Sort IDs before sampling so CSV row order does not change the result.
  The baseline may overlap the top 20, as a random sample of the same population.
- Use the last saved decision per current vessel ID. Ignore reviews for vessels
  outside this dataset. Dismissal rate is `false_alarm / reviewed`; no reviews
  means `null`, not 0%. Undo removes the current decision.
- Save per-vessel match method, IOTC ID and decision in the top-20 table. The JSON
  also includes timestamps, input hashes, seed, cohort sizes and baseline vessel IDs.
  Local feedback and the generated JSON are ignored by Git; no review notes are
  copied into the validation snapshot.

Missing/empty reference data yields unavailable list metrics, not zero matches.
A supplied nonempty CSV with no usable identity columns fails with an explicit
error. Radar coverage stays unavailable: an AIS vessel count is not radar coverage.

Current local run: 0/20 top-ranked matches, 0/20 random matches, no current reviews.
This does **not** establish accuracy, statistical significance, or that any vessel
is innocent/guilty. List coverage, missing identities, historical names and the
choice of dataset all limit this check. The page keeps these limits visible.

## Checks

```sh
venv/bin/python -m unittest discover -s tests -v
```

Tests cover matching priority, aliases, ambiguity/conflicts, repeatable sampling,
small datasets, missing input, latest feedback, stale review IDs, JSON output,
bilingual rendering, and automatic refresh after feedback changes.

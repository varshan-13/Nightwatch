"""Step 3: score each vessel 0-100 and explain the score in plain words.

Run:  python3 pipeline/score.py   (after build_profiles.py)

Writes data/alerts.csv and data/events.csv with exactly the columns in CLAUDE.md,
so the website works with no changes.

How the score works, in plain English:
1. Most features are "a few vessels have huge numbers, most have zero", so we take
   log(1 + value) to stop one extreme vessel squashing everybody else.
2. An IsolationForest learns what normal behaviour looks like here. It isolates
   each vessel with random cuts; vessels that are easy to isolate are unusual.
3. Its anomaly score is stretched to 0-100: the most normal vessel gets 0, the
   most unusual gets 100.
4. For the reasons, we measure how far each feature is above the typical vessel
   (in standard deviations), keep the three furthest above normal, and split the
   risk points between them in proportion to how far above normal each one is.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).parent.parent
RAW, DATA = ROOT / "data" / "raw", ROOT / "data"
COLUMNS = ["vessel_id", "name", "mmsi", "flag", "gear", "dark", "lat", "lon", "risk",
           "reason_1", "reason_1_pts", "reason_2", "reason_2_pts",
           "reason_3", "reason_3_pts", "last_seen"]


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


# One plain-English sentence per feature. translations.py has a matching pattern
# for each, so the French pages and the short labels keep working.
SENTENCES = {
    "ais_off_hours": lambda v: f"AIS off for {round(v)} hours in total",
    "edge_gaps": lambda v: f"AIS switched off {plural(int(v), 'time')} near the EEZ edge",
    "carrier_encounters": lambda v: f"Met a refrigerated carrier {plural(int(v), 'time')} at sea",
    "loitering_hours": lambda v: f"Loitered {round(v)} hours far from port",
    "days_since_port": lambda v: f"No port visit in {int(v)} days",
    "identity_changes": lambda v: f"Changed name or ID {plural(int(v), 'time')} this year",
    "mpa_fishing_hours": lambda v: f"Fished {round(v)} hours inside a protected area",
    # radar contacts
    "detections": lambda v: f"Seen by radar {plural(int(v), 'time')} here this year",
}


def score(features):
    """IsolationForest anomaly score -> 0..100, plus how far above normal each feature is."""
    x = np.log1p(features)
    x = x.loc[:, x.std() > 0]          # a feature that is the same for everyone tells us nothing
    model = IsolationForest(n_estimators=300, random_state=42).fit(x)
    raw = -model.score_samples(x)       # higher = more unusual
    risk = (raw - raw.min()) / (raw.max() - raw.min()) * 100
    above_normal = (x - x.median()) / x.std()
    return np.clip(risk.round(), 1, 99).astype(int), above_normal


def explain(row_above, values, risk):
    """Top three features above normal, as sentences with points that add up to the risk."""
    top = row_above[row_above > 0].sort_values(ascending=False).head(3)
    reasons = [(SENTENCES[f](values[f]), row_above[f]) for f in top.index]
    total = sum(w for _, w in reasons) or 1
    out = {}
    for i in range(3):
        if i < len(reasons):
            out[f"reason_{i + 1}"] = reasons[i][0]
            out[f"reason_{i + 1}_pts"] = round(risk * reasons[i][1] / total)
        else:  # fewer than three things stand out: leave the slot empty
            out[f"reason_{i + 1}"], out[f"reason_{i + 1}_pts"] = "", 0
    return out


def score_vessels():
    p = pd.read_csv(RAW / "profiles.csv", dtype={"mmsi": str, "imo": str}, keep_default_na=False)
    features = p[["ais_off_hours", "edge_gaps", "carrier_encounters", "loitering_hours",
                  "days_since_port", "identity_changes", "mpa_fishing_hours"]].astype(float)
    risk, above = score(features)
    rows = []
    for i, r in p.iterrows():
        rows.append({
            "vessel_id": r["vessel_id"],
            "name": r["name"] or (f"MMSI {r['mmsi']}" if r["mmsi"] else "Unknown vessel"),
            "mmsi": r["mmsi"], "flag": r["flag"] or "Unknown", "gear": r["gear"],
            "dark": False, "lat": r["lat"], "lon": r["lon"], "risk": int(risk[i]),
            **explain(above.loc[i], features.loc[i], int(risk[i])),
            "last_seen": r["last_seen"],
        })
    return rows


def score_radar():
    """Radar grid cells with detections that no AIS vessel explains ("dark" contacts).
    GFW's SAR reports were unavailable in Nov 2026, so this returns nothing until
    fetch_gfw.py can download them."""
    cells = json.loads((RAW / "sar_unmatched.json").read_text())
    if not cells:
        print("No radar data: skipping dark contacts.")
        return []
    df = pd.DataFrame(cells)
    grid = df.groupby(["lat", "lon"], as_index=False).agg(
        detections=("detections", "sum"), last_seen=("date", "max"))
    features = grid[["detections"]].astype(float)
    risk, above = score(features) if len(grid) > 1 else (np.array([50]), features * 0 + 1)
    rows = []
    for i, g in grid.iterrows():
        reasons = explain(above.loc[i], features.loc[i], int(risk[i]))
        # Every dark contact's first reason is that radar saw it but AIS did not.
        rows.append({
            "vessel_id": f"RC-{i:04d}", "name": "Unidentified", "mmsi": "",
            "flag": "Unknown", "gear": "Unknown", "dark": True,
            "lat": round(g["lat"], 3), "lon": round(g["lon"], 3), "risk": int(risk[i]),
            "reason_1": "Radar detection with no AIS signal", "reason_1_pts": int(risk[i]) // 2,
            "reason_2": reasons["reason_1"], "reason_2_pts": int(risk[i]) - int(risk[i]) // 2,
            "reason_3": "", "reason_3_pts": 0,
            "last_seen": pd.Timestamp(g["last_seen"]).strftime("%Y-%m-%d %H:%M"),
        })
    return rows


def main():
    alerts = pd.DataFrame(score_vessels() + score_radar(), columns=COLUMNS)
    alerts = alerts.sort_values("risk", ascending=False)
    alerts.to_csv(DATA / "alerts.csv", index=False)

    events = pd.read_csv(RAW / "vessel_events.csv")
    events = events[events["vessel_id"].isin(alerts["vessel_id"])]
    events.sort_values("time", ascending=False).to_csv(DATA / "events.csv", index=False)

    levels = pd.cut(alerts["risk"], [-1, 39, 69, 100], labels=["Low", "Medium", "High"])
    print(f"Wrote {len(alerts)} alerts and {len(events)} events")
    print("Levels:", levels.value_counts().to_dict())
    print(alerts.head(8)[["name", "flag", "gear", "risk", "reason_1", "reason_1_pts"]].to_string(index=False))


if __name__ == "__main__":
    main()

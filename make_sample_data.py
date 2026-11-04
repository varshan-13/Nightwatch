# Placeholder data so the website can be built before the real GFW pipeline exists.
# The pipeline later writes data/alerts.csv and data/events.csv with the same columns.
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

REASONS = [
    "AIS off for {h} hours near EEZ edge",
    "Met a refrigerated carrier at sea",
    "Loitered {d} days far from port",
    "No port visit in {p} days",
    "Changed name or ID {c} times this year",
    "Fishing close to a protected area",
]
FLAGS = ["Panama", "Taiwan", "Seychelles", "Spain", "China", "Mauritius", "Comoros"]
GEARS = ["Longliner", "Purse seiner", "Carrier"]
EVENTS = ["AIS gap", "Encounter", "Loitering", "Fishing", "Port visit"]
NOW = pd.Timestamp("2026-11-01 06:00")

alerts, events = [], []
for i in range(60):
    vid = f"V{i:03d}"
    dark = rng.random() < 0.25
    lat, lon = rng.uniform(-24, -12), rng.uniform(54, 65)
    risk = int(np.clip(rng.normal(72 if dark else 42, 18), 1, 99))
    reasons = [REASONS[j].format(h=rng.integers(6, 48), d=rng.integers(1, 6),
                                 p=rng.integers(20, 90), c=rng.integers(2, 5))
               for j in rng.choice(len(REASONS), 3, replace=False)]
    if dark:
        reasons[0] = "Radar detection with no AIS signal"
    pts = sorted((rng.dirichlet([3, 2, 1]) * risk * 0.9).astype(int), reverse=True)
    alerts.append({
        "vessel_id": vid,
        "name": "Unidentified" if dark else f"Vessel {i:03d}",
        "mmsi": "" if dark else str(rng.integers(100000000, 999999999)),
        "flag": "Unknown" if dark else rng.choice(FLAGS),
        "gear": "Unknown" if dark else rng.choice(GEARS),
        "dark": dark,
        "lat": round(lat, 3),
        "lon": round(lon, 3),
        "risk": risk,
        "reason_1": reasons[0], "reason_1_pts": pts[0],
        "reason_2": reasons[1], "reason_2_pts": pts[1],
        "reason_3": reasons[2], "reason_3_pts": pts[2],
        "last_seen": (NOW - pd.Timedelta(hours=int(rng.integers(1, 72)))).strftime("%Y-%m-%d %H:%M"),
    })
    for _ in range(rng.integers(2, 6)):
        events.append({
            "vessel_id": vid,
            "event": rng.choice(EVENTS),
            "time": (NOW - pd.Timedelta(hours=int(rng.integers(1, 720)))).strftime("%Y-%m-%d %H:%M"),
            "lat": round(lat + rng.normal(0, 0.5), 3),
            "lon": round(lon + rng.normal(0, 0.5), 3),
        })

pd.DataFrame(alerts).to_csv(DATA / "alerts.csv", index=False)
pd.DataFrame(events).sort_values("time", ascending=False).to_csv(DATA / "events.csv", index=False)
print("Wrote data/alerts.csv and data/events.csv")

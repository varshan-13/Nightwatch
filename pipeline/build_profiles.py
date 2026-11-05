"""Step 2: turn the raw GFW events into one row of numbers per vessel.

Run:  python3 pipeline/build_profiles.py   (after fetch_gfw.py)

Reads data/raw/*.json and writes:
  data/raw/profiles.csv      one row per vessel: identity + behaviour features
  data/raw/vessel_events.csv every event for those vessels, for the alert pages

Behaviour features (all over the last 12 months):
  ais_off_hours        total hours the vessel's AIS was switched off
  edge_gaps            AIS gaps that started near the EEZ edge (250-450 km offshore;
                       the EEZ ends about 370 km from the islands)
  carrier_encounters   meetings at sea with a refrigerated carrier
  loitering_hours      hours spent drifting slowly at sea, 20+ km from any port
                       (possible transshipment)
  days_since_port      days since its last port visit anywhere in the world
  identity_changes     extra names / MMSI numbers / flags it broadcast this year
  mpa_fishing_hours    hours of apparent fishing inside a marine protected area

The vessel's flag is kept for display only. It is NOT a feature, so it can never
raise the score.
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw"
VESSEL_TYPES = ("fishing", "carrier")
FEATURES = ["ais_off_hours", "edge_gaps", "carrier_encounters", "loitering_hours",
            "days_since_port", "identity_changes", "mpa_fishing_hours"]

# Our display names for GFW event types (CLAUDE.md data contract).
EVENT_NAMES = {"gap": "AIS gap", "encounter": "Encounter", "loitering": "Loitering",
               "fishing": "Fishing", "port_visit": "Port visit"}


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def hours_in_window(e, start, end):
    """Hours of an event that fall inside our 12-month window.
    (Some GFW gaps last years; we only count the part inside the window.)"""
    s, f = max(when(e["start"]), start), min(when(e["end"] or e["start"]), end)
    return max((f - s).total_seconds() / 3600, 0)


def event_position(e):
    """Where to put the event on the map. For a gap, where the AIS went off."""
    if e["type"] == "gap" and (e["gap"] or {}).get("off_position"):
        p = e["gap"]["off_position"]
    else:
        p = e["position"]
    return p["lat"], p["lon"]


def identity(record):
    """Latest name, MMSI, IMO, flag and gear from a vessel identity record,
    plus how many different identities it used during the window."""
    reports = sorted(record["self_reported_info"] or [],
                     key=lambda r: r["transmission_date_to"] or "")
    latest = reports[-1] if reports else {}
    gear = ""
    for c in record.get("combined_sources_info") or []:
        if c.get("gear_types"):
            gear = c["gear_types"][-1]["name"]
    registry = (record.get("registry_info") or [{}])[0]
    return {
        "name": latest.get("ship_name") or registry.get("ship_name") or "",
        "mmsi": latest.get("ssvid") or "",
        "imo": latest.get("imo") or registry.get("imo") or "",
        "flag": latest.get("flag") or registry.get("flag") or "",
        "gear_code": gear,
        "reports": reports,
    }


def gear_label(code, vessel_type):
    """GFW gear codes (e.g. DRIFTING_LONGLINES) -> the simple names the site shows."""
    code = (code or "").upper()
    if "LONGLINE" in code:
        return "Longliner"
    if "PURSE_SEINE" in code:
        return "Purse seiner"
    if "TRAWL" in code:
        return "Trawler"
    if "CARRIER" in code or "REEFER" in code or vessel_type == "carrier":
        return "Carrier"
    return "Fishing vessel"


def main():
    events = []
    for name in ["gaps", "encounters", "loitering", "fishing", "port_visits"]:
        events += load(f"events_{name}")
    events = [e for e in events if e["vessel"]["type"] in VESSEL_TYPES]

    # The window ends at the newest event we have (GFW data lags a few days).
    end = max(when(e["end"] or e["start"]) for e in events)
    start = end - timedelta(days=365)
    events = [e for e in events if when(e["end"] or e["start"]) >= start]
    print(f"{len(events)} events from {start:%Y-%m-%d} to {end:%Y-%m-%d}")

    identities = {}
    for record in load("identities"):
        for report in record["self_reported_info"] or []:
            identities.setdefault(report["id"], record)

    # Last port visit anywhere in the world, per vessel.
    last_port = {}
    for v in load("port_visits_global"):
        vid, t = v["vessel"]["id"], when(v["end"] or v["start"])
        last_port[vid] = max(last_port.get(vid, t), t)

    rows, event_rows = [], []
    by_vessel = {}
    for e in events:
        by_vessel.setdefault(e["vessel"]["id"], []).append(e)

    for vid, evs in by_vessel.items():
        f = dict.fromkeys(FEATURES, 0.0)
        for e in evs:
            if e["type"] == "gap":
                f["ais_off_hours"] += hours_in_window(e, start, end)
                shore = (e["distances"] or {}).get("start_distance_from_shore_km") or 0
                if 250 <= shore <= 450:
                    f["edge_gaps"] += 1
            elif e["type"] == "encounter":
                if "CARRIER" in ((e["encounter"] or {}).get("type") or "").upper():
                    f["carrier_encounters"] += 1
            elif e["type"] == "loitering":
                # Ignore boats waiting at anchor next to a port: only count
                # loitering that starts at least 20 km from the nearest port.
                port_km = (e["distances"] or {}).get("start_distance_from_port_km") or 0
                if port_km >= 20:
                    f["loitering_hours"] += hours_in_window(e, start, end)
            elif e["type"] == "fishing":
                if (e["regions"] or {}).get("mpa"):
                    f["mpa_fishing_hours"] += hours_in_window(e, start, end)

        # No port visit in the whole year counts as 365 days.
        if vid in last_port:
            f["days_since_port"] = min(max((end - last_port[vid]).days, 0), 365)
        else:
            f["days_since_port"] = 365

        ident = identity(identities[vid]) if vid in identities else None
        if ident:
            in_window = {(r["ship_name"], r["ssvid"], r["flag"]) for r in ident["reports"]
                         if r["transmission_date_to"] and when(r["transmission_date_to"]) >= start}
            f["identity_changes"] = max(len(in_window) - 1, 0)

        # Drifting fishing-gear buoys broadcast AIS with their battery level in the
        # name (e.g. "BOAT A 92%"). Some are labelled as fishing vessels; skip them.
        name = (ident and ident["name"]) or evs[0]["vessel"]["name"] or ""
        if re.search(r"\d+\s*%$", name):
            continue

        latest = max(evs, key=lambda e: e["end"] or e["start"])
        lat, lon = event_position(latest)
        first = evs[0]["vessel"]
        rows.append({
            "vessel_id": vid,
            "name": name,
            "mmsi": (ident and ident["mmsi"]) or first["ssvid"] or "",
            "imo": ident["imo"] if ident else "",
            "flag": (ident and ident["flag"]) or first["flag"] or "Unknown",
            "gear": gear_label(ident["gear_code"] if ident else "", first["type"]),
            "lat": round(lat, 3), "lon": round(lon, 3),
            "last_seen": when(latest["end"] or latest["start"]).strftime("%Y-%m-%d %H:%M"),
            **{k: round(v, 1) for k, v in f.items()},
        })
        for e in evs:
            lat, lon = event_position(e)
            event_rows.append({"vessel_id": vid, "event": EVENT_NAMES[e["type"]],
                               "time": when(e["start"]).strftime("%Y-%m-%d %H:%M"),
                               "lat": round(lat, 3), "lon": round(lon, 3)})

    profiles = pd.DataFrame(rows)
    profiles.to_csv(RAW / "profiles.csv", index=False)
    pd.DataFrame(event_rows).to_csv(RAW / "vessel_events.csv", index=False)
    print(f"Wrote {len(profiles)} vessel profiles")
    print(profiles[FEATURES].describe().round(1).to_string())


if __name__ == "__main__":
    main()

"""Step 1: download real data from Global Fishing Watch and save it in data/raw/.

Run:  python3 pipeline/fetch_gfw.py
Needs the GFW_API_ACCESS_TOKEN environment variable (never put the token in code).

What it saves (all JSON, so later steps and the demo work offline):
  data/raw/eez.json                 the Mauritius EEZ region we looked up
  data/raw/events_<type>.json       12 months of AIS gaps, encounters, loitering,
                                    fishing and port visits inside the EEZ
  data/raw/identities.json          name, MMSI, IMO, flag and gear history of each
                                    fishing vessel / carrier we saw
  data/raw/port_visits_global.json  the same vessels' port visits anywhere in the
                                    world (not only Mauritius), so a foreign boat that
                                    docked in Reunion isn't counted as "never in port"
  data/raw/sar_unmatched.json       satellite radar detections with NO AIS match
  data/raw/sar_matched.json         radar detections that DO match an AIS vessel
"""
import asyncio
import datetime
import json
import os
from pathlib import Path

import gfwapiclient as gfw

RAW = Path(__file__).parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# We only score fishing vessels and carriers. GFW also tracks cargo ships, ferries
# and drifting fishing-gear buoys, which would swamp the ranking.
VESSEL_TYPES = ("fishing", "carrier")
BATCH = 50  # vessel ids per API call

END = datetime.date.today()
START = END - datetime.timedelta(days=365)

# One GFW dataset per event type. Names come from the client's documentation.
EVENT_DATASETS = {
    "gaps": "public-global-gaps-events:latest",
    "encounters": "public-global-encounters-events:latest",
    "loitering": "public-global-loitering-events:latest",
    "fishing": "public-global-fishing-events:latest",
    "port_visits": "public-global-port-visits-events:latest",
}


def save(name, rows):
    path = RAW / f"{name}.json"
    path.write_text(json.dumps(rows, indent=1, default=str))
    print(f"  saved {len(rows):>6} rows -> {path.relative_to(RAW.parent.parent)}")


async def find_eez(client):
    """Look up the Mauritius EEZ in GFW's region list instead of guessing its ID.
    There are three matches (main EEZ, Chagos, Tromelin overlap); we keep the main one,
    which covers Mauritius, Rodrigues, St Brandon and Agaléga."""
    regions = (await client.references.get_eez_regions()).df()
    match = regions[regions["label"] == "Mauritian Exclusive Economic Zone"]
    eez = {"dataset": "public-eez-areas", "id": str(int(match.iloc[0]["id"])),
           "label": match.iloc[0]["label"]}
    print(f"EEZ: {eez['label']} (id {eez['id']})")
    return eez


async def main():
    client = gfw.Client(access_token=os.environ["GFW_API_ACCESS_TOKEN"])
    eez = await find_eez(client)
    save("eez", [eez])
    region = {"dataset": eez["dataset"], "id": eez["id"]}
    print(f"Dates: {START} to {END}")

    for name, dataset in EVENT_DATASETS.items():
        print(f"Fetching {name}...")
        result = await client.events.get_all_events(
            datasets=[dataset], start_date=START, end_date=END, region=region)
        save(f"events_{name}", [e.model_dump(mode="json") for e in result.data()])

    # Every fishing vessel / carrier that appeared in any event above.
    ids = sorted({e["vessel"]["id"] for name in EVENT_DATASETS
                  for e in json.loads((RAW / f"events_{name}.json").read_text())
                  if e["vessel"]["type"] in VESSEL_TYPES})
    print(f"{len(ids)} fishing vessels / carriers found")
    batches = [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]

    print("Fetching vessel identities...")
    identities = []
    for batch in batches:
        result = await client.vessels.get_vessels_by_ids(ids=batch)
        identities += [v.model_dump(mode="json") for v in result.data()]
    save("identities", identities)

    print("Fetching their port visits worldwide...")
    visits = []
    for batch in batches:
        result = await client.events.get_all_events(
            datasets=[EVENT_DATASETS["port_visits"]], vessels=batch,
            start_date=START, end_date=END)
        visits += [e.model_dump(mode="json") for e in result.data()]
    save("port_visits_global", visits)

    # Radar (SAR) detections come as a grid: each row is one map cell and one month,
    # with how many boats the satellite saw there. "matched" means GFW could link
    # the radar dot to a ship sending AIS at that moment.
    for matched in ("false", "true"):
        print(f"Fetching SAR detections, matched={matched}...")
        name = "sar_unmatched" if matched == "false" else "sar_matched"
        try:
            result = await client.fourwings.create_sar_presence_report(
                spatial_resolution="HIGH", temporal_resolution="MONTHLY",
                filters=[f"matched='{matched}'"],
                start_date=START, end_date=END, region=region)
            save(name, [r.model_dump(mode="json") for r in result.data()])
        except gfw.exceptions.GFWAPIClientError as error:
            # In Nov 2026 GFW paused SAR reports ("temporarily unavailable").
            # We carry on without radar data; re-run this script once it is back.
            print(f"  SAR not available: {str(error)[:120]}")
            save(name, [])


if __name__ == "__main__":
    asyncio.run(main())

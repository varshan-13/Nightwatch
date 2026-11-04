from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request

from translations import T, translate_reason

app = Flask(__name__)
DATA = Path(__file__).parent / "data"


# ---------- Data ----------

def level_of(risk):
    """High / Medium / Low, from the rule in CLAUDE.md. Never stored in the CSV."""
    if risk >= 70:
        return "high"
    if risk >= 40:
        return "med"
    return "low"


ACTION = {"high": "send_patrol", "med": "keep_watching", "low": "no_action"}


def load_alerts():
    """Read alerts.csv and add the computed level and action to each row."""
    df = pd.read_csv(DATA / "alerts.csv", dtype={"mmsi": str})
    df["mmsi"] = df["mmsi"].fillna("")
    df["level"] = df["risk"].apply(level_of)
    df["action"] = df["level"].map(ACTION)
    return df.sort_values("risk", ascending=False)


def reviewed_ids():
    """Vessel ids that already have an officer decision in feedback.csv."""
    path = DATA / "feedback.csv"
    if not path.exists():
        return set()
    return set(pd.read_csv(path)["vessel_id"])


# ---------- Pages ----------
# Each page has two URLs: English (/watch) and French (/fr/watch).
# `defaults` tells Flask which language each URL means, so the view gets `lang`
# and url_for('watch', lang='fr') builds /fr/watch.

def page(template, lang, **data):
    return render_template(template, lang=lang, t=T[lang],
                           reason=lambda text: translate_reason(text, lang), **data)


@app.route("/", defaults={"lang": "en"})
@app.route("/fr/", defaults={"lang": "fr"})
def landing(lang):
    return page("landing.html", lang)


@app.route("/watch", defaults={"lang": "en"})
@app.route("/fr/watch", defaults={"lang": "fr"})
def watch(lang):
    # Filters come from the URL, e.g. /watch?min_risk=60&dark=1&q=014
    min_risk = request.args.get("min_risk", 40, type=int)
    dark_only = request.args.get("dark") == "1"
    q = request.args.get("q", "").strip()

    df = load_alerts()
    df = df[df["risk"] >= min_risk]
    if dark_only:
        df = df[df["dark"]]
    if q:
        text = df["name"] + " " + df["mmsi"] + " " + df["vessel_id"]
        df = df[text.str.contains(q, case=False, regex=False)]

    reviewed = reviewed_ids()
    counts = {
        "alerts": len(df),
        "high": int((df["level"] == "high").sum()),
        "dark": int(df["dark"].sum()),
        "awaiting": int((~df["vessel_id"].isin(reviewed)).sum()),
    }

    # The same filtered rows feed the table and the map.
    # The map only needs a few fields; the template turns this list into JSON.
    rows = df.to_dict("records")
    points = [{"id": r["vessel_id"], "name": r["vessel_id"] if r["dark"] else r["name"],
               "lat": r["lat"], "lon": r["lon"], "risk": r["risk"],
               "level": r["level"], "dark": bool(r["dark"])} for r in rows]
    return page("watch.html", lang, rows=rows, points=points, counts=counts,
                min_risk=min_risk, dark_only=dark_only, q=q)


@app.route("/alert/<vessel_id>", defaults={"lang": "en"})
@app.route("/fr/alert/<vessel_id>", defaults={"lang": "fr"})
def alert(lang, vessel_id):
    return page("alert.html", lang, vessel_id=vessel_id)


@app.route("/validation", defaults={"lang": "en"})
@app.route("/fr/validation", defaults={"lang": "fr"})
def validation(lang):
    return page("validation.html", lang)

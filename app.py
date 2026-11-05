from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, abort, redirect, render_template, request, url_for

from translations import T, reason_label, translate_reason

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
    # A low-risk vessel may have fewer than three reasons; empty slots are blank.
    for i in (1, 2, 3):
        df[f"reason_{i}"] = df[f"reason_{i}"].fillna("")
    df["level"] = df["risk"].apply(level_of)
    df["action"] = df["level"].map(ACTION)
    return df.sort_values("risk", ascending=False)


FEEDBACK = DATA / "feedback.csv"
FEEDBACK_COLUMNS = ["vessel_id", "label", "note", "time"]


def load_feedback():
    """All officer decisions so far. feedback.csv is created by the first decision."""
    if not FEEDBACK.exists():
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)
    return pd.read_csv(FEEDBACK, dtype=str, keep_default_na=False)


def reviewed_ids():
    """Vessel ids that already have an officer decision in feedback.csv."""
    return set(load_feedback()["vessel_id"])


def load_events(vessel_id):
    """This vessel's events from events.csv, oldest first."""
    df = pd.read_csv(DATA / "events.csv")
    df = df[df["vessel_id"] == vessel_id]
    return df.sort_values("time").to_dict("records")


def hours_since(time_text):
    """How many whole hours ago a 'YYYY-MM-DD HH:MM' time was."""
    return int((datetime.now() - datetime.strptime(time_text, "%Y-%m-%d %H:%M")).total_seconds() // 3600)


# ---------- Pages ----------
# Each page has two URLs: English (/watch) and French (/fr/watch).
# `defaults` tells Flask which language each URL means, so the view gets `lang`
# and url_for('watch', lang='fr') builds /fr/watch.

def page(template, lang, **data):
    return render_template(template, lang=lang, t=T[lang],
                           reason=lambda text: translate_reason(text, lang),
                           reason_label=lambda text: reason_label(text, lang),
                           fmt_time=lambda text: fmt_time(text, lang), **data)


def fmt_time(text, lang):
    """'2026-11-01 00:10' -> '01 NOV 00:10' (month name in the page language)."""
    d = datetime.strptime(text, "%Y-%m-%d %H:%M")
    return f"{d:%d} {T[lang]['months'][d.month - 1]} {d:%H:%M}"


@app.route("/", defaults={"lang": "en"})
@app.route("/fr/", defaults={"lang": "fr"})
def landing(lang):
    # "Open a sample alert" goes to whichever vessel currently ranks highest.
    return page("landing.html", lang, top_id=load_alerts().iloc[0]["vessel_id"])


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
    alerts = load_alerts()
    match = alerts[alerts["vessel_id"] == vessel_id]
    if match.empty:
        abort(404)
    a = match.to_dict("records")[0]

    # The three reasons, each with its points. Rows worth 20+ points are drawn
    # in the high colour, smaller ones in the medium colour.
    reasons = [{"text": a[f"reason_{i}"], "pts": int(a[f"reason_{i}_pts"]),
                "level": "high" if a[f"reason_{i}_pts"] >= 20 else "med"}
               for i in (1, 2, 3) if a[f"reason_{i}"]]

    events = load_events(vessel_id)

    # Track for the map: every event in time order, then the last known position.
    # A segment that starts at an "AIS gap" is drawn dashed (AIS off, estimated).
    track = [{"lat": e["lat"], "lon": e["lon"], "event": e["event"], "time": e["time"]} for e in events]
    track.append({"lat": a["lat"], "lon": a["lon"], "event": "Last seen", "time": a["last_seen"]})
    track.sort(key=lambda p: p["time"])

    # The officer's decision, if there is one (the latest row for this vessel).
    fb = load_feedback()
    fb = fb[fb["vessel_id"] == vessel_id]
    decision = fb.iloc[-1]["label"] if len(fb) else None

    return page("alert.html", lang, a=a, reasons=reasons,
                events=list(reversed(events)),  # table: newest first
                track=track, decision=decision, hours_ago=hours_since(a["last_seen"]))


# Decision form. POST adds one row to feedback.csv, then redirects back to the
# alert page (so reloading the page doesn't send the form twice).
@app.route("/alert/<vessel_id>/decide", methods=["POST"], defaults={"lang": "en"})
@app.route("/fr/alert/<vessel_id>/decide", methods=["POST"], defaults={"lang": "fr"})
def decide(lang, vessel_id):
    label = request.form["label"]
    if label not in ("confirmed", "false_alarm"):
        abort(400)
    row = pd.DataFrame([{"vessel_id": vessel_id, "label": label,
                         "note": request.form.get("note", "").strip(),
                         "time": datetime.now().strftime("%Y-%m-%d %H:%M")}])
    # Append; write the header only when the file is new.
    row.to_csv(FEEDBACK, mode="a", header=not FEEDBACK.exists(), index=False)
    return redirect(url_for("alert", lang=lang, vessel_id=vessel_id))


# Undo removes this vessel's latest row from feedback.csv.
@app.route("/alert/<vessel_id>/undo", methods=["POST"], defaults={"lang": "en"})
@app.route("/fr/alert/<vessel_id>/undo", methods=["POST"], defaults={"lang": "fr"})
def undo(lang, vessel_id):
    fb = load_feedback()
    rows = fb.index[fb["vessel_id"] == vessel_id]
    if len(rows):
        fb.drop(rows[-1]).to_csv(FEEDBACK, index=False)
    return redirect(url_for("alert", lang=lang, vessel_id=vessel_id))


@app.route("/validation", defaults={"lang": "en"})
@app.route("/fr/validation", defaults={"lang": "fr"})
def validation(lang):
    return page("validation.html", lang)

from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from datetime import datetime, timezone
import os
import shutil
import json
import secrets
from threading import Lock

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, abort

from pipeline.validate import build_validation, fingerprints, write_validation

from translations import T, reason_label, translate_reason

app = Flask(__name__)
DATA = Path(__file__).parent / "data"

# Hosting on Vercel: the project folder is read-only there, and only /tmp can be
# written. Copy the data to /tmp at start-up so officer decisions and the
# validation snapshot can be saved. /tmp is per server instance and is wiped when
# Vercel recycles it, so hosted decisions are for demos only.
if os.environ.get("VERCEL"):
    hosted = Path("/tmp/nightwatch-data")
    hosted.mkdir(exist_ok=True)
    for source in DATA.glob("*.*"):  # copy contents only, so the copies are writable
        if not (hosted / source.name).exists():
            shutil.copyfile(source, hosted / source.name)
    DATA = hosted
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
feedback_lock = Lock()


@app.context_processor
def data_status():
    # True when there is no alerts.csv yet; base.html shows a friendly notice.
    return {"data_missing": not (DATA / "alerts.csv").exists()}


@app.context_processor
def review_token():
    if "review_token" not in session:
        session["review_token"] = secrets.token_hex(32)
    return {"review_token": session["review_token"]}


def load_feedback():
    path = DATA / "feedback.csv"
    if not path.exists():
        return pd.DataFrame(columns=["vessel_id", "label", "note", "time"])
    return pd.read_csv(path, keep_default_na=False).drop_duplicates("vessel_id", keep="last")


def save_decision(vessel_id, label, note):
    # One current decision per vessel. Replace the file only after writing succeeds.
    with feedback_lock:
        feedback = load_feedback()
        feedback = feedback[feedback["vessel_id"] != vessel_id].reset_index(drop=True)
        if label != "undo":
            feedback.loc[len(feedback)] = [vessel_id, label, note, datetime.now(timezone.utc).isoformat(timespec="seconds")]
        temporary = DATA / "feedback.csv.tmp"
        try:
            feedback.to_csv(temporary, index=False)
            temporary.replace(DATA / "feedback.csv")
        finally:
            temporary.unlink(missing_ok=True)


# ---------- Data ----------

def level_of(risk):
    """High / Medium / Low, from the rule in CLAUDE.md. Never stored in the CSV."""
    if risk >= 70:
        return "high"
    if risk >= 40:
        return "med"
    return "low"


ACTION = {"high": "send_patrol", "med": "keep_watching", "low": "no_action"}


ALERT_COLUMNS = ["vessel_id", "name", "mmsi", "flag", "gear", "dark", "lat", "lon", "risk",
                 "reason_1", "reason_1_pts", "reason_2", "reason_2_pts",
                 "reason_3", "reason_3_pts", "last_seen"]


def load_alerts():
    """Read alerts.csv and add the computed level and action to each row.
    If the file is missing, use an empty table so every page still opens
    (base.html then shows a notice saying how to create the data)."""
    path = DATA / "alerts.csv"
    if not path.exists():
        df = pd.DataFrame(columns=ALERT_COLUMNS).astype({"risk": int, "dark": bool})
    else:
        df = pd.read_csv(path, dtype={"mmsi": str})
    df["mmsi"] = df["mmsi"].fillna("")
    # A low-risk vessel may have fewer than three reasons; empty slots are blank.
    for i in (1, 2, 3):
        df[f"reason_{i}"] = df[f"reason_{i}"].fillna("")
    df["level"] = df["risk"].apply(level_of)
    df["action"] = df["level"].map(ACTION)
    return df.sort_values("risk", ascending=False)


def reviewed_ids():
    """Vessel ids that already have an officer decision in feedback.csv."""
    return set(load_feedback()["vessel_id"])


def load_validation():
    # Refresh whenever rankings, reference identities, or local decisions change.
    with feedback_lock:
        path = DATA / "validation.json"
        try:
            result = json.loads(path.read_text())
        except (FileNotFoundError, ValueError):
            result = {}
        if result.get("schema_version") != 1 or result.get("inputs") != fingerprints(DATA):
            try:
                result = write_validation(DATA)
            except OSError:
                # Can't save the snapshot (read-only disk): use the saved one if there
                # is one, otherwise work the results out in memory for this request.
                try:
                    result = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))
                except (FileNotFoundError, ValueError):
                    result = build_validation(DATA)
        return result


# ---------- Pages ----------
# Each page has two URLs: English (/watch) and French (/fr/watch).
# `defaults` tells Flask which language each URL means, so the view gets `lang`
# and url_for('watch', lang='fr') builds /fr/watch.

def watch_return(lang):
    origin = urlsplit(request.args.get("return_to", ""))
    if not origin.scheme and not origin.netloc and origin.path in {"/watch", "/fr/watch"}:
        query = parse_qs(origin.query)
        args = {key: query[key][-1] for key in ("min_risk", "max_risk", "q", "dark") if key in query}
    else:
        args = session.get("watch_filters", {})
    return url_for("watch", lang=lang, **args)


def page(template, lang, **data):
    return render_template(template, lang=lang, t=T[lang],
                           reason=lambda text: translate_reason(text, lang),
                           reason_label=lambda text: reason_label(text, lang),
                           watch_back=watch_return(lang), **data)


@app.route("/", defaults={"lang": "en"})
@app.route("/fr/", defaults={"lang": "fr"})
def landing(lang):
    # "Open a sample alert" goes to whichever vessel currently ranks highest.
    alerts = load_alerts()
    top_id = alerts.iloc[0]["vessel_id"] if len(alerts) else None
    return page("landing.html", lang, top_id=top_id, validation=load_validation())


@app.route("/watch", defaults={"lang": "en"})
@app.route("/fr/watch", defaults={"lang": "fr"})
def watch(lang):
    # Filters come from the URL, e.g. /watch?min_risk=60&dark=1&q=014
    min_risk = max(0, min(100, request.args.get("min_risk", 40, type=int)))
    max_risk = max(min_risk, min(100, request.args.get("max_risk", 100, type=int)))
    dark_only = request.args.get("dark") == "1"
    q = request.args.get("q", "").strip()

    df = load_alerts()
    total = len(df)
    session["watch_filters"] = {"min_risk": min_risk, "max_risk": max_risk, "q": q, **({"dark": "1"} if dark_only else {})}
    def filter_url(**changes):
        args = {"min_risk": min_risk, "max_risk": max_risk, "q": q, **({"dark": "1"} if dark_only else {})}
        args.update(changes)
        return url_for("watch", lang=lang, **args)
    df = df[df["risk"].between(min_risk, max_risk)]
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
                min_risk=min_risk, max_risk=max_risk, dark_only=dark_only, q=q,
                total=total, filter_url=filter_url)


@app.route("/alert/<vessel_id>", defaults={"lang": "en"}, methods=["GET", "POST"])
@app.route("/fr/alert/<vessel_id>", defaults={"lang": "fr"}, methods=["GET", "POST"])
def alert(lang, vessel_id):
    matches = load_alerts()
    matches = matches[matches["vessel_id"] == vessel_id]
    if matches.empty:
        return page("alert.html", lang, vessel=None), 404
    if request.method == "POST":
        if not session.get("review_token") or not secrets.compare_digest(session["review_token"], request.form.get("token", "")):
            abort(400)
        label = request.form.get("label", "")
        note = request.form.get("note", "").strip()
        if label not in {"confirmed", "false_alarm", "undo"} or len(note) > 2000:
            abort(400)
        save_decision(vessel_id, label, note)
        return redirect(url_for("alert", lang=lang, vessel_id=vessel_id, saved=label, return_to=request.args.get("return_to")), code=303)
    vessel = matches.iloc[0].to_dict()
    events_path = DATA / "events.csv"
    events = []
    if events_path.exists():
        df = pd.read_csv(events_path)
        df = df[df["vessel_id"] == vessel_id].sort_values("time", ascending=False)
        events = df.to_dict("records")
    reasons = [{"text": vessel[f"reason_{n}"], "points": vessel[f"reason_{n}_pts"]}
               for n in range(1, 4) if vessel[f"reason_{n}"]]
    feedback = load_feedback()
    decisions = feedback[feedback["vessel_id"] == vessel_id].to_dict("records")
    return page("alert.html", lang, vessel=vessel, events=events, reasons=reasons,
                decision=decisions[0] if decisions else None)


@app.route("/validation", defaults={"lang": "en"})
@app.route("/fr/validation", defaults={"lang": "fr"})
def validation(lang):
    return page("validation.html", lang, validation=load_validation())


@app.route("/alerts", defaults={"lang": "en"})
@app.route("/fr/alerts", defaults={"lang": "fr"})
def alerts(lang):
    status = request.args.get("status", "pending")
    if status not in {"pending", "reviewed", "all"}:
        status = "pending"
    feedback = {row["vessel_id"]: row for row in load_feedback().to_dict("records")}
    rows = load_alerts().to_dict("records")
    counts = {"all": len(rows), "reviewed": sum(row["vessel_id"] in feedback for row in rows)}
    counts["pending"] = counts["all"] - counts["reviewed"]
    if status != "all":
        rows = [row for row in rows if (row["vessel_id"] in feedback) == (status == "reviewed")]
    return page("alerts.html", lang, rows=rows, feedback=feedback, counts=counts, status=status)

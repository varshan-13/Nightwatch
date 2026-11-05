"""Phase 7: compare the ranking with a locally supplied IOTC IUU CSV.

Run: python pipeline/validate.py
CSV columns: name, imo, mmsi (blank identifiers allowed); optional iotc_id,
aliases (pipe-separated), source_url, list_date. See pipeline/VALIDATION.md.
No network requests, API tokens, or extra dependencies are needed.
"""
import csv
import hashlib
import json
import random
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data'
SEED = 42
INPUTS = ('alerts.csv', 'iotc_iuu.csv', 'raw/profiles.csv', 'feedback.csv')


def fingerprints(data):
    return {name: hashlib.sha256((data / name).read_bytes()).hexdigest()
            if (data / name).exists() else None for name in INPUTS}


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return [{key.strip().lower(): (value or '').strip() for key, value in row.items()
                 if key is not None} for row in reader]


def identifier(value, length):
    value = str(value or '').strip()
    value = re.sub(r'\.0$', '', value)
    value = re.sub(r'^(IMO|MMSI)\s*[:#-]?\s*', '', value, flags=re.I)
    return value if re.fullmatch(r'\d{' + str(length) + '}', value) and int(value) else ''


def vessel_name(value):
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r'[^A-Z0-9]', '', value.upper())
    return '' if value in {'', 'UNKNOWN', 'UNIDENTIFIED', 'NA', 'NONE', 'UNK', 'INC'} else value


def match_vessel(vessel, imo, entries):
    """Exact normalized matches, strongest identifier first. No fuzzy accusations.

    A duplicate/ambiguous name or conflicting known IMO prevents a name match.
    Historical identities may be supplied as separate rows sharing iotc_id.
    """
    keys = [('imo', identifier(imo, 7)), ('mmsi', identifier(vessel.get('mmsi'), 9)),
            ('name', vessel_name(vessel.get('name')))]
    for method, key in keys:
        if not key:
            continue
        candidates = []
        for entry in entries:
            values = ([entry.get('name', '')] + entry.get('aliases', '').split('|')) if method == 'name' else [entry.get(method, '')]
            normalize = vessel_name if method == 'name' else lambda v: identifier(v, 7 if method == 'imo' else 9)
            if key in {normalize(v) for v in values}:
                candidates.append(entry)
        if not candidates:
            continue
        identities = {entry.get('iotc_id') or str(entry) for entry in candidates}
        if len(identities) > 1:
            return {'on_iotc': False, 'match_method': 'ambiguous', 'iotc_id': None}
        entry = candidates[0]
        known_imo = identifier(entry.get('imo'), 7)
        if method != 'imo' and identifier(imo, 7) and known_imo and identifier(imo, 7) != known_imo:
            return {'on_iotc': False, 'match_method': 'conflict', 'iotc_id': None}
        return {'on_iotc': True, 'match_method': method, 'iotc_id': entry.get('iotc_id') or None}
    return {'on_iotc': False, 'match_method': None, 'iotc_id': None}


def build_validation(data=DATA):
    alerts = read_csv(data / 'alerts.csv')
    ids = [row['vessel_id'] for row in alerts]
    if len(set(ids)) != len(ids):
        raise ValueError('alerts.csv must contain one row per vessel_id')
    alerts.sort(key=lambda row: (-float(row['risk']), row['vessel_id']))
    entries = read_csv(data / 'iotc_iuu.csv')
    if entries and not any(vessel_name(e.get('name')) or identifier(e.get('imo'), 7) or identifier(e.get('mmsi'), 9) for e in entries):
        raise ValueError('IOTC CSV needs usable name, imo or mmsi columns')
    profiles = {r['vessel_id']: r for r in read_csv(data / 'raw/profiles.csv')}
    # Last decision wins; ignore stale feedback for vessels outside this dataset.
    feedback = {r['vessel_id']: r for r in read_csv(data / 'feedback.csv')
                if r.get('label') in {'confirmed', 'false_alarm'} and r.get('vessel_id') in set(ids)}
    matches = {r['vessel_id']: match_vessel(r, profiles.get(r['vessel_id'], {}).get('imo'), entries)
               for r in alerts} if entries else {}
    size = min(20, len(alerts))
    # Sort before sampling so CSV row order cannot change the baseline.
    baseline = random.Random(SEED).sample(sorted(alerts, key=lambda r: r['vessel_id']), size)
    reviewed = len(feedback)
    false_alarms = sum(r['label'] == 'false_alarm' for r in feedback.values())
    top = [{
        'rank': i + 1, 'vessel_id': r['vessel_id'], 'name': r['name'], 'risk': float(r['risk']),
        **matches.get(r['vessel_id'], {'on_iotc': None, 'match_method': None, 'iotc_id': None}),
        'decision': feedback.get(r['vessel_id'], {}).get('label'),
    } for i, r in enumerate(alerts[:size])]
    return {
        'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'inputs': fingerprints(data), 'seed': SEED, 'vessel_count': len(alerts), 'sample_size': size,
        'list_available': bool(entries), 'list_rows': len(entries),
        'list_dates': sorted({r['list_date'] for r in entries if r.get('list_date')}),
        'source_urls': sorted({r['source_url'] for r in entries if r.get('source_url')}),
        'imo_profiles_available': bool(profiles),
        'imo_vessels': sum(bool(identifier(profiles.get(r['vessel_id'], {}).get('imo'), 7)) for r in alerts),
        'top20_hits': sum(r['on_iotc'] for r in top) if entries and size else None,
        'random_hits': sum(matches[r['vessel_id']]['on_iotc'] for r in baseline) if entries and size else None,
        'baseline_ids': [r['vessel_id'] for r in baseline],
        'reviewed_count': reviewed, 'false_alarm_count': false_alarms,
        'false_alarm_rate': false_alarms / reviewed if reviewed else None,
        'radar_coverage': None, 'top20': top,
    }


def write_validation(data=DATA):
    result = build_validation(data)
    path = data / 'validation.json'
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)
    return result


if __name__ == '__main__':
    result = write_validation()
    print(f"Top {result['sample_size']}: {result['top20_hits']}; random: {result['random_hits']}; reviewed: {result['reviewed_count']}")
    if not result['list_available']:
        print('IOTC list missing/empty: supply data/iotc_iuu.csv. List-based metrics are unavailable, not zero.')
    if not result['imo_profiles_available']:
        print('Raw profiles missing: matching uses MMSI and name only.')
    print('Wrote data/validation.json')

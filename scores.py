"""Local best times per seed."""

import json
from pathlib import Path

_SCORES_PATH = Path(__file__).parent / "best_times.json"


def _load_all():
    if not _SCORES_PATH.exists():
        return {}
    try:
        return json.loads(_SCORES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def get_best(seed):
    entry = _load_all().get(str(seed))
    if not entry:
        return None
    return {"time": entry["time"], "cores": entry.get("cores", 0)}


def save_best(seed, time_sec, cores):
    data = _load_all()
    key = str(seed)
    prev = data.get(key)
    if prev is not None and prev["time"] <= time_sec:
        return False
    data[key] = {"time": round(time_sec, 2), "cores": cores}
    _SCORES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return True

"""Lane log front matter (docs/bakeoff/lane-log-format.md): parse it, list its problems, and total its numbers.
THROWAWAY bake-off tooling."""

import math
from datetime import datetime
from pathlib import Path

import yaml

# The five lanes the plan runs, with the direction and engine each one is for.
LANES = {
    "g-a": ("A", "godot"),
    "g-d": ("D", "godot"),
    "u-d": ("D", "unity"),
    "g-c": ("C", "godot"),
    "control": ("control", "blender"),
}
ENUMS = {
    "direction": {"A", "C", "D", "control"},
    "engine": {"godot", "unity", "blender"},
    "machine": {"oryx", "sami"},
    "status": {"in-progress", "delivered", "blocked"},
}
FIELDS = ("lane", "direction", "engine", "machine", "status", "sessions", "costs", "interventions", "friction", "blockers", "deliverables")
# List field -> {item key: kind}; kinds: text, time, amount (a finite number >= 0).
LISTS = {
    "sessions": {"start": "time", "end": "time", "purpose": "text"},
    "costs": {"item": "text", "usd": "amount", "evidence": "text"},
    "interventions": {"at": "time", "who": "text", "what": "text", "minutes": "amount"},
    "friction": {"at": "time", "what": "text", "workaround": "text"},
    "blockers": {"what": "text", "since": "time", "waiting_on": "text"},
}
DELIVERABLES = ("build", "capture", "stills", "tests")


def parse(path: Path) -> dict | str:
    """The YAML front matter as a dict, or a message saying why there is none. OSError propagates."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].rstrip() != "---":
        return "no YAML front matter (the file must start with a '---' line)"
    end = next((index for index, line in enumerate(lines[1:], 1) if line.rstrip() == "---"), None)
    if end is None:
        return "the YAML front matter has no closing '---' line"
    try:
        front = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        return f"the YAML front matter does not parse: {error}"
    return front if isinstance(front, dict) else "the YAML front matter is not a mapping"


def timestamp(value: object) -> datetime | None:
    """A time-zone-aware datetime from YAML (which may already have parsed it), or None."""
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    return moment if moment.tzinfo is not None else None


def _is_amount(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _unknown(keys: object, known: object) -> list[object]:
    return sorted(set(keys) - set(known), key=str)


def _item_problems(field: str, index: int, item: object) -> list[str]:
    where = f"{field}[{index}]"
    if not isinstance(item, dict):
        return [f"{where}: must be a mapping"]
    found = []
    for key, kind in LISTS[field].items():
        value = item.get(key)
        if key not in item:
            found.append(f"{where}.{key}: missing")
        elif kind == "time" and timestamp(value) is None:
            found.append(f"{where}.{key}: {value!r} is not an ISO-8601 timestamp with a time zone")
        elif kind == "amount" and not _is_amount(value):
            found.append(f"{where}.{key}: {value!r} is not a number of 0 or more")
        elif kind == "text" and not (isinstance(value, str) and value.strip()):
            found.append(f"{where}.{key}: must be non-empty text")
    found += [f"{where}.{key}: unknown key" for key in _unknown(item, LISTS[field])]
    if field == "sessions" and not found and timestamp(item["end"]) < timestamp(item["start"]):
        found.append(f"{where}.end: {item['end']} is before start {item['start']}")
    return found


def problems(front: dict | str, lane_dir: str | None = None) -> list[str]:
    """Every way the front matter departs from docs/bakeoff/lane-log-format.md, one message each.

    `lane_dir` is the name of the directory the log is in (bakeoff/<lane>/LOG.md); the log must name that lane.
    """
    if isinstance(front, str):
        return [front]
    found = [f"{key}: missing" for key in FIELDS if key not in front]
    found += [f"{key}: unknown key" for key in _unknown(front, FIELDS)]
    for key, allowed in ENUMS.items():
        if key in front and not (isinstance(front[key], str) and front[key] in allowed):
            found.append(f"{key}: {front[key]!r} is not one of {', '.join(sorted(allowed))}")
    lane = front.get("lane")
    if "lane" in front and not (isinstance(lane, str) and lane.strip()):
        found.append("lane: must be non-empty text")
    elif lane_dir is not None and lane != lane_dir:
        found.append(f"lane: {lane!r}, but the log is in {lane_dir}/; set it to {lane_dir!r}")
    elif lane in LANES:
        for key, expected in zip(("direction", "engine"), LANES[lane], strict=True):
            if isinstance(front.get(key), str) and front[key] in ENUMS[key] and front[key] != expected:
                found.append(f"{key}: lane {lane} is {expected!r}, not {front[key]!r}")
    for field in LISTS:
        if field not in front:
            continue
        if not isinstance(front[field], list):
            found.append(f"{field}: must be a list")
            continue
        for index, item in enumerate(front[field]):
            found += _item_problems(field, index, item)
    deliverables = front.get("deliverables")
    if "deliverables" in front:
        if not isinstance(deliverables, dict) or set(deliverables) != set(DELIVERABLES):
            found.append(f"deliverables: must be a mapping with exactly {', '.join(DELIVERABLES)}")
        elif not isinstance(deliverables["stills"], list):
            found.append("deliverables.stills: must be a list")
    return found


def metrics(front: dict) -> dict:
    """Totals the gallery shows; call only on front matter without problems."""
    hours = sum((timestamp(s["end"]) - timestamp(s["start"])).total_seconds() for s in front["sessions"]) / 3600
    return {
        "agent_hours": hours,
        "usd": sum(cost["usd"] for cost in front["costs"]),
        "interventions": len(front["interventions"]),
        "intervention_minutes": sum(i["minutes"] for i in front["interventions"]),
        "friction": len(front["friction"]),
        "blockers": len(front["blockers"]),
        "status": front["status"],
    }

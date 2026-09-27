"""The bake-off decision rule (docs/bakeoff/judging.md, verbatim from the studio spec). THROWAWAY bake-off tooling.

D wins if Sami answers would_ship: yes for at least one D lane; otherwise A wins, and C instead only if Sami
prefers it. The engine is the higher-scored lane of the winning direction (sum of the three scores, among that
direction's lanes with yes); a tie goes to Godot. Control is scored for information and never decides.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from bakeoff import BakeoffError

SCHEMA = Path("docs/bakeoff/scores.schema.json")
D_LANES = {"g-d": "godot", "u-d": "unity"}


class ScoresError(Exception):
    """Scores that cannot be decided on; the message names the file and the problem."""


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict:
    keys = [key for key, _ in pairs]
    repeated = sorted({key for key in keys if keys.count(key) > 1})
    if repeated:
        raise ValueError(f"duplicate key(s) {', '.join(map(repr, repeated))}; the last copy would silently win")
    return dict(pairs)


def load_scores(path: Path, repo_root: Path) -> dict:
    """Read a scores file and validate it against the repository's docs/bakeoff/scores.schema.json."""
    try:
        scores = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
    except ValueError as error:  # json.JSONDecodeError is a ValueError, as is a duplicate key
        raise ScoresError(f"{path}: not valid JSON: {error}") from error
    schema_path = repo_root / SCHEMA
    if not schema_path.is_file():
        raise BakeoffError(f"no {SCHEMA} in {repo_root}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(scores),
                    key=lambda error: error.json_path)
    if errors:
        raise ScoresError(f"{path}:\n  " + "\n  ".join(f"{error.json_path}: {error.message}" for error in errors))
    return scores


def total(score: dict) -> int:
    return score["visual_quality"] + score["character_appeal"] + score["color_readability"]


def decide(scores: dict) -> dict:
    lanes = scores["lanes"]
    d_yes = {lane: score for lane, score in lanes.items() if lane in D_LANES and score["would_ship"]}
    if d_yes:
        lane = max(d_yes, key=lambda name: (total(d_yes[name]), name == "g-d"))  # a tie goes to Godot
        return {"direction": "D", "engine": D_LANES[lane], "winning_lane": lane,
                "reason": f"would_ship=yes for {sorted(d_yes)}; highest total {total(d_yes[lane])} ({lane})"}
    if scores.get("prefers_c_over_a") is True:
        return {"direction": "C", "engine": "godot", "winning_lane": "g-c", "reason": "no D lane got yes; Sami prefers C over A"}
    recorded = "" if scores.get("prefers_c_over_a") is False else " (prefers_c_over_a was not recorded)"
    return {"direction": "A", "engine": "godot", "winning_lane": "g-a", "reason": f"no D lane got yes; A is the default{recorded}"}

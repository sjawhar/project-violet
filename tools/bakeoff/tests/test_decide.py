"""The decision rule from the studio spec (docs/bakeoff/judging.md). THROWAWAY bake-off tooling."""

import json
from pathlib import Path

import pytest

from bakeoff.cli import main
from bakeoff.decide import ScoresError, decide, load_scores

REPO = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("fixture", "direction", "engine", "winning_lane"),
    [
        ("scores-u-d-only.json", "D", "unity", "u-d"),  # only u-d got yes; g-d's higher total doesn't count
        ("scores-d-tie.json", "D", "godot", "g-d"),  # both yes, totals 11 and 11: a tie goes to Godot
        ("scores-u-d-higher.json", "D", "unity", "u-d"),  # both yes, u-d 13 beats g-d 9
        ("scores-prefers-c.json", "C", "godot", "g-c"),  # no D yes, Sami prefers C
        ("scores-default-a.json", "A", "godot", "g-a"),  # no D yes, prefers_c_over_a false
        ("scores-a-missing-preference.json", "A", "godot", "g-a"),  # no D yes, preference not given
    ],
)
def test_applies_the_decision_rule(fixture: str, direction: str, engine: str, winning_lane: str):
    result = decide(load_scores(FIXTURES / fixture, REPO))

    assert (result["direction"], result["engine"], result["winning_lane"]) == (direction, engine, winning_lane)


def _scores_file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "scores.json"
    path.write_text(text)
    return path


def test_a_control_lane_yes_never_decides(tmp_path: Path):
    scores = json.loads((FIXTURES / "scores-default-a.json").read_text())
    scores["lanes"]["control"] = {"visual_quality": 5, "character_appeal": 5, "color_readability": 5, "would_ship": True, "notes": ""}

    assert decide(load_scores(_scores_file(tmp_path, json.dumps(scores)), REPO))["direction"] == "A"


@pytest.mark.parametrize(
    ("change", "named"),
    [
        (lambda s: s["lanes"]["g-d"].update(visual_quality=6), "visual_quality"),
        (lambda s: s["lanes"].pop("u-d"), "u-d"),  # an untranscribed D lane could flip the decision
        (lambda s: s.update(scored_at="yesterday"), "scored_at"),
        (lambda s: s.update(source="see Slack"), "source"),
        (lambda s: s["lanes"].update({"g-b": s["lanes"]["g-a"]}), "g-b"),
    ],
)
def test_refuses_scores_outside_the_schema(tmp_path: Path, change, named: str):
    scores = json.loads((FIXTURES / "scores-d-tie.json").read_text())
    change(scores)

    with pytest.raises(ScoresError, match=named):
        load_scores(_scores_file(tmp_path, json.dumps(scores)), REPO)


def test_a_lane_sami_could_not_score_has_null_scores_but_only_as_a_no(tmp_path: Path):
    scores = json.loads((FIXTURES / "scores-default-a.json").read_text())
    scores["lanes"]["u-d"] = {"visual_quality": None, "character_appeal": None, "color_readability": None, "would_ship": False, "notes": "blocked"}
    assert decide(load_scores(_scores_file(tmp_path, json.dumps(scores)), REPO))["direction"] == "A"

    scores["lanes"]["u-d"]["would_ship"] = True
    with pytest.raises(ScoresError, match="visual_quality"):
        load_scores(_scores_file(tmp_path, json.dumps(scores)), REPO)


def test_the_reason_says_when_the_c_preference_was_not_recorded():
    missing = decide(load_scores(FIXTURES / "scores-a-missing-preference.json", REPO))
    answered = decide(load_scores(FIXTURES / "scores-default-a.json", REPO))

    assert "prefers_c_over_a" in missing["reason"] and "prefers_c_over_a" not in answered["reason"]


def test_refuses_a_lane_transcribed_twice(tmp_path: Path):
    text = (FIXTURES / "scores-default-a.json").read_text()
    lane = '"u-d": {"visual_quality": 5, "character_appeal": 5, "color_readability": 5, "would_ship": true, "notes": ""},'
    twice = text.replace('"lanes": {', '"lanes": {' + lane, 1)
    assert twice != text

    with pytest.raises(ScoresError, match="duplicate"):
        load_scores(_scores_file(tmp_path, twice), REPO)


def test_cli_prints_the_decision_as_json(capsys: pytest.CaptureFixture[str]):
    assert main(["decide", str(FIXTURES / "scores-d-tie.json")]) == 0

    result = json.loads(capsys.readouterr().out)
    assert (result["direction"], result["engine"], result["winning_lane"]) == ("D", "godot", "g-d")


def test_cli_exits_1_on_invalid_scores_and_names_the_file(capsys: pytest.CaptureFixture[str]):
    assert main(["decide", str(FIXTURES / "scores-out-of-range.json")]) == 1
    assert "scores-out-of-range.json" in capsys.readouterr().err


def test_cli_exits_2_on_a_missing_scores_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["decide", str(tmp_path / "scores.json")]) == 2
    assert "bakeoff: error:" in capsys.readouterr().err


def test_cli_exits_2_outside_the_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.chdir(tmp_path)

    assert main(["decide", str(FIXTURES / "scores-d-tie.json")]) == 2
    assert "scores.schema.json" in capsys.readouterr().err

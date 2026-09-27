"""Lane log front matter (docs/bakeoff/lane-log-format.md). THROWAWAY bake-off tooling."""

import re
from pathlib import Path

import pytest

from bakeoff.cli import main
from bakeoff.log import metrics, parse, problems

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "docs/bakeoff/lane-log-template.md"

LOG = """---
lane: g-a
direction: A
engine: godot
machine: oryx
status: delivered
sessions:
  - {start: "2026-09-28T09:00:00Z", end: "2026-09-28T10:30:00Z", purpose: greybox}
  - {start: "2026-09-29T14:00:00+00:00", end: "2026-09-29T15:30:00+00:00", purpose: art pass}
costs:
  - {item: gen image batch, usd: 1.25, evidence: "https://example.invalid/receipt/1"}
  - {item: gen image retry, usd: 0.75, evidence: "https://example.invalid/receipt/2"}
interventions:
  - {at: "2026-09-28T09:40:00Z", who: sjawhar, what: approved the greybox, minutes: 5}
friction:
  - {at: "2026-09-28T09:20:00Z", what: import reordering, workaround: explicit import step}
blockers: []
deliverables: {build: out/g-a/violet-g-a.x86_64, capture: bakeoff/g-a/capture/capture.mp4, stills: [bakeoff/g-a/capture/still-05.png], tests: bakeoff/g-a/reports/replay.json}
---

Notes go here.
"""
SESSIONS = (
    "sessions:\n"
    '  - {start: "2026-09-28T09:00:00Z", end: "2026-09-28T10:30:00Z", purpose: greybox}\n'
    '  - {start: "2026-09-29T14:00:00+00:00", end: "2026-09-29T15:30:00+00:00", purpose: art pass}\n'
)


def _write(tmp_path: Path, text: str, lane: str = "g-a") -> Path:
    path = tmp_path / "bakeoff" / lane / "LOG.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_the_template_is_valid():
    assert problems(parse(TEMPLATE)) == []


def _filled_in(template: str) -> str:
    """The template with each commented example put in place, as a lane fills it in."""
    text = re.sub(r"^(\w+): \[\]\n# - (.*)$", r"\1:\n  - \2", template, flags=re.M)
    return re.sub(r"^deliverables: .*\n# e\.g\. (.*)$", r"deliverables: \1", text, flags=re.M)


def test_the_template_s_examples_are_valid_once_filled_in(tmp_path: Path):
    text = _filled_in(TEMPLATE.read_text())
    assert "# - " not in text and "# e.g." not in text

    assert problems(parse(_write(tmp_path, text)), lane_dir="g-a") == []


def test_a_complete_log_is_valid(tmp_path: Path):
    assert problems(parse(_write(tmp_path, LOG)), lane_dir="g-a") == []


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        (SESSIONS, "", "sessions: missing"),
        (SESSIONS, "sessions: 5\n", "sessions: must be a list"),
        ('start: "2026-09-28T09:00:00Z"', 'start: "Monday morning"', "sessions[0].start:"),
        ('start: "2026-09-28T09:00:00Z"', 'start: "2026-09-28T09:00:00"', "sessions[0].start:"),  # no time zone
        ('end: "2026-09-28T10:30:00Z"', 'end: "2026-09-28T08:30:00Z"', "sessions[0].end:"),
        ("status: delivered", "status: done", "status:"),
        ("direction: A", "direction: B", "direction: 'B' is not one of"),
        ("direction: A", "direction: [A]", "direction:"),
        ("engine: godot", "engine: {x: 1}", "engine:"),
        ("engine: godot", "engine: unity", "engine: lane g-a is"),  # g-a is the Godot lane
        ("direction: A", "direction: D", "direction: lane g-a is"),  # g-a is direction A
        ("machine: oryx", "machine: laptop", "machine:"),
        ("lane: g-a", 'lane: ""', "lane: '' is not one of"),
        ("lane: g-a", "lane: ga", "lane: 'ga' is not one of"),
        ("usd: 1.25", "usd: lots", "costs[0].usd:"),
        ("usd: 1.25", "usd: -3", "costs[0].usd:"),
        ("usd: 1.25", "usd: .inf", "costs[0].usd:"),
        ("minutes: 5", "minutes: soon", "interventions[0].minutes:"),
        ("minutes: 5", "minutes: true", "interventions[0].minutes:"),
        (', evidence: "https://example.invalid/receipt/1"', "", "costs[0].evidence: missing"),
        ("purpose: greybox}", "purpose: greybox, mood: good}", "sessions[0].mood: unknown key"),
        ("blockers: []", "blockers: []\nnotes: none", "notes: unknown key"),
        ("tests: bakeoff/g-a/reports/replay.json}", "tests: bakeoff/g-a/reports/replay.json, log: x}", "deliverables:"),
        ("stills: [bakeoff/g-a/capture/still-05.png]", "stills: bakeoff/g-a/capture/still-05.png", "deliverables.stills:"),
        (", tests: bakeoff/g-a/reports/replay.json}", "}", "deliverables:"),
        ("what: import reordering, ", "what: '', ", "friction[0].what:"),
    ],
)
def test_names_each_problem_once(tmp_path: Path, old: str, new: str, field: str):
    assert old in LOG
    found = problems(parse(_write(tmp_path, LOG.replace(old, new, 1))), lane_dir="g-a")

    assert len(found) == 1, found
    assert found[0].startswith(field), found


def test_a_log_names_the_lane_directory_it_is_in(tmp_path: Path):
    found = problems(parse(_write(tmp_path, LOG, lane="g-d")), lane_dir="g-d")

    assert len(found) == 1 and found[0].startswith("lane:"), found


def test_unknown_keys_of_mixed_types_are_listed_not_crashed_on(tmp_path: Path):
    found = problems(parse(_write(tmp_path, LOG.replace("blockers: []", "blockers: []\n1: oops\nextra: x"))))

    assert sorted(found) == ["1: unknown key", "extra: unknown key"]


@pytest.mark.parametrize("encode", [lambda text: text.replace("\n", "\r\n"), lambda text: "\ufeff" + text], ids=["crlf", "bom"])
def test_windows_line_endings_and_a_byte_order_mark_parse(tmp_path: Path, encode):
    path = tmp_path / "LOG.md"
    path.write_bytes(encode(LOG).encode("utf-8"))

    assert problems(parse(path)) == []


def test_metrics_sum_sessions_costs_and_interventions(tmp_path: Path):
    result = metrics(parse(_write(tmp_path, LOG)))

    assert result["agent_hours"] == 3.0
    assert result["usd"] == 2.0
    assert (result["interventions"], result["intervention_minutes"]) == (1, 5)
    assert (result["friction"], result["blockers"], result["status"]) == (1, 0, "delivered")


@pytest.mark.parametrize(("text", "named"), [("# just notes\n", "no YAML front matter"), ("---\nlane: g-a\n", "no closing")])
def test_a_file_without_front_matter_is_one_problem(tmp_path: Path, text: str, named: str):
    found = problems(parse(_write(tmp_path, text)))

    assert len(found) == 1 and named in found[0]


def test_log_check_names_the_file_and_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    bad = _write(tmp_path, LOG.replace("status: delivered", "status: done"))

    assert main(["log-check", str(TEMPLATE), str(bad)]) == 1
    captured = capsys.readouterr()
    assert f"{bad}: status:" in captured.err
    assert captured.out == "bakeoff log-check: 1 problem(s)\n"  # the template adds none


def test_log_check_holds_a_lane_log_to_its_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    copied = _write(tmp_path, LOG, lane="u-d")  # g-a's log copied into u-d without editing it

    assert main(["log-check", str(copied)]) == 1
    assert f"{copied}: lane:" in capsys.readouterr().err


def test_log_check_refuses_a_lane_outside_the_five(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    log = _write(tmp_path, LOG.replace("lane: g-a", "lane: ga"), lane="ga")  # CI on bakeoff/ga would otherwise go green

    assert main(["log-check", str(log)]) == 1
    assert f"{log}: lane:" in capsys.readouterr().err


def test_log_check_works_from_inside_the_lane_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.chdir(_write(tmp_path, LOG).parent)

    assert main(["log-check", "LOG.md"]) == 0, capsys.readouterr().err


def test_log_check_on_a_missing_file_is_a_usage_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["log-check", str(tmp_path / "bakeoff/g-a/LOG.md")]) == 2
    assert "bakeoff: error:" in capsys.readouterr().err

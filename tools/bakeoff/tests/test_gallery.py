"""The judging gallery and results table. THROWAWAY bake-off tooling."""

import json
import re
import shutil
from pathlib import Path

import pytest

from bakeoff import BakeoffError
from bakeoff.cli import main
from bakeoff.gallery import build, lane_results, results_markdown
from bakeoff.log import LANES

REPO = Path(__file__).resolve().parents[3]
CHECKS = ("build", "replay", "no-dash-fails", "no-double-jump-fails", "tags", "mutation-fails")

LOG = """---
lane: {lane}
direction: {direction}
engine: {engine}
machine: oryx
status: {status}
sessions:
  - {{start: "2026-09-28T09:00:00Z", end: "{end}", purpose: build}}
costs:
  - {{item: images, usd: 1.5, evidence: receipt}}
interventions:
  - {{at: "2026-09-28T10:00:00Z", who: sjawhar, what: checked the greybox, minutes: 4}}
friction: []
blockers: {blockers}
deliverables: {{build: null, capture: null, stills: [], tests: null}}
---
"""

# What each Godot lane's ci.sh writes (plan Task 7 Step 16): the runner's verdict is its last stdout line, and the
# tag validator's `2>&1` files can end with Godot's shutdown warnings.
GODOT_OK = {
    "replay.json": 'booting\n{"tick": 10}\n{"ok": true, "goal_tick": 1400}\n',
    "replay-no-dash.json": '{"ok": false, "reason": "goal not reached"}\n',
    "replay-no-double-jump.json": '{"tick": 700}\n{"ok": false, "reason": "goal not reached"}\n',
    "tags.txt": "checking 14 cells\ntag-check: 0 problem(s)\nWARNING: 2 ObjectDB instances were leaked at exit\n",
    "tags-mutated.txt": "no tagged body at (33, 4)\ntag-check: 1 problem(s)\n",
    "build.txt": "-rwxr-xr-x 1 agent agent 71M out/g-a/violet-g-a.x86_64\n",
}
UNITY_TESTS = ("Level01ReplayReachesTheGoal", "Level01ReplayFailsWithoutDash",
               "TagValidatorPassesOnTheBuiltLevel", "TagValidatorFailsWhenATagIsRemoved")


def _nunit(results: dict[str, str]) -> str:
    """A PlayMode NUnit3 report with one test-case per entry and the run's totals computed from them."""
    cases = "\n".join(f'    <test-case name="{name}" fullname="Bakeoff.{name}" result="{result}" />' for name, result in results.items())
    failed = sum(result == "Failed" for result in results.values())
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            f'<test-run id="2" testcasecount="{len(results)}" result="{"Failed" if failed else "Passed"}" total="{len(results)}" '
            f'passed="{len(results) - failed}" failed="{failed}" skipped="0">\n'
            f'  <test-suite type="Assembly" name="Bakeoff.Tests.PlayMode.dll">\n{cases}\n  </test-suite>\n</test-run>\n')


UNITY_OK = {"playmode.xml": _nunit(dict.fromkeys(UNITY_TESTS, "Passed")), "build.log": "Building player...\nBuild succeeded\n"}
RENDER = {"clips": ["idle", "run", "jump", "fall", "double_jump", "dash", "land"], "frames": 2250, "device": "CPU", "seconds": 75}
CONTROL_OK = {"render.json": json.dumps(RENDER, indent=2)}  # render_reel.py may pretty-print it
LANE_SETUP = {  # lane -> direction, engine, reports
    "g-a": ("A", "godot", GODOT_OK),
    "g-d": ("D", "godot", {**GODOT_OK, "replay.json": '{"ok": false, "reason": "hazard at tick 400"}\n'}),
    "u-d": ("D", "unity", UNITY_OK),
    "control": ("control", "blender", CONTROL_OK),
}


def _lane(root: Path, lane: str, *, status: str = "delivered", blockers: str = "[]", end: str = "2026-09-28T11:00:00Z",
          reports: dict[str, str] | None = None, capture: bool = True) -> Path:
    direction, engine = LANES[lane]
    lane_dir = root / "bakeoff" / lane
    (lane_dir / "reports").mkdir(parents=True)
    (lane_dir / "LOG.md").write_text(LOG.format(lane=lane, direction=direction, engine=engine, status=status, blockers=blockers, end=end))
    for name, text in (reports or {}).items():
        (lane_dir / "reports" / name).write_text(text)
    if capture:
        (lane_dir / "capture").mkdir()
        for name in ("capture.mp4", "still-05.png", "still-20.png"):
            (lane_dir / "capture" / name).write_bytes(b"media")
    return lane_dir


def _score(total_parts: tuple[int, int, int], would_ship: bool, notes: str = "") -> dict:
    return dict(zip(("visual_quality", "character_appeal", "color_readability"), total_parts, strict=True), would_ship=would_ship, notes=notes)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "docs/bakeoff").mkdir(parents=True)
    shutil.copyfile(REPO / "docs/bakeoff/scores.schema.json", tmp_path / "docs/bakeoff/scores.schema.json")
    for lane, (_, _, reports) in LANE_SETUP.items():
        _lane(tmp_path, lane, reports=reports)
    _lane(tmp_path, "g-c", status="blocked", capture=False,
          blockers='[{what: Recraft account, since: "2026-09-28T09:00:00Z", waiting_on: sjawhar}]')
    _write_scores(tmp_path, {"g-a": _score((4, 3, 5), True, "warm"), "g-d": _score((2, 2, 2), False), "u-d": _score((3, 3, 3), False)})
    return tmp_path


def _write_scores(root: Path, lanes: dict) -> None:
    (root / "docs/bakeoff/scores.json").write_text(json.dumps({
        "scored_by": "sjawhar", "scored_at": "2026-10-03T18:00:00Z", "source": "https://example.invalid/comment",
        "prefers_c_over_a": None, "lanes": lanes,
    }))


class FakePreview:
    """Stands in for `preview build`: records what it was asked to render and writes a gallery with a manifest."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Path]]] = []

    def __call__(self, pr: str, paths: list[Path], repo_root: Path) -> Path:
        self.calls.append((pr, paths))
        out = repo_root / "out/review" / f"pr-{pr}"
        out.mkdir(parents=True)
        items = []
        for index, path in enumerate(paths, 1):
            if path.suffix == ".mp4":
                items.append({"name": path.name, "kind": "animation", "media": {"video": f"items/{index:02d}-capture.mp4", "gif": f"items/{index:02d}-capture.gif", "poster": f"items/{index:02d}-capture.poster.webp"}})
            else:
                items.append({"name": path.name, "kind": "image", "media": {"image": f"items/{index:02d}-{path.stem}.webp"}})
        (out / "preview.json").write_text(json.dumps({"pr": pr, "contact_sheet": None, "items": items}))
        (out / "index.html").write_text("<p>preview</p>")
        return out


RUNS = {"g-a": 101, "g-d": 102, "u-d": 103, "control": 105}  # g-c has never run CI


def _runs(lane: str) -> str | None:
    return f"https://github.com/sjawhar/project-violet/actions/runs/{RUNS[lane]}" if lane in RUNS else None


def _row(html: str, lane: str) -> str:
    """The lane's card."""
    card = re.search(rf'<section class="lane" id="lane-{lane}">(.*?)</section>', html, re.S)
    assert card, f"no card for {lane}"
    return card.group(1)


def _cells(html: str, lane: str) -> dict[str, str]:
    """The row's cells as text, with <br> kept as a newline."""
    return {name: re.sub(r"<[^>]+>", "", value.replace("<br>", "\n")).strip()
            for _, name, value in re.findall(r'<(\w+)\b[^>]*\bdata-col="([^"]+)"[^>]*>(.*?)</\1>', _row(html, lane), re.S)}


def _gallery(repo: Path) -> str:
    out = build("40", repo / "bakeoff", repo, preview=FakePreview(), latest_run=_runs)
    return (out / "bakeoff.html").read_text()


def _checks(repo: Path, lane: str) -> tuple[dict[str, bool | None], list[str]]:
    [found] = [result for result in lane_results(repo / "bakeoff") if result.name == lane]
    return found.checks, found.problems


def test_the_gallery_reports_each_lane_s_checks_metrics_and_scores(repo: Path):
    html = _gallery(repo)

    g_a = _cells(html, "g-a")
    assert {k: g_a[k] for k in CHECKS} == dict.fromkeys(CHECKS, "✓")
    assert (g_a["agent-hours"], g_a["usd"], g_a["interventions"], g_a["friction"]) == ("2.0", "1.50", "1 / 4 min", "0")
    assert (g_a["visual_quality"], g_a["character_appeal"], g_a["color_readability"], g_a["would_ship"]) == ("4", "3", "5", "yes")
    g_d = _cells(html, "g-d")
    assert {k: g_d[k] for k in CHECKS} == {**dict.fromkeys(CHECKS, "✓"), "replay": "✗"}
    assert g_d["would_ship"] == "no"
    u_d = _cells(html, "u-d")
    assert {k: u_d[k] for k in CHECKS} == {**dict.fromkeys(CHECKS, "✓"), "no-double-jump-fails": "n/a"}
    control = _cells(html, "control")
    assert {k: control[k] for k in CHECKS} == {**dict.fromkeys(CHECKS, "n/a"), "build": "✓"}  # a reel, no playable build
    g_c = _cells(html, "g-c")
    assert (g_c["status"], g_c["blockers"], g_c["visual_quality"], g_c["capture"]) == ("blocked", "Recraft account", "unscored", "no capture yet")
    assert (g_c["direction"], g_c["engine"]) == ("C", "godot")


def test_a_lane_sami_could_not_score_shows_not_scored(repo: Path):
    _write_scores(repo, {"g-a": _score((4, 3, 5), True), "g-d": _score((2, 2, 2), False),
                         "u-d": {"visual_quality": None, "character_appeal": None, "color_readability": None, "would_ship": False, "notes": "blocked"}})

    u_d = _cells(_gallery(repo), "u-d")

    assert (u_d["visual_quality"], u_d["would_ship"]) == ("not scored", "no")


def test_each_lane_row_links_its_own_branch_and_ci_run(repo: Path):
    html = _gallery(repo)

    for lane, run in RUNS.items():
        row = _row(html, lane)
        assert f'href="https://github.com/sjawhar/project-violet/tree/bakeoff/{lane}"' in row
        assert f'href="https://github.com/sjawhar/project-violet/actions/runs/{run}"' in row
    assert "(no CI run)" in _row(html, "g-c")


def test_the_gallery_uses_preview_s_media_for_every_capture_and_still(repo: Path):
    preview = FakePreview()

    out = build("40", repo / "bakeoff", repo, preview=preview, latest_run=_runs)

    [(pr, paths)] = preview.calls
    assert pr == "40"
    assert [p.relative_to(repo).as_posix() for p in paths] == [  # lane-named copies, so preview's page names the lane
        f"out/lanes/{lane}/{lane}-{name}" for lane in ("g-a", "g-d", "u-d", "control") for name in ("capture.mp4", "still-05.png", "still-20.png")]
    assert all(path.read_bytes() == b"media" for path in paths)
    g_d = _row((out / "bakeoff.html").read_text(), "g-d")
    assert 'src="items/04-capture.mp4"' in g_d and 'poster="items/04-capture.poster.webp"' in g_d  # g-d's capture, the fourth path
    assert 'src="items/05-g-d-still-05.webp"' in g_d
    assert (out / "index.html").exists()  # preview's own page stays beside it


@pytest.mark.parametrize(
    ("report", "text", "check", "broken"),  # broken: the report is not a result at all, so the notes name it
    [
        ("replay.json", '{"ok": false, "reason": "hazard"}\n', "replay", False),
        ("replay.json", '{"ok": 1}\n', "replay", False),  # the runner's verdict is a JSON boolean
        ("replay.json", None, "replay", True),
        ("replay-no-dash.json", '{"ok": true}\n', "no-dash-fails", False),
        ("replay-no-dash.json", None, "no-dash-fails", True),
        ("replay-no-double-jump.json", '{"ok": true}\n', "no-double-jump-fails", False),
        ("replay-no-double-jump.json", "Segmentation fault\n", "no-double-jump-fails", True),
        ("tags.txt", "tag-check: 2 problem(s)\n", "tags", False),
        ("tags.txt", "SCRIPT ERROR: Parse Error\n", "tags", True),
        ("tags-mutated.txt", "tag-check: 0 problem(s)\n", "mutation-fails", False),
        ("tags.txt", "tag-check: 0 problem(s)\nretrying with the built scene\ntag-check: 3 problem(s)\n", "tags", False),  # the last count wins
        ("build.txt", "", "build", True),
        ("build.txt", None, "build", True),
    ],
)
def test_a_godot_report_that_fails_fails_only_its_own_check(repo: Path, report: str, text: str | None, check: str, broken: bool):
    path = repo / "bakeoff/g-a/reports" / report
    if text is None:
        path.unlink()
    else:
        path.write_text(text)

    checks, found = _checks(repo, "g-a")

    assert checks == {**dict.fromkeys(CHECKS, True), check: False}
    if broken:
        assert any(problem.startswith(f"reports/{report}") for problem in found), found
    else:
        assert found == []


@pytest.mark.parametrize("missing", UNITY_TESTS)
def test_a_unity_lane_needs_each_required_test_to_pass(repo: Path, missing: str):
    (repo / "bakeoff/u-d/reports/playmode.xml").write_text(_nunit({test: "Passed" for test in UNITY_TESTS if test != missing}))

    checks, found = _checks(repo, "u-d")

    assert [name for name, ok in checks.items() if ok is False] == [
        {"Level01ReplayReachesTheGoal": "replay", "Level01ReplayFailsWithoutDash": "no-dash-fails",
         "TagValidatorPassesOnTheBuiltLevel": "tags", "TagValidatorFailsWhenATagIsRemoved": "mutation-fails"}[missing]]
    assert any(missing in problem for problem in found)


def test_a_skipped_required_unity_test_has_not_passed(repo: Path):
    (repo / "bakeoff/u-d/reports/playmode.xml").write_text(_nunit({**dict.fromkeys(UNITY_TESTS, "Passed"), "TagValidatorPassesOnTheBuiltLevel": "Skipped"}))

    checks, found = _checks(repo, "u-d")

    assert checks["tags"] is False and checks["replay"] is True
    assert any("TagValidatorPassesOnTheBuiltLevel" in problem for problem in found)


def test_a_truncated_playmode_report_is_named_not_crashed_on(repo: Path):
    (repo / "bakeoff/u-d/reports/playmode.xml").write_text(UNITY_OK["playmode.xml"][:120])

    checks, found = _checks(repo, "u-d")

    assert [checks[name] for name in ("replay", "no-dash-fails", "tags", "mutation-fails")] == [False] * 4
    assert any(problem.startswith("reports/playmode.xml: does not parse") for problem in found)


def test_a_unity_run_with_any_failed_test_fails_every_test_check(repo: Path):
    (repo / "bakeoff/u-d/reports/playmode.xml").write_text(_nunit({**dict.fromkeys(UNITY_TESTS, "Passed"), "GreyboxLoads": "Failed"}))

    checks, found = _checks(repo, "u-d")

    assert checks == {"build": True, "no-double-jump-fails": None, "replay": False, "no-dash-fails": False, "tags": False, "mutation-fails": False}
    assert any("GreyboxLoads" in problem for problem in found)


@pytest.mark.parametrize("build_log", ["Building player...\nBuild failed: 3 errors\n", None])
def test_a_unity_lane_needs_a_successful_build_log(repo: Path, build_log: str | None):
    path = repo / "bakeoff/u-d/reports/build.log"
    if build_log is None:
        path.unlink()
    else:
        path.write_text(build_log)

    checks, found = _checks(repo, "u-d")

    assert checks["build"] is False and checks["replay"] is True
    assert any(problem.startswith("reports/build.log") for problem in found)


def test_a_control_reel_may_list_its_clips_as_reel_json_objects(repo: Path):
    clips = [{"name": name, "glb": f"anims/{name}.glb", "seconds": 8} for name in RENDER["clips"]]
    (repo / "bakeoff/control/reports/render.json").write_text(json.dumps({**RENDER, "clips": clips}))

    assert _checks(repo, "control") == ({**dict.fromkeys(CHECKS, None), "build": True}, [])


def test_the_control_card_says_its_build_is_the_reel(repo: Path):
    assert "no playable build by design" in _cells(_gallery(repo), "control")["notes"]


@pytest.mark.parametrize(
    ("change", "named"),
    [
        ({"clips": ["idle", "run", "jump", "fall", "dash", "land"]}, "double_jump"),
        ({"seconds": 45}, "seconds"),
        ({"frames": 0}, "frames"),
        ({"frames": True}, "frames"),
        ({"seconds": 120}, "seconds"),
        ({"clips": [["idle"], {"name": ["run"]}]}, "idle"),  # malformed clip entries are missing clips, not a crash
        ("{\"clips\": [\"idle\"", "not valid JSON"),  # truncated
    ],
)
def test_a_control_reel_that_misses_its_contract_fails(repo: Path, change: dict | str, named: str):
    (repo / "bakeoff/control/reports/render.json").write_text(change if isinstance(change, str) else json.dumps({**RENDER, **change}))

    checks, found = _checks(repo, "control")

    assert checks["build"] is False
    assert any(named in problem for problem in found)


def test_lane_text_is_escaped_in_the_page(repo: Path):
    shutil.rmtree(repo / "bakeoff/g-c")
    _lane(repo, "g-c", status="blocked", capture=False,
          blockers='[{what: "<b>Spine</b> & <script>alert(1)</script>", since: "2026-09-28T09:00:00Z", waiting_on: sjawhar}]')

    html = _gallery(repo)

    assert "<script>" not in html and "<b>Spine" not in html
    assert "&lt;b&gt;Spine&lt;/b&gt; &amp; &lt;script&gt;" in _row(html, "g-c")


def test_a_lane_with_an_invalid_log_shows_its_problems_instead_of_numbers(repo: Path):
    shutil.rmtree(repo / "bakeoff/g-d")
    _lane(repo, "g-d", end="2026-09-28T08:00:00Z", reports=LANE_SETUP["g-d"][2])

    g_d = _cells(_gallery(repo), "g-d")

    assert (g_d["agent-hours"], g_d["usd"]) == ("?", "?")
    assert "LOG.md: sessions[0].end" in g_d["notes"]


def test_a_log_that_does_not_parse_is_a_note(repo: Path):
    (repo / "bakeoff/g-d/LOG.md").write_text("---\nlane: g-d\nsessions: [unclosed\n---\n")

    g_d = _cells(_gallery(repo), "g-d")

    assert g_d["agent-hours"] == "?" and "LOG.md: the YAML front matter does not parse" in g_d["notes"]


def test_a_lane_without_a_log_yet_keeps_its_row_and_report_problems(repo: Path):
    (repo / "bakeoff/u-d/LOG.md").unlink()
    (repo / "bakeoff/u-d/reports/build.log").unlink()

    card = _row(_gallery(repo), "u-d")

    assert "no u-d/LOG.md yet<br>reports/build.log: missing" in card  # one line each on the page


def test_several_blockers_are_listed_in_one_cell(repo: Path):
    shutil.rmtree(repo / "bakeoff/g-c")
    _lane(repo, "g-c", status="blocked", capture=False, blockers=(
        '[{what: Recraft account, since: "2026-09-28T09:00:00Z", waiting_on: sjawhar},'
        ' {what: SVG export, since: "2026-09-29T09:00:00Z", waiting_on: Task 6}]'))

    html = _gallery(repo)

    assert _cells(html, "g-c")["blockers"] == "Recraft account; SVG export"
    assert _cells(html, "g-a")["blockers"] == "none"


def test_a_log_for_another_lane_is_a_problem(repo: Path):
    log = repo / "bakeoff/u-d/LOG.md"
    log.write_text(log.read_text().replace("lane: u-d", "lane: g-a"))

    _, found = _checks(repo, "u-d")

    assert any(problem.startswith("LOG.md: lane:") for problem in found), found


def test_a_lane_that_has_not_started_still_gets_a_row(repo: Path):
    shutil.rmtree(repo / "bakeoff/g-c")

    g_c = _cells(_gallery(repo), "g-c")

    assert g_c["notes"] == "no g-c/ directory yet"
    assert {g_c[k] for k in CHECKS} == {"✗"}


def test_refuses_a_lanes_directory_that_does_not_exist(repo: Path):
    with pytest.raises(BakeoffError, match="bakeoff-typo"):
        results_markdown("40", repo / "bakeoff-typo", repo)


def test_refuses_to_build_without_any_capture(repo: Path):
    for capture in (repo / "bakeoff").glob("*/capture"):
        shutil.rmtree(capture)

    with pytest.raises(BakeoffError, match="capture"):
        build("40", repo / "bakeoff", repo, preview=FakePreview(), latest_run=_runs)


def _markdown_rows(text: str) -> dict[str, dict[str, str]]:
    table = [line for line in text.splitlines() if line.startswith("|")]
    header = [cell.strip() for cell in table[0].strip("|").split(" | ")]
    rows = {}
    for line in table[2:]:
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        assert len(cells) == len(header), line
        rows[cells[0]] = dict(zip(header, cells, strict=True))
    return rows


def test_results_markdown_is_the_gallery_table_without_media(repo: Path):
    shutil.rmtree(repo / "bakeoff/g-c")
    _lane(repo, "g-c", status="blocked", capture=False,
          blockers='[{what: "Recraft | <b>account</b>\\nsecond line", since: "2026-09-28T09:00:00Z", waiting_on: sjawhar}]')

    text = results_markdown("40", repo / "bakeoff", repo)

    assert "https://sjawhar.github.io/project-violet/review/pr-40/bakeoff.html" in text
    rows = _markdown_rows(text)
    assert list(rows) == ["g-a", "g-d", "u-d", "g-c", "control"]
    assert (rows["g-d"]["replay"], rows["g-d"]["tags"], rows["g-d"]["machine"], rows["g-d"]["friction"]) == ("✗", "✓", "oryx", "0")
    assert (rows["g-a"]["would_ship"], rows["g-a"]["notes"]) == ("yes", "warm")
    assert rows["g-c"]["blockers"] == "Recraft \\| &lt;b&gt;account&lt;/b&gt;<br>second line"
    assert rows["g-c"]["notes"].split("<br>")[:2] == ["reports/replay.json: missing", "reports/replay-no-dash.json: missing"]


def test_results_md_from_a_subdirectory_reads_the_repository_s_lanes(repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.chdir(repo / "docs")

    assert main(["results-md", "--pr", "0-smoke"]) == 0

    out = capsys.readouterr().out
    assert "review/pr-0-smoke/bakeoff.html" in out
    assert list(_markdown_rows(out)) == ["g-a", "g-d", "u-d", "g-c", "control"]


def test_results_md_reads_the_lanes_directory_it_is_given(repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    shutil.copytree(repo / "bakeoff", repo / "elsewhere")
    shutil.rmtree(repo / "bakeoff")
    monkeypatch.chdir(repo)

    assert main(["results-md", "--pr", "40", "--lanes-dir", "elsewhere"]) == 0
    assert _markdown_rows(capsys.readouterr().out)["g-a"]["replay"] == "✓"


@pytest.mark.parametrize("pr", ["x y", "12/../13", "-3"])
def test_results_md_refuses_a_pr_argument_preview_would_refuse(repo: Path, monkeypatch: pytest.MonkeyPatch, pr: str):
    monkeypatch.chdir(repo)

    with pytest.raises(SystemExit) as exit_info:
        main(["results-md", "--pr", pr])
    assert exit_info.value.code == 2

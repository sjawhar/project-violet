"""The judging gallery (bakeoff.html) and results table for the bake-off lanes. THROWAWAY bake-off tooling.

Every lane in log.LANES gets a row, read from `<lanes_dir>/<lane>/`: LOG.md, reports/ written by the lane's ci.sh,
and capture/. A lane that has not written something yet shows it as a problem in its notes, never as a missing row.
The gallery page sits beside `preview build`'s index.html in out/review/pr-<n>/ and shows preview's copies of the
captures and stills, so `preview publish` puts both pages on GitHub Pages.
"""

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from pathlib import Path

from bakeoff import BakeoffError
from bakeoff.decide import load_scores
from bakeoff.log import LANES, metrics, parse, problems

REPO = "sjawhar/project-violet"
CHECKS = ("build", "replay", "no-dash-fails", "no-double-jump-fails", "tags", "mutation-fails")
COLUMNS = ("direction", "engine", "machine", "status", *CHECKS, "agent-hours", "usd", "interventions", "friction", "blockers")
SCORES = ("visual_quality", "character_appeal", "color_readability", "would_ship")
UNITY_TESTS = {
    "replay": "Level01ReplayReachesTheGoal",
    "no-dash-fails": "Level01ReplayFailsWithoutDash",
    "tags": "TagValidatorPassesOnTheBuiltLevel",
    "mutation-fails": "TagValidatorFailsWhenATagIsRemoved",
}
REEL_CLIPS = {"idle", "run", "jump", "fall", "double_jump", "dash", "land"}
TAG_LINE = re.compile(r"tag-check: (\d+) problem\(s\)")
PREVIEW_TIMEOUT_S = 1800  # preview transcodes every capture and still; measured 2.5 min for five lanes
GH_TIMEOUT_S = 60

Checks = dict[str, bool | None]
"""Check name -> True passed, False failed or missing, None does not apply to this lane."""


@dataclass
class Lane:
    name: str
    front: dict
    problems: list[str]
    """What is wrong with the lane's LOG.md and reports, one message each; shown in the notes."""
    checks: Checks
    capture: Path | None
    stills: list[Path]

    @property
    def media(self) -> list[Path]:
        return ([self.capture] if self.capture else []) + self.stills


def _lines(path: Path, found: list[str]) -> list[str] | None:
    if not path.is_file():
        found.append(f"reports/{path.name}: missing")
        return None
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _verdict(path: Path, found: list[str]) -> dict | None:
    """The replay runner's verdict: the last line that is a JSON object (Godot may print warnings after it)."""
    lines = _lines(path, found)
    for line in reversed(lines or []):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    if lines is not None:
        found.append(f"reports/{path.name}: no JSON line")
    return None


def _tag_count(path: Path, found: list[str]) -> int | None:
    """The count on the last `tag-check: N problem(s)` line (Godot may print warnings after it)."""
    lines = _lines(path, found)
    for line in reversed(lines or []):
        if match := TAG_LINE.fullmatch(line.strip()):
            return int(match.group(1))
    if lines is not None:
        found.append(f"reports/{path.name}: no 'tag-check: N problem(s)' line")
    return None


def godot_checks(reports: Path) -> tuple[Checks, list[str]]:
    found: list[str] = []
    replay = _verdict(reports / "replay.json", found)
    no_dash = _verdict(reports / "replay-no-dash.json", found)
    no_double_jump = _verdict(reports / "replay-no-double-jump.json", found)
    tags, mutated = _tag_count(reports / "tags.txt", found), _tag_count(reports / "tags-mutated.txt", found)
    build = reports / "build.txt"
    built = build.is_file() and build.stat().st_size > 0
    if not built:
        found.append("reports/build.txt: missing or empty")
    return {
        "build": built,
        "replay": replay is not None and replay.get("ok") is True,
        "no-dash-fails": no_dash is not None and no_dash.get("ok") is False,
        "no-double-jump-fails": no_double_jump is not None and no_double_jump.get("ok") is False,
        "tags": tags == 0,
        "mutation-fails": mutated is not None and mutated > 0,
    }, found


def unity_checks(reports: Path) -> tuple[Checks, list[str]]:
    """NUnit3 PlayMode results: the run has no failures and each of the four required tests passed."""
    found: list[str] = []
    passed: set[str] = set()
    clean_run = False
    playmode = reports / "playmode.xml"
    if not playmode.is_file():
        found.append("reports/playmode.xml: missing")
    else:
        try:
            run = ET.parse(playmode).getroot()
        except ET.ParseError as error:
            found.append(f"reports/playmode.xml: does not parse: {error}")
        else:
            cases = list(run.iter("test-case"))
            passed = {case.get("name", "") for case in cases if case.get("result") == "Passed"}
            clean_run = run.get("failed") == "0"
            if not clean_run:
                failing = sorted(case.get("name", "?") for case in cases if case.get("result") == "Failed")
                found.append(f"reports/playmode.xml: failed={run.get('failed')!r} ({', '.join(failing) or 'no failed test-case'})")
            missing = [test for test in UNITY_TESTS.values() if test not in passed]
            if missing:
                found.append(f"reports/playmode.xml: did not pass: {', '.join(missing)}")
    lines = _lines(reports / "build.log", found)
    built = lines is not None and any("Build succeeded" in line for line in lines)
    if lines is not None and not built:
        found.append("reports/build.log: no 'Build succeeded'")
    checks: Checks = {name: clean_run and test in passed for name, test in UNITY_TESTS.items()}
    return {"build": built, "no-double-jump-fails": None, **checks}, found


def control_checks(reports: Path) -> tuple[Checks, list[str]]:
    """Control renders a reel; it has no playable build or completability test by design."""
    found: list[str] = []
    path = reports / "render.json"
    rendered = False
    if not path.is_file():
        found.append("reports/render.json: missing")
    else:
        try:
            render = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            found.append(f"reports/render.json: not valid JSON: {error}")
        else:
            render = render if isinstance(render, dict) else {}
            clips = render.get("clips")  # names, or reel.json's {name, glb, seconds} clip objects
            names = [clip.get("name") if isinstance(clip, dict) else clip for clip in clips] if isinstance(clips, list) else []
            clips = {name for name in names if isinstance(name, str)}
            frames, seconds = render.get("frames"), render.get("seconds")
            if missing := sorted(REEL_CLIPS - clips):
                found.append(f"reports/render.json: clips missing {', '.join(missing)}")
            if not (isinstance(frames, int) and not isinstance(frames, bool) and frames > 0):
                found.append(f"reports/render.json: frames {frames!r} is not a positive integer")
            if not (isinstance(seconds, int | float) and not isinstance(seconds, bool) and 60 <= seconds <= 90):
                found.append(f"reports/render.json: seconds {seconds!r} is not 60-90")
            rendered = not found
    return {"build": rendered, **dict.fromkeys(CHECKS[1:], None)}, found


ENGINE_CHECKS = {"godot": godot_checks, "unity": unity_checks, "blender": control_checks}


def lane_results(lanes_dir: Path) -> list[Lane]:
    if not lanes_dir.is_dir():
        raise BakeoffError(f"{lanes_dir}: no such directory (the lanes directory, default bakeoff/)")
    lanes = []
    for name, (_, engine) in LANES.items():
        lane_dir = lanes_dir / name
        checks, report_problems = ENGINE_CHECKS[engine](lane_dir / "reports")
        if not lane_dir.is_dir():
            front, found = {}, [f"no {name}/ directory yet"]
        elif not (lane_dir / "LOG.md").is_file():
            front, found = {}, [f"no {name}/LOG.md yet", *report_problems]
        else:
            parsed = parse(lane_dir / "LOG.md")
            front = parsed if isinstance(parsed, dict) else {}
            found = [f"LOG.md: {problem}" for problem in problems(parsed, lane_dir=name)] + report_problems
        capture = lane_dir / "capture" / "capture.mp4"
        lanes.append(Lane(
            name=name, front=front, problems=found, checks=checks,
            capture=capture if capture.is_file() else None,
            stills=sorted((lane_dir / "capture").glob("still-*.png")),
        ))
    return lanes


def run_preview(pr: str, paths: list[Path], repo_root: Path) -> Path:
    """`preview build` on the captures and stills; returns out/review/pr-<n>/."""
    command = ["uv", "run", "--project", str(repo_root / "tools/preview"), "preview", "build", pr, *map(str, paths)]
    try:
        result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, timeout=PREVIEW_TIMEOUT_S)
    except subprocess.TimeoutExpired as error:
        raise BakeoffError(f"preview build did not finish in {PREVIEW_TIMEOUT_S} s") from error
    if result.returncode != 0:
        raise BakeoffError(f"preview build failed:\n{result.stderr.strip()}")
    return repo_root / "out/review" / f"pr-{pr}"


def latest_run_url(lane: str) -> str | None:
    """The newest Actions run on bakeoff/<lane>, or None when there is none."""
    command = ["gh", "api", f"repos/{REPO}/actions/runs?branch=bakeoff/{lane}&per_page=1", "--jq", ".workflow_runs[0].html_url // empty"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=GH_TIMEOUT_S)
    except subprocess.TimeoutExpired as error:
        raise BakeoffError(f"gh api for bakeoff/{lane} did not answer in {GH_TIMEOUT_S} s (gh auth status?)") from error
    if result.returncode != 0:
        raise BakeoffError(f"gh api failed for bakeoff/{lane}: {result.stderr.strip()}")
    return result.stdout.strip() or None


def _scores(repo_root: Path) -> dict:
    """Scores per lane from docs/bakeoff/scores.json; before Sami judges there is no file and every lane is unscored."""
    path = repo_root / "docs/bakeoff/scores.json"
    return load_scores(path, repo_root)["lanes"] if path.is_file() else {}


def _mark(value: bool | None) -> str:
    return "n/a" if value is None else "✓" if value else "✗"


def _text(value: object) -> str:
    return "?" if value is None else str(value)


def _row_values(lane: Lane, scores: dict) -> dict[str, str]:
    front = lane.front
    direction, engine = LANES[lane.name]
    values = {"direction": direction, "engine": engine, "machine": _text(front.get("machine")), "status": _text(front.get("status"))}
    values.update({name: _mark(lane.checks[name]) for name in CHECKS})
    log_ok = bool(front) and not any(problem.startswith("LOG.md:") for problem in lane.problems)
    if log_ok:
        numbers = metrics(front)
        values.update({
            "agent-hours": f"{numbers['agent_hours']:.1f}",
            "usd": f"{numbers['usd']:.2f}",
            "interventions": f"{numbers['interventions']} / {numbers['intervention_minutes']:g} min",
            "friction": str(numbers["friction"]),
        })
    else:
        values.update(dict.fromkeys(("agent-hours", "usd", "interventions", "friction"), "?"))
    blockers = front.get("blockers")
    if isinstance(blockers, list):
        values["blockers"] = "; ".join(_text(b.get("what")) if isinstance(b, dict) else str(b) for b in blockers) or "none"
    else:
        values["blockers"] = _text(blockers)
    score = scores.get(lane.name)
    if score:
        values.update({key: "not scored" if score[key] is None else str(score[key]) for key in SCORES[:3]})
        values["would_ship"] = "yes" if score["would_ship"] else "no"
    else:
        values.update(dict.fromkeys(SCORES, "unscored"))
    caveat = ["build here means the reel rendered (render.json); control has no playable build by design"] if LANES[lane.name][1] == "blender" else []
    values["notes"] = "\n".join(([score["notes"]] if score and score["notes"] else []) + caveat + lane.problems)
    return values


def _media_by_source(out: Path, paths: list[Path]) -> dict[Path, dict]:
    manifest = json.loads((out / "preview.json").read_text(encoding="utf-8"))
    return {path: item["media"] for path, item in zip(paths, manifest["items"], strict=True)}


def _html(value: str) -> str:
    return escape(value).replace("\n", "<br>")


def _fields(names: tuple[str, ...], values: dict[str, str]) -> str:
    """Labelled values in a grid that wraps to the screen width."""
    return "".join(f'<div><dt>{escape(name)}</dt><dd data-col="{name}">{_html(values[name])}</dd></div>' for name in names)


STYLE = (
    "body{margin:0 auto;max-width:60rem;padding:1rem;background:#111116;color:#e5e5ea;font:15px/1.45 system-ui,sans-serif}"
    "a{color:#a78bfa}nav a{margin-right:.8rem}"
    ".lane{border-top:1px solid #33333d;padding:1rem 0}.lane h2{margin:0 0 .25rem;font-size:1.2rem}.lane p{margin:.25rem 0}"
    "video{width:100%;display:block;background:#000}"
    ".stills{display:grid;grid-template-columns:repeat(2,1fr);gap:.4rem;margin:.4rem 0}.stills img{width:100%;display:block}"
    "dl{display:grid;grid-template-columns:repeat(auto-fill,minmax(9.5rem,1fr));gap:.3rem .8rem;margin:.6rem 0}"
    "dt{color:#9a9aa6;font-size:.8rem}dd{margin:0;font-weight:600}"
    ".notes{white-space:normal;color:#c9c9d3}"
)


def page(pr: str, lanes: list[Lane], scores: dict, media: dict[Path, dict], runs: dict[str, str | None]) -> str:
    """One card per lane, in a single column that reads on a phone: summary, capture, stills, checks, numbers, scores."""
    cards = []
    for lane in lanes:
        values = _row_values(lane, scores)
        run = runs.get(lane.name)
        links = (f'<a href="https://github.com/{REPO}/tree/bakeoff/{escape(lane.name)}">{escape(lane.name)}</a> '
                 + (f'<a href="{escape(run)}">CI</a>' if run else "(no CI run)"))
        summary = " · ".join(f'<span data-col="{c}">{_html(values[c])}</span>' for c in ("direction", "engine", "machine", "status"))
        if lane.capture:
            clip = media[lane.capture]
            poster = f' poster="{escape(clip["poster"])}"' if "poster" in clip else ""
            capture = f'<video src="{escape(clip["video"])}"{poster} controls playsinline preload="none"></video>'
        else:
            capture = "no capture yet"
        stills = "".join(f'<img src="{escape(media[s]["image"])}" alt="{escape(s.name)}" loading="lazy">' for s in lane.stills)
        cards.append(
            f'<section class="lane" id="lane-{escape(lane.name)}"><h2 data-col="lane">{links}</h2><p>{summary}</p>'
            f'<div data-col="capture">{capture}</div><div class="stills" data-col="stills">{stills or "no stills yet"}</div>'
            f"<dl>{_fields(CHECKS, values)}</dl>"
            f'<dl>{_fields(("agent-hours", "usd", "interventions", "friction", "blockers"), values)}</dl>'
            f"<dl>{_fields(SCORES, values)}</dl>"
            f'<p class="notes" data-col="notes">{_html(values["notes"])}</p></section>'
        )
    nav = " ".join(f'<a href="#lane-{escape(lane.name)}">{escape(lane.name)}</a>' for lane in lanes)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>Bake-off judging: PR {escape(pr)}</title><style>{STYLE}</style></head><body>"
        f"<h1>Bake-off judging (THROWAWAY), PR {escape(pr)}</h1>"
        f'<p>Score every lane against <a href="https://github.com/{REPO}/blob/master/docs/bakeoff/judging.md">docs/bakeoff/judging.md</a>. '
        f'<a href="index.html">All media</a>.</p><nav>{nav}</nav>{"".join(cards)}'
        "</body></html>\n"
    )


def build(pr: str, lanes_dir: Path, repo_root: Path, *,
          preview: Callable[[str, list[Path], Path], Path] = run_preview,
          latest_run: Callable[[str], str | None] = latest_run_url) -> Path:
    """Build out/review/pr-<n>/: preview's page for every capture and still, then bakeoff.html beside it.

    The media are copied to out/lanes/<lane>/ as `<lane>-<name>` first, so preview's own page says which lane each
    item came from.
    """
    lanes = lane_results(lanes_dir)
    scores = _scores(repo_root)
    staged: dict[Path, Path] = {}
    for lane in lanes:
        if lane.media:
            directory = repo_root / "out/lanes" / lane.name
            shutil.rmtree(directory, ignore_errors=True)
            directory.mkdir(parents=True)
            staged |= {path: shutil.copy2(path, directory / f"{lane.name}-{path.name}") for path in lane.media}
    if not staged:
        raise BakeoffError(f"no lane under {lanes_dir} has a capture or still yet; there is nothing to judge")
    out = preview(pr, list(staged.values()), repo_root)
    by_copy = _media_by_source(out, list(staged.values()))
    media = {path: by_copy[copy] for path, copy in staged.items()}
    runs = {lane.name: latest_run(lane.name) for lane in lanes}
    (out / "bakeoff.html").write_text(page(pr, lanes, scores, media, runs), encoding="utf-8")
    return out


def results_markdown(pr: str, lanes_dir: Path, repo_root: Path) -> str:
    """The gallery's table without the media, for docs/bakeoff/results.md."""
    lanes = lane_results(lanes_dir)
    scores = _scores(repo_root)
    columns = (*COLUMNS, *SCORES, "notes")
    lines = [
        "# Bake-off results (THROWAWAY)",
        "",
        f"Gallery: https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/review/pr-{pr}/bakeoff.html",
        "",
        "| lane | " + " | ".join(columns) + " |",
        "|" + "---|" * (len(columns) + 1),
    ]
    for lane in lanes:
        values = _row_values(lane, scores)
        # GitHub renders HTML inside a table cell, so text is escaped before newlines become <br>.
        cells = [escape(values[c], quote=False).replace("|", "\\|").replace("\n", "<br>") for c in columns]
        lines.append(f"| {lane.name} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"

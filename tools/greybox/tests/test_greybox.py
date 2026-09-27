"""Tests for greybox.cli: check() and render() against in-memory violet-greybox levels
and the real docs/bakeoff/level01.greybox.json. THROWAWAY bake-off tooling tests."""
import json
from pathlib import Path

from PIL import Image

from greybox.cli import check, render

REPO_ROOT = Path(__file__).resolve().parents[3]
LEVEL01 = REPO_ROOT / "docs" / "bakeoff" / "level01.greybox.json"


def make_level(rows: list[str], legend: dict[str, str] | None = None, tile_size_px: int = 64) -> dict:
    return {
        "format": "violet-greybox",
        "version": 1,
        "tile_size_px": tile_size_px,
        "legend": legend if legend is not None else {".": "empty", "#": "solid", "S": "start", "E": "goal"},
        "rows": rows,
    }


def test_ragged_rows_report_columns_problem():
    level_ok = make_level(["S..E", "...."])
    assert not any("columns" in p for p in check(level_ok))
    ragged = make_level(["S..E", "..."])
    problems = check(ragged)
    assert any("row 1" in p and "columns" in p for p in problems)


def test_unknown_character_names_it():
    level = make_level(["S.X.E"])
    problems = check(level)
    assert any("'X'" in p and "not in the legend" in p for p in problems)


def test_two_goals_is_a_problem():
    level = make_level(["S.E.E"])
    problems = check(level)
    assert any("exactly one goal" in p for p in problems)


def test_missing_start_is_a_problem():
    level = make_level(["..E."])
    problems = check(level)
    assert any("exactly one start" in p for p in problems)


def test_tagged_wall_without_its_orb_is_a_problem():
    legend = {".": "empty", "S": "start", "E": "goal", "R": "wall_red"}
    level = make_level(["S.R.E"], legend=legend)
    problems = check(level)
    assert any("wall_red is used but there is no orb_red" in p for p in problems)


def test_tagged_wall_with_its_orb_has_no_problem():
    legend = {".": "empty", "S": "start", "E": "goal", "R": "wall_red", "1": "orb_red"}
    level = make_level(["S.R1E"], legend=legend)
    problems = check(level)
    assert not any("orb_red" in p for p in problems)


def test_bad_tile_size_is_a_problem():
    level = make_level(["S.E"], tile_size_px=50)
    problems = check(level)
    assert any("tile_size_px" in p for p in problems)


def test_level01_has_zero_problems():
    assert LEVEL01.exists(), f"missing {LEVEL01}"
    level = json.loads(LEVEL01.read_text())
    assert check(level) == []


def test_render_writes_png_sized_to_rows_times_scale(tmp_path):
    level = json.loads(LEVEL01.read_text())
    out = tmp_path / "level01.png"
    render(level, out, scale=4)
    with Image.open(out) as img:
        assert img.size == (72 * 4, 16 * 4)

"""bakeoff: THROWAWAY Phase 1 bake-off tooling. Run anywhere inside the repository.

Exit codes: 0 ok, 1 content problems (a LOG.md or a scores file), 2 usage, configuration or I/O errors.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from bakeoff import BakeoffError
from bakeoff.decide import SCHEMA, ScoresError, decide, load_scores
from bakeoff.gallery import build, results_markdown
from bakeoff.log import parse, problems


def find_root(start: Path) -> Path:
    """The repository root: the nearest directory at or above `start` holding docs/bakeoff/scores.schema.json."""
    for directory in (start, *start.parents):
        if (directory / SCHEMA).is_file():
            return directory
    raise BakeoffError(f"no {SCHEMA} in {start} or any parent; run bakeoff inside the project-violet repository")


def _pr(text: str) -> str:
    """The same PR argument `preview` takes, so the gallery lands where `preview publish` expects it."""
    if not re.fullmatch(r"[0-9]+(-[a-z0-9]+)*", text):
        raise argparse.ArgumentTypeError(f"expected a PR number such as 12 or 0-smoke, got {text!r}")
    return text


def cmd_log_check(args: argparse.Namespace) -> int:
    found = []
    for path in args.logs:
        lane_dir = path.parent.name if path.name == "LOG.md" else None  # bakeoff/<lane>/LOG.md must name <lane>
        found += [f"{path}: {problem}" for problem in problems(parse(path), lane_dir=lane_dir)]
    for line in found:
        print(line, file=sys.stderr)
    print(f"bakeoff log-check: {len(found)} problem(s)")
    return 1 if found else 0


def cmd_decide(args: argparse.Namespace) -> int:
    print(json.dumps(decide(load_scores(args.scores, find_root(Path.cwd()))), indent=2))
    return 0


def cmd_gallery(args: argparse.Namespace) -> int:
    root = find_root(Path.cwd())
    out = build(args.pr, args.lanes_dir or root / "bakeoff", root)
    print(f"wrote {out / 'bakeoff.html'}; publish it with `uv run --project tools/preview preview publish {args.pr}`")
    return 0


def cmd_results_md(args: argparse.Namespace) -> int:
    root = find_root(Path.cwd())
    print(results_markdown(args.pr, args.lanes_dir or root / "bakeoff", root), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bakeoff", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    log_check = commands.add_parser("log-check", help="check lane LOG.md front matter against docs/bakeoff/lane-log-format.md")
    log_check.add_argument("logs", nargs="+", type=Path, metavar="LOG")
    log_check.set_defaults(handler=cmd_log_check)
    decide_parser = commands.add_parser("decide", help="apply the decision rule to a scores file")
    decide_parser.add_argument("scores", type=Path, metavar="SCORES")
    decide_parser.set_defaults(handler=cmd_decide)
    for name, handler, text in (("gallery", cmd_gallery, "build out/review/pr-<n>/bakeoff.html (then `preview publish`)"),
                                ("results-md", cmd_results_md, "print the results table as Markdown")):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("--pr", required=True, type=_pr, metavar="PR_NUMBER")
        sub.add_argument("--lanes-dir", type=Path, metavar="DIR", help="the lanes directory (default: bakeoff/ at the repository root)")
        sub.set_defaults(handler=handler)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ScoresError as error:
        print(f"bakeoff: {error}", file=sys.stderr)
        return 1
    except (BakeoffError, OSError) as error:
        print(f"bakeoff: error: {error}", file=sys.stderr)
        return 2

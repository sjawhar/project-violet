"""The `provenance` command line."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from provenance.config import Config, ProvenanceError, find_config, load_config
from provenance.lfs import lfs_check
from provenance.record import GENERATOR_FLAGS, RecordRequest, write_record
from provenance.records import check_asset, discover_assets, load_record, sidecar_for, validator
from provenance.report import steam_report


def _print_problems(config: Config, assets: list[Path]) -> bool:
    """Print every provenance problem across the assets to stderr; return whether there were any."""
    problems = [problem for asset in assets for problem in check_asset(config, asset)]
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"provenance: {len(problems)} problem(s) across {len(assets)} asset(s)", file=sys.stderr)
    return bool(problems)


def cmd_check(config: Config, args: argparse.Namespace) -> int:
    assets = discover_assets(config, [Path(p).resolve() for p in args.paths])
    if _print_problems(config, assets):
        return 1
    print(f"provenance check: {len(assets)} asset(s) OK")
    return 0


def cmd_steam_report(config: Config, args: argparse.Namespace) -> int:
    assets = discover_assets(config, [])
    if _print_problems(config, assets):
        print("provenance steam-report: fix these records first; the disclosure must cover every asset", file=sys.stderr)
        return 1
    records = [load_record(sidecar_for(asset))[0] for asset in assets]
    print(steam_report(records), end="")
    return 0


def cmd_lfs_check(config: Config, args: argparse.Namespace) -> int:
    problems = lfs_check(config.root)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"provenance lfs-check: {len(problems)} file(s) should be LFS pointers", file=sys.stderr)
        return 1
    print("provenance lfs-check: OK")
    return 0


def cmd_record(config: Config, args: argparse.Namespace) -> int:
    params = dict(args.params)
    if len(params) != len(args.params):
        raise ProvenanceError("--param keys must be unique")
    request = RecordRequest(
        asset=Path(args.asset).resolve(),
        kind=args.kind,
        origin=args.origin,
        license=args.license,
        source_url=args.source_url,
        authors=args.authors,
        generator={name: getattr(args, name) for name in GENERATOR_FLAGS if getattr(args, name) is not None},
        params=params,
        inputs=[Path(p).resolve() for p in args.inputs],
        human_edits=args.human_edits,
    )
    sidecar = write_record(config, request, force=args.force, now=datetime.now(UTC))
    print(f"wrote {config.display(sidecar)}")
    return 0


def _key_value(text: str) -> tuple[str, str]:
    key, sep, value = text.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {text!r}")
    return key, value


def _human_edit(text: str) -> tuple[str, str]:
    by, sep, description = text.partition(": ")
    if not sep or not by.strip() or not description.strip():
        raise argparse.ArgumentTypeError(f"expected 'NAME: DESCRIPTION', got {text!r}")
    return by.strip(), description.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="provenance", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="verify every asset has a valid, current provenance sidecar")
    check.add_argument("paths", nargs="*", metavar="PATH", help="files or directories to check (default: every configured root)")
    check.set_defaults(handler=cmd_check)

    schema = validator().schema["properties"]
    record = commands.add_parser("record", help="write the provenance sidecar (<asset>.provenance.json) for an asset")
    record.add_argument("asset", metavar="ASSET")
    record.add_argument("--kind", required=True, choices=schema["kind"]["enum"])
    record.add_argument("--origin", required=True, choices=schema["origin"]["enum"])
    record.add_argument("--license", required=True, help="e.g. proprietary, CC0-1.0")
    record.add_argument("--source-url", help="where a third-party asset came from")
    record.add_argument("--author", action="append", default=[], dest="authors", metavar="NAME", help="required for --origin human; repeatable")
    record.add_argument(
        "--human-edit", action="append", default=[], type=_human_edit, dest="human_edits", metavar="'NAME: DESCRIPTION'",
        help="a manual edit to the asset; repeatable",
    )
    record.add_argument("--force", action="store_true", help="replace an existing sidecar")
    generator = record.add_argument_group("generator", "required unless --origin human: --tool, --tool-version, --provider, --model, --prompt")
    for name, flag in GENERATOR_FLAGS.items():
        generator.add_argument(flag, dest=name, type=int if name == "seed" else str)
    generator.add_argument("--param", action="append", default=[], type=_key_value, dest="params", metavar="KEY=VALUE", help="repeatable")
    generator.add_argument("--input", action="append", default=[], dest="inputs", metavar="PATH", help="a source or reference asset; repeatable")
    record.set_defaults(handler=cmd_record)

    report = commands.add_parser("steam-report", help="print the Steam Pre-Generated AI Content disclosure from the records")
    report.add_argument("--format", choices=["md"], default="md", help="output format (default: md)")
    report.set_defaults(handler=cmd_steam_report)

    lfs = commands.add_parser("lfs-check", help="fail on files matching a filter=lfs rule that are committed as regular blobs")
    lfs.set_defaults(handler=cmd_lfs_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(find_config(Path.cwd()))
        return args.handler(config, args)
    except ProvenanceError as error:
        print(f"provenance: error: {error}", file=sys.stderr)
        return 2

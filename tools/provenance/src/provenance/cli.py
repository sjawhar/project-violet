"""Provenance records for Violet's shipped assets: write them, check them, and report them for Steam."""

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from provenance.config import Config, ProvenanceError, find_config, load_config
from provenance.lfs import lfs_check
from provenance.record import GENERATOR_FLAGS, RecordRequest, add_human_edit, write_record
from provenance.records import Record, check_asset, discover_assets, load_record, missing_roots, sidecar_for, validator
from provenance.report import steam_report


def _absolute(path: str) -> Path:
    """Absolute and normalized, without resolving symlinks: a symlinked asset's sidecar sits beside the link."""
    return Path(os.path.abspath(path))


def _report(problems: list[str], summary: str) -> bool:
    """Print the problems and a summary line to stderr; return whether there were any."""
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(summary.format(count=len(problems)), file=sys.stderr)
    return bool(problems)


def _checked_records(config: Config, assets: list[Path]) -> tuple[list[str], dict[str, Record]]:
    problems: list[str] = []
    records: dict[str, Record] = {}
    for asset in assets:
        asset_problems, record = check_asset(config, asset)
        problems += asset_problems
        if record is not None:
            records[config.display(asset)] = record
    return problems, records


def _note_missing_roots(config: Config) -> None:
    for root in missing_roots(config):
        print(f"note: asset root '{root}' does not exist; nothing there to check", file=sys.stderr)


def cmd_check(config: Config, args: argparse.Namespace) -> int:
    if not args.paths:
        _note_missing_roots(config)
    assets = discover_assets(config, [_absolute(p) for p in args.paths])
    problems, _ = _checked_records(config, assets)
    if _report(problems, f"provenance check: {{count}} problem(s) across {len(assets)} asset(s)"):
        return 1
    print(f"provenance check: {len(assets)} asset(s) OK")
    return 0


def cmd_steam_report(config: Config, args: argparse.Namespace) -> int:
    _note_missing_roots(config)
    assets = discover_assets(config, [])
    problems, records = _checked_records(config, assets)
    if _report(problems, "provenance steam-report: {count} problem(s); the disclosure must cover every asset, so fix them first"):
        return 1

    known = dict(records)

    def lookup(path: str) -> Record:
        """The record for an asset or an input to one, which may sit outside the asset roots."""
        if path not in known:
            sidecar = sidecar_for(config.root / path)
            if not sidecar.is_file():
                raise ProvenanceError(
                    f"{path} is an input to a recorded asset but has no provenance record; "
                    "record it so the disclosure can tell whether AI was involved"
                )
            record, record_problems = load_record(sidecar)
            if record is None:
                raise ProvenanceError(f"{config.display(sidecar)} is invalid:\n  " + "\n  ".join(record_problems))
            known[path] = record
        return known[path]

    report = steam_report(records, lookup)
    if not report:
        print(f"provenance steam-report: none of the {len(records)} recorded asset(s) involve generative AI; nothing to disclose", file=sys.stderr)
        return 0
    print(report, end="")
    return 0


def cmd_lfs_check(config: Config, args: argparse.Namespace) -> int:
    if _report(lfs_check(config.root), "provenance lfs-check: {count} file(s) should be LFS pointers"):
        return 1
    print("provenance lfs-check: OK")
    return 0


def cmd_record(config: Config, args: argparse.Namespace) -> int:
    params = dict(args.params)
    if len(params) != len(args.params):
        raise ProvenanceError("--param keys must be unique")
    request = RecordRequest(
        asset=_absolute(args.asset),
        kind=args.kind,
        origin=args.origin,
        license=args.license,
        source_url=args.source_url,
        authors=args.authors,
        generator={name: getattr(args, name) for name in GENERATOR_FLAGS if getattr(args, name) is not None},
        params=params,
        inputs=[_absolute(p) for p in args.inputs],
    )
    sidecar = write_record(config, request, force=args.force, now=datetime.now(UTC))
    print(f"wrote {config.display(sidecar)}")
    return 0


def cmd_edit(config: Config, args: argparse.Namespace) -> int:
    sidecar = add_human_edit(config, _absolute(args.asset), by=args.by, description=args.description, now=datetime.now(UTC))
    print(f"updated {config.display(sidecar)}")
    return 0


def _key_value(text: str) -> tuple[str, str]:
    key, sep, value = text.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {text!r}")
    return key, value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="provenance", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="verify every asset has a valid, current provenance sidecar")
    check.add_argument("paths", nargs="*", metavar="PATH", help="files or directories to check (default: every configured root)")
    check.set_defaults(handler=cmd_check)

    schema = validator().schema["properties"]
    record = commands.add_parser(
        "record",
        help="write the provenance sidecar (<asset>.provenance.json) for an asset",
        description="generated needs --tool, --tool-version, --provider, --model, --prompt; "
        "derived needs --tool, --tool-version and at least one --input; human needs --author and takes no generator flags.",
    )
    record.add_argument("asset", metavar="ASSET")
    record.add_argument("--kind", required=True, choices=schema["kind"]["enum"])
    record.add_argument("--origin", required=True, choices=schema["origin"]["enum"])
    record.add_argument("--license", required=True, help="e.g. proprietary, CC0-1.0")
    record.add_argument("--source-url", help="where a third-party asset came from")
    record.add_argument("--author", action="append", default=[], dest="authors", metavar="NAME", help="required for --origin human; repeatable")
    record.add_argument("--force", action="store_true", help="replace an existing sidecar")
    generator = record.add_argument_group("generator")
    for name, flag in GENERATOR_FLAGS.items():
        generator.add_argument(flag, dest=name, type=int if name == "seed" else str)
    generator.add_argument("--param", action="append", default=[], type=_key_value, dest="params", metavar="KEY=VALUE", help="repeatable")
    generator.add_argument("--input", action="append", default=[], dest="inputs", metavar="PATH", help="a source or reference asset in the repository; repeatable")
    record.set_defaults(handler=cmd_record)

    edit = commands.add_parser("edit", help="record a person's edit to an asset: append it to the sidecar and update the hash")
    edit.add_argument("asset", metavar="ASSET")
    edit.add_argument("--by", required=True, metavar="NAME")
    edit.add_argument("--description", required=True, metavar="TEXT")
    edit.set_defaults(handler=cmd_edit)

    report = commands.add_parser("steam-report", help="print the Steam Pre-Generated AI Content disclosure from the records")
    report.add_argument("--format", choices=["md"], default="md", help="output format (default: md)")
    report.set_defaults(handler=cmd_steam_report)

    lfs = commands.add_parser(
        "lfs-check",
        help="fail on files matching a filter=lfs rule that are committed as regular blobs",
        description="Checks the git index (in a jj colocated repository, the parent of the working-copy commit).",
    )
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

"""`gen image ...`: call a provider's image-generation API and record its provenance sidecar."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from provenance.config import ProvenanceError, find_config, load_config
from provenance.record import RecordRequest, write_record
from provenance.records import check_asset

from gen.providers import Provider, ProviderError
from gen.providers import gemini as gemini_provider
from gen.providers import openai as openai_provider

PROVIDERS: dict[str, Provider] = {"openai": openai_provider, "gemini": gemini_provider}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gen", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    image = commands.add_parser("image", help="generate an image and record its provenance")
    image.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    image.add_argument("--model", required=True, help="the provider's model id, e.g. gpt-image-2 or gemini-3.1-flash-image")
    image.add_argument("--prompt", required=True)
    image.add_argument("--negative-prompt", help="folded into the prompt text; neither provider has a native field for this")
    image.add_argument("--size", metavar="WxH", help="e.g. 1024x1024; provider-specific constraints apply")
    image.add_argument("--seed", type=int)
    image.add_argument("--input", action="append", default=[], dest="inputs", metavar="PATH", help="a reference image inside the repository; repeatable")
    image.add_argument(
        "--background",
        choices=["transparent", "opaque"],
        help="OpenAI only; Gemini raises an error if this is set",
    )
    image.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        help="OpenAI only, default high; low is for drafts and tests. Gemini raises an error if this is set",
    )
    image.add_argument("--license", default="proprietary", help="recorded in the sidecar (default: proprietary)")
    image.add_argument("--force", action="store_true", help="replace an existing --out file and sidecar")
    image.add_argument("--out", required=True, type=Path)
    image.set_defaults(handler=cmd_image)

    return parser


def cmd_image(args: argparse.Namespace) -> int:
    out = args.out.resolve()
    if out.exists() and not args.force:
        print(f"gen: error: {out} already exists; pass --force to replace it", file=sys.stderr)
        return 1

    try:
        config = load_config(find_config(Path.cwd()))
    except ProvenanceError as error:
        print(f"gen: error: {error}", file=sys.stderr)
        return 1

    inputs = [Path(p).resolve() for p in args.inputs]
    for input_path in inputs:
        if not input_path.is_file():
            print(f"gen: error: --input {input_path}: no such file", file=sys.stderr)
            return 1
        if not input_path.is_relative_to(config.root):
            print(f"gen: error: --input {input_path}: inputs must live inside the repository ({config.root})", file=sys.stderr)
            return 1
        problems, _ = check_asset(config, input_path)
        if problems:
            print(
                f"gen: error: --input {config.display(input_path)} has no valid, current provenance record; "
                "run `provenance record` (or `gen image`, if it was itself generated) for it first",
                file=sys.stderr,
            )
            return 1
    provider = PROVIDERS[args.provider]
    try:
        image = provider.generate(
            args.prompt,
            model=args.model,
            size=args.size,
            seed=args.seed,
            negative_prompt=args.negative_prompt,
            inputs=inputs,
            background=args.background,
            quality=args.quality,
        )
    except ProviderError as error:
        print(f"gen: error: {error}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(image.data)

    generator: dict[str, str | int] = {
        "tool": "gen",
        "tool_version": version("gen"),
        "provider": args.provider,
        "model": args.model,
    }
    if image.model_version is not None:
        generator["model_version"] = image.model_version
    generator["prompt"] = args.prompt
    if args.negative_prompt is not None:
        generator["negative_prompt"] = args.negative_prompt
    if args.seed is not None:
        generator["seed"] = args.seed

    request = RecordRequest(
        asset=out,
        kind="image",
        origin="generated",
        license=args.license,
        generator=generator,
        params=image.params,
        inputs=inputs,
    )
    try:
        sidecar = write_record(config, request, force=args.force, now=datetime.now(UTC))
    except ProvenanceError as error:
        out.unlink(missing_ok=True)
        print(f"gen: error: {error}", file=sys.stderr)
        return 1

    print(f"wrote {config.display(out)} and {config.display(sidecar)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)

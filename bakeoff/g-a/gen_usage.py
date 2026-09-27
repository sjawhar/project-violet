"""THROWAWAY (bake-off lane G-A): runs `gen image` unchanged and appends each provider response's token usage to a JSONL file.

tools/gen writes the image and its provenance sidecar but keeps no usage record, and the lane log needs a cost per
generation. This wraps httpx's POST in-process to read the `usage` (OpenAI) or `usageMetadata` (Gemini) the response
already carries; the request, the image and the sidecar are exactly what `gen` alone produces.

    secrets OPENAI_API_KEY -- uv run --project tools/gen python bakeoff/g-a/gen_usage.py USAGE.jsonl image --provider ... --out PATH
"""

import json
import sys
from datetime import UTC, datetime

import httpx
from gen.cli import main

log_path, argv = sys.argv[1], sys.argv[2:]
responses: list[dict] = []
_post = httpx.Client.post


def post(self: httpx.Client, *args, **kwargs) -> httpx.Response:
    response = _post(self, *args, **kwargs)
    try:
        body = response.json()
    except ValueError:
        body = {}
    responses.append({
        "status": response.status_code,
        "endpoint": response.request.url.path,
        "usage": body.get("usage") or body.get("usageMetadata"),
        "size": body.get("size"),
        "quality": body.get("quality"),
        "model_version": body.get("modelVersion"),
    })
    return response


httpx.Client.post = post
code = main(argv)
out = argv[argv.index("--out") + 1]
model = argv[argv.index("--model") + 1]
with open(log_path, "a") as log:
    for entry in responses:
        log.write(json.dumps({"at": datetime.now(UTC).isoformat(timespec="seconds"), "out": out, "model": model, "exit": code, **entry}) + "\n")
sys.exit(code)

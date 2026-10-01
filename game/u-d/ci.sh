#!/usr/bin/env bash
# THROWAWAY (Phase 1 bake-off). Lane U-D has not started: it waits on Sami's one-time Unity Hub sign-in
# (bakeoff/u-d/LOG.md). With no Unity project there is nothing to build or test, so this fails on purpose.
set -euo pipefail
echo "u-d: no Unity project yet; the lane waits on Sami's Unity sign-in (see bakeoff/u-d/LOG.md)" >&2
exit 1

#!/usr/bin/env bash
# generate.sh — write every derivative of src/mark.svg (generate.py) in the
# pinned renderer, so a laptop and CI write the same bytes. The image is pinned
# by digest, and apt reads the Debian snapshot the image was built from (named
# in its sources' comments), so every package, rsvg-convert's libraries among
# them, is the version that image's date had.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd -P)"
IMAGE=debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc

source "$ROOT/build-tools/container-runtime.sh"
RUNTIME="$(detect_container_runtime)"
"$RUNTIME" run --rm --platform linux/amd64 \
  --volume "$ROOT:/brand" \
  "$IMAGE" bash -euc '
    # Each snapshot comment sits above the URIs line it stands for.
    sed -i -E "s|^# (http://snapshot\.debian\.org/\S+)$|URIs: \1|;T;n;d" /etc/apt/sources.list.d/debian.sources
    grep -q snapshot.debian.org /etc/apt/sources.list.d/debian.sources
    apt-get -o Acquire::Check-Valid-Until=false update -qq
    apt-get install -qq --no-install-recommends librsvg2-bin python3 >/dev/null
    python3 /brand/generate.py /brand
  '

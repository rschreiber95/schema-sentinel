#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir/.."

cleanup() {
  docker compose --profile test down --remove-orphans
}

trap cleanup EXIT

docker compose --profile test up \
  --build \
  --abort-on-container-exit \
  --exit-code-from roundtrip-test

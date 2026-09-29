#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  docker compose --profile test down --remove-orphans
}

trap cleanup EXIT

docker compose --profile test up \
  --build \
  --abort-on-container-exit \
  --exit-code-from roundtrip-test

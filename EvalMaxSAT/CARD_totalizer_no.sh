#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
./_run_batch.sh no_preprocessing CARD 6 6 "$@"

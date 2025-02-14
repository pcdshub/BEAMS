#! /bin/bash
set -e
THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "$THIS_DIR"
source venv/bin/activate
python3 -m beams.bin.beams_service "$@"

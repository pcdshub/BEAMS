#! /bin/bash
set -e
THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "$THIS_DIR/.."
if [ -d venv ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
    pip3 install .
fi
make gen_grpc
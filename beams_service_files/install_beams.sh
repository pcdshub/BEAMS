#! /bin/bash
set -e
THIS_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
cd "$THIS_DIR"
python3 -m venv venv
source venv/bin/activate
pip3 install $THIS_DIR/..

#!/usr/bin/bash
#
# This script can be used to regenerate the mfx example tree's json file and sim IOC.
#
# It does the following:
# 1. Sets up the Python environment
# 2. Loads mfx_tree.py to regenerate the json file
# 3. Runs beam's gen_test_ioc function to regenerate the sim IOC script

set -e

here="$(realpath "$(dirname ${BASH_SOURCE[0]})")"
cd "${here}"

source ./mfx_tree_env.sh

# Regenerate the tree
python mfx_tree.py

# Regenerate the sim ioc
python -m beams gen_test_ioc mfx_tree.json > mfx_sim.py

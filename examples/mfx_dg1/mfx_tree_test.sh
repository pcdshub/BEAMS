#!/usr/bin/bash
#
# This script can be used to do an offline test-run of the mfx example tree.
#
# It does the following:
# 1. Sets up the Python environment
# 2. Sets up some important environment variables for making sure the sims don't touch real hardware
# 3. Runs the simulator IOC, the behavior tree (in process), and a tree PV PyDM screen all at once.
# 4. Stops the IOC and BT when the PyDM screen is closed.
#
# If you've edited the tree definitions in mfx.py or you'd like to sync with the real system state
# Try running mfx_tree_gen.sh first

set -e

here="$(realpath "$(dirname ${BASH_SOURCE[0]})")"
cd "${here}"

source ./mfx_tree_env.sh

# Align with sim IOC, do not touch real devices on 5068!
export EPICS_CA_SERVER_PORT=5066
export EPICS_CA_AUTO_ADDR_LIST=NO
export EPICS_CA_ADDR_LIST=localhost

# This starts a subshell with three processes.
# The trap command will cause all three processes to close on sigint
# or when the foreground process (PyDM) closes
(
  trap 'kill 0' SIGINT EXIT;
  python mfx_sim.py &
  python -m beams run --tick-count 0 --tick-delay 2 mfx_tree.json &
  pydm mfx_tree_ui.py
)

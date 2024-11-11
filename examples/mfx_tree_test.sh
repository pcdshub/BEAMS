#!/usr/bin/bash
#
# This script can be used to do an offline test-run of the mfx example tree.
#
# It does the following:
# 1. Sets up a default conda environment if the user doesn't already have a conda or a venv activated
# 2. Includes this clone's beams package as the PYTHONPATH if PYTHONPATH is unset
# 3. Regenerates mfx_tree.json from the contents of mfx_sim.py to be used in future steps.
# 4. Runs the simulator IOC, the behavior tree (in process), and a tree PV PyDM screen all at once.
# 5. Stops the IOC and BT when the PyDM screen is closed.

set -e

here="$(realpath "$(dirname ${BASH_SOURCE[0]})")"
cd "${here}"

# If you don't have a conda env or a venv, let's use this one
if [[ -z "${CONDA_PREFiX}" ]] && [[ -z "${VIRTUAL_ENV}" ]]; then
  conda_bin="/cds/group/pcds/pyps/conda/py39/envs/pcds-5.9.1/bin/"
  export PATH="${conda_bin}:${PATH}"
fi
# If you didn't set up your python path, let's use this clone of beams
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH="$(realpath "${here}"/..)"
fi

# Align with sim IOC, do not touch real devices on 5068!
export EPICS_CA_SERVER_PORT=5066

python mfx_tree.py
(
  trap 'kill 0' SIGINT EXIT;
  python mfx_sim.py &
  python -m beams run --tick-count 0 --tick-delay 2 mfx_tree.json &
  pydm mfx_tree_ui.py
)

#!/usr/bin/bash
here="$(realpath "$(dirname ${BASH_SOURCE[0]})")"
cd "${here}"

if [ -z "${CONDA_PREFiX}" ]; then
  conda_bin="/cds/group/pcds/pyps/conda/py39/envs/pcds-5.9.1/bin/"
else
  # Make sure your env has pydm and caproto!
  conda_bin="${CONDA_PREFIX}/bin"
fi
export PATH="${conda_bin}:${PATH}"
export PYTHONPATH="$(realpath "${here}"/..)"
export EPICS_CA_SERVER_PORT=5066

python mfx_tree.py
(
  trap 'kill 0' SIGINT EXIT;
  python mfx_sim.py &
  python -m beams run --tick-count 0 --tick-delay 2 mfx_tree.json &
  pydm mfx_tree_ui.py
)

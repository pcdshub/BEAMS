#!/usr/bin/bash
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

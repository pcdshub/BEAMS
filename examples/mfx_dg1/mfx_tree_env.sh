#!/usr/bin/bash
#
# This sourceable script sets up a Python environment for running the mfx test tree.
#
# It does the following:
# 1. Sets up a default conda environment if the user doesn't already have a conda or a venv activated
# 2. Includes this clone's beams package as the PYTHONPATH if PYTHONPATH is unset

# If you don't have a conda env or a venv, let's use this one
if [[ -z "${CONDA_PREFiX}" ]] && [[ -z "${VIRTUAL_ENV}" ]]; then
  conda_bin="/cds/group/pcds/pyps/conda/py39/envs/pcds-5.9.1/bin/"
  export PATH="${conda_bin}:${PATH}"
fi
# If you didn't set up your python path, let's use this clone of beams
if [[ -z "${PYTHONPATH}" ]]; then
  export PYTHONPATH="$(realpath "${here}"/../..)"
fi

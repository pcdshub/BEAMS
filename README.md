# Beamline Engineering Automation Management Systems
Name pending.

## What is it
Framework for automating actions done by operators in a modular, procedural way such that we can conretize the intended set of actions we take to permutate beamline state and ensure our systems adhere to explicitly state sequencing logic.

More to come.

## High level documentation
[Link](https://www.figma.com/file/cWactF57tlhV3Wj5t4qTWq/High-Level-Architecture-Concepts?type=whiteboard&node-id=0%3A1&t=tdtB5ka79CpvdgvI-1)

## To setup
- clone to directory
- `mkdir venv && python -m venv venv`  make venv
- `source venv/bin/activate` activate venv
- `pip3 install requirements.txt`

# Makefile interface
* `make test` - runs tests in test directory
* `make test_verbose` - runs tests in test directory and prints stdout
* `make update_beams` - updates the locally install `beams` package
* `make flake8` - flake check source files
* `make gen_grpc` - generates all needed GRPC files
* `make docker_image` - builds rhel7 docker image with slac-epics base and BEAMS directory
* `make run_sequener` - launches sequencer engine

## Hanging TODOs:
- make a decorator for work functions in beams/sequencer/Worker.py that logs PID
- handle keyboard interrupt kill signal more elegantly
- can package Queue and Event in single object

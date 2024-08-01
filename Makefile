SHELL:=/bin/bash
VERSION=0x03

.PHONY: gen_grpc
gen_grpc:
	@python3 -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. beams/sequencer/remote_calls/sequencer.proto

.PHONY: update_beams
update_beams:
	@cd beams && pip install --editable ..

.PHONY: flake8
flake8:
	@python3 -m flake8 || true

.PHONY: test
test:
	@source venv/bin/activate && pytest beams/tests/Test*

.PHONY: test_verbose
test_verbose:
	@source venv/bin/activate && pytest --capture=tee-sys beams/tests/Test*

.PHONY: run_sequencer
run_sequencer:
	@source venv/bin/activate && python3 beams/sequencer/Sequencer.py

.PHONY: docker_build
docker_build:
	@docker build -f docker/Dockerfile --tag beams_playpen .

.PHONY: docker_run
docker_run:
	@docker run --rm -it --hostname "psbuild-rhel7" beams_playpen || true

SHELL:=/bin/bash
VERSION=0x03

.PHONY: gen_grpc
gen_grpc:
	@# This is a tough one to read I'm sorry. This grabs all our protofiles that aren't GRPC proto files
	@python3 -m grpc_tools.protoc -I . --python_out=. --pyi_out=. $(filter-out beams/service/remote_calls/beams_rpc.proto, $(wildcard beams/service/remote_calls/*.proto))
	@# This runs the GRPC proto on GRPC proto file
	@python3 -m grpc_tools.protoc -I . --python_out=. --pyi_out=. --grpc_python_out=. beams/service/remote_calls/beams_rpc.proto

.PHONY: update_beams
update_beams:
	@cd beams && pip install --editable ..

.PHONY: flake8
flake8:
	@python3 -m flake8 || true

.PHONY: test
test:
	@source venv/bin/activate && pytest

.PHONY: test_verbose
test_verbose:
	@source venv/bin/activate && pytest --capture=tee-sys

.PHONY: test_artifacts
test_artifacts:
	@python3 beams/tests/artifacts/egg_generator.py

.PHONY: run_sequencer
run_sequencer:
	@source venv/bin/activate && python3 beams/sequencer/Sequencer.py

.PHONY: docker_build
docker_build:
	@docker build -f docker/Dockerfile --tag beams_playpen .

.PHONY: docker_run
docker_run:
	@docker run --rm -it --hostname "psbuild-rhel7" beams_playpen || true

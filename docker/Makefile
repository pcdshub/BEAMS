SHELL:=/bin/bash
VERSION=0x03

.PHONY: gen_grpc
gen_grpc:
	@python3.6 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. beams/sequencer/remote_calls/sequencer.proto

.PHONY: update_beams
update_beams:
	@cd beams && pip install --editable ..

.PHONY: flake8
flake8:
	@python3.6 -m flake8 || true

.PHONY: test
test:
	@source venv/bin/activate && pytest tests/Test*.py

.PHONY: test_verbose
test_verbose:
	@source venv/bin/activate && pytest --capture=tee-sys tests/Test*.py

.PHONY: run_sequencer
run_sequencer:
	@source venv/bin/activate && python3.6 beams/sequencer/Sequencer.py

.PHONY: docker_image
docker_image:
		@docker build -f docker/Dockerfile --tag beams_playpen .

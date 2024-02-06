SHELL:=/bin/bash
VERSION=0x03


.PHONY: flake8
flake8:
	@python3 -m flake8 || true

.PHONY: test
test:
	@source venv/bin/activate && pytest tests/Test*.py
all: lint test

.ONESHELL:
.DEFAULT_GOAL: install

SHELL = bash
CPU_CORES = $(shell nproc)

VENV = .venv
$(VENV):
	python3 -m venv $(VENV)
	source $(VENV)/bin/activate
	$(MAKE) install

install: $(VENV)
	source $(VENV)/bin/activate
	pip install --upgrade pip setuptools wheel
	pip install --editable .[dev]

format: $(VENV)
	source $(VENV)/bin/activate
	black .
	isort . --profile black

lint: $(VENV)
	source $(VENV)/bin/activate
	black . --check
	isort . --profile black --check
	pylint --jobs=$(CPU_CORES) --output-format=colorized pyzabbix tests

test: $(VENV)
	source $(VENV)/bin/activate
	pytest -v \
		--numprocesses=$(CPU_CORES) \
		--color=yes \
		--cov-report=term \
		--cov=pyzabbix \
		tests

clean:
	rm -Rf $(VENV)

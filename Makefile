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
	pip install --upgrade pip setuptools wheel build
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
	mypy pyzabbix tests || true


PYTEST_CMD = pytest -v \
		--numprocesses=$(CPU_CORES) \
		--color=yes

test: $(VENV)
	source $(VENV)/bin/activate
	$(PYTEST_CMD) \
		--cov-config=./pyproject.toml \
		--cov-report=term \
		--cov-report=xml:./coverage.xml \
		--cov=pyzabbix \
		tests

.PHONY: e2e
e2e: $(VENV)
	source $(VENV)/bin/activate
	$(PYTEST_CMD) e2e

build: $(VENV)
	source $(VENV)/bin/activate
	python -m build .

release:
	./scripts/release.sh

clean:
	rm -Rf $(VENV) dist

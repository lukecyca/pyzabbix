all: lint test

.DEFAULT_GOAL: install

SHELL = bash
CPU_CORES = $(shell N=$$(nproc); echo $$(( $$N > 4 ? 4 : $$N )))

VENV = .venv
$(VENV):
	python3 -m venv $(VENV)
	$(MAKE) install

install: $(VENV)
	$(VENV)/bin/pip install --upgrade pip setuptools wheel build
	$(VENV)/bin/pip install --editable .[dev]

format: $(VENV)
	$(VENV)/bin/black .
	$(VENV)/bin/isort .

lint: $(VENV)
	$(VENV)/bin/black . --check
	$(VENV)/bin/isort . --check
	$(VENV)/bin/pylint --jobs=$(CPU_CORES) --output-format=colorized pyzabbix tests
	$(VENV)/bin/mypy pyzabbix tests


PYTEST_CMD = $(VENV)/bin/pytest -v \
		--numprocesses=$(CPU_CORES) \
		--color=yes

test: $(VENV)
	$(PYTEST_CMD) \
		--cov-config=./pyproject.toml \
		--cov-report=term \
		--cov-report=xml:./coverage.xml \
		--cov=pyzabbix \
		tests

.PHONY: e2e
e2e: $(VENV)
	$(PYTEST_CMD) e2e

build: $(VENV)
	$(VENV)/bin/python -m build .

release:
	./scripts/release.sh

clean:
	rm -Rf $(VENV) dist

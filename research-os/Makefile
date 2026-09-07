PYTHON=python

.PHONY: run install test

run:
	$(PYTHON) -m research_os.app.main

install:
	bash installer/install.sh

test:
	$(PYTHON) -m pytest -q

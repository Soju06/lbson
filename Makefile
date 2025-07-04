.PHONY: build install test test-fast test-benchmark test-coverage clean help

generate-stubs:
	pybind11-stubgen lbson._core --output-dir=src --enum-class-locations DecoderMode:lbson._core

build:
	pip install -e . -v
	$(MAKE) generate-stubs

install: build

install-test: build
	pip install -e .[test] -v

test: install-test
	python -m pytest tests/ -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

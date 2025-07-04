.PHONY: install build build-test test clean

generate-stubs:
	pybind11-stubgen lbson._core --output-dir=src --enum-class-locations DecoderMode:lbson._core

install:
	pip install -e . -v

build:
	pip install -e .[dev] -v
	$(MAKE) generate-stubs

build-test:
	pip install -e .[test] -v
	$(MAKE) generate-stubs

test:
	python -m pytest tests/ -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

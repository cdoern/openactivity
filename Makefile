.PHONY: install dev test lint format clean

install:
	pip install .

dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=openactivity --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

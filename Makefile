.PHONY: install test run fmt lint typecheck clean

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=mcp_server_aws --cov-report=term-missing

run:
	python -m mcp_server_aws

run-with-writes:
	python -m mcp_server_aws --allow-writes

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache dist build *.egg-info

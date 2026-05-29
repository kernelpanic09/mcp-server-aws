# Contributing

Pull requests are welcome. This is a personal portfolio project, so if you're planning something larger than a bug fix (like adding a new AWS service), please open an issue first to discuss it before putting in the work.

## Dev setup

```bash
git clone https://github.com/kernelpanic09/mcp-server-aws.git
cd mcp-server-aws

# Install with dev extras
uv pip install -e ".[dev]"

# Run tests (uses moto for AWS mocking, no real account needed)
pytest

# Lint
ruff check .

# Format
ruff format .

# Type check
pyright

# Run the server locally
make run
```

Tests use [moto](https://github.com/getmoto/moto) to mock AWS, so you don't need live credentials to run the test suite. If you're adding a new tool, add a test in `tests/` that covers the happy path and at least one error case.

## Commit style

This repo follows [Conventional Commits](https://www.conventionalcommits.org/). Examples:

- `fix: handle paginated results correctly in list_iam_roles`
- `feat: add route53 list hosted zones tool`
- `chore: bump moto to 5.x`
- `docs: clarify --allow-writes flag behavior`

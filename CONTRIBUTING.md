# Contributing

Thanks for helping improve Corey's Harness.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## Pull requests

Keep each change focused, add or update tests for behavior changes, and update the changelog or roadmap when a release-facing capability changes. Do not commit `.env` files, API keys, prompt logs, model files, or production audit data.

Tool integrations must begin read-only and include schemas, validation, timeouts, failure handling, audit events, and tests. Write-capable tools require a documented human-approval boundary.

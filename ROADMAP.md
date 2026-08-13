# Roadmap

This roadmap describes the intended direction for Corey's Harness. Planned features may change after testing and community feedback. A feature belongs in the current release only after it is implemented, tested, and documented.

## v0.1.0 — Public Preview

Status: current release.

- OpenAI-compatible chat and model-list endpoints.
- Deterministic general, coding, and security routing.
- Streaming and non-streaming Ollama responses.
- Advisory-only policy enforcement.
- Metadata-focused JSONL audit logging.
- Optional bearer-key authentication.
- Docker Compose deployment.

## v0.2.0 — Read-only tools and web search

- Read-only tool registry with explicit schemas and timeouts.
- Provider-configurable web search, beginning with a SearXNG-compatible adapter.
- Search-result source metadata returned to the model.
- Domain allowlists, result limits, and auditable tool calls.
- Read-only security-report and failed-login summary tools.
- Tests for tool validation, provider failures, and untrusted search content.

## v0.3.0 — Approval workflow

- Human approval queue for proposed write actions.
- Per-tool authorization rules and risk labels.
- Request cancellation, timeout, and replay protection.
- Structured tool-result validation and expanded audit events.

## v0.4.0 — Extensibility

- Pluggable model and tool providers.
- Configuration validation and migration helpers.
- Additional routing strategies and evaluation fixtures.
- Packaged observability metrics and deployment examples.

## v1.0.0 — Stable release

- Stable configuration and API compatibility policy.
- Threat model and documented security boundaries.
- Broader integration, load, and failure-recovery tests.
- Upgrade documentation and supported deployment profiles.

# Changelog

All notable changes to Corey's Harness will be documented in this file. The project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-08-13

### Added

- OpenAI-compatible model-list and chat-completions endpoints.
- Automatic routing for general, coding, and security prompts.
- Explicit model-route aliases and a route-preview endpoint.
- Streaming and non-streaming Ollama proxy support.
- Advisory-only policy enforcement with tool execution disabled.
- Metadata-focused JSONL audit logging with optional prompt logging.
- Optional bearer-key authentication.
- Docker Compose and local Python development workflows.
- Public documentation, roadmap, security policy, contribution guide, and CI checks.

### Security

- Localhost-only Docker port binding by default.
- Constant-time API-key comparison.
- Prompt content excluded from audit logs by default.

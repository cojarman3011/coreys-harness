# Security Policy

## Supported versions

Corey's Harness is currently a public preview. Security fixes are provided for the latest published version only.

## Reporting a vulnerability

Do not open a public issue containing exploit details, credentials, prompt data, internal addresses, or audit records. Report suspected vulnerabilities privately to `info@skylinee.co` with the affected version, impact, reproduction steps, and any suggested mitigation. Please allow reasonable time for investigation before public disclosure.

## Deployment guidance

- Keep the default localhost binding unless remote access is required.
- Configure a long, unique `SKYLINEE_API_KEY` before exposing the service.
- Do not expose Ollama directly to the public internet.
- Place remote deployments behind TLS, access controls, and a firewall or trusted reverse proxy.
- Keep `SKYLINEE_LOG_PROMPT_CONTENT=false` unless prompt retention is explicitly required and protected.
- Treat model output and future tool output as untrusted data requiring human review.
- Do not enable write-capable tools without authentication, authorization, validation, timeouts, approval, and auditable execution.

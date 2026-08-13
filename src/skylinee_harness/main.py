import json
import secrets
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from . import __version__
from .audit import AuditLogger
from .config import Settings, get_settings
from .policy import PolicyViolation, enforce_advisory_policy
from .router import RouteDecision, route_request


def require_api_key(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key:
        return
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    supplied = authorization[len(prefix) :]
    if not secrets.compare_digest(supplied, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.audit = AuditLogger(settings.audit_log_path, settings.log_prompt_content)
    yield


app = FastAPI(
    title="Corey's Harness",
    version=__version__,
    description="Local-first model routing and governance for Open WebUI and Ollama.",
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/v1/models", dependencies=[Depends(require_api_key)])
async def list_models(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    names = ["skylinee-auto", "skylinee-general", "skylinee-code", "skylinee-security"]
    return {
        "object": "list",
        "data": [
            {"id": name, "object": "model", "created": 0, "owned_by": "skylinee"}
            for name in names
        ],
    }


@app.post("/v1/routes/preview", dependencies=[Depends(require_api_key)])
async def preview_route(request: Request, settings: Settings = Depends(get_settings)) -> dict[str, str]:
    payload = await _read_chat_payload(request)
    decision = route_request(payload.get("model", "skylinee-auto"), payload["messages"], settings)
    return {
        "requested_model": payload.get("model", "skylinee-auto"),
        "category": decision.category,
        "selected_model": decision.model,
        "reason": decision.reason,
    }


@app.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
async def chat_completions(request: Request, settings: Settings = Depends(get_settings)):
    original_payload = await _read_chat_payload(request)
    request_id = f"skylinee-{uuid.uuid4()}"
    started = time.monotonic()

    decision = route_request(
        original_payload.get("model", "skylinee-auto"),
        original_payload["messages"],
        settings,
    )
    try:
        payload = enforce_advisory_policy(original_payload)
    except PolicyViolation as exc:
        _audit(request, request_id, decision, started, "policy_denied", original_payload)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    payload["model"] = decision.model
    upstream_url = f"{settings.ollama_base_url.rstrip('/')}/v1/chat/completions"

    if payload.get("stream", False):
        return await _stream_response(
            request,
            upstream_url,
            payload,
            original_payload,
            request_id,
            decision,
            started,
            settings,
        )
    return await _json_response(
        request,
        upstream_url,
        payload,
        original_payload,
        request_id,
        decision,
        started,
        settings,
    )


async def _read_chat_payload(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise HTTPException(status_code=422, detail="messages must be an array")
    return payload


async def _json_response(
    request: Request,
    upstream_url: str,
    payload: dict[str, Any],
    original_payload: dict[str, Any],
    request_id: str,
    decision: RouteDecision,
    started: float,
    settings: Settings,
) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(upstream_url, json=payload)
            response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        _audit(request, request_id, decision, started, "upstream_error", original_payload, str(exc))
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    _audit(request, request_id, decision, started, "completed", original_payload)
    return JSONResponse(
        content=body,
        headers={
            "X-Skylinee-Request-ID": request_id,
            "X-Skylinee-Route": decision.category,
            "X-Skylinee-Model": decision.model,
        },
    )


async def _stream_response(
    request: Request,
    upstream_url: str,
    payload: dict[str, Any],
    original_payload: dict[str, Any],
    request_id: str,
    decision: RouteDecision,
    started: float,
    settings: Settings,
) -> StreamingResponse:
    client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
    try:
        upstream = await client.send(
            client.build_request("POST", upstream_url, json=payload),
            stream=True,
        )
        upstream.raise_for_status()
    except httpx.HTTPError as exc:
        await client.aclose()
        _audit(request, request_id, decision, started, "upstream_error", original_payload, str(exc))
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    async def iterator() -> AsyncIterator[bytes]:
        outcome = "completed"
        error: str | None = None
        try:
            async for chunk in upstream.aiter_bytes():
                yield chunk
        except Exception as exc:  # Streaming failures must still reach the audit trail.
            outcome = "stream_error"
            error = str(exc)
            raise
        finally:
            await upstream.aclose()
            await client.aclose()
            _audit(request, request_id, decision, started, outcome, original_payload, error)

    return StreamingResponse(
        iterator(),
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "text/event-stream"),
        headers={
            "X-Skylinee-Request-ID": request_id,
            "X-Skylinee-Route": decision.category,
            "X-Skylinee-Model": decision.model,
        },
    )


def _audit(
    request: Request,
    request_id: str,
    decision: RouteDecision,
    started: float,
    outcome: str,
    payload: dict[str, Any],
    error: str | None = None,
) -> None:
    event = {
        "request_id": request_id,
        "route": decision.category,
        "model": decision.model,
        "route_reason": decision.reason,
        "outcome": outcome,
        "latency_ms": round((time.monotonic() - started) * 1000, 2),
    }
    if error:
        event["error"] = error
    request.app.state.audit.write(event, payload)

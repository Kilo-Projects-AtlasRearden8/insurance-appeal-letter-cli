"""OpenAI-compatible chat client with a local-first default (Ollama).

No API keys are required. The endpoint is configurable via CLI flags or
environment variables. All HTTP traffic is local unless the user explicitly
configures a remote endpoint.
"""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"
DEFAULT_TIMEOUT_SECONDS = 120


def _env_or_default(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is not None and value.strip() != "":
        return value.strip()
    return default


def resolve_base_url(explicit: str | None = None) -> str:
    """Resolve the OpenAI-compatible base URL.

    Precedence: explicit CLI flag > OLLAMA_BASE_URL / INSURANCE_APPEAL_BASE_URL
    > default localhost Ollama URL.
    """
    if explicit:
        return explicit.rstrip("/")
    for name in ("OLLAMA_BASE_URL", "INSURANCE_APPEAL_BASE_URL"):
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip().rstrip("/")
    return DEFAULT_BASE_URL


def resolve_model(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for name in ("OLLAMA_MODEL", "INSURANCE_APPEAL_MODEL"):
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return DEFAULT_MODEL


def chat(
    messages: list[dict[str, str]],
    *,
    base_url: str | None = None,
    model: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    temperature: float = 0.2,
    stream: bool = False,
) -> str:
    """Send a chat completion request to an OpenAI-compatible endpoint.

    Uses the standard library `urllib` so there are no third-party
    dependencies. Returns the assistant message content as a string.
    Raises RuntimeError on transport or API errors.
    """
    from urllib import error, request

    url = resolve_base_url(base_url).rstrip("/") + "/v1/chat/completions"
    model_name = resolve_model(model)

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - local endpoints only
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:  # pragma: no cover - depends on server
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body or exc.reason}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Request to {url} failed: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from {url}: {raw[:200]!r}") from exc

    if not isinstance(parsed, dict) or "choices" not in parsed:
        raise RuntimeError(f"Unexpected response shape from {url}: {raw[:200]!r}")

    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError(f"Empty choices in response from {url}")

    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError(f"Malformed choice in response from {url}")

    message = first.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"Empty assistant content in response from {url}")

    return content.strip()


def healthcheck(base_url: str | None = None, timeout: int = 10) -> bool:
    """Return True if the endpoint responds to a models listing."""
    from urllib import request

    url = resolve_base_url(base_url).rstrip("/") + "/v1/models"
    req = request.Request(url, headers={"Accept": "application/json"}, method="GET")  # noqa: S310
    try:
        with request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False

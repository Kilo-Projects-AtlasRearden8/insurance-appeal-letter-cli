"""Insurance denial appeal letter CLI.

Drafts appeal letters from policy and claim details using a configurable
OpenAI-compatible endpoint (default Ollama). Education-only: never medical,
legal, or financial advice. Never sends automatically.
"""

from .client import chat, healthcheck, resolve_base_url, resolve_model
from .disclaimer import DISCLAIMER, render_disclaimer
from .models import (
    AppealRequest,
    Claim,
    DenialReason,
    Policyholder,
)
from .templates import SYSTEM_PROMPT, assemble_letter, build_prompt

__version__ = "1.0.0"

__all__ = [
    "SYSTEM_PROMPT",
    "AppealRequest",
    "Claim",
    "DenialReason",
    "DISCLAIMER",
    "Policyholder",
    "assemble_letter",
    "build_prompt",
    "chat",
    "healthcheck",
    "render_disclaimer",
    "resolve_base_url",
    "resolve_model",
]

"""Test fixtures: mock OpenAI-compatible endpoint and sample request data."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from insurance_appeal.models import (
    AppealRequest,
    Claim,
    DenialReason,
    Policyholder,
)


class _MockHandler(BaseHTTPRequestHandler):
    """Minimal OpenAI-compatible chat completions mock."""

    def do_POST(self) -> None:  # noqa: N802 - http.server naming convention
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length).decode("utf-8", errors="replace")

        if self.path == "/v1/chat/completions":
            response = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "DRAFT APPEAL LETTER (mocked)\n\n"
                                "This is a mock response for testing."
                            ),
                        }
                    }
                ]
            }
            self._send_json(response)
        elif self.path == "/v1/models":
            self._send_json({"data": [{"id": "mock-model"}]})
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._send_json({"data": [{"id": "mock-model"}]})
        else:
            self._send_json({"error": "not found"}, status=404)

    def _send_json(self, obj: Any, status: int = 200) -> None:
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # noqa: D401 - silence server logs
        pass


class MockEndpoint:
    """Context manager running a real HTTP mock on an ephemeral port."""

    def __init__(self) -> None:
        self.server: HTTPServer = HTTPServer(("127.0.0.1", 0), _MockHandler)
        self.port: int = self.server.server_address[1]
        self.base_url: str = f"http://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> MockEndpoint:
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def mock_endpoint():
    with MockEndpoint() as ep:
        yield ep


@pytest.fixture
def sample_request() -> AppealRequest:
    return AppealRequest(
        policyholder=Policyholder(
            full_name="Jane Doe",
            date_of_birth="1980-01-01",
            member_id="MEM123456",
            address="123 Main St, Indianapolis, IN 46202",
            phone="317-555-0100",
        ),
        claim=Claim(
            claim_number="CLM-99999",
            date_of_service="2026-01-15",
            provider="Meridian Health",
            procedure_codes="99213",
            diagnosis_codes="E11.9",
            amount_charged="250.00",
            amount_paid="0.00",
            denial_reason=DenialReason.NOT_MEDICALLY_NECESSARY,
            denial_reason_detail="Service deemed not medically necessary.",
        ),
        clinical_notes="Patient presents with uncontrolled type 2 diabetes.",
        supporting_docs="Medical records, physician letter of necessity.",
        requested_action="reverse the denial and authorize payment",
        tone="professional",
        extra_context="Patient is appealing within the deadline.",
    )

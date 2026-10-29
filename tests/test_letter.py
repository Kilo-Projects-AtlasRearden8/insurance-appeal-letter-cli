"""Tests for letter templates and drafting logic."""

from __future__ import annotations

from insurance_appeal.models import (
    AppealRequest,
    Claim,
    DenialReason,
    Policyholder,
)
from insurance_appeal.templates import assemble_letter, build_prompt


def _sample_request() -> AppealRequest:
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


def test_build_prompt_uses_facts():
    prompt = build_prompt(_sample_request())
    assert "Jane Doe" in prompt
    assert "CLM-99999" in prompt
    assert "99213" in prompt
    assert "E11.9" in prompt
    assert "Not medically necessary" in prompt
    assert "Meridian Health" in prompt


def test_assemble_letter_contains_disclaimer():
    prompt = build_prompt(_sample_request())
    letter = assemble_letter(prompt)
    assert "EDUCATION-ONLY DISCLAIMER" in letter
    assert "NOT legal, financial, or medical" in letter
    assert "medical" in letter and "advice" in letter


def test_models_defaults():
    claim = Claim(claim_number="X", date_of_service="2026-01-01", provider="P")
    assert claim.amount_paid == "0.00"
    assert claim.denial_reason == DenialReason.OTHER

    assert (
        DenialReason.from_label("Not medically necessary")
        == DenialReason.NOT_MEDICALLY_NECESSARY
    )
    assert DenialReason.from_label("weird unknown") == DenialReason.OTHER

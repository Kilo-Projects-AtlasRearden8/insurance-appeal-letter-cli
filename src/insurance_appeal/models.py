"""Data models for insurance appeal letter drafting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DenialReason(str, Enum):
    """Common insurance denial reasons. Values are human-friendly labels."""

    NOT_MEDICALLY_NECESSARY = "Not medically necessary"
    OUT_OF_NETWORK = "Out of network"
    EXPERIMENTAL_INVESTIGATIONAL = "Experimental / investigational"
    PRIOR_AUTH_MISSING = "Prior authorization not obtained"
    DUPLICATE_BILLING = "Duplicate billing"
    NO_COVERAGE_AT_SERVICE_DATE = "No coverage at date of service"
    EXCLUSIONS = "Plan exclusions / limitations"
    MAX_BENEFITS_EXCEEDED = "Maximum benefits exceeded"
    CLAIM_REJECTED = "Claim rejected (formalities / coding)"
    OTHER = "Other"

    @classmethod
    def from_label(cls, label: str) -> DenialReason:
        for member in cls:
            if member.value.lower() == label.strip().lower():
                return member
        return cls.OTHER


@dataclass
class Policyholder:
    full_name: str
    date_of_birth: str
    member_id: str
    address: str = ""
    phone: str = ""


@dataclass
class Claim:
    claim_number: str
    date_of_service: str
    provider: str
    procedure_codes: str = ""
    diagnosis_codes: str = ""
    amount_charged: str = ""
    amount_paid: str = "0.00"
    denial_reason: DenialReason = DenialReason.OTHER
    denial_reason_detail: str = ""


@dataclass
class AppealRequest:
    policyholder: Policyholder
    claim: Claim
    clinical_notes: str = ""
    supporting_docs: str = ""
    requested_action: str = "Reconsider the denial and pay the claim"
    tone: str = "professional"
    extra_context: str = ""

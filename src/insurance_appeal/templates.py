"""Prompt templates and letter drafting logic."""

from __future__ import annotations

from .disclaimer import DISCLAIMER
from .models import AppealRequest, Policyholder

SYSTEM_PROMPT = (
    "You are an experienced insurance appeals specialist. Your job is to draft "
    "clear, professional, and persuasive appeal letters for health insurance "
    "denials. Use only the facts provided. Do not invent medical facts, codes, "
    "dates, or clinical details. If information is missing, leave a clear "
    "placeholder like [INSERT ...] rather than making it up. Never give "
    "medical advice. Keep the letter factual, respectful, and structured."
)

SYSTEM_PROMPT = (
    "You are an experienced insurance appeals specialist. Your job is to draft "
    "clear, professional, and persuasive appeal letters for health insurance "
    "denials. Use only the facts provided. Do not invent medical facts, codes, "
    "dates, or clinical details. If information is missing, leave a clear "
    "placeholder like [INSERT ...] rather than making it up. Never give "
    "medical advice. Keep the letter factual, respectful, and structured."
)

USER_PROMPT_TEMPLATE = """Draft a formal appeal letter for a denied health insurance claim.

Use this structure:
1. Header with policyholder name, address, member ID, date, and claim number.
2. Opening paragraph stating that this is an appeal of a denial.
3. Summary of the claim: date of service, provider, procedure codes,
   diagnosis codes, and amounts.
4. The specific denial reason being appealed, with a brief explanation of
   why the denial should be reconsidered based on the facts provided.
5. Requested action.
6. List of supporting documentation being enclosed.
7. Closing with signature block placeholders.
8. A clear note that the letter was drafted for educational/administrative
   use only.

Facts:
- Policyholder: {policyholder_name}
- Date of birth: {dob}
- Member ID: {member_id}
- Address: {address}
- Phone: {phone}
- Claim number: {claim_number}
- Date of service: {date_of_service}
- Provider: {provider}
- Procedure codes: {procedure_codes}
- Diagnosis codes: {diagnosis_codes}
- Amount charged: {amount_charged}
- Amount paid: {amount_paid}
- Denial reason: {denial_reason}
- Denial reason detail: {denial_reason_detail}
- Requested action: {requested_action}
- Supporting documents: {supporting_docs}
- Clinical notes: {clinical_notes}
- Extra context: {extra_context}

Rules:
- Only use facts listed above. Do not invent anything.
- Use [INSERT ...] for any missing fact.
- Keep tone: {tone}.
- The letter must be complete and ready to print.
"""


def _format_address(policyholder: Policyholder) -> str:
    parts = [policyholder.address.strip()] if policyholder.address else []
    if policyholder.phone:
        parts.append("Phone: " + policyholder.phone.strip())
    if not parts:
        return "[INSERT address]"
    return "\n".join(parts)


def build_prompt(request: AppealRequest) -> str:
    """Build the user prompt from an AppealRequest."""
    return USER_PROMPT_TEMPLATE.format(
        policyholder_name=request.policyholder.full_name.strip() or "[INSERT policyholder name]",
        dob=request.policyholder.date_of_birth.strip() or "[INSERT date of birth]",
        member_id=request.policyholder.member_id.strip() or "[INSERT member ID]",
        address=_format_address(request.policyholder),
        phone=request.policyholder.phone.strip() or "[INSERT phone]",
        claim_number=request.claim.claim_number.strip() or "[INSERT claim number]",
        date_of_service=request.claim.date_of_service.strip() or "[INSERT date of service]",
        provider=request.claim.provider.strip() or "[INSERT provider name]",
        procedure_codes=request.claim.procedure_codes.strip() or "[INSERT procedure codes]",
        diagnosis_codes=request.claim.diagnosis_codes.strip() or "[INSERT diagnosis codes]",
        amount_charged=request.claim.amount_charged.strip() or "[INSERT amount charged]",
        amount_paid=request.claim.amount_paid.strip() or "0.00",
        denial_reason=request.claim.denial_reason.value,
        denial_reason_detail=request.claim.denial_reason_detail.strip() or "[INSERT denial detail]",
        requested_action=request.requested_action.strip() or "[INSERT requested action]",
        supporting_docs=request.supporting_docs.strip() or "[INSERT supporting documents]",
        clinical_notes=request.clinical_notes.strip() or "[INSERT clinical notes]",
        extra_context=request.extra_context.strip() or "None provided.",
        tone=request.tone.strip() or "professional",
    )


def assemble_letter(body: str) -> str:
    """Wrap the LLM-generated body with the education-only disclaimer."""
    return body.rstrip() + "\n\n" + DISCLAIMER

"""Command-line interface for drafting insurance denial appeal letters."""

from __future__ import annotations

import argparse
import json
import sys

from .client import chat, healthcheck, resolve_base_url
from .models import AppealRequest, Claim, DenialReason, Policyholder
from .templates import SYSTEM_PROMPT, assemble_letter, build_prompt


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="insurance-appeal",
        description=(
            "Draft an insurance denial appeal letter from policy and claim "
            "details using a configurable OpenAI-compatible endpoint "
            "(default Ollama). Education-only. Never sends automatically."
        ),
    )

    # Core details
    parser.add_argument("--policyholder-name", help="Name of the policyholder")
    parser.add_argument("--dob", help="Date of birth")
    parser.add_argument("--member-id", help="Member ID")
    parser.add_argument("--address", help="Mailing address")
    parser.add_argument("--phone", help="Phone number")

    parser.add_argument("--claim-number", help="Claim number")
    parser.add_argument("--date-of-service", help="Date of service")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--procedure-codes", help="Procedure codes (e.g. CPT)")
    parser.add_argument("--diagnosis-codes", help="Diagnosis codes (e.g. ICD-10)")
    parser.add_argument("--amount-charged", help="Amount charged")
    parser.add_argument("--amount-paid", default="0.00", help="Amount paid")
    parser.add_argument("--denial-reason", help="Denial reason (label or index)")
    parser.add_argument("--denial-reason-detail", help="Detail about the denial")

    # Appeal details
    parser.add_argument("--clinical-notes", default="", help="Clinical notes")
    parser.add_argument("--supporting-docs", default="", help="Supporting documents")
    parser.add_argument("--requested-action", default="Reconsider the denial and pay the claim")
    parser.add_argument("--tone", default="professional", help="Letter tone")
    parser.add_argument("--extra-context", default="", help="Extra context")

    # Endpoint / model
    parser.add_argument("--endpoint", default=None, help="OpenAI-compatible base URL")
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--no-llm", action="store_true", help="Use built-in template only")
    parser.add_argument("--healthcheck", action="store_true", help="Check endpoint then exit")

    # Output
    parser.add_argument("--output", help="Write letter to this file")
    parser.add_argument("--from", dest="from_file", help="Read details from a JSON file")

    return parser.parse_args(argv)


def _load_json_file(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _build_request(ns: argparse.Namespace) -> AppealRequest:
    policyholder = Policyholder(
        full_name=ns.policyholder_name or "",
        date_of_birth=ns.dob or "",
        member_id=ns.member_id or "",
        address=ns.address or "",
        phone=ns.phone or "",
    )
    denial_reason = DenialReason.OTHER
    if ns.denial_reason:
        denial_reason = DenialReason.from_label(ns.denial_reason)
    claim = Claim(
        claim_number=ns.claim_number or "",
        date_of_service=ns.date_of_service or "",
        provider=ns.provider or "",
        procedure_codes=ns.procedure_codes or "",
        diagnosis_codes=ns.diagnosis_codes or "",
        amount_charged=ns.amount_charged or "",
        amount_paid=ns.amount_paid or "0.00",
        denial_reason=denial_reason,
        denial_reason_detail=ns.denial_reason_detail or "",
    )
    return AppealRequest(
        policyholder=policyholder,
        claim=claim,
        clinical_notes=ns.clinical_notes,
        supporting_docs=ns.supporting_docs,
        requested_action=ns.requested_action,
        tone=ns.tone,
        extra_context=ns.extra_context,
    )


def _render_built_in_template(request: AppealRequest) -> str:
    """Deterministic template-based letter when no LLM is used."""
    lines: list[str] = []
    lines.append(request.policyholder.full_name or "[INSERT policyholder name]")
    if request.policyholder.address:
        lines.append(request.policyholder.address)
    lines.append("")
    lines.append("Date: [INSERT date]")
    lines.append("")
    lines.append("Insurance Appeals Department")
    lines.append("[INSERT insurer name]")
    lines.append("[INSERT insurer address]")
    lines.append("")
    lines.append("RE: Appeal of Denied Claim")
    lines.append(f"Claim Number: {request.claim.claim_number or '[INSERT claim number]'}")
    lines.append(f"Policyholder: {request.policyholder.full_name or '[INSERT name]'}")
    lines.append(f"Member ID: {request.policyholder.member_id or '[INSERT member ID]'}")
    lines.append(f"Date of Service: {request.claim.date_of_service or '[INSERT date]'}")
    lines.append(f"Provider: {request.claim.provider or '[INSERT provider]'}")
    lines.append("")
    lines.append("Dear Appeals Team,")
    lines.append("")
    lines.append(
        "I am writing to formally appeal the denial of the claim referenced "
        "above. The denial reason stated was: "
        f"{request.claim.denial_reason.value}."
    )
    if request.claim.denial_reason_detail:
        lines.append(f"Detail: {request.claim.denial_reason_detail}")
    lines.append("")
    lines.append(
        "I respectfully request that you reconsider this denial and "
        f"{request.requested_action.lower()}."
    )
    if request.clinical_notes:
        lines.append("")
        lines.append("Clinical notes:")
        lines.append(request.clinical_notes)
    if request.supporting_docs:
        lines.append("")
        lines.append("Supporting documents:")
        lines.append(request.supporting_docs)
    lines.append("")
    lines.append("Thank you for your time and consideration.")
    lines.append("")
    lines.append("Sincerely,")
    lines.append("")
    lines.append("_________________________")
    lines.append(request.policyholder.full_name or "[INSERT signature]")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)

    if ns.from_file:
        data = _load_json_file(ns.from_file)
        # Convert flat JSON fields to fields
        ns.policyholder_name = data.get("policyholder_name", ns.policyholder_name)
        ns.dob = data.get("dob", ns.dob)
        ns.member_id = data.get("member_id", ns.member_id)
        ns.address = data.get("address", ns.address)
        ns.phone = data.get("phone", ns.phone)
        ns.claim_number = data.get("claim_number", ns.claim_number)
        ns.date_of_service = data.get("date_of_service", ns.date_of_service)
        ns.provider = data.get("provider", ns.provider)
        ns.procedure_codes = data.get("procedure_codes", ns.procedure_codes)
        ns.diagnosis_codes = data.get("diagnosis_codes", ns.diagnosis_codes)
        ns.amount_charged = data.get("amount_charged", ns.amount_charged)
        ns.amount_paid = data.get("amount_paid", ns.amount_paid)
        ns.denial_reason = data.get("denial_reason", ns.denial_reason)
        ns.denial_reason_detail = data.get("denial_reason_detail", ns.denial_reason_detail)
        ns.clinical_notes = data.get("clinical_notes", ns.clinical_notes)
        ns.supporting_docs = data.get("supporting_docs", ns.supporting_docs)
        ns.requested_action = data.get("requested_action", ns.requested_action)
        ns.tone = data.get("tone", ns.tone)
        ns.extra_context = data.get("extra_context", ns.extra_context)
        ns.endpoint = data.get("endpoint", ns.endpoint)
        ns.model = data.get("model", ns.model)

    if ns.healthcheck:
        base_url = resolve_base_url(ns.endpoint)
        ok = healthcheck(base_url=base_url)
        print(f"Endpoint {base_url}: {'reachable' if ok else 'unreachable'}")
        return 0 if ok else 1

    request = _build_request(ns)

    if ns.no_llm:
        body = _render_built_in_template(request)
    else:
        prompt = build_prompt(request)
        try:
            body = chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                base_url=ns.endpoint,
                model=ns.model,
            )
        except RuntimeError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            print(
                "Tip: use --no-llm to draft a template letter without an endpoint.",
                file=sys.stderr,
            )
            return 1

    letter = assemble_letter(body)
    print(letter)

    if ns.output:
        with open(ns.output, "w", encoding="utf-8") as fh:
            fh.write(letter)
        print(f"\nLetter written to {ns.output}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

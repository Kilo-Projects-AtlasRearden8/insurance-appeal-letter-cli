# STATUS

## What was built

A local-first Python CLI (`insurance-appeal`) that drafts insurance denial
appeal letters from policy and claim details using a configurable
OpenAI-compatible endpoint (default Ollama).

- Drafts formal appeal letters from policyholder, claim, denial reason,
  procedure/diagnosis codes, amounts, clinical notes, and supporting docs.
- Configurable endpoint via `--endpoint`, `--model`, `OLLAMA_BASE_URL`,
  `OLLAMA_MODEL`, `INSURANCE_APPEAL_BASE_URL`, `INSURANCE_APPEAL_MODEL`.
- Defaults to local Ollama (`http://localhost:11434`); no API keys required.
- `--no-llm` mode uses a built-in template so the tool works without any LLM
  endpoint.
- `--healthcheck` verifies endpoint reachability then exits.
- `--from <json>` reads details from a JSON file; `--output <file>` writes the
  letter to disk (also printed to stdout).
- **Education-only disclaimer printed on every output.** Never medical, legal,
  or financial advice.
- **Never sends automatically.** The letter is printed for your review; you
  decide whether and when to submit it.
- No secrets, API keys, or personal data in the repository. No
  `.github/workflows`. MIT licensed.

## Project layout

```
insurance-appeal-letter-cli/
├── LICENSE
├── README.md
├── STATUS.md
├── pyproject.toml
├── src/insurance_appeal/
│   ├── __init__.py
│   ├── cli.py          # argparse CLI entry point
│   ├── client.py       # OpenAI-compatible chat client (stdlib urllib)
│   ├── disclaimer.py   # education-only disclaimer
│   ├── models.py       # Policyholder, Claim, AppealRequest, DenialReason
│   ├── templates.py    # SYSTEM_PROMPT, build_prompt, assemble_letter
│   └── py.typed
└ tests/
    ├── conftest.py     # mock OpenAI-compatible endpoint fixture
    ├── test_client.py  # LLM client + mock endpoint tests
    ├── test_letter.py  # template / drafting logic tests
    └── test_cli.py     # CLI end-to-end tests
```

## How to run

Install (creates/uses a venv is recommended):

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Draft a letter with the built-in template (no endpoint needed):

```bash
.venv/bin/insurance-appeal --no-llm \
  --policyholder-name "Jane Doe" \
  --member-id "MEM123456" \
  --claim-number "CLM-99999" \
  --date-of-service "2026-01-15" \
  --provider "Meridian Health" \
  --denial-reason "Not medically necessary" \
  --output letter.txt
```

Draft using a local Ollama endpoint:

```bash
.venv/bin/insurance-appeal \
  --policyholder-name "Jane Doe" \
  --claim-number "CLM-99999" \
  --denial-reason "Not medically necessary" \
  --output letter.txt
```

Check endpoint reachability:

```bash
.venv/bin/insurance-appeal --healthcheck
```

## Verification results

- Package installs cleanly in editable mode (`pip install -e ".[dev]"`).
- `pytest`: **12 passed** (client, letter/template, CLI tests).
- `ruff check`: **all checks passed** (no lint errors).
- Tests use a real mock HTTP server on an ephemeral port; no API keys, no
  network, no secrets.
- CLI `--no-llm` end-to-end verified: letter written to file and stdout,
  disclaimer present.

## Known gaps

- No remote LLM endpoint is available in this environment, so the Ollama
  code path is exercised only via the mock endpoint in tests (not against a
  live Ollama server).
- No type checker (mypy/pyright) is configured; the code is annotated but
  not statically type-checked in CI (there is no CI).
- The built-in `--no-llm` template is basic; the LLM path produces richer
  letters but depends on the endpoint/model quality.
- No packaging/publish step (intentionally: never publish).

## About

Built and maintained by **Asdale Dynamics, LLC** (Indiana, formed October
2026) — beginner-friendly AI education, books and guides, and practical
tools. Founder Dylan Asdale is a registered nurse turned AI author; his book
*The Massive AI Manual* and hub site dylanasdale.github.io explain AI "like a
friend would": plain English, step by step, never condescending.

Copyright (c) 2026 Asdale Dynamics, LLC
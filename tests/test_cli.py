"""Tests for the CLI entry point."""

from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "insurance_appeal.cli", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_no_llm_produces_letter_with_disclaimer():
    result = run_cli(
        "--no-llm",
        "--policyholder-name", "Jane Doe",
        "--member-id", "MEM123",
        "--claim-number", "CLM-1",
        "--date-of-service", "2026-01-15",
        "--provider", "Meridian Health",
        "--denial-reason", "Not medically necessary",
        "--output", "/tmp/kilo/test_letter_no_llm.txt",
    )
    assert result.returncode == 0, result.stderr
    combined = result.stdout + result.stderr
    assert "EDUCATION-ONLY DISCLAIMER" in combined
    assert "Dear Appeals Team" in combined
    assert "Jane Doe" in combined
    assert "CLM-1" in combined


def test_no_llm_writes_output_file():
    result = run_cli(
        "--no-llm",
        "--policyholder-name", "Jane Doe",
        "--claim-number", "CLM-1",
        "--output", "/tmp/kilo/test_letter_file.txt",
    )
    assert result.returncode == 0, result.stderr
    with open("/tmp/kilo/test_letter_file.txt", encoding="utf-8") as fh:
        content = fh.read()
    assert "EDUCATION-ONLY DISCLAIMER" in content


def test_healthcheck_fails_gracefully_without_endpoint():
    result = run_cli("--healthcheck")
    assert result.returncode == 1
    assert "unreachable" in result.stdout


def test_disclaimer_always_printed():
    result = run_cli("--no-llm", "--policyholder-name", "Jane Doe")
    assert result.returncode == 0
    assert "EDUCATION-ONLY DISCLAIMER" in result.stdout

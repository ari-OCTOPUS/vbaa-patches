"""RED contract: ArtifactAdmission on fixture artifacts only.

Sources for locked behaviour (not invention):
- User prompt 2026-09-08 named reject classes: unsigned, wrong type, path escape, empty.
- Fail-closed convention: `.cursor/rules/20-python-tests.mdc` (deny unless allowed; no retry after violation).
- VBAA is concept-only in `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv` (V-01); no per-field spec found.

This file imports the not-yet-implemented unit. Collection/import failure is the intended RED.
Do not skip-if-missing. Do not import a live node, Telegram, or 138 ledger.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_VAULT = Path(__file__).resolve().parents[3]
_OPS = _VAULT / "_ops"
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from vbaa.artifact_admission import ArtifactAdmission  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "artifact_admission"


def _load(name: str) -> dict:
    return json.loads((_FIX / name).read_text(encoding="utf-8"))


def _allowed_types() -> frozenset[str]:
    data = _load("allowed_types.json")
    return frozenset(data["allowed_types"])


def _gate() -> ArtifactAdmission:
    return ArtifactAdmission(allowed_types=_allowed_types(), path_root=_FIX)


def test_empty_artifact_is_rejected():
    """User-named reject class: empty."""
    v = _gate().admit(_load("empty.json"))
    assert v.admitted is False
    assert v.reason_code == "EMPTY"


def test_empty_payload_is_rejected():
    """User-named reject class: empty. Empty mapping payload is fail-closed EMPTY."""
    v = _gate().admit(_load("empty_payload.json"))
    assert v.admitted is False
    assert v.reason_code == "EMPTY"


def test_unsigned_artifact_is_rejected():
    """User-named reject class: unsigned (missing signature field)."""
    v = _gate().admit(_load("unsigned.json"))
    assert v.admitted is False
    assert v.reason_code == "UNSIGNED"


def test_empty_signature_is_rejected_as_unsigned():
    """Empty signature string is unsigned, not a present signature."""
    v = _gate().admit(_load("empty_signature.json"))
    assert v.admitted is False
    assert v.reason_code == "UNSIGNED"


def test_wrong_type_is_rejected():
    """User-named reject class: wrong type (not in fixture allowlist)."""
    v = _gate().admit(_load("wrong_type.json"))
    assert v.admitted is False
    assert v.reason_code == "WRONG_TYPE"


def test_posix_dotdot_path_is_rejected():
    """User-named reject class: path escape (`../`)."""
    v = _gate().admit(_load("path_escape_dotdot.json"))
    assert v.admitted is False
    assert v.reason_code == "PATH_ESCAPE"


def test_windows_dotdot_path_is_rejected():
    """User-named reject class: path escape (`..\\` on Windows)."""
    v = _gate().admit(_load("path_escape_windows.json"))
    assert v.admitted is False
    assert v.reason_code == "PATH_ESCAPE"


def test_absolute_path_is_rejected():
    """User-named reject class: path escape (absolute path outside path_root)."""
    v = _gate().admit(_load("path_escape_abs.json"))
    assert v.admitted is False
    assert v.reason_code == "PATH_ESCAPE"


def test_signed_correct_type_confined_path_is_admitted():
    """Positive fixture: non-empty payload, signature present, allowed type, confined path."""
    v = _gate().admit(_load("valid_signed.json"))
    assert v.admitted is True
    assert v.reason_code == "OK"


def test_rejected_artifact_stays_rejected_on_second_call():
    """Fail-closed: no retry-into-allow after an invariant violation.

    Source: `.cursor/rules/20-python-tests.mdc`.
    """
    gate = _gate()
    first = gate.admit(_load("unsigned.json"))
    second = gate.admit(_load("unsigned.json"))
    assert first.admitted is False
    assert second.admitted is False
    assert second.reason_code == "UNSIGNED"


@pytest.mark.xfail(
    reason=(
        "unverified: cryptographic verification of signature (Ed25519 vs presence-only) "
        "is not in V-01 registry. See 07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md (INV-CRYPTO)."
    ),
    strict=False,
)
def test_signature_is_cryptographically_verified_not_presence_only():
    """Invented until a VBAA spec names the signature scheme. Must not hide the RED import."""
    gate = _gate()
    artifact = _load("valid_signed.json")
    artifact["signature"] = "sig-fixture-ok"
    v = gate.admit(artifact)
    assert getattr(v, "signature_verified", False) is True

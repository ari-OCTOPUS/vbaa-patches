"""RED contract: ArgumentProvenanceGuard on fixture provenance only.

Sources:
- V-01 names ArgumentProvenanceGuard in `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv`.
- User prompt 2026-09-08: untrusted/unprovenanced arguments rejected; trusted fixture provenance passes.
- trust_level vocabulary `verified | derived | untrusted` from `_ops/epistemics/schemas.py` (EvidenceScoreBand.provenance / EvidenceRecord.trust_level).

No VBAA-specific field spec found. derived-trust policy is unverified (xfail).
This file imports the not-yet-implemented unit. Collection/import failure is the intended RED.
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

from vbaa.argument_provenance_guard import ArgumentProvenanceGuard  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "argument_provenance"


def _load(name: str) -> dict:
    return json.loads((_FIX / name).read_text(encoding="utf-8"))


def _guard() -> ArgumentProvenanceGuard:
    return ArgumentProvenanceGuard()


def test_unprovenanced_arguments_are_rejected():
    """User-named: missing provenance object is rejected."""
    fx = _load("unprovenanced.json")
    v = _guard().check(arguments=fx["arguments"], provenance=fx.get("provenance"))
    assert v.allowed is False
    assert v.reason_code == "UNPROVENANCED"


def test_empty_provenance_object_is_rejected_as_unprovenanced():
    """Empty provenance mapping has no trust_level / provenance_id."""
    fx = _load("empty_provenance.json")
    v = _guard().check(arguments=fx["arguments"], provenance=fx["provenance"])
    assert v.allowed is False
    assert v.reason_code == "UNPROVENANCED"


def test_untrusted_provenance_is_rejected():
    """User-named: untrusted arguments are rejected.

    trust_level=untrusted is an in-repo label (`_ops/epistemics/schemas.py`).
    """
    fx = _load("untrusted.json")
    v = _guard().check(arguments=fx["arguments"], provenance=fx["provenance"])
    assert v.allowed is False
    assert v.reason_code == "UNTRUSTED"


def test_trusted_fixture_provenance_passes():
    """User-named: trusted fixture provenance passes.

    trust_level=verified is an in-repo label (`_ops/epistemics/schemas.py`).
    """
    fx = _load("trusted.json")
    v = _guard().check(arguments=fx["arguments"], provenance=fx["provenance"])
    assert v.allowed is True
    assert v.reason_code == "OK"


def test_none_provenance_is_rejected():
    fx = _load("trusted.json")
    v = _guard().check(arguments=fx["arguments"], provenance=None)
    assert v.allowed is False
    assert v.reason_code == "UNPROVENANCED"


def test_rejected_arguments_stay_rejected_on_second_call():
    """Fail-closed: no retry-into-allow. Source: `.cursor/rules/20-python-tests.mdc`."""
    guard = _guard()
    fx = _load("untrusted.json")
    first = guard.check(arguments=fx["arguments"], provenance=fx["provenance"])
    second = guard.check(arguments=fx["arguments"], provenance=fx["provenance"])
    assert first.allowed is False
    assert second.allowed is False
    assert second.reason_code == "UNTRUSTED"


@pytest.mark.xfail(
    reason=(
        "unverified: whether trust_level=derived is allowed or rejected is not in V-01. "
        "See 07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md (INV-DERIVED)."
    ),
    strict=False,
)
def test_derived_trust_policy_is_specified():
    """Invented until the VBAA spec says derived is allow or deny."""
    fx = _load("derived.json")
    v = _guard().check(arguments=fx["arguments"], provenance=fx["provenance"])
    assert v.reason_code in {"OK", "UNTRUSTED", "UNPROVENANCED", "DERIVED_DENIED"}
    assert isinstance(v.allowed, bool)

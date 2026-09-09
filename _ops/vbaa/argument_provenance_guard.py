"""Smallest ArgumentProvenanceGuard for the L7 RED fixture contract.

Fail-closed: missing/empty provenance is UNPROVENANCED; untrusted is UNTRUSTED;
verified with provenance_id passes. derived and unknown levels deny as UNTRUSTED
(INV-DERIVED remains xfail). No live node, Telegram, or ledger writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProvenanceVerdict:
    allowed: bool
    reason_code: str


class ArgumentProvenanceGuard:
    REASON_OK = "OK"
    REASON_UNPROVENANCED = "UNPROVENANCED"
    REASON_UNTRUSTED = "UNTRUSTED"

    def check(
        self,
        arguments: Mapping[str, Any] | None,
        provenance: Mapping[str, Any] | None,
    ) -> ProvenanceVerdict:
        if provenance is None or not isinstance(provenance, Mapping) or not provenance:
            return ProvenanceVerdict(False, self.REASON_UNPROVENANCED)
        trust = provenance.get("trust_level")
        provenance_id = provenance.get("provenance_id")
        if not trust or not provenance_id:
            return ProvenanceVerdict(False, self.REASON_UNPROVENANCED)
        if trust == "verified":
            return ProvenanceVerdict(True, self.REASON_OK)
        if trust == "untrusted":
            return ProvenanceVerdict(False, self.REASON_UNTRUSTED)
        return ProvenanceVerdict(False, self.REASON_UNTRUSTED)

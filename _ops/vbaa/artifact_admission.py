"""Smallest ArtifactAdmission that satisfies the L7 RED fixture contract.

Fail-closed. Presence-only signature check (INV-CRYPTO remains xfail).
No network, no live node, no Telegram, no ledger writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class AdmissionVerdict:
    admitted: bool
    reason_code: str


class ArtifactAdmission:
    REASON_OK = "OK"
    REASON_EMPTY = "EMPTY"
    REASON_UNSIGNED = "UNSIGNED"
    REASON_WRONG_TYPE = "WRONG_TYPE"
    REASON_PATH_ESCAPE = "PATH_ESCAPE"

    def __init__(self, allowed_types: Iterable[str], path_root: Path | str) -> None:
        self._allowed = frozenset(allowed_types)
        self._root = Path(path_root)

    def admit(self, artifact: Mapping[str, Any] | None) -> AdmissionVerdict:
        if artifact is None or not artifact:
            return AdmissionVerdict(False, self.REASON_EMPTY)
        payload = artifact.get("payload", None)
        if payload is None or payload == {} or payload == "" or payload == []:
            return AdmissionVerdict(False, self.REASON_EMPTY)
        signature = artifact.get("signature", None)
        if signature is None or (isinstance(signature, str) and signature.strip() == ""):
            return AdmissionVerdict(False, self.REASON_UNSIGNED)
        artifact_type = artifact.get("artifact_type")
        if artifact_type not in self._allowed:
            return AdmissionVerdict(False, self.REASON_WRONG_TYPE)
        if self._escapes(artifact.get("path")):
            return AdmissionVerdict(False, self.REASON_PATH_ESCAPE)
        return AdmissionVerdict(True, self.REASON_OK)

    def _escapes(self, raw: Any) -> bool:
        if not isinstance(raw, str) or raw.strip() == "":
            return True
        normalized = raw.replace("\\", "/")
        parts = [p for p in normalized.split("/") if p not in ("", ".")]
        if any(p == ".." for p in parts):
            return True
        path = Path(raw)
        if path.is_absolute():
            return True
        if len(raw) >= 2 and raw[1] == ":":
            return True
        try:
            resolved = (self._root / raw).resolve()
            resolved.relative_to(self._root.resolve())
        except (ValueError, OSError):
            return True
        return False

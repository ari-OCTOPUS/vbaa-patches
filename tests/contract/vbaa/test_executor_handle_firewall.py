"""RED contract: ExecutorHandleFirewall — AST-only, fixture trees only.

Board 180 must not import the executor. Production check is AST parse, not
runtime import of a live executor. Do not scan or mutate the live service tree.

Sources:
- User prompt 2026-09-08: host `.180` has no executor import; AST finds
  `import …executor…` / `from …executor import …`; clean fixture tree passes.
- Fail-closed: `.cursor/rules/20-python-tests.mdc`.

Matching rule locked by these tests (PROMPT 2 must satisfy):
  An `ast.Import` or `ast.ImportFrom` is a violation iff any dotted component of
  the module path equals `executor` (relative ImportFrom with module `executor`
  included). Comments and string literals are not Import nodes.

Substring-anywhere matching (`import executory`) is unverified (xfail).
This file imports the not-yet-implemented unit. Collection/import failure is RED.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

_VAULT = Path(__file__).resolve().parents[3]
_OPS = _VAULT / "_ops"
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from vbaa.executor_handle_firewall import ExecutorHandleFirewall  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "executor_firewall"
_DIRTY = _FIX / "dirty_tree"
_CLEAN = _FIX / "clean_tree"
_SUBSTRING = _FIX / "substring_tree"


def _sha_tree(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix().encode("utf-8")
            h.update(rel)
            h.update(p.read_bytes())
    return h.hexdigest()


def test_dirty_fixture_tree_reports_violations():
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_DIRTY, host_id="180")
    assert report.clean is False
    assert len(report.violations) >= 3
    modules = {v.module for v in report.violations}
    assert "foo.executor" in modules or any(
        part == "executor" for m in modules for part in m.split(".")
    )
    kinds = {v.statement for v in report.violations}
    assert "import" in kinds
    assert "from" in kinds


def test_clean_fixture_tree_passes():
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_CLEAN, host_id="180")
    assert report.clean is True
    assert list(report.violations) == []
    assert report.scanned_files >= 3
    assert report.host_id == "180"


def test_string_and_comment_mentions_are_not_violations():
    """AST-only: comments and string literals mentioning executor are not imports."""
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_CLEAN, host_id="180")
    assert report.clean is True


def test_scan_does_not_import_executor_into_sys_modules():
    """Must not runtime-import the executor (live or fixture). AST parse only."""
    before = set(sys.modules)
    ExecutorHandleFirewall().scan_python_tree(_DIRTY, host_id="180")
    after = set(sys.modules)
    leaked = [name for name in (after - before) if "executor" in name.split(".")]
    assert leaked == []


def test_scan_does_not_mutate_fixture_tree():
    before = _sha_tree(_DIRTY)
    ExecutorHandleFirewall().scan_python_tree(_DIRTY, host_id="180")
    after = _sha_tree(_DIRTY)
    assert after == before


def test_relative_from_executor_is_a_violation():
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_DIRTY, host_id="180")
    rel = [
        v
        for v in report.violations
        if Path(v.path).name == "relative_from.py"
    ]
    assert rel, "relative `from .executor import …` must be reported"
    assert any(
        "executor" in v.module.split(".") or v.module == "executor"
        for v in rel
    )


def test_host_id_on_report_is_180_for_this_board():
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_CLEAN, host_id="180")
    assert report.host_id == "180"
    assert getattr(fw, "TARGET_HOST_ID", "180") == "180"


@pytest.mark.xfail(
    reason=(
        "unverified: substring match on `executory` vs component-equality. "
        "See 07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md (INV-SUBSTRING)."
    ),
    strict=False,
)
def test_executory_substring_policy_is_specified():
    fw = ExecutorHandleFirewall()
    report = fw.scan_python_tree(_SUBSTRING, host_id="180")
    assert isinstance(report.clean, bool)
    assert report.scanned_files >= 1

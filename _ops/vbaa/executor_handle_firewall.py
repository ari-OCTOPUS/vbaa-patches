"""AST-only ExecutorHandleFirewall for host .180 fixture trees.

A violation is an ast.Import or ast.ImportFrom whose dotted module path has a
component exactly equal to ``executor``. Comments and string literals do not
count. ``import executory`` does not match (INV-SUBSTRING remains xfail).

Never imports the scanned modules. Does not write the tree. No live service scan.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportViolation:
    path: str
    lineno: int
    module: str
    statement: str


@dataclass(frozen=True)
class FirewallReport:
    host_id: str
    violations: tuple[ImportViolation, ...]
    scanned_files: int

    @property
    def clean(self) -> bool:
        return len(self.violations) == 0


def _has_executor_component(module: str | None) -> bool:
    if not module:
        return False
    return any(part == "executor" for part in module.split(".") if part)


class ExecutorHandleFirewall:
    TARGET_HOST_ID = "180"

    def scan_python_tree(self, root: Path | str, *, host_id: str = "180") -> FirewallReport:
        base = Path(root)
        violations: list[ImportViolation] = []
        scanned = 0
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            scanned += 1
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(path))
            except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
                continue
            rel = path.relative_to(base).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _has_executor_component(alias.name):
                            violations.append(
                                ImportViolation(
                                    path=rel,
                                    lineno=getattr(node, "lineno", 0),
                                    module=alias.name,
                                    statement="import",
                                )
                            )
                elif isinstance(node, ast.ImportFrom):
                    if _has_executor_component(node.module):
                        violations.append(
                            ImportViolation(
                                path=rel,
                                lineno=getattr(node, "lineno", 0),
                                module=node.module or "executor",
                                statement="from",
                            )
                        )
        return FirewallReport(
            host_id=host_id,
            violations=tuple(violations),
            scanned_files=scanned,
        )

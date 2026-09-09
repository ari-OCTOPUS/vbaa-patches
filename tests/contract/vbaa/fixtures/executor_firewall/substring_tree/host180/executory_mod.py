"""Fixture used only by the unverified substring-match xfail.

If production matching is component-equality, this file is clean.
If production matching is substring-anywhere, this is dirty.
See 07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md (INV-SUBSTRING).
"""
import executory  # noqa: F401

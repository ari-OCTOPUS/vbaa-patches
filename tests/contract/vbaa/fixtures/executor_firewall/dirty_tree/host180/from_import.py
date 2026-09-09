"""Dirty fixture — AST ImportFrom of a module path whose last component is executor.

This is not a live executor. Do not execute this file against a node.
"""
from pkg.executor import run  # noqa: F401

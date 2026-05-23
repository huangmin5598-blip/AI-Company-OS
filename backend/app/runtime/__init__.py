# @PRODUCT backend/app/runtime/__init__.py
"""
Runtime Adapter Package — OS Core layer for AI runtime abstraction.

This package defines the protocol for integrating different AI runtimes
(Hermes, Codex, Claude Code, etc.) into AI Company OS.
"""

from .protocol import RuntimeAdapter, RuntimeCapability, RuntimeStatus, RuntimeSession

"""
Command line interface: ``python -m svgwriter``.
"""

from __future__ import annotations

from .tools.cli import app, main

__all__ = ["app", "main"]

if __name__ == "__main__":
    raise SystemExit(main())

"""Tailwhip - Sort Tailwind CSS classes in HTML and CSS files."""

from __future__ import annotations

from tailwhip.cli import main

__author__ = "Martin Mahner"
__all__ = ["__author__", "__version__", "main"]


def __getattr__(name: str) -> str:
    """Resolve the package version on first use; reading the metadata is slow."""
    if name == "__version__":
        from importlib import metadata  # noqa: PLC0415

        return metadata.version("tailwhip")

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

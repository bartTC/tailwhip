"""Tailwhip - Sort Tailwind CSS classes in HTML and CSS files."""

from __future__ import annotations

from importlib import metadata

from tailwhip.cli import main

__all__ = ["main"]
__version__ = metadata.version("tailwhip")
__author__ = "Martin Mahner"

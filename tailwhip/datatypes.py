"""Datatypes for tailwhip."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console


@dataclass(frozen=True)
class Config:
    """Argument parser config."""

    console: Console
    paths: list[Path]
    write: bool
    verbosity: int

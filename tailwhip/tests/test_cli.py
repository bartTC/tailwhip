"""Tests for CLI functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tailwhip.cli import app

if TYPE_CHECKING:
    from pathlib import Path


runner = CliRunner()


@pytest.mark.parametrize(
    "arguments",
    [
        "",
        "-v",
        "-vv",
        "-vvv",
        "-vvvvvvvvvv",
        "--quiet",
        "--version",
        "--help",
        "--custom-colors='primary,secondary'",
    ],
)
def test_cli_with_path(testdata_dir: Path, arguments: str) -> None:
    """Test CLI with a single path argument."""
    result = runner.invoke(app, [str(testdata_dir), arguments])
    assert result.exit_code == 0

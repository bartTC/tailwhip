"""Global pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from tailwhip.constants import SKIP_EXPRESSIONS
from tailwhip.datatypes import Config

# Get the testdata directory relative to this test file
TESTDATA = Path(__file__).parent / "testdata"


@pytest.fixture
def testdata_dir() -> Path:
    """Provide the testdata directory path."""
    return TESTDATA


@pytest.fixture
def config() -> Config:
    """Return a base configuration object."""
    return Config(
        console=Console(quiet=True),
        paths=[Path()],
        write=False,
        skip_expressions=SKIP_EXPRESSIONS,
        verbosity=0,
        custom_colors=[],
    )

"""Global pytest fixtures."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TypedDict, Unpack

import pytest
from rich.console import Console

from tailwhip.constants import SKIP_EXPRESSIONS
from tailwhip.context import get_config, set_config
from tailwhip.datatypes import Config

# Get the testdata directory relative to this test file
TESTDATA = Path(__file__).parent / "testdata"


@pytest.fixture(autouse=True)
def testdata_dir(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide the testdata directory path."""
    monkeypatch.chdir(TESTDATA)
    return TESTDATA


@pytest.fixture(autouse=True, scope="session")
def config() -> None:
    """Return a base configuration object and set it as global config."""
    cfg = Config(
        console=Console(quiet=True),
        paths=[Path()],
        write=False,
        skip_expressions=SKIP_EXPRESSIONS,
        verbosity=0,
        custom_colors=set(),
    )
    set_config(cfg)


class ConfigTypes(TypedDict, total=False):
    """Typed kwargs for Config fields."""

    console: Console
    paths: list[Path]
    write: bool
    skip_expressions: list[str]
    verbosity: int
    custom_colors: set[str]


def update_config(**kwargs: Unpack[ConfigTypes]) -> None:
    """Update the global config instance."""
    config = replace(get_config(), **kwargs)
    set_config(config)

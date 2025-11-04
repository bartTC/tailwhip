"""Configuration management for tailwhip."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import dynaconf
import rich
import tomllib

# Path to default configuration file
BASE_CONFIGURATION_FILE = Path(__file__).parent / "configuration.toml"

# Console theme for rich.Console output
CONSOLE_THEME = rich.theme.Theme(
    {
        "important": "white on deep_pink4",
        "highlight": "yellow1",
        "filename": "white",
        "bold": "sky_blue1",
    }
)


@dataclass
class Pattern:
    """A compiled pattern for matching and reconstructing class attributes."""

    name: str
    regex: re.Pattern
    template: str


def get_pyproject_toml_data(start_path: Path) -> Path | None:
    """Search for pyproject.toml starting at the given path."""
    pyproject_path = None

    for directory in [start_path, *start_path.resolve().parents]:
        candidate = directory / "pyproject.toml"
        if candidate.exists():
            pyproject_path = candidate
            break

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    return data.get("tool", {}).get("tailwhip")


def update_configuration(data: dict | Path) -> None:
    """Update configuration with the given data."""
    if isinstance(data, dict):
        config.update(data, merge=False)
        _recompile_patterns()
        return

    if isinstance(data, Path):
        with data.open("rb") as f:
            config_data = tomllib.load(f)
        config.update(config_data, merge=False)
        _recompile_patterns()
        return

    # pragma: no cover
    msg = f"Invalid data type '{type(data)}' for configuration update."  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def _recompile_patterns() -> None:
    """Re-compile regular expressions pattern objects."""
    config.tailwind_colors = set(config.tailwind_colors)
    config.custom_colors = set(config.custom_colors)

    config.UTILITY_PATTERNS = [re.compile("^" + g) for g in config.utility_groups]
    config.VARIANT_PATTERNS = [re.compile(v) for v in config.variant_groups]

    # Compile class_patterns into Pattern objects with compiled regexes
    config.APPLY_PATTERNS = [
        Pattern(
            name=pattern["name"],
            regex=re.compile(pattern["regex"], re.IGNORECASE | re.DOTALL),
            template=pattern["template"],
        )
        for pattern in config.class_patterns
    ]


class VerbosityLevel(IntEnum):
    """Verbosity level enum."""

    QUIET = 0
    NORMAL = 1  # Default
    VERBOSE = 2  # Show unchanged files
    DIFF = 3  # Show diff of changes
    DEBUG = 4


class TailwhipConfig(dynaconf.Dynaconf):
    """Configuration for tailwhip."""

    # Utilities created at runtime
    console: rich.console.Console

    # Settings provided by the base config
    verbosity: VerbosityLevel
    write_mode: bool
    default_globs: list[str]
    skip_expressions: list[str]
    variant_separator: str
    utility_groups: list[str]
    variant_groups: list[str]
    tailwind_colors: set[str]
    custom_colors: set[str]
    class_patterns: list[dict[str, str]]

    # Compiled regex patterns
    UTILITY_PATTERNS: list[re.Pattern]
    VARIANT_PATTERNS: list[re.Pattern]
    APPLY_PATTERNS: list[Pattern]


config = TailwhipConfig(
    settings_files=[str(BASE_CONFIGURATION_FILE)],
    merge_enabled=False,
    envvar_prefix="TAILWHIP",
    root_path=Path.cwd(),
    load_dotenv=False,
    lowercase_read=True,
)

# Initialize constants on module load
_recompile_patterns()

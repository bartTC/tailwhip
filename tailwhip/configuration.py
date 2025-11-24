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

    if pyproject_path is None:
        return None

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    return data.get("tool", {}).get("tailwhip")


def update_configuration(data: dict | Path) -> None:
    """Update configuration with the given data."""
    if isinstance(data, dict):
        config.update(data, merge=False)
        _rebuild_lookups()
        return

    if isinstance(data, Path):
        with data.open("rb") as f:
            config_data = tomllib.load(f)
        config.update(config_data, merge=False)
        _rebuild_lookups()
        return

    # pragma: no cover
    msg = f"Invalid data type '{type(data)}' for configuration update."  # pragma: no cover
    raise TypeError(msg)  # pragma: no cover


def _rebuild_lookups() -> None:
    """Rebuild lookup dictionaries and compile patterns."""
    # Build lookup dicts for O(1) index access
    config.variant_index = {v: i for i, v in enumerate(config.variants)}
    config.prefix_index = {p: i for i, p in enumerate(config.prefixes)}
    config.direction_index = {d: i for i, d in enumerate(config.directions)}
    config.size_index = {s: i for i, s in enumerate(config.sizes)}
    config.value_index = {v: i for i, v in enumerate(config.numerics)}
    config.shade_index = {s: i for i, s in enumerate(config.shades)}
    config.alpha_index = {a: i for i, a in enumerate(config.alphas)}

    # Combine and sort colors alphabetically
    all_colors_sorted = sorted({*config.colors, *config.custom_colors})
    config.color_index = {c: i for i, c in enumerate(all_colors_sorted)}

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
    class_patterns: list[dict[str, str]]

    # Component order and lists
    component_order: list[str]
    variants: list[str]
    prefixes: list[str]
    directions: list[str]
    sizes: list[str]
    numerics: list[str]
    colors: list[str]
    custom_colors: list[str]
    shades: list[str]
    alphas: list[str]

    # Lookup dictionaries (built at runtime for O(1) access)
    variant_index: dict[str, int]
    prefix_index: dict[str, int]
    direction_index: dict[str, int]
    size_index: dict[str, int]
    value_index: dict[str, int]
    color_index: dict[str, int]
    shade_index: dict[str, int]
    alpha_index: dict[str, int]

    # Compiled patterns
    APPLY_PATTERNS: list[Pattern]


config = TailwhipConfig(
    settings_files=[str(BASE_CONFIGURATION_FILE)],
    merge_enabled=False,
    envvar_prefix="TAILWHIP",
    root_path=Path.cwd(),
    load_dotenv=False,
    lowercase_read=True,
)

# Initialize lookups on module load
_rebuild_lookups()

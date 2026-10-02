"""Configuration management for tailwhip."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING

import dynaconf

if TYPE_CHECKING:
    from collections.abc import Callable

    import rich.console

# Path to default configuration file
BASE_CONFIGURATION_FILE = Path(__file__).parent / "configuration.toml"

# Styles for the rich.Console output
CONSOLE_STYLES = {
    "important": "white on deep_pink4",
    "highlight": "yellow1",
    "filename": "white",
    "bold": "sky_blue1",
}


def create_console(*, quiet: bool) -> rich.console.Console:
    """
    Create the console used for all output.

    Rich is imported here rather than at module level: importing it is a
    noticeable part of the startup time, and stdin mode never prints through it.
    """
    from rich.console import Console  # noqa: PLC0415
    from rich.theme import Theme  # noqa: PLC0415

    return Console(quiet=quiet, theme=Theme(CONSOLE_STYLES))


@dataclass
class Pattern:
    """A compiled pattern for matching and reconstructing class attributes."""

    name: str
    regex: re.Pattern
    template: str


@dataclass(slots=True)
class Lookups:
    """
    Plain lookup tables derived from the configuration lists.

    Values stored on the Dynaconf settings object are wrapped in node types whose
    membership tests scan every key, far too slow for the sorting hot path. These
    plain structures are refreshed in place by _rebuild_lookups() whenever the
    configuration changes, so modules can keep a reference to the single instance.
    """

    variant_separator: str = ":"
    skip_expressions: tuple[str, ...] = ()
    component_order: tuple[str, ...] = ()
    variant_index: dict[str, int] = field(default_factory=dict)
    prefix_index: dict[str, int] = field(default_factory=dict)
    direction_index: dict[str, int] = field(default_factory=dict)
    size_index: dict[str, int] = field(default_factory=dict)
    value_index: dict[str, int] = field(default_factory=dict)
    color_index: dict[str, int] = field(default_factory=dict)
    shade_index: dict[str, int] = field(default_factory=dict)
    alpha_index: dict[str, int] = field(default_factory=dict)


lookups = Lookups()


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


# Functions that drop cached results derived from the configuration. Modules that
# memoize configuration-dependent work register their cache clearers here.
_cache_clearers: list[Callable[[], None]] = []


def register_cache_clearer(clear: Callable[[], None]) -> None:
    """Register a function to call whenever the configuration changes."""
    _cache_clearers.append(clear)


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
    """Rebuild the lookup tables and compile patterns."""
    # Plain copies of the settings read for every class or attribute
    lookups.variant_separator = config.variant_separator
    lookups.skip_expressions = tuple(config.skip_expressions)
    lookups.component_order = tuple(config.component_order)

    # Build lookup dicts for O(1) index access
    lookups.variant_index = {v: i for i, v in enumerate(config.variants)}
    lookups.prefix_index = {p: i for i, p in enumerate(config.prefixes)}
    lookups.direction_index = {d: i for i, d in enumerate(config.directions)}
    lookups.size_index = {s: i for i, s in enumerate(config.sizes)}
    lookups.value_index = {v: i for i, v in enumerate(config.numerics)}
    lookups.shade_index = {s: i for i, s in enumerate(config.shades)}
    lookups.alpha_index = {a: i for i, a in enumerate(config.alphas)}

    # Combine and sort colors alphabetically
    all_colors_sorted = sorted({*config.colors, *config.custom_colors})
    lookups.color_index = {c: i for i, c in enumerate(all_colors_sorted)}

    # Compile class_patterns into Pattern objects with compiled regexes
    config.APPLY_PATTERNS = [
        Pattern(
            name=pattern["name"],
            regex=re.compile(pattern["regex"], re.IGNORECASE | re.DOTALL),
            template=pattern["template"],
        )
        for pattern in config.class_patterns
    ]

    # Cached results derived from the configuration are stale now, so drop them
    for clear in _cache_clearers:
        clear()


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

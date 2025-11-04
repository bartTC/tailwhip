"""Constants used by tailwhip."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib
from rich.theme import Theme


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary with default values
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _find_pyproject_toml(start_path: Path | None = None) -> Path | None:
    """Find pyproject.toml by walking up the directory tree.

    Args:
        start_path: Directory to start searching from. Defaults to current working directory.

    Returns:
        Path to pyproject.toml if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    while True:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            return pyproject_path

        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _load_pyproject_config(start_path: Path | None = None) -> dict | None:
    """Load tailwhip configuration from pyproject.toml [tool.tailwhip] section.

    Args:
        start_path: Directory to start searching from. Defaults to current working directory.

    Returns:
        Configuration dictionary from [tool.tailwhip] section, or None if not found
    """
    pyproject_path = _find_pyproject_toml(start_path)
    if not pyproject_path:
        return None

    try:
        with pyproject_path.open("rb") as f:
            pyproject_data = tomllib.load(f)

        # Extract [tool.tailwhip] section if it exists
        return pyproject_data.get("tool", {}).get("tailwhip", None)
    except Exception:
        # If there's any error reading the file, just skip it
        return None


def _load_config(
    custom_config_path: Path | None = None,
    search_path: Path | None = None,
) -> dict:
    """Load configuration with priority: custom > pyproject.toml > defaults.

    Args:
        custom_config_path: Optional path to a custom TOML config file that will be
                           merged with the default config. Only specified values will
                           be overridden.
        search_path: Directory to start searching for pyproject.toml. Defaults to cwd.

    Returns:
        Configuration dictionary
    """
    # Load default config
    default_config_path = Path(__file__).parent / "constants.toml"
    with default_config_path.open("rb") as f:
        config = tomllib.load(f)

    # Merge with pyproject.toml [tool.tailwhip] if found
    pyproject_config = _load_pyproject_config(search_path)
    if pyproject_config:
        config = _deep_merge(config, pyproject_config)

    # Merge with custom config if provided (highest priority)
    if custom_config_path:
        if not custom_config_path.exists():
            msg = f"Custom config file not found: {custom_config_path}"
            raise FileNotFoundError(msg)

        with custom_config_path.open("rb") as f:
            custom_config = tomllib.load(f)

        config = _deep_merge(config, custom_config)

    return config


def reload_config(
    custom_config_path: Path | None = None,
    search_path: Path | None = None,
) -> None:
    """Reload configuration from disk, optionally with a custom config file.

    This function allows reloading the configuration at runtime, useful when
    a custom config file is specified via CLI or when pyproject.toml should be loaded.

    Configuration priority: custom > pyproject.toml > defaults

    Args:
        custom_config_path: Optional path to a custom TOML config file
        search_path: Directory to start searching for pyproject.toml. Defaults to cwd.
    """
    global _config, GLOBS, SKIP_EXPRESSIONS, VARIANT_SEP, GROUP_ORDER, GROUP_PATTERNS
    global VARIANT_PREFIX_ORDER, VARIANT_PATTERNS, TAILWIND_COLORS, CLASSES_RE
    global CLASS_ATTR_RE, APPLY_RE

    _config = _load_config(custom_config_path, search_path)

    # Reload all constants
    GLOBS = _config["globs"]
    SKIP_EXPRESSIONS = _config["skip_expressions"]
    VARIANT_SEP = _config["variant_sep"]
    GROUP_ORDER = _config["group_order"]
    GROUP_PATTERNS = [re.compile("^" + g) for g in GROUP_ORDER]
    VARIANT_PREFIX_ORDER = _config["variant_prefix_order"]
    VARIANT_PATTERNS = [re.compile(v) for v in VARIANT_PREFIX_ORDER]
    TAILWIND_COLORS = set(_config["tailwind_colors"])

    # Load combined regex if available, otherwise use individual patterns
    if "classes_re" in _config:
        CLASSES_RE = re.compile(
            _config["classes_re"],
            re.IGNORECASE | re.DOTALL | re.MULTILINE,
        )
    # Keep the hardcoded individual patterns for backwards compatibility
    CLASS_ATTR_RE = re.compile(
        r"""(?P<full>\bclass\s*=\s*(?P<quote>["'])(?P<val>.*?)(?P=quote))""",
        re.IGNORECASE | re.DOTALL,
    )
    APPLY_RE = re.compile(
        r"""@apply\s+(?P<classes>[^;]+);""",
        re.MULTILINE,
    )


# Load default configuration
_config = _load_config()

# File glob(s) to process
GLOBS = _config["globs"]

# Skip if a template expression appears inside the class attribute
SKIP_EXPRESSIONS = _config["skip_expressions"]

# Recognize Tailwind variants
VARIANT_SEP = _config["variant_sep"]

# Group order patterns
GROUP_ORDER = _config["group_order"]
GROUP_PATTERNS = [re.compile("^" + g) for g in GROUP_ORDER]

# Variant prefix order patterns
VARIANT_PREFIX_ORDER = _config["variant_prefix_order"]
VARIANT_PATTERNS = [re.compile(v) for v in VARIANT_PREFIX_ORDER]

# Standard Tailwind color names
TAILWIND_COLORS = set(_config["tailwind_colors"])

# Regex patterns
CLASS_ATTR_RE = re.compile(
    _config["class_attr_re"],
    re.IGNORECASE | re.DOTALL,
)

APPLY_RE = re.compile(
    _config["apply_re"],
    re.MULTILINE,
)

CONSOLE_THEME = Theme(
    {
        "important": "white on deep_pink4",
        "highlight": "yellow1",
        "filename": "white",
        "bold": "sky_blue1",
    }
)

VERBOSITY_NONE = 0
VERBOSITY_LOUD = 2
VERBOSITY_ALL = 3

"""Configuration management for tailwhip."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from dynaconf import Dynaconf
from rich.theme import Theme

# Path to default configuration file
_default_config_path = Path(__file__).parent / "configuration.toml"

# Initialize dynaconf configuration
# Configuration priority: custom > pyproject.toml > defaults
configuration = Dynaconf(
    settings_files=[str(_default_config_path)],
    includes=["pyproject.toml"],  # Auto-discover pyproject.toml
    merge_enabled=False,  # Replace values instead of merging lists
    envvar_prefix="TAILWHIP",
    root_path=Path.cwd(),
    load_dotenv=False,
    lowercase_read=True,
)


def reload_config(
    custom_config_path: Path | None = None,
    search_path: Path | None = None,
) -> None:
    """Reload configuration from disk, optionally with a custom config file.

    Configuration priority: custom > pyproject.toml > defaults

    Args:
        custom_config_path: Optional path to a custom TOML config file
        search_path: Directory to start searching for pyproject.toml
    """
    global configuration

    if custom_config_path and not custom_config_path.exists():
        msg = f"Custom config file not found: {custom_config_path}"
        raise FileNotFoundError(msg)

    # Build settings files list  (priority: defaults < pyproject < custom)
    settings_files = [str(_default_config_path)]

    # Search for pyproject.toml and extract [tool.tailwhip] section
    pyproject_path = _find_pyproject_toml(search_path or Path.cwd())
    pyproject_config = None
    if pyproject_path:
        pyproject_config = _extract_tool_tailwhip(pyproject_path)

    # Load custom config keys if present
    custom_keys = set()
    if custom_config_path:
        settings_files.append(str(custom_config_path))
        # Read custom config to know which keys it defines
        try:
            with custom_config_path.open("rb") as f:
                custom_data = tomllib.load(f)
            custom_keys = set(custom_data.keys())
        except Exception:
            pass  # If can't read, dynaconf will handle error

    # Create new Dynaconf instance (configure() doesn't fully reload)
    # Note: merge_enabled=False so lists are replaced, not merged
    configuration = Dynaconf(
        settings_files=settings_files,
        merge_enabled=False,  # Replace values instead of merging lists
        envvar_prefix="TAILWHIP",
        root_path=search_path or Path.cwd(),
        load_dotenv=False,
        lowercase_read=True,
    )

    # Manually apply pyproject [tool.tailwhip] config for keys not in custom config
    # This gives us the priority: custom > pyproject > defaults
    if pyproject_config:
        for key, value in pyproject_config.items():
            # Only set if not defined in custom config
            if key not in custom_keys:
                configuration.set(key, value)

    # Update module-level constants from settings
    _update_constants()


def _find_pyproject_toml(start_path: Path) -> Path | None:
    """Find pyproject.toml by walking up the directory tree.

    Args:
        start_path: Directory to start searching from.

    Returns:
        Path to pyproject.toml if found, None otherwise
    """
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


def _extract_tool_tailwhip(pyproject_path: Path) -> dict | None:
    """Extract [tool.tailwhip] section from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary with tailwhip config, or None if section doesn't exist

    Raises:
        Exception: If pyproject.toml has invalid TOML syntax
    """
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get("tailwhip")


def _update_constants() -> None:
    """Update module-level constants from dynaconf configuration."""
    global GLOBS, SKIP_EXPRESSIONS, VARIANT_SEP, GROUP_ORDER, GROUP_PATTERNS
    global VARIANT_PREFIX_ORDER, VARIANT_PATTERNS, TAILWIND_COLORS
    global CLASS_ATTR_RE, APPLY_RE

    GLOBS = configuration.get("globs", [])
    SKIP_EXPRESSIONS = configuration.get("skip_expressions", [])
    VARIANT_SEP = configuration.get("variant_sep", ":")
    GROUP_ORDER = configuration.get("group_order", [])
    GROUP_PATTERNS = [re.compile("^" + g) for g in GROUP_ORDER]
    VARIANT_PREFIX_ORDER = configuration.get("variant_prefix_order", [])
    VARIANT_PATTERNS = [re.compile(v) for v in VARIANT_PREFIX_ORDER]
    TAILWIND_COLORS = set(configuration.get("tailwind_colors", []))

    CLASS_ATTR_RE = re.compile(
        configuration.get("class_attr_re", r"""(?P<full>\bclass\s*=\s*(?P<quote>["'])(?P<val>.*?)(?P=quote))"""),
        re.IGNORECASE | re.DOTALL,
    )

    APPLY_RE = re.compile(
        configuration.get("apply_re", r"""@apply\s+(?P<classes>[^;]+);"""),
        re.MULTILINE,
    )


# Initialize constants on module load
_update_constants()

# Export constants (initialized by _update_constants())
GLOBS: list[str]
SKIP_EXPRESSIONS: list[str]
VARIANT_SEP: str
GROUP_ORDER: list[str]
GROUP_PATTERNS: list[re.Pattern]
VARIANT_PREFIX_ORDER: list[str]
VARIANT_PATTERNS: list[re.Pattern]
TAILWIND_COLORS: set[str]
CLASS_ATTR_RE: re.Pattern
APPLY_RE: re.Pattern

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

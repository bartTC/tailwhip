"""Constants used by tailwhip."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib
from rich.theme import Theme


def _load_config() -> dict:
    """Load configuration from constants.toml file."""
    config_path = Path(__file__).parent / "constants.toml"
    with config_path.open("rb") as f:
        return tomllib.load(f)


# Load configuration
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

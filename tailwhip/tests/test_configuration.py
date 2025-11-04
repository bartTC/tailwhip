"""Tests for dynaconf configuration system.

This test module provides comprehensive coverage of the configuration loading system,
which uses dynaconf to manage settings from multiple sources with proper priority.

Test Coverage:
--------------

No Settings (Defaults):
    - test_default_configuration: Verifies defaults load correctly from configuration.toml

Custom Config Tests:
    - test_custom_config_valid: Valid custom config overrides defaults
    - test_custom_config_partial_override: Partial overrides work correctly
    - test_custom_config_missing_file: Missing file raises FileNotFoundError
    - test_custom_config_invalid_toml: Invalid TOML syntax raises error
    - test_empty_custom_config: Empty file uses all defaults

Pyproject.toml Tests:
    - test_pyproject_toml_valid: Valid [tool.tailwhip] section works
    - test_pyproject_toml_invalid_syntax: Invalid TOML raises error
    - test_pyproject_toml_no_tailwhip_section: No section = uses defaults
    - test_search_path_parent_directory: Finds pyproject.toml in parent dirs

Combined Tests (pyproject + custom):
    - test_custom_and_pyproject_both_valid: Custom overrides pyproject
    - test_custom_invalid_pyproject_valid: Invalid custom fails
    - test_custom_valid_pyproject_invalid: Invalid pyproject fails
    - test_configuration_priority_chain: Full priority: custom > pyproject > defaults

Additional Features:
    - test_custom_colors_configuration: Custom Tailwind colors
    - test_regex_patterns_compilation: Regex patterns compile correctly
    - test_group_and_variant_patterns: Pattern lists compile
    - test_environment_variable_override: ENV vars work (TAILWHIP_ prefix)
    - test_reload_resets_previous_config: Reload properly resets state

Key Features Tested:
--------------------
✓ Configuration priority chain (custom > pyproject.toml > defaults)
✓ File validation and error handling
✓ TOML syntax validation
✓ Partial overrides (only override what you need)
✓ Parent directory discovery (walks up from search_path)
✓ Environment variable support (TAILWHIP_* variables)
✓ State reset on reload (no config leakage between calls)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tailwhip import configuration

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for config files."""
    return tmp_path


@pytest.fixture(autouse=True)
def reset_constants() -> None:
    """Reset constants to defaults after each test."""
    yield
    # Reload with no custom config to reset to defaults
    configuration.reload_config()


def test_default_configuration(temp_config_dir: Path) -> None:
    """Test that default configuration loads correctly."""
    configuration.reload_config(search_path=temp_config_dir)

    # Verify defaults from configuration.toml
    assert configuration.GLOBS == ["**/*.html", "**/*.css"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%"]
    assert configuration.VARIANT_SEP == ":"
    assert len(configuration.GROUP_ORDER) > 0
    assert len(configuration.TAILWIND_COLORS) > 0


def test_custom_config_valid(temp_config_dir: Path) -> None:
    """Test loading a valid custom config file."""
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
globs = ["**/*.jsx", "**/*.tsx"]
skip_expressions = ["{{", "{%", "<%", "<?"]

[tailwind_colors]
# Add custom colors to existing ones
""")

    configuration.reload_config(custom_config, temp_config_dir)

    # Custom config should override defaults
    assert configuration.GLOBS == ["**/*.jsx", "**/*.tsx"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%", "<?"]
    # Other values should remain default
    assert configuration.VARIANT_SEP == ":"


def test_custom_config_partial_override(temp_config_dir: Path) -> None:
    """Test that custom config can partially override defaults."""
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
# Only override globs, keep other defaults
globs = ["**/*.vue"]
""")

    configuration.reload_config(custom_config, temp_config_dir)

    assert configuration.GLOBS == ["**/*.vue"]
    # Everything else should be default
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%"]
    assert configuration.VARIANT_SEP == ":"


def test_custom_config_missing_file(temp_config_dir: Path) -> None:
    """Test that missing custom config file raises FileNotFoundError."""
    nonexistent = temp_config_dir / "nonexistent.toml"

    with pytest.raises(FileNotFoundError, match="Custom config file not found"):
        configuration.reload_config(nonexistent, temp_config_dir)


def test_custom_config_invalid_toml(temp_config_dir: Path) -> None:
    """Test that invalid TOML syntax raises an error."""
    custom_config = temp_config_dir / "invalid.toml"
    custom_config.write_text("""
globs = ["**/*.html"  # Missing closing bracket
invalid syntax here
""")

    with pytest.raises(Exception):  # Dynaconf/tomllib will raise
        configuration.reload_config(custom_config, temp_config_dir)


def test_pyproject_toml_valid(temp_config_dir: Path) -> None:
    """Test loading valid pyproject.toml with [tool.tailwhip] section."""
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"

[tool.tailwhip]
globs = ["**/*.html", "**/*.jinja2"]
skip_expressions = ["{{", "{%", "{#"]
""")

    configuration.reload_config(search_path=temp_config_dir)

    assert configuration.GLOBS == ["**/*.html", "**/*.jinja2"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "{#"]


def test_pyproject_toml_invalid_syntax(temp_config_dir: Path) -> None:
    """Test that invalid TOML syntax in pyproject.toml is handled."""
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[project
name = "test-project"  # Missing closing bracket
""")

    # Should handle gracefully or raise appropriate error
    with pytest.raises(Exception):
        configuration.reload_config(search_path=temp_config_dir)


def test_pyproject_toml_no_tailwhip_section(temp_config_dir: Path) -> None:
    """Test pyproject.toml without [tool.tailwhip] section uses defaults."""
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "test-project"
version = "1.0.0"

[tool.other]
setting = "value"
""")

    configuration.reload_config(search_path=temp_config_dir)

    # Should use defaults since no [tool.tailwhip] section
    assert configuration.GLOBS == ["**/*.html", "**/*.css"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%"]


def test_custom_and_pyproject_both_valid(temp_config_dir: Path) -> None:
    """Test that custom config overrides pyproject.toml (priority)."""
    # Create pyproject.toml
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[tool.tailwhip]
globs = ["**/*.html", "**/*.jinja2"]
skip_expressions = ["{{", "{%"]
variant_sep = ":"
""")

    # Create custom config that overrides pyproject
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
globs = ["**/*.vue"]
skip_expressions = ["{{", "{%", "<%", "<?"]
""")

    configuration.reload_config(custom_config, temp_config_dir)

    # Custom config should win
    assert configuration.GLOBS == ["**/*.vue"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%", "<?"]
    # Values not in custom should come from pyproject/defaults
    assert configuration.VARIANT_SEP == ":"


def test_custom_invalid_pyproject_valid(temp_config_dir: Path) -> None:
    """Test that invalid custom config fails even if pyproject.toml is valid."""
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[tool.tailwhip]
globs = ["**/*.html"]
""")

    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
globs = ["**/*.html"  # Invalid syntax
""")

    with pytest.raises(Exception):
        configuration.reload_config(custom_config, temp_config_dir)


def test_custom_valid_pyproject_invalid(temp_config_dir: Path) -> None:
    """Test that valid custom config is used even if pyproject.toml is invalid."""
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[tool.tailwhip
globs = invalid  # Invalid syntax
""")

    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
globs = ["**/*.vue"]
""")

    # Custom config should load, but pyproject error should propagate
    with pytest.raises(Exception):
        configuration.reload_config(custom_config, temp_config_dir)


def test_configuration_priority_chain(temp_config_dir: Path) -> None:
    """Test complete priority chain: custom > pyproject > defaults."""
    # Set up pyproject that overrides some defaults
    pyproject = temp_config_dir / "pyproject.toml"
    pyproject.write_text("""
[tool.tailwhip]
globs = ["**/*.html", "**/*.jinja2"]
skip_expressions = ["{{", "{%", "{#"]
""")

    # Set up custom that overrides only globs
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
globs = ["**/*.vue"]
""")

    configuration.reload_config(custom_config, temp_config_dir)

    # Priority chain should work:
    # - globs: from custom (highest priority)
    # - skip_expressions: from pyproject (middle priority)
    # - variant_sep: from defaults (lowest priority)
    assert configuration.GLOBS == ["**/*.vue"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "{#"]
    assert configuration.VARIANT_SEP == ":"


def test_custom_colors_configuration(temp_config_dir: Path) -> None:
    """Test configuring custom Tailwind colors."""
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
tailwind_colors = [
    "transparent", "current", "black", "white",
    "brand", "company", "accent"
]
""")

    configuration.reload_config(custom_config, temp_config_dir)

    assert "brand" in configuration.TAILWIND_COLORS
    assert "company" in configuration.TAILWIND_COLORS
    assert "accent" in configuration.TAILWIND_COLORS
    # Note: This replaces the list, not extends it
    assert len(configuration.TAILWIND_COLORS) == 7


def test_regex_patterns_compilation(temp_config_dir: Path) -> None:
    """Test that regex patterns are properly compiled from config."""
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
class_attr_re = '''(?P<full>\\bclass\\s*=\\s*(?P<quote>["'])(?P<val>.*?)(?P=quote))'''
apply_re = '''@apply\\s+(?P<classes>[^;]+);'''
""")

    configuration.reload_config(custom_config, temp_config_dir)

    # Verify patterns are compiled and work
    assert configuration.CLASS_ATTR_RE.pattern
    assert configuration.APPLY_RE.pattern

    # Test they actually match
    assert configuration.CLASS_ATTR_RE.search('class="flex p-4"')
    assert configuration.APPLY_RE.search("@apply flex p-4;")


def test_group_and_variant_patterns(temp_config_dir: Path) -> None:
    """Test that group_order and variant_prefix_order are compiled to patterns."""
    custom_config = temp_config_dir / "custom.toml"
    custom_config.write_text("""
group_order = ["(container)", "(flex|grid)"]
variant_prefix_order = ["sm:", "md:", "lg:"]
""")

    configuration.reload_config(custom_config, temp_config_dir)

    assert len(configuration.GROUP_PATTERNS) == 2
    assert len(configuration.VARIANT_PATTERNS) == 3

    # Verify patterns work
    assert configuration.GROUP_PATTERNS[0].match("container")
    assert configuration.GROUP_PATTERNS[1].match("flex")
    assert configuration.VARIANT_PATTERNS[0].match("sm:")


def test_environment_variable_override(
    temp_config_dir: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test that environment variables can override config (TAILWHIP_ prefix)."""
    monkeypatch.setenv("TAILWHIP_VARIANT_SEP", "|")

    configuration.reload_config(search_path=temp_config_dir)

    # Environment variable should override default
    assert configuration.VARIANT_SEP == "|"


def test_empty_custom_config(temp_config_dir: Path) -> None:
    """Test that empty custom config file uses all defaults."""
    custom_config = temp_config_dir / "empty.toml"
    custom_config.write_text("# Empty config file\n")

    configuration.reload_config(custom_config, temp_config_dir)

    # Should use all defaults
    assert configuration.GLOBS == ["**/*.html", "**/*.css"]
    assert configuration.SKIP_EXPRESSIONS == ["{{", "{%", "<%"]


def test_search_path_parent_directory(tmp_path: Path) -> None:
    """Test that pyproject.toml is found in parent directories."""
    # Create nested directory structure
    root = tmp_path / "project"
    root.mkdir()
    subdir = root / "src" / "components"
    subdir.mkdir(parents=True)

    # Put pyproject.toml in root
    pyproject = root / "pyproject.toml"
    pyproject.write_text("""
[tool.tailwhip]
globs = ["**/*.component.html"]
""")

    # Search from subdirectory - should find parent pyproject.toml
    configuration.reload_config(search_path=subdir)

    assert configuration.GLOBS == ["**/*.component.html"]


def test_reload_resets_previous_config(temp_config_dir: Path) -> None:
    """Test that reload_config properly resets previous configuration."""
    # First, load custom config
    custom1 = temp_config_dir / "custom1.toml"
    custom1.write_text("""
globs = ["**/*.vue"]
skip_expressions = ["{{", "{%", "<%", "<?", "{#"]
""")

    configuration.reload_config(custom1, temp_config_dir)
    assert len(configuration.SKIP_EXPRESSIONS) == 5

    # Now reload with different config
    custom2 = temp_config_dir / "custom2.toml"
    custom2.write_text("""
globs = ["**/*.jsx"]
skip_expressions = ["{{"]
""")

    configuration.reload_config(custom2, temp_config_dir)

    # Should completely replace previous config
    assert configuration.GLOBS == ["**/*.jsx"]
    assert configuration.SKIP_EXPRESSIONS == ["{{"]
    assert len(configuration.SKIP_EXPRESSIONS) == 1  # Not merged, replaced

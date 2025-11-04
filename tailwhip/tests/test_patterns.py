"""
Tests for custom pattern configuration.

This module tests that users can add custom patterns via configuration to support
different frameworks and syntaxes (JSX, Vue, Svelte, etc.).

Test Coverage:
- Custom patterns via pyproject.toml ([[tool.tailwhip.class_patterns]])
- Custom patterns via custom config file ([[class_patterns]])
- Pattern compilation and loading into config.APPLY_PATTERNS
- Pattern functionality (HTML class, CSS @apply, custom JSX className)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tailwhip.configuration import (
    BASE_CONFIGURATION_FILE,
    config,
    get_pyproject_toml_data,
    update_configuration,
)
from tailwhip.process import process_text

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset configuration to defaults before each test to avoid test pollution."""
    # Reload base configuration
    update_configuration(BASE_CONFIGURATION_FILE)


def test_custom_pattern_from_pyproject(tmp_path: Path) -> None:
    """Test that custom patterns can be added via pyproject.toml configuration."""
    # Create pyproject.toml with custom JSX className pattern
    # Note: Must include default patterns too, as class_patterns replaces (not extends) defaults
    # Note: Use [[tool.tailwhip.class_patterns]] to nest array-of-tables under tool.tailwhip
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
# Include default patterns
[[tool.tailwhip.class_patterns]]
name = "html_class"
regex = '''\\bclass\\s*=\\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'class={quote}{classes}{quote}'

[[tool.tailwhip.class_patterns]]
name = "css_apply"
regex = '''@apply\\s+(?P<classes>[^;]+);'''
template = '@apply {classes};'

# Add custom JSX pattern
[[tool.tailwhip.class_patterns]]
name = "jsx_classname"
regex = '''\\bclassName\\s*=\\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'className={quote}{classes}{quote}'
"""
    )

    # Load the pyproject.toml configuration
    pyproject_data = get_pyproject_toml_data(tmp_path)
    assert pyproject_data is not None

    # Update configuration with pyproject data
    update_configuration(pyproject_data)

    # Verify custom pattern is loaded in config
    assert len(config.APPLY_PATTERNS) == 3  # html_class, css_apply, jsx_classname
    pattern_names = [p.name for p in config.APPLY_PATTERNS]
    assert "html_class" in pattern_names
    assert "css_apply" in pattern_names
    assert "jsx_classname" in pattern_names

    # Test that all patterns work with UNSORTED classes
    jsx_input = '<Component className="p-4 m-2 flex" />'
    jsx_output = process_text(jsx_input)
    assert jsx_output == '<Component className="flex m-2 p-4" />'

    html_input = '<div class="p-4 m-2 flex"></div>'
    html_output = process_text(html_input)
    assert html_output == '<div class="flex m-2 p-4"></div>'

    css_input = ".btn { @apply p-4 m-2 flex; }"
    css_output = process_text(css_input)
    assert css_output == ".btn { @apply flex m-2 p-4; }"


def test_custom_pattern_from_config_file(tmp_path: Path) -> None:
    """Test that custom patterns can be added via custom configuration file."""
    # Create custom config file with custom JSX className pattern
    # Note: Must include default patterns too, as class_patterns replaces (not extends) defaults
    # Note: Use [[class_patterns]] (not [[tool.tailwhip.class_patterns]]) in custom config files
    custom_config = tmp_path / "tailwhip.toml"
    custom_config.write_text(
        """
# Include default patterns
[[class_patterns]]
name = "html_class"
regex = '''\\bclass\\s*=\\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'class={quote}{classes}{quote}'

[[class_patterns]]
name = "css_apply"
regex = '''@apply\\s+(?P<classes>[^;]+);'''
template = '@apply {classes};'

# Add custom JSX pattern
[[class_patterns]]
name = "jsx_classname"
regex = '''\\bclassName\\s*=\\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'className={quote}{classes}{quote}'
"""
    )

    # Load the custom configuration file directly
    update_configuration(custom_config)

    # Verify custom pattern is loaded in config
    assert len(config.APPLY_PATTERNS) == 3  # html_class, css_apply, jsx_classname
    pattern_names = [p.name for p in config.APPLY_PATTERNS]
    assert "html_class" in pattern_names
    assert "css_apply" in pattern_names
    assert "jsx_classname" in pattern_names

    # Test that all patterns work with UNSORTED classes
    jsx_input = '<Component className="p-4 m-2 flex" />'
    jsx_output = process_text(jsx_input)
    assert jsx_output == '<Component className="flex m-2 p-4" />'

    html_input = '<div class="p-4 m-2 flex"></div>'
    html_output = process_text(html_input)
    assert html_output == '<div class="flex m-2 p-4"></div>'

    css_input = ".btn { @apply p-4 m-2 flex; }"
    css_output = process_text(css_input)
    assert css_output == ".btn { @apply flex m-2 p-4; }"

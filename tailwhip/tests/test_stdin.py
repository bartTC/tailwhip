"""
Tests for stdin mode functionality.

This module tests the stdin/stdout filter mode, which allows tailwhip
to be used as a text filter in editor integrations and command pipelines.

Test Coverage:
- Basic stdin/stdout sorting for HTML
- CSS @apply directive sorting via stdin
- Empty input handling
- Multiline content preservation
"""

from __future__ import annotations

from typer.testing import CliRunner

from tailwhip.cli import app

runner = CliRunner()


def test_stdin_mode_sorts_classes() -> None:
    """Test that stdin mode reads from stdin and outputs sorted classes to stdout."""
    input_html = '<div class="p-4 m-2 bg-white text-lg font-bold"></div>'
    expected_output = '<div class="m-2 p-4 font-bold text-lg bg-white"></div>'

    result = runner.invoke(app, [], input=input_html)

    assert result.exit_code == 0
    assert result.output == expected_output


def test_stdin_mode_with_css() -> None:
    """Test that stdin mode works with CSS @apply directives."""
    input_css = ".btn { @apply text-white p-4 m-2 rounded bg-blue-500; }"
    expected_output = ".btn { @apply m-2 p-4 text-white bg-blue-500 rounded; }"

    result = runner.invoke(app, [], input=input_css)

    assert result.exit_code == 0
    assert result.output == expected_output


def test_stdin_mode_with_empty_input() -> None:
    """Test that stdin mode handles empty input gracefully."""
    result = runner.invoke(app, [], input="")

    assert result.exit_code == 0
    assert result.output == ""


def test_stdin_mode_with_multiline_html() -> None:
    """Test that stdin mode preserves formatting across multiple lines."""
    input_html = """<div class="p-4 m-2 bg-white">
    <span class="font-bold text-lg text-gray-900"></span>
</div>"""
    expected_output = """<div class="m-2 p-4 bg-white">
    <span class="font-bold text-lg text-gray-900"></span>
</div>"""

    result = runner.invoke(app, [], input=input_html)

    assert result.exit_code == 0
    assert result.output == expected_output

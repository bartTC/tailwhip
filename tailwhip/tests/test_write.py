"""
Tests for file writing functionality.

This module tests the full write cycle: reading files, sorting classes,
and writing the changes back to disk.

Test Coverage:
- End-to-end write functionality with --write flag
- HTML class attribute sorting
- CSS @apply directive sorting
- Multiple elements with various Tailwind utilities
- Preservation of non-class content
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tailwhip.cli import app

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

# Unsorted HTML with various Tailwind classes (intentionally messy)
UNSORTED_HTML = """<style>
    .btn { @apply px-4 py-2 rounded-lg font-semibold
                  bg-blue-500 text-white hover:bg-blue-600
                  focus:ring-2 active:scale-95; }
    .card { @apply shadow-lg p-6 rounded-xl bg-white border-2 border-gray-200 hover:shadow-xl; }
</style>
<div class="p-4 mx-auto container max-w-4xl
            lg:max-w-6xl dark:bg-gray-900">
    <h1 class="font-bold text-3xl mb-4 text-gray-900 dark:text-white sm:text-4xl md:text-5xl">Title</h1>
    <button class="transition-all px-6 py-3 rounded-md font-medium bg-indigo-500 text-white hover:bg-indigo-600 focus:ring-2 focus:ring-indigo-500 active:scale-95 disabled:opacity-50">Click</button>
</div>
"""

# Expected sorted HTML (classes sorted according to Tailwind conventions)
SORTED_HTML = """<style>
    .btn { @apply px-4 py-2 font-semibold text-white bg-blue-500 rounded-lg active:scale-95 focus:ring-2 hover:bg-blue-600; }
    .card { @apply p-6 bg-white rounded-xl border-2 border-gray-200 shadow-lg hover:shadow-xl; }
</style>
<div class="container max-w-4xl mx-auto p-4 dark:bg-gray-900 lg:max-w-6xl">
    <h1 class="mb-4 font-bold text-3xl text-gray-900 dark:text-white sm:text-4xl md:text-5xl">Title</h1>
    <button class="px-6 py-3 font-medium text-white bg-indigo-500 rounded-md transition-all disabled:opacity-50 active:scale-95 focus:ring-2 focus:ring-indigo-500 hover:bg-indigo-600">Click</button>
</div>
"""


@pytest.fixture
def html_file(tmp_path: Path) -> Path:
    """Create a temporary HTML file with unsorted Tailwind classes."""
    test_file = tmp_path / "test.html"
    test_file.write_text(UNSORTED_HTML)
    return test_file


def test_write_mode_sorts_and_saves(html_file: Path) -> None:
    """Test that --write flag sorts classes and saves changes to file."""
    # Run CLI with --write flag
    result = runner.invoke(app, [str(html_file), "-vv", "--write"])

    # Command should succeed
    assert result.exit_code == 0

    # Read the file content after processing
    actual_output = html_file.read_text()

    # Content should match expected sorted HTML
    assert actual_output == SORTED_HTML


def test_dry_run_does_not_modify_file(html_file: Path) -> None:
    """Test that dry-run mode (default) does not modify the file."""
    # Store original content
    original_content = html_file.read_text()

    # Run CLI without --write flag (dry-run mode)
    result = runner.invoke(app, [str(html_file), "-vv"])

    # Command should succeed
    assert result.exit_code == 0

    # File content should remain unchanged
    actual_content = html_file.read_text()
    assert actual_content == original_content

    # Output should indicate dry-run mode
    assert "Dry Run" in result.output or "dry" in result.output.lower()


def test_write_mode_multiple_files(tmp_path: Path) -> None:
    """Test that --write processes multiple files correctly."""
    # Create multiple test files
    file1 = tmp_path / "file1.html"
    file2 = tmp_path / "file2.html"

    file1.write_text('<div class="p-4 m-2 bg-white"></div>')
    file2.write_text('<div class="text-lg font-bold text-gray-900"></div>')

    # Run CLI with --write on directory
    result = runner.invoke(app, [str(tmp_path), "--write"])

    # Command should succeed
    assert result.exit_code == 0

    # Both files should be sorted
    assert file1.read_text() == '<div class="m-2 p-4 bg-white"></div>'
    assert file2.read_text() == '<div class="font-bold text-lg text-gray-900"></div>'

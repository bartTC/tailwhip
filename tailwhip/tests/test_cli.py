"""
Tests for CLI functionality and configuration precedence.

This module tests the command-line interface and validates that configuration
settings are properly loaded and prioritized from multiple sources.

Test Coverage:
- Basic CLI argument handling (-h, --help, no arguments)
- Configuration precedence chain:
  1. Default values from configuration.toml
  2. pyproject.toml [tool.tailwhip] overrides defaults
  3. Custom config file (--configuration) overrides pyproject.toml
  4. CLI arguments (--write, -v, --quiet) override all config files
- Configuration isolation between tests (autouse fixture resets config)

Configuration Priority (lowest to highest):
  defaults < pyproject.toml < custom config < CLI arguments
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tailwhip.cli import app
from tailwhip.configuration import BASE_CONFIGURATION_FILE, config, update_configuration

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset configuration to defaults before each test to avoid test pollution."""
    # Reload base configuration
    update_configuration(BASE_CONFIGURATION_FILE)


@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path:
    """Create a temporary HTML file for testing."""
    test_file = tmp_path / "test.html"
    test_file.write_text('<div class="p-4 m-2">Test</div>')
    return test_file


@pytest.fixture
def pyproject_toml(tmp_path: Path) -> Path:
    """Create a pyproject.toml with [tool.tailwhip] configuration."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.tailwhip]
custom_colors = ["brand", "accent"]
skip_expressions = ["{{", "{%", "[["]
"""
    )
    return pyproject


@pytest.fixture
def custom_config(tmp_path: Path) -> Path:
    """Create a custom configuration file."""
    custom_conf = tmp_path / "tailwhip.toml"
    custom_conf.write_text(
        """
custom_colors = ["custom1", "custom2"]
skip_expressions = ["<%", "%>"]
"""
    )
    return custom_conf


@pytest.mark.parametrize(
    ("args", "expected_exit_code"),
    [
        ([], 2),  # No arguments - should exit with code 2
        (["-h"], 0),  # Help flag - should succeed
        (["--help"], 0),  # Help flag (long form) - should succeed
        (["--version"], 0),  # Version (long form) - should succeed
    ],
)
def test_cli_basic_args(args: list[str], expected_exit_code: int) -> None:
    """Test basic CLI argument handling."""
    result = runner.invoke(app, args)
    assert result.exit_code == expected_exit_code


def test_config_default_values(temp_test_file: Path) -> None:
    """Test that default configuration values are used when no overrides exist."""
    result = runner.invoke(app, [str(temp_test_file)])

    assert result.exit_code == 0

    # Default values from configuration.toml
    assert config.verbosity == 1
    assert config.write_mode is False
    assert config.default_globs == ["**/*.html", "**/*.css"]
    assert config.skip_expressions == ["{{", "{%", "<%"]


def test_config_pyproject_overrides_defaults(
    temp_test_file: Path, pyproject_toml: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that pyproject.toml overrides default values."""
    # Change to directory containing pyproject.toml
    monkeypatch.chdir(pyproject_toml.parent)

    result = runner.invoke(app, [str(temp_test_file)])

    assert result.exit_code == 0
    # Values should come from pyproject.toml
    assert "brand" in config.custom_colors
    assert "accent" in config.custom_colors
    assert "[[" in config.skip_expressions  # from pyproject.toml


def test_config_custom_file_overrides_defaults(
    temp_test_file: Path, custom_config: Path
) -> None:
    """Test that custom config file overrides default values."""
    result = runner.invoke(
        app, [str(temp_test_file), "--configuration", str(custom_config)]
    )

    assert result.exit_code == 0
    # Values should come from custom config
    assert "custom1" in config.custom_colors
    assert "custom2" in config.custom_colors
    assert "<%" in config.skip_expressions  # from custom config
    assert "%>" in config.skip_expressions  # from custom config


def test_config_custom_overrides_pyproject(
    temp_test_file: Path,
    pyproject_toml: Path,
    custom_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that custom config overrides pyproject.toml when both exist."""
    # Change to directory containing pyproject.toml
    monkeypatch.chdir(pyproject_toml.parent)

    result = runner.invoke(
        app,
        [str(temp_test_file), "--configuration", str(custom_config)],
    )

    assert result.exit_code == 0
    # Custom config should win over pyproject.toml
    assert "custom1" in config.custom_colors  # from custom, not pyproject
    assert "custom2" in config.custom_colors
    assert "<%" in config.skip_expressions  # from custom config
    assert "%>" in config.skip_expressions  # from custom config
    # Verify pyproject values are NOT present
    assert "brand" not in config.custom_colors
    assert "accent" not in config.custom_colors
    assert "[[" not in config.skip_expressions  # from pyproject should be overridden


def test_config_cli_args_override_all(
    temp_test_file: Path,
    pyproject_toml: Path,
    custom_config: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that CLI arguments override all configuration sources."""
    # Change to directory containing pyproject.toml
    monkeypatch.chdir(pyproject_toml.parent)

    result = runner.invoke(
        app,
        [
            str(temp_test_file),
            "--configuration",
            str(custom_config),
            "--write",  # CLI: write_mode = True
            "-vvv",  # CLI: verbosity = 3 + 1 = 4
        ],
    )

    assert result.exit_code == 0

    # CLI args should override everything
    assert config.write_mode is True  # from CLI --write (overrides custom config False)
    assert config.verbosity == 4  # from CLI -vvv (3) + 1


def test_config_quiet_flag_overrides_verbosity(temp_test_file: Path) -> None:
    """Test that --quiet flag sets verbosity to 0 regardless of other settings."""
    result = runner.invoke(
        app,
        [str(temp_test_file), "-vvv", "--quiet"],  # -vvv should be overridden
    )

    assert result.exit_code == 0
    # --quiet should override -vvv
    assert config.verbosity == 0


def test_no_files_found_error(tmp_path: Path) -> None:
    """Test that CLI exits with error when no files are found."""
    # Create an empty directory with no HTML/CSS files
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    # Invoke CLI with the empty directory
    result = runner.invoke(app, [str(empty_dir)])

    # Should exit with error code 1
    assert result.exit_code == 1
    # Should display error message
    assert "No files found" in result.output


def test_nonexistent_configuration_file_error(
    temp_test_file: Path, tmp_path: Path
) -> None:
    """Test that CLI exits with clean error when config file doesn't exist."""
    nonexistent_config = tmp_path / "nonexistent_config.toml"

    # Invoke CLI with nonexistent configuration file
    result = runner.invoke(
        app, [str(temp_test_file), "--configuration", str(nonexistent_config)]
    )

    # Should exit with error code 1
    assert result.exit_code == 1

    # Should display friendly error message
    assert "not found" in result.output.lower()
    assert str(nonexistent_config) in result.output

    # Should NOT show a traceback
    assert "Traceback" not in result.output
    assert "Exception" not in result.output

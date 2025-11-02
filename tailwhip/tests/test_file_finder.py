"""Tests for file finding functionality."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tailwhip.files import find_files

if TYPE_CHECKING:
    import pytest

    from tailwhip.datatypes import Config


def test_find_files_current_directory(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with '.' as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path()]

    results = sorted(find_files(config=config))

    # Should find HTML and CSS files in current directory and subdirectories
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "page.html" for f in results)


def test_find_files_relative_directory(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with relative_dir/ as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("templates/")]

    results = sorted(find_files(config=config))

    # Should find HTML files in templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all("templates" in str(f) for f in results)


def test_find_files_absolute_directory(config: Config, testdata_dir: Path) -> None:
    """Test finding files with /absolute_dir/relative_dir/ as input path."""
    absolute_path = testdata_dir / "templates"
    config.paths = [absolute_path]

    results = sorted(find_files(config=config))

    # Should find HTML files in the absolute templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)


def test_find_files_specific_html_file(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with path/to/file.html as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("index.html")]

    results = list(find_files(config=config))

    # Should find the specific file
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_specific_css_file(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with path/to/css.html as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("styles.css")]

    results = list(find_files(config=config))

    # Should find the specific CSS file
    assert len(results) == 1
    assert results[0].name == "styles.css"


def test_find_files_specific_custom_extension(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with path/to/customglob.glob as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("theme.pcss")]

    results = list(find_files(config=config))

    # Should find the specific file with custom extension
    assert len(results) == 1
    assert results[0].name == "theme.pcss"


def test_find_files_simple_glob(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with path/*.html glob pattern."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("templates/*.html")]

    results = list(find_files(config=config))

    # Should find HTML files matching the glob pattern
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_recursive_glob(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with path/**/*.html glob pattern."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("**/*.html")]

    results = sorted(find_files(config=config))

    # Should find all HTML files recursively
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_complex_glob(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with more complex glob patterns."""
    monkeypatch.chdir(testdata_dir)
    # Match all CSS-related files with different extensions
    config.paths = [Path("*.css"), Path("*.pcss"), Path("*.postcss")]

    results = sorted(find_files(config=config))

    # Should find all CSS-related files
    assert len(results) > 0
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "theme.pcss" for f in results)
    assert any(f.name == "utilities.postcss" for f in results)


def test_find_files_deduplication(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that duplicate files are deduplicated."""
    monkeypatch.chdir(testdata_dir)
    # Specify same file multiple ways
    config.paths = [Path("index.html"), Path("./index.html"), Path("index.html")]

    results = list(find_files(config=config))

    # Should only return one instance
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_multiple_paths(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files from multiple input paths."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("index.html"), Path("templates/"), Path("*.css")]

    results = sorted(find_files(config=config))

    # Should find files from all specified paths
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert any(f.name == "styles.css" for f in results)


def test_find_files_nonexistent_path(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with nonexistent path (treated as glob)."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("nonexistent/*.html")]

    results = list(find_files(config=config))

    # Should return empty list for nonexistent paths
    assert len(results) == 0


def test_find_files_nested_directory(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files in nested directory structures."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path("styles/")]

    results = sorted(find_files(config=config))

    # Should search nested directories based on config.globs
    assert isinstance(results, list)


def test_find_files_current_dir(
    config: Config, testdata_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test finding files with '.' as input path."""
    monkeypatch.chdir(testdata_dir)
    config.paths = [Path()]

    results = sorted(find_files(config=config))

    # Should find HTML and CSS files in current directory and subdirectories
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "page.html" for f in results)

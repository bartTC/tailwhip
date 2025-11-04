"""Tests for file finding functionality."""

from __future__ import annotations

from pathlib import Path

from tailwhip.files import find_files
from tailwhip.tests.conftest import update_config


def test_find_files_current_directory() -> None:
    """Test finding files with '.' as input path."""
    update_config(paths=[Path()])

    results = sorted(find_files())

    # Should find HTML and CSS files in current directory and subdirectories
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "page.html" for f in results)


def test_find_files_relative_directory() -> None:
    """Test finding files with relative_dir/ as input path."""
    update_config(paths=[Path("templates/")])

    results = sorted(find_files())

    # Should find HTML files in templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all("templates" in str(f) for f in results)


def test_find_files_absolute_directory(testdata_dir: Path) -> None:
    """Test finding files with /absolute_dir/relative_dir/ as input path."""
    absolute_path = testdata_dir / "templates"
    update_config(paths=[absolute_path])

    results = sorted(find_files())

    # Should find HTML files in the absolute templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)


def test_find_files_specific_html_file() -> None:
    """Test finding files with path/to/file.html as input path."""
    update_config(paths=[Path("index.html")])

    results = list(find_files())

    # Should find the specific file
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_specific_css_file() -> None:
    """Test finding files with path/to/css.html as input path."""
    update_config(paths=[Path("styles.css")])

    results = list(find_files())

    # Should find the specific CSS file
    assert len(results) == 1
    assert results[0].name == "styles.css"


def test_find_files_specific_custom_extension() -> None:
    """Test finding files with path/to/customglob.glob as input path."""
    update_config(paths=[Path("theme.pcss")])

    results = list(find_files())

    # Should find the specific file with custom extension
    assert len(results) == 1
    assert results[0].name == "theme.pcss"


def test_find_files_simple_glob() -> None:
    """Test finding files with path/*.html glob pattern."""
    update_config(paths=[Path("templates/*.html")])
    results = list(find_files())

    # Should find HTML files matching the glob pattern
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_recursive_glob() -> None:
    """Test finding files with path/**/*.html glob pattern."""
    update_config(paths=[Path("**/*.html")])

    results = sorted(find_files())

    # Should find all HTML files recursively
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_complex_glob() -> None:
    """Test finding files with more complex glob patterns."""
    update_config(paths=[Path("*.css"), Path("*.pcss"), Path("*.postcss")])

    results = sorted(find_files())

    # Should find all CSS-related files
    assert len(results) > 0
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "theme.pcss" for f in results)
    assert any(f.name == "utilities.postcss" for f in results)


def test_find_files_deduplication() -> None:
    """Test that duplicate files are deduplicated."""
    update_config(paths=[Path("index.html"), Path("./index.html"), Path("index.html")])

    results = list(find_files())

    # Should only return one instance
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_multiple_paths() -> None:
    """Test finding files from multiple input paths."""
    update_config(paths=[Path("index.html"), Path("templates/"), Path("*.css")])

    results = sorted(find_files())

    # Should find files from all specified paths
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert any(f.name == "styles.css" for f in results)


def test_find_files_nonexistent_path() -> None:
    """Test finding files with nonexistent path (treated as glob)."""
    update_config(paths=[Path("nonexistent/*.html")])

    results = list(find_files())

    # Should return empty list for nonexistent paths
    assert len(results) == 0


def test_find_files_nested_directory() -> None:
    """Test finding files in nested directory structures."""
    update_config(paths=[Path("styles/")])

    results = sorted(find_files())

    # Should search nested directories based on config.globs
    assert isinstance(results, list)


def test_find_nested_but_not_direct_child() -> None:
    """Select child directory which is not an immediate child,.

    Select a directory which is not an immediate child, does not fail.
    This is a regression test for a glob pattern bug.
    """
    # Components exists in './styles/component'. In an earlier version it was
    # discovered, but paths were unable to be resolved.
    update_config(paths=[Path("components")])

    results = sorted(find_files())

    # Should not error out but also not find any files
    assert isinstance(results, list)
    assert len(results) == 0


def test_find_files_current_dir() -> None:
    """Test finding files with '.' as input path."""
    update_config(paths=[Path()])

    results = sorted(find_files())

    # Should find HTML and CSS files in current directory and subdirectories
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "page.html" for f in results)

"""
Tests for file finding functionality.

This module tests the file discovery mechanism that locates HTML and CSS files
for processing based on various input patterns.

Test Coverage:
- Directory scanning (current directory, relative paths, absolute paths)
- Specific file targeting (individual HTML/CSS files)
- Glob pattern matching (*.html, **/*.css, custom extensions)
- Path deduplication (same file specified multiple ways)
- Multiple path inputs processed together
- Edge cases (nonexistent paths, nested directories, empty directories)

All tests run in an isolated temporary directory created by the testdata_dir
fixture. Files are created on-demand with empty content, keeping the repository
clean and avoiding test pollution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tailwhip.files import find_files


@pytest.fixture(autouse=True)
def testdata_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Create a temporary test directory structure with empty files.

    Structure:
        tmp_path/
        ├── index.html
        ├── styles.css
        ├── theme.pcss
        ├── utilities.postcss
        ├── app.less
        ├── templates/
        │   └── page.html
        ├── styles/
        │   └── components/
        │       ├── button.scss
        │       └── card.sass
        ├── nested/
        └── empty/
    """
    # Create root-level files
    (tmp_path / "index.html").touch()
    (tmp_path / "styles.css").touch()
    (tmp_path / "theme.pcss").touch()
    (tmp_path / "utilities.postcss").touch()
    (tmp_path / "app.less").touch()

    # Create subdirectory structure with files
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "page.html").touch()

    styles_components_dir = tmp_path / "styles" / "components"
    styles_components_dir.mkdir(parents=True)
    (styles_components_dir / "button.scss").touch()
    (styles_components_dir / "card.sass").touch()

    # Create empty directories for edge case testing
    (tmp_path / "nested").mkdir()
    (tmp_path / "empty").mkdir()

    # Change to the temporary directory for all tests
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_find_files_current_directory() -> None:
    """Test finding files with '.' as input path."""
    results = sorted(find_files(paths=[Path()]))

    # Should find HTML and CSS files in current directory and subdirectories
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "page.html" for f in results)


def test_find_files_relative_directory() -> None:
    """Test finding files with relative_dir/ as input path."""
    results = sorted(find_files(paths=[Path("templates/")]))

    # Should find HTML files in templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all("templates" in str(f) for f in results)


def test_find_files_absolute_directory(testdata_dir: Path) -> None:
    """Test finding files with /absolute_dir/relative_dir/ as input path."""
    absolute_path = testdata_dir / "templates"
    results = sorted(find_files(paths=[absolute_path]))

    # Should find HTML files in the absolute templates directory
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)


def test_find_files_specific_html_file() -> None:
    """Test finding files with path/to/file.html as input path."""
    results = list(find_files(paths=[Path("index.html")]))

    # Should find the specific file
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_specific_css_file() -> None:
    """Test finding files with path/to/css.html as input path."""
    results = list(find_files(paths=[Path("styles.css")]))

    # Should find the specific CSS file
    assert len(results) == 1
    assert results[0].name == "styles.css"


def test_find_files_specific_custom_extension() -> None:
    """Test finding files with path/to/customglob.glob as input path."""
    results = list(find_files(paths=[Path("theme.pcss")]))

    # Should find the specific file with custom extension
    assert len(results) == 1
    assert results[0].name == "theme.pcss"


def test_find_files_simple_glob() -> None:
    """Test finding files with path/*.html glob pattern."""
    results = list(find_files(paths=[Path("templates/*.html")]))

    # Should find HTML files matching the glob pattern
    assert len(results) > 0
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_recursive_glob() -> None:
    """Test finding files with path/**/*.html glob pattern."""
    results = sorted(find_files(paths=[Path("**/*.html")]))

    # Should find all HTML files recursively
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert all(f.suffix == ".html" for f in results)


def test_find_files_complex_glob() -> None:
    """Test finding files with more complex glob patterns."""
    results = sorted(
        find_files(paths=[Path("*.css"), Path("*.pcss"), Path("*.postcss")])
    )

    # Should find all CSS-related files
    assert len(results) > 0
    assert any(f.name == "styles.css" for f in results)
    assert any(f.name == "theme.pcss" for f in results)
    assert any(f.name == "utilities.postcss" for f in results)


def test_find_files_deduplication() -> None:
    """Test that duplicate files are deduplicated."""
    results = list(
        find_files(paths=[Path("index.html"), Path("./index.html"), Path("index.html")])
    )

    # Should only return one instance
    assert len(results) == 1
    assert results[0].name == "index.html"


def test_find_files_multiple_paths() -> None:
    """Test finding files from multiple input paths."""
    results = sorted(
        find_files(paths=[Path("index.html"), Path("templates/"), Path("*.css")])
    )

    # Should find files from all specified paths
    assert len(results) > 0
    assert any(f.name == "index.html" for f in results)
    assert any(f.name == "page.html" for f in results)
    assert any(f.name == "styles.css" for f in results)


def test_find_files_nonexistent_path() -> None:
    """Test finding files with nonexistent path (treated as glob)."""
    results = list(find_files(paths=[Path("nonexistent/*.html")]))

    # Should return empty list for nonexistent paths
    assert len(results) == 0


def test_find_files_nested_directory() -> None:
    """Test finding files in nested directory structures."""
    results = sorted(find_files(paths=[Path("styles/")]))

    # Should search nested directories based on config.globs
    assert isinstance(results, list)


def test_find_nested_but_not_direct_child() -> None:
    """
    Select child directory which is not an immediate child.

    Select a directory which is not an immediate child, does not fail.
    This is a regression test for a glob pattern bug.
    """
    # Components exists in './styles/component'. In an earlier version it was
    # discovered, but paths were unable to be resolved.
    results = sorted(find_files(paths=[Path("components")]))

    # Should not error out but also not find any files
    assert isinstance(results, list)
    assert len(results) == 0


def test_find_files_empty_directory() -> None:
    """Test scanning an empty directory returns no files without errors."""
    results = list(find_files(paths=[Path("empty/")]))

    # Should complete successfully but return no files
    assert isinstance(results, list)
    assert len(results) == 0

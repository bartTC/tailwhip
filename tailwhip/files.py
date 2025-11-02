"""File-related utilities."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import TYPE_CHECKING

from rich.padding import Padding
from rich.syntax import Syntax

from tailwhip.constants import GLOBS, VERBOSITY_ALL, VERBOSITY_LOUD, VERBOSITY_NONE
from tailwhip.process import process_text

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from tailwhip.datatypes import Config


def find_files(*, config: Config) -> Generator[Path]:  # noqa: C901
    """Find all HTML/CSS files from a list of paths.

    Processes multiple path inputs (files, directories, or glob patterns), expands each
    one, and returns a deduplicated generator of all matching HTML/CSS files. If no paths
    are provided, defaults to scanning the current directory.

    Args:
        config: Argument configuration object

    Yields:
        Path objects for all HTML/CSS files found (deduplicated and sorted)

    Examples:
        >>> config.paths = [Path('templates/'), Path('styles/')]
        >>> list(find_files(config))
        [PosixPath('templates/index.html'), PosixPath('styles/main.css')]

        >>> config.paths = [Path('src/**/*.html'), Path('components/**/*.html')]
        >>> list(find_files(config))
        [PosixPath('src/pages/home.html'), PosixPath('components/nav.html')]

        >>> config.paths = []
        >>> list(find_files(config))  # Defaults to current directory
        [PosixPath('./index.html'), PosixPath('./styles.css')]

        >>> config.paths = [Path('index.html'), Path('about.html'), Path('index.html')]
        >>> list(find_files(config))
        [PosixPath('index.html'), PosixPath('about.html')]  # Deduplication

        >>> config.paths = [Path('*.html'), Path('static/*.css')]
        >>> list(find_files(config))
        [PosixPath('home.html'), PosixPath('static/app.css')]

    """
    seen = set()

    for entry in config.paths:
        p = Path(entry)

        # Case 1: Existing directory - search within it using configured glob patterns
        # Example: entry="src/" with config.globs=["**/*.html"]
        # → yields: src/index.html, src/pages/about.html
        if p.is_dir():
            for pattern in GLOBS:
                for match in p.glob(pattern):
                    resolved = match.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved

        # Case 2: Existing file - yield it directly without pattern matching
        # Example: entry="index.html" (file exists)
        # → yields: /absolute/path/to/index.html
        elif p.is_file():
            resolved = p.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved

        # Case 3: Non-existent path - interpret as recursive glob pattern from cwd
        # Example: entry="**/*.css" or entry="templates/*.html" (path doesn't exist as literal)
        # → yields: styles/main.css, components/button.css (all matching files from cwd)
        else:
            for match in Path().rglob(str(entry)):
                if match.is_file():
                    resolved = match.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved


def get_diff(path: Path, old_text: str, new_text: str) -> Syntax:
    """Show a nice diff using Rich."""
    # Create a text diff between old and new text
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile=str(path),
        tofile=str(path),
        n=1,
    )

    # Remove blank lines
    code = "\n".join([line.strip() for line in diff])
    return Syntax(code, "diff", theme="ansi_dark", background_color="default")


def apply_changes(*, targets: Iterable[Path], config: Config) -> tuple[bool, int, int]:
    """Process target files and apply Tailwind class sorting changes.

    Reads each file, processes it to sort Tailwind classes (skipping any with
    template syntax), and either writes the changes back or reports what would be
    changed. Provides detailed diff output at higher verbosity levels.

    Args:
        targets: List of Path objects for files to process
        config: Argument configuration object

    Returns:
        A tuple of (skipped_count, changed_count) where:
        - skipped_count: Number of files with no changes needed
        - changed_count: Number of files that were modified or would be modified

    Examples:
        >>> apply_changes(targets=[Path('index.html')], config=config)
        (0, 1)  # 0 skipped, 1 changed

        >>> apply_changes(targets=[Path('a.html'), Path('b.html')], config=config)
        (1, 1)  # 1 skipped (no changes), 1 changed

    """
    skipped = 0
    changed = 0
    found_any = False

    for f in targets:
        found_any = True
        old_text = f.read_text(encoding="utf-8")
        new_text = process_text(old_text, config)

        # Skip files that don't need changes
        if old_text == new_text:
            if config.verbosity >= VERBOSITY_LOUD:
                config.console.print(
                    f"[grey30]Already sorted {f}[/grey30]", highlight=False
                )
            skipped += 1
            continue

        changed += 1

        # Write changes if in write mode, otherwise just report
        if config.write:
            f.write_text(new_text, encoding="utf-8")

        # No report if verbosity is low
        if config.verbosity == VERBOSITY_NONE:
            continue

        if config.write:
            config.console.print(f"[dim]Updated[/dim] [filename]{f}[/filename]")
        else:
            config.console.print(f"[dim]Would update[/dim] [filename]{f}[/filename]")

        if config.verbosity >= VERBOSITY_ALL:
            diff = get_diff(f, old_text, new_text)
            config.console.print(Padding(diff, (1, 0, 1, 4)))

    return found_any, skipped, changed

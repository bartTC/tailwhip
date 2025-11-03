"""File-related utilities."""

from __future__ import annotations

import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.padding import Padding
from rich.syntax import Syntax
from wcmatch import glob

from tailwhip.constants import GLOBS, VERBOSITY_ALL, VERBOSITY_LOUD, VERBOSITY_NONE
from tailwhip.context import get_config
from tailwhip.process import process_text

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


@dataclass(slots=True)
class FileResult:
    """Result of processing a single file."""

    path: Path
    skipped: bool
    changed: bool
    old_text: str | None
    new_text: str | None


def find_files() -> Generator[Path]:  # noqa: C901
    """Find all HTML/CSS files from a list of paths.

    Processes multiple path inputs (files, directories, or glob patterns), expands each
    one, and returns a deduplicated generator of all matching HTML/CSS files. If no paths
    are provided, defaults to scanning the current directory.

    Yields:
        Path objects for all HTML/CSS files found (deduplicated and sorted)

    Examples:
        >>> list(find_files())
        [PosixPath('templates/index.html'), PosixPath('styles/main.css')]

        >>> list(find_files())
        [PosixPath('src/pages/home.html'), PosixPath('components/nav.html')]

        >>> list(find_files())  # Defaults to current directory
        [PosixPath('./index.html'), PosixPath('./styles.css')]

        >>> list(find_files())
        [PosixPath('index.html'), PosixPath('about.html')]  # Deduplication

        >>> list(find_files())
        [PosixPath('home.html'), PosixPath('static/app.css')]

    """
    config = get_config()
    seen = set()
    flags = glob.GLOBSTAR | glob.BRACE | glob.EXTGLOB | glob.DOTGLOB

    for entry in config.paths:
        p = Path(entry)

        # If it's a directory, expand it with default GLOBS patterns
        # Example: entry="src/" → patterns=["src/**/*.html", "src/**/*.css"]
        if p.is_dir():
            patterns = [str(p / pattern) for pattern in GLOBS]
        else:
            # Otherwise treat as literal file path or glob pattern
            patterns = [str(entry)]

        # Use wcmatch to handle all patterns uniformly (files, globs, braces, etc.)
        for pattern in patterns:
            for match_str in glob.glob(pattern, flags=flags):

                match = Path(match_str)
                if not match.is_file():
                    continue

                resolved = match.resolve()
                if resolved in seen:
                    continue

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


def _process_file(f: Path) -> FileResult:
    """Process a single file for Tailwind class sorting.

    Args:
        f: Path to the file to process

    Returns:
        FileResult with processing status and file content
    """
    try:
        old_text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return FileResult(path=f, skipped=True, changed=False, old_text=None, new_text=None)

    new_text = process_text(old_text)

    # Skip files that don't need changes
    if old_text == new_text:
        return FileResult(path=f, skipped=True, changed=False, old_text=old_text, new_text=None)

    return FileResult(path=f, skipped=False, changed=True, old_text=old_text, new_text=new_text)


def apply_changes(*, targets: Iterable[Path]) -> tuple[bool, int, int]:
    """Process target files and apply Tailwind class sorting changes.

    Reads each file, processes it to sort Tailwind classes (skipping any with
    template syntax), and either writes the changes back or reports what would be
    changed. Provides detailed diff output at higher verbosity levels.

    Args:
        targets: List of Path objects for files to process

    Returns:
        A tuple of (skipped_count, changed_count) where:
        - skipped_count: Number of files with no changes needed
        - changed_count: Number of files that were modified or would be modified

    Examples:
        >>> apply_changes(targets=[Path('index.html')])
        (0, 1)  # 0 skipped, 1 changed

        >>> apply_changes(targets=[Path('a.html'), Path('b.html')])
        (1, 1)  # 1 skipped (no changes), 1 changed

    """
    config = get_config()
    skipped = 0
    changed = 0
    found_any = False
    targets_list = list(targets)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_process_file, f): f for f in targets_list}

        for future in as_completed(futures):
            found_any = True
            result = future.result()

            if result.old_text is None:
                # UnicodeDecodeError occurred
                config.console.print(
                    f"[red]Unable to read[/red] [filename]{result.path}[/filename]",
                    highlight=False,
                )
                skipped += 1
                continue

            if result.skipped:
                if config.verbosity >= VERBOSITY_LOUD:
                    config.console.print(
                        f"[grey30]Already sorted {result.path}[/grey30]",
                        highlight=False,
                    )
                skipped += 1
                continue

            changed += 1

            # Write changes if in write mode, otherwise just report
            if config.write:
                result.path.write_text(result.new_text, encoding="utf-8")

            # No report if verbosity is low
            if config.verbosity == VERBOSITY_NONE:
                continue

            if config.write:
                config.console.print(
                    f"[dim]Updated[/dim] [filename]{result.path}[/filename]"
                )
            else:
                config.console.print(
                    f"[dim]Would update[/dim] [filename]{result.path}[/filename]"
                )

            if config.verbosity >= VERBOSITY_ALL:
                diff = get_diff(result.path, result.old_text, result.new_text)
                config.console.print(Padding(diff, (1, 0, 1, 4)))

    return found_any, skipped, changed

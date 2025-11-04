"""CLI entrypoint."""

from __future__ import annotations

import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from tailwhip import configuration
from tailwhip.configuration import CONSOLE_THEME, GLOBS, VERBOSITY_LOUD
from tailwhip.context import set_config
from tailwhip.datatypes import Config
from tailwhip.files import apply_changes, find_files


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        version = metadata.version("tailwhip")
        typer.echo(f"tailwhip {version}")
        raise typer.Exit


app = typer.Typer(
    help="Sort Tailwind CSS classes in HTML and CSS files.",
    add_completion=False,
    rich_markup_mode="rich",
)


def main() -> None:
    """Entrypoint for the CLI."""
    app()


@app.command(context_settings={"help_option_names": ["-h", "--help"]})
def run(  # noqa: PLR0913
    paths: Annotated[
        list[Path],
        typer.Argument(
            help=(
                f"Files or directories to process. "
                f"Directories use default patterns ({', '.join(GLOBS)}), "
                f"glob patterns (e.g., 'src/**/*.jsx') match as specified."
            ),
            metavar="PATH",
        ),
    ],
    version: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
    write_mode: Annotated[
        bool,
        typer.Option(
            "--write",
            "-w",
            help="Write changes to files (default: dry-run mode).",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress output except errors and warnings.",
        ),
    ] = False,
    verbosity: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase output verbosity (-v: changes, -vv: diff, -vvv: debug).",
        ),
    ] = 0,
    configuration_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Load custom configuration file (overrides pyproject.toml settings).",
            metavar="FILE",
        ),
    ] = None,
) -> None:
    """Sort Tailwind CSS classes in HTML and CSS files.

    Automatically discovers and sorts Tailwind classes according to a consistent
    ordering. Supports HTML, CSS, and template files with Tailwind @apply directives.
    """
    # Load configuration (dynaconf handles file validation and discovery)
    search_path = paths[0] if paths else Path.cwd()

    try:
        configuration.reload_config(configuration_file, search_path)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    console = Console(quiet=quiet, theme=CONSOLE_THEME)

    config = Config(
        console=console,
        paths=paths,
        write=write_mode,
        verbosity=verbosity + 1,
    )
    set_config(config)

    console.print("")

    start_time = time.time()
    found_any, skipped, changed = apply_changes(targets=find_files())
    duration = time.time() - start_time

    if not found_any:
        config.console.print("[red]Error: No files found[/red]")
        sys.exit(1)

    if config.verbosity < VERBOSITY_LOUD:
        console.print(
            "\nUse [important] -v [/important] (show unchanged files) or [important] -vv [/important] (show diff preview) for more detail."
        )

    if not config.write:
        console.print(
            "\n:warning: Dry Run. No files were actually written. "
            "Use [important] --write [/important] to write changes."
        )

    console.print(
        f"⏱ Completed in [bold]{duration:.3f}s[/bold] for {changed} files. [dim]({skipped} skipped)[/dim]",
        highlight=False,
    )

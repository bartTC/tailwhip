"""CLI entrypoint."""

from __future__ import annotations

import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from tailwhip.configuration import (
    CONSOLE_THEME,
    VerbosityLevel,
    config,
    get_pyproject_toml_data,
    update_configuration,
)
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
            help="Files or directories to process.",
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
    custom_configuration_file: Annotated[
        Path | None,
        typer.Option(
            "--configuration",
            "-c",
            help="Load custom configuration file (overrides pyproject.toml settings).",
            metavar="FILE",
        ),
    ] = None,
) -> None:
    """
    Sort Tailwind CSS classes in HTML and CSS files.

    Automatically discovers and sorts Tailwind classes according to a consistent
    ordering. Supports HTML, CSS, and template files with Tailwind @apply directives.
    """
    # Check if the given configuration file exists
    if custom_configuration_file and not custom_configuration_file.exists():
        typer.echo(
            f"Custom configuration file {custom_configuration_file} not found.",
            err=True,
        )
        raise typer.Exit(1)

    # Setup configuration values -------------------------------------------------------

    # 1. Overwrite config defaults with pyproject.toml settings if they exist
    if pyproject_data := get_pyproject_toml_data(Path.cwd()):
        update_configuration(pyproject_data)

    # 2. Overwrite config defaults with custom settings if they exist
    if custom_configuration_file:
        update_configuration(custom_configuration_file)

    # 3. Overwrite config defaults with CLI options
    update_configuration(
        {
            "write_mode": write_mode,
            "verbosity": 0 if quiet else verbosity + 1,
        }
    )

    # Setup helper tools ---------------------------------------------------------------

    config.console = Console(quiet=quiet, theme=CONSOLE_THEME)

    # Start Tailwhipping ---------------------------------------------------------------

    start_time = time.time()
    found_any, skipped, changed = apply_changes(targets=find_files(paths=paths))
    duration = time.time() - start_time

    if not found_any:
        config.console.print("[red]Error: No files found[/red]")
        sys.exit(1)

    if config.verbosity == VerbosityLevel.NORMAL:
        config.console.print(
            "\nUse [important] -v [/important] (show unchanged files) or [important] -vv [/important] (show diff preview) for more detail."
        )

    if not config.write_mode:
        config.console.print(
            "\n:warning: Dry Run. No files were actually written. "
            "Use [important] --write [/important] to write changes."
        )

    config.console.print(
        f"⏱ Completed in [bold]{duration:.3f}s[/bold] for {changed} files. [dim]({skipped} skipped)[/dim]",
        highlight=False,
    )

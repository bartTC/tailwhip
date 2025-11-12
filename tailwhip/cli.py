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
from tailwhip.process import process_text


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
        list[Path] | None,
        typer.Argument(
            help="Files or directories to process. Omit to read from stdin.",
            metavar="PATH",
        ),
    ] = None,
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

    [bold]Examples:[/bold]

      # Check a single file (dry-run by default)
      tailwhip index.html

      # Sort classes in multiple files
      tailwhip file1.html file2.html styles.css

      # Process all HTML and CSS files in a directory
      tailwhip src/templates/

      # Actually write changes to files
      tailwhip src/ --write

      # Preview detailed diff before writing
      tailwhip index.html -vv

      # Read from stdin and output to stdout
      echo '<div class="mt-4 p-2 bg-blue-500"></div>' | tailwhip

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

    # Handle stdin mode ----------------------------------------------------------------

    if not paths:
        # Check if stdin is being piped (not a TTY)
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
            output_text = process_text(input_text)
            sys.stdout.write(output_text)
            return

        # No paths and no piped input
        config.console.print(
            "[red]Error: No paths provided. Provide file paths or pipe content to stdin.[/red]"
        )
        sys.exit(1)

    # Handle File Mode -----------------------------------------------------------------

    start_time = time.time()
    found_any, skipped, changed = apply_changes(targets=find_files(paths=paths))
    duration = time.time() - start_time

    if not found_any:
        config.console.print("[red]Error: No files found[/red]")
        sys.exit(1)

    if config.verbosity >= VerbosityLevel.VERBOSE:
        if not config.write_mode:
            config.console.print(
                "\n:warning: Dry Run. No files were actually written. "
                "Use [important] --write [/important] to write changes."
            )

        config.console.print(
            f"⏱ Completed in [bold]{duration:.3f}s[/bold] for {changed} files. [dim]({skipped} skipped)[/dim]",
            highlight=False,
        )

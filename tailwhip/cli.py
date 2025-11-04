"""CLI entrypoint."""

from __future__ import annotations

import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from tailwhip import constants
from tailwhip.constants import CONSOLE_THEME, GLOBS, VERBOSITY_LOUD
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
    help="Sort Tailwind CSS classes in HTML and CSS files",
    add_completion=False,
)


def main() -> None:
    """Entrypoint for the CLI."""
    app()


@app.command()
def run(  # noqa: PLR0913
    paths: Annotated[
        list[Path],
        typer.Argument(
            help=(
                f"File or directory paths to process. Plain directories "
                f"(e.g., 'templates/') use default patterns ({', '.join(GLOBS)}). "
                f"Glob patterns (e.g., 'templates/**/*.postcss') are matched as-is."
            )
        ),
    ],
    version: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
    write_mode: Annotated[
        bool,
        typer.Option(
            "--write",
            help="Apply sorting changes to files. Without this flag, runs in check-only mode to preview changes.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Minimal output mode. Only displays errors and warnings.",
        ),
    ] = False,
    verbosity: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase output detail level. Use -v for changes, -vv for file processing, -vvv for debug info.",
        ),
    ] = 0,
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help=(
                "Path to a custom TOML config file. This file will be merged with the default "
                "constants.toml. You only need to specify the values you want to override. "
                "Useful for customizing globs, group_order, variant_prefix_order, etc."
            ),
        ),
    ] = None,
) -> None:
    """Sort Tailwind CSS classes in HTML and CSS files."""
    # Load configuration (dynaconf handles file validation and discovery)
    search_path = paths[0] if paths else Path.cwd()

    try:
        constants.reload_config(config_file, search_path)
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

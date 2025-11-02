"""CLI entrypoint."""

from __future__ import annotations

import time
from importlib import metadata
from pathlib import Path  # noqa: TC003
from typing import Annotated

import typer
from rich.console import Console

from tailwhip.constants import CONSOLE_THEME, GLOBS, SKIP_EXPRESSIONS, VERBOSITY_LOUD
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
    skip_expressions: Annotated[
        str,
        typer.Option(
            "--skip-expressions",
            help="Template syntax markers that indicate code blocks to skip sorting. Comma-separated list (e.g., '{{,{%,<%'). Prevents sorting dynamic template expressions.",
        ),
    ] = ",".join(SKIP_EXPRESSIONS),
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
    custom_colors: Annotated[
        str,
        typer.Option(
            "--custom-colors",
            help=(
                "Comma-separated list of custom color names from your Tailwind config "
                "(e.g., 'brand,company,accent'). These colors will be recognized and sorted "
                "alongside standard Tailwind colors. WARNING: Classes using these custom colors "
                "will sort differently if you run tailwhip again without providing the same "
                "--custom-colors values. Omitting previously-used custom colors will cause those "
                "utilities to be treated as non-color classes and sorted into different positions."
            ),
        ),
    ] = "",
) -> None:
    """Sort Tailwind CSS classes in HTML and CSS files."""
    console = Console(quiet=quiet, theme=CONSOLE_THEME)
    skip_expressions = [
        expr.strip() for expr in skip_expressions.split(",") if expr.strip()
    ]
    custom_colors_list = {
        color.strip() for color in custom_colors.split(",") if color.strip()
    }

    config = Config(
        console=console,
        paths=paths,
        write=write_mode,
        skip_expressions=skip_expressions,
        verbosity=verbosity + 1,
        custom_colors=custom_colors_list,
    )

    console.print("")

    start_time = time.time()
    targets = find_files(config=config)
    skipped, changed = apply_changes(targets=targets, config=config)
    duration = time.time() - start_time

    if config.verbosity < VERBOSITY_LOUD:
        console.print("\nUse [important] -v [/important] (show unchanged files) or [important] -vv [/important] (show diff preview) for more detail.")

    if not config.write:
        console.print(
            "\n:warning: Dry Run. No files were actually written. "
            "Use [important] --write [/important] to write changes."
        )

    console.print(
        f"⏱ Completed in [bold]{duration:.3f}s[/bold] for {changed} files. [dim]({skipped} skipped)[/dim]",
        highlight=False,
    )

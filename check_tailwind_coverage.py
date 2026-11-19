"""
Check the default configuration against the utilities and variants of Tailwind CSS.

Installs the `tailwindcss` npm package into a temporary directory, asks its
design system for every utility class and variant it knows, and runs each class
through tailwhip's parser. Reports classes whose prefix is not in the
`prefixes` list (they would sort as non-Tailwind classes, before everything
else) and variants that are not in the `variants` list (they would sort last).

Requires Node.js and npm. Exits with status 1 when anything is missing, so it can
run in CI; with --markdown it also writes a report for a GitHub issue, which the
weekly Tailwind coverage workflow uses.

    python check_tailwind_coverage.py
    python check_tailwind_coverage.py --version 4.3.5 --verbose
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from tailwhip.configuration import lookups
from tailwhip.sorting import _MAX_RANK, _get_variant_rank, parse_class

# Loads Tailwind's design system from the package installed in the directory
# given as the first argument and prints its classes and variants as JSON.
DUMP_SCRIPT = """
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const base = process.argv[1];
const pkg = path.join(base, 'node_modules', 'tailwindcss');
const tw = await import(pathToFileURL(path.join(pkg, 'dist', 'lib.mjs')).href);
const css = fs.readFileSync(path.join(pkg, 'index.css'), 'utf8');
const ds = await tw.__unstable__loadDesignSystem(css, { base });

process.stdout.write(JSON.stringify({
  version: JSON.parse(fs.readFileSync(path.join(pkg, 'package.json'), 'utf8')).version,
  classes: ds.getClassList().map(([name]) => name),
  variants: ds.getVariants().map((v) => ({ name: v.name, values: v.values ?? [] })),
}));
"""

EXAMPLE_COUNT = 6


def load_tailwind(version: str) -> dict:
    """Install the given tailwindcss version and return its classes and variants."""
    npm = shutil.which("npm")
    node = shutil.which("node")
    if not npm or not node:
        sys.exit("Node.js and npm are required to load Tailwind CSS.")

    with tempfile.TemporaryDirectory(prefix="tailwhip-check-") as base:
        subprocess.run(  # noqa: S603
            [
                npm,
                "install",
                "--prefix",
                base,
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
                "--silent",
                f"tailwindcss@{version}",
            ],
            check=True,
        )
        result = subprocess.run(  # noqa: S603
            [node, "--input-type=module", "-e", DUMP_SCRIPT, base],
            check=True,
            capture_output=True,
            text=True,
        )
    return json.loads(result.stdout)


def variant_known(name: str, values: list[str]) -> bool:
    """
    Check whether a variant sorts by a configured rank.

    Functional variants without a configured base name count as known when every
    value they take is configured, e.g. "@" with "@sm", "@md", ...
    """
    if _get_variant_rank(name) != _MAX_RANK:
        return True
    separator = "" if name.endswith("@") else "-"
    return bool(values) and all(
        _get_variant_rank(f"{name}{separator}{value}") != _MAX_RANK for value in values
    )


def find_unknown_prefixes(classes: list[str]) -> dict[str, list[str]]:
    """Group the classes whose parsed prefix is not configured by that prefix."""
    unknown: dict[str, list[str]] = defaultdict(list)
    for classname in classes:
        prefix = parse_class(classname).prefix
        if prefix not in lookups.prefix_index:
            unknown[prefix].append(classname)
    return dict(sorted(unknown.items()))


def find_unused_entries(tailwind: dict) -> tuple[list[str], list[str]]:
    """
    Return the configured prefixes and variants that Tailwind does not list.

    Not necessarily wrong: Tailwind 3 names, arbitrary-only utilities such as
    "font-features" and expanded variants such as "aria-checked" show up here.
    """
    class_prefixes = set()
    for classname in tailwind["classes"]:
        parts = classname.split("-")
        class_prefixes.update("-".join(parts[:i]) for i in range(1, len(parts) + 1))

    variant_names = set()
    for variant in tailwind["variants"]:
        name = variant["name"]
        separator = "" if name.endswith("@") else "-"
        variant_names.add(name)
        variant_names.update(f"{name}{separator}{v}" for v in variant["values"])

    prefixes = [p for p in lookups.prefix_index if p not in class_prefixes]
    variants = [v for v in lookups.variant_index if v not in variant_names]
    return prefixes, variants


def markdown_report(
    version: str,
    unknown_prefixes: dict[str, list[str]],
    unknown_variants: list[str],
) -> str:
    """Render the missing classes and variants as a GitHub issue body."""
    lines = [
        (
            f"Tailwind CSS {version} has utilities or variants that the default "
            "configuration in `tailwhip/configuration.toml` does not cover. Until "
            "they are added, classes with an unknown prefix sort before every "
            "Tailwind class and unknown variants sort last."
        ),
    ]
    if unknown_prefixes:
        lines += ["", "### Prefixes missing from `prefixes`", ""]
        lines += [
            f"- `{prefix}`: {', '.join(f'`{c}`' for c in classes)}"
            for prefix, classes in unknown_prefixes.items()
        ]
    if unknown_variants:
        lines += ["", "### Variants missing from `variants`", ""]
        lines += [f"- `{name}`" for name in unknown_variants]
    lines += [
        "",
        "Run `python check_tailwind_coverage.py` locally to reproduce.",
    ]
    return "\n".join(lines) + "\n"


def print_report(
    unknown_prefixes: dict[str, list[str]],
    unknown_variants: list[str],
) -> None:
    """Print the missing classes and variants to the terminal."""
    if unknown_prefixes:
        print("\nClasses with a prefix missing from `prefixes`:")
        for prefix, classes in unknown_prefixes.items():
            examples = ", ".join(classes[:EXAMPLE_COUNT])
            more = (
                f", ... ({len(classes)} total)" if len(classes) > EXAMPLE_COUNT else ""
            )
            print(f"  {prefix}: {examples}{more}")

    if unknown_variants:
        print("\nVariants missing from `variants`:")
        for name in unknown_variants:
            print(f"  {name}")


def main() -> int:
    """Run the check and print a report; return the exit status."""
    parser = argparse.ArgumentParser(
        description="Check the default configuration against Tailwind CSS."
    )
    parser.add_argument(
        "--version",
        default="latest",
        help="The tailwindcss npm version or dist-tag to check against.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Also list configured entries that Tailwind does not know.",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        metavar="PATH",
        help="Write a Markdown report (an issue body) to PATH when anything is missing.",
    )
    args = parser.parse_args()

    tailwind = load_tailwind(args.version)
    print(
        f"Tailwind CSS {tailwind['version']}: {len(tailwind['classes'])} classes, "
        f"{len(tailwind['variants'])} variants"
    )

    unknown_prefixes = find_unknown_prefixes(tailwind["classes"])
    unknown_variants = [
        v["name"]
        for v in tailwind["variants"]
        if not variant_known(v["name"], v["values"])
    ]
    print_report(unknown_prefixes, unknown_variants)

    if args.verbose:
        unused_prefixes, unused_variants = find_unused_entries(tailwind)
        print("\nConfigured prefixes Tailwind does not list (may be intentional):")
        print(f"  {', '.join(unused_prefixes) or '-'}")
        print("\nConfigured variants Tailwind does not list (may be intentional):")
        print(f"  {', '.join(unused_variants) or '-'}")

    if unknown_prefixes or unknown_variants:
        if args.markdown:
            args.markdown.write_text(
                markdown_report(tailwind["version"], unknown_prefixes, unknown_variants)
            )
        return 1

    print("\nEvery Tailwind class and variant is covered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

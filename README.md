# Tailwhip — Tailwind CSS class sorter

[![PyPI version](https://img.shields.io/pypi/v/tailwhip.svg)](https://pypi.org/project/tailwhip/)
[![Test](https://github.com/bartTC/tailwhip/actions/workflows/test.yml/badge.svg)](https://github.com/bartTC/tailwhip/actions/workflows/test.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Tailwhip is a pure Python Tailwind CSS class sorter that works with any HTML or CSS
file — including Django templates and other templating languages.

![Screenshot of Tailwhip](https://github.com/bartTC/tailwhip/blob/main/screenshot.png?raw=true)

## Why Tailwhip?

The [official Prettier plugin][1] for sorting Tailwind classes doesn’t play well
with many template languages, such as Django. While there are Prettier plugins that
add limited support for [Jinja templates][2], they often require configuration
workarounds or restrict what you can do with Prettier.

Tailwhip takes a more pragmatic approach. Instead of trying to parse and understand
every possible template syntax, it focuses on sorting Tailwind classes reliably, and
ignores class attributes that contain template syntax.

[1]: https://github.com/tailwindlabs/prettier-plugin-tailwindcss
[2]: https://github.com/davidodenwald/prettier-plugin-jinja-template

How it works:

1. It finds all `class=""` attributes and `@apply` directives in the given files.
2. It sorts the contained classes according to the official Tailwind CSS class order.
3. If a class attribute contains template syntax (e.g., `{{ ... }}` or `{% ... %}`),
   Tailwhip leaves it untouched.

This approach ensures Tailwhip works across diverse environments — Django, Flask,
Jinja2, or even custom templating engines — without breaking your templates or
requiring complicated setup.

## Usage

Tailwhip requires Python 3.11 or later.

```bash
$ uvx tailwhip [options] [filepath...]

# Find all .html and .css files in the templates directory
$ uvx tailwhip templates/

# Preview changes
$ uvx tailwhip templates/ -vv

# Actually apply changes
$ uvx tailwhip templates/ --write

# Sort classes in .scss files
$ uvx tailwhip "templates/**/*.scss"

# Standard glob patterns are supported
$ uvx tailwhip "static/**/*.{css,scss}" "templates/**/*.htm[l]"
```

You can also install it with pip and use it as a Python library:

```bash
$ pip install tailwhip

$ tailwhip templates/
$ python -m tailwhip templates/
```

See `--help` for all options and features.

## Configuration

Tailwhip works great out of the box with sensible defaults, but you can customize its behavior to match your project's needs. There are two ways to configure Tailwhip:

### Option 1: `pyproject.toml`

Add a `[tool.tailwhip]` section to your project's `pyproject.toml`:

```toml
[tool.tailwhip]
# Increase verbosity to see detailed changes
verbosity = 2

# Customize file patterns to include JSX/TSX files
default_globs = [
    "**/*.html",
    "**/*.css",
    "**/*.jsx",
    "**/*.tsx",
]

# Add your custom Tailwind colors
custom_colors = ["brand", "accent", "company"]

# Add template syntax for your templating engine
skip_expressions = ["{{", "{%", "<%", "[[", "]]"]
```

### Option 2: Custom Configuration File

Create a `tailwhip.toml` file anywhere in your project and pass it via the `--configuration` flag:

```toml
# tailwhip.toml
verbosity = 3

default_globs = [
    "**/*.html",
    "**/*.css",
    "**/*.liquid",  # Shopify Liquid templates
]

custom_colors = ["primary", "secondary", "accent"]

skip_expressions = ["{{", "{%", "<%", "{-"]  # Add Nunjucks syntax
```

Then use it with:

```bash
$ tailwhip templates/ --configuration=tailwhip.toml
```

### Configuration Precedence

Settings are loaded in this order (later sources override earlier ones):

1. **Default values** (built into Tailwhip)
2. **`pyproject.toml`** (`[tool.tailwhip]` section)
3. **Custom config file** (via `--configuration` flag)
4. **CLI arguments** (e.g., `--write`, `-v`, `--quiet`)

CLI arguments always take precedence, so you can override any config value on the command line.

### Available Configuration Options

For a complete list of all configuration options with detailed explanations, see the [default configuration file](https://github.com/bartTC/tailwhip/blob/main/tailwhip/configuration.toml). It includes:

- **Output settings**: `verbosity`, `write_mode`
- **File discovery**: `default_globs`
- **Template handling**: `skip_expressions`
- **Sorting behavior**: `utility_groups`, `variant_groups`
- **Color recognition**: `tailwind_colors`, `custom_colors`
- **Pattern matching**: `class_patterns` (advanced)

Most users only need to customize `custom_colors` and occasionally `default_globs` or `skip_expressions`. The sorting algorithm is based on Tailwind best practices and rarely needs modification.

### Advanced: Custom Pattern Matching

Tailwhip uses configurable patterns to find and sort class attributes across different syntaxes. By default, it supports:

- HTML `class="..."` attributes
- CSS `@apply ...;` directives

You can add custom patterns for other frameworks (JSX, Vue, Svelte, etc.) by configuring `class_patterns` in your `pyproject.toml` or custom config file.

**Important:** Custom `class_patterns` **replace** (not extend) the defaults, just like any other configuration setting. You must include the default HTML and CSS patterns if you want to keep them:

```toml
# Example: Add JSX className support while keeping HTML class and CSS @apply
# In pyproject.toml, use [[tool.tailwhip.class_patterns]]
# In custom config file, use [[class_patterns]]

# Keep default: HTML class attribute
[[tool.tailwhip.class_patterns]]
name = "html_class"
regex = '''\bclass\s*=\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'class={quote}{classes}{quote}'

# Keep default: CSS @apply directive
[[tool.tailwhip.class_patterns]]
name = "css_apply"
regex = '''@apply\s+(?P<classes>[^;]+);'''
template = '@apply {classes};'

# Add custom: JSX className
[[tool.tailwhip.class_patterns]]
name = "jsx_classname"
regex = '''\bclassName\s*=\s*(?P<quote>["'])(?P<classes>.*?)(?P=quote)'''
template = 'className={quote}{classes}{quote}'
```

**Requirements:**
- Each pattern must have a `(?P<classes>...)` named group to capture the classes
- The `template` field uses `{classes}` and any other named groups from the regex
- Additional named groups are optional but must match between regex and template

See the [configuration file](https://github.com/bartTC/tailwhip/blob/main/tailwhip/configuration.toml) for more examples and detailed documentation.

## Changelog

See [CHANGELOG.md](https://github.com/bartTC/tailwhip/blob/main/CHANGELOG.md) for a complete list of changes and version history.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.1] - 2025-01-04

### Added

- **CI/CD**: GitHub Actions workflow for linting
  - Runs ruff check to verify code quality
  - Runs ruff format check to ensure consistent code formatting
  - Added ruff to dev dependencies

- **Documentation**: PyPI version badge in README

- **Pattern System**: Extensible pattern matching for multiple syntaxes
  - New `class_patterns` configuration with regex and template support
  - Built-in support for HTML `class` and CSS `@apply`
  - Users can add custom patterns for JSX, Vue, Svelte, and other frameworks
  - All patterns use consistent `(?P<classes>...)` named group requirement
  - Template-based reconstruction using named groups from regex matches

### Changed

- **Configuration**: Updated `example.tailwhip.toml` with comprehensive documentation
  - Aligned structure and descriptions with main `configuration.toml`
  - Added clearer usage examples for common customization scenarios
  - Improved comments and organization for better user guidance

- **Architecture**: Unified pattern processing system
  - Replaced separate `class_regex` and `apply_regex` with `class_patterns` list
  - Single `process_pattern()` function handles all syntax types
  - New `Pattern` dataclass for compiled regex patterns
  - Compiled patterns stored in `config.APPLY_PATTERNS`

### Removed

- **Deprecated Functions**: Removed `process_html()` and `process_css()`
  - All functionality now available through `process_text()`
  - Tests updated to use unified `process_text()` function

## [0.9] - 2025-11-04

### Added

- **CI/CD**: GitHub Actions workflow for automated testing
  - Python matrix testing across versions 3.11, 3.12, 3.13, and 3.14
  - Runs on push and pull requests to main branch
  - Uses uv for fast dependency management

- **Documentation Enhancements**
  - CI/CD status badge in README
  - Python version support badge
  - MIT license badge
  - Direct link to CHANGELOG.md from README

- **Testing Infrastructure**
  - Comprehensive tests for file writing functionality
  - Edge case coverage for file operations
  - Coverage configuration with proper exclusions

- **Verbosity Levels**: New DIFF mode for showing changes
  - Enhanced output options for reviewing modifications
  - Better visibility into what will be changed

### Changed

- **Configuration Access**: Refactored to use direct attribute access instead of dictionary keys
  - Cleaner, more Pythonic API
  - Better IDE autocomplete support

### Fixed

- **Documentation**: Corrected README usage example for `--configuration` flag syntax

### Removed

- **Code Cleanup**: Removed unused `datatypes.py` module

## [0.9b0] - 2025-01-04

### Added

- **Configuration System**: Complete configuration management with Dynaconf
  - Support for `pyproject.toml` via `[tool.tailwhip]` section
  - Support for custom configuration files via `--configuration` flag
  - Clear configuration precedence: defaults < pyproject.toml < custom config < CLI arguments
  - Comprehensive configuration documentation in `configuration.toml` with examples and recommendations

- **Configuration Options**: New customizable settings
  - `verbosity`: Control output detail level (0-3)
  - `write_mode`: Safe dry-run mode by default
  - `default_globs`: Customize file patterns to process
  - `skip_expressions`: Add template engine syntax to skip
  - `custom_colors`: Define custom Tailwind colors from your config
  - `utility_groups` and `variant_groups`: Fine-tune sorting behavior (advanced)

- **CLI Enhancements**
  - `--configuration` / `-c` flag to specify custom config file
  - Improved help text and error messages
  - Configuration validation and error handling

- **Testing Infrastructure**
  - Comprehensive CLI and configuration precedence tests
  - Dynamic test fixtures using temporary directories (no stub files in repo)
  - Module docstrings for all test files
  - Configuration reset fixture to prevent test pollution

- **Documentation**
  - Complete configuration guide in README.md
  - Examples for `pyproject.toml` and custom config files
  - Configuration precedence documentation
  - Detailed comments in `configuration.toml`

### Changed

- **Configuration Architecture**: Migrated from simple constants to Dynaconf-based system
  - Centralized configuration in `configuration.py`
  - Dynamic recompilation of regex patterns on config updates
  - Type-safe configuration with `TailwhipConfig` class

- **Unknown Class Sorting**: Unknown classes now sort at the front (before matched patterns)

- **Test Files**: Tests now use temporary directories instead of static testdata files
  - Cleaner repository (no stub files)
  - Better test isolation
  - Faster test setup

### Fixed

- Handle `UnicodeDecodeError` when reading files - now skips unreadable files gracefully
- Configuration value types properly validated and converted
- Test pollution between test runs via autouse reset fixture

### Internal

- Simplified pyproject.toml retrieval logic
- Refactored constants handling with centralized pattern compilation
- Improved file discovery with generic glob setup
- Better thread context management for parallel processing
- Code organization and type improvements

## Alpha Status (0.9a1 - 0.9a3)

The initial alpha releases established the core functionality of Tailwhip.

### Features

- **Tailwind Class Sorting**: Core sorting algorithm based on official Tailwind CSS class ordering
  - Utility class grouping (layout, spacing, typography, visual effects, etc.)
  - Variant sorting (responsive breakpoints, pseudo-classes, state modifiers)
  - Alphabetical sorting within groups

- **Template Engine Support**: Automatic detection and skipping of template syntax
  - Support for Django, Jinja2, Liquid, ERB, and other templating languages
  - Classes with template expressions (`{{ }}`, `{% %}`, `<% %>`) are left unchanged

- **File Processing**: Batch processing with multiple file types
  - HTML and CSS file support
  - `@apply` directive sorting in CSS
  - Glob pattern support for file discovery

- **CLI Interface**: Command-line tool with essential options
  - Dry-run mode by default (safe preview of changes)
  - `--write` flag to apply changes
  - Verbosity controls (`-v`, `-vv`, `-vvv`)
  - `--quiet` mode for minimal output

- **Error Handling**: Robust file processing
  - Skip unreadable files (Unicode errors)
  - Skip nonexistent paths gracefully
  - Continue processing on individual file errors

### Development Milestones

- **0.9a1** - Initial release with core sorting functionality
- **0.9a2** - Bug fixes, improved error handling, and type hint improvements
- **0.9a3** - Enhanced template syntax handling and documentation updates

[Unreleased]: https://github.com/bartTC/tailwhip/compare/v0.9...HEAD
[0.9]: https://github.com/bartTC/tailwhip/compare/v0.9b0...v0.9
[0.9b0]: https://github.com/bartTC/tailwhip/releases/tag/v0.9b0

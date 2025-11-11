# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Testing**: Added test coverage for stdin behavior when no input is provided
  - New test `test_no_stdin_and_no_files` verifies proper error handling
  - Ensures clean exit with appropriate error message (no traceback)

## [0.10.1] - 2025-11-07

### Fixed

- **Reliability**: Fixed crash when no `pyproject.toml` is found in current or parent directories

## [0.10.0] - 2025-11-06

### Added

- **Editor Integration**: STDIN/STDOUT filter mode for text editor integrations
  - Tailwhip now reads from stdin and writes to stdout when no file paths are provided
  - Enables direct integration with Vim/Neovim (`:%!tailwhip`), Emacs, VSCode, and other editors
  - No configuration or file I/O needed - just pipe text through tailwhip
  - Added comprehensive test suite in `test_stdin.py` with 4 test cases
  - Updated documentation with editor integration examples for Vim, VSCode, and Emacs

### Changed

- **Documentation**: Added additional project metadata URLs to `pyproject.toml`

  - Added direct link to project documentation (README.md)
  - Added direct link to changelog (CHANGELOG.md)
  - Added direct link to bug tracker (GitHub Issues)

- **Refactoring**: Moved `all_colors` computation to configuration module

  - Added `all_colors` attribute to `TailwhipConfig` class
  - Computed once during pattern recompilation instead of on every sort
  - Simplified function signatures by removing `all_colors` parameter passing
  - `is_color_utility()` and `sort_key()` now use `config.all_colors` directly

- **Testing**: Simplified test suite for better maintainability
  - Removed redundant integration tests (`test_kitchen_sink_example`, `test_css_apply_advanced`)
  - Added focused `test_deduplication` test for duplicate class handling
  - Updated test documentation to reflect current coverage

## [0.9.4] - 2025-11-05

### Added

- **Development**: Claude Code project configuration
  - Added PROJECT.md with development workflow guidelines
  - Added slash commands: `/release`, `/changelog` and `/verify`
  - Configured hooks to enforce workflow: tests → linting → changelog
  - Automated reminders after code changes to ensure quality standards
  - Shared settings in `settings.json` for all contributors
  - Added `.claude/settings.local.json` to `.gitignore` for personal overrides

### Changed

- **Performance**: File processing now starts immediately when scanning large directories

  - Removed eager materialization of file list in `apply_changes()`
  - Files are now processed as they are discovered by the generator
  - Significantly reduces startup delay for large codebases

- **Reliability**: Added 60-second timeout to file processing

  - Prevents indefinite hangs when processing files
  - `as_completed()` now uses timeout parameter in `apply_changes()`

- **Documentation**: Restructured comments in configuration arrays
  - All comments in `utility_groups` and `variant_groups` now consistently appear above their patterns
  - Clear separation between major groups with blank lines
  - Improved readability and maintainability of configuration structure

## [0.9.3] - 2025-01-04

### Changed

- **Sorting**: Position utilities (top, right, bottom, left) now sort clockwise
  - Split combined positioning pattern into separate utility groups
  - Order: top → right → bottom → left (clockwise direction)

## [0.9.2] - 2025-01-04

### Removed

- **Configuration**: Removed "primary" from default `custom_colors` list
  - The default config should not include example custom colors
  - Users should add their own custom colors as needed

### Added

- **Tests**: Added tests for custom pattern configuration
  - `test_custom_pattern_from_pyproject`: Tests custom patterns via `pyproject.toml`
  - `test_custom_pattern_from_config_file`: Tests custom patterns via custom config file
  - Both tests verify JSX `className` pattern as example of extensibility
  - Ensures all patterns (HTML, CSS, custom) work correctly together
  - Demonstrates correct TOML syntax for both configuration methods

### Changed

- **Documentation**: Clarified that `class_patterns` replace (not extend) defaults
  - Updated README.md with explicit warning about replacement behavior
  - Updated configuration.toml with IMPORTANT note about preserving defaults
  - Updated example.tailwhip.toml with complete example showing default patterns
  - Added JSX example showing how to include defaults when adding custom patterns

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

[Unreleased]: https://github.com/bartTC/tailwhip/compare/v0.10.1...HEAD
[0.10.1]: https://github.com/bartTC/tailwhip/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/bartTC/tailwhip/compare/v0.9.4...v0.10.0
[0.9.4]: https://github.com/bartTC/tailwhip/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/bartTC/tailwhip/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/bartTC/tailwhip/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/bartTC/tailwhip/compare/v0.9...v0.9.1
[0.9]: https://github.com/bartTC/tailwhip/compare/v0.9b0...v0.9
[0.9b0]: https://github.com/bartTC/tailwhip/releases/tag/v0.9b0

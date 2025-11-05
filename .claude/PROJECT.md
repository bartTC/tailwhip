# Tailwhip Project Guidelines

## Overview

Tailwhip is a Tailwind CSS class sorting utility that helps maintain consistent class ordering in HTML and CSS files.

## Development Workflow

### After Making Code Changes

When you make changes to the codebase, **always** follow these steps in order:

1. **Run the test suite FIRST**
   ```bash
   .venv/bin/python -m pytest
   ```
   - All tests must pass before proceeding
   - If tests fail, fix the issues before continuing
   - DO NOT proceed to the next step until tests pass

2. **Run code quality checks**
   ```bash
   ruff check
   ruff format --check
   ```
   - Code must pass both linting and formatting checks
   - If ruff check fails, fix the linting issues
   - If ruff format --check fails, run `ruff format` to fix formatting
   - DO NOT proceed until linting passes

### Changelog Guidelines

- **Always update CHANGELOG.md** after making code changes
- Place entries in the `[Unreleased]` section at the top
- Use these categories (in order):
  - **Added** - New features
  - **Changed** - Changes to existing functionality
  - **Fixed** - Bug fixes
  - **Removed** - Removed features
  - **Deprecated** - Soon-to-be removed features
  - **Security** - Security fixes

### Testing Philosophy

- Tests are located in `tailwhip/tests/`
- Use pytest for all testing
- Configuration tests should cover precedence: defaults < pyproject.toml < custom config < CLI args
- File processing tests should use temporary directories (not stub files)

### Code Style

- Python 3.11+ syntax
- Type hints for all functions
- Ruff for linting and formatting (configured in pyproject.toml)
- Clear docstrings for public APIs

## Project Structure

```
tailwhip/
├── tailwhip/
│   ├── files.py          # File processing and discovery
│   ├── configuration.py  # Configuration management (Dynaconf)
│   ├── sorting.py        # Core sorting algorithm
│   └── tests/           # Test suite
├── CHANGELOG.md         # Keep a Changelog format
└── pyproject.toml       # Project config and dependencies
```

## Important Notes

- **Never skip tests** - The test suite must pass
- **Never skip linting** - Code must be clean
- **Always update changelog** - Document all changes
- Configuration uses Dynaconf with clear precedence
- The sorting algorithm follows Tailwind CSS best practices
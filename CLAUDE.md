# Tailwhip - Claude AI Assistant Guide

This document contains guidelines and workflows for AI assistants working with the Tailwhip project.

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

## Common Workflows

### Verification Workflow

Run the complete verification workflow for Tailwhip IN ORDER:

1. FIRST: Run the test suite: `.venv/bin/python -m pytest`
   - Must pass before proceeding to next step

2. SECOND: Run ruff linting: `ruff check`
   - Must pass before proceeding to next step

3. THIRD: Verify code formatting: `ruff format --check`
   - Must pass before proceeding

Report the results clearly after each step. If any check fails, stop and explain what needs to be fixed before continuing.

### Adding Changelog Entries

Add a changelog entry to CHANGELOG.md for the most recent changes.

IMPORTANT: Before adding a changelog entry, ensure:
1. Tests have passed (.venv/bin/python -m pytest)
2. Linting has passed (ruff check && ruff format --check)

If tests or linting have not been run yet, run them first and ensure they pass.

Then add the changelog entry:
1. Review the unstaged git changes to understand what changed
2. Add an appropriate entry to the [Unreleased] section
3. Follow the Keep a Changelog format
4. Use the correct category (Added, Changed, Fixed, Removed, etc.)
5. Include a bold label (e.g., **Performance**, **Documentation**, **Reliability**)
6. Be specific and concise

### Release Workflow

Create a new release for Tailwhip by automating the entire release workflow.

#### Workflow Steps:

##### 1. Version Analysis
- Read the current version from `pyproject.toml`
- Parse the version (e.g., "0.9.3" → major.minor.patch)
- Calculate suggestions:
  - **Patch**: Increment patch (e.g., 0.9.3 → 0.9.4) - Bug fixes only
  - **Minor**: Increment minor (e.g., 0.9.3 → 0.10.0) - New features, backward compatible
  - **Major**: Increment major (e.g., 0.9.3 → 1.0.0) - Breaking changes

##### 2. Ask User for Version
Use the AskUserQuestion tool to present options:
- Show current version clearly
- Offer patch, minor, and major version options
- Include "Custom" option for manual entry
- Explain what each version type means

##### 3. Update pyproject.toml
- Replace the version line in pyproject.toml with the new version
- Show the diff

##### 4. Run uv sync
- Execute `uv sync` to update lock file with new version

##### 5. Update CHANGELOG.md
- Move the `[Unreleased]` section to a new version section with today's date
- Format: `## [X.Y.Z] - YYYY-MM-DD`
- Ask the user to verify that the date is correct.
- Keep the structure (Added, Changed, Fixed, etc.)
- Add a new empty `[Unreleased]` section at the top
- Update the version comparison links at the bottom:
  - Update `[Unreleased]` link to compare from new version to HEAD
  - Add new version link comparing from previous version to new version

##### 6. Run Tests and Linting
- Run pytest to ensure everything passes
- Run ruff check and format check
- DO NOT proceed if any checks fail

##### 7. Create Git Commit
- Stage pyproject.toml, CHANGELOG.md, and uv.lock
- Create commit message: "Release v{version}"
- Include Claude co-authorship

##### 8. Create Git Tag
- Create annotated git tag: `v{version}`
- Tag message: "Release version {version}"

##### 9. Summary
- Show what was done
- Remind user to:
  - Review the commit: `git show`
  - Push to remote: `git push origin main --tags`
  - Create GitHub release: `gh release create v{version} --generate-notes`
  - Build and publish to PyPI: `uv build && uv publish`

#### Important Notes:
- ALWAYS run tests before committing
- ALWAYS verify CHANGELOG.md formatting is correct
- Show clear output at each step
- If anything fails, stop and explain the issue

## Permissions

The following commands are pre-approved for execution without user confirmation:
- `python -m pytest` and `.venv/bin/python -m pytest`
- `uv pip install`, `uv pip list`, `uv sync`
- `python` and `.venv/bin/python`
- `ruff check` and `ruff format`
- `git log`
- `mkdir`
- Test file execution
- Web search operations

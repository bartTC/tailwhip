---
description: Create a new release with version bump, changelog update, and git tag
---

Create a new release for Tailwhip by automating the entire release workflow.

## Workflow Steps:

### 1. Version Analysis
- Read the current version from `pyproject.toml`
- Parse the version (e.g., "0.9.3" → major.minor.patch)
- Calculate suggestions:
  - **Patch**: Increment patch (e.g., 0.9.3 → 0.9.4) - Bug fixes only
  - **Minor**: Increment minor (e.g., 0.9.3 → 0.10.0) - New features, backward compatible
  - **Major**: Increment major (e.g., 0.9.3 → 1.0.0) - Breaking changes

### 2. Ask User for Version
Use the AskUserQuestion tool to present options:
- Show current version clearly
- Offer patch, minor, and major version options
- Include "Custom" option for manual entry
- Explain what each version type means

### 3. Update pyproject.toml
- Replace the version line in pyproject.toml with the new version
- Show the diff

### 4. Run uv sync
- Execute `uv sync` to update lock file with new version

### 5. Update CHANGELOG.md
- Move the `[Unreleased]` section to a new version section with today's date
- Format: `## [X.Y.Z] - YYYY-MM-DD`
- Keep the structure (Added, Changed, Fixed, etc.)
- Add a new empty `[Unreleased]` section at the top
- Update the version comparison links at the bottom:
  - Update `[Unreleased]` link to compare from new version to HEAD
  - Add new version link comparing from previous version to new version

### 6. Run Tests and Linting
- Run pytest to ensure everything passes
- Run ruff check and format check
- DO NOT proceed if any checks fail

### 7. Create Git Commit
- Stage pyproject.toml, CHANGELOG.md, and uv.lock
- Create commit message: "Release v{version}"
- Include Claude co-authorship

### 8. Create Git Tag
- Create annotated git tag: `v{version}`
- Tag message: "Release version {version}"

### 9. Summary
- Show what was done
- Remind user to:
  - Review the commit: `git show`
  - Push to remote: `git push origin main --tags`
  - Create GitHub release: `gh release create v{version} --generate-notes`
  - Build and publish to PyPI: `uv build && uv publish`

## Important Notes:
- ALWAYS run tests before committing
- ALWAYS verify CHANGELOG.md formatting is correct
- Show clear output at each step
- If anything fails, stop and explain the issue
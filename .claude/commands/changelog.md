---
description: Add an entry to CHANGELOG.md for recent changes
---

Add a changelog entry to CHANGELOG.md for the most recent changes.

IMPORTANT: Before adding a changelog entry, ensure:
1. Tests have passed (.venv/bin/python -m pytest)
2. Linting has passed (ruff check && ruff format --check)

If tests or linting have not been run yet, run them first and ensure they pass.

Then add the changelog entry:
1. Review the git diff to understand what changed
2. Add an appropriate entry to the [Unreleased] section
3. Follow the Keep a Changelog format
4. Use the correct category (Added, Changed, Fixed, Removed, etc.)
5. Include a bold label (e.g., **Performance**, **Documentation**, **Reliability**)
6. Be specific and concise
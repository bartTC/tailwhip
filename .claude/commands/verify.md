---
description: Run all verification checks (tests and linting) in the correct order
---

Run the complete verification workflow for Tailwhip IN ORDER:

1. FIRST: Run the test suite: `.venv/bin/python -m pytest`
   - Must pass before proceeding to next step

2. SECOND: Run ruff linting: `ruff check`
   - Must pass before proceeding to next step

3. THIRD: Verify code formatting: `ruff format --check`
   - Must pass before proceeding

Report the results clearly after each step. If any check fails, stop and explain what needs to be fixed before continuing.